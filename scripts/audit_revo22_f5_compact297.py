"""Slice and audit every packed F5 plate, preserving exact per-object profiles."""
import sys,json,copy,shutil,hashlib,zipfile,xml.etree.ElementTree as ET,concurrent.futures,traceback
import numpy as np
from search_revo22_f5_orientation268 import R,B,O,OLD,put
from stage_revo22_f5_compact296 import S,sha
import package_revo22_fins_v4 as pack
from prepare_revo22_f3 import slicer
from verify_revo22_f4_local_extrusion import check as localcheck
from verify_revo22_f3_native_mesh import check as meshcheck
import stage_revo22_f4_plates97 as stage
import verify_revo22_f4_full_bead as full
import o22_recover_native_flag_paths as recover
import refine_revo22_f4_full_bead as finer
import refine_revo22_f4_islands84 as exact
import refine_revo22_f4_lateral104 as lateral
from audit_revo22_f5_native271 import endpoints

def baseline(profile=None):
 m=json.loads((OLD/'manifest.json').read_text());p=m['plates'][1]
 with zipfile.ZipFile(OLD/p['project'])as z:s=json.loads(z.read('Metadata/project_settings.config'))
 s['print_settings_id']='O22-F5 sparse removable fins / A1 mini PLA 0.4'
 if profile:s.update(layer_height=str(profile['layer']),initial_layer_print_height=str(profile['initial']))
 return s

def keys():
 m=json.loads((S/'stage_manifest.json').read_text());ks={'wall_generator','min_feature_size','is_infill_first','outer_wall_line_width','inner_wall_line_width','bridge_angle','wall_sequence','detect_thin_wall'}
 for p in m['plates']:
  for i in p['items']:ks.update(i['source_profile'].get('overrides',{}))
 return sorted(ks)
def expected(it):
 prof=it['source_profile'];s=baseline(prof);s['wall_generator']=prof['wall'];s.update(prof.get('overrides',{}));return{k:str(s[k])for k in keys()if k in s}
def inject(src,p):
 with zipfile.ZipFile(src)as z:data={n:z.read(n)for n in z.namelist()}
 data['Metadata/project_settings.config']=json.dumps(baseline(p['profile'])).encode();cfg=ET.fromstring(data['Metadata/model_settings.config']);objs=cfg.findall('object');assert len(objs)==len(p['items']);ranges=ET.Element('objects')
 root=ET.fromstring(data['3D/3dmodel.model'])
 for n in root.findall('{*}metadata'):
  if n.get('name')=='Title':n.text=p['id']+' O22-F5'
 data['3D/3dmodel.model']=ET.tostring(root,encoding='utf-8',xml_declaration=True)
 for ordinal,(obj,it)in enumerate(zip(objs,p['items']),1):
  assert it['source_profile']['layer']==p['profile']['layer'] and it['source_profile']['initial']==p['profile']['initial']
  for key,value in expected(it).items():
   node=next((n for n in obj.findall('metadata')if n.get('key')==key),None)
   if node is None:node=ET.SubElement(obj,'metadata',{'key':key})
   node.set('value',value)
  rr=it['source_profile'].get('height_overrides',[])
  if rr:
   node=ET.SubElement(ranges,'object',{'id':str(ordinal)})
   for lo,hi,settings in rr:
    ran=ET.SubElement(node,'range',{'min_z':str(lo),'max_z':str(hi)})
    for key,value in dict(layer_height=str(it['source_profile']['layer']),**settings).items():ET.SubElement(ran,'option',{'opt_key':key}).text=str(value)
 data['Metadata/model_settings.config']=ET.tostring(cfg,encoding='utf-8',xml_declaration=True)
 if len(ranges):data['Metadata/layer_config_ranges.xml']=ET.tostring(ranges,encoding='utf-8',xml_declaration=True)
 with zipfile.ZipFile(src,'w',zipfile.ZIP_DEFLATED)as z:
  for name,raw in data.items():z.writestr(name,raw)
def verify_profiles(path,p):
 with zipfile.ZipFile(path)as z:
  g=json.loads(z.read('Metadata/project_settings.config'));cfg=ET.fromstring(z.read('Metadata/model_settings.config'));byid={q.get('id'):q for q in cfg.findall('object')};root=ET.fromstring(z.read('3D/3dmodel.model'));objects=[byid[q.get('objectid')]for q in root.findall('{*}build/{*}item')];rroot=ET.fromstring(z.read('Metadata/layer_config_ranges.xml'))if'Metadata/layer_config_ranges.xml'in z.namelist()else ET.Element('objects')
 assert len(objects)==len(p['items']);assert g==baseline(p['profile']),[(k,g.get(k),v)for k,v in baseline(p['profile']).items()if g.get(k)!=v]
 rr={int(n.get('id')):[[float(q.get('min_z')),float(q.get('max_z')),{o.get('opt_key'):o.text for o in q.findall('option')}]for q in n.findall('range')]for n in rroot.findall('object')};records=[]
 for idx,(obj,it)in enumerate(zip(objects,p['items']),1):
  actual={n.get('key'):n.get('value')for n in obj.findall('metadata')};assert actual['name']==it['object_name'];effective={k:actual.get(k,str(g[k]))for k in expected(it)};assert effective==expected(it),(it['id'],effective,expected(it));want=it['source_profile'].get('height_overrides',[]);got=rr.get(idx,[]);assert len(want)==len(got)
  for a,b in zip(got,want):
   assert abs(a[0]-b[0])<1e-5 and abs(a[1]-b[1])<1e-5
   for k,v in dict(layer_height=str(it['source_profile']['layer']),**b[2]).items():assert float(a[2][k])==float(v)
  records.append(dict(object=it['object_name'],previous_f4_address=it['previous_f4_address'],effective_settings=effective,height_ranges=got))
 return dict(all_selected_object_profiles_preserved=True,project_sha256=sha(path),objects=records)
