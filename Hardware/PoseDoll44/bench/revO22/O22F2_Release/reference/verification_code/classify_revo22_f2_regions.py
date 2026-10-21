import json,collections,numpy as np
from build_revo22_fins_v2 import *
plates=json.loads((O/'manifest.json').read_text())['plates'];mesh={};allrows=[];counts=collections.Counter()
for plate in plates:
 q=json.loads((O/'verification'/f"{plate['id']}_extrusion_contacts.json").read_text());items=plate['items'];rows=[]
 for issue in q['floating_printed_components']:
  bb=np.array(issue['bounds_mm']);z=issue['z_mm']-.1;xy=(bb[:2]+bb[2:])/2;it=next((it for it in items if it['fins_bounds_mm'][0]-.5<=xy[0]<=it['fins_bounds_mm'][3]+.5 and it['fins_bounds_mm'][1]-.5<=xy[1]<=it['fins_bounds_mm'][4]+.5),None)
  if not it:rows.append({**issue,'object_name':'unknown','roles':[]});continue
  pid=it['id']
  if pid not in mesh:
   n=np.load(O/'parts'/f'{pid}.npz');mesh[pid]={role:solid(n[vk],n[fk]) for role,vk,fk in [('part','v','f'),('fin','fin_v','fin_f'),('teeth','teeth_v','teeth_f')] if len(n[fk])}
  T=np.c_[np.array(it['rotation_matrix']),it['translation_mm']];region=md.CrossSection.square(bb[2:]-bb[:2]).translate(bb[:2]);areas={role:float((s.transform(T).slice(z)^region).area()) for role,s in mesh[pid].items()};roles=[role for role,a in areas.items() if a>.002];counts['+'.join(roles) or 'none']+=1;rows.append({**issue,'object_name':it['object_name'],'id':pid,'roles':roles,'role_section_bbox_overlap_mm2':areas})
 allrows.append({'plate':plate['id'],'regions':rows})
(O/'verification/remaining_regions.json').write_text(json.dumps({'classification_method':'Bounding rectangle of actual extrusion island intersected with colored role cross-sections at layer midpoint. This localizes candidates; it is not a strength or melt-flow simulation.','counts':dict(counts),'plates':allrows},ensure_ascii=False,indent=2),encoding='utf-8');print('COUNTS',dict(counts),flush=True)
for p in allrows:
 print(p['plate'],[(r.get('id'),round(r['z_mm'],1),r['roles']) for r in p['regions']],flush=True)