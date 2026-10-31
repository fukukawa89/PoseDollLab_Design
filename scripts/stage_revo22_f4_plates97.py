"""Freeze qualified single-part meshes into a draft plate stage, then audit actual whole-plate G-code."""
from pathlib import Path
import sys,json,shutil,hashlib,numpy as np,concurrent.futures,traceback
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'scripts'))
from select_revo22_f4_repairs import select
import package_revo22_fins_v4 as pack
from prepare_revo22_f3 import slicer
from verify_revo22_f4_local_extrusion import check as localcheck
import verify_revo22_f4_full_bead as full
import o22_recover_native_flag_paths as recover
import refine_revo22_f4_full_bead as finer
import refine_revo22_f4_islands84 as exact
O=R/'Hardware/PoseDoll44/bench/revO22/a1mini_fins_v4';S=O/'plate_stage97';B=O.parent

def prepare():
 S.mkdir(exist_ok=True);rows=select();selected={};groups={}
 for q in rows:
  if not q['eligible_before_fin_geometry_check']:continue
  p=O/'candidates'/q['id']/q['label'];gp=p/'verification/geometry.json'
  if not gp.exists():continue
  g=json.loads(gp.read_text());npz=p/'parts'/f"{q['id']}.npz"
  if not g['geometric_constraints_passed']or g['npz_sha256']!=hashlib.sha256(npz.read_bytes()).hexdigest():continue
  for sub,ext in [('parts','npz'),('design','json')]:
   (S/sub).mkdir(exist_ok=True);shutil.copy2(p/sub/f"{q['id']}.{ext}",S/sub/f"{q['id']}.{ext}")
  d=json.loads((p/'design'/f"{q['id']}.json").read_text());key=json.dumps({'layer':d.get('required_layer_height_mm',.2),'initial':d.get('required_initial_layer_height_mm',.2),'wall':d.get('required_wall_generator','arachne'),'overrides':d.get('required_process_overrides',{}),'fuse':d.get('fuse_print_geometry',True)},sort_keys=True);selected[q['id']]=dict(q,profile_key=key,npz_sha256=g['npz_sha256'])
 manifest=json.loads((B/'a1mini/manifest.json').read_text());main=[i for p in manifest['plates']if not p['optional']for i in p['items']if i['id']in selected];pack.O=S;plates=[];start=2
 for key in sorted({q['profile_key']for q in selected.values()}):
  items=[i for i in main if selected[i['id']]['profile_key']==key];pp=pack.arrange(items,'F','O22-F4 draft whole-plate validation',False,start);start+=len(pp)
  for p in pp:p['profile']=json.loads(key);p['status']='pending whole-plate validation'
  plates+=pp
 out={'stage':'Draft; not a complete printing release','source_type_count':150,'qualified_type_count':len(selected),'staged_instance_count':len(main),'pending_type_ids':[q['id']for q in rows if q['id']not in selected],'selection':selected,'plates':plates};(S/'stage_manifest.json').write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding='utf8');print('STAGE97_PREPARED',len(selected),len(main),len(plates),flush=True);return plates

def merge_role(items,role):
 vk,fk=role;vs=[];fs=[];offset=0
 for it in items:
  n=np.load(S/'parts'/f"{it['id']}.npz");v=n[vk]@np.array(it['rotation_matrix']).T+np.array(it['translation_mm']);f=n[fk]
  if len(f):vs.append(v);fs.append(f+offset);offset+=len(v)
 return np.concatenate(vs)if vs else np.empty((0,3)),np.concatenate(fs)if fs else np.empty((0,3),dtype=int)

def audit(p):
 try:
  pid='PLATE_'+p['id'];label='native';q=S/'candidates'/pid/label
  for sub in ['parts','design','verification','projects']:(q/sub).mkdir(parents=True,exist_ok=True)
  prof=p['profile'];pack.O=S;pack.WORK=R/'.local/o22-f4-stage97';pack.WORK.mkdir(exist_ok=True);pack.PROCESS_LAYER_HEIGHT=prof['layer'];pack.INITIAL_LAYER_HEIGHT=prof['initial'];pack.WALL_GENERATOR=prof['wall'];pack.EXTRA_PROCESS_SETTINGS=prof['overrides'];pack.FUSE_PRINT_GEOMETRY=prof['fuse'];src,work=pack.build(p);(S/'projects').mkdir(exist_ok=True);dest=S/'projects'/f"{p['id']}_O22F4_PLA_fins_DRAFT.3mf";rr=slicer(src,dest,work/'orca');assert rr['complete'],rr;shutil.copy2(dest,q/'projects'/dest.name);(q/'verification/slicer.json').write_text(json.dumps(rr,indent=2));n={}
  for vk,fk in [('v','f'),('fin_v','fin_f'),('teeth_v','teeth_f')]:n[vk],n[fk]=merge_role(p['items'],(vk,fk))
  np.savez_compressed(q/'parts'/f'{pid}.npz',**n);(q/'design'/f'{pid}.json').write_text(json.dumps({'id':pid,'required_layer_height_mm':prof['layer'],'required_initial_layer_height_mm':prof['initial'],'whole_plate_geometry_merged_from_actual_instance_transforms':True}));(q/'verification/plate_manifest.json').write_text(json.dumps({'id':pid,'items':[{'rotation_matrix':np.eye(3).tolist(),'translation_mm':[0,0,0]}],'real_instance_manifest':p},ensure_ascii=False,indent=2));localcheck(q/'projects'/dest.name,q/'verification/local_extrusion.json');full.O=S;recover.O=S;finer.O=S;exact.O=S;full.check(pid,label);d=finer.refine(pid,label)
  if d['external_islands']:d=exact.trial(pid,label)
  r={'plate':p['id'],'instances':len(p['items']),'source_ids':[i['id']for i in p['items']],'native_clear':d['native_review_resolved'],'external_islands':d['external_island_count'],'critical_external_runs':d['critical_external_count'],'project_sha256':d['project_sha256'],'geometry_qualified_per_instance':True,'physical_print_tested':False};(q/'verification/plate_result.json').write_text(json.dumps(r,indent=2));print('STAGE97_PLATE',r,flush=True);return r
 except Exception:return {'plate':p['id'],'error':traceback.format_exc()}
if __name__=='__main__':
 ps=prepare();out=[]
 with concurrent.futures.ProcessPoolExecutor(max_workers=2)as pool:
  for f in concurrent.futures.as_completed([pool.submit(audit,p)for p in ps]):
   out.append(f.result());(S/'progress.json').write_text(json.dumps(out,indent=2))
