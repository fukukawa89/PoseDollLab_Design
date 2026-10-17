from pathlib import Path
import sys,json,numpy as np,shapely
sys.path.insert(0,str(Path(__file__).resolve().parent))
from build_revo22_fins import solid,vf
from o22_reference_mesh import reference_solid
from repair_revo22_f4_guarded_chamfer import context
from o22_cross_section_geometry import polygon
R=Path(__file__).resolve().parents[1];O=R/'Hardware/PoseDoll44/bench/revO22/a1mini_fins_v4';p=O/'candidates/X038/seam184';n=np.load(p/'parts/X038.npz');d=json.loads((p/'design/X038.json').read_text());parts,key,T=context(d,'X038');capkey='thigh_l/P_case_plus';cap=parts[capkey].transform(T[:3,:]);old=reference_solid(n,d);new=solid(n['v'],n['f']);removed=old-new;v,f=vf(cap);tri=v[f];cross=np.cross(tri[:,1]-tri[:,0],tri[:,2]-tri[:,0]);area=np.linalg.norm(cross,axis=1)/2;norm=cross/np.maximum(2*area[:,None],1e-30);groups={}
for j,(nn,tt,aa)in enumerate(zip(norm,tri,area)):
 if aa<1e-7:continue
 k=tuple(np.round(np.r_[nn,np.dot(nn,tt[0])],5));groups.setdefault(k,[]).append(j)
rows=[]
for j,(key0,ids)in enumerate(groups.items()):
 nn=norm[ids[0]];origin=tri[ids[0],0];u=np.eye(3)[np.argmin(abs(nn))];u=np.cross(u,nn);u/=np.linalg.norm(u);w=np.cross(nn,u);A=np.array([u,w,nn]);off=-A@origin
 polys=[shapely.Polygon((tt-origin)@A[:2].T)for tt in tri[ids]];face=shapely.union_all(polys);aold=polygon(old.transform(np.c_[A,off]).slice(.002)).intersection(face);anew=polygon(new.transform(np.c_[A,off]).slice(.002)).intersection(face)
 if aold.area>1e-5:
  rows.append({'normal_bed':nn.tolist(),'face_area_mm2':float(face.area),'original_contact_area_mm2':float(aold.area),'new_contact_area_mm2':float(anew.area),'lost_contact_area_mm2':float(aold.difference(anew).area),'contact_retained_fraction':float(anew.area/aold.area),'lost_inside_face_core_mm2':{str(m):float(aold.difference(anew).intersection(face.buffer(-m)).area)for m in[.15,.3,.5,1.]},'lost_patch_bounds_in_face':list(aold.difference(anew).bounds)})
others=[]
for k,s in parts.items():
 if k in ['frame/pelvis',capkey]:continue
 gap=float(removed.min_gap(s.transform(T[:3,:]),2.))
 if gap<1.99:others.append({'part':k,'gap_mm':gap})
fit=json.loads((p/'verification/body_change_fit_and_pose.json').read_text());contacts=fit['sampled_contact_changes_at_nonintersecting_baseline_poses'];before=sum(q['original_contact_area_mm2']for q in rows);after=sum(q['new_contact_area_mm2']for q in rows)
out={'scope':'Actual planar faces of the removable P case half are intersected with old and new frame sections 0.002 mm outside each case face. This is geometric contact-area measurement, not FEA. The case is clamped by four M2 bolts; shaft, stop, screw and nut geometries remain separately protected.','removed_volume_mm3':float(removed.volume()),'original_total_case_contact_area_mm2':before,'new_total_case_contact_area_mm2':after,'total_contact_retained_fraction':after/before if before else None,'contact_face_groups':rows,'removed_material_near_other_parts_within_2mm':others,'sampled_changed_contact_part_keys':sorted({q['part']for q in contacts}),'all_recorded_case_contacts_have_same_rigid_motion':all(q.get('same_rigid_motion')for q in contacts if q['part']==capkey),'all_other_base_contacts_clear':all(q['part']==capkey or q['gap_mm']>=.08 for q in fit['assembly_contacts']),'physical_or_structural_test_performed':False}
(p/'verification/removable_case_seam184.json').write_text(json.dumps(out,indent=2));print(json.dumps({k:v for k,v in out.items()if k!='contact_face_groups'},indent=2),flush=True)
