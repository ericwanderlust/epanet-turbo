"""Confirm old 2.3 bug and version-aware helper's safe standard option."""
import argparse
import ctypes as c
import json
import sys
import tempfile
from pathlib import Path

p=argparse.ArgumentParser()
p.add_argument('--module-dir',required=True)
p.add_argument('--library',required=True)
p.add_argument('--inp',required=True)
p.add_argument('--output',required=True)
a=p.parse_args()
sys.path.insert(0,str(Path(a.module_dir).resolve()))
from turbo_bulk import BulkAPI
lib=(c.WinDLL if sys.platform=='win32' else c.CDLL)(str(Path(a.library).resolve()))
def bind(name,types):
 fn=lib[name];fn.argtypes=types;fn.restype=c.c_int;return fn
create=bind('EN_createproject',[c.POINTER(c.c_void_p)])
open_project=bind('EN_open',[c.c_void_p,c.c_char_p,c.c_char_p,c.c_char_p])
close=bind('EN_close',[c.c_void_p]);delete=bind('EN_deleteproject',[c.c_void_p])
get=bind('EN_getoption',[c.c_void_p,c.c_int,c.POINTER(c.c_double)])
set_option=bind('EN_setoption',[c.c_void_p,c.c_int,c.c_double])
old_multiplier=bind('ENT_set_demand_multiplier',[c.c_void_p,c.c_double])
def value(project,code):
 out=c.c_double();assert get(project,code,c.byref(out))==0;return out.value
project=c.c_void_p();assert create(c.byref(project))==0;opened=False
directory=tempfile.TemporaryDirectory(prefix='legacy-multiplier-',dir=Path(a.output).resolve().parent)
try:
 assert open_project(project,bytes(str(Path(a.inp).resolve()),'utf-8'),bytes(str(Path(directory.name)/'report.rpt'),'utf-8'),b'')==0;opened=True
 base_visc,base_demand=value(project,13),value(project,4)
 assert old_multiplier(project,0.8)==0
 bad_visc,bad_demand=value(project,13),value(project,4)
 assert abs(bad_visc-0.8)<1e-12 and bad_demand==base_demand
 assert set_option(project,13,base_visc)==0
 bulk=BulkAPI(lib,project);bulk.set_demand_multiplier(0.8)
 fixed_visc,fixed_demand=value(project,13),value(project,4)
 assert fixed_visc==base_visc and abs(fixed_demand-0.8)<1e-12
 result={'old_native_bug_confirmed':True,'helper_uses_standard_epanet_option':True,'demand':fixed_demand,'viscosity_unchanged':True,'engine_version':bulk.version}
 Path(a.output).write_text(json.dumps(result,indent=2)+'\n')
 print(json.dumps(result,indent=2))
finally:
 if opened:close(project)
 delete(project)
 directory.cleanup()
