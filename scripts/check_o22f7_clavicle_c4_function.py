"""Check functional datums and new material against the complete posed assembly."""
from o22f7_animation import *
from build_revo22_assembly import b
import itertools,time
def freeze(s):
 s.volume();return b.b.from_tri_exact(b.g.tri(s))
C=WORK/'structure_revision';x=Build();x.begin(x.g['steps'][3]);leftmount=x.mount.copy();I=np.linalg.inv(leftmount);key='frame/clavicle_l.protract_frame';z=np.load(C/'W005_C4.npz');new={k:b.b.from_tri_exact(z[k]) for k in z.files};combined=freeze(new['root']+new['distal']);world={};meshes={};bounds={};owners={}
for k,o in x.obs.items():
 m=x.scene['meshes'][o['mesh']]
 if o['mesh'] not in meshes:meshes[o['mesh']]=b.b.from_tri_exact(x.verts[m['first']:m['first']+m['count'],:3].reshape(-1,3,3))
 world[k]=b.g.move(meshes[o['mesh']],x.mats[k]);mm=x.meta['meta'][k];owners[k]=('f',mm['body']) if mm['owner']=='rigid_frame' else ('o',mm['module'],mm['owner']);bounds[k]=np.array(list(itertools.product(*zip(world[k].bounding_box()[:3],world[k].bounding_box()[3:]))))
original=b.g.move(world[key],I);root_guard=b.b.cyl(12,-3,16);ep=b.b.L.libraries()['hinge'][0]['base_sensor_half'];bb=np.array(ep.bounding_box());distal_guard=b.g.move(b.b.box(bb[:3]-1,bb[3:]+1),I@x.owners['clavicle_l.elevate','parent']);guards=root_guard+distal_guard
protected={'removed_mm3':max(0.,((original-combined)^guards).volume()),'added_mm3':max(0.,((combined-original)^guards).volume()),'root_bearing_magnet_roi_radius_mm':12,'root_components':b.g.solid_count(new['root']),'distal_components':b.g.solid_count(new['distal']),'body_overlap_mm3':max(0.,(new['root']^new['distal']).volume())};print('DATUMS',protected,flush=True)
added=freeze(combined-original)
for k in ['nut_0','nut_1','screw_0','screw_1']:added=freeze(added+new[k])
added=b.g.move(added,leftmount);f0,o0=kin.owners(x.raw);start=x.raw.copy();own0=f0['clavicle_l.protract_frame'];invown=np.linalg.inv(own0);inverse0={t:np.linalg.inv(f0[t[1]] if t[0]=='f' else o0[t[1:]]) for t in set(owners.values())};addedbb=np.array(list(itertools.product(*zip(added.bounding_box()[:3],added.bounding_box()[3:]))));ks=[k for k in world if k!=key];BBS=np.array([bounds[k] for k in ks]);tokens=list(inverse0);ix=np.array([tokens.index(owners[k]) for k in ks]);poses=[('default',start),('neutral',x.profile['neutral_raw_deg'])]
for rid in ['clavicle_l.protract/r0','clavicle_r.protract/r0','clavicle_l.elevate/r0','clavicle_r.elevate/r0']:
 for a in np.arange(-90,146,5):
  raw=start.copy();raw[rid]=float(a);poses.append((rid+'/'+str(a),raw))
for rid,lim in x.profile['raw_limits_deg'].items():
 for a in lim:
  raw=start.copy();raw[rid]=a;poses.append((rid+'/limit/'+str(a),raw))
rng=np.random.default_rng(20261016)
for i in range(128):poses.append(('combined_'+str(i),{k:float(rng.uniform(*v)) for k,v in x.profile['raw_limits_deg'].items()}))
cache={};new_hits=[];preexisting=[];rows=[];starttime=time.time()
for i,(name,raw) in enumerate(poses):
 ff,oo=kin.owners(raw);mats=np.array([(ff[t[1]] if t[0]=='f' else oo[t[1:]])@inverse0[t] for t in tokens]);own=ff['clavicle_l.protract_frame']@invown;im=np.linalg.inv(own);wc=addedbb@own[:3,:3].T+own[:3,3];lo,hi=wc.min(0),wc.max(0);each=mats[ix];v=np.einsum('nkj,nij->nki',BBS,each[:,:3,:3])+each[:,None,:3,3];mask=np.all(np.minimum(v.max(1),hi+.1)>np.maximum(v.min(1),lo-.1),axis=1);hits=[]
 for ki in np.flatnonzero(mask):
  k=ks[ki];rel=im@each[ki];ck=(k,tuple(np.round(rel,7).flat))
  if ck not in cache:
   s=b.g.move(world[k],rel);v=max(0.,float((added^s).volume()));gap=float(added.min_gap(s,.1));old=max(0.,float((world[key]^s).volume())) if v>.001 or gap<.05 else 0
   cache[ck]={'part':k,'new_overlap_mm3':v,'gap_mm_capped_at_01':gap,'old_frame_overlap_mm3':old}
  rec=dict(cache[ck],pose=name)
  if rec['new_overlap_mm3']>.001 or rec['gap_mm_capped_at_01']<.05:
   hits.append(rec)
   if rec['old_frame_overlap_mm3']>.02:preexisting.append(rec)
   else:new_hits.append(rec)
 rows.append({'pose':name,'hits':hits})
 if i%50==0:print('MOTION',i,len(poses),'new',len(new_hits),'old',len(preexisting),'sec',round(time.time()-starttime),flush=True)
put(C/'W005_C4_function_review.json',{'status':'CANDIDATE_REVIEW','candidate_sha256':sha(C/'W005_C4.npz'),'datums':protected,'pose_count':len(poses),'new_interferences_or_close_contacts':new_hits,'contacts_at_preexisting_same_pair_collisions':preexisting,'pose_records':rows,'unique_solid_checks':len(cache),'passed':not new_hits and protected['removed_mm3']<1e-5 and protected['added_mm3']<1e-5,'physical_strength_tested':False,'continuous_full_motion_certified':False,'scope':'Complete model including electronics, 5-degree clavicle sweeps, every raw-axis endpoint and 128 deterministic combined poses. Same-pair old interferences are listed separately; no entire pose is silently discarded.'})
print('FUNCTION',not new_hits,len(new_hits),len(preexisting),flush=True)
