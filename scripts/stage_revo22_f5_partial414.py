import json,shutil
from search_revo22_f5_orientation268 import O,OLD,put
import stage_revo22_f5_compact296 as stage
from audit_revo22_f5_compact297 import audit
import concurrent.futures
S=stage.S

def provisional():
 old=json.loads((OLD/'manifest.json').read_text());chosen={};pending={'P130':'orient407_r4_route1','X046':'cap396_0'}
 for sub in ['parts','design','verification/types']:(S/sub).mkdir(parents=True,exist_ok=True)
 for row in json.loads((O/'inventory.json').read_text())['rows']:
  p=row['id'];sf=O/'selections'/f'{p}.json'
  sel=json.loads(sf.read_text())if sf.exists()else dict(id=p,label=pending[p],qualification_pending=True)
  q=O/'candidates'/p/sel['label'];gpath=q/'verification/f5_geometry.json';g=json.loads(gpath.read_text())if gpath.exists()else None
  if not sel.get('qualification_pending'):assert g and g['geometric_constraints_passed']
  for sub,ext in [('parts','npz'),('design','json')]:shutil.copy2(q/sub/f'{p}.{ext}',S/sub/f'{p}.{ext}')
  (S/'verification/types'/p).mkdir(exist_ok=True)
  for name in ['f5_geometry.json','f5_fit_and_pose.json','native_final.json','construction.json','relief_geometry.json','f5_fin_groups.npz','guards.npz','strict_magnet_guards.npz']:
   if(q/'verification'/name).exists():shutil.copy2(q/'verification'/name,S/'verification/types'/p/name)
  chosen[p]=dict(sel,npz_sha256=stage.sha(S/'parts'/f'{p}.npz'),geometric_proof=g)
 put(S/'provisional_selection.json',chosen);return old
if __name__=='__main__':
 stage.prepare=provisional;stage.main();m=json.loads((S/'stage_manifest.json').read_text());m['status']='PROVISIONAL: P130 and X046 qualification still pending';put(S/'stage_manifest.json',m)
 ready=[p for p in m['plates']if not any(i['id']in['P130','X046']for i in p['items'])];print('READY414_PLATES',[p['id']for p in ready],flush=True)
 with concurrent.futures.ProcessPoolExecutor(max_workers=3)as ex:
  for f in concurrent.futures.as_completed([ex.submit(audit,p)for p in ready]):print('READY414_RESULT',f.result(),flush=True)
