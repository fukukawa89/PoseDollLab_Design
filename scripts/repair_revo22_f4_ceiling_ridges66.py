"""Continuous short breakaway ridges for a broad flat ceiling, with transverse bridge paths."""
from pathlib import Path
import sys,json,numpy as np,trimesh
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'scripts'))
from build_revo22_fins import solid,vf,box,md,union
from o22_material_components import material_components
from slice_revo22_f4_candidate import run
from verify_revo22_f4_full_bead import check
from refine_revo22_f4_full_bead import refine
O=R/'Hardware/PoseDoll44/bench/revO22/a1mini_fins_v4'
pid='X046';parent='portal65';label='ceiling_ridges66';src=O/'candidates'/pid/parent;dst=O/'candidates'/pid/label
for sub in ['parts','design','verification']:(dst/sub).mkdir(parents=True,exist_ok=True)
n=dict(np.load(src/'parts'/f'{pid}.npz'));d=json.loads((src/'design'/f'{pid}.json').read_text());part=solid(n['v'],n['f']);fin=solid(n['fin_v'],n['fin_f']);teeth=solid(n['teeth_v'],n['teeth_f']);roof=23.;fresh=part.slice(roof+.05)-part.slice(roof-.05);section=fin.slice(roof-.4)^fresh;added=[];rows=[]
for c in section.decompose():
 if c.area()<.1:continue
 b=c.bounds();cy=(b[1]+b[3])/2;strip=md.CrossSection.square([b[2]-b[0],.45]).translate([b[0],cy-.225]);profile=(c^strip);t=profile.extrude(.8).translate([0,0,roof-.6]);bite=float((t^part).volume());root=float((t^fin).volume())
 if bite<.005 or root<.005:continue
 assert (t^part^box([-300,-300,0],[300,300,roof-.01])).volume()<1e-6
 added.append(t);rows.append({'bounds_mm':list(t.bounding_box()),'part_bite_mm3':bite,'fin_root_mm3':root,'nominal_tip_penetration_mm':.2,'continuous_breakaway_ridge':True,'ridge_width_mm':.45,'ridge_vertical_height_mm':.8,'roof_z_mm':roof,'removal_instruction':'Cut the continuous yellow ridge along the orange blade after cooling; work through the open box mouth. Keep the cutter against the disposable support side.'})
teeth=teeth+union(added);assert all(float((t^part).volume())>.005 and float((t^fin).volume())>.005 for t in material_components(teeth));n['teeth_v'],n['teeth_f']=vf(teeth);d['teeth']+=rows;d['continuous_roof_ridges']=rows;d.setdefault('required_process_overrides',{}).update(bridge_angle='90',thick_bridges='1');d['required_bridge_direction_in_part_xy']=[0,1];d['requires_dedicated_plate_and_bridge_direction_check']=True;d.update(support_volume_mm3=float((fin+teeth).volume()),teeth_part_overlap_mm3=float((teeth^part).volume()));np.savez_compressed(dst/'parts'/f'{pid}.npz',**n);(dst/'design'/f'{pid}.json').write_text(json.dumps(d,ensure_ascii=False,indent=2),encoding='utf8');print('CEILING_RIDGES66',len(rows),'ridgevol',float(union(added).volume()),flush=True);run(pid,label);check(pid,label);q=refine(pid,label);print('CEILING_RESULT66',q['external_island_count'],q['critical_external_count'],flush=True)
