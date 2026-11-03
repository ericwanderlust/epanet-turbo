"""Verify full WNTR demand scenarios with Turbo and stock EPANET 2.2."""
import argparse
import os
import platform
import sys
import tempfile
from pathlib import Path

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
sys.path.insert(0, str(bundle / 'python' / tag))

import pandas as pd
import wntr
from wntr.epanet.toolkit import ENepanet
from turbo_adapter import TurboSimulator
from turbo_wntr_batch import DemandScenarios

network = wntr.network.WaterNetworkModel(args.inp)
libraries = {'turbo': bundle / 'native' / subdir / binary,
             'wntr': Path(ENepanet(version=2.2).ENlib._name)}
factors = (0.9, 1.0, 1.1, 0.9)
with tempfile.TemporaryDirectory(prefix='epanet-batch-test-', dir=args.work_dir) as folder:
    folder = Path(folder)
    for label, library in libraries.items():
        expected = []
        original = network.options.hydraulic.demand_multiplier
        try:
            for i, factor in enumerate(factors):
                network.options.hydraulic.demand_multiplier = factor
                simulator = TurboSimulator(network, library, fast_io=True)
                expected.append(simulator.run_sim(file_prefix=str(folder / f'{label}-{i}'), version=2.2))
        finally:
            network.options.hydraulic.demand_multiplier = original
        with DemandScenarios(network, library, work_dir=folder) as batch:
            assert batch.version // 100 == 202
            if label == 'wntr':
                assert batch._bulk.capabilities['node_write'] == 'scalar'
            try:
                batch.run(0)
            except ValueError:
                pass
            else:
                raise AssertionError('Zero multiplier should be rejected')
            for factor, reference in zip(factors, expected):
                result = batch.run(factor)
                assert result.error_code == reference.error_code
                assert not batch.last_warnings
                for group in ('node', 'link'):
                    left, right = getattr(reference, group), getattr(result, group)
                    assert list(left) == list(right)
                    for field in left:
                        pd.testing.assert_frame_equal(left[field], right[field], check_exact=True)
        print(label, 'four complete scenarios match and close successfully')
print('PASS WNTR demand scenarios and 2.2 scalar fallback')
