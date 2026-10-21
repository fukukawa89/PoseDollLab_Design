from pathlib import Path
import sys,json,numpy as np,trimesh
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'scripts'))
from build_revo22_fins import solid,vf,box,union,md
from o22_material_components import material_components
from slice_revo22_f4_candidate import run
from verify_revo22_f4_full_bead import check
from refine_revo22_f4_lateral104 import check as refine
from verify_revo22_f4_repaired_geometry import check as geom
O=R/'Hardware/PoseDoll44/bench/revO22/a1mini_fins_v4';pid='X066';parent='contact110';label='low_tab113';src=O/'candidates'/pid/parent;dst=O/'candidates'/pid/label
for sub in ['parts','design','verification']:(dst/sub).mkdir(parents=True,exist_ok=True)
n=dict(np.load(src/'parts'/f'{pid}.npz'));d=json.loads((src/'design'/f'{pid}.json').read_text());q=json.loads((src/'verification/full_bead_contacts_v5.json').read_text());it=json.loads((src/'verification/plate_manifest.json').read_text())['items'][0];M=np.array(it['rotation_matrix']);off=np.array(it['translation_mm']);s=solid(n['v'],n['f']);fin=solid(n['fin_v'],n['fin_f']);teeth=solid(n['teeth_v'],n['teeth_f']);added=[]
for issue in q['external_islands']+q['critical_external_runs']:
 if issue['z_mm']>2:continue
 b=issue['bounds_mm'];p=(np.array([(b[0]+b[2])/2,(b[1]+b[3])/2,issue['z_mm']-.1])-off)@M;foot=md.CrossSection.square([4,4]).translate(p[:2]-2);blocked=(s^box([-300,-300,-.1],[300,300,.55])).project().offset(.24,circular_segments=12);core=(foot-blocked).extrude(.2);tt=box([p[0]-.5,p[1]-.5,.14],[p[0]+.5,p[1]+.5,p[2]+.3]);core=union([c for c in material_components(core)if(c^tt).volume()>.005]);bite=float((tt^s).volume());root=float((tt^core).volume());gap=float(core.min_gap(s,.5));print('LOW_TAB113_PROPOSAL',bite,root,gap,core.volume(),flush=True)
 if bite<.005 or root<.005 or gap<.235 or(core^s).volume()>1e-6:continue
 fin=fin+core;teeth=teeth+tt;num=len(d['segments'])+1;d['segments'].append({'number':num,'bounds_mm':list(core.bounding_box()),'height_mm':.2,'blade_width_mm':4.,'blade_thickness_mm':4.,'teeth_count':1,'brace_count':0,'on_build_plate':True,'vertical_bed_path':True,'min_gap_mm':gap,'removal_vector':[0,0,-1],'very_low_breakaway_bed_tab':True});d['teeth'].append({'fin_number':num,'bounds_mm':list(tt.bounding_box()),'part_bite_mm3':bite,'fin_root_mm3':root,'nominal_tip_penetration_mm':.3,'neck_xy_mm':[1,1],'contact_point_mm':p.tolist()});added.append(issue)
n['fin_v'],n['fin_f']=vf(fin);n['teeth_v'],n['teeth_f']=vf(teeth);d.update(support_count=len(d['segments']),support_volume_mm3=float((fin+teeth).volume()),low_tabs113=added);np.savez_compressed(dst/'parts'/f'{pid}.npz',**n);(dst/'design'/f'{pid}.json').write_text(json.dumps(d,ensure_ascii=False,indent=2),encoding='utf8');g=geom(pid,label)
if added and g['geometric_constraints_passed']:run(pid,label);check(pid,label);refine(pid,label)
