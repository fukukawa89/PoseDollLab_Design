"""O20 manufacture meshes, inherited measurement chain, actual CAD viewer."""
from base import *
import copy,shutil,csv,importlib.util,collections
from export_print_batch import orient
import print_io17,print_io20
from device import digest
OLD=H/'bench/revO19';PAGE=H/'tutorials/full-doll-o20'

def legacy():
 spec=importlib.util.spec_from_file_location('o19_export_readonly',H/'cad/revO19/export.py');mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod);return mod

def main():
 BENCH.mkdir(parents=True,exist_ok=True);PAGE.mkdir(parents=True,exist_ok=True);changes=g.read(OUT/'changes.json');new={k:from_tri_exact(v) for k,v in np.load(OUT/'changed_parts.npz').items()}
 p,m,pr,st,prov=load_o19();gone=set(changes['removed_stock_parts'])|{k for r in changes['replacements'] for k in r['replaces']}
 for name in ('profiles','harness','source','electronics','firmware_source','firmware_binaries'):shutil.copytree(OLD/name,BENCH/name,dirs_exist_ok=True)
 for name in ('POWER_AND_USB.zh-CN.md','requirements-reference.txt','serve_preview.py','target_adapter_contract.json'):shutil.copy2(OLD/name,BENCH/name)
 delta=collections.Counter(m[k]['sku'] for k in changes['removed_stock_parts']);assert delta=={'SCREW_M3_L20':4,'NUT_M3':4}
 proc=g.read(OLD/'procurement.json');rows=[]
 for r in proc['characters'][0]['rows']:
  r['net_quantity']-=delta[r['sku']]
  if r['net_quantity']==0:continue
  r['optional_spares']=min(r['optional_spares'],int(np.ceil(r['net_quantity']*.1)));r['suggested_total']=r['net_quantity']+r['optional_spares'];rows.append(r)
 proc['characters'][0]['rows']=rows;proc['status']='O20_LIGHTWEIGHT_SINGLE_DOLL';g.write(BENCH/'procurement.json',proc)
 manifest=g.read(OLD/'print_batch/manifest.json');rows=[];ids={};folder=BENCH/'print_batch';folder.mkdir(exist_ok=True);helper=print_io20
 for row in manifest['rows']:
  row=copy.deepcopy(row);row['instances']=[i for i in row['instances'] if i['part'] not in gone]
  if not row['instances']:continue
  row['quantity_by_character']={'universal':len(row['instances'])};rows.append(row)
  for i in row['instances']:ids[i['part']]=row['id']
  for ext in ('stl','3mf'):shutil.copy2(OLD/'print_batch'/(row['id']+'.'+ext),folder/(row['id']+'.'+ext))
 for index,(k,s) in enumerate(new.items(),1):
  pid=f'W{index:03}';source=s.simplify(1e-10) if k.startswith('frame/foot_') else s;bedshape,bed=orient(source);assert solid_count(bedshape)==1
  if k.startswith('frame/foot_'):bed['mesh_precision_cleanup_mm']=1e-10;bed['cleanup_volume_delta_mm3']=abs(float(source.volume()-s.volume()))
  fmt=helper.stl(folder/(pid+'.stl'),bedshape);print_io17.write_3mf(folder/(pid+'.3mf'),{pid:bedshape});ids[k]=pid
  rows.append({'id':pid,'instances':[{'character':'universal','part':k,'body':m[k]['body'],'print_id':pid}],'quantity_by_character':{'universal':1},'stl':'print_batch/'+pid+'.stl','stl_sha256':g.sha(folder/(pid+'.stl')),'bed':bed,'stl_format':fmt,'geometry_source':'O20 / O19 baseline','material_note':'Preserve established joint process. Capped 4/5 mm core cavities require slicer bridge review; do not generate inaccessible cavity supports. New carrier stiffness not physically measured.'})
  print('PRINT',pid,k,fmt,flush=True)
 count=sum(r['quantity_by_character']['universal'] for r in rows);assert count==186
 manifest.update(schema='POSEDOLL-O20-PRINT/1',status='LIGHTWEIGHT_DIGITAL_CANDIDATE',rows=rows,print_types=len(rows),print_pieces=count,source_snapshot='98c084a / O19',on_doll_print_pieces=185,assembly_fixture_pieces=1,o11_coupon_user_test='PASS_REPORTED_2026-09-30')
 g.write(folder/'manifest.json',manifest)
 with (BENCH/'PRINT_UNIVERSAL.csv').open('w',newline='',encoding='utf-8-sig') as f:
  w=csv.writer(f);w.writerow(['print_id','quantity','file','parts'])
  for r in rows:w.writerow([r['id'],r['quantity_by_character']['universal'],r['stl'],'; '.join(i['part'] for i in r['instances'])])
 profile=g.read(BENCH/'profiles/device_profile.json');profile.update(schema='POSEDOLL-O20-DEVICE/1',profile_id='o20_usb_universal_v1');profile['source_geometry']={'revision':'O20','base':'O19','raw_joint_centres_unchanged':True,'changes_file':'verification/changes.json'};g.write(BENCH/'profiles/device_profile.json',profile)
 cal=g.read(BENCH/'profiles/calibration_INCOMPLETE.json');cal.update(schema='POSEDOLL-O20-CALIBRATION/1',profile_sha256=digest(profile));g.write(BENCH/'profiles/calibration_INCOMPLETE.json',cal)
 g.write(BENCH/'profiles/measurement_SYNTHETIC.json',{'status':'NO_O20_HARDWARE_CAPTURE','runtime_schema':'O17 measurement / P17R USB retained','o11_mechanical_fit_friction':'USER_REPORTED_PASS; distinct from sensor calibration'})
 contract=g.read(BENCH/'target_adapter_contract.json');contract['schema']='POSEDOLL-O20-TARGET-CONTRACT/1'
 for t in contract['targets']:t['device_profile_id']='o20_usb_universal_v1';t['o20_live_adapter_implemented']=False;t['o20_capture_save_reopen_test']='NOT_RUN'
 contract['o20_note']='Printed material and fixed fasteners reduced. Measurement axes, kinematics and orientation conversion unchanged.';g.write(BENCH/'target_adapter_contract.json',contract)
 g.write(OUT/'bom_comparison.json',{'O19_print_pieces':188,'O20_print_pieces':count,'O19_print_types':117,'O20_print_types':len(rows),'on_doll_prints_before':187,'on_doll_prints_after':185,'assembly_fixture_pieces':1,'replaced_prints':len(new),'removed_stock_quantities':dict(delta),'total_individual_items_removed':10,'extra_friction_parts':0,'raw_channels':46,'semantic_dof':41})
 viewer(new,ids,rows,count,changes,p,m,pr)

