"""Bed-rooted, cross-braced low fin grid for the X046 box ceiling.
Staggered short ridge contacts prevent transverse bridge paths missing entire rows.
"""
from pathlib import Path
import sys,json,numpy as np,math
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'scripts'))
from build_revo22_fins import solid,vf,box,union,md
from o22_material_components import material_components
from slice_revo22_f4_candidate import run
from verify_revo22_f4_full_bead import check
from refine_revo22_f4_full_bead import refine
O=R/'Hardware/PoseDoll44/bench/revO22/a1mini_fins_v4';pid='X046';parent='portal65';label='ceiling_grid69';src=O/'candidates'/pid/parent;dst=O/'candidates'/pid/label
for sub in ['parts','design','verification']:(dst/sub).mkdir(parents=True,exist_ok=True)
n=dict(np.load(src/'parts'/f'{pid}.npz'));d=json.loads((src/'design'/f'{pid}.json').read_text());s=solid(n['v'],n['f']);fin=solid(n['fin_v'],n['fin_f']);teeth=solid(n['teeth_v'],n['teeth_f']);roof=23.;h=22.6;fresh=s.slice(roof+.05)-s.slice(roof-.05);obstacles=(s^box([-300,-300,-.1],[300,300,h+.3])).project().offset(.32,circular_segments=12);available=fresh.offset(-.32,circular_segments=12)-obstacles;bb=available.bounds();blades=[];ridges=[];records=[]
for row,y in enumerate(np.arange(bb[1]+.42,bb[3]-.42,1.7)):
 strip=md.CrossSection.square([bb[2]-bb[0]+2,.8]).translate([bb[0]-1,y-.4]);cs=available^strip
 if cs.is_empty():continue
 blade=cs.extrude(h);blades.append(blade);tr=[]
 for x in np.arange(bb[0]-5+(2.4 if row%2 else 0),bb[2]+1,4.8):
  neckcs=cs^md.CrossSection.square([4.,.45]).translate([x,y-.225]);tooth=neckcs.extrude(.8).translate([0,0,roof-.6])
  if tooth.is_empty()or(tooth^s).volume()<.005 or(tooth^blade).volume()<.005:continue
  ridges.append(tooth);q={'bounds_mm':list(tooth.bounding_box()),'part_bite_mm3':float((tooth^s).volume()),'fin_root_mm3':float((tooth^blade).volume()),'nominal_tip_penetration_mm':.2,'ridge_width_mm':.45,'ridge_length_at_most_mm':4.,'ridge_vertical_height_mm':.8,'staggered_roof_contact':True,'grid_row':row};tr.append(q);d['teeth'].append(q)
 records.append({'number':len(d['segments'])+len(records)+1,'bounds_mm':list(blade.bounding_box()),'height_mm':h,'blade_width_mm':bb[2]-bb[0],'blade_thickness_mm':.8,'teeth_count':len(tr),'brace_count':0,'on_build_plate':True,'vertical_bed_path':True,'min_gap_mm':float(blade.min_gap(s,.5)),'removal_vector':[0,0,-1],'low_bed_grid_fin':True})
braces=[]
for x in np.arange(bb[0]+3,bb[2]-1,12.):
 cs=available^md.CrossSection.square([1.2,bb[3]-bb[1]+2]).translate([x-.6,bb[1]-1]);braces.append(cs.extrude(h-2.))
grid=union(blades+braces);foot=available.extrude(.4);grid=grid+foot;assert(grid^s).volume()<1e-6 and grid.min_gap(s,.5)>.235;newteeth=union(ridges);assert all((q^newteeth).volume()>.005 for q in material_components(grid));fin=fin+grid;teeth=teeth+newteeth;n['fin_v'],n['fin_f']=vf(fin);n['teeth_v'],n['teeth_f']=vf(teeth);d['segments']+=records;d['ceiling_grid']={'pitch_mm':1.7,'fin_thickness_mm':.8,'height_mm':h,'cross_brace_spacing_mm':12.,'cross_brace_thickness_mm':1.2,'contact_width_mm':.45,'contact_segment_length_mm':4.,'contact_gap_mm':.8,'alternating_row_phase_mm':2.4,'all_grid_columns_direct_to_bed':True,'grid_volume_mm3':float(grid.volume()),'ridge_count':len(ridges),'removal':'After cooling, sever the yellow short ridge contacts through the open box mouth. The orange grid then withdraws toward the bed; cut it into smaller pieces if needed. Clean the four PCB-post holes completely.'};d.setdefault('required_process_overrides',{}).update(bridge_angle='90',thick_bridges='1');d['required_bridge_direction_in_part_xy']=[0,1];d['requires_dedicated_plate_and_bridge_direction_check']=True;d.update(support_count=len(d['segments']),support_volume_mm3=float((fin+teeth).volume()),body_part_overlap_mm3=float((fin^s).volume()),teeth_part_overlap_mm3=float((teeth^s).volume()));np.savez_compressed(dst/'parts'/f'{pid}.npz',**n);(dst/'design'/f'{pid}.json').write_text(json.dumps(d,ensure_ascii=False,indent=2),encoding='utf8');print('GRID69',len(blades),len(ridges),float(grid.volume()),flush=True);run(pid,label);check(pid,label);q=refine(pid,label);print('GRID69_RESULT',q['external_island_count'],q['critical_external_count'],flush=True)
