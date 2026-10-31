"""Create fresh Bambu multi-part projects from rigidly oriented source meshes."""
import json,zipfile,uuid,xml.etree.ElementTree as ET,sys,argparse,collections,copy
import numpy as np
from build_revo22_fins_v4 import R,B,O,solid,union,vf
from pack_revo22_a1mini import best_pack
from package_revo22_fins import Q,P,meta,write_mesh
from prepare_revo22_f3 import slicer
WORK=R/'.local/o22-fins-v4';WORK.mkdir(exist_ok=True)
FUSE_PRINT_GEOMETRY=True
PROCESS_LAYER_HEIGHT=.2
INITIAL_LAYER_HEIGHT=.2
WALL_GENERATOR="arachne"
EXTRA_PROCESS_SETTINGS={}
REL='http://schemas.openxmlformats.org/package/2006/relationships';MODELREL='http://schemas.microsoft.com/3dmanufacturing/2013/01/3dmodel'
ET.register_namespace('',Q[1:-1]);ET.register_namespace('p',P[1:-1])
def xb(r):return ET.tostring(r,encoding='utf-8',xml_declaration=True)
def tf(M,t):return ' '.join(format(float(x),'.14g') for x in np.c_[M,t].T.flat)
def build(p):
 template=next((B/'a1mini_fins/projects').glob('S00*.3mf'))
 with zipfile.ZipFile(template) as z:settings=json.loads(z.read('Metadata/project_settings.config'));ct=z.read('[Content_Types].xml')
 settings.update({'print_settings_id':'O22-F4 modeled broad vertical fins','enable_support':'0','layer_height':str(PROCESS_LAYER_HEIGHT),'initial_layer_print_height':str(INITIAL_LAYER_HEIGHT),'brim_type':'no_brim','skirt_loops':'0','print_sequence':'by layer','wall_loops':'3','wall_generator':WALL_GENERATOR,'sparse_infill_density':'20%','enable_prime_tower':'0','bridge_speed':['20'],'outer_wall_speed':'40','inner_wall_speed':'70','initial_layer_speed':'20','default_acceleration':'1500','outer_wall_acceleration':'700','inner_wall_acceleration':'1000'})
 settings.update(EXTRA_PROCESS_SETTINGS)
 root=ET.Element(Q+'model',{'unit':'millimeter','{http://www.w3.org/XML/1998/namespace}lang':'en-US','requiredextensions':'p'});ET.SubElement(root,Q+'metadata',{'name':'Application'}).text='BambuStudio-02.08.02.61';ET.SubElement(root,Q+'metadata',{'name':'BambuStudio:3mfVersion'}).text='1';ET.SubElement(root,Q+'metadata',{'name':'Title'}).text=p['id']+' O22-F4'
 res=ET.SubElement(root,Q+'resources');build=ET.SubElement(root,Q+'build',{P+'UUID':str(uuid.uuid4())});cfg=ET.Element('config');pc=ET.SubElement(cfg,'plate')
 for k,v in [('plater_id','1'),('plater_name',p['id']),('locked','false'),('filament_map_mode','Auto For Flush'),('filament_maps','1'),('filament_volume_maps','0')]:meta(pc,k,v)
 relroot=ET.Element('Relationships',{'xmlns':REL});ET.SubElement(relroot,'Relationship',{'Target':'/3D/3dmodel.model','Id':'rel-1','Type':MODELREL});rels=ET.Element('Relationships',{'xmlns':REL});data={};oid=0
 for index,it in enumerate(p['items'],1):
  n=np.load(O/'parts'/f"{it['id']}.npz");doc=ET.Element(Q+'model',{'unit':'millimeter'});rr=ET.SubElement(doc,Q+'resources');path=f'3D/Objects/object_{index}.model';roles=[]
  if FUSE_PRINT_GEOMETRY:
   physical=union([solid(n[vk],n[fk]) for vk,fk in [('v','f'),('fin_v','fin_f'),('teeth_v','teeth_f')] if len(n[fk])]);assert str(physical.status())=='Error.NoError' and physical.volume()>0
   vv,ff=vf(physical);n={'v':vv,'f':ff};role_defs=[('PART','v','f')]
  else:role_defs=[('PART','v','f'),('FIN_BODY','fin_v','fin_f'),('BREAKAWAY_TEETH','teeth_v','teeth_f')]
  for role,vk,fk in role_defs:
   if len(n[fk])==0:continue
   oid+=1;name=it['object_name'] if role=='PART' else role+' | '+it['object_name'];write_mesh(rr,oid,name,n[vk],n[fk]);roles.append((oid,name,len(n[fk])))
  oid+=1;group=ET.SubElement(res,Q+'object',{'id':str(oid),'type':'model','name':it['object_name'],P+'UUID':str(uuid.uuid4())});comps=ET.SubElement(group,Q+'components');co=ET.SubElement(cfg,'object',{'id':str(oid)})
  for k,v in [('name',it['object_name']),('enable_support','0'),('extruder','1'),('brim_type','no_brim')]:meta(co,k,v)
  for subid,name,count in roles:
   ET.SubElement(comps,Q+'component',{'objectid':str(subid),P+'path':'/'+path,P+'UUID':str(uuid.uuid4()),'transform':tf(np.eye(3),[0,0,0])});part=ET.SubElement(co,'part',{'id':str(subid),'subtype':'normal_part','uuid':str(uuid.uuid4())});meta(part,'name',name);meta(part,'extruder','1');ET.SubElement(part,'mesh_stat',{'face_count':str(count),'edges_fixed':'0','degenerate_facets':'0','facets_removed':'0','facets_reversed':'0','backwards_edges':'0'})
  ET.SubElement(build,Q+'item',{'objectid':str(oid),P+'UUID':str(uuid.uuid4()),'transform':tf(np.array(it['rotation_matrix']),it['translation_mm']),'printable':'1'});inst=ET.SubElement(pc,'model_instance')
  for k,v in [('object_id',oid),('instance_id',0),('identify_id',index)]:meta(inst,k,v)
  data[path]=xb(doc);ET.SubElement(rels,'Relationship',{'Target':'/'+path,'Id':f'rel-{index}','Type':MODELREL})
 ET.SubElement(cfg,'assemble');data.update({'[Content_Types].xml':ct,'_rels/.rels':xb(relroot),'3D/_rels/3dmodel.model.rels':xb(rels),'3D/3dmodel.model':xb(root),'Metadata/model_settings.config':xb(cfg),'Metadata/project_settings.config':json.dumps(settings).encode()})
 work=WORK/p['id'];work.mkdir(exist_ok=True);src=work/'input.3mf'
 with zipfile.ZipFile(src,'w',zipfile.ZIP_DEFLATED) as z:
  for key,val in data.items():z.writestr(key,val)
 (work/'manifest.json').write_text(json.dumps(p,ensure_ascii=False,indent=2),encoding='utf-8');return src,work

