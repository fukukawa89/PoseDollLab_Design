from pathlib import Path
import sys,json,numpy as np,concurrent.futures,traceback
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'scripts'))
from search_revo22_f2_orientations import frame
import build_revo22_fins_v4 as builder
from build_revo22_f4_coverage_candidates import ITEMS,VOLS
from slice_revo22_f4_candidate import run
from verify_revo22_f4_full_bead import check
from refine_revo22_f4_full_bead import refine
from repair_revo22_f4_broad_short_targets import repair
B=R/'Hardware/PoseDoll44/bench/revO22';O=B/'a1mini_fins_v4'
def one(sign):
 pid='X046';label='box62_'+('up' if sign==1 else 'down');folder=O/'candidates'/pid/label
 try:
  meta=json.loads((B/'mechanical/assembly_metadata.json').read_text());A=np.array(meta['meta']['frame/chest']['transform']);A[:3,1]*=1 if np.linalg.det(A[:3,:3])>0 else -1;bed=next(x['bed'] for x in json.loads((B/'print_batch/manifest.json').read_text())['rows'] if x['id']==pid);G=np.array(bed['rotation'])@A[:3,:3].T@(np.array([-1.,0,0])*sign);M=frame(G);n=np.load(B/'O22F3_Release/reference/parts'/f'{pid}.npz');vv=n['source_v']@M.T;t=-vv.min(0);ori={'matrix':M.tolist(),'source_translation_mm':t.tolist(),'gravity_in_source':G.tolist(),'size_mm':np.ptp(vv,axis=0).tolist()};print('BOX_ORIENTATION',label,ori,flush=True)
  for s in ['parts','design','verification','figures']:(folder/s).mkdir(parents=True,exist_ok=True)
  builder.O=folder;builder.choose=lambda _:ori;builder.AXIS=None;builder.FACE_FILTER=None;builder.PITCH_OVERRIDE=4.;builder.NORMAL_THRESHOLD=-.3;builder.make(pid,ITEMS[pid],VOLS.get(pid,[]));run(pid,label);check(pid,label);d=refine(pid,label)
  if not d['native_review_resolved']:
   repair(pid,label,label+'_short');label+='_short';d=refine(pid,label)
  out={k:d[k] for k in ['id','label','external_island_count','critical_external_count','native_review_resolved']};print('BOX62_RESULT',out,flush=True);return out
 except Exception:return {'label':label,'error':traceback.format_exc()}
if __name__=='__main__':
 with concurrent.futures.ProcessPoolExecutor(max_workers=2) as pool:
  out=list(pool.map(one,[1,-1]));(O/'box62_progress.json').write_text(json.dumps(out,indent=2))
