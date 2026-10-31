from base import *
p,m,pr,st,prov=load_o18();p={k:s for k,s in p.items() if k.startswith(('thigh_l/','thigh_r/','waist/','calf_l/','calf_r/','foot_l/','foot_r/'))};focus={k for k in p if k.startswith(('thigh_l/','thigh_r/'))}
cases={k:v for k,v in g.read(H/'mechanical_manifest/revO_pose_cases.json')['cases'].items() if k in ('neutral','sitting','crouch','hip_abduction','kneeling','legs_crossed')};cases['assembly']=g.ASSEMBLY_POSE
_,mods=L.config('quinn');base={s['id']:s for s in mods if s['id'].startswith('thigh_')};results=[]
for label,params in [('baseline',None),('offset14',14),('offset12',12)]+[(str((tilt,phase)),(tilt,phase)) for tilt in (60,75,90) for phase in (-90,180)]:
 ov={}
 for name,s in base.items():
  if params is None:continue
  if isinstance(params,int):ov[name]={'offset_parent_mm':[0,params if name.endswith('_l') else -params,0]};continue
  tilt,phase=params;V=np.array(s['V'])@rot(2,phase);F=V@rot(1,tilt);ov[name]={'F':F.tolist(),'V':V.tolist(),'offset_parent_mm':[0,0,0]}
 rows=[]
 for name,a in cases.items():
  q,tr,states,fail,prof=position(p,m,a,ov);found=overlaps(q,focus,same_body_meta=m)
  rows.append({'pose':name,'fail':fail,'hits':found,'volume':sum(r['overlap_mm3'] for r in found)})
 results.append({'label':label,'overrides':ov,'cases':rows});g.write(OUT/'hip_mount_final_search.json',results)
 print('FINAL SEARCH',label,[(r['pose'],len(r['hits']),round(r['volume'],2),len(r['fail'])) for r in rows],flush=True)
