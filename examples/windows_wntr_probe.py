"""Validate an encrypted WNTR bundle on Windows and quantify engine differences."""
import argparse
import json
import os
import platform
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

network = wntr.network.WaterNetworkModel(str(args.inp))
library = args.bundle / 'native' / 'windows_x86_64' / 'epanet2.dll'


def run(engine, fast, directory):
    simulator = (wntr.sim.EpanetSimulator(network) if engine == 'stock'
                 else TurboSimulator(network, library))
    if fast:
        simulator.reader = FastBinFile()
    result = simulator.run_sim(file_prefix=str(directory / f'{engine}-{fast}'), version=2.2)
    if result.error_code is not None:
        raise RuntimeError(f'{engine}/{fast}: {result.error_code}')
    return result


def compare(a, b, exact=False):
    output = {}
    for group in ('node', 'link'):
        left, right = getattr(a, group), getattr(b, group)
        assert left.keys() == right.keys()
        for name, table in left.items():
            other = right[name]
            assert table.index.equals(other.index) and table.columns.equals(other.columns)
            assert np.array_equal(table.dtypes.to_numpy(), other.dtypes.to_numpy())
            x, y = table.to_numpy(), other.to_numpy()
            assert np.isfinite(x).all() and np.isfinite(y).all()
            if exact:
                np.testing.assert_array_equal(x, y)
            delta = np.abs(x.astype(np.float64) - y.astype(np.float64))
            row, col = np.unravel_index(np.argmax(delta), delta.shape)
            output[f'{group}.{name}'] = {
                'different_values': int(np.count_nonzero(delta)),
                'max_abs': float(delta[row, col]),
                'time': int(table.index[row]),
                'id': str(table.columns[col]),
                'stock': float(x[row, col]),
                'turbo': float(y[row, col]),
            }
    return output


with tempfile.TemporaryDirectory(prefix='epanet-probe-') as temp:
    directory = Path(temp)
    stock = run('stock', False, directory)
    stock_fast = run('stock', True, directory)
    turbo = run('turbo', False, directory)
    turbo_fast = run('turbo', True, directory)
    compare(stock, stock_fast, exact=True)
    compare(turbo, turbo_fast, exact=True)
    differences = compare(stock, turbo)
    report = {
        'platform': platform.platform(), 'machine': platform.machine(),
        'python': platform.python_version(), 'wntr': wntr.__version__,
        'numpy': np.__version__, 'nodes': network.num_nodes,
        'links': network.num_links, 'report_times': len(stock.node['pressure']),
        'stock_fast_reader_exact': True, 'turbo_fast_reader_exact': True,
        'engine_differences': differences,
    }
    args.output.write_text(json.dumps(report, indent=2), encoding='utf-8')
    print(json.dumps(report, indent=2))
