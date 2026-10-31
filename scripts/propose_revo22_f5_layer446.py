import json,copy,numpy as np,importlib
from pathlib import Path
from search_revo22_f5_orientation268 import O,put
import stage_revo22_f5_compact296 as stage
S=stage.S;m=json.loads((S/'stage_manifest.json').read_text());p=next(p for p in m['plates']if p['id']=='D09');r=json.loads((S/'plate_results/D09.json').read_text());q=json.loads((S/'candidates/PLATE_D09'/r['label']/'verification/native_final.json').read_text());lock=[]
for q in q['external_islands']+q['critical_external_runs']:
 b=q['bounds_mm'];x,y=(b[0]+b[2])/2,(b[1]+b[3])/2
 for i in p['items']:
  c=i['bounds_mm']
  if c[0]<=x<=c[3]and c[1]<=y<=c[4]:lock.append(i['id']);print('LOCK446',i['id'],i['rotation_z_deg'],q['z_mm'],flush=True)
p=Path(stage.__file__);s=p.read_text(encoding='utf-8-sig');s=s.replace("'P049','P071']else[0,1]","'P049','P071',"+','.join(repr(x)for x in lock)+"]else[0,1]")
s=s.replace("it['id']not in ['X062','P130'] and (it.get('has_fins') is False or it['size'][2]<40 or it.get('optional_sample',False))","it['id']in ['N004','X045','P013','P045','X081']")
p.write_text(s,encoding='utf-8');importlib.reload(stage)
ids=['D01','D09','D11','D12','D13'];items=[]
for p in m['plates']:
 if p['id']not in ids:continue
 for old in p['items']:
  i=copy.deepcopy(old);nn=np.load(S/'parts'/f"{i['id']}.npz");vv=np.r_[nn['v'],nn['fin_v'],nn['teeth_v']];i.update(size=np.ptp(vv,axis=0).tolist(),local_bounds_mm=np.r_[vv.min(0),vv.max(0)].tolist());d=json.loads((S/'design'/f"{i['id']}.json").read_text());i['source_profile']=dict(layer=d.get('required_layer_height_mm',.2),initial=d.get('required_initial_layer_height_mm',.2),wall=d.get('required_wall_generator','arachne'),overrides=d.get('required_process_overrides',{}),height_overrides=d.get('required_layer_ranges',[]),fuse=True);i.pop('finer_layer_for_compact_layout',None);i.pop('single_part_validated_profile',None);items.append(i)
best=None
for gap in [6.,5.,4.]:
 stage.GAP=gap;stage.LIMIT=172+gap
 for seed in range(1800):
  ps=stage.pack(items,seed);score=(len(ps),sum(bool(i.get('finer_layer_for_compact_layout'))for p in ps for i in p['items']))
  if best is None or score<best[0]:best=(score,ps,seed,gap);print('PACK446_BEST',score,seed,gap,flush=True)
 if best[0][0]<=5:break
assert best[0][0]<=5,best[0];out=[p for p in m['plates']if p['id']not in ids]
for pid,pp in zip(ids,best[1]):
 for k,i in enumerate(pp['items'],1):
  name=f'{pid}-{k:02} '+i['id']+' '+i['part']+(' [可选小样]'if i['optional_sample']else'');i.update(number=k,object_name=name,native_internal_object_name=name)
 out.append(dict(id=pid,title='O22-F5 稀疏支撑合盘主套',optional=False,items=pp['items'],profile=dict(layer=pp['layer'],initial=pp['initial'],wall='arachne',overrides={},fuse=True)))
out.sort(key=lambda p:p['id']);gaps=[]
for p in out:
 for k,i in enumerate(p['items']):
  b=np.array(i['bounds_mm']);assert min(b[:2])>=4-1e-6 and max(b[3:5])<=176+1e-6
  for j in p['items'][k+1:]:
   c=np.array(j['bounds_mm']);g=float(np.linalg.norm(np.maximum(np.maximum(b[:2]-c[3:5],c[:2]-b[3:5]),0)));assert g>=best[3]-1e-6;gaps.append(g)
m.update(plates=out,minimum_combined_body_fin_teeth_bbox_gap_mm=min(gaps),layer_repair=dict(seed=best[2],gap=best[3],modified_plates=ids));put(S/'proposed_layout446.json',m);print('PACK446_DONE',[(p['id'],len(p['items']))for p in out],flush=True)
