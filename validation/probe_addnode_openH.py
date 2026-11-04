import ctypes
import os
import sys
from pathlib import Path

if os.name == 'nt':
    dll_directory = os.add_dll_directory(str(Path(sys.argv[1]).resolve().parent))
library = ctypes.CDLL(sys.argv[1])
project = ctypes.c_void_p()
library.EN_createproject.argtypes = [ctypes.POINTER(ctypes.c_void_p)]
library.EN_open.argtypes = [ctypes.c_void_p, ctypes.c_char_p, ctypes.c_char_p, ctypes.c_char_p]
library.EN_openH.argtypes = [ctypes.c_void_p]
library.EN_closeH.argtypes = [ctypes.c_void_p]
library.EN_initH.argtypes = [ctypes.c_void_p, ctypes.c_int]
library.EN_runH.argtypes = [ctypes.c_void_p, ctypes.POINTER(ctypes.c_long)]
library.EN_nextH.argtypes = [ctypes.c_void_p, ctypes.POINTER(ctypes.c_long)]
library.EN_gettimeparam.argtypes = [ctypes.c_void_p, ctypes.c_int, ctypes.POINTER(ctypes.c_long)]
library.EN_addnode.argtypes = [ctypes.c_void_p, ctypes.c_char_p, ctypes.c_int, ctypes.POINTER(ctypes.c_int)]

assert library.EN_createproject(ctypes.byref(project)) == 0
assert library.EN_open(project, sys.argv[2].encode(), sys.argv[3].encode(), b'') == 0
duration = ctypes.c_long()
assert library.EN_gettimeparam(project, 0, ctypes.byref(duration)) == 0
for cycle in range(5):
    assert library.EN_openH(project) == 0
    for reset in range(2):
        assert library.EN_initH(project, 10) == 0
        while True:
            t, dt = ctypes.c_long(), ctypes.c_long()
            assert 0 <= library.EN_runH(project, ctypes.byref(t)) < 100
            assert library.EN_nextH(project, ctypes.byref(dt)) == 0
            assert dt.value >= 0
            if dt.value == 0:
                assert t.value == duration.value
                break
    assert library.EN_closeH(project) == 0
print('Five OpenH/CloseH cycles complete', flush=True)
index = ctypes.c_int()
assert library.EN_addnode(project, b'ORPHAN', 0, ctypes.byref(index)) == 0
print('EN_addnode returned 0, new junction index', index.value, flush=True)
code = library.EN_openH(project)
print('EN_openH returned', code, flush=True)
assert code == 233
