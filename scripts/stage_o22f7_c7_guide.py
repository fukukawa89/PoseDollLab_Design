"""Stage a self-contained C7 assembly revision; keep the released package intact."""
from o22f7_animation import *
from build_revo22_assembly import b
import copy,itertools
C=WORK/'structure_revision';P=C/'print_candidate';N=B/'O22F7_PLA_AssemblyRevision';NG=N/'assembly/tutorials/assembly-o22'
if not N.exists():shutil.copytree(F,N,ignore=shutil.ignore_patterns('__pycache__'))
put(N/'RELEASED.json',{'status':'ASSEMBLY_REVISION_CANDIDATE','complete':False,'physical_print_tested':False})
for pid in ['W005A','W005B']:
 for sub in ['parts','design']:shutil.copy2(P/f'{sub}/{pid}.'+Path('')) if False else None
 for sub,suffix in [('parts','npz'),('design','json')]:shutil.copy2(P/f'{sub}/{pid}.{suffix}',N/f'{sub}/{pid}.{suffix}')
# Old W005 is superseded, and the old D05 is absent from the active project set.
for rel in ['parts/W005.npz','design/W005.json','records/W005.json','records/W005.js','geometry/W005_candidate.js','projects/D05_O22F7_PLA_final.3mf']:
 q=N/rel
 if q.exists():q.unlink()
changed=read(P/'changed_plates.json');m=read(F/'manifest.json');m['plates']=[next((c for c in changed['plates'] if c['id']==p['id']),p) for p in m['plates']]+[changed['plates'][1]]
for p in changed['plates']:shutil.copy2(P/p['project'],N/p['project'])
g=read(G/'guide-data.json');instances=[q for q in g['instances'] if q['id']!='W005'];newinstances=[]
for p in changed['plates']:
 for it in p['items']:
  if it['id'] not in ['W005A','W005B']:continue
  q=copy.deepcopy(it);q.update(address=p['id']+f"-{it['number']:02}",plate=p['id'],project=p['project'],optional=False,first_use='S02',name_zh='左锁骨／可拆根部' if it['id']=='W005A' else '左锁骨／连接长杆');q.pop('source_3mf',None);newinstances.append(q)
for q in instances:
 if q['plate']=='D05':q['project']=changed['plates'][0]['project']
 if q['part']=='frame/clavicle_r.protract_frame':q['first_use']='S02'
instances+=newinstances;instances.sort(key=lambda q:q['address']);g.update(instances=instances,on_doll_instances=186,main_instances=187,revision='O22F7-assembly-r4-C7');g['parts']={q['part']:q for q in instances if not q['optional']};g['first_use'].update({q['part']:'S02' for q in newinstances},**{'frame/clavicle_r.protract_frame':'S02'})
g['plates']=[{'id':p['id'],'project':p['project'],'items':[q for q in instances if q['plate']==p['id']],'preview':f"images/plates/{p['id']}.png",'count':len(p['items']),'optional_count':sum(q['optional'] for q in instances if q['plate']==p['id'])} for p in m['plates']]
for p in changed['plates']:g['native_project_sha256'][p['id']]=sha(N/p['project'])
g['hardware']['NUT_M2']['net_quantity']+=1;g['hardware']['NUT_M2']['suggested_total']+=1;g['hardware']['SCREW_M2_L6']={'sku':'SCREW_M2_L6','name_zh':'M2×6 内六角圆柱头机螺钉（头径 3.8 mm、头高 2 mm）','category':'金属标准件','net_quantity':1,'optional_spares':1,'suggested_total':2}
# A rigid split of the same moving frame: no new channel, axis or joint.
x=Build();x.begin(x.g['steps'][3]);mount=x.mount;meta=copy.deepcopy(x.meta);sc=copy.deepcopy(x.scene);raw=x.verts;z=np.load(C/'W005_C7.npz');key='frame/clavicle_l.protract_frame';root='revision/clavicle_l.root';nut='revision/clavicle_l.join_nut';screw='revision/clavicle_l.join_screw';old=next(o for o in sc['objects'] if o['label']==key)
for new,sku,role in [(root,None,'frame'),(nut,'NUT_M2','metal'),(screw,'SCREW_M2_L6','metal')]:
 o=copy.deepcopy(old);o.update(label=new,role=role,sku=sku,module=new)
 for attr in ['address','print_id','name_zh','project','part_url']:o.pop(attr,None)
 sc['objects'].append(o);meta['meta'][new]=dict(body='clavicle_l.protract_frame',module=new,owner='rigid_frame',sku=sku,transform=mount.tolist())
replace={key:'distal',root:'root',nut:'nut_0',screw:'screw_0'};chunks=[];meshes={};first=0
for o in sc['objects']:
 k=o['label']
 if k in replace:
  tri=z[replace[k]];normal=np.cross(tri[:,1]-tri[:,0],tri[:,2]-tri[:,0]);normal/=np.maximum(np.linalg.norm(normal,axis=1)[:,None],1e-20);a=np.concatenate([tri,np.repeat(normal[:,None,:],3,axis=1)],axis=2).reshape(-1,6).astype('<f4');o['matrix']=mount.flatten().tolist()
  if k in [key,root]:
   q=next(q for q in newinstances if q['part']==k);o.update(address=q['address'],name_zh=q['name_zh'],print_id=q['id'],project='../../../'+q['project'],body_revision='O22F7-C7',part_url='../../../index.html?id='+q['id'])
 else:
  mm=x.scene['meshes'][o['mesh']];a=raw[mm['first']:mm['first']+mm['count']]
 stamp=hashlib.sha256(a.tobytes()).hexdigest()[:24]
 if stamp not in meshes:meshes[stamp]={'first':first,'count':len(a),'min':a[:,:3].min(0).tolist(),'max':a[:,:3].max(0).tolist()};chunks.append(a);first+=len(a)
 o['mesh']=stamp;M=np.array(o['matrix']).reshape(4,4);corners=np.array(list(itertools.product(*zip(meshes[stamp]['min'],meshes[stamp]['max']))));v=corners@M[:3,:3].T+M[:3,3];o.update(bounds=[v.min(0).tolist(),v.max(0).tolist()],center=v.mean(0).tolist())
sc.update(meshes=meshes,geometry_url='geometry-o22f7-c7.bin',revision='O22F7-assembly-r4-C7',scope='186 installed print instances; rigid left clavicle split; original kinematics retained.');(NG/sc['geometry_url']).write_bytes(np.concatenate(chunks).tobytes());sc['geometry_sha256']=sha(NG/sc['geometry_url']);put(NG/'scene.json',sc);put(NG/'assembly_metadata_c7.json',meta)
extra=[root,nut,screw];g['steps'][1]['objects']=list(dict.fromkeys(g['steps'][1]['objects']+g['steps'][3]['objects']+g['steps'][10]['objects']+extra));g['steps'][3]['objects']+=extra;put(NG/'guide-data.json',g)
import o22f7_assembly_guide as ag
ag.F=N;ag.G=NG;ag.plate_images([p for p in g['plates'] if p['id'] in ['D05','D15']])
put(C/'revision_paths.json',{'package':str(N),'guide':str(NG),'new_parts':newinstances,'metadata':str(NG/'assembly_metadata_c7.json')});print('STAGED',N,flush=True)
