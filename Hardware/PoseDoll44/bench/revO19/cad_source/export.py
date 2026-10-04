"""Export O19 leg carriers and an honest UE/physical-skeleton comparison viewer."""
from base import *
import copy,shutil,csv,importlib.util
from export_print_batch import orient
import print_io17
from device import digest
OLD=H/'bench/revO18';PAGE=H/'tutorials/full-doll-o19'

def load_export_helpers():
 spec=importlib.util.spec_from_file_location('frozen_o18_export',H/'cad/revO18/export.py');mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod);return mod

def bones(angles):
 ref=g.read(L.G3/'layouts/quinn/anatomy_profile.json');RT,RA=L.fk(ref,angles)
 _,_,states,f,pr=L.build('quinn',angles,geometry=False);PT,PA=L.fk(pr,angles);parents={s['child']:s for s in states};blue=[];orange=[]
 for s in states:
  if s['parent']=='pelvis':aa=RT['pelvis'][:3,3];pa=PT['pelvis'][:3,3]
  else:
   ps=parents[s['parent']];aa=RA[ps['axis_ids'][0]]['origin'];pa=PA[ps['axis_ids'][0]]['origin']
  aid=s['axis_ids'][0];bb=RA[aid]['origin'];pb=PA[aid]['origin']
  group='leg_'+s['id'][-1] if s['id'].startswith(('thigh_','foot_')) else 'leg_'+s['id'].split('.')[0][-1] if s['id'].startswith(('calf_','ball_')) else 'all'
  blue.append({'a':aa.tolist(),'b':bb.tolist(),'group':group,'joint':s['id']});orange.append({'a':pa.tolist(),'b':pb.tolist(),'group':group,'joint':s['id']})
 return blue,orange

def main():
 BENCH.mkdir(parents=True,exist_ok=True);PAGE.mkdir(parents=True,exist_ok=True);changes=g.read(OUT/'changes.json');new={k:from_tri_exact(v) for k,v in np.load(OUT/'changed_parts.npz').items()}
 # Runtime/electronics are inherited; no hardware or UE calibration is invented.
 for name in ('profiles','harness','source','electronics','firmware_source','firmware_binaries'):shutil.copytree(OLD/name,BENCH/name,dirs_exist_ok=True)
 for name in ('procurement.json','POWER_AND_USB.zh-CN.md','requirements-reference.txt','serve_preview.py','target_adapter_contract.json'):shutil.copy2(OLD/name,BENCH/name)
 manifest=g.read(OLD/'print_batch/manifest.json');rows=[];ids={};folder=BENCH/'print_batch';folder.mkdir(exist_ok=True);helper=load_export_helpers()
 for row in manifest['rows']:
  row=copy.deepcopy(row);row['instances']=[i for i in row['instances'] if i['part'] not in new]
  if not row['instances']:continue
  row['quantity_by_character']={'universal':len(row['instances'])};rows.append(row)
  for i in row['instances']:ids[i['part']]=row['id']
  for ext in ('stl','3mf'):shutil.copy2(OLD/'print_batch'/(row['id']+'.'+ext),folder/(row['id']+'.'+ext))
 for index,(k,s) in enumerate(new.items(),1):
  pid=f'L{index:03}';bedshape,bed=orient(s);assert solid_count(bedshape)==1
  fmt=helper.stl(folder/(pid+'.stl'),bedshape);print_io17.write_3mf(folder/(pid+'.3mf'),{pid:bedshape});ids[k]=pid
  rows.append({'id':pid,'instances':[{'character':'universal','part':k,'body':k[6:],'print_id':pid}],'quantity_by_character':{'universal':1},'stl':'print_batch/'+pid+'.stl','stl_sha256':g.sha(folder/(pid+'.stl')),'bed':bed,'stl_format':fmt,'geometry_source':'O19 free leg span; O18 joint ends retained','material_note':'Use the established joint process; O11 fit/friction accepted from user report. This new carrier has digital verification only.'})
  print('PRINT',pid,k,fmt,flush=True)
 count=sum(r['quantity_by_character']['universal'] for r in rows);assert count==188
 manifest.update(schema='POSEDOLL-O19-PRINT/1',status='LEG_ALIGNMENT_DESIGN_CANDIDATE',rows=rows,print_types=len(rows),print_pieces=count,source_snapshot='08e8f8b / O18',o11_coupon_user_test='PASS_REPORTED_2026-09-30')
 g.write(folder/'manifest.json',manifest)
 with (BENCH/'PRINT_UNIVERSAL.csv').open('w',newline='',encoding='utf-8-sig') as f:
  w=csv.writer(f);w.writerow(['print_id','quantity','file','parts'])
  for r in rows:w.writerow([r['id'],r['quantity_by_character']['universal'],r['stl'],'; '.join(i['part'] for i in r['instances'])])
 profile=g.read(BENCH/'profiles/device_profile.json');profile.update(schema='POSEDOLL-O19-DEVICE/1',profile_id='o19_usb_universal_v1');profile['source_geometry']={'revision':'O19','base':'O18 / O17 / O16 Quinn lineage','raw_joint_centres_unchanged':True,'changes_file':'verification/changes.json'};g.write(BENCH/'profiles/device_profile.json',profile)
 cal=g.read(BENCH/'profiles/calibration_INCOMPLETE.json');cal.update(schema='POSEDOLL-O19-CALIBRATION/1',profile_sha256=digest(profile));g.write(BENCH/'profiles/calibration_INCOMPLETE.json',cal)
 g.write(BENCH/'profiles/measurement_SYNTHETIC.json',{'status':'NO_O19_HARDWARE_CAPTURE','runtime_schema':'O17 measurement / P17R USB retained','o11_mechanical_fit_friction':'USER_REPORTED_PASS; separate from sensor calibration'})
 contract=g.read(BENCH/'target_adapter_contract.json');contract['schema']='POSEDOLL-O19-TARGET-CONTRACT/1'
 for t in contract['targets']:t['device_profile_id']='o19_usb_universal_v1';t['o19_live_adapter_implemented']=False;t['o19_capture_save_reopen_test']='NOT_RUN'
 contract['o19_note']='O19 only reroutes four leg beams; target orientation mapping and the physical kinematic tree remain unchanged.';g.write(BENCH/'target_adapter_contract.json',contract)
 viewer(new,ids,rows,count)
 g.write(OUT/'bom_comparison.json',{'O18_print_pieces':188,'O19_print_pieces':count,'O18_print_types':117,'O19_print_types':len(rows),'new_leg_carriers':4,'extra_friction_parts':0,'stock_parts_changed':0,'raw_channels':46,'semantic_dof':41})

