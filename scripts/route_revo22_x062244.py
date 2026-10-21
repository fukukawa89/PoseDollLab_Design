"""Local bed-rooted, removable fingers for actual native overhang paths."""
from pathlib import Path
import sys,json,shutil,math
import numpy as np,trimesh
from shapely.geometry import LineString
from build_revo22_x062_open242 import S,put,sha
from build_revo22_fins import solid,vf,box,union,md,write_stl
from o22_material_components import material_components

def tooth(a,b,w=.8):
 xy=np.array([[-w/2,-w/2,0],[w/2,-w/2,0],[w/2,w/2,0],[-w/2,w/2,0]])
 return md.Manifold.hull_points(np.vstack([xy+a,xy+b]))
def sweep_convex(s,d):
 v=vf(s)[0];return md.Manifold.hull_points(np.vstack([v,v+np.asarray(d)]))
def attempt(src,label):
 old=S/'candidates/X062'/src;folder=S/'candidates/X062'/label
 for sub in ['parts','design','verification','projects','stl']:(folder/sub).mkdir(parents=True,exist_ok=True)
 n=dict(np.load(old/'parts/X062.npz'));design=json.loads((old/'design/X062.json').read_text());basegeom=json.loads((old/'verification/geometry.json').read_text());s=solid(n['v'],n['f']);fin=solid(n['fin_v'],n['fin_f']);teeth=solid(n['teeth_v'],n['teeth_f']);mesh=trimesh.Trimesh(n['v'],n['f'],process=False);fm=trimesh.Trimesh(n['fin_v'],n['fin_f'],process=False)
 vp=(S/'candidates/X062'/sys.argv[3]/'verification')if len(sys.argv)>3 else old/'verification';d=json.loads((vp/'full_bead_contacts_v5.json').read_text());it=json.loads((vp/'plate_manifest.json').read_text())['items'][0];M=np.array(it['rotation_matrix']);t=np.array(it['translation_mm']);bb=np.array(s.bounding_box());height=bb[5];req=[]
 for q in d['external_islands']:
  b=q['bounds_mm'];req.append((np.array([(b[0]+b[2])/2,(b[1]+b[3])/2,q['z_mm']])-t)@M)
 for q in sorted(d['critical_external_runs'],key=lambda q:-q['length_mm']):
  line=LineString(q['xy_mm']);length=line.length
  for x in (np.arange(max(1,int(math.ceil(length/1.6))))+.5)*length/max(1,int(math.ceil(length/1.6))):
   p=line.interpolate(x);req.append((np.array([p.x,p.y,q['z_mm']])-t)@M)
 roots=[];newteeth=[];newrecords=[];failed=[];seen=[];dirs=[np.array([0.,0.])]+[np.array([math.cos(a),math.sin(a)])for a in np.arange(0,2*np.pi,np.pi/12)]
 for qi,p in enumerate(req):
  if any(np.linalg.norm(p-q)<1.3 for q in seen):continue
  hits,ri,fi=mesh.ray.intersects_location([[p[0],p[1],-.1]],[[0,0,1]],multiple_hits=True);valid=[(h,f)for h,f in zip(hits,fi)if -.25<=p[2]-h[2]<=1.25 and mesh.face_normals[f,2]<-.18]
  if not valid:failed.append(dict(p=p.tolist(),reason='No nearby downward body surface'));continue
  hit,face=min(valid,key=lambda hf:abs(p[2]-hf[0][2]));roof=float(hit[2]);b=hit+[0,0,.24];candidates=[]
  for seg in sorted(design['segments'],key=lambda q:abs(q['y']-hit[1]))[:2]:
   xy=np.array([hit[0],seg['y']]);hh,_,_=fm.ray.intersects_location([[*xy,roof-.1]],[[0,0,-1]],multiple_hits=False)
   if len(hh)and 3.7<roof-hh[0,2]<9:candidates.append((np.r_[xy,hh[0,2]-.25],None,np.array([0.,0.,-1.])))
  for parent in design.get('local_route_repairs',[]):
   a0=np.array(parent['root'])
   if 3.7<roof-a0[2]<8 and np.linalg.norm(a0[:2]-hit[:2])<6:candidates.append((a0,None,np.array(parent['removal_vector'])))
  for dv,dz in [(u,z)for u in dirs for z in [5.2,3.2]]:
   az=roof-dz
   if az<.6:continue
   a=np.r_[hit[:2]-dv*4.5,az];direction=np.r_[-dv*4.5/dz,-1.];direction/=np.linalg.norm(direction);u=dv if np.linalg.norm(dv)>.1 else np.array([1.,0.]);perp=np.array([-u[1],u[0]])
   for lean in [0.,.4,.8]:
    c=a[:2]-u*lean*az;pts=[]
    for center,z,w in [(c,0.,max(6,az/4)),(a[:2],az+.2,2.2)]:
     for l,k in [(-1,-1),(1,-1),(1,1),(-1,1)]:pts.append([*(center+u*l*w/2+perp*k*.6),z])
    core=md.Manifold.hull_points(np.array(pts));foot=core.slice(.1).offset(1.0,circular_segments=8).extrude(.4);core+=foot
    candidates.append((a,core,direction))
  success=False
  for a,core,direction in candidates:
   tt=tooth(a,b);bite=tt^s;bv=float(bite.volume())
   if not .015<bv<.85 or bite.bounding_box()[2]<roof-1:continue
   cutz=roof-1.2;cut=a+(b-a)*((cutz-a[2])/(b[2]-a[2]));stub=tooth(a,cut);swept=sweep_convex(stub,direction*(height+150))
   if (swept^s).volume()>1e-6:continue
   if core is None:
    if (tt^fin).volume()<.025:continue
   else:
    if (core^s).volume()>1e-6 or (core^fin).volume()>1e-6 or (core^union(roots)).volume()>1e-6:continue
    if (core^teeth).volume()>1e-6 or (core^union(newteeth)).volume()>1e-6:continue
    if (tt^core).volume()<.025:continue
    if (sweep_convex(core,direction*(height+150))^s).volume()>1e-6:continue
   if core is not None:roots.append(core)
   newteeth.append(tt);seen.append(p);newrecords.append(dict(target=hit.tolist(),root=a.tolist(),neck_xy_mm=[.8,.8],free_vertical_mm=float(roof-a[2]-.2),cut_z_mm=float(cutz),body_overlap_mm3=bv,fin_overlap_mm3=float((tt^(core if core is not None else fin)).volume()),new_bed_fin=core is not None,removal_vector=direction.tolist(),continuous_extraction_sweep_collision_mm3=0));success=True;break
  if not success:failed.append(dict(p=p.tolist(),roof=roof,reason='No open bed route with clear withdrawal'))
  if qi%40==0:print('ROUTE_PROGRESS',qi,len(req),'added',len(newrecords),'new_fins',len(roots),'failed',len(failed),flush=True)
 fin+=union(roots);teeth+=union(newteeth);n['fin_v'],n['fin_f']=vf(fin);n['teeth_v'],n['teeth_f']=vf(teeth);npz=folder/'parts/X062.npz';np.savez_compressed(npz,**n)
 checks=[]
 for p in material_components(fin):
  rec=dict(bounds_mm=list(p.bounding_box()),bed_contact_mm2=float(p.slice(.1).area()),tooth_overlap_mm3=float((p^teeth).volume()));assert rec['bounds_mm'][2]<1e-6 and rec['bed_contact_mm2']>.01 and rec['tooth_overlap_mm3']>.005;checks.append(rec)
 assert (fin^s).volume()<1e-6
 for p in material_components(teeth):assert (p^s).volume()>.005 and (p^fin).volume()>.005
 design.update(trial=label,local_route_repairs=design.get('local_route_repairs',[])+newrecords,unrouted_native_targets=failed,support_count=len(checks),support_volume_mm3=float((fin+teeth).volume()),native_previous_label=src,physical_print_tested=False)
 put(folder/'design/X062.json',design);basegeom.update(parts_npz_sha256=sha(npz),support_volume_mm3=design['support_volume_mm3'],support_reduction_percent=100*(1-design['support_volume_mm3']/194203.47766082024),bed_rooted_components=checks,local_route_repairs=design['local_route_repairs'],local_removal_policy='Cut long teeth; withdraw side fingers first along recorded directions, then lower combs. All authored cores and cut stubs have continuous swept collision checks.',fin_body_overlap_mm3=float((fin^s).volume()),native_audit_pending=True);put(folder/'verification/geometry.json',basegeom)
 for name,obj in [('body',s),('fins',fin),('teeth',teeth),('combined',s+fin+teeth)]:write_stl(folder/'stl'/f'X062_{name}.stl',obj)
 print('ROUTE244_BUILT',label,'added_teeth',len(newteeth),'new_fins',len(roots),'failed',len(failed),'volume',design['support_volume_mm3'],flush=True)
if __name__=='__main__':attempt(sys.argv[1],sys.argv[2])



