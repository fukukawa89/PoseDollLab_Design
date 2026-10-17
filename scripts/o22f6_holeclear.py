"""Reproducible O22-F6 fastener clearance audit. F5 is never overwritten."""
from pathlib import Path
import sys,json,hashlib,shutil,math,re,argparse,copy
import numpy as np
import manifold3d as md
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'scripts'))
from build_revo22_fins import solid,vf,union,box
from o22_material_components import material_components
B=R/'Hardware/PoseDoll44/bench/revO22';SRC=B/'O22F5_Compact';OUT=B/'O22F6_HoleClear';WORK=B/'diagnostics/O22F6_holeclear_20261015';TOL=1e-6
PROJECT_SUFFIX='PLA_holeclear';PRINT_SETTINGS_ID='O22-F6 hole-clear / A1 mini PLA 0.4';ORIGINAL_PROFILE_IDS=frozenset();SCREEN_LABEL='holeclear'

def put(p,x):
 p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(x,ensure_ascii=False,indent=2),encoding='utf-8')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def H(Q,t):
 a=np.eye(4);a[:3,:3]=Q;a[:3,3]=t;return a
def save_mesh(p,s):
 v,f=vf(s);p.parent.mkdir(parents=True,exist_ok=True);np.savez_compressed(p,v=v,f=f)
def fastener(name):return bool(re.search(r'M\d|shoulder|washer|screw|bolt|nut',name,re.I))
def assembly_context():
 import build_revo22_assembly as assembly
 scratch=WORK/'assembly';scratch.mkdir(parents=True,exist_ok=True)
 for name in ['sensor_fit.json','end_axis_fit.json','sensor_cassettes.npz','end_axis_parts.npz']:
  if not(scratch/name).exists():shutil.copy2(B/'mechanical'/name,scratch/name)
 assembly.D=scratch;assembly.b.D=scratch
 parts,meta,*rest=assembly.model();hw={k:s for k,s in parts.items() if fastener(meta[k].get('sku')or'')}
 print('ASSEMBLY',len(parts),'FASTENERS',len(hw),flush=True);return parts,meta,hw

