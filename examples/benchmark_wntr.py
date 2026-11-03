"""Compare WNTR's default engine/reader with Turbo and the optional reader."""
import argparse
import gc
import json
import os
import platform
import statistics
import tempfile
import time
from pathlib import Path

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--inp', required=True, help='EPANET INP model')
parser.add_argument('--library', required=True, help='2.2-compatible Turbo library')
parser.add_argument('--runs', type=int, default=5, help='measurements per configuration')
parser.add_argument('--threads', type=int, default=4, help='Turbo OpenMP threads')
parser.add_argument('--work-dir', help='directory in which to create temporary output files')
parser.add_argument('--output', help='optional path for the JSON results')
args = parser.parse_args()
if args.runs < 1 or args.threads < 1:
    parser.error('--runs and --threads must be positive')
os.environ['OMP_NUM_THREADS'] = str(args.threads)
os.environ['OMP_DYNAMIC'] = 'FALSE'
os.environ.setdefault('OPENBLAS_NUM_THREADS', '1')

import numpy as np
import wntr
import wntr.epanet.toolkit as toolkit
import wntr.sim.epanet as epanet_sim
from wntr.epanet.io import BinFile
from fast_wntr_reader import FastBinFile
from turbo_adapter import TurboSimulator

started = time.perf_counter()
network = wntr.network.WaterNetworkModel(args.inp)
model_load_seconds = time.perf_counter() - started
labels = ('stock_standard', 'stock_fast', 'turbo_standard', 'turbo_fast')
records = {label: [] for label in labels}
phases = {}
original_write = epanet_sim.write_inpfile
original_methods = {}


def timed_write(*a, **kw):
    start = time.perf_counter()
    try:
        return original_write(*a, **kw)
    finally:
        phases['write_inp'] = time.perf_counter() - start


def timed_method(name, original):
    def run(self, *a, **kw):
        start = time.perf_counter()
        try:
            return original(self, *a, **kw)
        finally:
            phases[name] = time.perf_counter() - start
    return run


def compare(reference, candidate, label, *, exact=False):
    if reference.error_code != candidate.error_code:
        raise ValueError(f'{label}: simulation error codes differ')
    differences = {}
    for group in ('node', 'link'):
        expected = getattr(reference, group)
        actual = getattr(candidate, group)
        if expected.keys() != actual.keys():
            raise ValueError(f'{label}: {group} result fields differ')
        for field, a in expected.items():
            b = actual[field]
            if not (a.index.equals(b.index) and a.columns.equals(b.columns) and
                    a.index.names == b.index.names and a.columns.names == b.columns.names and
                    np.array_equal(a.dtypes.to_numpy(), b.dtypes.to_numpy())):
                raise ValueError(f'{label}: {group}.{field} indices or data types differ')
            left, right = a.to_numpy(), b.to_numpy()
            if not np.isfinite(left).all() or not np.isfinite(right).all():
                raise ValueError(f'{label}: {group}.{field} contains non-finite values')
            equal = np.array_equal(left, right)
            if not equal and (exact or (group == 'link' and field == 'status')):
                raise ValueError(f'{label}: {group}.{field} values differ')
            delta = np.abs(left.astype(np.float64) - right.astype(np.float64))
            summary = {
                'equal': bool(equal),
                'different_values': int(np.count_nonzero(delta)),
                'max_absolute_difference': float(delta.max(initial=0)),
            }
            if delta.size and not equal:
                row, col = np.unravel_index(np.argmax(delta), delta.shape)
                summary.update(time=int(a.index[row]), id=str(a.columns[col]),
                               stock=float(left[row, col]), turbo=float(right[row, col]))
            differences[f'{group}.{field}'] = summary
    return differences


def run(label, directory):
    phases.clear()
    engine, reader = label.split('_')
    sim = (wntr.sim.EpanetSimulator(network) if engine == 'stock'
           else TurboSimulator(network, args.library))
    sim.reader = BinFile() if reader == 'standard' else FastBinFile()
    read = sim.reader.read

    def timed_read(*a, **kw):
        start = time.perf_counter()
        try:
            return read(*a, **kw)
        finally:
            phases['read_output'] = time.perf_counter() - start

    sim.reader.read = timed_read
    start = time.perf_counter()
    result = sim.run_sim(file_prefix=str(directory / label), version=2.2)
    elapsed = time.perf_counter() - start
    if result.error_code is not None:
        raise RuntimeError(f'{label} did not produce a complete result: {result.error_code}')
    return result, dict(phases, run_sim_wall_seconds=elapsed)


try:
    epanet_sim.write_inpfile = timed_write
    for name in ('ENopen', 'ENsolveH', 'ENsolveQ', 'ENreport', 'ENclose'):
        original_methods[name] = getattr(toolkit.ENepanet, name)
        setattr(toolkit.ENepanet, name, timed_method(name, original_methods[name]))
    with tempfile.TemporaryDirectory(prefix='epanet-wntr-benchmark-', dir=args.work_dir) as tmp:
        directory = Path(tmp)
        reference, _ = run(labels[0], directory)
        result, _ = run(labels[1], directory)
        compare(reference, result, labels[1], exact=True)
        del result
        gc.collect()
        turbo_reference, _ = run(labels[2], directory)
        engine_differences = compare(reference, turbo_reference, labels[2])
        del reference
        gc.collect()
        result, _ = run(labels[3], directory)
        compare(turbo_reference, result, labels[3], exact=True)
        del turbo_reference, result
        gc.collect()
        for i in range(args.runs):
            order = labels[i % 4:] + labels[:i % 4]
            if i % 2:
                order = tuple(reversed(order))
            for label in order:
                result, sample = run(label, directory)
                records[label].append(sample)
                print(f"{label} run {i+1}: {sample['run_sim_wall_seconds']:.4f} s", flush=True)
                del result
                gc.collect()
finally:
    epanet_sim.write_inpfile = original_write
    for name, original in original_methods.items():
        setattr(toolkit.ENepanet, name, original)

summary = {label: {field: statistics.median(row[field] for row in samples)
                   for field in samples[0]} for label, samples in records.items()}
report = {
    'wntr': wntr.__version__, 'python': platform.python_version(),
    'system': platform.platform(), 'machine': platform.machine(),
    'nodes': network.num_nodes, 'links': network.num_links,
    'duration_s': network.options.time.duration,
    'quality': network.options.quality.parameter,
    'model_load_seconds': model_load_seconds, 'threads': args.threads,
    'description': 'One model load; one warm-up and rotated full run_sim measurements per configuration. Model load is excluded from run_sim.',
    'warmup_results': 'Each engine produces exactly equal results with the default and fast readers; stock and Turbo differences are reported below.',
    'engine_differences': engine_differences,
    'comparison_note': 'Timings do not establish engineering equivalence; assess the reported engine differences for the model.',
    'median_seconds': summary, 'runs': records,
}
text = json.dumps(report, indent=2)
if args.output:
    Path(args.output).write_text(text + '\n')
print(text)
