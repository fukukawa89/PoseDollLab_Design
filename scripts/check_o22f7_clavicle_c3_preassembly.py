"""Check C3 in its real, staged left/right chest preassembly context."""
from o22f7_animation import *
from build_revo22_assembly import b
import math,time
C=WORK/'structure_revision';x=Build();x.begin(x.g['steps'][3]);leftmount=x.mount.copy();I=np.linalg.inv(leftmount)
def shape(k):
 o=x.obs[k];m=x.scene['meshes'][o['mesh']];return b.g.move(b.b.from_tri_exact(x.verts[m['first']:m['first']+m['count'],:3].reshape(-1,3,3)),I@x.mats[k])
def matrix(q):
 M=np.eye(4);M[:3,:3]=b.b.rot(0,q[3])@b.b.rot(1,q[4])@b.b.rot(2,q[5]);M[:3,3]=q[:3];return M
checks=[]
def check(name,moving,obstacles,path,frame=None,tol=.001,step=.25):
 frame=np.eye(4) if frame is None else frame;inverse=np.linalg.inv(frame);bo={k:np.array(v.bounding_box()) for k,v in obstacles.items()};radius=max(np.linalg.norm(np.array(s.transform(inverse[:3]).bounding_box()).reshape(2,3),axis=1).max() for s in moving.values());peak=0;samples=0;bad=None
 for i,(a,c) in enumerate(zip(path,path[1:])):
  a=np.array(a,float);c=np.array(c,float);delta=c-a;bound=np.linalg.norm(delta[:3])+radius*np.deg2rad(abs(delta[3:])).sum();n=max(1,math.ceil(bound/step))
  for t in np.linspace(0,1,n+1):
   q=a+delta*t;M=frame@matrix(q)@inverse;samples+=1
   for k,s in moving.items():
    ss=b.g.move(s,M);bb=np.array(ss.bounding_box())
    for fk,f in obstacles.items():
     if np.any(np.minimum(bb[3:],bo[fk][3:])<=np.maximum(bb[:3],bo[fk][:3])+1e-7):continue
     v=max(0.,float((ss^f).volume()));peak=max(peak,v)
     if v>tol:bad={'moving':k,'fixed':fk,'q':q.tolist(),'intersection_mm3':v,'segment':i};break
    if bad:break
   if bad:break
  if bad:break
 rec={'name':name,'passed':bad is None,'maximum_overlap_mm3':peak,'samples':samples,'sample_displacement_upper_bound_mm':step,'overlap_tolerance_mm3':tol,'first_conflict':bad,'path':path,'motion_frame':frame.tolist()};checks.append(rec);print(name,rec['passed'],peak,samples,bad,flush=True);save();return rec

def save():put(C/'W005_C3_preassembly_review.json',{'status':'CANDIDATE_REVIEW','candidate_sha256':sha(C/'W005_C3.npz'),'checks':checks,'physical_assembly_tested':False})
z=np.load(C/'W005_C3.npz');p={k:b.b.from_tri_exact(z[k]) for k in z.files};chest=shape('frame/chest');stock=['M3_nut','M3_reaction_washer','inner_M4_wide','outer_M4_wide','spring_1','spring_2','front_M4_washer','shoulder_D4_L8_M3_thread6'];leftstock={k:shape('clavicle_l.protract/'+k) for k in stock};rightstock={k:shape('clavicle_r.protract/'+k) for k in stock};rootpath=read(C/'proximal_root_escape_candidate.json')['path'];fixed={'chest':chest,**{'left_'+k:v for k,v in leftstock.items() if k in stock[:3]}}
check('left_root_into_bare_chest',{'root':p['root']},fixed,rootpath)
# Put the existing preload hardware in and secure the root before the right frame.
fixed['left_root']=p['root']
for k in stock[3:]:
 check('left_'+k+'_from_axial', {k:leftstock[k]},fixed,[[0,0,0,0,0,0],[0,0,35,0,0,0]])
 fixed['left_'+k]=leftstock[k]
# New lap nuts enter from the open back of their hexagonal sockets.
for k in ['nut_0','nut_1']:
 check(k+'_entry',{k:p[k]},fixed,[[0,0,0,0,0,0],[0,0,30,0,0,0]])
 fixed[k]=p[k]
x.begin(x.g['steps'][10]);rf=I@x.mount;right=shape('frame/clavicle_r.protract_frame')
for k in stock[:3]:fixed['right_'+k]=rightstock[k]
rightpath=read(WORK/'clavicle_right_goal_0_1_path.json')['path']
check('right_frame_with_only_left_root',{'right':right},fixed,rightpath,frame=rf,tol=.02)
fixed['right']=right
# Far left beam closes from above after the right connector is seated.
check('left_distal_after_right',{'distal':p['distal']},fixed,[[0,0,0,0,0,0],[0,0,-110,0,0,0]])
fixed['distal']=p['distal']
for k in ['screw_0','screw_1']:
 check(k+'_entry',{k:p[k]},fixed,[[0,0,0,0,0,0],[0,0,-40,0,0,0]])
 fixed[k]=p[k]
# All new fasteners must be clear of the full model at the final neutral pose.
allfixed={k:shape(k) for k in x.obs if k!='frame/clavicle_l.protract_frame'};allfixed.update(root=p['root'],distal=p['distal'])
for k in ['nut_0','nut_1','screw_0','screw_1']:check(k+'_final_all_parts',{k:p[k]},allfixed,[[0,0,0,0,0,0],[0,0,0,0,0,0]])