def audit():
 manifest=json.loads((SRC/'manifest.json').read_text(encoding='utf-8'));source_guards=json.loads((B/'a1mini_supports/design/all_protected_volumes.json').read_text());exports={r['id']:r for r in json.loads((B/'print_batch/manifest.json').read_text())['rows']}
 selection=json.loads((WORK/'hardware_cavity_selection.json').read_text());parts,meta,hw=assembly_context();hwbounds={k:np.array(s.bounding_box()) for k,s in hw.items()};offsets=np.array([[x,y,z]for x in[-.25,.25]for y in[-.25,.25]for z in[-.25,.25]]);summary=[]
 for r in manifest['rows']:
  pid=r['id'];n=np.load(SRC/f'parts/{pid}.npz');d=json.loads((SRC/f'design/{pid}.json').read_text());body,fins,teeth=[solid(n[v],n[f])for v,f in[('v','f'),('fin_v','fin_f'),('teeth_v','teeth_f')]]
  orient=H(d['orientation']['matrix'],d['orientation']['source_translation_mm']);guards=[];records=[];seen=set()
  for item in source_guards['objects']:
   if item['id']!=pid:continue
   for q in item['volumes']:
    if not fastener(q['feature']):continue
    token=json.dumps({k:v for k,v in q.items()if k in['feature','shape','radius_mm','z_mm','min_mm','max_mm','local_to_source_print_matrix']},sort_keys=True)
    if token in seen:continue
    seen.add(token)
    if q['shape']=='box':s=box(np.array(q['min_mm'])-.2,np.array(q['max_mm'])+.2)
    else:
     radius=q['radius_mm']/(math.cos(math.pi/6)if'nut'in q['feature'].lower()else 1)+.2;z0,z1=q['z_mm'];s=md.Manifold.cylinder(z1-z0+.5,radius,radius,96).translate([0,0,z0-.25])
    s=s.transform((orient@np.array(q['local_to_source_print_matrix']))[:3,:])-body;guards.append(s);records.append(dict(source='analytic_cad',feature=q['feature'],evidence=q['evidence'],fin_mm3=max(0.,float((fins^s).volume())),tooth_mm3=max(0.,float((teeth^s).volume()))))
  alignment=None;key=d['part'];hw_used=[]
  if key in parts and not pid.startswith('N'):
   a=np.array(meta[key]['transform'],float).copy()
   if pid.startswith(('P','X'))and np.linalg.det(a[:3,:3])<0:a[:3,1]*=-1
   bed=exports[pid]['bed'];transform=orient@H(bed['rotation'],bed['translation_mm'])@np.linalg.inv(a);reference=parts[key].transform(transform[:3,:]);alignment=float((body^reference).volume())/max(float(body.volume()),1e-9)
   assert alignment>.97,(pid,'assembly/source alignment',alignment)
   worldbody=body.transform(np.linalg.inv(transform)[:3,:]);bb=np.array(worldbody.bounding_box())
   for k,s in hw.items():
    if not selection.get(pid,{}).get(k,{}).get('is_cavity',False):continue
    hb=hwbounds[k];sep=np.maximum(np.maximum(hb[:3]-bb[3:],bb[:3]-hb[3:]),0)
    if np.linalg.norm(sep)>.65:continue
    if s.min_gap(worldbody,.65)>.55:continue
    vv=vf(s)[0];expanded=md.Manifold.hull_points((vv[:,None,:]+offsets).reshape(-1,3));g=expanded.transform(transform[:3,:])-body;guards.append(g);hw_used.append(k);records.append(dict(source='assembled_fastener',feature=k,sku=meta[k].get('sku'),margin_mm=.25,fin_mm3=max(0.,float((fins^g).volume())),tooth_mm3=max(0.,float((teeth^g).volume()))))
  guard=union(guards);save_mesh(WORK/f'guards/{pid}.npz',guard);before=max(0.,float(((fins+teeth)^guard).volume()))
  result=dict(id=pid,part=key,source_npz_sha256=sha(SRC/f'parts/{pid}.npz'),guard_count=len(guards),analytic_feature_count=sum(x['source']=='analytic_cad'for x in records),assembly_fastener_count=len(hw_used),source_alignment_fraction=alignment,support_count=r['fin_count'],support_in_fastener_clearance_mm3=before,fin_intrusion_mm3=max(0.,float((fins^guard).volume())),tooth_intrusion_mm3=max(0.,float((teeth^guard).volume())),features=records)
  put(WORK/f'initial/{pid}.json',result);summary.append({k:v for k,v in result.items()if k!='features'});print('AUDIT',pid,len(guards),'intrusion',round(before,6),flush=True);put(WORK/'initial_summary.json',summary)
 put(WORK/'inventory.json',dict(source_manifest_sha256=sha(SRC/'manifest.json'),types=len(summary),instances=sum(len(p['items'])for p in manifest['plates']),plates=len(manifest['plates']),guard_policy='Source fastener cores expanded radially 0.2 mm and axially 0.25 mm; hex corners covered by circumcircle; assembled screw/nut/washer/shoulder/self-tap convex envelopes expanded 0.25 mm. Permanent body is excluded from cuts.',rows=summary))


