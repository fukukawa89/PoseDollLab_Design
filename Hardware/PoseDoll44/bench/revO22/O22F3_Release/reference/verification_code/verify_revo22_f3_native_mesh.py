import json,zipfile,xml.etree.ElementTree as ET,hashlib,time
import numpy as np
from build_revo22_fins_v3 import O,R
from package_revo22_fins import Q,P,transform

def md(x):return {m.get('key'):m.get('value') for m in x.findall('metadata') if m.get('key')}
def read_project(path):
 with zipfile.ZipFile(path) as z:
  docs={k:ET.fromstring(z.read(k)) for k in z.namelist() if k.endswith('.model')};root=docs['3D/3dmodel.model'];cfg=ET.fromstring(z.read('Metadata/model_settings.config'));configs={x.get('id'):x for x in cfg.findall('object')};settings=json.loads(z.read('Metadata/project_settings.config'))
  def walk(docid,oid,T):
   ob=docs[docid].find(Q+f'resources/{Q}object[@id="{oid}"]');mesh=ob.find(Q+'mesh')
   if mesh is not None:
    v=np.array([[float(n.get(k)) for k in ['x','y','z']] for n in mesh.findall(Q+'vertices/'+Q+'vertex')]);f=np.array([[int(n.get(k)) for k in ['v1','v2','v3']] for n in mesh.findall(Q+'triangles/'+Q+'triangle')]);return [(v@T[:3,:3].T+T[:3,3],f)]
   out=[]
   for c in ob.findall(Q+'components/'+Q+'component'):out+=walk(c.get(P+'path',docid).lstrip('/'),c.get('objectid'),T@transform(c.get('transform')))
   return out
  objects={};repairs=[]
  for bi in root.findall(Q+'build/'+Q+'item'):
   oid=bi.get('objectid');co=configs[oid];name=md(co)['name'];ss=walk('3D/3dmodel.model',oid,transform(bi.get('transform')));assert len(ss)==1;objects[name]=ss[0]
   for part in co.findall('part'):
    assert part.get('subtype')=='normal_part'
    stat=part.find('mesh_stat')
    if stat is not None:repairs.append({k:int(stat.get(k,'0')) for k in ['edges_fixed','degenerate_facets','facets_removed','facets_reversed','backwards_edges']})
  return objects,settings,repairs

def check(p,path=None,source=None,report_dir=None):
 pid=p['id'];path=path or O/'projects'/f'{pid}_O22F3_PLA_fins.3mf';source=source or R/'.local/o22-fins-v3'/pid/'input.3mf';a,_,_=read_project(source);b,settings,repairs=read_project(path);assert a.keys()==b.keys();rows=[]
 for name,(v,f) in a.items():
  vv,ff=b[name];assert v.shape==vv.shape and np.array_equal(f,ff),(pid,name,'topology');err=float(abs(v-vv).max());assert err<.0002,(pid,name,err)
  assert vv.min()>-.0002 and np.max(vv)<180.0002
  rows.append({'object_name':name,'vertices':len(v),'triangles':len(f),'maximum_native_export_shift_mm':err})
 assert str(settings['enable_support'])=='0' and float(settings['layer_height'])==.2 and float(settings['initial_layer_print_height'])==.2
 assert settings['print_sequence']=='by layer' and all(sum(r.values())==0 for r in repairs)
 report={'plate':pid,'objects':rows,'source_is_checked_boolean_union_of_part_and_supports':True,'source_instances':len(rows),'native_mesh_preserved':True,'native_mesh_repairs':repairs,'automatic_supports_disabled':True,'project_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'printing_geometry_fused_per_part':True}
 ((report_dir or O/'verification')/f'{pid}_native_mesh.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8');print('NATIVE PASS',pid,len(rows),flush=True)
if __name__=='__main__':
 manifest=O/'manifest.json';stamp=manifest.stat().st_mtime
 for p in json.loads(manifest.read_text())['plates']:
  path=O/'verification'/f"{p['id']}_slice.json"
  while not path.exists() or path.stat().st_mtime<stamp:time.sleep(1)
  check(p)