def audit(p):
 try:
  key=hashlib.sha256(json.dumps(dict(plate=p,geometry={i['id']:sha(S/'parts'/f"{i['id']}.npz")for i in p['items']}),sort_keys=True).encode()).hexdigest();label='native_'+key[:12];pid='PLATE_'+p['id'];q=S/'candidates'/pid/label;vp=q/'verification';dest=S/'projects'/f"{p['id']}_O22F5_PLA_fins.3mf";done=vp/'plate_result.json'
  if done.exists()and dest.exists():
   old=json.loads(done.read_text())
   if old.get('native_clear')and old['project_sha256']==sha(dest):return old
  for sub in ['parts','design','verification','projects']:(q/sub).mkdir(parents=True,exist_ok=True)
  (S/'projects').mkdir(exist_ok=True);pack.O=S;pack.WORK=R/'.local/o22-f5-compact297';pack.WORK.mkdir(exist_ok=True);pack.PROCESS_LAYER_HEIGHT=p['profile']['layer'];pack.INITIAL_LAYER_HEIGHT=p['profile']['initial'];pack.WALL_GENERATOR='arachne';pack.EXTRA_PROCESS_SETTINGS={};pack.FUSE_PRINT_GEOMETRY=True;src=pack.WORK/p['id']/'input.3mf';work=src.parent
  if not(vp/'slice.json').exists():
   src,work=pack.build(p);inject(src,p);sr=slicer(src,dest,work/label,timeout=1800);assert sr['complete'],sr;put(vp/'slice.json',sr)
  put(vp/'object_profiles.json',verify_profiles(dest,p));meshcheck(p,path=dest,source=src,report_dir=vp,expected_layer_height=p['profile']['layer'],expected_initial_layer_height=p['profile']['initial']);shutil.copy2(vp/f"{p['id']}_native_mesh.json",vp/'native_mesh.json');shutil.copy2(dest,q/'projects'/dest.name);stage.S=S;n={}
  for vk,fk in [('v','f'),('fin_v','fin_f'),('teeth_v','teeth_f')]:n[vk],n[fk]=stage.merge_role(p['items'],(vk,fk))
  np.savez_compressed(q/'parts'/f'{pid}.npz',**n);put(q/'design'/f'{pid}.json',dict(id=pid,required_layer_height_mm=p['profile']['layer'],required_initial_layer_height_mm=p['profile']['initial'],whole_plate_geometry_merged_from_actual_instance_transforms=True));put(vp/'plate_manifest.json',dict(id=pid,items=[dict(rotation_matrix=np.eye(3).tolist(),translation_mm=[0,0,0])],real_instance_manifest=p))
  lp=vp/'local_extrusion.json'
  if not lp.exists():localcheck(dest,lp)
  for module in [full,recover,finer,exact,lateral]:module.O=S
  full.check(pid,label);d=finer.refine(pid,label)
  if d['external_islands']:d=exact.trial(pid,label)
  if d['critical_external_runs']:d=lateral.check(pid,label)
  d=endpoints(pid,label,root=S);r=dict(plate=p['id'],label=label,instances=len(p['items']),source_ids=[i['id']for i in p['items']],native_clear=d['native_review_resolved'],external_islands=d['external_island_count'],critical_external_runs=d['critical_external_count'],project_sha256=sha(dest),layout_and_source_hash=key,geometry_qualified_per_instance=True,all_selected_effective_object_profiles_preserved=True,native_mesh_preserved=True,physical_plate_print_tested=False);assert r['project_sha256']==d['project_sha256'];put(done,r);put(S/'plate_results'/f"{p['id']}.json",r);print('F5_PLATE297',r,flush=True);return r
 except Exception:
  r=dict(plate=p['id'],error=traceback.format_exc());print('F5_PLATE297_ERROR',r,flush=True);return r
if __name__=='__main__':
 m=json.loads((S/'stage_manifest.json').read_text());ps=[p for p in m['plates']if not sys.argv[1:]or p['id']in sys.argv[1:]];out=[]
 with concurrent.futures.ProcessPoolExecutor(max_workers=3)as ex:
  for f in concurrent.futures.as_completed([ex.submit(audit,p)for p in ps]):out.append(f.result());put(S/'native_progress.json',out)
