"""Restore exact source washer bearing material, never add material outside the frozen part."""
from pathlib import Path
import sys,json,numpy as np,concurrent.futures,traceback
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'scripts'))
from repair_revo22_f4_guarded_chamfer import context,O
from build_revo22_fins import solid,vf,union,md
from o22_reference_mesh import reference_solid
from o22_cross_section_geometry import polygon
from verify_revo22_f4_body_change import check as fit
from verify_revo22_f4_repaired_geometry import check as geom
from slice_revo22_f4_candidate import run
from verify_revo22_f4_full_bead import check
from refine_revo22_f4_full_bead import refine

def trial(spec):
 pid,parent=spec.split(':');label='bearing101';src=O/'candidates'/pid/parent;dst=O/'candidates'/pid/label
 for sub in ['parts','design','verification']:(dst/sub).mkdir(parents=True,exist_ok=True)
 n=dict(np.load(src/'parts'/f'{pid}.npz'));d=json.loads((src/'design'/f'{pid}.json').read_text());original=reference_solid(n,d);body=solid(n['v'],n['f']);parts,key,T=context(d,pid);rows=[];restores=[]
 wr=json.loads((src/'verification/washer_contact_surfaces.json').read_text())
 for item in wr:
  if item['entry_chamfer_geometric_criteria_passed']:continue
  v=vf(parts[item['part']])[0];center=v.mean(0);_,Q=np.linalg.eigh(np.cov((v-center).T));axis=Q[:,0];u=Q[:,1];A=np.array([u,np.cross(axis,u),axis]);inv=np.c_[A.T,center];w=parts[item['part']].transform(np.c_[A,-A@center]);wb=w.bounding_box();outer=float(np.linalg.norm(vf(w)[0][:,:2],axis=1).max());gs=[]
  for face in item['contact_sides']:
   if face['original_contact_area_mm2']<=.1:continue
   z=face['z'];direction=1 if z>wb[5] else -1
   if face['outer_1mm_bearing_ring_lost_volume_mm3']>1e-6:
    ring=md.Manifold.cylinder(1.025,outer+.012,outer+.012,192)-md.Manifold.cylinder(1.03,max(0,outer-1.012),max(0,outer-1.012),192)
    gs.append(ring.translate([0,0,z-.012 if direction>0 else z-1.013]))
   if face['retained_fraction']<.98:
    disk=md.Manifold.cylinder(.26,outer+.012,outer+.012,192);gs.append(disk.translate([0,0,z-.012 if direction>0 else z-.248]))
  guard=union(gs).transform(inv).transform(T[:3,:]);restored=(original-body)^guard;restores.append(restored);rows.append({'hardware':item['part'],'restored_source_volume_mm3':float(restored.volume()),'method':'Actual washer-axis outer 1 mm bearing ring backed by 1 mm of source plastic; when necessary the original annular contact surface is also restored through 0.24 mm.'})
 new=body+union(restores);fin=solid(n['fin_v'],n['fin_f']);delta=original-new;print('BEARING101_PROPOSAL',pid,rows,'fin_overlap',float((fin^new).volume()),'gap',float(fin.min_gap(new,.5)),flush=True)
 assert(new-original).volume()<1e-6;assert(fin^new).volume()<1e-6
 n['v'],n['f']=vf(new);n['removed_body_v'],n['removed_body_f']=vf(delta);d['body_change'].update(removed_volume_mm3=float(delta.volume()),added_volume_mm3=0.,actual_washer_backing_restored=rows);np.savez_compressed(dst/'parts'/f'{pid}.npz',**n);(dst/'design'/f'{pid}.json').write_text(json.dumps(d,ensure_ascii=False,indent=2),encoding='utf8');f=fit(pid,label);g=geom(pid,label)
 if f['fit_and_pose_geometry_passed']and g['geometric_constraints_passed']:
  run(pid,label);check(pid,label);q=refine(pid,label);print('BEARING101_NATIVE',pid,q['external_island_count'],q['critical_external_count'],flush=True)
 return {'id':pid,'fit':f['fit_and_pose_geometry_passed'],'geometry':g['geometric_constraints_passed']}
if __name__=='__main__':
 with concurrent.futures.ProcessPoolExecutor(max_workers=2)as p:
  for f in concurrent.futures.as_completed([p.submit(trial,q)for q in sys.argv[1:]]):
   try:print('BEARING101_END',f.result(),flush=True)
   except Exception:traceback.print_exc()
