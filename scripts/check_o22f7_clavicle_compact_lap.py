"""Validate candidate bodies and assembly moves; no release side effects."""
from o22f7_animation import *
from build_revo22_assembly import b
import math,time
C=WORK/'structure_revision';x=Build();x.begin(x.g['steps'][3]);I=np.linalg.inv(x.mount)
def shape(k):
 o=x.obs[k];m=x.scene['meshes'][o['mesh']];return b.g.move(b.b.from_tri_exact(x.verts[m['first']:m['first']+m['count'],:3].reshape(-1,3,3)),I@x.mats[k])
fixed={k:shape(k) for k in ['frame/chest']+['clavicle_l.protract/'+t for t in ['M3_nut','M3_reaction_washer','inner_M4_wide']]};allfixed={k:shape(k) for k in x.obs if k!='frame/clavicle_l.protract_frame'}
def matrix(q):
 M=np.eye(4);M[:3,:3]=b.b.rot(0,q[3])@b.b.rot(1,q[4])@b.b.rot(2,q[5]);M[:3,3]=q[:3];return M

def check(name,moving,obstacles,path,tol=.02,step=.25):
 bo={k:np.array(v.bounding_box()) for k,v in obstacles.items()};radius=max(np.linalg.norm(np.array(s.bounding_box()).reshape(2,3),axis=1).max() for s in moving.values());peak=0;samples=0;bad=None
 for i,(a,c) in enumerate(zip(path,path[1:])):
  a=np.array(a,float);c=np.array(c,float);delta=c-a;bound=np.linalg.norm(delta[:3])+radius*np.deg2rad(abs(delta[3:])).sum();n=max(1,math.ceil(bound/step))
  for t in np.linspace(0,1,n+1):
   q=a+delta*t;M=matrix(q);samples+=1
   for k,s in moving.items():
    ss=b.g.move(s,M);bb=np.array(ss.bounding_box())
    for fk,f in obstacles.items():
     if np.any(np.minimum(bb[3:],bo[fk][3:])<=np.maximum(bb[:3],bo[fk][:3])+1e-7):continue
     v=max(0.,float((ss^f).volume()));peak=max(peak,v)
     if v>tol:bad={'moving':k,'fixed':fk,'q':q.tolist(),'intersection_mm3':v,'segment':i};break
    if bad:break
   if bad:break
  if bad:break
 rec={'name':name,'passed':bad is None,'maximum_overlap_mm3':peak,'samples':samples,'sample_displacement_upper_bound_mm':step,'overlap_tolerance_mm3':tol,'first_conflict':bad,'path':path};print(name,rec['passed'],peak,samples,bad,flush=True);return rec
reports=[]
for plane in [2.5,4.5]:
 name=f'compact_lap_z{plane}_w8';z=np.load(C/(name+'.npz'));p={k:b.b.from_tri_exact(z[k]) for k in z.files};rows=[]
 rootpath=read(C/'proximal_root_escape_candidate.json')['path'];rows.append(check('root_insertion_'+name,{'root':p['root']},fixed,rootpath))
 obs=dict(fixed,root=p['root'])
 rows.append(check('distal_insertion_'+name,{'distal':p['distal']},obs,[[0,0,0,0,0,0],[0,0,-100,0,0,0]],tol=.001))
 obs=dict(allfixed,root=p['root'],distal=p['distal']);stockchecks=[]
 for k in ['nut_0','nut_1','screw_0','screw_1']:
  ss=p[k];bb=np.array(ss.bounding_box());hits=[]
  for fk,f in obs.items():
   bo=np.array(f.bounding_box())
   if np.any(np.minimum(bb[3:],bo[3:])<=np.maximum(bb[:3],bo[:3])+1e-7):continue
   v=max(0.,float((ss^f).volume()))
   if v>.001:hits.append({'part':fk,'overlap_mm3':v})
  stockchecks.append({'stock':k,'conflicts':hits});print('STOCK',name,k,hits,flush=True)
 reports.append({'name':name,'npz_sha256':sha(C/(name+'.npz')),'checks':rows,'static_stock':stockchecks})
 put(C/'compact_lap_paths_review.json',{'status':'CANDIDATE_REVIEW','reports':reports,'physical_assembly_tested':False})