def repair():
 manifest=json.loads((SRC/'manifest.json').read_text());summary=[]
 for r in manifest['rows']:
  pid=r['id'];raw=dict(np.load(SRC/f'parts/{pid}.npz'));d=json.loads((SRC/f'design/{pid}.json').read_text());g=np.load(WORK/f'guards/{pid}.npz');guard=solid(g['v'],g['f']);body=solid(raw['v'],raw['f']);oldfin=solid(raw['fin_v'],raw['fin_f']);oldteeth=solid(raw['teeth_v'],raw['teeth_f']);old=oldfin+oldteeth
  intrusion=max(0.,float((old^guard).volume()));fin=oldfin;teeth=oldteeth;discarded=[]
  if intrusion>TOL:
   fin=fin-guard;teeth=teeth-guard
   for step in range(8):
    before=float((fin+teeth).volume());keep=[]
    for c in material_components(fin):
     if c.bounding_box()[2]>1e-5 or c.slice(.05).area()<.005:discarded.append(dict(role='fin',reason='not_bed_rooted',volume_mm3=float(c.volume())))
     else:keep.append(c)
    fin=union(keep);keep=[]
    for c in material_components(teeth):
     if (c^fin).volume()<.001 or(c^body).volume()<.001:discarded.append(dict(role='tooth',reason='not_connected_to_both_fin_and_body',volume_mm3=float(c.volume())))
     else:keep.append(c)
    teeth=union(keep);keep=[]
    for c in material_components(fin):
     if (c^teeth).volume()<.001:discarded.append(dict(role='fin',reason='no_retained_connector',volume_mm3=float(c.volume())))
     else:keep.append(c)
    fin=union(keep)
    if abs(before-float((fin+teeth).volume()))<TOL:break
   raw['fin_v'],raw['fin_f']=vf(fin);raw['teeth_v'],raw['teeth_f']=vf(teeth)
  new=fin+teeth;remaining=max(0.,float((new^guard).volume()));assert remaining<TOL,(pid,remaining)
  whole=body+new;cc=material_components(whole);bodycc=material_components(body)
  assert len(cc)==len(bodycc),(pid,'disconnected_print',len(cc),len(bodycc))
  assert (fin^body).volume()<TOL,(pid,'fin_body_overlap')
  OUT.joinpath('parts').mkdir(parents=True,exist_ok=True)
  if intrusion>TOL:np.savez_compressed(OUT/f'parts/{pid}.npz',**raw)
  else:shutil.copy2(SRC/f'parts/{pid}.npz',OUT/f'parts/{pid}.npz')
  after=np.load(OUT/f'parts/{pid}.npz');assert np.array_equal(after['v'],raw['v'])and np.array_equal(after['f'],raw['f'])
  result=dict(id=pid,part=d['part'],changed=intrusion>TOL,before_intrusion_mm3=intrusion,after_intrusion_mm3=remaining,removed_support_mm3=max(0.,float((old-new).volume())),discarded_components=discarded,body_vertices_and_faces_identical=True,geometry_components=len(cc),all_retained_fins_bed_rooted=True,all_retained_connectors_touch_fin_and_body=True,parts_sha256=sha(OUT/f'parts/{pid}.npz'),physical_print_tested=False)
  d.update(f6_hole_clearance=result,connector_void_policy='no_support_in_fastener_clearance',f5_tooth_records_are_historical=True,physical_print_tested=False)
  put(OUT/f'design/{pid}.json',d);put(WORK/f'repair/{pid}.json',result);summary.append(result);print('REPAIR',pid,result['changed'],round(result['removed_support_mm3'],4),len(discarded),flush=True)
 put(WORK/'repair_summary.json',summary)

