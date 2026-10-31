from pathlib import Path
import sys,json,concurrent.futures,traceback
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'scripts'))
from verify_revo22_f4_local_extrusion import check
O=R/'Hardware/PoseDoll44/bench/revO22/a1mini_fins_v4'
def one(choice):
 pid=choice['id'];label=choice['label'];folder=O/'candidates'/pid/label;dest=folder/'verification/local_extrusion.json'
 try:
  if dest.exists():
   old=json.loads(dest.read_text(encoding='utf8'))
   if old.get('audit_schema')=='local-extrusion-v2-preserve-nested-islands':r=old
   else:
    archive=dest.with_name('local_extrusion_superseded_polygon_holes.json');assert not archive.exists();dest.rename(archive);r=check(next((folder/'projects').glob('*.3mf')),dest)
  else:r=check(next((folder/'projects').glob('*.3mf')),dest)
  return {'id':pid,'label':label,'detached':len(r['detached_bead_regions']),'unresolved':r['unresolved_count'],'max_span_mm':r['max_unresolved_span_mm'],'native_slicing_complete':True,'audit_schema':r['audit_schema']}
 except Exception:return {'id':pid,'label':label,'error':traceback.format_exc()}
if __name__=='__main__':
 choices=json.loads((O/'native_review_choices.json').read_text(encoding='utf8'));rows=[]
 with concurrent.futures.ProcessPoolExecutor(max_workers=3) as pool:
  futures={pool.submit(one,c):c for c in choices}
  for f in concurrent.futures.as_completed(futures):
   q=f.result();rows.append(q);(O/'native_candidate_progress_v2.json').write_text(json.dumps({'completed':len(rows),'total':len(choices),'results':rows},ensure_ascii=False,indent=2),encoding='utf8');print('CANDIDATE_V2',q,flush=True)
 print('NATIVE_CANDIDATES_V2_COMPLETE',len(rows),flush=True)

