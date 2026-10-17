"""Build O22 native Bambu projects with per-face, per-object support decisions.
No printer connection. Original source geometry is preserved and checked.
"""
from pathlib import Path
import argparse,collections,copy,hashlib,json,re,subprocess,zipfile,time
import xml.etree.ElementTree as ET
import numpy as np
from pack_revo22_a1mini import read_mesh,pack,mesh_at,write_3mf,volume
from verify_revo22_a1mini import inspect_paths_and_positions,profiles
from verify_revo22_native_supports import compare_projects
ROOT=Path(__file__).resolve().parents[1]
B=ROOT/'Hardware/PoseDoll44/bench/revO22'
OUT=B/'a1mini_supports'
WORK=ROOT/'.local/o22-easy-support'
Q='{http://schemas.microsoft.com/3dmanufacturing/core/2015/02}'
P='{http://schemas.microsoft.com/3dmanufacturing/production/2015/06}'
ET.register_namespace('',Q[1:-1])
ET.register_namespace('p',P[1:-1])
STUDIO=Path('D:/ProgramFiles/Bambu Studio/bambu-studio.exe')
SETTINGS={
'print_settings_id':'O22 PLA 0.4 selective supports v1',
'layer_height':'0.2','initial_layer_print_height':'0.2',
'enable_support':'1','support_type':'normal(auto)','support_style':'snug',
'support_on_build_plate_only':'0','support_threshold_angle':'30',
'support_top_z_distance':'0.28','support_bottom_z_distance':'0.28',
'independent_support_layer_height':'1','support_object_xy_distance':'0.45',
'support_object_first_layer_gap':'0.45','raft_first_layer_expansion':'0','support_interface_top_layers':'2',
'support_interface_bottom_layers':'2','support_interface_spacing':'0.5',
'support_bottom_interface_spacing':'0.5','support_interface_pattern':'rectilinear',
'support_interface_loop_pattern':'0','support_expansion':'0',
'support_base_pattern':'rectilinear','support_base_pattern_spacing':'3','tree_support_wall_count':'1',
'tree_support_branch_diameter':'2','tree_support_branch_distance':'3',
'tree_support_branch_angle':'35','tree_support_branch_diameter_angle':'5',
'support_remove_small_overhang':'0','support_critical_regions_only':'0',
'bridge_no_support':'0','support_filament':'0','support_interface_filament':'0',
'support_speed':['80'],'support_interface_speed':['40'],'bridge_speed':['25'],
'brim_type':'outer_only','brim_width':'2','brim_object_gap':'0.15',
'skirt_loops':'0','print_sequence':'by layer','enable_prime_tower':'0',
'wall_loops':'3','sparse_infill_density':'20%','filament_colour':['#BBC1C4'],
}
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def metadata(o,k,v):
 n=next((n for n in o.findall('metadata') if n.get('key')==k),None)
 if n is None:n=ET.SubElement(o,'metadata',{'key':k})
 n.set('value',str(v))
def xmlbytes(root):return ET.tostring(root,encoding='utf-8',xml_declaration=True)
def native_template(p):
    if p.get('native_template'):return Path(p['native_template'])
    native=ROOT/'.local/a1mini-slicer'/p['id']/'sliced.3mf'
    if native.exists():return native
    native.parent.mkdir(parents=True,exist_ok=True)
    configs=ROOT/'.local/a1mini-slicer'
    files,_=profiles(STUDIO.parent);machine,process,filament=files
    cmd=[str(STUDIO),'--arrange','0','--load-settings',str(machine)+';'+str(process),'--load-filaments',str(filament),'--curr-bed-type','Textured PEI Plate','--export-3mf',str(native),str(B/'a1mini'/p['file'])]
    run=subprocess.run(cmd,cwd=native.parent,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0),timeout=180)
    assert run.returncode==0 and native.exists(),(run.stdout or b'')[-2000:]
    return native

