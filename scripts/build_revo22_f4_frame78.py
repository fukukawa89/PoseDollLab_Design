from pathlib import Path
import sys,json,numpy as np,concurrent.futures,traceback
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'scripts'))
import build_revo22_fins_v4 as builder
from build_revo22_f4_coverage_candidates import ITEMS,VOLS
from build_revo22_fins import solid,vf,md
from slice_revo22_f4_candidate import run
from verify_revo22_f4_full_bead import check
from refine_revo22_f4_full_bead import refine
from repair_revo22_f4_broad_short_targets import repair as sides
from repair_revo22_f4_low_portal72 import trial as portal
from repair_revo22_f4_recessed_portal76 import trial as recessed
from verify_revo22_f4_body_change import check as fit
from verify_revo22_f4_repaired_geometry import check as geom
B=R/'Hardware/PoseDoll44/bench/revO22';O=B/'a1mini_fins_v4';beds={q['id']:q['bed']for q in json.loads((B/'print_batch/manifest.json').read_text())['rows']}
def one(spec):
 pid,donor,donorlabel=spec.split(':');label='frame78';out=[]
 try:
  dd=json.loads((O/'candidates'/donor/donorlabel/'design'/f'{donor}.json').read_text());M=np.array(dd['orientation']['matrix'])@np.array(beds[donor]['rotation'])@np.array(beds[pid]['rotation']).T;original=np.load(B/'O22F3_Release/reference/parts'/f'{pid}.npz');v=original['source_v'];f=original['f'];nominal=None;certp=R/'.local/o22-nominal-reference'/f'{pid}.json'
  if certp.exists():
   cert=json.loads(certp.read_text());nv=np.load(certp.with_suffix('.npz'))
   if cert['nominal_reference_qualified']:
    tv=nv['v']@M.T;ss=solid(tv-tv.min(0),nv['f'])
    if abs((ss-ss).volume())<1e-6:v=nv['v'];f=nv['f'];nominal=cert
  vv=v@M.T;t=-vv.min(0);ori={'matrix':M.tolist(),'source_translation_mm':t.tolist(),'gravity_in_source':M[2].tolist(),'size_mm':np.ptp(vv,axis=0).tolist()};assert max(ori['size_mm'])<174;folder=O/'candidates'/pid/label
  for sub in ['parts','design','verification','figures']:(folder/sub).mkdir(parents=True,exist_ok=True)
  builder.O=folder;builder.read_mesh=lambda _:(v,f);builder.choose=lambda _:ori;builder.AXIS=None;builder.FACE_FILTER=None;builder.PITCH_OVERRIDE=3.2;builder.THICKNESS_OVERRIDE=None;builder.NORMAL_THRESHOLD=-.3;builder.SEGMENT_OVERRIDE=None;builder.make(pid,ITEMS[pid],VOLS.get(pid,[]));n=dict(np.load(folder/'parts'/f'{pid}.npz'));d=json.loads((folder/'design'/f'{pid}.json').read_text());d['functional_frame_orientation_donor']={'id':donor,'label':donorlabel,'method':'Map only the print orientation through each original owner-local to print-bed rotation. All target body dimensions are retained; supports are rebuilt for this target.'}
  if nominal:
   n['source_v']=original['source_v'];n['source_f']=original['f'];n['nominal_source_v']=v;n['nominal_source_f']=f;n['removed_body_v'],n['removed_body_f']=vf(md.Manifold());d['nominal_reference']=nominal;d['source_mesh_preserved']=False;d['body_change']={'kind':'nominal_cad_precision_recovery','removed_volume_mm3':0.,'added_volume_mm3':0.,'chamfers':[],'source_body_volume_mm3':float(solid(n['v'],n['f']).volume()),'assembly_contact_validation_pending':True}
  np.savez_compressed(folder/'parts'/f'{pid}.npz',**n);(folder/'design'/f'{pid}.json').write_text(json.dumps(d,ensure_ascii=False,indent=2),encoding='utf8');run(pid,label);check(pid,label);q=refine(pid,label)
  for suffix,func in [('_side',sides),('_portal',portal),('_recessed',recessed)]:
   out.append({k:q[k]for k in['id','label','external_island_count','critical_external_count','native_review_resolved']});print('FRAME78_STEP',out[-1],flush=True)
   if q['native_review_resolved']:break
   new=label+suffix;func(pid,label,new)
   if (O/'candidates'/pid/new/'verification/local_extrusion.json').exists():label=new;q=refine(pid,label)
  if q['native_review_resolved']:
   if nominal:fit(pid,label)
   geom(pid,label)
  return {'id':pid,'results':out,'final_label':label,'native_clear':q['native_review_resolved']}
 except Exception:return {'id':pid,'results':out,'error':traceback.format_exc()}
if __name__=='__main__':
 out=[]
 with concurrent.futures.ProcessPoolExecutor(max_workers=2)as pool:
  for f in concurrent.futures.as_completed([pool.submit(one,s)for s in sys.argv[1:]]):
   out.append(f.result());(O/'frame78_progress.json').write_text(json.dumps(out,indent=2))
