import json,concurrent.futures
from final_revo22_f3_slice_checks import O,one
if __name__=='__main__':
 ids=json.loads((O/'verification/neck_recheck_plates.json').read_text());m=json.loads((O/'manifest.json').read_text());p=[p for p in m['plates'] if p['id'] in ids]
 with concurrent.futures.ProcessPoolExecutor(max_workers=3) as pool:
  for r in pool.map(one,p):
   print('RECHECK_DONE',r['plate'],'error' in r,flush=True);assert 'error' not in r,r
 rows=[json.loads((O/'verification'/f"{p['id']}_final_run.json").read_text()) for p in m['plates']]
 (O/'verification/final_run.json').write_text(json.dumps(rows,indent=2),encoding='utf8')