def blocker_mesh(vol,margin=.35):
    if vol['shape']=='box':
        lo=np.array(vol['min_mm'])-margin;hi=np.array(vol['max_mm'])+margin
        v=np.array([[x,y,z] for z in (lo[2],hi[2]) for y in (lo[1],hi[1]) for x in (lo[0],hi[0])])
        f=np.array([[0,2,1],[1,2,3],[4,5,6],[5,7,6],[0,1,4],[1,5,4],[2,6,3],[3,6,7],[0,4,2],[2,4,6],[1,3,5],[3,7,5]])
    else:
        n=48;r=vol['radius_mm']+margin;lo=vol['z_mm'][0]-margin;hi=vol['z_mm'][1]+margin
        v=np.array([[r*np.cos(a),r*np.sin(a),z] for z in (lo,hi) for a in np.arange(n)*2*np.pi/n]+[[0,0,lo],[0,0,hi]])
        f=np.array([tri for i in range(n) for tri in ([i,(i+1)%n,n+i],[(i+1)%n,n+(i+1)%n,n+i],[2*n,(i+1)%n,i],[2*n+1,n+i,n+(i+1)%n])])
    mat=np.array(vol['local_to_source_print_matrix']);return v@mat[:3,:3].T+mat[:3,3],f

class NormalGeometry:
    def __init__(self,z,met):self.z=z;self.normal={p.get('id') for o in met.findall('object') for p in o.findall('part') if p.get('subtype')=='normal_part'}
    def read(self,n):
        data=self.z.read(n)
        if n=='3D/3dmodel.model':
            d=ET.fromstring(data)
            for cs in d.findall('.//'+Q+'components'):
                for c in list(cs):
                    if c.get('objectid') not in self.normal:cs.remove(c)
            return xmlbytes(d)
        return data

