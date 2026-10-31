"""Native geometry and actual extrusions, per plate. No printer access."""
import json,sys,concurrent.futures,traceback
from build_revo22_fins_v3 import O
from verify_revo22_f3_native_mesh import check as native
from verify_revo22_f3_extrusions import check_project

def one(p):
    try:
        native(p)
        path=O/'projects'/f"{p['id']}_O22F3_PLA_fins.3mf"
        r=check_project(path,p)
        return {'plate':p['id'],'floating_regions':len(r['floating_printed_components']),'missing_teeth':r['teeth_missing_printed_layer'],'unprinted_roots':sum(x['first_layer_printed_mm2']<=.01 for x in r['fin_bed_roots'])}
    except Exception:
        return {'plate':p['id'],'error':traceback.format_exc()}
if __name__=='__main__':
    p=json.loads((O/'manifest.json').read_text())['plates'];skip=sys.argv[1:]
    p=[x for x in p if x['id'] not in skip]
    with concurrent.futures.ProcessPoolExecutor(max_workers=3) as pool:
        for result in pool.map(one,p):print(json.dumps(result,ensure_ascii=False),flush=True)
