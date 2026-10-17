from pathlib import Path
import sys,json,numpy as np,concurrent.futures,traceback
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'scripts'))
from select_revo22_f4_repairs import select,O
from o22_reference_mesh import reference_mesh
from build_revo22_fins import solid,vf,md
from slice_revo22_f4_candidate import run
from verify_revo22_f4_full_bead import check
from verify_revo22_f4_body_change import check as fit
from verify_revo22_f4_repaired_geometry import check as geom
D=R/'.local/o22-nominal-reference'
def one(q):
 pid=q['id'];label='nominal32';src=O/'candidates'/pid/q['label'];dst=O/'candidates'/pid/label
 try:
  report=json.loads((D/f'{pid}.json').read_text());assert report['nominal_reference_qualified'];ref=np.load(D/f'{pid}.npz');n=dict(np.load(src/'parts'/f'{pid}.npz'));d=json.loads((src/'design'/f'{pid}.json').read_text());assert d.get('body_change',{}).get('removed_volume_mm3',0)<1e-6
  n['source_f']=n['f'].copy();n['nominal_source_v']=ref['v'];n['nominal_source_f']=ref['f'];d['nominal_reference']=report;rv,rf=reference_mesh(n,d);n['v']=rv@np.array(d['orientation']['matrix']).T+np.array(d['orientation']['source_translation_mm']);n['f']=rf.copy();s=solid(n['v'],n['f']);identity=float((s-s).volume());assert abs(identity)<1e-6,identity
  n['removed_body_v'],n['removed_body_f']=vf(md.Manifold());d['source_mesh_preserved']=False;d['body_change']={'kind':'nominal_cad_precision_recovery','removed_volume_mm3':0.,'added_volume_mm3':0.,'source_body_volume_mm3':float(s.volume()),'removed_fraction':0.,'chamfers':[],'outer_bounds_unchanged_within_mm':report['max_bidirectional_sampled_boundary_distance_mm'],'reason':'Recover the unchanged analytic CAD triangulation after the frozen rounded mesh failed a self-difference identity control. No design dimension is changed; measured boundary agreement is retained in nominal_reference.'};d['source_recovery_parent']=q['label']
  for sub in ['parts','design','verification']:(dst/sub).mkdir(parents=True,exist_ok=True)
  np.savez_compressed(dst/'parts'/f'{pid}.npz',**n);(dst/'design'/f'{pid}.json').write_text(json.dumps(d,ensure_ascii=False,indent=2),encoding='utf8');run(pid,label);r=check(pid,label);fr=fit(pid,label);g=geom(pid,label);out={k:r[k] for k in ['id','label','external_island_count','critical_external_count','native_review_resolved']};out['fit']=fr['fit_and_pose_geometry_passed'];out['geometry']=g['geometric_constraints_passed'];print('NOMINAL32_RESULT',out,flush=True);return out
 except Exception:return {'id':pid,'error':traceback.format_exc()}
if __name__=='__main__':
 ids=set(sys.argv[1:]);jobs=[q for q in select() if q['id'] in ids];out=[]
 with concurrent.futures.ProcessPoolExecutor(max_workers=2) as pool:
  for f in concurrent.futures.as_completed([pool.submit(one,q) for q in jobs]):
   out.append(f.result());(O/'nominal32_progress.json').write_text(json.dumps(out,indent=2))