def build(p):
 audit=json.loads((OUT/'design/object_strategy.json').read_text())
 decisions={x['object_name']:x for x in audit['objects']}
 candidates=json.loads((OUT/'design/mesh_candidates.json').read_text())
 additions={x['part']:x['additional_enforcer_faces'] for x in json.loads((OUT/'design/additional_enforcers.json').read_text())['objects']}
 protected={x['part']:x['volumes'] for x in json.loads((OUT/'design/all_protected_volumes.json').read_text())['objects']}
 native=native_template(p)
 work=WORK/p['id'];work.mkdir(parents=True,exist_ok=True)
 with zipfile.ZipFile(native) as z:data={n:z.read(n) for n in z.namelist()}
 settings=json.loads(data['Metadata/project_settings.config']);settings.update(SETTINGS)
 data['Metadata/project_settings.config']=json.dumps(settings,ensure_ascii=False,indent=2).encode()
 root=ET.fromstring(data['3D/3dmodel.model']);met=ET.fromstring(data['Metadata/model_settings.config'])
 names={next(n.get('value') for n in o.findall('metadata') if n.get('key')=='name'):o for o in met.findall('object')}
 parents={o.get('id'):o for o in root.findall(Q+'resources/'+Q+'object')}
 instances={o.get('objectid'):o for o in root.findall(Q+'build/'+Q+'item')}
 evidence=[]
 next_oid=max(int(o.get('id')) for o in root.findall(Q+'resources/'+Q+'object'))+100
 for item in p['items']:
  dec=decisions[item.get('strategy_original_object_name',item['object_name'])];c=candidates[item['source_3mf']]
  enabled=dec['support_strategy'].startswith('external_manual_tree')
  obj=names[item['object_name']];oid=obj.get('id');comp=parents[oid].find(Q+'components/'+Q+'component')
  path=comp.get(P+'path').lstrip('/');doc=ET.fromstring(data[path]);verts=doc.findall('.//'+Q+'vertex');faces=doc.findall('.//'+Q+'triangle')
  v=np.array([[float(n.get(k)) for k in ('x','y','z')] for n in verts]);f=np.array([[int(n.get(k)) for k in ('v1','v2','v3')] for n in faces])
  sv,sf=read_mesh(B/item['source_3mf']);pv=sv@np.array(item['rotation_matrix']).T+item['translation_mm']
  t=np.array(list(map(float,instances[oid].get('transform').split()))).reshape(4,3).T
  wv=v@t[:3,:3].T+t[:3,3]
  assert np.array_equal(f,sf),('triangle indexing changed',item['object_name'])
  err=float(np.max(abs(wv-pv)));assert err<.0001,(item['object_name'],err)
  chosen=set(c['external_downward_candidate_faces'])|set(additions.get(item['part'],[])) if enabled else set()
  centers=sv[sf].mean(axis=1)
  blocked=set()
  for vol in protected.get(item['part'],[]):
   inv=np.linalg.inv(np.array(vol['local_to_source_print_matrix']));loc=centers@inv[:3,:3].T+inv[:3,3];margin=.2
   if vol['shape']=='box':mask=np.all((loc>=np.array(vol['min_mm'])-margin)&(loc<=np.array(vol['max_mm'])+margin),axis=1)
   else:mask=(np.sum(loc[:,:2]**2,axis=1)<=(vol['radius_mm']+margin)**2)&(loc[:,2]>=vol['z_mm'][0]-margin)&(loc[:,2]<=vol['z_mm'][1]+margin)
   blocked.update(np.where(mask)[0].tolist())
  chosen-=blocked
  for vol in protected.get(item['part'],[]):
   if (item['id'],vol['feature']) not in {('X046','chest_C02_-1_D4_shoulder_hole'),('X038','waist/P_PCB_clearance')}:continue
   keep,_=blocker_mesh(vol,margin=0);lo=keep.min(0)-3.5;hi=keep.max(0)+3.5;start_z=keep[:,2].min()-.25
   tri=sv[sf];overlap=np.all(tri[:,:,:2].max(1)>=lo[:2],axis=1)&np.all(tri[:,:,:2].min(1)<=hi[:2],axis=1)&(tri[:,:,2].max(1)>=start_z)
   chosen-=set(np.where(overlap)[0].tolist())
  for j,face in enumerate(faces):
   if j in chosen:face.attrib.pop('paint_supports',None)
   else:face.set('paint_supports','8')
  brim=3 if dec['brim_recommended'] else (1.5 if np.prod(np.array(item['bounds_mm'])[3:5]-np.array(item['bounds_mm'])[:2])<200 else 0)
  if item['id'] in {'P035','P002','P018','P051','X058','P073','X066','P095','X073','P117','X080'}:brim=0
  for k,val in {'enable_support':int(enabled),'brim_type':'outer_only' if brim else 'no_brim','brim_width':brim,'brim_object_gap':.15}.items():metadata(obj,k,val)
  blocker_count=0
  if enabled:
   for vol in protected.get(item['part'],[]):
    bv,bf=blocker_mesh(vol,margin=0)
    blo=bv.min(0);bhi=bv.max(0);blo[:2]-=.8;bhi[:2]+=.8;blo[2]-=.25;bhi[2]=max(bhi[2],float(sv[:,2].max()))+.5
    if (item['id'],vol['feature']) in {('X046','chest_C02_-1_D4_shoulder_hole'),('X038','waist/P_PCB_clearance')}:blo[:2]-=2.7;bhi[:2]+=2.7
    if vol['feature']=='chest/P_shaft_bearing':blo[:2]-=.4;bhi[:2]+=.4
    shadow={'shape':'box','min_mm':blo.tolist(),'max_mm':bhi.tolist(),'local_to_source_print_matrix':np.eye(4).tolist()}
    vv,ff=blocker_mesh(shadow,margin=0);vv=vv@np.array(item['rotation_matrix']).T+item['translation_mm'];vv=(vv-t[:3,3])@t[:3,:3]
    next_oid+=1;boid=str(next_oid);bobj=ET.SubElement(doc.find(Q+'resources'),Q+'object',{'id':boid,'type':'model'});bm=ET.SubElement(bobj,Q+'mesh');vs=ET.SubElement(bm,Q+'vertices');ts=ET.SubElement(bm,Q+'triangles')
    for vtx in vv:ET.SubElement(vs,Q+'vertex',{k:format(float(x),'.9g') for k,x in zip('xyz',vtx)})
    for face in ff:ET.SubElement(ts,Q+'triangle',{k:str(int(x)) for k,x in zip(('v1','v2','v3'),face)})
    ET.SubElement(parents[oid].find(Q+'components'),Q+'component',{P+'path':'/'+path,'objectid':boid,'transform':'1 0 0 0 1 0 0 0 1 0 0 0'})
    part=ET.SubElement(obj,'part',{'id':boid,'subtype':'support_blocker'});metadata(part,'name','No support | '+vol['feature']);metadata(part,'matrix','1 0 0 0 0 1 0 0 0 0 1 0 0 0 0 1');blocker_count+=1
  data[path]=xmlbytes(doc)
  evidence.append({**item,'blocker_volumes':blocker_count,'strategy':'localized_snug_with_keepout_columns' if enabled else dec['support_strategy'],'enabled':enabled,'brim_mm':brim,'painted_enforcer_faces':0,'unpainted_allowed_faces':len(chosen),'painted_blocker_faces':len(faces)-len(chosen),'geometry_max_vertex_error_mm':err})
 data['Metadata/model_settings.config']=xmlbytes(met)
 data['3D/3dmodel.model']=xmlbytes(root)
 # Engine always reslices; cached paths from source template are not a delivered result.
 output=work/'input.3mf'
 with zipfile.ZipFile(output,'w',zipfile.ZIP_DEFLATED) as z:
  for n,b in data.items():z.writestr(n,b)
 (work/'decisions.json').write_text(json.dumps(evidence,ensure_ascii=False,indent=2),encoding='utf-8')
 return output,evidence

