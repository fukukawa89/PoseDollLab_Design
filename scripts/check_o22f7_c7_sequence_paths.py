"""Verify the actual exported C7 assembly sequence at changed interfaces."""
from build_o22f7_c7_animation import Revised,C,prekeys,read,put,sha,a
from build_revo22_assembly import b
import numpy as np,math
x=Revised();seq=read(a.OUT/'sequence.json');obs=list(x.obs);seen=set();delta={};cache={};rows=[]
def Q(q):
 M=np.eye(4);M[:3,:3]=b.b.rot(0,q[3])@b.b.rot(1,q[4])@b.b.rot(2,q[5]);M[:3,3]=q[:3];return M
def pose(act,q):
 if 'pose_path' not in act:M=np.eye(4);M[:3,3]=q;return M
 T=np.eye(4);T[:3,3]=act['station'];return T@np.array(act['motion_frame']).reshape(4,4)@Q(q)@np.array(act['motion_frame_inverse']).reshape(4,4)
def mesh(i):
 o=x.obs[obs[i]];m=x.scene['meshes'][o['mesh']]
 if o['mesh'] not in cache:cache[o['mesh']]=b.b.from_tri_exact(x.verts[m['first']:m['first']+m['count'],:3].reshape(-1,3,3))
 return cache[o['mesh']]
chapter=None
for act in seq['actions']:
 if act['chapter'] not in ['S01','S02','S03']:break
 if chapter!=act['chapter']:chapter=act['chapter'];x.begin(next(s for s in x.g['steps'] if s['step']==chapter))
 if act.get('raw_overrides'):x.set_raw(act['raw_overrides'])
 seen.update(act['new']);moving=act['moving'];select=(chapter=='S02' and (act.get('verified_path') in ['nut_0','left_distal_after_right','screw_0_entry'] or act['kind']=='transfer')) or(chapter=='S03' and act['kind']=='transfer' and '近端半壳' in act['title'])
 if select and moving:
  fixedids=[i for i in seen if i not in moving];fixed=[b.g.move(mesh(i),delta.get(i,np.eye(4))@x.mats[obs[i]]) for i in fixedids];bounds=np.array([s.bounding_box() for s in fixed]);base={i:b.g.move(mesh(i),x.mats[obs[i]]) for i in moving};path=act.get('pose_path',act['path']);radius=max(np.linalg.norm(np.array(s.bounding_box()).reshape(2,3),axis=1).max() for s in base.values());peak=0.;samples=0;hit=None
  for pa,pb in zip(path,path[1:]):
   pa=np.array(pa);pb=np.array(pb);dp=pb-pa;n=max(1,math.ceil((np.linalg.norm(dp[:3])+(radius*np.deg2rad(abs(dp[3:])).sum() if len(dp)==6 else 0))/.25))
   for t in np.linspace(0,1,n+1):
    M=pose(act,pa+dp*t);samples+=1
    for i,shape in base.items():
     s=b.g.move(shape,M);bb=np.array(s.bounding_box());candidates=np.where(np.all(np.minimum(bb[3:],bounds[:,3:])>np.maximum(bb[:3],bounds[:,:3])+1e-6,axis=1))[0]
     for j in candidates:
      v=float((s^fixed[j]).volume());peak=max(peak,v)
      if v>.02:hit={'moving':obs[i],'fixed':obs[fixedids[j]],'overlap_mm3':v,'q':(pa+dp*t).tolist()};break
     if hit:break
    if hit:break
   if hit:break
  row={'id':act['id'],'title':act['title'],'passed':hit is None,'samples':samples,'moving_count':len(moving),'fixed_count':len(fixed),'maximum_overlap_mm3':peak,'hit':hit};rows.append(row);put(C/'W005_C7_sequence_interfaces.json',{'sequence_sha256':sha(a.OUT/'sequence.json'),'checks':rows,'sampling_mm':.25,'overlap_tolerance_mm3':.02});print(row,flush=True)
 for i in moving:delta[i]=pose(act,act.get('pose_path',act['path'])[-1])
print('DONE',all(r['passed'] for r in rows),flush=True)