def arrange(items,prefix,title,optional,start=1):
 inp=[]
 for it in items:
  n=np.load(O/'parts'/f"{it['id']}.npz");vv=np.concatenate([n[k] for k in ['v','fin_v','teeth_v'] if len(n[k])]);lo=vv.min(0);hi=vv.max(0);q=copy.deepcopy(it);q.update(w=hi[0]-lo[0],h=hi[1]-lo[1],local_bounds_mm=np.r_[lo,hi].tolist());inp.append(q)
 if len(inp)==1 and max(inp[0]['w'],inp[0]['h'])>168:
  it=inp[0];assert max(it['w'],it['h'])<=172,'Dedicated plate still requires at least 4 mm edge clearance'
  packed=[{'items':[dict(it,x=(180-it['w'])/2,y=(180-it['h'])/2,rotation_z_deg=0)]}]
 else:packed=best_pack(inp)
 out=[]
 for pn,pp in enumerate(packed,start):
  pid=f'{prefix}{pn:02}';p={'id':pid,'title':title+(f' {pn-start+1}/{len(packed)}' if len(packed)>1 else ''),'optional':optional,'items':[]}
  for number,it in enumerate(pp['items'],1):
   rot=np.eye(3) if it['rotation_z_deg']==0 else np.array([[0,-1,0],[1,0,0],[0,0,1.]])
   lo=np.array(it['local_bounds_mm'][:3]);hi=np.array(it['local_bounds_mm'][3:]);corners=np.array([[x,y,z] for x in [lo[0],hi[0]] for y in [lo[1],hi[1]] for z in [lo[2],hi[2]]]);rotated=corners@rot.T;t=np.array([it['x'],it['y'],0])-rotated.min(0);bb=np.r_[rotated.min(0)+t,rotated.max(0)+t]
   it.update(number=number,original_object_name=it.get('original_object_name',it['object_name']),object_name=f'{pid}-{number:02} '+it['id']+' '+it['part'],rotation_matrix=rot.tolist(),translation_mm=t.tolist(),bounds_mm=bb.tolist(),fins_bounds_mm=bb.tolist());p['items'].append(it)
  out.append(p)
 return out

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--id',nargs='*');ap.add_argument('--slice',action='store_true');a=ap.parse_args();m=json.loads((B/'a1mini/manifest.json').read_text());main=[i for p in m['plates'] if not p['optional'] for i in p['items']]
 if a.id:items=[next(i for i in main if i['id']==pid) for pid in a.id];plates=arrange(items,'V','几何与切片验证',True)
 else:
  plates=arrange([next(i for i in main if i['id']=='X046')],'F','胸架单件主套盘',False)+arrange([i for i in main if i['id']!='X046'],'F','O22-F4 主套',False,2);sam=json.loads((R/'.local/o22-easy-support/S00/manifest.json').read_text())['items'];plates=arrange(sam,'S','小样验证',True)+plates
  assert len([i for p in plates if not p['optional'] for i in p['items']])==186
  (O/'manifest.json').write_text(json.dumps({'version':'O22-F4','plates':plates,'source_instances':186,'source_types':150,'physical_print_tested':False},ensure_ascii=False,indent=2),encoding='utf-8')
 for p in plates:
  src,work=build(p);dest=O/'projects'/f"{p['id']}_O22F4_PLA_fins.3mf";dest.parent.mkdir(exist_ok=True)
  if a.slice:
   result=slicer(src,dest,work/'orca');assert result['complete'],result;(O/'verification'/f"{p['id']}_slice.json").write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
  else:dest.write_bytes(src.read_bytes())
  print(p['id'],len(p['items']),dest.stat().st_size,flush=True)
if __name__=='__main__':main()
