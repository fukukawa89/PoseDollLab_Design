from base import *
p,m,pr,st,prov=load_o18();p={k:s for k,s in p.items() if k.startswith(('thigh_l/','thigh_r/','waist/','calf_l/','calf_r/','foot_l/','foot_r/'))};focus={k for k in p if k.startswith(('thigh_l/','thigh_r/'))}
r=g.read(OUT/'hip_mount_refined.json');chosen=next(x for x in r if x['tilt']==60 and x['phase']==90 and x['offset']==0);ov=chosen['overrides']
for row in chosen['cases']:
 print(row['pose'],'worst',row['hits'][:5],flush=True)
cases=g.read(H/'mechanical_manifest/revO_pose_cases.json')['cases'];orig=L.candidates
records=[]
for name in ('sitting','crouch','hip_abduction'):
 a=cases[name];_,_,ss,f,pr=L.build('quinn',a,overrides=ov,geometry=False);T,A=L.fk(pr,a);state=next(x for x in ss if x['id']=='thigh_l');M=np.array(state['F']).T@T[state['parent']][:3,:3].T@T['thigh_l'][:3,:3]@np.array(state['V']);qs=orig(M,120)
 best=[]
 for iq,qraw in enumerate(qs):
  def pick(MM,max_b=95):
   if max_b==120 and np.max(np.abs(M-MM))<1e-7:return np.array([qraw])
   return orig(MM,max_b)
  L.candidates=pick
  placed,tr,ss,f,pr=position(p,m,a,ov);found=overlaps(placed,focus,same_body_meta=m)
  best.append({'raw':qraw.tolist(),'hits':found,'volume':sum(h['overlap_mm3'] for h in found),'fail':f})
 L.candidates=orig
 best.sort(key=lambda b:b['volume']);print('BRANCH',name,'candidates',len(best),'best',[(b['raw'],len(b['hits']),b['volume']) for b in best[:4]],flush=True);records.append({'pose':name,'trials':best})
g.write(OUT/'hip_branch_search.json',records)