def slice_project(source,output,work):
 command=[str(STUDIO),'--arrange','0','--slice','0','--debug','2','--export-3mf',str(output),str(source)]
 started=time.time();rp=work/'result.json'
 process=subprocess.Popen(command,cwd=work,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
 complete_at=None;r={}
 while time.time()-started<360:
  try:
   if rp.exists() and rp.stat().st_mtime>=started-0.5:r=json.loads(rp.read_text())
   ready=r.get('return_code')==0 and output.exists() and output.stat().st_mtime>=started-0.5
   if ready:
    with zipfile.ZipFile(output) as z:
     assert 'Metadata/plate_1.gcode' in z.namelist()
     z.read('Metadata/project_settings.config')
    if complete_at is None:complete_at=time.time()
    if process.poll() is not None or time.time()-complete_at>5:break
   if process.poll() is not None and not ready:raise RuntimeError((process.returncode,r))
  except (OSError,ValueError,zipfile.BadZipFile):pass
  time.sleep(.2)
 else:
  process.terminate();raise TimeoutError('Bambu export did not complete')
 code=process.poll()
 lifecycle={'process_exit_code':code,'result_json_return_code':r.get('return_code'),'native_export_complete':True}
 if code is None:
  # Some local GUI-build CLI processes remain alive after a complete export.
  # Only terminate this helper, never the user's Bambu Studio GUI process.
  try:process.terminate();lifecycle['helper_stopped_after_completed_export']=True
  except OSError:lifecycle['helper_already_exited']=True
 (work/'process_completion.json').write_text(json.dumps(lifecycle,indent=2),encoding='utf-8')
 print(source.stem,'export complete',r.get('error_string'),flush=True)
 if r.get('return_code')!=0:raise RuntimeError(r)
 return r

def validate(p,path,evidence,result):
 with zipfile.ZipFile(path) as z:
  s=json.loads(z.read('Metadata/project_settings.config'));met=ET.fromstring(z.read('Metadata/model_settings.config'))
  assert s['nozzle_diameter']==['0.4'] and s['printer_model']=='Bambu Lab A1 mini'
  assert s['filament_settings_id']==['Generic PLA @BBL A1M']
  for k,v in SETTINGS.items():assert s[k]==v,(p['id'],k,s[k],v)
  names={next(n.get('value') for n in o.findall('metadata') if n.get('key')=='name'):o for o in met.findall('object')}
  assert set(names)=={i['object_name'] for i in p['items']}
  paint=collections.Counter()
  for n in z.namelist():
   if n.startswith('3D/Objects/') and n.endswith('.model'):
    d=ET.fromstring(z.read(n));paint.update(t.get('paint_supports','') for t in d.findall('.//'+Q+'triangle'))
  assert paint['4']==sum(i['painted_enforcer_faces'] for i in evidence),paint
  assert paint['8']==sum(i['painted_blocker_faces'] for i in evidence),paint
  for i in evidence:
   vals={n.get('key'):n.get('value') for n in names[i['object_name']].findall('metadata')}
   assert vals['enable_support']==str(int(i['enabled']))
  repairs={k:sum(int(t.get(k,0)) for t in met.findall('.//mesh_stat')) for k in ('edges_fixed','degenerate_facets','facets_removed','facets_reversed','backwards_edges')}
  assert not any(repairs.values()),repairs
  paths=inspect_paths_and_positions(NormalGeometry(z,met),p,met)
  features=collections.Counter(re.findall(r'^; FEATURE: (.+)$',z.read('Metadata/plate_1.gcode').decode(),re.M))
  return {'id':p['id'],'sha256':sha(path),'objects':len(names),'paint_faces':dict(paint),'mesh_repairs':repairs,'features':dict(features),'slice_result':result,**paths}

def sample_plate(m):
    ids=['P130','P033','X005','N003','X045','H004','P036']
    chosen=[]
    for pid in ids:
        item=next(copy.deepcopy(i) for p in m['plates'] for i in p['items'] if i['id']==pid)
        item['strategy_original_object_name']=item['object_name']
        v,f=read_mesh(B/item['source_3mf']);item['w'],item['h']=np.ptp(v,axis=0)[:2];chosen.append(item)
    ps=pack(chosen,1);assert len(ps)==1
    p={'id':'S00','slug':'support_trial','title':'先试印：支撑拆除与小孔配合','optional':True,'purpose':'Seven extra unchanged actual parts for PLA support release and fit trial','items':[]}
    objects=[]
    for n,i in enumerate(ps[0]['items'],1):
        v,f,rot,offset=mesh_at(i,read_mesh(B/i['source_3mf']));i.update(number=n,object_name=f"S00-{n:02d} {i['id']} {i['part']}",bounds_mm=[*v.min(0).tolist(),*v.max(0).tolist()],rotation_matrix=rot.tolist(),translation_mm=offset.tolist())
        objects.append((i['object_name'],v,f));p['items'].append(i)
    p['count']=len(objects);work=WORK/'S00';work.mkdir(parents=True,exist_ok=True)
    geometry=work/'geometry.3mf';write_3mf(geometry,objects)
    native=work/('native_template_'+str(len(objects))+'.3mf')
    if not native.exists():
        configs=ROOT/'.local/a1mini-slicer';configs.mkdir(parents=True,exist_ok=True)
        if not (configs/'machine.json').exists():profiles(STUDIO.parent)
        cmd=[str(STUDIO),'--arrange','0','--load-settings',str(configs/'machine.json')+';'+str(configs/'process.json'),'--load-filaments',str(configs/'filament.json'),'--curr-bed-type','Textured PEI Plate','--export-3mf',str(native),str(geometry)]
        run=subprocess.run(cmd,cwd=work,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0),timeout=180)
        assert run.returncode==0 and native.exists(),(run.stdout or b'')[-2000:]
    p['native_template']=str(native)
    (work/'manifest.json').write_text(json.dumps(p,ensure_ascii=False,indent=2),encoding='utf-8')
    return p

