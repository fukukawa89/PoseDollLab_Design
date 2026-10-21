import sys,subprocess,concurrent.futures
from search_revo22_f5_orientation268 import O,R

def run(p):
 code="import sys;sys.path.insert(0,"+repr(str(R/'scripts'))+");from resolve_revo22_f5_stem356 import run;print('STEM356_RESULT',run("+repr(p)+"),flush=True)"
 with (O/f'stem356_{p}.log').open('w')as f:
  q=subprocess.run([sys.executable,'-X','utf8','-X','faulthandler','-c',code],stdout=f,stderr=subprocess.STDOUT)
 return p,q.returncode
if __name__=='__main__':
 with concurrent.futures.ThreadPoolExecutor(max_workers=3)as ex:
  for q in ex.map(run,sys.argv[1:]):print('ISOLATED356',q,flush=True)
