import sys,json,traceback
from build_revo22_fins_v2 import O,B
from package_revo22_fins_v2 import arrange,build
from build_revo22_supports import slice_project
from verify_revo22_f2_extrusions import check_project
main={i['id']:i for p in json.loads((B/'a1mini/manifest.json').read_text())['plates'] if not p['optional'] for i in p['items']}
for pid in sys.argv[1:]:
 try:
  p=arrange([main[pid]],'Q','单件实际出丝验证',True)[0];p['id']='QC_'+pid
  for it in p['items']:it['object_name']=p['id']+' '+it['id']+' '+it['part']
  src,work=build(p);dest=O/'projects'/f"{p['id']}_O22F2_PLA_fins.3mf";r=slice_project(src,dest,work);(O/'verification'/f"{p['id']}_slice.json").write_text(json.dumps({'result':r},ensure_ascii=False,indent=2),encoding='utf-8');print('SLICER',pid,r['sliced_plates'][0].get('warning_message'),flush=True);check_project(dest,p)
 except Exception:print('ERROR',pid,traceback.format_exc(),flush=True)