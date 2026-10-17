from pathlib import Path
import sys,json,numpy as np
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'scripts'))
from repair_revo22_f4_guarded_chamfer import context,O
from build_revo22_fins import solid,vf,union,md
from o22_reference_mesh import reference_solid
from slice_revo22_f4_candidate import run
from verify_revo22_f4_full_bead import check
from refine_revo22_f4_full_bead import refine
from verify_revo22_f4_body_change import check as fit
from verify_revo22_f4_repaired_geometry import check as geom
pid='P049';parent='portal83';label='bearing_finish85';src=O/'candidates'/pid/parent;dst=O/'candidates'/pid/label
for sub in ['parts','design','verification']:(dst/sub).mkdir(parents=True,exist_ok=True)
n=dict(np.load(src/'parts'/f'{pid}.npz'));d=json.loads((src/'design'/f'{pid}.json').read_text());old=reference_solid(n,d);body=solid(n['v'],n['f']);parts,key,T=context(d,pid);guards=[];rows=[]
for name,margin in [('upperarm_l/C01_magnet_nut_6.1',1.2),('upperarm_l/C01_magnet_cartridge',.1)]:
 v=vf(parts[name])[0];offset=np.array([[x,y,z]for x in[-margin,margin]for y in[-margin,margin]for z in[-margin,margin]]);guard=md.Manifold.hull_points((v[:,None,:]+offset[None,:,:]).reshape(-1,3)).transform(T[:3,:]);restore=(old-body)^guard;guards.append(restore);rows.append({'hardware':name,'source_material_restored_mm3':float(restore.volume()),'convex_guard_margin_mm':margin})
new=body+union(guards);delta=old-new;assert(new-old).volume()<1e-6;assert(solid(n['fin_v'],n['fin_f'])^new).volume()<1e-6;n['v'],n['f']=vf(new);n['removed_body_v'],n['removed_body_f']=vf(delta);d['body_change'].update(removed_volume_mm3=float(delta.volume()),bearing_final_restoration=rows);np.savez_compressed(dst/'parts'/f'{pid}.npz',**n);(dst/'design'/f'{pid}.json').write_text(json.dumps(d,ensure_ascii=False,indent=2),encoding='utf8');print('BEARING85_RESTORED',rows,flush=True);f=fit(pid,label);run(pid,label);check(pid,label);q=refine(pid,label);geom(pid,label);print('BEARING85_RESULT',f['fit_and_pose_geometry_passed'],q['native_review_resolved'],flush=True)
