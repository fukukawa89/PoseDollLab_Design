from base import *
p,m,pr,st,prov=load_o18();p={k:s for k,s in p.items() if k.startswith(('thigh_l/','thigh_r/','waist/','calf_l/','calf_r/','foot_l/','foot_r/'))};focus={k for k in p if k.startswith(('thigh_l/','thigh_r/'))}
cc=g.read(H/'mechanical_manifest/revO_pose_cases.json')['cases'];cases={'assembly':g.ASSEMBLY_POSE,**{k:cc[k] for k in ('hip_abduction','crouch','sitting','neutral','kneeling','legs_crossed')}}
_,mods=L.config('quinn');base={s['id']:s for s in mods if s['id'].startswith('thigh_')};results=[]
for off,axis,deg in [(o,ax,d) for o in (8,12) for ax in (0,1,2) for d in (-10,10)]+[(14,2,d) for d in (-5,5)]:
 ov={name:{'F':(np.array(s['F'])@rot(axis,deg)).tolist(),'offset_parent_mm':[0,off if name.endswith('_l') else -off,0]} for name,s in base.items()};rows=[]
 for name,a in cases.items():
  q,tr,states,fail,prof=position(p,m,a,ov);found=overlaps(q,focus,same_body_meta=m);volume=sum(r['overlap_mm3'] for r in found)
  rows.append({'pose':name,'fail':fail,'hits':found,'volume':volume})
  if fail or volume>.001:break
 results.append({'offset':off,'axis':axis,'deg':deg,'overrides':ov,'cases':rows});g.write(OUT/'hip_mount_compromise.json',results)
 print('COMPROMISE',off,axis,deg,[(r['pose'],len(r['hits']),round(r['volume'],2),len(r['fail'])) for r in rows],flush=True)
