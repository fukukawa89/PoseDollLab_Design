from pathlib import Path
import sys,json,shutil
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'scripts'))
from slice_revo22_f4_candidate import run
from verify_revo22_f4_full_bead import check
from refine_revo22_f4_full_bead import refine
O=R/'Hardware/PoseDoll44/bench/revO22/a1mini_fins_v4'
def trial(pid,source,label,overrides):
 src=O/'candidates'/pid/source;dst=O/'candidates'/pid/label
 for sub,ext in [('parts','npz'),('design','json')]:
  (dst/sub).mkdir(parents=True,exist_ok=True);shutil.copy2(src/sub/f'{pid}.{ext}',dst/sub/f'{pid}.{ext}')
 (dst/'verification').mkdir(exist_ok=True);p=dst/'design'/f'{pid}.json';d=json.loads(p.read_text());d.setdefault('required_process_overrides',{}).update(overrides);d['slicing_trial_parent']=source;p.write_text(json.dumps(d,ensure_ascii=False,indent=2),encoding='utf8');run(pid,label);check(pid,label);out=refine(pid,label);print('PROCESS_TRIAL_RESULT',pid,label,out['external_island_count'],out['critical_external_count'],flush=True);return out
if __name__=='__main__':trial(sys.argv[1],sys.argv[2],sys.argv[3],json.loads(sys.argv[4]))
