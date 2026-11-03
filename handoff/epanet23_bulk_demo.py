"""Use EPANET-Turbo 2.3 bulk node/link setters and hydraulic getters."""
import argparse
import ctypes as c
import math
import os
import sys
from pathlib import Path
from tempfile import TemporaryDirectory

parser = argparse.ArgumentParser()
parser.add_argument('--library', required=True, help='EPANET 2.3.3 DLL, SO or dylib')
parser.add_argument('--inp', required=True, help='EPANET INP file')
parser.add_argument('--node', action='append', default=[], help='junction ID; repeat to set several')
parser.add_argument('--pipe', action='append', default=[], help='pipe ID; repeat to set several')
parser.add_argument('--node-factor', type=float, default=1.0, help='multiply selected base demands')
parser.add_argument('--pipe-factor', type=float, default=1.0, help='multiply selected pipe roughness')
parser.add_argument('--threads', type=int, default=4)
parser.add_argument('--factors', type=float, nargs='+', default=[1.0], help='demand multiplier for each full scenario')
args = parser.parse_args()
if args.threads < 1 or args.node_factor < 0 or args.pipe_factor <= 0 or any(f < 0 for f in args.factors):
    parser.error('threads and pipe factor must be positive; node factor must be non-negative')
os.environ['OMP_NUM_THREADS'] = str(args.threads)
os.environ['OMP_DYNAMIC'] = 'FALSE'
path = Path(args.library).expanduser().resolve(strict=True)
dll_dir = os.add_dll_directory(str(path.parent)) if os.name == 'nt' else None
lib = (c.WinDLL if os.name == 'nt' else c.CDLL)(str(path))
project = c.c_void_p()
int_p, double_p = c.POINTER(c.c_int), c.POINTER(c.c_double)


def bind(name, types):
    fn = getattr(lib, name)
    fn.argtypes, fn.restype = types, c.c_int
    return fn

create = bind('EN_createproject', [c.POINTER(c.c_void_p)])
open_model = bind('EN_open', [c.c_void_p, c.c_char_p, c.c_char_p, c.c_char_p])
close_model = bind('EN_close', [c.c_void_p])
delete = bind('EN_deleteproject', [c.c_void_p])
counts = bind('EN_get_counts', [c.c_void_p, int_p, int_p])
node_index = bind('EN_getnodeindex', [c.c_void_p, c.c_char_p, int_p])
link_index = bind('EN_getlinkindex', [c.c_void_p, c.c_char_p, int_p])
node_type = bind('EN_getnodetype', [c.c_void_p, c.c_int, int_p])
link_type = bind('EN_getlinktype', [c.c_void_p, c.c_int, int_p])
node_get = bind('EN_getnodevalue', [c.c_void_p, c.c_int, c.c_int, double_p])
link_get = bind('EN_getlinkvalue', [c.c_void_p, c.c_int, c.c_int, double_p])
set_nodes = bind('ENT_set_node_values', [c.c_void_p, c.c_int, int_p, double_p, c.c_int])
set_links = bind('ENT_set_link_values', [c.c_void_p, c.c_int, int_p, double_p, c.c_int])
set_multiplier = bind('ENT_set_demand_multiplier', [c.c_void_p, c.c_double])
get_option = bind('EN_getoption', [c.c_void_p, c.c_int, double_p])
open_h = bind('EN_openH', [c.c_void_p])
init_h = bind('EN_initH', [c.c_void_p, c.c_int])
run_h = bind('EN_runH', [c.c_void_p, c.POINTER(c.c_long)])
next_h = bind('EN_nextH', [c.c_void_p, c.POINTER(c.c_long)])
close_h = bind('EN_closeH', [c.c_void_p])
get_pressures = bind('EN_get_all_pressures', [c.c_void_p, c.c_int, c.c_int, double_p])
get_flows = bind('EN_get_all_flows', [c.c_void_p, c.c_int, c.c_int, double_p])

warnings = []
def check(code, where):
    if code >= 100:
        raise RuntimeError(f'{where}: EPANET error {code}')
    if code:
        warnings.append((where, code))
        print(f'EPANET warning {code} at {where}', file=sys.stderr)


def set_batch(names, lookup, get_type, getter, setter, prop, factor, allowed):
    if not names:
        return
    indexes, values = [], []
    for name in names:
        idx, typ, value = c.c_int(), c.c_int(), c.c_double()
        check(lookup(project, name.encode('utf-8'), c.byref(idx)), f'lookup {name}')
        check(get_type(project, idx.value, c.byref(typ)), f'type {name}')
        if typ.value not in allowed:
            raise ValueError(f'{name} has an incompatible node/link type {typ.value}')
        check(getter(project, idx.value, prop, c.byref(value)), f'read {name}')
        indexes.append(idx.value)
        values.append(value.value * factor)
    n = len(indexes)
    check(setter(project, prop, (c.c_int * n)(*indexes), (c.c_double * n)(*values), n), 'bulk set')
    for index, expected in zip(indexes, values):
        actual = c.c_double()
        check(getter(project, index, prop, c.byref(actual)), 'bulk readback')
        if not math.isclose(actual.value, expected, rel_tol=1e-12, abs_tol=1e-12):
            raise RuntimeError(f'Bulk readback differs for index {index}')
    print(f'Updated {n} values in memory; original INP is unchanged.')


opened = hydraulics_open = False
directory = TemporaryDirectory(prefix='epanet-turbo-demo-')
check(create(c.byref(project)), 'create project')
try:
    report = Path(directory.name) / 'report.rpt'
    check(open_model(project, os.fsencode(Path(args.inp).expanduser().resolve()), os.fsencode(report), b''), 'open model')
    opened = True
    nodes, links = c.c_int(), c.c_int()
    check(counts(project, c.byref(nodes), c.byref(links)), 'counts')
    # Property 1 = base demand; property 2 = roughness. Values use INP units.
    set_batch(args.node, node_index, node_type, node_get, set_nodes, 1, args.node_factor, {0})
    set_batch(args.pipe, link_index, link_type, link_get, set_links, 2, args.pipe_factor, {0, 1})
    p, q = (c.c_double * nodes.value)(), (c.c_double * links.value)()
    # Reuse one open model; each factor receives its own full hydraulic pass.
    for factor in args.factors:
        warning_start = len(warnings)
        check(set_multiplier(project, factor), 'set demand multiplier')
        actual_factor = c.c_double()
        check(get_option(project, 4, c.byref(actual_factor)), 'read demand multiplier')
        if not math.isclose(actual_factor.value, factor, rel_tol=1e-12, abs_tol=1e-12):
            raise RuntimeError('Demand multiplier readback differs')
        check(open_h(project), 'open hydraulics'); hydraulics_open = True
        check(init_h(project, 0), 'init hydraulics')
        current, step, count = c.c_long(), c.c_long(), 0
        while True:
            check(run_h(project, c.byref(current)), f'run at {current.value}s')
            check(get_pressures(project, nodes.value, 11, p), 'bulk pressures')
            check(get_flows(project, links.value, 8, q), 'bulk flows')
            if count == 0:
                print(f'Factor {factor}: first time {current.value}s')
                print('First five pressures:', list(p[:5]))
                print('First five flows:', list(q[:5]))
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
