"""Cross-slice identical physical geometry in Bambu Studio for an independent check."""
import json,sys
from build_revo22_fins_v3 import O,R
from build_revo22_supports import slice_project
from verify_revo22_f3_native_mesh import check as native
from verify_revo22_f3_extrusions import check_project
out=O/'crosscheck_bambu';out.mkdir(exist_ok=True);reports=O/'verification/bambu';reports.mkdir(exist_ok=True)
for p in json.loads((O/'manifest.json').read_text())['plates']:
    pid=p['id'];source=R/'.local/o22-fins-v3'/pid/'input.3mf';work=R/'.local/o22-fins-v3/bambu'/pid;work.mkdir(parents=True,exist_ok=True);dst=out/f'{pid}_O22F3_PLA_fins.3mf'
    result=slice_project(source,dst,work);(reports/f'{pid}_slice.json').write_text(json.dumps(result,indent=2),encoding='utf8')
    native(p,path=dst,report_dir=reports);r=check_project(dst,p,output_dir=reports)
    print('BAMBU',pid,'floating',len(r['floating_printed_components']),'teeth_missing_raw',r['teeth_missing_printed_layer'],flush=True)