def main():
 parser=argparse.ArgumentParser();parser.add_argument('--plate',action='append');parser.add_argument('--roundtrip',action='store_true');parser.add_argument('--validate-only',action='store_true');a=parser.parse_args()
 for d in ['projects','verification','previews']: (OUT/d).mkdir(parents=True,exist_ok=True)
 m=json.loads((B/'a1mini/manifest.json').read_text())
 if not a.plate or 'S00' in a.plate:m['plates']=[sample_plate(m)]+m['plates']
 for p in m['plates']:
  if a.plate and p['id'] not in a.plate:continue
  work=WORK/p['id'];output=OUT/'projects'/(p['id']+'_'+p['slug']+'_PLA_supports.3mf')
  if a.validate_only:
   evidence=json.loads((work/'decisions.json').read_text());r=json.loads((work/'result.json').read_text());report=validate(p,output,evidence,r);report['native_roundtrip']=compare_projects(work/'input.3mf',output);target=OUT/'verification'/(p['id']+'.json')
  elif a.roundtrip:
   evidence=json.loads((work/'decisions.json').read_text());rw=work/'roundtrip';rw.mkdir(exist_ok=True)
   again=rw/'reopened.3mf';r=slice_project(output,again,rw);report=validate(p,again,evidence,r);report['native_roundtrip']=compare_projects(output,again)
   target=OUT/'verification'/(p['id']+'_roundtrip.json')
  else:
   source,evidence=build(p);r=slice_project(source,output,work);report=validate(p,output,evidence,r);report['native_roundtrip']=compare_projects(source,output)
   target=OUT/'verification'/(p['id']+'.json')
  target.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
  (OUT/'verification'/(p['id']+'_decisions.json')).write_text(json.dumps(evidence,ensure_ascii=False,indent=2),encoding='utf-8')
  print(p['id'],'PASS',report['objects'],'support',report['features'].get('Support'),flush=True)
if __name__=='__main__':main()
