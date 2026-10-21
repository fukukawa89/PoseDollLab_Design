from bambu_revo23_print import *

def refresh(file):
    r=read(file);r['clearance']=void_audit(r);r['islands']=starting_islands(r)
    r['passed']=bool(r['native']['passed'] and r['repairs']==0 and r['bed_violations']==0 and r['clearance']['passed'] and r['islands']['passed'])
    put(file,r);print('REFRESH',r['id'],r['name'],r['passed'],flush=True)
    return r

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--ids',nargs='*');ap.add_argument('--workers',type=int,default=3);a=ap.parse_args()
    files=[x for x in (OUT/'bambu').glob('*/*/checked_result.json') if not a.ids or x.parent.parent.name in a.ids]
    with concurrent.futures.ProcessPoolExecutor(max_workers=a.workers) as pool:list(pool.map(refresh,files))
