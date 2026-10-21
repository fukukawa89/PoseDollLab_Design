"""Freeze translated F4 objects, preserve per-object profiles, and audit actual new G-code."""
from pathlib import Path
import sys,json,copy,shutil,hashlib,zipfile,xml.etree.ElementTree as ET,concurrent.futures,traceback
import numpy as np
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'scripts'))
B=R/'Hardware/PoseDoll44/bench/revO22';D=B/'O22F4_Release';O=B/'a1mini_fins_v4';S=O/'compact230'
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
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def write(p,d):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(d,ensure_ascii=False,indent=2),encoding='utf8')
def baseline():
 m=json.loads((D/'manifest.json').read_text());p=next(p for p in m['plates']if p['id']=='F03')
 with zipfile.ZipFile(D/p['project'])as z:return json.loads(z.read('Metadata/project_settings.config'))
BASE_KEYS=['wall_generator','min_feature_size','is_infill_first']
def expected(it):
 prof=it['source_profile'];s=baseline();s['wall_generator']=prof['wall'];s.update(prof.get('overrides',{}));return {k:str(s[k])for k in BASE_KEYS}
def prepare():
 m=json.loads((S/'layout.json').read_text());old=json.loads((D/'manifest.json').read_text());oldplates={p['id']:p for p in old['plates']}
 for sub in ['parts','design']:
  (S/sub).mkdir(exist_ok=True)
  for p in (D/sub).iterdir():
   if p.is_file():shutil.copy2(p,S/sub/p.name);assert sha(p)==sha(S/sub/p.name)
 for p in m['plates']:
  p['profile']=copy.deepcopy(oldplates['F03']['profile']);p['per_object_profiles_preserved']=True
  for it in p['items']:
   if not p.get('exact_original_plate_reuse'):it['native_internal_object_name']=it['object_name']
  if p.get('exact_original_plate_reuse'):
   src=oldplates[p['exact_original_plate_reuse']];p['profile']=copy.deepcopy(src['profile']);dest=S/'projects'/f"{p['id']}_O22F4_PLA_fins.3mf";dest.parent.mkdir(exist_ok=True);shutil.copy2(D/src['project'],dest)
   assert sha(dest)==src['project_sha256'];vd=S/'candidates'/('PLATE_'+p['id'])/'native/verification';shutil.copytree(D/'verification/plates'/src['id'],vd,dirs_exist_ok=True);proof=json.loads((D/src['proof']).read_text());assert proof['native_clear']and proof['project_sha256']==sha(dest)
   proof.update(plate=p['id'],exact_original_plate_reuse=src['id'],audit_reuse_proof='The native 3MF, G-code, internal object name, geometry and transforms are byte-identical to the qualified original F4 plate. Only its external filename and guide address are aliases.');write(vd/'plate_result.json',proof)
 write(S/'stage_manifest.json',m);print('COMPACT231_PREPARED',len(m['plates']),flush=True)
def inject(src,p):
 with zipfile.ZipFile(src)as z:data={n:z.read(n)for n in z.namelist()}
 data['Metadata/project_settings.config']=json.dumps(baseline()).encode();cfg=ET.fromstring(data['Metadata/model_settings.config']);objs=cfg.findall('object');assert len(objs)==len(p['items']);ranges=ET.Element('objects')
 for ordinal,(obj,it)in enumerate(zip(objs,p['items']),1):
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
  g=json.loads(z.read('Metadata/project_settings.config'));cfg=ET.fromstring(z.read('Metadata/model_settings.config'));objects_by_id={q.get('id'):q for q in cfg.findall('object')};root=ET.fromstring(z.read('3D/3dmodel.model'));objects=[objects_by_id[q.get('objectid')]for q in root.findall('{*}build/{*}item')];rroot=ET.fromstring(z.read('Metadata/layer_config_ranges.xml'))if 'Metadata/layer_config_ranges.xml'in z.namelist()else ET.Element('objects')
 assert len(objects)==len(p['items']);assert g==baseline(),[(k,g.get(k),v)for k,v in baseline().items()if g.get(k)!=v]
 rr={int(n.get('id')):[[float(q.get('min_z')),float(q.get('max_z')),{o.get('opt_key'):o.text for o in q.findall('option')}]for q in n.findall('range')]for n in rroot.findall('object')};records=[]
 for idx,(obj,it)in enumerate(zip(objects,p['items']),1):
  actual={n.get('key'):n.get('value')for n in obj.findall('metadata')};assert actual['name']==it['object_name'];effective={k:actual.get(k,str(g[k]))for k in BASE_KEYS};assert effective==expected(it),(it['id'],effective,expected(it));want=it['source_profile'].get('height_overrides',[]);got=rr.get(idx,[]);assert len(want)==len(got),(it['id'],want,got)
  for a,b in zip(got,want):
   assert abs(a[0]-b[0])<1e-5 and abs(a[1]-b[1])<1e-5
   for k,v in dict(layer_height=str(it['source_profile']['layer']),**b[2]).items():assert float(a[2][k])==float(v),(it['id'],k,a[2],v)
  records.append({'object':it['object_name'],'old_address':it['previous_f4_address'],'effective_settings':effective,'height_ranges':got})
 return {'all_original_effective_object_profiles_preserved':True,'project_sha256':sha(path),'global_settings_identical_to_original_F03':True,'objects':records}
