from audit_revo23_print import *

def check(file):
    r=read(file)
    if r['islands']['passed'] and not r['passed']:
        v=void_audit(r,5);print('APERTURES',r['id'],r['name'],v['passed'],len(v['functional_void_hits']),len(v['wire_void_hits']),flush=True)

if __name__=='__main__':
    with concurrent.futures.ProcessPoolExecutor(max_workers=3) as pool:list(pool.map(check,(OUT/'bambu').glob('*/*/checked_result.json')))
