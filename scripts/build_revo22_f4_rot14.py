from pathlib import Path
import sys,json,concurrent.futures,traceback
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'scripts'))
import build_revo22_fins_v4 as builder
from build_revo22_f4_coverage_candidates import ITEMS,VOLS
from slice_revo22_f4_candidate import run
from verify_revo22_f4_full_bead import check
from repair_revo22_f4_fast_paths import repair as full
from repair_revo22_f4_lower_root_targets import repair as lower
from verify_revo22_f4_repaired_geometry import check as geom
O=R/'Hardware/PoseDoll44/bench/revO22/a1mini_fins_v4'
def one(spec):
 pid,index=spec;label='rot14_'+str(index).zfill(2);folder=O/'candidates'/pid/label
 try:
  option=json.loads((O/'orientation_fine'/f'{pid}.json').read_text())['best'][index]
  for d in ['parts','design','verification','figures']:(folder/d).mkdir(parents=True,exist_ok=True)
  builder.O=folder;builder.choose=lambda _:option['orientation'];builder.AXIS=None;builder.FACE_FILTER=None;builder.PITCH_OVERRIDE=3.2 if option['orientation']['size_mm'][2]<50 else 4.;builder.THICKNESS_OVERRIDE=None;builder.NORMAL_THRESHOLD=-.3;builder.SEGMENT_OVERRIDE=None
  if not (folder/'parts'/f'{pid}.npz').exists():builder.make(pid,ITEMS[pid],VOLS.get(pid,[]))
  if not (folder/'verification/local_extrusion.json').exists():run(pid,label)
  d=check(pid,label)
  for suffix,func in [('_full',full),('_lower',lower)]:
   if d['native_review_resolved']:break
   new=label+suffix;func(pid,label,new);label=new;d=check(pid,label)
  if d['native_review_resolved']:geom(pid,label)
  result={k:d[k] for k in ['id','label','external_island_count','critical_external_count','native_review_resolved']};print('ROT14_RESULT',result,flush=True);return result
 except Exception:return {'id':pid,'label':label,'error':traceback.format_exc()}
if __name__=='__main__':
 specs=[(s.split(':')[0],int(s.split(':')[1])) for s in sys.argv[1:]];out=[]
 with concurrent.futures.ProcessPoolExecutor(max_workers=2) as pool:
  for f in concurrent.futures.as_completed([pool.submit(one,s) for s in specs]):
   out.append(f.result());(O/'rot14_progress.json').write_text(json.dumps(out,indent=2))
