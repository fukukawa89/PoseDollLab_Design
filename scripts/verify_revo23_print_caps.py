"""Recheck the four selected temporary-cap projects using current path rules."""
from audit_revo23_print import *

NAMES={'O23G-S09':'peel_caps2','O23G-S10':'caps_bead_clear','O23G-S12':'peel_exact','O23G-S14':'peel_clearance'}

def verify(rid):
    p=OUT/'bambu'/rid/NAMES[rid]/'checked_result.json';r=read(p)
    r['caps']=cap_audit(r)
    print('CAP GAP',rid,r['caps']['passed'],[round(x['minimum_actual_bead_gap_mm'],4) for x in r['caps']['rows']],flush=True)
    r['clearance']=void_audit(r);r['islands']=starting_islands(r)
    r['passed']=all(r[k]['passed'] for k in ('native','clearance','islands','caps'))
    put(p,r);print('CAP FINAL',rid,r['passed'],flush=True)
    return r['passed']

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--ids',nargs='*',default=list(NAMES));a=ap.parse_args()
    with concurrent.futures.ProcessPoolExecutor(max_workers=3) as pool:
        assert all(pool.map(verify,a.ids))
