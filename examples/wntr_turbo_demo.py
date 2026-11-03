"""Run WNTR 1.4.0 with the EPANET-Turbo 2.2-compatible bundle."""
import argparse
import os
import platform
import sys
from pathlib import Path

parser = argparse.ArgumentParser()
parser.add_argument('--bundle', required=True, help='extracted EPANET 2.2-compatible bundle')
parser.add_argument('--inp', required=True, help='EPANET INP file')
parser.add_argument('--output-dir', default='turbo-output', help='directory for WNTR output files')
parser.add_argument('--threads', type=int, default=4)
args = parser.parse_args()
if args.threads < 1:
    parser.error('--threads must be positive')
os.environ['OMP_NUM_THREADS'] = str(args.threads)
os.environ['OMP_DYNAMIC'] = 'FALSE'

bundle = Path(args.bundle).expanduser().resolve()
tag = f'cp{sys.version_info.major}{sys.version_info.minor}'
if tag not in ('cp311', 'cp312'):
    raise SystemExit('Use CPython 3.11 or 3.12')
platforms = {
    ('Windows', 'AMD64'): ('windows_x86_64', 'epanet2.dll'),
    ('Linux', 'x86_64'): ('linux_x86_64', 'libepanet2.so'),
    ('Darwin', 'arm64'): ('macos_arm64', 'libepanet2.dylib'),
}
key = (platform.system(), platform.machine())
if key not in platforms:
    raise SystemExit(f'Unsupported platform: {key}')
subdir, library = platforms[key]
sys.path.insert(0, str(bundle / 'python' / tag))
import wntr
from turbo_adapter import TurboSimulator
from fast_wntr_reader import FastBinFile

output = Path(args.output_dir).expanduser().resolve()
output.mkdir(parents=True, exist_ok=True)
try:
    str(output / 'run').encode('latin-1')
except UnicodeEncodeError:
    raise SystemExit('WNTR 1.4 requires a Latin-1 output path; use --output-dir with an ASCII path')
network = wntr.network.WaterNetworkModel(args.inp)
simulator = TurboSimulator(network, bundle / 'native' / subdir / library)
simulator.reader = FastBinFile()
results = simulator.run_sim(file_prefix=str(output / 'run'), version=2.2)
if results.error_code is not None:
    raise RuntimeError(f'Incomplete simulation: {results.error_code}')
print('Pressure (WNTR SI units):')
print(results.node['pressure'].iloc[:3, :5])
print('Flow (WNTR SI units):')
print(results.link['flowrate'].iloc[:3, :5])
print(f'Report steps: {len(results.node["pressure"])}')