def audit(p):
 try:
  if p.get('exact_original_plate_reuse'):return json.loads((S/'candidates'/('PLATE_'+p['id'])/'native/verification/plate_result.json').read_text())
  pid='PLATE_'+p['id'];q=S/'candidates'/pid/'native';vp=q/'verification';dest=S/'projects'/f"{p['id']}_O22F4_PLA_fins.3mf";done=vp/'plate_result.json'
  if done.exists():
   old=json.loads(done.read_text())
   if old.get('native_clear')and old['project_sha256']==sha(dest):print('COMPACT231_REUSED_AUDIT',p['id'],flush=True);return old
  for sub in ['parts','design','verification','projects']:(q/sub).mkdir(parents=True,exist_ok=True)
  pack.O=S;pack.WORK=R/'.local/o22-f4-compact231';pack.WORK.mkdir(exist_ok=True);pack.PROCESS_LAYER_HEIGHT=.2;pack.INITIAL_LAYER_HEIGHT=.2;pack.WALL_GENERATOR='arachne';pack.EXTRA_PROCESS_SETTINGS={};pack.FUSE_PRINT_GEOMETRY=True;src=pack.WORK/p['id']/'input.3mf';work=src.parent
  if not(dest.exists()and(vp/'slice.json').exists()):
   src,work=pack.build(p);inject(src,p);sr=slicer(src,dest,work/'orca',timeout=1200);assert sr['complete'],sr;write(vp/'slice.json',sr)
  write(vp/'object_profiles.json',verify_profiles(dest,p));meshcheck(p,path=dest,source=src,report_dir=vp);shutil.copy2(vp/f"{p['id']}_native_mesh.json",vp/'native_mesh.json');shutil.copy2(dest,q/'projects'/dest.name);stage.S=S;n={}
  for vk,fk in [('v','f'),('fin_v','fin_f'),('teeth_v','teeth_f')]:n[vk],n[fk]=stage.merge_role(p['items'],(vk,fk))
  np.savez_compressed(q/'parts'/f'{pid}.npz',**n);write(q/'design'/f'{pid}.json',{'id':pid,'required_layer_height_mm':.2,'required_initial_layer_height_mm':.2,'whole_plate_geometry_merged_from_actual_instance_transforms':True});write(vp/'plate_manifest.json',{'id':pid,'items':[{'rotation_matrix':np.eye(3).tolist(),'translation_mm':[0,0,0]}],'real_instance_manifest':p})
  lp=vp/'local_extrusion.json'
  if not lp.exists()or json.loads(lp.read_text()).get('project_sha256')!=sha(dest):localcheck(q/'projects'/dest.name,lp)
  for module in [full,recover,finer,exact,lateral]:module.O=S
  fp=vp/'full_bead_contacts.json'
  if not fp.exists()or json.loads(fp.read_text()).get('project_sha256')!=sha(dest):full.check(pid,'native')
  d=finer.refine(pid,'native')
  if d['external_islands']:d=exact.trial(pid,'native')
  if d['critical_external_runs']:d=lateral.check(pid,'native')
  r={'plate':p['id'],'instances':len(p['items']),'source_ids':[i['id']for i in p['items']],'native_clear':d['native_review_resolved'],'external_islands':d['external_island_count'],'critical_external_runs':d['critical_external_count'],'project_sha256':sha(dest),'geometry_qualified_per_instance':True,'all_original_meshes_and_print_rotations_preserved':True,'all_original_effective_object_profiles_preserved':True,'native_mesh_preserved':True,'physical_print_tested':False};assert r['project_sha256']==d['project_sha256'];write(done,r);print('COMPACT231_PLATE',r,flush=True);return r
 except Exception:
  r={'plate':p['id'],'error':traceback.format_exc()};print('COMPACT231_ERROR',r,flush=True);return r
def main():
 import argparse
 a=argparse.ArgumentParser();a.add_argument('--prepare',action='store_true');a.add_argument('--id',nargs='*');a.add_argument('--workers',type=int,default=2);args=a.parse_args()
 if args.prepare:prepare()
 m=json.loads((S/'stage_manifest.json').read_text());ps=[p for p in m['plates']if args.id is None or p['id']in args.id];out=[]
 with concurrent.futures.ProcessPoolExecutor(max_workers=args.workers)as pool:
  for f in concurrent.futures.as_completed([pool.submit(audit,p)for p in ps]):out.append(f.result());write(S/('progress_'+('_'.join(args.id)if args.id else'all')+'.json'),out)
 print('COMPACT231_DONE',[(r['plate'],r.get('native_clear'),r.get('external_islands'),r.get('critical_external_runs'),r.get('error','')[:100])for r in out],flush=True)
if __name__=='__main__':main()