def build_plate(p):
 import zipfile,xml.etree.ElementTree as ET
 import package_revo22_fins_v4 as pack
 from prepare_revo22_f3 import slicer
 from verify_revo22_f3_native_mesh import check as meshcheck
 pid=p['id'];pack.O=OUT;pack.WORK=WORK/'build';pack.WORK.mkdir(parents=True,exist_ok=True);pack.PROCESS_LAYER_HEIGHT=p['profile']['layer'];pack.INITIAL_LAYER_HEIGHT=p['profile']['initial'];pack.FUSE_PRINT_GEOMETRY=True
 source,work=pack.build(p)
 with zipfile.ZipFile(SRC/p['project'])as z:old_settings=json.loads(z.read('Metadata/project_settings.config'));old_cfg=ET.fromstring(z.read('Metadata/model_settings.config'));ranges=z.read('Metadata/layer_config_ranges.xml')if'Metadata/layer_config_ranges.xml'in z.namelist()else None
 with zipfile.ZipFile(source)as z:data={k:z.read(k)for k in z.namelist()}
 overrides=json.loads((WORK/'profile_overrides.json').read_text()) if (WORK/'profile_overrides.json').exists() else {}
 old_by_name={next(q.get('value')for q in o.findall('metadata')if q.get('key')=='name'):o for o in old_cfg.findall('object')};cfg=ET.fromstring(data['Metadata/model_settings.config'])
 for obj in cfg.findall('object'):
  name=next(q.get('value')for q in obj.findall('metadata')if q.get('key')=='name');old=old_by_name[name]
  for q in list(obj.findall('metadata')):obj.remove(q)
  for q in old.findall('metadata'):
   qq=copy.deepcopy(q);key=qq.get('key');part_id=next(it['id'] for it in p['items'] if it['object_name']==name)
   if key=='counterbore_hole_bridging' and part_id not in ORIGINAL_PROFILE_IDS:qq.set('value','none')
   if key in overrides.get(part_id,{}):qq.set('value',str(overrides[part_id][key]))
   obj.append(qq)
 old_settings['print_settings_id']=PRINT_SETTINGS_ID;assert old_settings['filament_type']==['PLA'] and old_settings['enable_support']=='0'
 data['Metadata/project_settings.config']=json.dumps(old_settings).encode();data['Metadata/model_settings.config']=ET.tostring(cfg,encoding='utf-8',xml_declaration=True)
 root=ET.fromstring(data['3D/3dmodel.model'])
 for q in root.findall('{*}metadata'):
  if q.get('name')=='Title':q.text=pid+' O22-F6'
 data['3D/3dmodel.model']=ET.tostring(root,encoding='utf-8',xml_declaration=True)
 if ranges:data['Metadata/layer_config_ranges.xml']=ranges
 with zipfile.ZipFile(source,'w',zipfile.ZIP_DEFLATED)as z:
  for k,v in data.items():z.writestr(k,v)
 dest=OUT/f'projects/{pid}_O22F6_{PROJECT_SUFFIX}.3mf';dest.parent.mkdir(parents=True,exist_ok=True);vp=WORK/f'plates/{pid}';vp.mkdir(parents=True,exist_ok=True)
 result=slicer(source,dest,work/'orca',timeout=1800);assert result['complete'],result
 meshcheck(p,path=dest,source=source,report_dir=vp,expected_layer_height=p['profile']['layer'],expected_initial_layer_height=p['profile']['initial'])
 with zipfile.ZipFile(dest)as z:
  actual=json.loads(z.read('Metadata/project_settings.config'));config=ET.fromstring(z.read('Metadata/model_settings.config'))
  assert actual==old_settings,('settings_changed',pid)
  new_by_name={next(q.get('value')for q in o.findall('metadata')if q.get('key')=='name'):o for o in config.findall('object')}
  assert set(new_by_name)=={it['object_name']for it in p['items']}
  for name in new_by_name:
   old=old_by_name[name]
   before={q.get('key'):q.get('value')for q in old.findall('metadata')};after={q.get('key'):q.get('value')for q in new_by_name[name].findall('metadata')};part_id=next(it['id']for it in p['items']if it['object_name']==name)
   if part_id not in ORIGINAL_PROFILE_IDS:before['counterbore_hole_bridging']='none'
   before.update(overrides.get(part_id,{}));assert after==before,(pid,name,'object_profile_changed')
   assert after.get('counterbore_hole_bridging')!='filled',(pid,name,'sacrificial_filling_enabled')
 result.update(project_sha256=sha(dest),source_sha256=sha(source),object_profiles_verified=True,sacrificial_hole_fill_disabled=True,profile_overrides=overrides,restored_original_profile_ids=sorted(set(it['id']for it in p['items'])&set(ORIGINAL_PROFILE_IDS)),original_plate_layout_preserved=True)
 put(vp/'slice.json',result);print('SLICE_DONE',pid,round(result['elapsed_s'],1),flush=True);return result

def build():
 import concurrent.futures
 manifest=json.loads((SRC/'manifest.json').read_text());assert len(list((OUT/'parts').glob('*.npz')))==150
 with concurrent.futures.ProcessPoolExecutor(max_workers=2)as pool:
  fs={pool.submit(build_plate,p):p['id']for p in manifest['plates']}
  for f in concurrent.futures.as_completed(fs):f.result()

