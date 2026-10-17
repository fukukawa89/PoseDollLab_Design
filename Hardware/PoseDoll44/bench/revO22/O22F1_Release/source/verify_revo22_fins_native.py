from pathlib import Path
import json,zipfile,xml.etree.ElementTree as ET,sys,hashlib
import numpy as np
from build_revo22_fins import O,solid,polygon
from package_revo22_fins import Q,P,transform
from o22_support_gcode import extract_paths
from shapely.geometry import LineString

def metadata(x):return {m.get('key'):m.get('value') for m in x.findall('metadata') if m.get('key')}
def mesh(ob):
 m=ob.find(Q+'mesh');v=np.array([[float(n.get(k)) for k in ['x','y','z']] for n in m.findall(Q+'vertices/'+Q+'vertex')]);f=np.array([[int(n.get(k)) for k in ['v1','v2','v3']] for n in m.findall(Q+'triangles/'+Q+'triangle')]);return v,f

def run(plate):
 pid=plate['id'];path=O/'projects'/f'{pid}_O22F1_PLA_fins.3mf';items={i['object_name']:i for i in plate['items']};checks=[];maxerror=0
 with zipfile.ZipFile(path) as z:
  docs={n:ET.fromstring(z.read(n)) for n in z.namelist() if n.endswith('.model')};root=docs['3D/3dmodel.model'];cfg=ET.fromstring(z.read('Metadata/model_settings.config'));configs={ob.get('id'):ob for ob in cfg.findall('object')};settings=json.loads(z.read('Metadata/project_settings.config'))
  assert settings['enable_support']=='0' and float(settings['layer_height'])==.2 and float(settings['initial_layer_print_height'])==.2
  assert settings['print_sequence']=='by layer' and settings['brim_type']=='no_brim'
  def walk(docid,oid,T):
   ob=docs[docid].find(Q+f'resources/{Q}object[@id="{oid}"]')
   if ob.find(Q+'mesh') is not None:
    v,f=mesh(ob);return [(oid,v@T[:3,:3].T+T[:3,3],f)]
   out=[]
   for c in ob.findall(Q+'components/'+Q+'component'):out+=walk(c.get(P+'path',docid).lstrip('/'),c.get('objectid'),T@transform(c.get('transform')))
   return out
  for build in root.findall(Q+'build/'+Q+'item'):
   oid=build.get('objectid');co=configs[oid];name=metadata(co)['name'];it=items[name];n=np.load(O/'parts'/f"{it['id']}.npz");M=np.array(it['rotation_matrix']);t=np.array(it['translation_mm']);parts={p.get('id'):p for p in co.findall('part')};roles=[]
   assert metadata(co).get('enable_support','0')=='0'
   for subid,v,f in walk('3D/3dmodel.model',oid,transform(build.get('transform'))):
    sub=parts[subid];sn=metadata(sub)['name'];assert sub.get('subtype')=='normal_part'
    role='fin' if sn.startswith('FIN_BODY') else 'teeth' if sn.startswith('BREAKAWAY_TEETH') else 'part';vk,fk=('v','f') if role=='part' else ('fin_v','fin_f') if role=='fin' else ('teeth_v','teeth_f')
    expected=n[vk]@M.T+t;assert v.shape==expected.shape,(pid,name,role,v.shape,expected.shape)
    error=float(abs(v-expected).max());assert error<.00015,(pid,name,role,error)
    assert np.array_equal(f,n[fk]),(pid,name,role,'triangles_changed');maxerror=max(maxerror,error);roles.append(role)
    stat=sub.find('mesh_stat')
    if stat is not None:assert all(int(stat.get(k,'0'))==0 for k in ['edges_fixed','degenerate_facets','facets_removed','facets_reversed','backwards_edges'])
   assert 'part' in roles and len(roles)==len(set(roles));checks.append({'object_name':name,'roles':roles})
  assert len(checks)==len(items)
 report,raw=extract_paths(path);arr=np.asarray(raw).reshape(-1,8)
 assert report['out_of_bed_segment_count']==0
 assert all(x['segments']==0 for x in report['classes'][1:])
 toothchecks=[];footchecks=[]
 for it in plate['items']:
  d=json.loads((O/'design'/f"{it['id']}.json").read_text());M=np.array(it['rotation_matrix']);tr=np.array(it['translation_mm']);n=np.load(O/'parts'/f"{it['id']}.npz")
  for j,tooth in enumerate(d['teeth']):
   bb=np.array(tooth['bounds_mm']);p=(bb[:3]+bb[3:])/2;p=p@M.T+tr;z=bb[5]+tr[2];a=arr[np.abs(arr[:,5]-z)<.003];u=a[:,:2];v=a[:,3:5];dv=v-u
   denom=np.sum(dv*dv,axis=1);f=np.clip(np.sum((p[:2]-u)*dv,axis=1)/np.maximum(denom,1e-20),0,1);dist=np.linalg.norm(p[:2]-u-f[:,None]*dv,axis=1)
   near=float(dist.min()) if len(dist) else 999
   toothchecks.append({'object_name':it['object_name'],'tooth':j+1,'z_mm':float(z),'nearest_extrusion_centerline_mm':near,'path_within_half_tooth_width':near<=.3})
  if len(n['fin_f']):
   b=solid(n['fin_v'],n['fin_f']).transform(np.c_[M,tr]);a=arr[np.abs(arr[:,5]-.2)<.003];lines=[LineString([x[:2],x[3:5]]) for x in a]
   import shapely
   tree=shapely.STRtree(lines)
   for j,comp in enumerate(b.decompose()):
    footprint=polygon(comp.slice(.1));hits=tree.query(footprint,predicate='intersects');footchecks.append({'object_name':it['object_name'],'component':j+1,'first_layer_extrusion_present':len(hits)>0})
 sl=json.loads((O/'verification'/f'{pid}_slice.json').read_text())['result']['sliced_plates'][0]
 result={'plate':pid,'project_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'native_object_count':len(checks),'original_vertices_preserved_within_mm':maxerror,'original_triangle_indices_exact':True,'mesh_repair_changes':0,'auto_support_disabled':True,'source_and_fin_roles':checks,'gcode':{k:report[k] for k in ['segment_count','extrusion_moves','arc_moves','bounds_mm','out_of_bed_segment_count','features','warnings','unsupported_commands']},'all_fin_components_have_first_layer_extrusion':all(x['first_layer_extrusion_present'] for x in footchecks),'fin_first_layer_checks':footchecks,'teeth_path_checks':toothchecks,'teeth_without_nearby_path':sum(not x['path_within_half_tooth_width'] for x in toothchecks),'slicer_warnings':sl.get('warning_message'),'estimated_time_s':sl['total_predication'],'estimated_filament_g':sum(x['total_used_g'] for x in sl['filaments'])}
 (O/'verification'/f'{pid}_native_gcode.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8');print(pid,'mesh_delta',round(maxerror,7),'bed_roots',len(footchecks),'missing_roots',sum(not x['first_layer_extrusion_present'] for x in footchecks),'teeth',len(toothchecks),'missing_teeth',result['teeth_without_nearby_path'],'warnings',sl.get('warning_message'),flush=True)
 return result
if __name__=='__main__':
 plates=json.loads((O/'manifest.json').read_text())['plates']
 for p in plates:
  if len(sys.argv)>1 and p['id'] not in sys.argv[1:]:continue
  run(p)