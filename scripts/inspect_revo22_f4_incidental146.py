from pathlib import Path
import sys,json,numpy as np
R=Path.cwd();sys.path.insert(0,str(R/'scripts'))
import repair_revo22_f4_guarded_chamfer as ctx
import build_revo22_assembly as assembly
from build_revo22_fins import solid
from o22_reference_mesh import reference_solid
O=ctx.O;pid='P033';label='access124';p=O/'candidates'/pid/label;n=np.load(p/'parts'/f'{pid}.npz');d=json.loads((p/'design'/f'{pid}.json').read_text());parts,key,T=ctx.context(d,pid);parts,meta,base,*_=ctx.CACHE;f0,o0=assembly.owners(base);rng=np.random.default_rng(22);poses={}
for j in range(12):poses['combined_'+str(j)]={k:float(rng.uniform(*v))for k,v in assembly.profile['raw_limits_deg'].items()}
rep=json.loads((p/'verification/body_change_fit_and_pose.json').read_text());old=reference_solid(n,d).transform(np.linalg.inv(T)[:3,:]);new=solid(n['v'],n['f']).transform(np.linalg.inv(T)[:3,:]);rows=[]
for event in rep['sampled_contact_changes_at_nonintersecting_baseline_poses']:
 pose=poses[event['pose']];f,o=assembly.owners(pose)
 def tr(k):
  m=meta[k];return f[m['body']]@np.linalg.inv(f0[m['body']])if m['owner']=='rigid_frame'else o[(m['module'],m['owner'])]@np.linalg.inv(o0[(m['module'],m['owner'])])
 other=event['part'];a=old.transform(tr(key)[:3,:]);b=new.transform(tr(key)[:3,:]);neighbor=parts[other].transform(tr(other)[:3,:]);row={'event':event,'part_metadata':meta[key],'neighbor_metadata':meta[other],'old_whole_body_gap_mm':float(a.min_gap(neighbor,.5)),'new_whole_body_gap_mm':float(b.min_gap(neighbor,.5)),'old_actual_intersection_mm3':float((a^neighbor).volume()),'new_actual_intersection_mm3':float((b^neighbor).volume()),'new_material_added_mm3':float((b-a).volume())};rows.append(row)
report={'id':pid,'candidate':label,'body_mesh_sha256':rep['body_mesh_sha256'],'scope':'Read-only measurement of actual whole-part distance for non-contact proximity flags; no approval rules changed.','measurements':rows};(p/'verification/incidental_clearance146.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8');print(json.dumps(report,ensure_ascii=False,indent=2),flush=True)
