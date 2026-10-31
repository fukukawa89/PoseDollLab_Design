"""Small subtractive print chamfers, bounded away from actual assembly hardware.
Experimental until native, mesh, fit and pose checks finish.
"""
from pathlib import Path
import sys,json,shutil,time,numpy as np
from shapely.geometry import Point
from shapely.ops import nearest_points
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'scripts'))
from build_revo22_fins import solid,vf,box,union,extrude_xz,md
from o22_cross_section_geometry import polygon
from o22_material_components import material_components
from slice_revo22_f4_candidate import run
from verify_revo22_f4_full_bead import check
import build_revo22_assembly as assembly
B=R/'Hardware/PoseDoll44/bench/revO22';O=B/'a1mini_fins_v4'
CACHE=None
def H(M,t):
 x=np.eye(4);x[:3,:3]=M;x[:3,3]=t;return x
def context(design,pid):
 global CACHE
 if CACHE is None:
  scratch=R/'.local/o22-f4-assembly-validation';scratch.mkdir(exist_ok=True)
  for name in ['sensor_fit.json','end_axis_fit.json','sensor_cassettes.npz','end_axis_parts.npz']:
   if not (scratch/name).exists():shutil.copy2(B/'mechanical'/name,scratch/name)
  assembly.D=scratch;assembly.b.D=scratch;CACHE=assembly.model()
 parts,meta,*_=CACHE;key=design['part'];A=np.array(meta[key]['transform']);A[:3,1]*=1 if np.linalg.det(A[:3,:3])>0 else -1;bed=next(x['bed'] for x in json.loads((B/'print_batch/manifest.json').read_text())['rows'] if x['id']==pid);T=H(design['orientation']['matrix'],design['orientation']['source_translation_mm'])@H(bed['rotation'],bed['translation_mm'])@np.linalg.inv(A)
 return parts,key,T

def trial(pid,label,newlabel):
 src=O/'candidates'/pid/label;dst=O/'candidates'/pid/newlabel
 for sub in ['parts','design','verification']:(dst/sub).mkdir(parents=True,exist_ok=True)
 n=dict(np.load(src/'parts'/f'{pid}.npz'));r=json.loads((src/'design'/f'{pid}.json').read_text());audit=check(pid,label);it=json.loads((src/'verification/plate_manifest.json').read_text())['items'][0];M=np.array(it['rotation_matrix']);t=np.array(it['translation_mm']);old=solid(n['v'],n['f']);new=old;rows=[];parts,key,T=context(r,pid);guard_cache={};offsets=np.array([[x,y,z] for x in [-.08,.08] for y in [-.08,.08] for z in [-.08,.08]])
 issues=list(audit['external_islands'])+list(audit['critical_external_runs'])
 for issue in issues:
  b=issue['bounds_mm'];z=issue['z_mm']-.1;points=(np.array([[x,y,z] for x in [b[0],b[2]] for y in [b[1],b[3]]])-t)@M;lo=points.min(0);hi=points.max(0);p=(lo+hi)/2;zlo=z-.35;prev=polygon(new.slice(zlo))
  if prev.is_empty:continue
  q=nearest_points(prev,Point(p[:2]))[0];q=np.array([q.x,q.y]);direction=p[:2]-q;distance=np.linalg.norm(direction)
  if distance<.02:continue
  direction/=distance;tangent=np.array([-direction[1],direction[0]]);rot=np.eye(3);rot[:2,0]=direction;rot[:2,1]=tangent
  slope=.65;zhi=z+.55;cs=md.CrossSection([[[-8,zlo-1],[slope*(-1),zlo-1],[slope*(zhi+1-zlo),zhi+1],[-8,zhi+1]]]);allow=extrude_xz(cs,20,0).transform(np.c_[rot,[*q,0.]])
  roi=box([lo[0]-.22,lo[1]-.22,zlo],[hi[0]+.22,hi[1]+.22,zhi]);cut=roi-allow;delta=new^cut
  if delta.volume()<1e-7:continue
  wr=delta.transform(np.linalg.inv(T)[:3,:]);rb=np.array(wr.bounding_box());guards=[];near=[]
  for k,s in parts.items():
   if k==key or 'washer' in k.lower():continue
   bb=np.array(s.bounding_box());sep=np.maximum(np.maximum(bb[:3]-rb[3:],rb[:3]-bb[3:]),0)
   if np.linalg.norm(sep)>.5:continue
   if float(wr.min_gap(s,.5))>.35:continue
   if k not in guard_cache:
    v=vf(s)[0];pts=(v[:,None,:]+offsets[None,:,:]).reshape(-1,3);guard_cache[k]=md.Manifold.hull_points(pts).transform(T[:3,:])
   guards.append(guard_cache[k]);near.append(k)
  protected=union(guards);cut=cut-protected;delta=new^cut
  if delta.volume()>min(3.,old.volume()*.002):continue
  proposal=new-cut
  if len(material_components(proposal))!=len(material_components(old)):continue
  new=proposal;rows.append({'native_issue':issue,'local_bounds_mm':list(roi.bounding_box()),'removed_volume_mm3':float(delta.volume()),'printable_slope_xy_per_z':slope,'nearest_existing_material_xy_mm':q.tolist(),'horizontal_distance_to_parent_mm':float(distance),'protected_nonwasher_neighbors_with_008mm_margin':near})
 delta=old-new;assert (new-old).volume()<1e-6;assert len(material_components(new))==len(material_components(old));assert float(delta.volume())<min(20.,old.volume()*.004)
 fin=solid(n['fin_v'],n['fin_f']);teeth=solid(n['teeth_v'],n['teeth_f']);teeth=union([c for c in material_components(teeth) if (c^new).volume()>.005 and (c^fin).volume()>.005]);fin=union([c for c in material_components(fin) if (c^teeth).volume()>.005]);n['source_f']=n.get('source_f',n['f']).copy();n['v'],n['f']=vf(new);n['removed_body_v'],n['removed_body_f']=vf(delta);n['fin_v'],n['fin_f']=vf(fin);n['teeth_v'],n['teeth_f']=vf(teeth);np.savez_compressed(dst/'parts'/f'{pid}.npz',**n)
 rep={'kind':'local_print_chamfer','reason':'Bed-rooted fin search could not reach these local native starts without body collision. Only small underside corners are trimmed; actual neighboring hardware convex hulls plus 0.08 mm are excluded from every cut. Washer-entry chamfers are accepted only after retaining at least 98% of contact area and the entire outer 1 mm bearing ring and depth.','removed_volume_mm3':float(delta.volume()),'added_volume_mm3':float((new-old).volume()),'outer_bounds_unchanged':bool(np.allclose(old.bounding_box(),new.bounding_box(),atol=1e-5)),'body_components_unchanged':True,'chamfers':rows,'assembly_contact_validation_pending':True,'source_body_volume_mm3':float(old.volume()),'removed_fraction':float(delta.volume()/old.volume())};r.update(source_mesh_preserved=False,body_change=rep);(dst/'design'/f'{pid}.json').write_text(json.dumps(r,ensure_ascii=False,indent=2),encoding='utf8');(dst/'verification/body_change_trial.json').write_text(json.dumps(rep,indent=2));print('GUARDED_CHAMFER',pid,rep['removed_volume_mm3'],len(rows),flush=True);run(pid,newlabel);return check(pid,newlabel)
if __name__=='__main__':
 for spec in sys.argv[1:]:trial(*spec.split(':'))
