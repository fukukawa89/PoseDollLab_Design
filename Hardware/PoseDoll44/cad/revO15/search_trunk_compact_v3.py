from layout_fullbody import *
from search_adjacent import first_cross
from connected import adjacent_pairs
import copy
cache=read(OUT/'trunk_compact_search_v2.json');waists=[r['overrides']['waist'] for r in cache['individual_valid']['waist']];cc=read(OUT/'trunk_orientation_candidates.json')['groups']['waist']
for az,phase in ((90,0),(270,0),(270,180)):
 c=next(c for c in cc if c['az']==az and c['el']==0 and c['phase']==phase and c['bias']==42);waists.append({'offset_parent_mm':[-12,0,16],'F':c['F'],'V':c['V']})
chests=[r['overrides']['chest'] for r in cache['individual_valid']['chest']];positions=[[0,0,8],[0,0,16],[0,0,24]]+[[x,y,z] for x,y,z in ((8,0,0),(-8,0,0),(16,0,0),(-16,0,0),(24,0,0),(-24,0,0),(32,0,0),(-32,0,0),(0,16,0),(0,-16,0),(0,24,0),(0,-24,0),(16,0,8),(-16,0,8),(24,0,8),(-24,0,8),(16,0,16),(-16,0,16),(24,0,16),(-24,0,16),(0,16,16),(0,-16,16))]
options=[(w,{**c,'offset_parent_mm':pos}) for w,c,pos in itertools.product(waists,chests,positions)];options.sort(key=lambda cc:sum(np.linalg.norm(c['offset_parent_mm']) for c in cc))
prof,_=config('quinn');pairposes=[{}, {'waist.pitch':35,'chest.pitch':25,'waist.yaw':30,'chest.yaw':20}];allposes=list(pairposes);names=('waist','chest','head','clavicle_l','clavicle_r','thigh_l','thigh_r');pairs={p for p in adjacent_pairs('quinn') if p<=set(names)}
for a in prof['axes']:
 if a['id'].split('.')[0] in names:allposes += [{a['id']:float(np.rad2deg(v))} for v in a['limits_rad']]
 if a['id'].split('.')[0] in ('waist','chest'):pairposes += [{a['id']:float(np.rad2deg(v))} for v in a['limits_rad']]
rr=[];inputs={str(p):sha(p) for p in [Path(__file__),Path(__file__).with_name('layout_fullbody.py'),*OUT.glob('*_parts.npz')]}
for w,c in options:
 op={'waist':w,'chest':c};ss=[];ok=True
 for a in pairposes:
  p,m,st,f,_=build('quinn',a,op,only=('waist','chest'));hit=first_cross(p,m);ss.append({'angles':a,'mapping':f,'hit':hit})
  if f or hit:ok=False;break
 if ok:
  print('PAIR_CLEAR',w['offset_parent_mm'],c['offset_parent_mm'],'checking neighbours',flush=True)
  for a in allposes:
   p,m,st,f,_=build('quinn',a,op,only=names);hit=first_cross(p,m,pairs=pairs);ss.append({'angles':a,'mapping':f,'hit':hit})
   if f or hit:ok=False;break
 rr.append({'overrides':op,'pass_all_samples':ok,'samples_checked':len(ss),'last':ss[-1]})
 if len(rr)%100==0 or ok:print('COMPACT_PAIR',len(rr),'pass',ok,'offsets',w['offset_parent_mm'],c['offset_parent_mm'],flush=True);save('trunk_compact_search_v3.json',{'status':'SEARCH_RUNNING','trials':rr,'input_sha256':inputs})
 if ok:break
if any(sha(Path(k))!=v for k,v in inputs.items()):raise RuntimeError('inputs changed')
save('trunk_compact_search_v3.json',{'status':'SEARCH_COMPLETE','trials':rr,'input_sha256':inputs})
