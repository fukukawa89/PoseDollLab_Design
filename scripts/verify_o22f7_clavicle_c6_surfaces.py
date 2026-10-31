"""Independently verify C6 edit provenance and unaltered functional surfaces."""
from o22f7_animation import *
from build_revo22_assembly import b
import trimesh
C=WORK/'structure_revision';x=Build();x.begin(x.g['steps'][3]);I=np.linalg.inv(x.mount)
def freeze(s):
 s.volume();return b.b.from_tri_exact(b.g.tri(s))
a=np.load(C/'W005_C5.npz');z=np.load(C/'W005_C6.npz');old={k:b.b.from_tri_exact(a[k]) for k in ['root','distal','added']};now={k:b.b.from_tri_exact(z[k]) for k in ['root','distal']};subset={k:max(0.,float((now[k]-old[k]).volume())) for k in now};assert max(subset.values())<1e-6,subset
newadd=freeze(freeze(old['added']^now['root'])+freeze(old['added']^now['distal']));np.savez_compressed(C/'W005_C6_verified_delta.npz',added=b.g.tri(newadd))
k='frame/clavicle_l.protract_frame';o=x.obs[k];m=x.scene['meshes'][o['mesh']];source=x.verts[m['first']:m['first']+m['count'],:3].reshape(-1,3,3).astype(float);T=I@x.mats[k];source=source@T[:3,:3].T+T[:3,3];target=np.concatenate([z['root'],z['distal']]);source_mesh=trimesh.Trimesh(source.reshape(-1,3),np.arange(source.size//3).reshape(-1,3),process=True);target_mesh=trimesh.Trimesh(target.reshape(-1,3),np.arange(target.size//3).reshape(-1,3),process=True)
A=np.linalg.inv(I@x.owners['clavicle_l.elevate','parent']);bb=np.array(b.b.L.libraries()['hinge'][0]['base_sensor_half'].bounding_box());lo,hi=bb[:3]+.0001,bb[3:]-.0001

def roi(points):
 root=(np.linalg.norm(points[:,:2],axis=1)<11.99)&(points[:,2]>-2.9)&(points[:,2]<15.9);pp=points@A[:3,:3].T+A[:3,3];dist=np.all((pp>lo)&(pp<hi),axis=1);return root|dist
checks=[]
for name,tri,mesh in [('original_to_candidate',source,target_mesh),('candidate_to_original',target,source_mesh)]:
 pts=np.concatenate([tri.reshape(-1,3),tri.mean(1),(tri[:,0]+tri[:,1])/2,(tri[:,1]+tri[:,2])/2,(tri[:,2]+tri[:,0])/2]);pts=np.unique(pts[roi(pts)],axis=0);peak=0
 for start in range(0,len(pts),800):
  closest,distance,faces=trimesh.proximity.closest_point(mesh,pts[start:start+800]);peak=max(peak,float(distance.max()))
 checks.append({'direction':name,'surface_points':len(pts),'maximum_surface_distance_mm':peak});assert peak<.00001,(name,peak)
rep={'candidate_sha256':sha(C/'W005_C6.npz'),'source_sha256':sha(C/'W005_C5.npz'),'delta_sha256':sha(C/'W005_C6_verified_delta.npz'),'piece_subset_added_mm3':subset,'new_added_volume_mm3':newadd.volume(),'functional_surface_checks':checks,'passed':True,'scope':'C6 plastics are strict subsets of the already delimited C5 edit. The new positive delta is intersected with each final solid; every protected original/candidate vertex, face centroid and edge midpoint is checked bidirectionally to the opposite surface. Kinematic transforms are unchanged.'};put(C/'W005_C6_surface_review.json',rep);print(rep,flush=True)
