"""Open either Turbo 2.2 or 2.3 and use automatically selected bulk APIs."""
import argparse
import ctypes as c
import os
import platform
import sys
from pathlib import Path
from tempfile import TemporaryDirectory

parser = argparse.ArgumentParser()
parser.add_argument('--bundle', required=True, help='extracted 2.2 or 2.3 release bundle')
parser.add_argument('--inp', required=True)
parser.add_argument('--library', help='optional alternative EPANET 2.2/2.3 library')
parser.add_argument('--node', action='append', default=[], help='junction ID; repeat for multiple nodes')
parser.add_argument('--pipe', action='append', default=[], help='pipe ID; repeat for multiple pipes')
parser.add_argument('--node-factor', type=float, default=1.0)
parser.add_argument('--pipe-factor', type=float, default=1.0)
parser.add_argument('--factors', type=float, nargs='+', default=[1.0])
parser.add_argument('--threads', type=int, default=4)
parser.add_argument('--work-dir', help='existing directory for a temporary report')
args = parser.parse_args()
if args.threads < 1 or args.node_factor < 0 or args.pipe_factor <= 0 or any(f < 0 for f in args.factors):
    parser.error('threads and pipe factor must be positive; demand factors must be non-negative')
os.environ['OMP_NUM_THREADS'] = str(args.threads)
os.environ['OMP_DYNAMIC'] = 'FALSE'

bundle = Path(args.bundle).expanduser().resolve()
tag = f'cp{sys.version_info.major}{sys.version_info.minor}'
if tag not in ('cp311', 'cp312'):
    raise SystemExit('Use CPython 3.11 or 3.12')
platforms = {('Windows', 'AMD64'): ('windows_x86_64', 'epanet2.dll'),
             ('Linux', 'x86_64'): ('linux_x86_64', 'libepanet2.so'),
             ('Darwin', 'arm64'): ('macos_arm64', 'libepanet2.dylib')}
key = (platform.system(), platform.machine())
if key not in platforms:
    raise SystemExit(f'Unsupported platform: {key}')
subdir, filename = platforms[key]
path = Path(args.library).expanduser().resolve(strict=True) if args.library else (bundle / 'native' / subdir / filename).resolve(strict=True)
sys.path.insert(0, str(bundle / 'python' / tag))
from turbo_bulk import BulkAPI

dll_dir = os.add_dll_directory(str(path.parent)) if os.name == 'nt' else None
lib = (c.WinDLL if os.name == 'nt' else c.CDLL)(str(path))
project = c.c_void_p()
int_p, double_p = c.POINTER(c.c_int), c.POINTER(c.c_double)


def bind(name, types):
    fn = lib[name]
    fn.argtypes, fn.restype = types, c.c_int
    return fn


create = bind('EN_createproject', [c.POINTER(c.c_void_p)])
open_model = bind('EN_open', [c.c_void_p, c.c_char_p, c.c_char_p, c.c_char_p])
close_model = bind('EN_close', [c.c_void_p])
delete = bind('EN_deleteproject', [c.c_void_p])
node_index = bind('EN_getnodeindex', [c.c_void_p, c.c_char_p, int_p])
link_index = bind('EN_getlinkindex', [c.c_void_p, c.c_char_p, int_p])
node_type = bind('EN_getnodetype', [c.c_void_p, c.c_int, int_p])
link_type = bind('EN_getlinktype', [c.c_void_p, c.c_int, int_p])
node_get = bind('EN_getnodevalue', [c.c_void_p, c.c_int, c.c_int, double_p])
link_get = bind('EN_getlinkvalue', [c.c_void_p, c.c_int, c.c_int, double_p])
open_h = bind('EN_openH', [c.c_void_p])
init_h = bind('EN_initH', [c.c_void_p, c.c_int])
run_h = bind('EN_runH', [c.c_void_p, c.POINTER(c.c_long)])
next_h = bind('EN_nextH', [c.c_void_p, c.POINTER(c.c_long)])
close_h = bind('EN_closeH', [c.c_void_p])

warnings = []
def check(code, operation):
    if code >= 100:
        raise RuntimeError(f'{operation}: EPANET error {code}')
    if code:
        warnings.append((operation, code))
        print(f'EPANET warning {code} at {operation}', file=sys.stderr)


def set_selected(names, lookup, get_type, getter, setter, prop, factor, allowed):
    indices, values = [], []
    for name in names:
        index, kind, value = c.c_int(), c.c_int(), c.c_double()
        check(lookup(project, name.encode('utf-8'), c.byref(index)), f'lookup {name}')
        check(get_type(project, index.value, c.byref(kind)), f'type {name}')
        if kind.value not in allowed:
            raise ValueError(f'{name} has an incompatible node/link type {kind.value}')
        check(getter(project, index.value, prop, c.byref(value)), f'read {name}')
        indices.append(index.value)
        values.append(value.value * factor)
    if indices:
        setter(prop, indices, values)
        print(f'Updated {len(indices)} values in memory; original INP is unchanged.')


opened = hydraulics_open = False
directory = TemporaryDirectory(prefix='epanet-bulk-auto-', dir=args.work_dir)
check(create(c.byref(project)), 'create project')
try:
    report = Path(directory.name) / 'report.rpt'
    check(open_model(project, os.fsencode(Path(args.inp).expanduser().resolve()), os.fsencode(report), b''), 'open model')
    opened = True
    bulk = BulkAPI(lib, project)
    print('Detected EPANET version:', bulk.version)
    print('Selected API paths:', bulk.capabilities)
    set_selected(args.node, node_index, node_type, node_get, bulk.set_node_values, 1, args.node_factor, {0})
    set_selected(args.pipe, link_index, link_type, link_get, bulk.set_link_values, 2, args.pipe_factor, {0, 1})
    for factor in args.factors:
        warning_start = len(warnings)
        bulk.set_demand_multiplier(factor)
        check(open_h(project), 'open hydraulics'); hydraulics_open = True
        check(init_h(project, 0), 'init hydraulics')
        current, step, count = c.c_long(), c.c_long(), 0
        while True:
            check(run_h(project, c.byref(current)), f'run at {current.value}s')
            pressures, flows = bulk.node_values(), bulk.link_values()
            if count == 0:
                print(f'Factor {factor}, first time {current.value}s:')
                print('First five pressures:', pressures[:5].tolist())
                print('First five flows:', flows[:5].tolist())
            count += 1
            check(next_h(project, c.byref(step)), 'next step')
            if step.value <= 0:
                break
        check(close_h(project), 'close hydraulics'); hydraulics_open = False
        print(f'Factor {factor}: completed {count} hydraulic steps; warnings: {len(warnings) - warning_start}.')
finally:
    if hydraulics_open:
        close_h(project)
    if opened:
        close_model(project)
    delete(project)
    directory.cleanup()
    if dll_dir is not None:
        dll_dir.close()
