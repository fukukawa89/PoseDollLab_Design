"""F5 native per-part audit. Unchanged 1/3 mm screening limits."""
from pathlib import Path
import sys,json,hashlib,concurrent.futures,traceback,shutil
from search_revo22_f5_orientation268 import R,B,O,OLD,put
import slice_revo22_f4_candidate as runner
import verify_revo22_f4_full_bead as full
import o22_recover_native_flag_paths as recover
import refine_revo22_f4_full_bead as finer
import refine_revo22_f4_islands84 as exact
import refine_revo22_f4_lateral104 as lateral
from verify_revo22_f3_native_mesh import check as meshcheck

def endpoints(pid,label,root=O):
 vp=root/'candidates'/pid/label/'verification'
 if not(vp/'full_bead_contacts_v5.json').exists():
  src=next(vp/n for n in ['full_bead_contacts_v4.json','full_bead_contacts_v2.json','full_bead_contacts.json']if(vp/n).exists());shutil.copy2(src,vp/'full_bead_contacts_v5.json')
 code=(R/'scripts/verify_revo22_x062_endpoints256.py').read_text(encoding='utf-8-sig')
 code=code.replace('from build_revo22_x062_open242 import S,put','from search_revo22_f5_orientation268 import put')
 code=code.replace("label=sys.argv[1];D=S/'candidates/X062'/label;",'D=S/"candidates"/pid/label;')
 env={'S':root,'pid':pid,'label':label,'__name__':'f5_endpoint_audit'};exec(compile(code,'f5_endpoint_audit','exec'),env)
 return env['result']

def run(pid,label='open_a'):
 folder=O/'candidates'/pid/label;vp=folder/'verification';runner.O=O
 if(vp/'native_final.json').exists():return json.loads((vp/'native_final.json').read_text())
 if not(vp/'local_extrusion.json').exists():runner.run(pid,label)
 plate=json.loads((vp/'plate_manifest.json').read_text());native=next((folder/'projects').glob('*.3mf'));source=R/'.local/o22-fins-v4/candidates'/pid/label/plate['id']/'input.3mf';design=json.loads((folder/'design'/f'{pid}.json').read_text())
 meshcheck(plate,path=native,source=source,report_dir=vp,expected_layer_height=design['required_layer_height_mm'],expected_initial_layer_height=design.get('required_initial_layer_height_mm',.2))
 for module in [full,recover,finer,exact,lateral]:module.O=O
 if not(vp/'full_bead_contacts.json').exists():full.check(pid,label)
 d=finer.refine(pid,label)
 if d['external_islands']:d=exact.trial(pid,label)
 if d['critical_external_runs']:d=lateral.check(pid,label)
 d=endpoints(pid,label)
 print('F5_AUDIT',pid,label,d['native_review_resolved'],d['external_island_count'],d['critical_external_count'],flush=True);return d
if __name__=='__main__':
 import argparse
 ap=argparse.ArgumentParser();ap.add_argument('ids',nargs='*');ap.add_argument('--label',default='open_a');ap.add_argument('--workers',type=int,default=2);args=ap.parse_args();ids=args.ids or sorted(p.name for p in(O/'candidates').iterdir()if(p/args.label/'parts'/f'{p.name}.npz').exists());out=[]
 with concurrent.futures.ProcessPoolExecutor(max_workers=args.workers)as pool:
  futures={pool.submit(run,pid,args.label):pid for pid in ids}
  for fut in concurrent.futures.as_completed(futures):
   pid=futures[fut]
   try:d=fut.result();out.append(dict(id=pid,label=args.label,ok=d['native_review_resolved'],islands=d['external_island_count'],critical=d['critical_external_count']));put(O/f'audit_progress_{args.label}.json',out)
   except Exception as e:traceback.print_exc();print('AUDIT_ERROR',pid,repr(e),flush=True)
