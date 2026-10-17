from pathlib import Path
import json,sys,concurrent.futures,traceback
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'scripts'))
from verify_revo22_f4_local_extrusion import check
B=R/'Hardware/PoseDoll44/bench/revO22';O=B/'a1mini_fins_v4/audit/native_baseline'
def one(args):
 engine,path=args;dest=O/engine/(path.stem+'.json')
 try:
  r=check(path,dest)
  return {'engine':engine,'plate':path.stem.split('_')[0],'detached':len(r['detached_bead_regions']),'unresolved':r['unresolved_count'],'max_mm':r['max_unresolved_span_mm'],'report':str(dest)}
 except Exception:return {'engine':engine,'plate':path.stem,'error':traceback.format_exc()}
if __name__=='__main__':
 tasks=[(e,p) for e,d in [('Orca','projects'),('Bambu','crosscheck_bambu')] for p in (B/'O22F3_Release'/d).glob('*.3mf')];rows=[]
 O.mkdir(parents=True,exist_ok=True)
 with concurrent.futures.ProcessPoolExecutor(max_workers=4) as pool:
  for r in pool.map(one,tasks):
   rows.append(r);(O/'progress.json').write_text(json.dumps({'completed':len(rows),'total':len(tasks),'parts':rows},ensure_ascii=False,indent=2),encoding='utf8');print('NATIVE_BASELINE_RESULT',r,flush=True)
 (O/'all_plates.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2),encoding='utf8')
