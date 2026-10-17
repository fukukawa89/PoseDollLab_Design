import json,time,concurrent.futures,traceback
from build_revo22_fins_v2 import O
from verify_revo22_f2_extrusions import check_project

def run_one(p):
 return check_project(O/'projects'/f"{p['id']}_O22F2_PLA_fins.3mf",p)
if __name__=='__main__':
 manifest=O/'manifest.json';stamp=manifest.stat().st_mtime;plates=json.loads(manifest.read_text())['plates'];pending={p['id']:p for p in plates};futures={};start=time.time()
 with concurrent.futures.ProcessPoolExecutor(max_workers=3) as pool:
  while pending or futures:
   for pid,p in list(pending.items()):
    dest=O/'projects'/f'{pid}_O22F2_PLA_fins.3mf'
    if dest.exists() and dest.stat().st_mtime>stamp and len(futures)<3:
     # Export completion is atomic only after the slicer writes its result report.
     report=O/'verification'/f'{pid}_slice.json'
     if report.exists() and report.stat().st_mtime>stamp:
      futures[pool.submit(run_one,p)]=pid;pending.pop(pid);print('START',pid,flush=True)
   for f,pid in list(futures.items()):
    if f.done():
     try:r=f.result();print('DONE',pid,'floats',len(r['floating_printed_components']),'missing_teeth',r['teeth_missing_printed_layer'],flush=True)
     except Exception:print('ERROR',pid,traceback.format_exc(),flush=True)
     futures.pop(f)
   if time.time()-start>3600:raise TimeoutError('Final slicing pipeline did not finish')
   if pending or futures:time.sleep(1)
 print('ALL EXTRUSION CHECKS COMPLETE',flush=True)