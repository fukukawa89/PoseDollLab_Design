import json,copy,shutil,numpy as np,importlib
from pathlib import Path
from search_revo22_f5_orientation268 import O,put
import stage_revo22_f5_compact296 as stage
S=stage.S;m=json.loads((S/'stage_manifest.json').read_text());p=next(p for p in m['plates']if p['id']=='D12');r=json.loads((S/'plate_results/D12.json').read_text());q=json.loads((S/'candidates/PLATE_D12'/r['label']/'verification/native_final.json').read_text());lock=[]
for q in q['external_islands']+q['critical_external_runs']:
 b=q['bounds_mm'];x,y=(b[0]+b[2])/2,(b[1]+b[3])/2
 for i in p['items']:
  c=i['bounds_mm']
  if c[0]<=x<=c[3]and c[1]<=y<=c[4]:lock.append(i['id']);print('D12_LOCK',i['id'],i['rotation_z_deg'],flush=True)
p=Path(stage.__file__);s=p.read_text(encoding='utf-8-sig');s=s.replace("'P115','P049']else[0,1]","'P115','P049',"+','.join(repr(x)for x in lock)+"]else[0,1]");s=s.replace("it['id']!='X062'","it['id']not in ['X062','P130']");p.write_text(s,encoding='utf-8');importlib.reload(stage)
for pid,label in [('P130',json.loads((O/'selections/P130.json').read_text())['label']),('X046','contact423')]:
 for sub,ext in [('parts','npz'),('design','json')]:shutil.copy2(O/'candidates'/pid/label/sub/f'{pid}.{ext}',S/sub/f'{pid}.{ext}')
fixed=[];pending=[]
for p in m['plates']:
 if p['id']in ['D02','D03','D05','D06','D14']:fixed.append(p);continue
 for old in p['items']:
  it=copy.deepcopy(old);pid=it['id'];n=np.load(S/'parts'/f'{pid}.npz');v=np.r_[n['v'],n['fin_v'],n['teeth_v']];d=json.loads((S/'design'/f'{pid}.json').read_text());it.update(source_profile=dict(layer=d.get('required_layer_height_mm',.2),initial=d.get('required_initial_layer_height_mm',.2),wall=d.get('required_wall_generator','arachne'),overrides=d.get('required_process_overrides',{}),height_overrides=d.get('required_layer_ranges',[]),fuse=True),local_bounds_mm=np.r_[v.min(0),v.max(0)].tolist(),size=np.ptp(v,axis=0).tolist());it.pop('finer_layer_for_compact_layout',None);it.pop('single_part_validated_profile',None);pending.append(it)
best=None
for gap in [6.,5.,4.]:
 stage.GAP=gap;stage.LIMIT=172+gap
 for seed in range(1600):
  ps=stage.pack(pending,seed);score=(len(ps),sum(bool(i.get('finer_layer_for_compact_layout'))for p in ps for i in p['items']))
  if best is None or score<best[0]:best=(score,ps,seed,gap);print('PACK433_BEST',score,seed,gap,flush=True)
 if best[0][0]<=9:break
assert best[0][0]<=9,('too many',best[0]);ids=[p['id']for p in m['plates']if p not in fixed];out=list(fixed)
for pid,pp in zip(ids,best[1]):
 for k,it in enumerate(pp['items'],1):
  name=f'{pid}-{k:02} '+it['id']+' '+it['part']+(' [可选小样]'if it['optional_sample']else'');it.update(number=k,object_name=name,native_internal_object_name=name)
 out.append(dict(id=pid,title='O22-F5 稀疏支撑合盘主套',optional=False,items=pp['items'],profile=dict(layer=pp['layer'],initial=pp['initial'],wall='arachne',overrides={},fuse=True)))
out.sort(key=lambda p:p['id']);gaps=[];edges=[]
for p in out:
 for k,i in enumerate(p['items']):
  b=np.array(i['bounds_mm']);assert min(b[:2])>=4-1e-6 and max(b[3:5])<=176+1e-6;edges.append(min(*b[:2],*(180-b[3:5])))
  for j in p['items'][k+1:]:
   c=np.array(j['bounds_mm']);gap=float(np.linalg.norm(np.maximum(np.maximum(b[:2]-c[3:5],c[:2]-b[3:5]),0)));assert gap>=best[3]-1e-6;gaps.append(gap)
put(S/'layout_before433.json',m);m.update(plates=out,after_main_plates=len(out),minimum_model_edge_margin_mm=min(edges),minimum_combined_body_fin_teeth_bbox_gap_mm=min(gaps),rotation_repair=dict(seed=best[2],gap=best[3],kept_qualified_plates=[p['id']for p in fixed]));put(S/'stage_manifest.json',m);print('PACK433_DONE',[(p['id'],len(p['items']),p['profile']['layer'])for p in out],flush=True)
