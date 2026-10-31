"""Restore frozen source material within a flagged sampled-pose neighbor clearance envelope."""
from pathlib import Path
import sys,json,numpy as np
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'scripts'))
import repair_revo22_f4_guarded_chamfer as ctx
import build_revo22_assembly as assembly
from build_revo22_fins import solid,vf,union,md
from o22_reference_mesh import reference_solid
from verify_revo22_f4_body_change import check as fit
from verify_revo22_f4_repaired_geometry import check as geom
from slice_revo22_f4_candidate import run
from verify_revo22_f4_full_bead import check
from refine_revo22_f4_lateral104 import check as refine
O=ctx.O;pid='P033';parent='access124';label='pose_restore130';src=O/'candidates'/pid/parent;dst=O/'candidates'/pid/label
for sub in ['parts','design','verification']:(dst/sub).mkdir(parents=True,exist_ok=True)
n=dict(np.load(src/'parts'/f'{pid}.npz'));d=json.loads((src/'design'/f'{pid}.json').read_text());rep=json.loads((src/'verification/body_change_fit_and_pose.json').read_text());parts,key,T=ctx.context(d,pid);parts,meta,base,*_=ctx.CACHE;f0,o0=assembly.owners(base);profile=assembly.profile;poses={'base':base,'neutral':profile['neutral_raw_deg'],'default':json.loads((O.parent/'profiles/default_pose.json').read_text())['raw_deg']}
for raw,limits in profile['raw_limits_deg'].items():
 for side,val in zip(['min','max'],limits):q=profile['neutral_raw_deg'].copy();q[raw]=val;poses[raw+'/'+side]=q
rng=np.random.default_rng(22)
for j in range(12):poses['combined_'+str(j)]={k:float(rng.uniform(*v))for k,v in profile['raw_limits_deg'].items()}
original=reference_solid(n,d);body=solid(n['v'],n['f']);restores=[];rows=[]
for event in rep['sampled_contact_changes_at_nonintersecting_baseline_poses']:
 pose=poses[event['pose']];f,o=assembly.owners(pose)
 def tr(k):
  m=meta[k];return f[m['body']]@np.linalg.inv(f0[m['body']])if m['owner']=='rigid_frame'else o[(m['module'],m['owner'])]@np.linalg.inv(o0[(m['module'],m['owner'])])
 other=event['part'];rel=np.linalg.inv(tr(key))@tr(other);v=vf(parts[other])[0];ofs=np.array([[x,y,z]for x in[-.10,.10]for y in[-.10,.10]for z in[-.10,.10]]);guard=md.Manifold.hull_points((v[:,None,:]+ofs[None,:,:]).reshape(-1,3)).transform(rel[:3,:]).transform(T[:3,:]);restore=(original-body)^guard;restores.append(restore);rows.append({'pose':event['pose'],'neighbor':other,'source_volume_restored_mm3':float(restore.volume()),'clearance_guard_mm':.1})
new=body+union(restores)
from o22_material_components import material_components
from build_revo22_fins import box
floating=[c for c in material_components(new) if float((c^body).volume())<1e-6]
for c in floating:
 bb=np.array(c.bounding_box())
 for pad in [.2,.4,.6,.8,1.,1.5]:
  connector=original^box(bb[:3]-pad,bb[3:]+pad);proposal=new+connector
  if len(material_components(proposal))==len(material_components(original)):
   restored=float((proposal-body).volume());assert restored<3.;new=proposal;rows.append({'source_only_continuity_restoration_mm3':restored,'padding_mm':pad});break
 else:raise ValueError('Cannot attach restored source corner without extending bounded ROI')
delta=original-new;fin=solid(n['fin_v'],n['fin_f']);print('POSE_RESTORE127',rows,'fin_overlap',float((fin^new).volume()),flush=True);assert(fin^new).volume()<1e-6 and(new-original).volume()<1e-6;n['v'],n['f']=vf(new);n['removed_body_v'],n['removed_body_f']=vf(delta);d['body_change'].update(removed_volume_mm3=float(delta.volume()),sampled_pose_contact_restoration=rows);np.savez_compressed(dst/'parts'/f'{pid}.npz',**n);(dst/'design'/f'{pid}.json').write_text(json.dumps(d,ensure_ascii=False,indent=2),encoding='utf8');f=fit(pid,label);g=geom(pid,label)
if f['fit_and_pose_geometry_passed']and g['geometric_constraints_passed']:run(pid,label);check(pid,label);q=refine(pid,label);print('POSE_RESTORE127_NATIVE',q['external_island_count'],q['critical_external_count'],flush=True)
