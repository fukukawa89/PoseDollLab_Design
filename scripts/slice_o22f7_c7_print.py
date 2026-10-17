"""Slice and inspect the two C7 replacement plates, retaining F7 PLA settings."""
from o22f7_animation import *
import o22f7_native as h
import package_revo22_fins_v4 as pack
from prepare_revo22_f3 import slicer
from verify_revo22_f3_native_mesh import check as meshcheck
import zipfile,xml.etree.ElementTree as ET,copy,argparse
C=WORK/'structure_revision';O=C/'print_candidate';W=C/'native_print_review';W.mkdir(exist_ok=True)
h.OUT=O;h.SRC=F;h.WORK=W;h.PROJECT_SUFFIX='PLA_assembly';h.SCREEN_LABEL='c7';pack.O=O;pack.WORK=W/'build';pack.WORK.mkdir(exist_ok=True)
plates=read(O/'changed_plates.json')['plates']
def build(p):
 pack.PROCESS_LAYER_HEIGHT=p['profile']['layer'];pack.INITIAL_LAYER_HEIGHT=p['profile']['initial'];src,work=pack.build(p)
 with zipfile.ZipFile(F/'projects/D05_O22F7_PLA_final.3mf') as z:settings=json.loads(z.read('Metadata/project_settings.config'));ocfg=ET.fromstring(z.read('Metadata/model_settings.config'))
 old={hkey(o,'name'):o for o in ocfg.findall('object')}
 with zipfile.ZipFile(src) as z:data={k:z.read(k) for k in z.namelist()}
 cfg=ET.fromstring(data['Metadata/model_settings.config']);expected={}
 for obj in cfg.findall('object'):
  name=hkey(obj,'name');oldname='D05-01 W005 frame/clavicle_l.protract_frame' if 'W005A' in name or 'W005B' in name else name
  for q in list(obj.findall('metadata')):obj.remove(q)
  for q in old[oldname].findall('metadata'):
   q=copy.deepcopy(q)
   if q.get('key')=='name':q.set('value',name)
   if 'W005A' in name and q.get('key')=='counterbore_hole_bridging':q.set('value','none')
   obj.append(q)
  expected[name]={q.get('key'):q.get('value') for q in obj.findall('metadata')}
 settings['print_settings_id']='O22F7 C7 assembly revision / A1 mini PLA 0.4';assert settings['filament_type']==['PLA'] and settings['enable_support']=='0';data['Metadata/project_settings.config']=json.dumps(settings).encode();data['Metadata/model_settings.config']=ET.tostring(cfg,encoding='utf-8',xml_declaration=True)
 with zipfile.ZipFile(src,'w',zipfile.ZIP_DEFLATED) as z:
  for k,v in data.items():z.writestr(k,v)
 dest=O/p['project'];vp=W/f"plates/{p['id']}";vp.mkdir(parents=True,exist_ok=True);res=slicer(src,dest,work/'orca',timeout=1800);assert res['complete'],res
 meshcheck(p,path=dest,source=src,report_dir=vp,expected_layer_height=p['profile']['layer'],expected_initial_layer_height=p['profile']['initial'])
 with zipfile.ZipFile(dest) as z:
  actual=json.loads(z.read('Metadata/project_settings.config'));cfg=ET.fromstring(z.read('Metadata/model_settings.config'))
 assert actual==settings
 assert {hkey(o,'name'):{q.get('key'):q.get('value') for q in o.findall('metadata')} for o in cfg.findall('object')}==expected
 res.update(project_sha256=sha(dest),source_sha256=sha(src),object_profiles_verified=True);put(vp/'slice.json',res);print('SLICE',p['id'],res['complete'],flush=True)
def hkey(o,k):return next(q.get('value') for q in o.findall('metadata') if q.get('key')==k)
if __name__=='__main__':
 ap=argparse.ArgumentParser();ap.add_argument('mode',choices=['build','screen']);ap.add_argument('--plate',default='all');a=ap.parse_args()
 for p in plates:
  if a.plate not in ['all',p['id']]:continue
  if a.mode=='build':build(p)
  else:h.screen_plate(p)
