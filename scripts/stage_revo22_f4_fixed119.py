from pathlib import Path
import sys,json,numpy as np,copy,shutil,concurrent.futures,zipfile
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'scripts'))
import stage_revo22_f4_plates97 as base
import refine_revo22_f4_lateral104 as lateral
O=base.O;OLD=O/'plate_stage97';S=O/'plate_stage119'
def placed(it,xy):
 it=copy.deepcopy(it);lo=np.array(it['local_bounds_mm'][:3]);hi=np.array(it['local_bounds_mm'][3:]);t=np.array([*xy,0])-lo;bb=np.r_[lo+t,hi+t];it.update(rotation_z_deg=0,rotation_matrix=np.eye(3).tolist(),translation_mm=t.tolist(),x=xy[0],y=xy[1],bounds_mm=bb.tolist(),fins_bounds_mm=bb.tolist());return it
def clearance(a,b):
 a=np.array(a['bounds_mm']);b=np.array(b['bounds_mm']);return float(np.linalg.norm(np.maximum(np.maximum(a[:2]-b[3:5],b[:2]-a[3:5]),0)))
def prepare():
 S.mkdir(exist_ok=True);manifest=json.loads((OLD/'stage_manifest.json').read_text());ps=[];extras=[];flags={'F06':{'P049'},'F07':{'X037','X076'},'F08':{'X053','X057'}}
 for plate in manifest['plates']:
  if plate['id']not in flags and plate['id']!='F02':continue
  p=copy.deepcopy(plate)
  if p['id']=='F02':
   src=O/'candidates/W001/rot14_00_full';n=np.load(src/'parts/W001.npz');v=np.r_[n['v'],n['fin_v'],n['teeth_v']];it=p['items'][0];it.update(local_bounds_mm=np.r_[v.min(0),v.max(0)].tolist());p['items']=[placed(it,[6.,6.])];d=json.loads((src/'design/W001.json').read_text());p['profile'].update(layer=.2,initial=.2,wall=d.get('required_wall_generator','arachne'),overrides=d.get('required_process_overrides',{}));p['corrected_source_selection']={'W001':'rot14_00_full'}
  else:
   for it in list(p['items']):
    if it['id']not in flags[p['id']]:continue
    bb=it['bounds_mm'];new=placed(it,[bb[0],bb[1]]);valid=max(new['bounds_mm'][3:5])<=174 and min(new['bounds_mm'][:2])>=6 and all(clearance(new,other)>=5.99 for other in p['items']if other['number']!=it['number'])
    p['items'].remove(it)
    if valid:p['items'].append(new)
    else:extras.append(new)
  p['items'].sort(key=lambda i:i['number']);p['status']='Revalidate at the previously qualified Z rotation; previous failed stage retained.';ps.append(p)
 if extras:
  p={'id':'F13','title':'O22 F4 fixed print orientation','optional':False,'items':[],'profile':copy.deepcopy(ps[-1]['profile'])};x=y=6.;rowh=0.
  for it in sorted(extras,key=lambda i:-(i['local_bounds_mm'][4]-i['local_bounds_mm'][1])):
   w=it['local_bounds_mm'][3]-it['local_bounds_mm'][0];h=it['local_bounds_mm'][4]-it['local_bounds_mm'][1]
   if x+w>174:x=6;y+=rowh+6;rowh=0
   if y+h>174:ps.append(p);p={**p,'id':'F'+str(14+len(ps)-4),'items':[]};x=y=6;rowh=0
   it=placed(it,[x,y]);it['number']=len(p['items'])+1;it['object_name']=p['id']+'-'+str(it['number']).zfill(2)+' '+it['id']+' '+it['part'];p['items'].append(it);x+=w+6;rowh=max(rowh,h)
  if p['items']:ps.append(p)
 for p in ps:
  for it in p['items']:
   src=O/'candidates/W001/rot14_00_full'if it['id']=='W001'else OLD
   for sub,ext in [('parts','npz'),('design','json')]:
    (S/sub).mkdir(exist_ok=True);shutil.copy2(src/sub/f"{it['id']}.{ext}",S/sub/f"{it['id']}.{ext}")
 (S/'stage_manifest.json').write_text(json.dumps({'plates':ps,'source_stage':'plate_stage97','reason':'Preserve the individually verified Z orientation; move conflicting objects to another plate. Correct W001 source and actual 0.2 mm profile.'},ensure_ascii=False,indent=2));print('STAGE119',[(p['id'],[(i['id'],i['rotation_z_deg'])for i in p['items']])for p in ps],flush=True);return ps

def audit(p):
 base.S=S;r=base.audit(p)
 if not r.get('native_clear',False)and 'error'not in r:
  lateral.O=S;d=lateral.check('PLATE_'+p['id'],'native');r.update(native_clear=d['native_review_resolved'],external_islands=d['external_island_count'],critical_external_runs=d['critical_external_count']);(S/'candidates'/('PLATE_'+p['id'])/'native/verification/plate_result.json').write_text(json.dumps(r,indent=2))
 return r
if __name__=='__main__':
 ps=prepare();out=[]
 with concurrent.futures.ProcessPoolExecutor(max_workers=2)as p:
  for f in concurrent.futures.as_completed([p.submit(audit,q)for q in ps]):out.append(f.result());(S/'progress.json').write_text(json.dumps(out,indent=2))
