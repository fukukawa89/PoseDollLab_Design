"""Trim only the unsupported native bead start and its unanchored descendants, bounded to 3 mm above each seed."""
from pathlib import Path
import sys,json,numpy as np,shapely,shutil
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'scripts'))
from o22_f3_gcode import extract_paths
from build_revo22_fins import solid,vf,union,md,box
from o22_material_components import material_components
from o22_reference_mesh import reference_solid
from verify_revo22_f4_body_change import check as fit
from verify_revo22_f4_repaired_geometry import check as geom
from verify_revo22_f4_portal_layers import check as growth
from slice_revo22_f4_candidate import run
from verify_revo22_f4_full_bead import check
from refine_revo22_f4_lateral104 import check as refine
O=R/'Hardware/PoseDoll44/bench/revO22/a1mini_fins_v4'
def trial(pid,parent,label):
 src=O/'candidates'/pid/parent;dst=O/'candidates'/pid/label;n=dict(np.load(src/'parts'/f'{pid}.npz'));d=json.loads((src/'design'/f'{pid}.json').read_text());q=json.loads((src/'verification/local_extrusion.json').read_text());it=json.loads((src/'verification/plate_manifest.json').read_text())['items'][0];M=np.array(it['rotation_matrix']);t=np.array(it['translation_mm']);proj=src/'projects'/q['project'];_,raw=extract_paths(proj,arc_tolerance_mm=.025,max_arc_segment_mm=1.);a=np.asarray(raw).reshape(-1,9);a=a[a[:,7]==0];zs=np.unique(a[:,5]);seeds=q['detached_bead_regions'];cscache={};cutters=[];records=[]
 def section(z):
  if z not in cscache:
   ar=a[abs(a[:,5]-z)<.002];xy=np.stack([ar[:,:2],ar[:,3:5]],1);buff=shapely.orient_polygons(shapely.buffer(shapely.linestrings(xy),np.maximum(ar[:,8]/2,.001),quad_segs=3));cscache[z]=md.CrossSection([np.round(np.asarray(p.exterior.coords)[:-1],4)for p in buff if not p.is_empty])
  return cscache[z]
 for seed in seeds:
  zi=int(np.argmin(abs(zs-seed['z_mm'])));prev=section(float(zs[zi-1]));roi=np.array(seed['bounds_mm']);ended=False;chain=[]
  for idx in range(zi,len(zs)):
   z=float(zs[idx]);pz=float(zs[idx-1]);cs=section(z);pieces=cs.decompose();bad=[]
   for c in pieces:
    b=np.array(c.bounds())
    if np.any(b[:2]>roi[2:]+2)or np.any(b[2:]<roi[:2]-2):continue
    if(c^prev.offset(.025,circular_segments=12)).area()<.001:
     assert c.area()<=12.,'Unanchored descendant exceeds local 12 mm2 investigation bound'
     bad.append(c)
   if not bad:ended=True;break
   if z>seed['z_mm']+3:break
   removed=md.CrossSection.batch_boolean(bad,md.OpType.Add);cut=removed.offset(.10,circular_segments=12).extrude(z-pz+.00002).translate([0,0,pz-.00001]);cut=cut.transform(np.c_[M.T,-M.T@t]);cutters.append(cut);chain.append({'z_mm':z,'bead_area_mm2':removed.area()});prev=cs-removed;roi=np.r_[np.minimum(roi[:2],np.array(removed.bounds())[:2]),np.maximum(roi[2:],np.array(removed.bounds())[2:])]
  assert ended,('chain_does_not_reach_existing_printed_material',pid,seed)
  records.append({'seed':seed,'removed_unanchored_layers':chain,'first_anchored_layer_z_mm':z})
 cut=union(cutters);old=solid(n['v'],n['f']);fin=solid(n['fin_v'],n['fin_f']);teeth=solid(n['teeth_v'],n['teeth_f']);bodyloss=float((old^cut).volume());finloss=float((fin^cut).volume());toothloss=float((teeth^cut).volume());print('NATIVE_CROP193_MEASURE',pid,'body',bodyloss,'fin',finloss,'teeth',toothloss,'chains',records,flush=True)
 assert bodyloss<=({'X038':5.4}.get(pid,3.)) and finloss<=3 and toothloss<=3,'bounded experiment exceeds 3 mm3 per role'
 new=old-cut;parts=sorted(material_components(new),key=lambda m:m.volume(),reverse=True);count=len(material_components(old));chips=parts[count:];assert all(c.volume()<.05 for c in chips)and sum(c.volume()for c in chips)<.1;new=union(parts[:count]);fin=fin-cut;teeth=teeth-cut;teeth=union([c for c in material_components(teeth)if(c^fin).volume()>.005 and(c^new).volume()>.005]);fin=union([c for c in material_components(fin)if(c^teeth).volume()>.005]);original=reference_solid(n,d);loss=original-new;assert(new-original).volume()<1e-6
 n['source_f']=n.get('source_f',n['f']);n['v'],n['f']=vf(new);n['fin_v'],n['fin_f']=vf(fin);n['teeth_v'],n['teeth_f']=vf(teeth);n['removed_body_v'],n['removed_body_f']=vf(loss)
 if bodyloss>1e-7:
  previous=d.get('body_change',{}).get('chamfers',[]);record={'kind':'native_disconnected_start_relief','local_bounds_mm':list((old-new).bounding_box()),'removed_volume_mm3':float((old-new).volume()),'native_chains':records};d['body_change']={'kind':'minimal_native_start_relief','removed_volume_mm3':float(loss.volume()),'added_volume_mm3':0.,'chamfers':previous+[record],'source_body_volume_mm3':float(original.volume()),'assembly_contact_validation_pending':True};d['source_mesh_preserved']=False
  if pid in ['W006','W007']:d['functional_edge_relief_review']='M4_wide_outer_edge'
  if pid=='X038':d['functional_edge_relief_review']='stationary_case_edge'
 if pid=='X046':d['required_layer_ranges']=[[65.6,66.8,{'outer_wall_line_width':'0.6','inner_wall_line_width':'0.6'}]]
 d['native_start_cleanup193']={'parent':parent,'body_removed_mm3':bodyloss,'fin_removed_mm3':finloss,'teeth_removed_mm3':toothloss,'records':records};d['support_volume_mm3']=float((fin+teeth).volume())
 for sub in ['parts','design','verification']:(dst/sub).mkdir(parents=True,exist_ok=True)
 np.savez_compressed(dst/'parts'/f'{pid}.npz',**n);(dst/'design'/f'{pid}.json').write_text(json.dumps(d,indent=2));ind=growth(fin+teeth,d);(dst/'verification/support_and_teeth_independent_growth.json').write_text(json.dumps(ind,indent=2));f=fit(pid,label)if'body_change'in d or'nominal_reference'in d else {'fit_and_pose_geometry_passed':True};g=geom(pid,label)
 if f['fit_and_pose_geometry_passed']and g['geometric_constraints_passed']and ind['passed']:run(pid,label);check(pid,label);refine(pid,label)
if __name__=='__main__':
 import concurrent.futures,traceback
 with concurrent.futures.ProcessPoolExecutor(max_workers=2)as pool:
  for f in concurrent.futures.as_completed([pool.submit(trial,*s.split(':'))for s in sys.argv[1:]]):
   try:f.result()
   except Exception:traceback.print_exc()
