"""Exercise the compiled Rust extension against Windows EPANET 2.2 and 2.3."""
import argparse
import ctypes
import os
from pathlib import Path
import sys

import numpy as np
import wntr


parser = argparse.ArgumentParser()
parser.add_argument("--extension-dir", type=Path, required=True)
parser.add_argument("--bundle22", type=Path, required=True)
parser.add_argument("--bundle23", type=Path, required=True)
parser.add_argument("--inp", type=Path, required=True)
args = parser.parse_args()
sys.path.insert(0, str(args.extension_dir))
import epanet_rs


def expect_error(call, text):
    try:
        call()
    except RuntimeError as error:
        assert text in str(error), error
    else:
        raise AssertionError(f"expected {text}")


native22 = args.bundle22 / "native/windows_x86_64"
native23 = args.bundle23 / "native/windows_x86_64"
stock = Path(wntr.__file__).parent / "epanet/libepanet/windows-x64/epanet22.dll"
libraries = ((stock, False), (native22 / "epanet2.dll", True), (native23 / "epanet2.dll", True))
with os.add_dll_directory(str(native22)), os.add_dll_directory(str(native23)):
    runtime = ctypes.CDLL(str((native22 / "libgomp-1.dll").resolve()))
    runtime.omp_set_num_threads.argtypes = [ctypes.c_int]
    runtime.omp_get_max_threads.restype = ctypes.c_int
    for path, threaded in libraries:
        context = epanet_rs.EpanetContext(str(path.resolve()))
        expect_error(context.run_hydraulics, "not open")
        context.open(str(args.inp.resolve()))
        counts = (context.n_nodes, context.n_links)
        context.open(str(args.inp.resolve()))
        assert counts == (context.n_nodes, context.n_links)
        expect_error(lambda: context.open(str(args.inp.with_name("__absent__.inp").resolve())), "EN_open")
        context.open(str(args.inp.resolve()))
        indices = np.array([0], dtype=np.int32)
        values = np.array([1.0], dtype=np.float64)
        expect_error(lambda: context.set_node_values(indices, 1, values), "203")
        expect_error(lambda: context.set_link_values(indices, 0, values), "204")
        times, pressure, flow, stats = context.run_hydraulics()
        times32, pressure32, flow32, stats32 = context.run_hydraulics_f32()
        assert len(times) == 56 and len(pressure) == len(times) * context.n_nodes
        assert len(flow) == len(times) * context.n_links
        np.testing.assert_array_equal(times, times32)
        np.testing.assert_allclose(pressure, pressure32, rtol=1e-6, atol=1e-6)
        np.testing.assert_allclose(flow, flow32, rtol=1e-6, atol=1e-6)
        assert stats["hydraulic_warnings"] == stats32["hydraulic_warnings"]
        if threaded:
            runtime.omp_set_num_threads(2)
            assert runtime.omp_get_max_threads() == 2
            context.run_hydraulics(4)
            assert runtime.omp_get_max_threads() == 4
        else:
            expect_error(lambda: context.run_hydraulics(4), "Thread control is unavailable")
        context.close()
        assert context.n_nodes == context.n_links == 0
        print("PASS", path.name, "threads", threaded, flush=True)

    engine = ctypes.WinDLL(str((native22 / "epanet2.dll").resolve()))
    engine.ENT_engine_id.restype = ctypes.c_char_p
    assert b"OpenMP" in engine.ENT_engine_id()
    engine.ENT_set_num_threads.argtypes = [ctypes.c_int]
    engine.ENT_set_num_threads(3)
    assert runtime.omp_get_max_threads() == 3
    print("PASS Windows 2.2 OpenMP control", flush=True)

raw = np.frombuffer(b"node\0\0\0\0" + "水".encode().ljust(8, b"\0"), dtype=np.uint8)
assert epanet_rs.decode_fixed_width_ids(raw, 8) == ["node", "水"]
print("PASS Rust WNTR ID decoding", flush=True)
