"""Check the protected WNTR writer, reader and simulator on a target platform."""
import argparse
import datetime
import os
import platform
import sys
import tempfile
import warnings
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

parser = argparse.ArgumentParser()
parser.add_argument('--bundle', required=True)
parser.add_argument('--inp', required=True)
parser.add_argument('--work-dir', required=True)
args = parser.parse_args()
os.environ['OMP_NUM_THREADS'] = '4'
os.environ['OMP_DYNAMIC'] = 'FALSE'
os.environ['OPENBLAS_NUM_THREADS'] = '1'
os.environ['MPLBACKEND'] = 'Agg'
bundle = Path(args.bundle).resolve(strict=True)
tag = f'cp{sys.version_info.major}{sys.version_info.minor}'
platforms = {('Windows', 'AMD64'): ('windows_x86_64', 'epanet2.dll'),
             ('Linux', 'x86_64'): ('linux_x86_64', 'libepanet2.so'),
             ('Darwin', 'arm64'): ('macos_arm64', 'libepanet2.dylib')}
subdir, binary = platforms[(platform.system(), platform.machine())]
library = bundle / 'native' / subdir / binary
sys.path.insert(0, str(bundle / 'python' / tag))

import pandas as pd
import wntr
import wntr.epanet.io as epanet_io
from wntr.epanet.util import FlowUnits
from fast_wntr_reader import FastBinFile
from fast_wntr_writer import write_inpfile
from turbo_adapter import TurboSimulator

class FixedDateTime(datetime.datetime):
    @classmethod
    def now(cls, tz=None):
        return cls(2026, 11, 3, 12, tzinfo=tz)

with tempfile.TemporaryDirectory(prefix='epanet-fast-io-', dir=args.work_dir) as folder:
    folder = Path(folder)
    network = wntr.network.WaterNetworkModel(args.inp)
    for formula in ('H-W', 'D-W', 'C-M'):
        network.options.hydraulic.headloss = formula
        if formula == 'D-W':
            for _, pipe in network.pipes():
                pipe.roughness = 0.00015
        for units in FlowUnits:
            standard, fast = folder / 'standard.inp', folder / 'fast.inp'
            with patch.object(epanet_io, 'datetime', SimpleNamespace(datetime=FixedDateTime)):
                wntr.network.write_inpfile(network, str(standard), units=units)
                write_inpfile(network, str(fast), units=units)
            assert standard.read_bytes() == fast.read_bytes(), (formula, units)
    network = wntr.network.WaterNetworkModel(args.inp)
    sim = TurboSimulator(network, library)
    sim.reader = FastBinFile()
    reference = sim.run_sim(file_prefix=str(folder / 'reference'), version=2.2)
    result = TurboSimulator(network, library, fast_io=True).run_sim(file_prefix=str(folder / 'fast'), version=2.2)
    assert result.error_code == reference.error_code
    for group in ('node', 'link'):
        left, right = getattr(reference, group), getattr(result, group)
        assert list(left) == list(right)
        for field in left:
            pd.testing.assert_frame_equal(left[field], right[field], check_exact=True)
    binary_data = (folder / 'reference.bin').read_bytes()
    for name, data in (('missing-epilog', binary_data[:-12]), ('invalid-magic', binary_data[:-4] + b'\0'*4), ('partial-periods', binary_data[:len(binary_data)//2])):
        incomplete = folder / (name + '.bin')
        incomplete.write_bytes(data)
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter('always')
            partial = FastBinFile().read(str(incomplete), convergence_error=False)
        assert caught and partial.error_code == wntr.sim.results.ResultsStatus.error
        try:
            FastBinFile().read(str(incomplete), convergence_error=True)
        except RuntimeError:
            pass
        else:
            raise AssertionError(f'{name}: strict mode did not raise')
print('PASS WNTR fast writer, simulation and incomplete-output handling')
