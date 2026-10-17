from pathlib import Path
import sys,json,shutil
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'scripts'))
from inspect_revo22_f4_washer_contacts import assess
from select_revo22_f4_repairs import select
from o22_mesh_identity import body_sha
import numpy as np
O=R/'Hardware/PoseDoll44/bench/revO22/a1mini_fins_v4'
rows=select();out=[]
for q in rows:
 if not q['fit_passed']:continue
 p=O/'candidates'/q['id']/q['label'];fp=p/'verification/body_change_fit_and_pose.json';f=json.loads(fp.read_text());n=np.load(p/'parts'/f"{q['id']}.npz");assert f['body_mesh_sha256']==body_sha(n)
 if not f.get('qualified_small_washer_entry_chamfers'):continue
 if not fp.with_name('body_change_fit_and_pose_pre_washer_axis81.json').exists():shutil.copy2(fp,fp.with_name('body_change_fit_and_pose_pre_washer_axis81.json'))
 washers=assess(q['id'],q['label']);allowed={x['part']for x in washers if x['entry_chamfer_geometric_criteria_passed']}|{x['part']for x in f.get('qualified_small_nut_corner_reliefs',[])if x['qualified_corner_relief']}|{x['part']for x in f.get('qualified_small_screw_clearance_chamfers',[])if x['qualified_clearance_corner_relief']}|{x['part']for x in f.get('qualified_magnet_retention_entry_reliefs',[])if x['qualified_magnet_retention_entry_relief']};close=[x for x in f['assembly_contacts']if x['gap_mm']<.08 and x['intersection_with_neighbor_shape_margin_008_mm3']>1e-6];motion=f['sampled_contact_changes'];remain=[x for x in motion if x['existing_overlap_mm3']<.01 and not(x['part']in allowed and x.get('same_rigid_motion',False))];f.update(qualified_small_washer_entry_chamfers=washers,all_other_base_contacts_clear=not[x for x in close if x['part']not in allowed],sampled_contact_changes_at_nonintersecting_baseline_poses=remain,washer_contact_axis_method='actual_disk_pca_axis81');f['fit_and_pose_geometry_passed']=f['purely_subtractive']and f['all_other_base_contacts_clear']and not remain and f['frozen_print_source_exactly_verified']and f['body_component_count_unchanged'];fp.write_text(json.dumps(f,ensure_ascii=False,indent=2),encoding='utf8');out.append({'id':q['id'],'label':q['label'],'fit_passed':f['fit_and_pose_geometry_passed']});print('WASHER81_REVIEW',out[-1],flush=True)
(O/'washer_axis81_revalidation.json').write_text(json.dumps(out,indent=2));select()