def screen_plate(p):
 import time
 deadline=time.time()+1800
 while not (WORK/f"plates/{p['id']}/slice.json").exists():
  assert time.time()<deadline,'Timed out waiting for plate slice'
  time.sleep(1)
 from verify_revo22_f4_local_extrusion import check as localcheck
 import verify_revo22_f4_full_bead as full
 import o22_recover_native_flag_paths as recover
 import refine_revo22_f4_full_bead as finer
 import refine_revo22_f4_islands84 as exact
 import refine_revo22_f4_lateral104 as lateral
 from audit_revo22_f5_native271 import endpoints
 pid='PLATE_'+p['id'];label=SCREEN_LABEL+'_'+sha(OUT/f"projects/{p['id']}_O22F6_{PROJECT_SUFFIX}.3mf")[:12];label+=('_parts_'+'_'.join(sorted(globals()['TARGET_PART_IDS'])) if globals().get('TARGET_PART_IDS') else '_full');folder=WORK/f'candidates/{pid}/{label}';vp=folder/'verification'
 for sub in['parts','design','projects','verification']:(folder/sub).mkdir(parents=True,exist_ok=True)
 dest=OUT/f"projects/{p['id']}_O22F6_{PROJECT_SUFFIX}.3mf";shutil.copy2(dest,folder/'projects'/dest.name);allarrays={}
 for vk,fk in[('v','f'),('fin_v','fin_f'),('teeth_v','teeth_f')]:
  vs=[];fs=[];off=0
  for it in p['items']:
   n=np.load(OUT/f"parts/{it['id']}.npz");v=n[vk]@np.array(it['rotation_matrix']).T+np.array(it['translation_mm']);f=n[fk];vs.append(v);fs.append(f+off);off+=len(v)
  allarrays[vk]=np.vstack(vs);allarrays[fk]=np.vstack(fs)
 np.savez_compressed(folder/f'parts/{pid}.npz',**allarrays);put(folder/f'design/{pid}.json',dict(id=pid,required_layer_height_mm=p['profile']['layer'],required_initial_layer_height_mm=p['profile']['initial']))
 put(vp/'plate_manifest.json',dict(id=pid,items=[dict(rotation_matrix=np.eye(3).tolist(),translation_mm=[0,0,0])],real_instance_manifest=p))
 if not(vp/'local_extrusion.json').exists():
  import verify_revo22_f4_local_extrusion as lc
  scope=globals().get('TARGET_PART_IDS');extract=lc.extract_detailed
  if scope:
   bounds=[np.array(it['bounds_mm']) for it in p['items'] if it['id']in scope]
   def scoped_extract(*args,**kwargs):
    rep,raw,features,names=extract(*args,**kwargs);a=np.asarray(raw).reshape(-1,9);mask=np.zeros(len(a),bool)
    for bb in bounds:mask|=(a[:,0]>=bb[0]-.5)&(a[:,0]<=bb[3]+.5)&(a[:,1]>=bb[1]-.5)&(a[:,1]<=bb[4]+.5)
    return rep,a[mask],np.array(features)[mask],names
   lc.extract_detailed=scoped_extract
  try:localcheck(dest,vp/'local_extrusion.json')
  finally:lc.extract_detailed=extract
 for mod in[full,recover,finer,exact,lateral]:mod.O=WORK
 full.check(pid,label);d=finer.refine(pid,label)
 if d['external_islands']:d=exact.trial(pid,label)
 if d['critical_external_runs']:d=lateral.check(pid,label)
 d=endpoints(pid,label,root=WORK);d.update(project_sha256=sha(dest),candidate_label=label,scope_part_ids=globals().get('TARGET_PART_IDS'));put(WORK/f"plates/{p['id']}/support_paths.json",d);print('SCREEN_DONE',p['id'],d['external_island_count'],d['critical_external_count'],flush=True)
 return d

def screen():
 import concurrent.futures
 manifest=json.loads((SRC/'manifest.json').read_text())
 with concurrent.futures.ProcessPoolExecutor(max_workers=2)as pool:
  fs={pool.submit(screen_plate,p):p['id']for p in manifest['plates']}
  for f in concurrent.futures.as_completed(fs):f.result()

if __name__=='__main__':
 parser=argparse.ArgumentParser();parser.add_argument('action',choices=['audit','repair','build','screen']);args=parser.parse_args();globals()[args.action]()
