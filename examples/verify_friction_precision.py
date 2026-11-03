"""Verify Net2 low-flow friction precision and standard hydraulic-file reuse."""
import argparse
import ctypes
import json
import os
import sys
import tempfile
from pathlib import Path

parser = argparse.ArgumentParser()
parser.add_argument('--bundle', type=Path, required=True)
parser.add_argument('--inp', type=Path, required=True)
parser.add_argument('--output', type=Path, required=True)
args = parser.parse_args()
os.environ['OMP_NUM_THREADS'] = '1'
os.environ['OPENBLAS_NUM_THREADS'] = '1'
tag = f'cp{sys.version_info.major}{sys.version_info.minor}'
sys.path.insert(0, str(args.bundle / 'python' / tag))

import numpy as np
import wntr
from fast_wntr_reader import FastBinFile
from turbo_adapter import TurboSimulator

if os.name == 'nt':
    library = args.bundle / 'native/windows_x86_64/epanet2.dll'
elif sys.platform == 'darwin':
    library = args.bundle / 'native/macos_arm64/libepanet2.dylib'
else:
    library = args.bundle / 'native/linux_x86_64/libepanet2.so'
network = wntr.network.WaterNetworkModel(str(args.inp))


def run(directory, name, *, fast=False, hydro=None, stock=False):
    sim = wntr.sim.EpanetSimulator(network) if stock else TurboSimulator(network, library)
    if fast:
        sim.reader = FastBinFile()
    kwargs = {'file_prefix': str(directory / name), 'version': 2.2}
    if hydro is None:
        kwargs['save_hyd'] = True
    else:
        kwargs.update(use_hyd=True, hydfile=str(hydro))
    result = sim.run_sim(**kwargs)
    if result.error_code is not None:
        raise RuntimeError(f'{name}: {result.error_code}')
    return result


def exact(left, right):
    for group in ('node', 'link'):
        a, b = getattr(left, group), getattr(right, group)
        assert a.keys() == b.keys()
        for field, table in a.items():
            other = b[field]
            assert table.index.equals(other.index) and table.columns.equals(other.columns)
            assert np.array_equal(table.dtypes.to_numpy(), other.dtypes.to_numpy())
            np.testing.assert_array_equal(table.to_numpy(), other.to_numpy())


def live_factor(inp, directory):
    loader = ctypes.WinDLL if os.name == 'nt' else ctypes.CDLL
    engine = loader(str(library.resolve()))
    project = ctypes.c_void_p()

    def call(name, *params):
        code = getattr(engine, name)(*params)
        if code:
            raise RuntimeError(f'{name}: {code}')

    call('EN_createproject', ctypes.byref(project))
    try:
        call('EN_open', project, os.fsencode(inp), os.fsencode(directory / 'direct.rpt'), b'')
        nodes = []
        for name in (b'18', b'32'):
            index = ctypes.c_int()
            call('EN_getnodeindex', project, name, ctypes.byref(index))
            nodes.append(index.value)
        link = ctypes.c_int()
        call('EN_getlinkindex', project, b'20', ctypes.byref(link))
        call('EN_openH', project)
        call('EN_initH', project, 0)
        time, step = ctypes.c_long(), ctypes.c_long()
        while True:
            call('EN_runH', project, ctypes.byref(time))
            if time.value == 90000:
                heads = []
                for index in nodes:
                    value = ctypes.c_double()
                    call('EN_getnodevalue', project, index, 10, ctypes.byref(value))
                    heads.append(value.value)
                flow = ctypes.c_double()
                call('EN_getlinkvalue', project, link, 8, ctypes.byref(flow))
                q = flow.value / 448.831
                return 39.725 * abs(heads[0] - heads[1]) / 350 / (q * q)
            call('EN_nextH', project, ctypes.byref(step))
            if not step.value:
                raise RuntimeError('Net2 did not reach 25 hours')
    finally:
        engine.EN_closeH(project)
        engine.EN_close(project)
        engine.EN_deleteproject(project)


with tempfile.TemporaryDirectory(prefix='epanet-friction-') as temp:
    directory = Path(temp)
    fresh = run(directory, 'fresh')
    fast = run(directory, 'fast', fast=True)
    exact(fresh, fast)
    expected = live_factor(directory / 'fresh.inp', directory)
    observed = float(fresh.link['friction_factor'].loc[90000, '20'])
    np.testing.assert_allclose(observed, expected, rtol=5e-6, atol=1e-7)
    hyd = directory / 'fresh.hyd'
    reused = run(directory, 'reused', hydro=hyd)
    stock_reused = run(directory, 'stock-reused', hydro=hyd, stock=True)
    np.testing.assert_array_equal(reused.link['friction_factor'].to_numpy(),
                                  stock_reused.link['friction_factor'].to_numpy())
    report = {
        'fresh_friction_factor': observed,
        'live_double_head_reference': expected,
        'reused_standard_hyd_friction_factor': float(reused.link['friction_factor'].loc[90000, '20']),
        'fast_reader_exact': True,
        'standard_hyd_readable_by_stock_epanet': True,
        'note': 'Existing standard .hyd files store rounded heads; their reused friction factors retain that precision limit.',
    }
    args.output.write_text(json.dumps(report, indent=2), encoding='utf-8')
    print(json.dumps(report, indent=2))
