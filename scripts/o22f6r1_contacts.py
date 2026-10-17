"""Two path-driven removable contacts after P095 elbow mesh revision.
Uses existing bed-rooted fins only. Never changes the permanent part.
"""
import sys,json,copy,math,collections,shutil
import numpy as np,trimesh
from shapely.geometry import LineString
import o22f6r1_p095 as r
from route_revo22_x062244 import tooth,sweep_convex
h=r.h

def run():
 n=dict(np.load(r.OUT/'parts/P095.npz'));d=json.loads((r.OUT/'design/P095.json').read_text());body=h.solid(n['v'],n['f']);fin=h.solid(n['fin_v'],n['fin_f']);teeth=h.solid(n['teeth_v'],n['teeth_f']);guard=r.npzsolid(r.WORK/'guards/P095.npz');mesh=trimesh.Trimesh(n['v'],n['f'],process=False);fm=trimesh.Trimesh(n['fin_v'],n['fin_f'],process=False)
 report=json.loads((r.WORK/'plates/D01/support_paths.json').read_text());it=r.plate()['items'][0];M=np.array(it['rotation_matrix']);t=np.array(it['translation_mm']);records=[];roots=d.get('teeth',[])+d.get('local_route_repairs',[])+d.get('r1_native_contacts',[]);counts=collections.Counter()
 archive=r.WORK/'before_native_contact_repair';archive.mkdir(exist_ok=True)
 if not(archive/'P095.npz').exists():shutil.copy2(r.OUT/'parts/P095.npz',archive/'P095.npz');shutil.copy2(r.WORK/'plates/D01/support_paths.json',archive/'support_paths.json')
 jobs=[]
 for issue in report['critical_external_runs']:
  count=max(1,int(math.ceil(issue['length_mm']/1.4)));jobs.extend((issue,(i+.5)/count)for i in range(count))
 seen=[]
 for issue,fraction in jobs:
  line=LineString(issue['xy_mm']);xy=np.array(line.interpolate(fraction,normalized=True).coords[0]);p=(np.r_[xy,issue['z_mm']]-t)@M
  if any(np.linalg.norm(p-q)<.65 for q in seen):continue
  candidates=[]
  for rad in [0,.25,.5,.8,1.1]:
   for ang in ([0]if rad==0 else np.arange(0,2*np.pi,np.pi/4)):
    x,y=p[:2]+rad*np.array([np.cos(ang),np.sin(ang)]);hh,_,ff=mesh.ray.intersects_location([[x,y,-.1]],[[0,0,1]],multiple_hits=True)
    for hit,face in zip(hh,ff):
     if -.3<=p[2]-hit[2]<=3 and mesh.face_normals[face,2]<-.15:candidates.append(hit)
  candidates.sort(key=lambda x:np.linalg.norm(x-p));success=False
  for hit in candidates:
   for keep_holes_clear in [True,False]:
    roof=hit[2];tip=hit+[0,0,.18];tip[2]=max(tip[2],p[2]+.2)
    parents=[]
    for a in {tuple(np.round(np.array(q['root'])-[0,0,dz],6))for q in roots+records for dz in [0,1.,2.]}:
     a=np.array(a);dz=roof-a[2]
     if 1.4<dz<9 and np.linalg.norm(a[:2]-hit[:2])<min(7,dz*.95):parents.append(a)
    for seg in sorted(d.get('segments',[]),key=lambda q:abs(q['y']-hit[1]))[:3]:
     xy=np.array([hit[0],seg['y']]);hh,_,_=fm.ray.intersects_location([[*xy,roof-.1]],[[0,0,-1]],multiple_hits=False)
     if len(hh)and 1.4<roof-hh[0,2]<9:parents.append(np.r_[xy,hh[0,2]-.28])
    parents.sort(key=lambda a:np.linalg.norm(a-tip))
    for a in parents:
     tt=tooth(a,tip,.8)
     if keep_holes_clear:tt=tt-guard
     if len(h.material_components(tt))!=1:counts['guard_split']+=1;continue
     bite=tt^body;bv=float(bite.volume())
     if not .008<bv<1.5 or bite.bounding_box()[2]<roof-1:counts['contact']+=1;continue
     if keep_holes_clear and (tt^guard).volume()>1e-6:counts['guard']+=1;continue
     if (tt^fin).volume()<.02:counts['fin']+=1;continue
     if (tt-(body+fin+teeth)).volume()<.01:counts['already']+=1;continue
     cutz=roof-1.2
     if cutz<=a[2]:continue
     cut=a+(tip-a)*((cutz-a[2])/(tip[2]-a[2]));stub=tooth(a,cut,.8)
     directions=[np.array([0.,0.,-1.]),(a-tip)/np.linalg.norm(a-tip)]
     direction=next((v for v in directions if(sweep_convex(stub,v*100)^body).volume()<1e-6),None)
     if direction is None:counts['exit']+=1;continue
     print("UNION_BEFORE",teeth.volume(),tt.volume(),teeth.status(),tt.status(),flush=True)
     teeth=(teeth+tt).as_original()
     print("UNION_AFTER",teeth.volume(),teeth.status(),flush=True)
     rec=dict(native_issue=issue,root=a.tolist(),tip=tip.tolist(),target=hit.tolist(),neck_xy_mm=[.8,.8],cut_z_mm=float(cutz),body_overlap_mm3=bv,fin_overlap_mm3=float((tt^fin).volume()),removal_vector=direction.tolist(),new_bed_fin=False,added_contact_in_guard_mm3=max(0.,float((tt^guard).volume())),continuous_cut_stub_exit_clear=True)
     records.append(rec);seen.append(p);success=True;print('CONTACT',rec['root'],rec['tip'],'guard',rec['added_contact_in_guard_mm3'],flush=True);break
    if success:break
   if success:break
  assert success,('no existing fin route',p.tolist(),dict(counts))
 original=h.solid(n['teeth_v'],n['teeth_f']);assert abs((original-teeth).volume())<1e-5;cc=h.material_components(body+fin+teeth);print('CONNECTIVITY',len(cc),flush=True);assert len(cc)==1
 for c in h.material_components(teeth):assert(c^body).volume()>.001 and(c^fin).volume()>.001
 n['teeth_v'],n['teeth_f']=h.vf(teeth);np.savez_compressed(r.OUT/'parts/P095.npz',**n)
 d['r1_native_contacts']=d.get('r1_native_contacts',[])+records;d['native_pending']=True;h.put(r.OUT/'design/P095.json',d)
 rep=dict(revised_npz_sha256=h.sha(r.OUT/'parts/P095.npz'),new_contacts=records,contact_count=len(records),body_vertices_and_faces_identical_to_elbow_candidate=True,fin_vertices_and_faces_identical_to_elbow_candidate=True,new_fins=0,hole_support_fallback_user_authorized=True,added_tooth_mm3=float((teeth-original).volume()),added_support_in_fastener_guard_mm3=max(0.,float(((teeth-original)^guard).volume())),whole_print_components=1,all_new_cut_stubs_continuously_extractable=True,cut_instruction='Clip the exposed new contact at its body attachment and remove the short upper remnant; the lower stub withdraws downward with its existing fin.')
 h.put(r.WORK/'native_contact_repair.json',rep);print('CONTACT_DONE',len(records),rep['added_tooth_mm3'],flush=True)
if __name__=='__main__':run()