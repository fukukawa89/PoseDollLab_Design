from base import *
p,m,pr,st,prov=load_o18();p={k:s for k,s in p.items() if k.startswith(('thigh_l/','thigh_r/','waist/','calf_l/','calf_r/','foot_l/','foot_r/'))};focus={k for k in p if k.startswith(('thigh_l/','thigh_r/'))}
cases={k:v for k,v in g.read(H/'mechanical_manifest/revO_pose_cases.json')['cases'].items() if k in ('neutral','sitting','crouch','hip_abduction','kneeling','legs_crossed')};cases['assembly']=g.ASSEMBLY_POSE
_,mods=L.config('quinn');base={s['id']:s for s in mods if s['id'].startswith('thigh_')}
results=[]
for tilt,phase,off in [(x,90,0) for x in (45,50,55,60,65)]+[(60,x,0) for x in (70,80,100,110)]+[(60,90,x) for x in (2,4,6)]:
 ov={}
 for name,s in base.items():
  V=np.array(s['V'])@rot(2,phase);F=V@rot(1,tilt);ov[name]={'F':F.tolist(),'V':V.tolist(),'offset_parent_mm':[0,off if name.endswith('_l') else -off,0]}
 rows=[]
 for name,a in cases.items():
  q,tr,states,fail,prof=position(p,m,a,ov);found=overlaps(q,focus,same_body_meta=m)
  rows.append({'pose':name,'fail':fail,'hits':found,'volume':sum(r['overlap_mm3'] for r in found)})
 results.append({'tilt':tilt,'phase':phase,'offset':off,'overrides':ov,'cases':rows})
 print('REFINE',tilt,phase,off,[(r['pose'],len(r['hits']),round(r['volume'],2),len(r['fail'])) for r in rows],flush=True)
 g.write(OUT/'hip_mount_refined.json',results)
