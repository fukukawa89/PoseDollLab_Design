"""Check the candidate right motion with left clavicle parked at reachable joint angles."""
from o22f7_animation import *
from build_revo22_assembly import b
import time
x=Build();st=x.g['steps'][3];x.begin(st);I=np.linalg.inv(x.mount);left='frame/clavicle_r.protract_frame';leftmod='clavicle_r.protract';keys=[left]+[leftmod+'/'+s for s in ['M3_nut','M3_reaction_washer','inner_M4_wide','outer_M4_wide','spring_1','spring_2','front_M4_washer','shoulder_D4_L8_M3_thread6']]
def mesh(k):
 o=x.obs[k];m=x.scene['meshes'][o['mesh']];return b.b.from_tri_exact(x.verts[m['first']:m['first']+m['count'],:3].reshape(-1,3,3))
base={k:mesh(k) for k in [*keys,'frame/chest','frame/clavicle_l.protract_frame']};chest=b.g.move(base['frame/chest'],I@x.mats['frame/chest']);moving=b.g.move(base['frame/clavicle_l.protract_frame'],I@x.mats['frame/clavicle_l.protract_frame']);path=np.array(read(WORK/'clavicle_corner_x_progress.json')['best_path']);samples=[path[0]]
for p,q in zip(path,path[1:]):
 n=max(1,int(np.ceil(np.linalg.norm((q-p)*[1,1,1,1.7,1.7,1.7])/2)))
 samples.extend(p+(q-p)*t for t in np.arange(1,n+1)/n)
def at(k,raw):
 ff,oo=kin.owners(raw);mm=x.meta['meta'][k];o=ff[mm['body']] if mm['owner']=='rigid_frame' else oo[mm['module'],mm['owner']];return b.g.move(base[k],I@o@np.array(x.bind[x.idx[k]]['local']).reshape(4,4))
rows=[];tic=time.time()
for angle in [0,-10,-20,-30,-40,-50,-60,-75,-90,10,20,30,45,60,90]:
 raw=dict(x.raw);raw[leftmod+'/r0']=angle;rotation_peak=0
 for a in np.linspace(0,angle,max(2,int(abs(angle)/2)+1)):
  rr=dict(raw);rr[leftmod+'/r0']=float(a);rotation_peak=max(rotation_peak,float((at(left,rr)^chest).volume()))
  if rotation_peak>.02:break
 if rotation_peak>.02:row={'angle':angle,'left_rotation_clear':False,'overlap_mm3':rotation_peak};rows.append(row);print(row,flush=True);continue
 fixed=[at(k,raw) for k in keys];bb=[np.array(f.bounding_box()) for f in fixed];failure=None
 for si,q in enumerate(samples):
  M=np.eye(4);M[:3,:3]=b.b.rot(0,q[3])@b.b.rot(1,q[4])@b.b.rot(2,q[5]);M[:3,3]=q[:3];s=b.g.move(moving,M);bo=np.array(s.bounding_box())
  for k,f,bbox in zip(keys,fixed,bb):
   if np.any(np.minimum(bo[3:],bbox[3:])<=np.maximum(bo[:3],bbox[:3])+1e-6):continue
   v=float((s^f).volume())
   if v>.02:failure={'sample':si,'part':k,'overlap_mm3':v};break
  if failure:break
 row={'angle':angle,'left_rotation_clear':True,'right_path_clear':failure is None,'failure':failure,'sample_count':len(samples)};rows.append(row);put(WORK/'left_partial_path_right_parked_review.json',{'checks':rows,'scope':'candidate sampled screening, not final validation'});print(row,'seconds',round(time.time()-tic),flush=True)
put(WORK/'left_partial_path_right_parked_review.json',{'checks':rows,'scope':'candidate sampled screening, not final validation'})

