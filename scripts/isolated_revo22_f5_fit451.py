import json,subprocess,sys,concurrent.futures
from search_revo22_f5_orientation268 import O,put
from verify_revo22_f5_contacts298 import SCHEMA
ids=[p.stem for p in(O/'selections').glob('*.json')if json.loads(p.read_text()).get('body_modified')]
def run(p):
 sel=json.loads((O/'selections'/f'{p}.json').read_text());f=O/'candidates'/p/sel['label']/'verification/f5_fit_and_pose.json'
 if f.exists():
  d=json.loads(f.read_text())
  if d.get('schema')==SCHEMA and d.get('fit_and_pose_geometry_passed'):return p,True,'already checked'
 log=O/'fit451'/f'{p}.log';log.parent.mkdir(exist_ok=True)
 with log.open('w',encoding='utf-8')as out:
  q=subprocess.run([sys.executable,'-u','-X','utf8','-X','faulthandler','-c','import sys;from verify_revo22_f5_contacts298 import run; assert run(sys.argv[1])["fit_and_pose_geometry_passed"]',p],cwd=__import__('pathlib').Path(__file__).parent,stdout=out,stderr=subprocess.STDOUT)
 return p,q.returncode==0,q.returncode
if __name__=='__main__':
 results=[]
 with concurrent.futures.ThreadPoolExecutor(max_workers=3)as ex:
  for q in ex.map(run,ids):results.append(q);print('FIT451_RESULT',q,flush=True);put(O/'fit451_results.json',results)
