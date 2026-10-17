from pathlib import Path
import sys,json
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'scripts'))
import package_revo22_fins_v4 as pack
from prepare_revo22_f3 import slicer
from verify_revo22_f4_local_extrusion import check
B=R/'Hardware/PoseDoll44/bench/revO22';O=B/'a1mini_fins_v4'
def run(pid,label):
 folder=O/'candidates'/pid/label;pack.FUSE_PRINT_GEOMETRY=json.loads((folder/'design'/f'{pid}.json').read_text()).get('fuse_print_geometry',True);pack.PROCESS_LAYER_HEIGHT=float(json.loads((folder/'design'/f'{pid}.json').read_text()).get('required_layer_height_mm',.2));pack.INITIAL_LAYER_HEIGHT=float(json.loads((folder/'design'/f'{pid}.json').read_text()).get('required_initial_layer_height_mm',.2));pack.WALL_GENERATOR=json.loads((folder/'design'/f'{pid}.json').read_text()).get('required_wall_generator','arachne');pack.EXTRA_PROCESS_SETTINGS=json.loads((folder/'design'/f'{pid}.json').read_text()).get('required_process_overrides',{});pack.O=folder;pack.WORK=R/'.local/o22-fins-v4/candidates'/pid/label;pack.WORK.mkdir(parents=True,exist_ok=True)
 item=next(i for p in json.loads((B/'a1mini/manifest.json').read_text(encoding='utf8'))['plates'] for i in p['items'] if i['id']==pid)
 plate=pack.arrange([item],'QC','F4 candidate under review',True)[0];plate['id']='QC_'+pid+'_'+label;src,work=pack.build(plate);(folder/'projects').mkdir(exist_ok=True);dst=folder/'projects'/f"{plate['id']}.3mf"
 ranges=json.loads((folder/'design'/f'{pid}.json').read_text()).get('required_layer_ranges',[])
 if ranges:
  import zipfile,xml.etree.ElementTree as ET
  root=ET.Element('objects');obj=ET.SubElement(root,'object',{'id':'1'})
  for lo,hi,settings in ranges:
   node=ET.SubElement(obj,'range',{'min_z':str(lo),'max_z':str(hi)})
   for key,value in dict(layer_height=str(pack.PROCESS_LAYER_HEIGHT),**settings).items():ET.SubElement(node,'option',{'opt_key':key}).text=str(value)
  with zipfile.ZipFile(src)as z:entries={name:z.read(name)for name in z.namelist()}
  entries['Metadata/layer_config_ranges.xml']=ET.tostring(root,encoding='utf-8',xml_declaration=True)
  with zipfile.ZipFile(src,'w',zipfile.ZIP_DEFLATED)as z:
   for name,raw in entries.items():z.writestr(name,raw)
 r=slicer(src,dst,work/'orca',timeout=900);assert r['complete'],r
 if ranges:
  with zipfile.ZipFile(dst)as z:retained=ET.fromstring(z.read('Metadata/layer_config_ranges.xml'))
  actual=[(float(q.attrib['min_z']),float(q.attrib['max_z']),{v.attrib['opt_key']:v.text for v in q.findall('option')})for q in retained.findall('object/range')]
  assert len(actual)==len(ranges),(actual,ranges)
  for a,e in zip(actual,ranges):
   assert abs(a[0]-e[0])<1e-5 and abs(a[1]-e[1])<1e-5
   for k,v in e[2].items():assert a[2][k]==str(v),(k,a[2][k],v)
  r['verified_native_layer_ranges']=actual
 (folder/'verification/plate_manifest.json').write_text(json.dumps(plate,ensure_ascii=False,indent=2),encoding='utf8');(folder/'verification/slice.json').write_text(json.dumps(r,ensure_ascii=False,indent=2),encoding='utf8');print('CANDIDATE_SLICED',pid,label,flush=True)
 return check(dst,folder/'verification/local_extrusion.json')
if __name__=='__main__':run(sys.argv[1],sys.argv[2])
