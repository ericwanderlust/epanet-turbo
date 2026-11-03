import ctypes as c,json,os,sys
from pathlib import Path
lib=c.CDLL(sys.argv[1]); model=sys.argv[2];out=Path(sys.argv[3]);P=c.c_void_p
lib.EN_createproject.argtypes=[c.POINTER(P)];lib.EN_open.argtypes=[P,c.c_char_p,c.c_char_p,c.c_char_p]
lib.EN_getoption.argtypes=[P,c.c_int,c.POINTER(c.c_double)];lib.EN_setoption.argtypes=[P,c.c_int,c.c_double]
lib.ENT_set_demand_multiplier.argtypes=[P,c.c_double];lib.EN_getcount.argtypes=[P,c.c_int,c.POINTER(c.c_int)]
lib.EN_gettimeparam.argtypes=[P,c.c_int,c.POINTER(c.c_long)];lib.EN_getnodevalues.argtypes=[P,c.c_int,c.POINTER(c.c_double)]
lib.EN_getlinkvalues.argtypes=[P,c.c_int,c.POINTER(c.c_double)];lib.EN_openH.argtypes=[P];lib.EN_initH.argtypes=[P,c.c_int]
lib.EN_runH.argtypes=[P,c.POINTER(c.c_long)];lib.EN_nextH.argtypes=[P,c.POINTER(c.c_long)];lib.EN_closeH.argtypes=[P]
lib.EN_close.argtypes=[P];lib.EN_deleteproject.argtypes=[P]
lib.EN_solveH.argtypes=[P];lib.EN_solveQ.argtypes=[P]
def getopt(h,k):
 v=c.c_double();assert lib.EN_getoption(h,k,c.byref(v))==0;return v.value
def new(label):
 h=P();assert lib.EN_createproject(c.byref(h))==0
 assert lib.EN_open(h,os.fsencode(model),os.fsencode(str(out)+label+'.rpt'),b'')==0
 return h
def run(h,factor,via):
 viscosity=getopt(h,13)
 rc=lib.ENT_set_demand_multiplier(h,factor) if via=='turbo' else lib.EN_setoption(h,4,factor)
 assert rc==0
 after_factor=getopt(h,4);after_viscosity=getopt(h,13)
 assert lib.EN_openH(h)==0 and lib.EN_initH(h,0)==0
 n=c.c_int();l=c.c_int();tanks=c.c_int();duration=c.c_long()
 for typ,val in ((0,n),(1,tanks),(2,l)):assert lib.EN_getcount(h,typ,c.byref(val))==0
 assert lib.EN_gettimeparam(h,0,c.byref(duration))==0
 node=(c.c_double*n.value)();links=(c.c_double*l.value)();t=c.c_long();dt=c.c_long();records=[];first_demand=0.
 while True:
  rc=lib.EN_runH(h,c.byref(t)); assert rc==0
  vals=[]
  for prop in (9,11):
   assert lib.EN_getnodevalues(h,prop,node)==0; vals.append(tuple(node))
  if not records:first_demand=sum(x for x in vals[0][:n.value-tanks.value] if x>0)
  for prop in (8,11):
   assert lib.EN_getlinkvalues(h,prop,links)==0;vals.append(tuple(links))
  records.append((t.value,*vals));assert lib.EN_nextH(h,c.byref(dt))==0
  if dt.value==0:break
 assert t.value==duration.value and lib.EN_closeH(h)==0
 return {'factor':factor,'actual_factor':after_factor,'viscosity_before':viscosity,'viscosity_after':after_viscosity,'steps':len(records),'first_positive_demand':first_demand},records
warm=new('warm');assert lib.ENT_set_demand_multiplier(None,1.2)==202
summaries=[];cold_equal=True;repeat_equal=False;states=[]
try:
 for i,factor in enumerate((0.8,1.0,1.2,0.8)):
  row,warm_values=run(warm,factor,'turbo');cold=new(str(i))
  try:ref,cold_values=run(cold,factor,'standard')
  finally:lib.EN_close(cold);lib.EN_deleteproject(cold)
  row['cold_standard_equal']=warm_values==cold_values
  row['viscosity_unchanged']=row['viscosity_before']==row['viscosity_after']
  cold_equal &= row['cold_standard_equal'];summaries.append(row);states.append(warm_values)
 repeat_equal=states[0]==states[-1]
finally:lib.EN_close(warm);lib.EN_deleteproject(warm)
result={'runs':summaries,'cold_equal':cold_equal,'repeat_equal':repeat_equal,'demand_changed':summaries[0]['first_positive_demand']!=summaries[2]['first_positive_demand'],'factors_correct':all(r['factor']==r['actual_factor'] for r in summaries),'viscosity_unchanged':all(r['viscosity_unchanged'] for r in summaries)}
if len(sys.argv)>4:
 model=sys.argv[4];tcv=new('tcv')
 try:
  result['zero_setting_tcv']=lib.EN_solveH(tcv)==0 and lib.EN_solveQ(tcv)==0
 finally:lib.EN_close(tcv);lib.EN_deleteproject(tcv)
 if not result['zero_setting_tcv']:sys.exit(1)
out.write_text(json.dumps(result,indent=2));print(json.dumps(result))
if not all(result[k] for k in ('cold_equal','repeat_equal','demand_changed','factors_correct','viscosity_unchanged')):sys.exit(1)
