import json,copy,numpy as np
from search_revo22_f5_orientation268 import O,put
from stage_revo22_f5_compact296 import S,EDGE,GAP,LIMIT
from pack_revo22_a1mini import split_free
m=json.loads((S/'stage_manifest.json').read_text());old=copy.deepcopy(m);p=next(p for p in m['plates']if p['id']=='D01');moving=[i for i in p['items']if i['number']in [5,6,7]];p['items']=[i for i in p['items']if i['number']not in [5,6,7]];targets=[next(p for p in m['plates']if p['id']==pid)for pid in ['D13','D12','D11','D10','D09','D08']];free={}
for pp in targets:
 fr=[(0.,0.,178.,178.)]
 for i in pp['items']:
  b=i['bounds_mm'];fr=split_free(fr,(b[0]-EDGE,b[1]-EDGE,b[3]-b[0]+GAP,b[4]-b[1]+GAP))
 free[pp['id']]=fr
changes={'D01'}
for i in sorted(moving,key=lambda i:-np.prod(i['size'][:2])):
 i['source_profile']=i.pop('single_part_validated_profile');i.pop('finer_layer_for_compact_layout',None);best=None
 for pi,pp in enumerate(targets):
  for x,y,w,h in free[pp['id']]:
   iw,ih=np.array(i['size'][:2])+GAP
   if iw>w+1e-6 or ih>h+1e-6:continue
   sc=(pi,min(w-iw,h-ih),max(w-iw,h-ih),y,x)
   if best is None or sc<best[0]:best=(sc,pp,x,y,iw,ih)
 assert best,('NO_SPACE',i['id'],i['size'])
 _,pp,x,y,iw,ih=best;fr=free[pp['id']];free[pp['id']]=split_free(fr,(x,y,iw,ih));lo=np.array(i['local_bounds_mm'][:3]);hi=np.array(i['local_bounds_mm'][3:]);delta=np.array([x+EDGE,y+EDGE,0])-lo;bb=np.r_[lo+delta,hi+delta];i.update(rotation_matrix=np.eye(3).tolist(),rotation_z_deg=0,translation_mm=delta.tolist(),bounds_mm=bb.tolist(),fins_bounds_mm=bb.tolist(),x=x+EDGE,y=y+EDGE,w=iw-GAP,h=ih-GAP);pp['items'].append(i);changes.add(pp['id']);print('MOVE444',i['id'],i['original_object_name'],pp['id'],bb.tolist(),flush=True)
for pp in m['plates']:
 if pp['id']in changes:
  for k,i in enumerate(pp['items'],1):
   name=f"{pp['id']}-{k:02} "+i['id']+' '+i['part']+(' [可选小样]'if i['optional_sample']else'');i.update(number=k,object_name=name,native_internal_object_name=name)
 for idx,i in enumerate(pp['items']):
  b=np.array(i['bounds_mm']);assert min(b[:2])>=4-1e-6 and max(b[3:5])<=176+1e-6
  for j in pp['items'][idx+1:]:
   c=np.array(j['bounds_mm']);assert np.linalg.norm(np.maximum(np.maximum(b[:2]-c[3:5],c[:2]-b[3:5]),0))>=6-1e-6
put(S/'layout_before444.json',old);m['status']='All 150 types frozen; final whole-plate audits in progress';put(S/'stage_manifest.json',m);put(S/'modified_plates444.json',sorted(changes));print('CHANGED444',sorted(changes),flush=True)
