from pathlib import Path
import sys,json,numpy as np
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'scripts'))
from repair_revo22_f4_guarded_chamfer import context,O
from build_revo22_fins import solid,vf,union,md,box
from o22_reference_mesh import reference_solid
from slice_revo22_f4_candidate import run
from verify_revo22_f4_full_bead import check
from refine_revo22_f4_full_bead import refine
from verify_revo22_f4_body_change import check as fit
from verify_revo22_f4_repaired_geometry import check as geom

def trial(pid,parent,label):
 src=O/'candidates'/pid/parent;dst=O/'candidates'/pid/label
 for sub in ['parts','design','verification']:(dst/sub).mkdir(parents=True,exist_ok=True)
 n=dict(np.load(src/'parts'/f'{pid}.npz'));d=json.loads((src/'design'/f'{pid}.json').read_text());old=reference_solid(n,d);body=solid(n['v'],n['f']);removed=old-body;parts,key,T=context(d,pid)
 import repair_revo22_f4_guarded_chamfer as ctx
 rows=[];guards=[]
 for k,s in parts.items():
  if k==key:continue
  sku=ctx.CACHE[1][k].get('sku')or''
  if not (sku.startswith('W_')or sku.startswith('NUT_')):continue
  sp=s.transform(T[:3,:])
  if removed.min_gap(sp,1.5)>=1.5:continue
  # Restore the source plastic in a full 1.2 mm contact/backing envelope around each affected actual washer or nut.
  guard=union([sp.translate([x,y,z])for x in [-1.2,0,1.2]for y in[-1.2,0,1.2]for z in[-1.2,0,1.2]])
  restored=removed^guard
  if restored.volume()>1e-7:guards.append(guard);rows.append({'hardware':k,'restored_volume_mm3':float(restored.volume()),'source_only':True})
 new=body+(removed^union(guards));delta=old-new;assert (new-old).volume()<1e-6
 fin=solid(n['fin_v'],n['fin_f']);assert (fin^new).volume()<1e-6,'Restored bearing overlaps fin; redesign fin first'
 n['v'],n['f']=vf(new);n['removed_body_v'],n['removed_body_f']=vf(delta);d['body_change'].update(removed_volume_mm3=float(delta.volume()),added_volume_mm3=0.,restored_bearing_backing=rows,assembly_contact_validation_pending=True);np.savez_compressed(dst/'parts'/f'{pid}.npz',**n);(dst/'design'/f'{pid}.json').write_text(json.dumps(d,ensure_ascii=False,indent=2),encoding='utf8');print('RESTORED',pid,rows,'remaining removed',delta.volume(),flush=True)
 f=fit(pid,label)
 run(pid,label);check(pid,label);q=refine(pid,label)
 if q['native_review_resolved']and f['fit_and_pose_geometry_passed']:geom(pid,label)
 print('RESTORE79',pid,q['native_review_resolved'],f['fit_and_pose_geometry_passed'],flush=True)
if __name__=='__main__':trial(*sys.argv[1:])
