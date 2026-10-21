"""Small subtractive print chamfers, bounded away from actual assembly hardware.
Experimental until native, mesh, fit and pose checks finish.
"""
from pathlib import Path
import sys,json,shutil,time,numpy as np,shapely
from o22_f3_gcode import extract_paths
from shapely.geometry import Point
from shapely.ops import nearest_points
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'scripts'))
from build_revo22_fins import solid,vf,box,union,extrude_xz,md
from o22_cross_section_geometry import polygon
from o22_material_components import material_components
from o22_reference_mesh import reference_mesh
from inspect_revo22_f4_nut_contacts import core_guards
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

from repair_revo22_f4_guarded_chamfer import context
import repair_revo22_f4_guarded_chamfer as shared_assembly

def trial(pid,label,newlabel):
 src=O/'candidates'/pid/label;dst=O/'candidates'/pid/newlabel
 for sub in ['parts','design','verification']:(dst/sub).mkdir(parents=True,exist_ok=True)
 n=dict(np.load(src/'parts'/f'{pid}.npz'));r=json.loads((src/'design'/f'{pid}.json').read_text());audit=check(pid,label);it=json.loads((src/'verification/plate_manifest.json').read_text())['items'][0];M=np.array(it['rotation_matrix']);t=np.array(it['translation_mm']);old=solid(n['v'],n['f']);rv,rf=reference_mesh(n,r);original=solid(rv@np.array(r['orientation']['matrix']).T+np.array(r['orientation']['source_translation_mm']),rf);new=old;previous_rows=r.get('body_change',{}).get('chamfers',[]);rows=[];parts,key,T=context(r,pid);guard_cache={};offsets=np.array([[x,y,z] for x in [-.08,0,.08] for y in [-.08,0,.08] for z in [-.08,0,.08]])
 project=json.loads((src/'verification/local_extrusion.json').read_text())['project'];_,raw=extract_paths(src/'projects'/project,arc_tolerance_mm=.025,max_arc_segment_mm=1.);a=np.asarray(raw).reshape(-1,9);a=a[a[:,7]==0];zs=np.unique(np.round(a[:,5],3));previous_cache={}
 issues=list(audit['external_islands'])+list(audit['critical_external_runs'])
 for issue in issues:
  b=issue['bounds_mm'];z=issue['z_mm']-.1;points=(np.array([[x,y,z] for x in [b[0],b[2]] for y in [b[1],b[3]]])-t)@M;lo=points.min(0);hi=points.max(0);p=(lo+hi)/2;zprev=float(zs[zs<round(issue['z_mm'],3)-.01][-1]);zlo=zprev-.1
  if zprev not in previous_cache:
   ar=a[abs(a[:,5]-zprev)<.002];xy=np.stack([ar[:,:2],ar[:,3:5]],axis=1);xy=(xy-t[:2])@M[:2,:2];lines=shapely.linestrings(xy);previous_cache[zprev]=shapely.union_all(shapely.buffer(lines,ar[:,8]/2,quad_segs=6))
  prev=previous_cache[zprev].buffer(-.08,quad_segs=6)
  if prev.is_empty:continue
  q=nearest_points(prev,Point(p[:2]))[0];q=np.array([q.x,q.y]);direction=p[:2]-q;distance=np.linalg.norm(direction)
  if distance<.02:continue
  direction/=distance;tangent=np.array([-direction[1],direction[0]]);rot=np.eye(3);rot[:2,0]=direction;rot[:2,1]=tangent
  slope=.5;pad=.5;corners=np.array([[x,y] for x in [lo[0]-pad,hi[0]+pad] for y in [lo[1]-pad,hi[1]+pad]]);reach=float(((corners-q)@direction).max());zhi=max(z+.7,zlo+(reach+.3)/slope);cs=md.CrossSection([[[-20,zlo-1],[slope*(-1),zlo-1],[slope*(zhi+1-zlo),zhi+1],[-20,zhi+1]]]);allow=extrude_xz(cs,40,0).transform(np.c_[rot,[*q,0.]])
  roi=box([lo[0]-pad,lo[1]-pad,zlo],[hi[0]+pad,hi[1]+pad,zhi]);cut=roi-allow;delta=new^cut
  if delta.volume()<1e-7:continue
  wr=delta.transform(np.linalg.inv(T)[:3,:]);rb=np.array(wr.bounding_box());guards=[];near=[]
  for k,s in parts.items():
   if k==key or (shared_assembly.CACHE[1][k].get('sku') or '').startswith('W_'):continue
   bb=np.array(s.bounding_box());sep=np.maximum(np.maximum(bb[:3]-rb[3:],rb[:3]-bb[3:]),0)
   if np.linalg.norm(sep)>.5:continue
   if float(wr.min_gap(s,.5))>.35:continue
   if k not in guard_cache:
    guard_cache[k]=(core_guards(s) if (shared_assembly.CACHE[1][k].get('sku') or '').startswith('NUT_') else union([s.translate(v) for v in offsets])).transform(T[:3,:])
   guards.append(guard_cache[k]);near.append(k)
  protected=union(guards);cut=cut-protected;delta=new^cut
  if delta.volume()>min(8.,old.volume()*.004):continue
  proposal=new-cut;pcs=sorted(material_components(proposal),key=lambda c:float(c.volume()),reverse=True);expected=len(material_components(old));chips=pcs[expected:]
  if chips:
   if sum(float(c.volume()) for c in chips)>.02 or any(float(c.volume())>.01 or float((c^protected).volume())>1e-7 for c in chips):continue
   debris=union(chips);proposal=union(pcs[:expected]);delta=new-proposal;rb=np.array(roi.bounding_box());cb=np.array(debris.bounding_box());roi=box(np.minimum(rb[:3],cb[:3])-.001,np.maximum(rb[3:],cb[3:])+.001)
  if len(material_components(proposal))!=expected:continue
  new=proposal;rows.append({'native_issue':issue,'local_bounds_mm':list(roi.bounding_box()),'removed_volume_mm3':float(delta.volume()),'printable_slope_xy_per_z':slope,'nearest_existing_material_xy_mm':q.tolist(),'horizontal_distance_to_parent_mm':float(distance),'protected_nonwasher_shape_envelopes_008mm':near,'detached_tip_fragments_removed_mm3':sum(float(c.volume()) for c in chips),'tip_fragment_policy':'Only newly separated fragments below 0.01 mm3 each and 0.02 mm3 total, outside protected hardware, are included in the cut; all removed material is subsequently checked against assembly contacts.'})
 delta=original-new;assert (new-original).volume()<1e-6;assert len(material_components(new))==len(material_components(old));assert float(delta.volume())<min(60.,original.volume()*.008)
 fin=solid(n['fin_v'],n['fin_f']);teeth=solid(n['teeth_v'],n['teeth_f']);teeth=union([c for c in material_components(teeth) if (c^new).volume()>.005 and (c^fin).volume()>.005]);fin=union([c for c in material_components(fin) if (c^teeth).volume()>.005]);n['source_f']=n.get('source_f',n['f']).copy();n['v'],n['f']=vf(new);n['removed_body_v'],n['removed_body_f']=vf(delta);n['fin_v'],n['fin_f']=vf(fin);n['teeth_v'],n['teeth_f']=vf(teeth);np.savez_compressed(dst/'parts'/f'{pid}.npz',**n)
 rep={'kind':'native_anchored_print_chamfer','reason':'Bed-rooted fin search could not reach these local native starts without body collision. The continuous underside chamfer is anchored to actual previous-layer printed bead footprints and extends until its plane fully clears the local region. Only small underside corners are trimmed; actual neighboring hardware actual neighboring hardware envelopes are protected; for nuts, central planar bearing and anti-rotation faces are protected and any corner relief needs separate face-by-face retention checks. Washer-entry chamfers are accepted only after retaining at least 98% of contact area and the entire outer 1 mm bearing ring and depth.','removed_volume_mm3':float(delta.volume()),'added_volume_mm3':float((new-old).volume()),'outer_bounds_unchanged':bool(np.allclose(old.bounding_box(),new.bounding_box(),atol=1e-5)),'body_components_unchanged':True,'chamfers':previous_rows+rows,'assembly_contact_validation_pending':True,'source_body_volume_mm3':float(original.volume()),'removed_fraction':float(delta.volume()/original.volume())};r.update(source_mesh_preserved=False,body_change=rep);(dst/'design'/f'{pid}.json').write_text(json.dumps(r,ensure_ascii=False,indent=2),encoding='utf8');(dst/'verification/body_change_trial.json').write_text(json.dumps(rep,indent=2));print('GUARDED_CHAMFER',pid,rep['removed_volume_mm3'],len(rows),flush=True);run(pid,newlabel);return check(pid,newlabel)
if __name__=='__main__':
 for spec in sys.argv[1:]:trial(*spec.split(':'))
