from pathlib import Path
import sys,json,shutil,concurrent.futures,traceback
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'scripts'))
from slice_revo22_f4_candidate import run
from verify_revo22_f4_full_bead import check
O=R/'Hardware/PoseDoll44/bench/revO22/a1mini_fins_v4'
def one(spec):
 pid,source,height=spec;label='classic_'+str(height).replace('.','p')+'_16';src=O/'candidates'/pid/source;dst=O/'candidates'/pid/label
 try:
  for sub,ext in [('parts','npz'),('design','json')]:
   (dst/sub).mkdir(parents=True,exist_ok=True);shutil.copy2(src/sub/f'{pid}.{ext}',dst/sub/f'{pid}.{ext}')
  (dst/'verification').mkdir(exist_ok=True)
  p=dst/'design'/f'{pid}.json';d=json.loads(p.read_text());d['required_layer_height_mm']=.2;d['required_initial_layer_height_mm']=height;d['required_wall_generator']='classic';d['slicing_trial_parent']=source;p.write_text(json.dumps(d,ensure_ascii=False,indent=2),encoding='utf8');run(pid,label);r=check(pid,label);print('PHASE_RESULT',pid,height,r['external_island_count'],r['critical_external_count'],flush=True);return {'id':pid,'label':label,'islands':r['external_island_count'],'critical':r['critical_external_count']}
 except Exception:return {'id':pid,'label':label,'error':traceback.format_exc()}
if __name__=='__main__':
 jobs=[(p,'contact_finish_03',h) for p in sys.argv[1:] for h in [.2]];out=[]
 with concurrent.futures.ProcessPoolExecutor(max_workers=2) as pool:
  for f in concurrent.futures.as_completed([pool.submit(one,j) for j in jobs]):
   out.append(f.result());(O/'classic16_progress.json').write_text(json.dumps(out,indent=2))
