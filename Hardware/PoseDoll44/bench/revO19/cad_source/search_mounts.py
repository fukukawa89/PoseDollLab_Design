from base import *
p,m,pr,st,prov=load_o18()
# Resolve frames and brackets later. Here compare actual moving hip solids.
p={k:s for k,s in p.items() if k.startswith(('thigh_l/','thigh_r/','waist/','calf_l/','calf_r/','foot_l/','foot_r/'))}
focus={k for k in p if k.startswith(('thigh_l/','thigh_r/'))}
cases={'neutral':{},'assembly':g.ASSEMBLY_POSE,'sit':{'thigh_l.flex':90,'thigh_r.flex':90,'calf_l.flex':90,'calf_r.flex':90},'abduct':{'thigh_l.abduct':45,'thigh_r.abduct':45}}
_,mods=L.config('quinn');base={s['id']:s for s in mods if s['id'].startswith('thigh_')}
cands=[]
for phase in (0,45,90,135):
 for tilt in (0,30,60,75,-30):
  ov={}
  for name,s in base.items():
   V=np.array(s['V'])@rot(2,phase);F=V@rot(1,tilt)
   ov[name]={'F':F.tolist(),'V':V.tolist(),'offset_parent_mm':[0,0,0]}
  cands.append((str((phase,tilt)),ov))
for off in (0,4,8,12):cands.append(('oldF_offset'+str(off),{name:{'offset_parent_mm':[0,off if name.endswith('_l') else -off,0]} for name in base}))
results=[]
for label,ov in cands:
 rows=[]
 for name,a in cases.items():
  q,tr,states,fail,prof=position(p,m,a,ov)
  found=overlaps(q,focus,same_body_meta=m)
  rows.append({'pose':name,'fail':fail,'hits':found,'volume':sum(r['overlap_mm3'] for r in found)})
  if name=='neutral' and sum(r['overlap_mm3'] for r in found)>25:break
 results.append({'label':label,'overrides':ov,'cases':rows})
 print('SEARCH',label,[(r['pose'],len(r['hits']),round(r['volume'],2),len(r['fail'])) for r in rows],flush=True)
 g.write(OUT/'hip_mount_candidates.json',results)
