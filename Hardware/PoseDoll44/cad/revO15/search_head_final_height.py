from common import *
from carriers_swept import motion_bank
from layout_fullbody import *
from collision_fast import first_cross
rows=[]
for char in ('quinn','manny'):
 bank=motion_bank(char);kind={m['id']:m['kind'] for m in config(char)[1]};raw={name+'/'+k:s for name in ('head','chest','clavicle_l.protract','clavicle_r.protract') for k,s in libraries()[kind[name]][0].items()};pairs={frozenset(('head',x)) for x in ('chest','clavicle_l.protract','clavicle_r.protract')}
 for dz in (0,4,8,12):
  findings=[]
  for label,meta,T in bank:
   pp={}
   for k,s in raw.items():
    M=meta[k]['transform'].copy()
    if k.startswith('head/'):M[:3,3]+=T['chest'][:3,:3]@np.array([0,0,dz-12])
    pp[k]=pose(s,M[:3,:3],M[:3,3])
   hit=first_cross(pp,meta,pairs,skip_same_body=True)
   if hit:findings.append({'case':label,'hit':hit})
  rows.append({'character':char,'head_offset_mm':dz,'cases':len(bank),'findings':findings});print('HEAD',char,dz,'fails',len(findings),findings[:1],flush=True)
save('head_final_height_search.json',{'trials':rows,'scope':'Bare head vs chest and clavicle roots, moving parts only; complete carriers checked later.'})