def viewer(new,ids,rows,count):
 data=g.read(H/'tutorials/full-doll-o18/scene_universal.json');raw=np.frombuffer((H/'tutorials/full-doll-o18/geometry_universal.bin').read_bytes(),dtype='<f4').reshape(-1,6);arrays={k:raw[v['first']:v['first']+v['count']].copy() for k,v in data['meshes'].items()}
 def mesh(mid,s):
  tt=tri(s.simplify(.015)).astype(np.float32);nn=np.cross(tt[:,1]-tt[:,0],tt[:,2]-tt[:,0]);nn/=np.maximum(np.linalg.norm(nn,axis=1)[:,None],1e-30);arrays[mid]=np.concatenate([tt,np.repeat(nn[:,None,:],3,axis=1)],axis=2).reshape(-1,6)
 mids={};centers={}
 for i,(k,s) in enumerate(new.items()):mids[k]='O19_'+str(i);mesh(mids[k],s);centers[k]=np.array(mesh_record(s)['COM_mm'])
 data['scenes']=[s for s in data['scenes'] if not s['pose'].startswith('detail_')];oldneutral=copy.deepcopy(next(s for s in data['scenes'] if s['pose']=='neutral'));cases={'assembly':g.ASSEMBLY_POSE,**g.read(H/'mechanical_manifest/revO_pose_cases.json')['cases']}
 for scene in data['scenes']:
  for o in scene['objects']:
   if o['label'] in new:
    k=o['label'];M=np.array(o['matrix']).reshape(4,4);o.update(mesh=mids[k],print_id=ids[k],center=(M[:3,:3]@centers[k]+M[:3,3]).tolist())
  scene['reference_bones'],scene['physical_bones']=bones(cases[scene['pose']]);scene['caption']='O19 实际 CAD。蓝线为 UE Quinn 比例参考轴心，橙线为实体转轴中心；髋中心仍各外移16 mm。示例姿势保留已知整机干涉，不代表实物均可到达。'
 neutral=next(s for s in data['scenes'] if s['pose']=='neutral');objects=[];blue=[];orange=[]
 for label,scene,dy in [('O18',oldneutral,-90),('O19',neutral,90)]:
  for obj in scene['objects']:
   if obj['group'] not in ('leg_l','leg_r'):continue
   o=copy.deepcopy(obj);o['comparison_offset']=dy;o['label']=label+' / '+o['label'];o['group']='all';o['print_id']=None
   if label=='O18' and o['role']=='frame':o['color']=[.49,.51,.49]
   objects.append(o)
  bb,oo=bones({})
  for src,dst in ((bb,blue),(oo,orange)):
   for b in src:
    if not b['group'].startswith('leg_'):continue
    b=copy.deepcopy(b);b['comparison_offset']=dy;dst.append(b)
 compare={'pose':'detail_legs','label':'腿部对照 · 左 O18 / 右 O19','objects':objects,'reference_bones':blue,'physical_bones':orange,'view_center':[0,0,140],'view_radius':180,'view_yaw':-np.pi/2,'view_pitch':-np.pi/2,'caption':'左 O18，右 O19。大腿中间25 mm直段：左偏差约18.75→0 mm，右约21.51→6 mm；两小腿中间29 mm直段落在参考线上。端部转接仍有偏置，髋转轴各外移16 mm仍未解决。'}
 data['scenes'].insert(0,compare)
 # Actual Boolean intersection, rendered as an x-ray highlight; no artistic estimate.
 p,m,pr,st,prov=load_o18();pn,tr,_,_,_=position(p,m,{});a,b='frame/pelvis','frame/forearm_l';inter=pn[a]^pn[b];objects=[]
 for key,color in [(a,[.30,.45,.60]),(b,[.68,.57,.33])]:
  obj=copy.deepcopy(next(o for o in oldneutral['objects'] if o['label']==key));obj.update(color=color,group='all');objects.append(obj)
 mid='actual_collision';mesh(mid,inter);objects.append({'mesh':mid,'label':'两件实体的相交体积','role':'collision','color':[.88,.12,.10],'group':'all','print_id':None,'sku':None,'matrix':np.eye(4).ravel().tolist(),'center':mesh_record(inter)['COM_mm'],'explode':[0,0,0],'body':'detail'})
 data['scenes'].insert(1,{'pose':'detail_interference','label':'整机干涉示例 · 骨盆架 / 左前臂架','objects':objects,'reference_bones':[],'physical_bones':[],'view_center':mesh_record(inter)['COM_mm'],'view_radius':86,'view_yaw':-.7,'view_pitch':-1.2,'caption':f'蓝色骨盆架与棕色左前臂架在中立位相交，红色透视高亮是真实布尔相交体积约{inter.volume()/1000:.3f} cm³。实物会在此处碰住。这与 UE 角色蒙皮穿模无关；O19沿用了这两件，尚未解决此处干涉。'})
 used={o['mesh'] for s in data['scenes'] for o in s['objects']};blocks=[];meshindex={};offset=0
 for mid,arr in arrays.items():
  if mid not in used:continue
  meshindex[mid]={'first':offset,'count':len(arr)};offset+=len(arr);blocks.append(arr)
 data.update(meshes=meshindex,print_index=rows,status='O19 腿杆对齐优化 · O11配合与可调摩擦用户实测通过 · 整机仍有已知干涉')
 data['coverage']=['O18已保存：08e8f8b / posedoll-o18-prototype-20260930，旧包保持不变。','O11独立小样：用户于2026-09-30报告打印件、螺钉和垫片配合通过，拧紧可使长杆几乎不能转动；继续采用原摩擦方案，不增加摩擦冗余。','O19只重做4件腿部连接架的中间杆段，端部几何保留；仍为188件打印件、46路测量、41个语义旋转自由度。','24个姿势案例的新杆件增量检查无新增干涉；检查范围和插值路径结果见验证报告，不等同连续全域证明。','髋关节各向外16 mm的偏移仍在。已试算的零偏移布局在深蹲或外展发生碰撞，因此未采用。','蓝线来自独立UE参考模型，橙线来自实际模块有效轴心，均按当前示例角度求值；不再用连接杆外观代替关节中心。','整机干涉与目标角色蒙皮穿模是不同问题。前者限制实体摆姿，后者留给UE后期；原始传感器精度与UE端到端仍未实测。']
 g.write(PAGE/'scene_universal.json',data);(PAGE/'geometry_universal.bin').write_bytes(np.concatenate(blocks).astype('<f4').tobytes())
 app=(H/'tutorials/full-doll-o18/app.js').read_text(encoding='utf-8-sig').replace('revO18','revO19').replace('O18','O19').replace("'打印件 202 → '","'打印件 '")
 app=app.replace("yaw:-1.08,pitch:-1.28", "yaw:-Math.PI/2,pitch:-Math.PI/2")
 app=app.replace("if(o.role==='frame'?", "if(o.role!=='collision'&&(o.role==='frame'?").replace("!$('#electronics').checked)continue", "!$('#electronics').checked))continue")
 app=app.replace('gl.drawArrays(gl.TRIANGLES,mesh.first,mesh.count)', "if(o.role==='collision')gl.depthFunc(gl.ALWAYS);gl.drawArrays(gl.TRIANGLES,mesh.first,mesh.count);gl.depthFunc(gl.LESS)")
 start=app.index("if($('#reference').checked&&!state.part)");end=app.index("$('#caption').textContent",start)
 app=app[:start]+"for(const [id,bones,color] of [['reference',scene.reference_bones,[.13,.35,.88]],['physical',scene.physical_bones||[],[.91,.35,.05]]]){if($('#'+id).checked&&!state.part){const arr=[];for(const b of bones){if(state.group.startsWith('leg_')&&b.group!==state.group)continue;arr.push(...b.a,0,0,1,...b.b,0,0,1);for(const axis of [0,1,2]){const p=b.b.slice(),q=b.b.slice();p[axis]-=1.8;q[axis]+=1.8;arr.push(...p,0,0,1,...q,0,0,1)}}const lb=gl.createBuffer();gl.bindBuffer(gl.ARRAY_BUFFER,lb);gl.bufferData(gl.ARRAY_BUFFER,new Float32Array(arr),gl.STREAM_DRAW);bind(lb);gl.depthFunc(gl.ALWAYS);gl.uniformMatrix4fv(L.M,false,col(view));gl.uniform3fv(L.color,color);gl.drawArrays(gl.LINES,0,arr.length/6);gl.depthFunc(gl.LESS);gl.deleteBuffer(lb)}}"+app[end:]
 app=app.replace("['parts','frames','metal','electronics','reference']", "['parts','frames','metal','electronics','reference','physical']")
 app=app.replace("state.scene=Number(e.target.value);", "state.scene=Number(e.target.value);const chosen=data.scenes[state.scene];if(chosen.view_yaw!==undefined){state.yaw=chosen.view_yaw;state.pitch=chosen.view_pitch;}")
 app=app.replace("partOptions();window.O19_VIEWER", "$('#group').disabled=true;partOptions();window.O19_VIEWER")
 app=app.replace('col(mul(view,M))', 'col((()=>{const V=mul(view,M);V[3]+=o.comparison_offset||0;return V})())')
 app=app.replace('arr.push(...b.a,0,0,1,...b.b,0,0,1);', 'const warp=p=>[0,1,2].map(i=>view[i*4]*p[0]+view[i*4+1]*p[1]+view[i*4+2]*p[2]+view[i*4+3]+(i===0?(b.comparison_offset||0):0));arr.push(...warp(b.a),0,0,1,...warp(b.b),0,0,1);')
 app=app.replace('arr.push(...p,0,0,1,...q,0,0,1)', 'arr.push(...warp(p),0,0,1,...warp(q),0,0,1)').replace('col(view));gl.uniform3fv(L.color,color)', 'col(I()));gl.uniform3fv(L.color,color)')
 (PAGE/'app.js').write_text(app,encoding='utf-8');shutil.copy2(H/'tutorials/full-doll-o18/style.css',PAGE/'style.css')
 g.write(OUT/'viewer_geometry.json',{'status':'EXPORTED','actual_cad':True,'scenes':len(data['scenes']),'print_types':len(rows),'print_pieces':count,'independent_UE_reference':True,'physical_axis_centres_overlay':True,'collision_example_volume_mm3':float(inter.volume())})
if __name__=='__main__':main()
