from pathlib import Path
import sys,json,copy,shutil,hashlib,numpy as np,concurrent.futures
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'scripts'))
from select_revo22_f4_repairs import select
import stage_revo22_f4_plates97 as base
import refine_revo22_f4_lateral104 as lateral
O=base.O;B=O.parent;S=O/'plate_stage136'
def prepare():
 S.mkdir(exist_ok=True);selected={};previous=json.loads((O/'plate_stage97/stage_manifest.json').read_text());already={i['original_object_name']for p in previous['plates']for i in p['items']};allmain=[i for p in json.loads((B/'a1mini/manifest.json').read_text())['plates']if not p['optional']for i in p['items']];samples=json.loads((R/'.local/o22-easy-support/S00/manifest.json').read_text())['items'];desired={i['id']for i in allmain if i['object_name']not in already}|{i['id']for i in samples}
 for q in select():
  if q['id']not in desired or not q['eligible_before_fin_geometry_check']:continue
  src=O/'candidates'/q['id']/q['label'];gp=src/'verification/geometry.json'
  if not gp.exists():continue
  g=json.loads(gp.read_text());npz=src/'parts'/f"{q['id']}.npz"
  if not g['geometric_constraints_passed']or g['npz_sha256']!=hashlib.sha256(npz.read_bytes()).hexdigest():continue
  d=json.loads((src/'design'/f"{q['id']}.json").read_text());prof={'layer':d.get('required_layer_height_mm',.2),'initial':d.get('required_initial_layer_height_mm',.2),'wall':d.get('required_wall_generator','arachne'),'overrides':d.get('required_process_overrides',{}),'fuse':d.get('fuse_print_geometry',True)};key=json.dumps(prof,sort_keys=True);n=np.load(npz);v=np.r_[n['v'],n['fin_v'],n['teeth_v']];lo=v.min(0);hi=v.max(0);selected[q['id']]=dict(q,profile_key=key,local_bounds_mm=np.r_[lo,hi].tolist(),npz_sha256=g['npz_sha256']);assert json.loads((src/'verification/plate_manifest.json').read_text())['items'][0]['rotation_z_deg']==0
  for sub,ext in [('parts','npz'),('design','json')]:
   (S/sub).mkdir(exist_ok=True);shutil.copy2(src/sub/f"{q['id']}.{ext}",S/sub/f"{q['id']}.{ext}")
 plates=[]
 for optional,items,prefix,num in [(False,[i for i in allmain if i['object_name']not in already and i['id']in selected],'F',14),(True,[i for i in samples if i['id']in selected],'S',1)]:
  if optional:print('SAMPLE_PENDING',[i['id']for i in samples if i['id']not in selected],flush=True)
  for key in sorted({selected[i['id']]['profile_key']for i in items}):
   group=sorted([i for i in items if selected[i['id']]['profile_key']==key],key=lambda i:-(selected[i['id']]['local_bounds_mm'][4]-selected[i['id']]['local_bounds_mm'][1]));p=None;x=y=6.;rowh=0.
   for source in group:
    q=selected[source['id']];lo=np.array(q['local_bounds_mm'][:3]);hi=np.array(q['local_bounds_mm'][3:]);w,h=(hi-lo)[:2]
    if p is None:p={'id':prefix+str(num).zfill(2),'title':'O22 F4 fixed orientation','optional':optional,'profile':json.loads(key),'items':[]};num+=1;x=y=6.;rowh=0
    if x+w>174:x=6.;y+=rowh+6;rowh=0.
    if y+h>174:
     plates.append(p);p={'id':prefix+str(num).zfill(2),'title':'O22 F4 fixed orientation','optional':optional,'profile':json.loads(key),'items':[]};num+=1;x=y=6.;rowh=0.
    assert max(w,h)<=168
    it=copy.deepcopy(source);number=len(p['items'])+1;t=np.array([x,y,0])-lo;it.update(number=number,original_object_name=source.get('original_object_name',source['object_name']),object_name=f"{p['id']}-{number:02} "+source['id']+' '+source['part'],local_bounds_mm=q['local_bounds_mm'],rotation_z_deg=0,rotation_matrix=np.eye(3).tolist(),translation_mm=t.tolist(),x=x,y=y,w=w,h=h,bounds_mm=np.r_[lo+t,hi+t].tolist(),fins_bounds_mm=np.r_[lo+t,hi+t].tolist());p['items'].append(it);x+=w+6;rowh=max(rowh,h)
   if p is not None:plates.append(p)
 out={'selection':selected,'plates':plates,'status':'Pending whole-plate audit; complete final package assembled separately'};(S/'stage_manifest.json').write_text(json.dumps(out,ensure_ascii=False,indent=2));print('STAGE136',[(p['id'],len(p['items']))for p in plates],flush=True);return plates

def audit(p):
 base.S=S;r=base.audit(p)
 if not r.get('native_clear',False)and'error'not in r:
  lateral.O=S;d=lateral.check('PLATE_'+p['id'],'native');r.update(native_clear=d['native_review_resolved'],external_islands=d['external_island_count'],critical_external_runs=d['critical_external_count']);(S/'candidates'/('PLATE_'+p['id'])/'native/verification/plate_result.json').write_text(json.dumps(r,indent=2))
 return r
if __name__=='__main__':
 ps=prepare();out=[]
 with concurrent.futures.ProcessPoolExecutor(max_workers=2)as pool:
  for f in concurrent.futures.as_completed([pool.submit(audit,p)for p in ps]):out.append(f.result());(S/'progress.json').write_text(json.dumps(out,indent=2))
