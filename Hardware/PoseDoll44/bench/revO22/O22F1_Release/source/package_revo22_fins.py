"""Write O22-F1 native Bambu projects, preserving O22 part geometry."""
from pathlib import Path
import json,zipfile,xml.etree.ElementTree as ET, numpy as np, sys,argparse,hashlib,copy
from build_revo22_fins import R,B,O
from build_revo22_supports import slice_project
Q='{http://schemas.microsoft.com/3dmanufacturing/core/2015/02}'
P='{http://schemas.microsoft.com/3dmanufacturing/production/2015/06}'
WORK=R/'.local/o22-fins';WORK.mkdir(exist_ok=True)
def meta(node,k,val):
 n=next((x for x in node.findall('metadata') if x.get('key')==k),None)
 if n is None:n=ET.SubElement(node,'metadata')
 n.set('key',k);n.set('value',str(val))
def transform(t):
 a=np.eye(4)
 if t:a[:3,:]=np.array(list(map(float,t.split()))).reshape(4,3).T
 return a
def write_mesh(res,oid,name,v,f):
 obj=ET.SubElement(res,Q+'object',{'id':str(oid),'type':'model','name':name})
 mesh=ET.SubElement(obj,Q+'mesh');verts=ET.SubElement(mesh,Q+'vertices');faces=ET.SubElement(mesh,Q+'triangles')
 for p in v:ET.SubElement(verts,Q+'vertex',dict(zip(['x','y','z'],[format(x,'.12g') for x in p])))
 for t in f:ET.SubElement(faces,Q+'triangle',dict(zip(['v1','v2','v3'],map(str,t))))
 return obj
def build(plate):
 pid=plate['id'];template=next((B/'a1mini_supports/projects').glob(pid+'_*PLA_supports.3mf'))
 with zipfile.ZipFile(template) as z:data={n:z.read(n) for n in z.namelist() if not (n.endswith('.gcode') or n.endswith('.png') or n=='Metadata/slice_info.config')}
 root=ET.fromstring(data['3D/3dmodel.model']);cfg=ET.fromstring(data['Metadata/model_settings.config'])
 docs={n:ET.fromstring(b) for n,b in data.items() if n.startswith('3D/Objects/') and n.endswith('.model')}
 maxid=max(int(x.get('id')) for d in [root]+list(docs.values()) for x in d.findall(Q+'resources/'+Q+'object'))
 settings=json.loads(data['Metadata/project_settings.config'])
 settings.update({'print_settings_id':'O22-F1 modeled fins PLA 0.4 / 0.20','enable_support':'0','layer_height':'0.2','initial_layer_print_height':'0.2','brim_type':'no_brim','brim_width':'0','skirt_loops':'0','print_sequence':'by layer','wall_loops':'3','wall_generator':'arachne','sparse_infill_density':'20%','enable_prime_tower':'0','bridge_speed':['25'],'outer_wall_speed':'60','inner_wall_speed':'100','normal_print_speed':'100','initial_layer_speed':'25','travel_speed':'300','default_acceleration':'2000','outer_wall_acceleration':'1000','inner_wall_acceleration':'1500','filament_colour':['#99BAC6']})
 # No inherited slicing directives or painted supports remain.
 for d in docs.values():
  for t in d.findall('.//'+Q+'triangle'):t.attrib.pop('paint_supports',None)
 configs={next(x.get('value') for x in ob.findall('metadata') if x.get('key')=='name'):ob for ob in cfg.findall('object')}
 groups={ob.get('id'):ob for ob in root.findall(Q+'resources/'+Q+'object')}
 builds={x.get('objectid'):x for x in root.findall(Q+'build/'+Q+'item')}
 evidence=[]
 for it in plate['items']:
  ob=configs[it['object_name']];oid=ob.get('id');group=groups[oid];comps=group.find(Q+'components')
  first=comps[0]
  for x in list(comps)[1:]:comps.remove(x)
  parts=ob.findall('part');source_part=next(x for x in parts if x.get('id')==first.get('objectid'))
  for x in parts:
   if x is not source_part:ob.remove(x)
  source_part.set('subtype','normal_part')
  for k,val in [('enable_support','0'),('brim_type','no_brim'),('brim_width','0'),('extruder','1')]:meta(ob,k,val)
  path=first.get(P+'path').lstrip('/');doc=docs[path];res=doc.find(Q+'resources')
  # Drop obsolete blocker meshes, not merely their references.
  for x in list(res):
   if x.tag==Q+'object' and x.get('id')!=first.get('objectid'):res.remove(x)
  n=np.load(O/'parts'/f"{it['id']}.npz")
  M=transform(builds[oid].get('transform'));inv=np.linalg.inv(M)
  roles=[]
  for role,vkey,fkey in [('FIN_BODY','fin_v','fin_f'),('BREAKAWAY_TEETH','teeth_v','teeth_f')]:
   if vkey not in n or len(n[fkey])==0:continue
   vs=n[vkey]@np.array(it['rotation_matrix']).T+it['translation_mm']
   loc=vs@inv[:3,:3].T+inv[:3,3];maxid+=1;name=role+' | '+it['object_name']
   write_mesh(res,maxid,name,loc,n[fkey])
   ET.SubElement(comps,Q+'component',{'objectid':str(maxid),P+'path':'/'+path,'transform':'1 0 0 0 1 0 0 0 1 0 0 0'})
   part=ET.SubElement(ob,'part',{'id':str(maxid),'subtype':'normal_part'});meta(part,'name',name);meta(part,'extruder','1')
   roles.append({'role':role,'vertices':len(vs),'triangles':len(n[fkey])})
  evidence.append({'object_name':it['object_name'],'added_parts':roles})
 for tag in [x for x in root.findall(Q+'metadata') if x.get('name','').startswith('Thumbnail_')]:root.remove(tag)
 data['Metadata/project_settings.config']=json.dumps(settings,ensure_ascii=False,indent=2).encode()
 data['Metadata/model_settings.config']=ET.tostring(cfg,encoding='utf-8',xml_declaration=True)
 data['3D/3dmodel.model']=ET.tostring(root,encoding='utf-8',xml_declaration=True)
 for k,v in docs.items():data[k]=ET.tostring(v,encoding='utf-8',xml_declaration=True)
 work=WORK/pid;work.mkdir(exist_ok=True)
 source=work/'input.3mf'
 with zipfile.ZipFile(source,'w',zipfile.ZIP_DEFLATED) as z:
  for k,v in data.items():z.writestr(k,v)
 (work/'manifest.json').write_text(json.dumps(plate,ensure_ascii=False,indent=2),encoding='utf-8')
 return source,work,evidence
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--plate',nargs='*');ap.add_argument('--slice',action='store_true');a=ap.parse_args()
 plates=json.loads((B/'a1mini/manifest.json').read_text())['plates']
 plates=[json.loads((R/'.local/o22-easy-support/S00/manifest.json').read_text())]+[p for p in plates if not p['optional']]
 (O/'projects').mkdir(exist_ok=True)
 for p in plates:
  if a.plate and p['id'] not in a.plate:continue
  source,work,evidence=build(p);dest=O/'projects'/f"{p['id']}_O22F1_PLA_fins.3mf"
  if a.slice:
   r=slice_project(source,dest,work)
   (O/'verification'/f"{p['id']}_slice.json").write_text(json.dumps({'result':r,'objects':evidence},ensure_ascii=False,indent=2),encoding='utf-8')
  else:dest.write_bytes(source.read_bytes())
  print(p['id'],dest.stat().st_size,flush=True)
if __name__=='__main__':main()
