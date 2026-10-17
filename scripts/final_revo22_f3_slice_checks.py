"""Final paired native exports and geometry/extrusion checks for frozen F3 parts."""
import json,concurrent.futures,traceback,time
from pathlib import Path
from build_revo22_fins_v3 import O,R
from prepare_revo22_f3 import slicer
from build_revo22_supports import slice_project
from verify_revo22_f3_native_mesh import check as native
from verify_revo22_f3_extrusions import check_project

def one(p):
    pid=p['id'];source=R/'.local/o22-fins-v3'/pid/'input.3mf';result={'plate':pid,'engines':{}}
    try:
        for engine in ['orca','bambu']:
            out=O/'projects' if engine=='orca' else O/'crosscheck_bambu';out.mkdir(exist_ok=True);reports=O/'verification' if engine=='orca' else O/'verification/bambu';reports.mkdir(exist_ok=True)
            work=R/'.local/o22-fins-v3/final'/engine/pid;work.mkdir(parents=True,exist_ok=True);dst=out/f'{pid}_O22F3_PLA_fins.3mf'
            rr=slicer(source,dst,work) if engine=='orca' else slice_project(source,dst,work)
            assert rr.get('complete',rr.get('return_code')==0),rr
            (reports/f'{pid}_slice.json').write_text(json.dumps(rr,indent=2),encoding='utf8');native(p,path=dst,report_dir=reports)
            report=check_project(dst,p,output_dir=reports)
            result['engines'][engine]={'floating_regions':len(report['floating_printed_components']),'floating_area_mm2':sum(x['area_mm2'] for x in report['floating_printed_components']),'maximum_region_mm2':max([x['area_mm2'] for x in report['floating_printed_components']],default=0),'missing_teeth':report['teeth_missing_printed_layer'],'unprinted_roots':sum(x['first_layer_printed_mm2']<=.01 for x in report['fin_bed_roots']),'project_sha256':report['project_sha256']}
            print('FINAL',pid,engine,json.dumps(result['engines'][engine]),flush=True)
    except Exception:result['error']=traceback.format_exc()
    (O/'verification'/f'{pid}_final_run.json').write_text(json.dumps(result,indent=2),encoding='utf8');return result
if __name__=='__main__':
    plates=json.loads((O/'manifest.json').read_text())['plates'];rows=[]
    with concurrent.futures.ProcessPoolExecutor(max_workers=3) as pool:
        futures=[pool.submit(one,p) for p in plates]
        for f in concurrent.futures.as_completed(futures):
            r=f.result();rows.append(r);(O/'verification/final_run.json').write_text(json.dumps(rows,indent=2),encoding='utf8');print('PLATE_DONE',r['plate'],'error' in r,flush=True)
    assert not any('error' in r for r in rows),rows
