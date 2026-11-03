"""Compare the opt-in reader against WNTR 1.4.0 across binary output modes."""
import json, os, sys, tempfile, struct
from pathlib import Path
import numpy as np
import wntr
from wntr.epanet.io import BinFile
root=Path(__file__).resolve().parent
sys.path.insert(0, str(root.parent / "examples"))
from fast_wntr_reader import FastBinFile
upstream=Path(os.environ.get("EPANET_TURBO_UPSTREAM_NETS",root.parent/"examples"))
tmp=tempfile.TemporaryDirectory(prefix="epanet-wntr-test-",dir=os.environ.get("EPANET_TURBO_TEST_DIR"))
out=Path(tmp.name)
assert wntr.__version__=='1.4.0'

def compare(a,b):
 assert a.error_code==b.error_code
 for group in ('node','link'):
  aa=getattr(a,group);bb=getattr(b,group)
  assert set(aa)==set(bb)
  for key in aa:
   x=aa[key];y=bb[key]
   assert x.index.equals(y.index) and x.columns.equals(y.columns)
   assert x.index.names==y.index.names and x.columns.names==y.columns.names
   assert np.array_equal(x.dtypes.to_numpy(),y.dtypes.to_numpy())
   np.testing.assert_array_equal(x.to_numpy(),y.to_numpy())

cases=[('Net1','NONE','NONE'),('Net1','AGE','NONE'),('Net1','CHEMICAL','NONE'),('Net1','TRACE','NONE'),('Net2','NONE','NONE'),('Net3','AGE','NONE'),('Net1','NONE','AVERAGED'),('Net1','NONE','MINIMUM'),('Net1','NONE','MAXIMUM'),('Net1','NONE','RANGE'),('Net2','NONE','D-W')]
rows=[]
for name,quality,stat in cases:
 wn=wntr.network.WaterNetworkModel(str(upstream/(name+'.inp')))
 wn.options.quality.parameter=quality
 if stat=='D-W':wn.options.hydraulic.headloss='D-W'
 else:wn.options.time.statistic=stat
 if quality=='TRACE':wn.options.quality.trace_node=wn.reservoir_name_list[0]
 if quality=='CHEMICAL':
  for _,node in wn.nodes():node.initial_quality=0.0002
  for _,node in wn.reservoirs():node.initial_quality=0.001
 prefix=out/(name+'-'+quality+'-'+stat)
 sim=wntr.sim.EpanetSimulator(wn)
 simulation_error=None
 try:
  sim.run_sim(file_prefix=str(prefix),version=2.2)
 except Exception as exc:
  if stat!='AVERAGED':raise
  simulation_error=(type(exc).__name__,str(exc))
 path=str(prefix)+'.bin'
 assert Path(path).is_file() and Path(path).stat().st_size > 0
 if (name,quality,stat)==('Net1','NONE','NONE'):
  # EPANET output stores IDs in fixed-width 32-byte slots.
  binary=bytearray(Path(path).read_bytes());num_nodes=struct.unpack_from('=i',binary,8)[0]
  offset=15*4+240+260+260+2*32
  for position,identifier in ((offset,'A'*31),(offset+num_nodes*32,'水闸-01')):
   encoded=identifier.encode('utf-8');binary[position:position+32]=encoded.ljust(32,b'\x00')
  modified=out/'id-boundaries.bin';modified.write_bytes(binary)
  left=BinFile().read(str(modified));right=FastBinFile().read(str(modified));compare(left,right)
  assert 'A'*31 in right.node['pressure'].columns and '水闸-01' in right.link['flowrate'].columns
  rows.append({'model':name,'case':'31-byte and Unicode IDs','outcome':'exact'})
 if stat=='AVERAGED':
  outcomes=[]
  for reader in (BinFile(), FastBinFile()):
   try:outcomes.append((reader.read(path),None))
   except Exception as exc:outcomes.append((None,(type(exc).__name__,str(exc))))
  assert outcomes[0][1]==outcomes[1][1]==simulation_error, outcomes
  if simulation_error:
   rows.append({'model':name,'quality':quality,'statistics':stat,'outcome':'same WNTR exception','exception':simulation_error[0]})
   print(name,quality,stat,'baseline and fast reader raise same exception',flush=True)
   continue
 for convert in (False,True):
  for status in (False,True):
   standard=BinFile(convert_status=status);fast=FastBinFile(convert_status=status)
   a=standard.read(path,convert=convert,darcy_weisbach=(stat=='D-W'));b=fast.read(path,convert=convert,darcy_weisbach=(stat=='D-W'))
   compare(a,b)
   for attr in ('node_names','link_names','report_times','flow_units','pres_units','mass_units','quality_type','num_nodes','num_tanks','num_links','num_pumps','num_valves','duration','report_start','report_step','peak_energy','averages'):
    x=getattr(standard,attr);y=getattr(fast,attr)
    if isinstance(x,np.ndarray):np.testing.assert_array_equal(x,y)
    else:assert x==y,(attr,x,y)
   rows.append({'model':name,'quality':quality,'statistics':stat,'convert':convert,'convert_status':status,'steps':len(a.node['pressure']),'quality_max':float(a.node['quality'].to_numpy().max())})
 print(name,quality,stat,'passed',flush=True)
if os.environ.get('EPANET_TURBO_TEST_REPORT'):
 Path(os.environ['EPANET_TURBO_TEST_REPORT']).write_text(json.dumps({'wntr':wntr.__version__,'comparison':'all result values, names, times, dtypes, metadata, energy and averages','rows':rows},indent=2))
tmp.cleanup()
