"""Slice and check a single F3 candidate with explicit local settings."""
import json,sys
from pathlib import Path
from prepare_revo22_f3 import *
import package_revo22_fins_v2 as pack
import verify_revo22_f2_extrusions as check
def run(pid,folder,engine='orca'):
    folder=Path(folder).resolve()
    pack.O=folder;pack.WORK=R/'.local/o22-fins-v3'/folder.name;pack.WORK.mkdir(parents=True,exist_ok=True)
    item=next(i for p in json.loads((B/'a1mini/manifest.json').read_text())['plates'] for i in p['items'] if i['id']==pid)
    p=pack.arrange([item],'Q','F3 single candidate',True)[0];p['id']='QC_'+pid+'_'+engine.upper()
    src,work=pack.build(p);(folder/'projects').mkdir(exist_ok=True)
    dst=folder/'projects'/f"{p['id']}.3mf"
    if engine=='orca':result=slicer(src,dst,work)
    else:
        from build_revo22_supports import slice_project
        result=slice_project(src,dst,work)
    (folder/'verification'/f"{p['id']}_manifest.json").write_text(json.dumps(p,ensure_ascii=False,indent=2),encoding='utf8')
    (folder/'verification'/f"{p['id']}_slice.json").write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf8')
    print('SLICED',pid,engine,result.get('complete',result.get('return_code')),flush=True)
    check.O=folder
    return check.check_project(dst,p)
if __name__=='__main__':run(sys.argv[1],sys.argv[2],sys.argv[3] if len(sys.argv)>3 else 'orca')

