import ctypes
from ctypes import *
import os

os.add_dll_directory(os.getcwd())

class P(Structure):
    _fields_ = [('total', c_double), ('assemble', c_double), ('linear_solve', c_double), ('headloss', c_double), ('convergence', c_double), ('controls', c_double), ('rules_time', c_double), ('simple_controls_time', c_double), ('step_count', c_int32), ('iter_count', c_int32), ('rules_eval_count', c_int32), ('rules_fire_count', c_int32), ('rules_skip_count', c_int32), ('simple_controls_eval_count', c_int32), ('simple_controls_fire_count', c_int32), ('simple_controls_skip_count', c_int32)]

print('Loading DLL from current directory...')
dll = ctypes.WinDLL('./epanet2.dll')
ph = c_void_p()
dll.EN_createproject(byref(ph))

INP = r'D:\Project\????\EPANET\Example\test_rules.inp'

print('Opening INP...')
err = dll.EN_open(ph, INP.encode('mbcs'), b'', b'')
print(f'Open Result: {err}')

if err == 0:
    dll.EN_openH(ph)
    dll.EN_initH(ph, 0)
    t=c_long(); ts=c_long()
    print('Simulating...')
    while True:
        dll.EN_runH(ph, byref(t))
        dll.EN_nextH(ph, byref(ts))
        if ts.value <= 0: break
    
    prof = P()
    dll.ENT_get_profile(ph, byref(prof))
    print('\n--- M6-2 VERIFICATION SUCCESS ---')
    print(f'Rules Eval: {prof.rules_eval_count}')
    print(f'Rules Skip: {prof.rules_skip_count}')
    print(f'Rules Fire: {prof.rules_fire_count}')
    
    if prof.rules_eval_count + prof.rules_skip_count > 0:
        skip_rate = (prof.rules_skip_count / (prof.rules_eval_count + prof.rules_skip_count)) * 100
        print(f'Skip Rate: {skip_rate:.2f}%')
        
    dll.EN_closeH(ph)
    dll.EN_close(ph)
    dll.EN_deleteproject(ph)
    print('Verification Complete.')
else:
    print('Failed to open.')
