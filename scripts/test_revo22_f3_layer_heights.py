"""Controlled layer-height comparison on an unchanged candidate."""
import json,zipfile,copy
from pathlib import Path
from prepare_revo22_f3 import *
import package_revo22_fins_v2 as pack
import verify_revo22_f3_extrusions as audit
folder=O/'candidates/X046/distributed_box'
pack.O=folder;pack.WORK=R/'.local/o22-fins-v3/chest_layer_height';pack.WORK.mkdir(parents=True,exist_ok=True)
item=next(i for p in json.loads((B/'a1mini/manifest.json').read_text())['plates'] for i in p['items'] if i['id']=='X046')
p=pack.arrange([item],'Q','Layer height comparison',True)[0];p['id']='SOURCE'
source,_=pack.build(p)
with zipfile.ZipFile(source) as z:data={k:z.read(k) for k in z.namelist()}
audit.O=folder
for height in [.16,.12,.10]:
    tag='L'+str(round(height*1000));work=pack.WORK/tag;work.mkdir(exist_ok=True)
    config=json.loads(data['Metadata/project_settings.config']);config.update(layer_height=str(height),initial_layer_print_height='0.2',print_settings_id='F3 '+tag+' controlled comparison')
    source2=work/'input.3mf'
    with zipfile.ZipFile(source2,'w',zipfile.ZIP_DEFLATED) as z:
        for k,v in data.items():z.writestr(k,json.dumps(config).encode() if k=='Metadata/project_settings.config' else v)
    dest=folder/'projects'/f'QC_X046_{tag}.3mf'
    result=slicer(source2,dest,work)
    pp=copy.deepcopy(p);pp['id']='QC_X046_'+tag
    print('HEIGHT_SLICE',height,result['complete'],flush=True)
    if result['complete']:audit.check_project(dest,pp)

