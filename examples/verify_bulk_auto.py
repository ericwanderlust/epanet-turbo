"""Verify version detection, native bulk and stock EPANET fallbacks."""
import argparse
import ctypes as ct
import json
import os
import sys
import tempfile
from pathlib import Path

os.environ['OMP_NUM_THREADS'] = '1'
os.environ['OPENBLAS_NUM_THREADS'] = '1'
parser = argparse.ArgumentParser()
parser.add_argument('--module-dir', required=True)
parser.add_argument('--lib22', required=True)
parser.add_argument('--lib23', required=True)
parser.add_argument('--inp', required=True)
parser.add_argument('--output', required=True)
args = parser.parse_args()
sys.path.insert(0, str(Path(args.module_dir).resolve()))
import numpy as np
from wntr.epanet.toolkit import ENepanet
from turbo_bulk import BulkAPI


class Standard23Only:
    def __init__(self, library):
        self.library = library
    def __getattr__(self, name):
        if name.startswith('ENT_') or name in ('EN_get_all_pressures', 'EN_get_all_flows'):
            raise AttributeError(name)
        return getattr(self.library, name)
    def __getitem__(self, name):
        return self.library[name]


def check_case(label, library_path, expected_version, expected_modes, directory, standard23=False):
    toolkit = ENepanet(version=2.2)
    if library_path:
        path = Path(library_path).resolve()
        if os.name == 'nt':
            dll_dir = os.add_dll_directory(str(path.parent))
        else:
            dll_dir = None
        toolkit.ENlib = (ct.WinDLL if os.name == 'nt' else ct.CDLL)(str(path))
    else:
        dll_dir = None
    toolkit.ENopen(str(Path(args.inp).resolve()), str(directory / f'{label}.rpt'), '')
    try:
        raw_library = toolkit.ENlib
        if standard23:
            toolkit.ENlib = Standard23Only(raw_library)
        bulk = BulkAPI.from_wntr(toolkit)
        assert bulk.version == expected_version, (label, bulk.version)
        assert bulk.capabilities == expected_modes, (label, bulk.capabilities)
        # Attaching must not change WNTR's own cached ctypes function signatures.
        before_node = toolkit.ENgetnodevalue(2, 1)
        before_link = toolkit.ENgetlinkvalue(1, 2)
        assert isinstance(before_node, float) and isinstance(before_link, float)
        node_indices = np.array([2, 3], dtype=np.int32)
        old_nodes = np.array([toolkit.ENgetnodevalue(int(i), 1) for i in node_indices])
        link_indices = np.array([1, 2], dtype=np.int32)
        old_links = np.array([toolkit.ENgetlinkvalue(int(i), 2) for i in link_indices])
        new_nodes, new_links = old_nodes * 1.01, old_links * 1.01
        bulk.set_node_values(1, node_indices, new_nodes)
        bulk.set_link_values(2, link_indices, new_links)
        np.testing.assert_allclose([toolkit.ENgetnodevalue(int(i), 1) for i in node_indices], new_nodes, rtol=1e-12, atol=1e-12)
        np.testing.assert_allclose([toolkit.ENgetlinkvalue(int(i), 2) for i in link_indices], new_links, rtol=1e-12, atol=1e-12)
        getoption = raw_library['EN_getoption']
        getoption.argtypes = [ct.c_void_p, ct.c_int, ct.POINTER(ct.c_double)]
        getoption.restype = ct.c_int
        ph = ct.c_void_p(toolkit._project.value)
        viscosity_before, viscosity_after, multiplier = ct.c_double(), ct.c_double(), ct.c_double()
        # 2.2 and 2.3 expose the same option codes for demand and viscosity.
        assert getoption(ph, 13, ct.byref(viscosity_before)) == 0
        bulk.set_demand_multiplier(0.8)
        assert getoption(ph, 4, ct.byref(multiplier)) == 0 and abs(multiplier.value - 0.8) < 1e-12
        assert getoption(ph, 13, ct.byref(viscosity_after)) == 0 and viscosity_before.value == viscosity_after.value
        toolkit.ENopenH(); toolkit.ENinitH(0); toolkit.ENrunH()
        try:
            pressure, flow = bulk.node_values(), bulk.link_values()
            scalar_pressure = np.array([toolkit.ENgetnodevalue(i, 11) for i in range(1, len(pressure) + 1)])
            scalar_flow = np.array([toolkit.ENgetlinkvalue(i, 8) for i in range(1, len(flow) + 1)])
            np.testing.assert_array_equal(pressure, scalar_pressure)
            np.testing.assert_array_equal(flow, scalar_flow)
        finally:
            toolkit.ENcloseH()
        bulk.set_node_values(1, node_indices, old_nodes)
        bulk.set_link_values(2, link_indices, old_links)
        np.testing.assert_allclose([toolkit.ENgetnodevalue(int(i), 1) for i in node_indices], old_nodes, rtol=1e-12, atol=1e-12)
        np.testing.assert_allclose([toolkit.ENgetlinkvalue(int(i), 2) for i in link_indices], old_links, rtol=1e-12, atol=1e-12)
        for indices, values in (([], []), ([1, 2], [1]), ([[1, 2]], [[1, 2]]), ([2.5], [1]), ([0], [1]), ([999999], [1]), ([2], [float('nan')])):
            try: bulk.set_node_values(1, indices, values)
            except ValueError: pass
            else: raise AssertionError('Invalid input accepted')
        assert toolkit.ENgetnodevalue(2, 1) == old_nodes[0]
        try: bulk.set_demand_multiplier(float('nan'))
        except ValueError: pass
        else: raise AssertionError('Non-finite demand multiplier accepted')
        try: bulk.node_values(9999)
        except RuntimeError: pass
        else: raise AssertionError('Invalid EPANET property accepted')
        return {'version': bulk.version, 'capabilities': bulk.capabilities,
                'nodes': len(pressure), 'links': len(flow), 'reads_exact': True,
                'setter_readback_and_restore': True, 'demand_multiplier': multiplier.value,
                'viscosity_unchanged': True, 'wntr_calls_still_work': True}
    finally:
        if standard23:
            toolkit.ENlib = raw_library
        toolkit.ENclose()
        if dll_dir:
            dll_dir.close()


turbo = {'node_read':'turbo_bulk','link_read':'turbo_bulk','node_write':'turbo_bulk','link_write':'turbo_bulk','demand_multiplier':'epanet'}
scalar = {'node_read':'scalar','link_read':'scalar','node_write':'scalar','link_write':'scalar','demand_multiplier':'epanet'}
standard = {'node_read':'epanet_bulk','link_read':'epanet_bulk','node_write':'scalar','link_write':'scalar','demand_multiplier':'epanet'}
with tempfile.TemporaryDirectory(prefix='bulk-auto-test-', dir=Path(args.output).resolve().parent) as temp:
    directory = Path(temp)
    result = {
        'turbo22': check_case('turbo22', args.lib22, 20200, turbo, directory),
        'turbo23': check_case('turbo23', args.lib23, 20303, turbo, directory),
        'wntr_stock22': check_case('wntr_stock22', None, 20200, scalar, directory),
        'standard23_capability_mask': check_case('standard23', args.lib23, 20303, standard, directory, standard23=True),
    }
Path(args.output).write_text(json.dumps(result, indent=2)+'\n')
print(json.dumps(result, indent=2))
