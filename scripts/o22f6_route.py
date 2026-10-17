"""Route only outside F6 fastener clearances; preserve existing plate envelopes."""
from pathlib import Path
import sys,json,copy,shutil,hashlib
import numpy as np
from o22f6_holeclear import SRC,OUT,WORK,R,put,sha

def collect():
 m=json.loads((SRC/'manifest.json').read_text());byid={};origins={}
 for p in m['plates']:
  fp=WORK/f"plates/{p['id']}/support_paths.json"
  if not fp.exists():continue
  r=json.loads(fp.read_text())
  for kind in ['external_islands','critical_external_runs']:
   for q in r[kind]:
    bb=q['bounds_mm'];pt=np.array([(bb[0]+bb[2])/2,(bb[1]+bb[3])/2,q['z_mm']]);matches=[it for it in p['items']if it['bounds_mm'][0]-.01<=pt[0]<=it['bounds_mm'][3]+.01 and it['bounds_mm'][1]-.01<=pt[1]<=it['bounds_mm'][4]+.01];assert len(matches)==1,(p['id'],q,matches)
    it=matches[0];pid=it['id'];rot=np.array(it['rotation_matrix']);t=np.array(it['translation_mm']);qq=copy.deepcopy(q);corn=np.array([[x,y,q['z_mm']]for x in[bb[0],bb[2]]for y in[bb[1],bb[3]]]);corn=(corn-t)@rot;qq['bounds_mm']=[*corn[:,:2].min(0),*corn[:,:2].max(0)];qq['z_mm']=float(corn[0,2])
    if 'xy_mm'in qq:
     v=np.c_[qq['xy_mm'],np.full(len(qq['xy_mm']),q['z_mm'])];qq['xy_mm']=((v-t)@rot)[:,:2].tolist()
    rr=byid.setdefault(pid,dict(external_islands=[],critical_external_runs=[]));rr[kind].append(qq);origins.setdefault(pid,set()).add(p['id'])
 return byid,origins

def prepare_and_route(ids=None):
 from o22f6_holeclear import solid
 import types
 code=(R/'scripts/route_revo22_f5_native272.py').read_text()
 code=code.replace("for q in rootrecs+records}", "for q in rootrecs+records if 'root'in q}")
 code=code.replace("if(core^s).volume()>1e-7:rr['core_body']+=1;continue", "if np.any(np.array(core.bounding_box())[:3]<limits[:3]-1e-6)or np.any(np.array(core.bounding_box())[3:]>limits[3:]+1e-6):rr['plate_envelope']+=1;continue\n      if(core^s).volume()>1e-7:rr['core_body']+=1;continue")
 code=code.replace("report=json.loads((old/'verification/native_final.json').read_text());", "reference=np.load(F5/'parts'/f'{pid}.npz'); vv=np.r_[reference['v'],reference['fin_v'],reference['teeth_v']];limits=np.r_[vv.min(0),vv.max(0)]; report=json.loads((old/'verification/native_final.json').read_text());")
 module=types.ModuleType('f6_external_router');exec(compile(code,'f6_external_router','exec'),module.__dict__);module.O=WORK;module.F5=SRC
 reports,origins=collect();rows=[];fine='--fine'in (ids or []);ids=[x for x in (ids or [])if x!='--fine']
 for pid,report in reports.items():
  if ids and pid not in ids:continue
  base=OUT
  digest=hashlib.sha256((json.dumps(report,sort_keys=True)+sha(base/f'parts/{pid}.npz')).encode()).hexdigest()[:10];src='clean_'+digest;label=('fine_'if fine else'outside_')+digest;folder=WORK/f'candidates/{pid}/{src}'
  for sub in['parts','design','verification','projects']:(folder/sub).mkdir(parents=True,exist_ok=True)
  shutil.copy2(base/f'parts/{pid}.npz',folder/f'parts/{pid}.npz');d=json.loads((base/f'design/{pid}.json').read_text());d.setdefault('new_tooth_count',len(d.get('teeth',[]))+len(d.get('local_route_repairs',[])));put(folder/f'design/{pid}.json',d);shutil.copy2(WORK/f'guards/{pid}.npz',folder/'verification/guards.npz');put(folder/'verification/native_final.json',report);put(folder/'verification/plate_manifest.json',dict(items=[dict(rotation_matrix=np.eye(3).tolist(),translation_mm=[0,0,0])]))
  result=module.run(pid,src,label,tip_width=.45 if fine else None);row=dict(id=pid,label=label,origin_plates=sorted(origins[pid]),remaining_targets=result['unrouted_native_targets'],added_records=result['new_tooth_count']-d['new_tooth_count']);rows.append(row);put(WORK/f'routes/{pid}.json',row);print('ROUTE_RESULT',pid,row['added_records'],len(row['remaining_targets']),flush=True)
 put(WORK/'routing_progress.json',rows)

if __name__=='__main__':prepare_and_route(sys.argv[1:])