def viewer(new,ids,rows,count,changes,p,m,pr):
 data=g.read(H/'tutorials/full-doll-o19/scene_universal.json');raw=np.frombuffer((H/'tutorials/full-doll-o19/geometry_universal.bin').read_bytes(),dtype='<f4').reshape(-1,6);arrays={k:raw[v['first']:v['first']+v['count']].copy() for k,v in data['meshes'].items()}
 def mesh(mid,s):
  tt=tri(s.simplify(.012)).astype(np.float32);nn=np.cross(tt[:,1]-tt[:,0],tt[:,2]-tt[:,0]);nn/=np.maximum(np.linalg.norm(nn,axis=1)[:,None],1e-30);arrays[mid]=np.concatenate([tt,np.repeat(nn[:,None,:],3,axis=1)],axis=2).reshape(-1,6)
 mids={};centers={}
 for i,(k,s) in enumerate(new.items()):mids[k]='O20_'+str(i);mesh(mids[k],s);centers[k]=np.array(mesh_record(s)['COM_mm'])
 data['scenes']=[s for s in data['scenes'] if not s['pose'].startswith('detail_')];original=copy.deepcopy(data['scenes']);removed=set(changes['removed_stock_parts'])|{k for r in changes['replacements'] for k in r['replaces'] if k!=r['part']}
 for scene in data['scenes']:
  scene['objects']=[o for o in scene['objects'] if o['label'] not in removed]
  for o in scene['objects']:
   if o['label'] in new:
    k=o['label'];M=np.array(o['matrix']).reshape(4,4);o.update(mesh=mids[k],print_id=ids[k],center=(M[:3,:3]@centers[k]+M[:3,3]).tolist())
  scene['caption']='O20实际CAD：保留O19腿杆走向与双髋各16 mm外移；该髋布局已接受。远端肢体接触可调整姿势避让。蓝线为UE参考，橙线为实体轴心。'
 # Start with a physically clear spread pose, not a neutral pose with remote hand contact.
 data['scenes'].sort(key=lambda s:s['pose']!='assembly')
 # Comparison objects are from actual CAD; no display simplification goes to print.
 def obj(mid,s,label,offset,color):
  mesh(mid,s);return {'mesh':mid,'label':label,'role':'frame','group':'all','print_id':None,'sku':None,'matrix':np.eye(4).ravel().tolist(),'center':mesh_record(s)['COM_mm'],'explode':[0,0,0],'body':'detail','comparison_offset':offset,'color':color}
 old0,tr,_,_,_=position(p,m,{});key='frame/calf_l';now0=g.move(new[key],tr[key]);x=.7164961230918814;cut=box([-1000,-1000,-1000],[x,1000,1000]);objects=[]
 for label,shape,dx,col in [('O19',old0[key],-30,[.50,.52,.50]),('O20',now0,30,[.28,.48,.64])]:objects.append(obj('core_'+label,shape^cut,label+' / 左小腿剖切',dx,col))
 data['scenes'].insert(1,{'pose':'detail_core','label':'空心杆剖切 · 左 O19 / 右 O20','objects':objects,'reference_bones':[],'physical_bones':[],'view_center':[x,29.5,88],'view_radius':87,'view_yaw':-np.pi/2,'view_pitch':-np.pi/2,'caption':'实际CAD剖切：左为O19实心杆，右为O20封闭空心杆。10 mm外径、5 mm芯孔，端部与弯头保留。剖切仅为展示；打印文件是完整单件，不增加拼缝。'})
 oldscene=next(s for s in original if s['pose']=='assembly');newscene=next(s for s in data['scenes'] if s['pose']=='assembly');objects=[]
 for label,sc,dx in [('O19',oldscene,-65),('O20',newscene,65)]:
  for ob in sc['objects']:
   if ob['label']!='frame/foot_l' and not ob['label'].startswith('ball_l.flex/'):continue
   ob=copy.deepcopy(ob);ob.update(comparison_offset=dx,group='all',print_id=None,label=label+' / '+ob['label']);objects.append(ob)
 c=np.array(p['frame/foot_l'].bounding_box()).reshape(2,3).mean(0)
 data['scenes'].insert(2,{'pose':'detail_toe','label':'脚趾外壳合并 · 左 O19 / 右 O20','objects':objects,'reference_bones':[],'physical_bones':[],'view_center':c.tolist(),'view_radius':110,'view_yaw':-.95,'view_pitch':-1.05,'caption':'每侧脚趾关节：两片固定外壳改成一体侧装结构，减少1件打印件、2颗M3×20螺钉、2个M3螺母。肩轴螺栓、摩擦垫片、编码器与转轴位置全部保留。先装侧向螺母和垫片，再装转动件。'})
 key='accessory/chest/controller_lid';entry=next(x for x in g.read(H/'generated/revO15/runs/o15_20260929_r1/equipment/quinn_search.json')['entries'] if x['kind']=='controller');F=np.c_[[0,1,0],[0,0,-1],[-1,0,0]];E=g.homogeneous(F,np.array(entry['front_center_world_mm'])-F@np.array([35,30,0]));objects=[]
 for label,s,dx,col in [('O19',p[key],-46,[.50,.52,.50]),('O20',g.move(new[key],m[key]['transform']),46,[.28,.48,.64])]:objects.append(obj('lid_'+label,g.move(s,np.linalg.inv(E)),label+' / 控制盒盖',dx,col))
 data['scenes'].insert(3,{'pose':'detail_lid','label':'控制盒盖减重 · 左 O19 / 右 O20','objects':objects,'reference_bones':[],'physical_bones':[],'view_center':[35,30,23],'view_radius':96,'view_yaw':0,'view_pitch':0,'caption':'保留外圈、四角固定孔、降压板支柱；O20增加28个直径7 mm圆孔。盒底另有12个9 mm减重孔，避开PCB支柱与骨架连接处。电子元件、USB与线束端点不变。'})
 used={o['mesh'] for s in data['scenes'] for o in s['objects']};blocks=[];mi={};offset=0
 for mid,arr in arrays.items():
  if mid not in used:continue
  mi[mid]={'first':offset,'count':len(arr)};offset+=len(arr);blocks.append(arr)
 data.update(meshes=mi,print_index=rows,status='O20 轻量化 · 减少2件打印件及8件五金 · 已接受髋布局与远端姿势避碰')
 data['coverage']=['O19已保存：98c084a / posedoll-o19-leg-alignment-20260930；本轮另存为O20。','保留单台USB测姿、46路原始轴、41个语义旋转自由度、约492 mm中立高度。','打印清单186件=185件装在人偶上+1件XIAO焊接间距治具；与O19同口径减少2件。','用户已验证O11尺寸配合与可调摩擦；不增加摩擦冗余。新外壳侧装路径与受压面做数字复核。','双髋各外移16 mm已按用户决定保留；远端肢体接触记录为姿势避让条件。相邻机构仍检查干涉。','模型减去约16.8 cm³打印实体；质量换算是实心材料当量，实际减重以相同切片设置和称重为准。','新空心杆保留原外轮廓，芯孔最大5 mm。切片时查看孔顶桥接，不生成无法取出的内支撑。','减重不能证明传感精度或打印刚度。原始标定、实物加载变形和UE端到端采集仍需实测；不重复要求O11摩擦原理测试。']
 g.write(PAGE/'scene_universal.json',data);(PAGE/'geometry_universal.bin').write_bytes(np.concatenate(blocks).astype('<f4').tobytes())
 app=(H/'tutorials/full-doll-o19/app.js').read_text('utf-8-sig').replace('revO19','revO20').replace('O19','O20').replace("$('#group').disabled=true;partOptions();", "$('#group').disabled=false;partOptions();")
 app=app.replace('if(chosen.view_yaw!==undefined){state.yaw=chosen.view_yaw;state.pitch=chosen.view_pitch;}','state.yaw=chosen.view_yaw??-Math.PI/2;state.pitch=chosen.view_pitch??-Math.PI/2;')
 (PAGE/'app.js').write_text(app,encoding='utf-8');shutil.copy2(H/'tutorials/full-doll-o19/style.css',PAGE/'style.css')
 g.write(OUT/'viewer_geometry.json',{'status':'EXPORTED','actual_cad':True,'scenes':len(data['scenes']),'print_types':len(rows),'print_pieces':count,'cutaway_is_visual_only':True,'independent_UE_reference':True,'physical_axis_centres_overlay':True})
if __name__=='__main__':main()
