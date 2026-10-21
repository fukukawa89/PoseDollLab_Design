"""Dense independent recheck of a candidate rigid path, never a release certificate."""
from o22f7_animation import *
from build_revo22_assembly import b
import time,itertools
x=Build();x.begin(x.g['steps'][10]);key='frame/'+x.st['child'];inv=np.linalg.inv(x.mount)
raw=dict(x.raw);raw['clavicle_l.protract/r0']=-20;ff,oo=kin.owners(raw)
for k in x.mats:
 mm=x.meta['meta'][k]
 if 'clavicle_l.protract' in k:
  owner=ff[mm['body']] if mm['owner']=='rigid_frame' else oo[mm['module'],mm['owner']];x.mats[k]=owner@np.array(x.bind[x.idx[k]]['local']).reshape(4,4)
def shape(k):
 o=x.obs[k];m=x.scene['meshes'][o['mesh']];return b.g.move(b.b.from_tri_exact(x.verts[m['first']:m['first']+m['count'],:3].reshape(-1,3,3)),inv@x.mats[k])
moving=shape(key);keys=['frame/chest',x.st['id']+'/M3_nut',x.st['id']+'/M3_reaction_washer',x.st['id']+'/inner_M4_wide'];keys+=['frame/clavicle_l.protract_frame']+['clavicle_l.protract/'+tail for tail in ['M3_nut','M3_reaction_washer','inner_M4_wide','outer_M4_wide','spring_1','spring_2','front_M4_washer','shoulder_D4_L8_M3_thread6']];fixed=[shape(k) for k in keys];bounds=[np.array(f.bounding_box()) for f in fixed];lo,hi=np.array(moving.bounding_box()).reshape(2,3);radius=max(np.linalg.norm(v) for v in itertools.product(*zip(lo,hi)));path=read(WORK/'clavicle_right_parked_left_goal_0_1_path.json')['path'];count=0;peak=0;bad=[];tic=time.time()
for seg,(pp,qq) in enumerate(zip(path,path[1:])):
 p=np.array(pp);q=np.array(qq);n=max(1,int(np.ceil((np.linalg.norm(q[:3]-p[:3])+radius*np.abs(q[3:]-p[3:]).sum()*np.pi/180)/.25)))
 for t in np.arange(n+1)/n:
  r=p+(q-p)*t;M=np.eye(4);M[:3,:3]=b.b.rot(0,r[3])@b.b.rot(1,r[4])@b.b.rot(2,r[5]);M[:3,3]=r[:3];s=b.g.move(moving,M);bb=np.array(s.bounding_box());count+=1
  for k,f,bo in zip(keys,fixed,bounds):
   if np.any(np.minimum(bb[3:],bo[3:])<=np.maximum(bb[:3],bo[:3])+1e-6):continue
   v=float((s^f).volume());peak=max(peak,v)
   if v>.02:bad.append({'segment':seg,'fraction':float(t),'pose':arr(r),'obstacle':k,'overlap_mm3':v});print('FAIL',bad[-1],flush=True);break
  if len(bad)>=15:break
 if len(bad)>=15:break
put(WORK/'right_parked_left_dense_review.json',{'passed':not bad,'samples':count,'max_sample_displacement_bound_mm':.25,'max_overlap_mm3':peak,'tolerance_mm3':.02,'failures':bad,'seconds':time.time()-tic,'all_context_included':False,'physical_tested':False});print('DONE',count,'bad',len(bad),'peak',peak,'seconds',time.time()-tic,flush=True)

