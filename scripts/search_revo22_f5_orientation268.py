"""Search low, open print orientations of the frozen F4 body meshes."""
from pathlib import Path
import json,sys,time,concurrent.futures,numpy as np,trimesh
from scipy.spatial import ConvexHull
R=Path(__file__).resolve().parents[1];B=R/'Hardware/PoseDoll44/bench/revO22';OLD=B/'O22F4_Compact';O=B/'a1mini_fins_v5';(O/'orientation').mkdir(exist_ok=True)
def put(p,x):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(x,ensure_ascii=False,indent=2),'utf-8')
def run(pid):
 dest=O/'orientation'/f'{pid}.json'
 if dest.exists():return json.loads(dest.read_text())
 t0=time.time();n=np.load(OLD/'parts'/f'{pid}.npz');v=n['v'];f=n['f'];tm=trimesh.Trimesh(v,f,process=False);ns=tm.face_normals;area=tm.area_faces;cent=tm.triangles_center;dirs=[]
 def add(z):
  z=np.array(z,dtype=float,copy=True);z/=np.linalg.norm(z)
  if not any(np.dot(z,a)>.9995 for a in dirs):dirs.append(z)
 for z in np.r_[np.eye(3),-np.eye(3)]:add(z)
 for i in np.argsort(-area)[:70]:add(ns[i]);add(-ns[i])
 _,ev=np.linalg.eigh(np.cov((v-v.mean(0)).T))
 for i in range(3):add(ev[:,i]);add(-ev[:,i])
 for i in range(36):
  z=1-2*(i+.5)/36;r=np.sqrt(1-z*z);a=i*np.pi*(3-np.sqrt(5));add([r*np.cos(a),r*np.sin(a),z])
 ranked=[]
 for di,z in enumerate(dirs):
  x=ev[:,2]-z*np.dot(ev[:,2],z)
  if np.linalg.norm(x)<.01:x=np.eye(3)[np.argmin(abs(z))];x-=z*np.dot(x,z)
  x/=np.linalg.norm(x);y=np.cross(z,x);Q=np.array([x,y,z]);vv=v@Q.T
  hull=vv[ConvexHull(vv[:,:2]).vertices,:2];edges=np.roll(hull,-1,axis=0)-hull;angs=np.arctan2(edges[:,1],edges[:,0]);best=None
  for a in angs:
   C=np.array([[np.cos(a),np.sin(a)],[-np.sin(a),np.cos(a)]]);wh=np.ptp(hull@C.T,axis=0);cost=np.prod(wh)+max(0,wh.max()-164)**2*10
   if best is None or cost<best[0]:best=(cost,a,wh)
  a=best[1];A=np.array([[np.cos(a),np.sin(a),0],[-np.sin(a),np.cos(a),0],[0,0,1.]]);Q=A@Q;vv=v@Q.T;size=np.ptp(vv,axis=0)
  if max(size[:2])>171:continue
  nz=ns@z;cz=cent@z-vv[:,2].min();down=(nz<-.50)&(cz>.32);ww=area*np.maximum(0,-nz);ids=np.flatnonzero(down);total=ww[ids].sum();occ=0.
  if len(ids):
   cum=np.cumsum(ww[ids]);sample=ids[np.searchsorted(cum,(np.arange(min(64,len(ids)))+.5)/min(64,len(ids))*cum[-1])];hits=tm.ray.intersects_any(cent[sample]-z*.02,np.tile(-z,(len(sample),1)));occ=total*np.mean(hits)
  bed=float(ww[(nz<-.98)&(cz<.12)].sum());proj=float(ConvexHull(vv[:,:2]).volume);volume_proxy=float(np.sum(ww[ids]*cz[ids]));score=total+8*occ+.015*volume_proxy+size[2]*1.5+max(0,size[2]-50)**2*.025+max(0,max(size[:2])-160)**2*4-min(bed,proj*.35)*.8
  ranked.append(dict(index=di,matrix_from_F4=Q.tolist(),size_mm=size.tolist(),score=float(score),downward_projection_mm2=float(total),occluded_projection_sample_estimate_mm2=float(occ),bed_face_mm2=bed,xy_hull_area_mm2=proj,support_height_area_proxy_mm3=volume_proxy))
 ranked.sort(key=lambda q:q['score']);assert ranked,pid
 result=dict(id=pid,source='Frozen O22F4_Compact actual body, including prior approved reliefs',candidate_count=len(ranked),ranked=ranked[:12],chosen=ranked[0],seconds=time.time()-t0,scope='Geometry heuristics choose candidates only; actual native slicing remains mandatory.');put(dest,result);print('ORIENT',pid,'H',round(ranked[0]['size_mm'][2],1),'size',np.round(ranked[0]['size_mm'],1).tolist(),'blocked_area',round(ranked[0]['occluded_projection_sample_estimate_mm2'],1),'bed',round(ranked[0]['bed_face_mm2'],1),flush=True);return result
if __name__=='__main__':
 inv=json.loads((O/'inventory.json').read_text());ids=sys.argv[1:]or[g[0]for g in inv['groups']if next(x for x in inv['rows']if x['id']==g[0])['has_fins']and g[0]!='X062'];out=[]
 with concurrent.futures.ProcessPoolExecutor(max_workers=3)as pool:
  for fut in concurrent.futures.as_completed([pool.submit(run,pid)for pid in ids]):
   try:out.append(fut.result());put(O/'orientation_progress.json',out)
   except Exception as e:print('ORIENT_ERROR',repr(e),flush=True)
 print('ORIENTATION_DONE',len(out),flush=True)
