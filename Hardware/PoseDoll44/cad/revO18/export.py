"""O18 manufacturing-review files and actual-CAD web viewer."""
from base import *
import copy,shutil,struct,csv,collections
from export_print_batch import orient,inspect
import print_io17
from device import digest
OLD=H/'bench/revO17';PAGE=H/'tutorials/full-doll-o18'

def stl(path,shape):
 full=tri(shape);tt=full.astype('<f4');normal=np.cross(tt[:,1]-tt[:,0],tt[:,2]-tt[:,0]);length=np.linalg.norm(normal.astype(float),axis=1)
 mask=length>0;tt=tt[mask];normal=normal[mask]/length[mask,None]
 # A float32 STL can collapse distinct near-coincident vertices. If its
 # topology is not closed, use standard ASCII STL with 17-digit coordinates.
 # Do not raise tolerances or discard nonzero faces to hide the failure.
 try:
  back=from_tri_exact(tt.astype(float));valid=solid_count(back)==1
  _,ix=np.unique(tt.reshape(-1,3),axis=0,return_inverse=True);ff=ix.reshape(-1,3)
  edges=np.concatenate([ff[:,[0,1]],ff[:,[1,2]],ff[:,[2,0]]]);_,counts=np.unique(np.sort(edges,axis=1),axis=0,return_counts=True)
  valid=valid and bool(np.all(counts==2))
 except ValueError:valid=False
 if valid:
  out=bytearray(b'PoseDoll O18 mm; prototype; test coupons before full assembly'.ljust(80,b' '));out+=struct.pack('<I',len(tt))
  for t,n in zip(tt,normal):out+=struct.pack('<12fH',*n,*t.ravel(),0)
  path.write_bytes(out);return 'BINARY_FLOAT32'
 with path.open('w',encoding='ascii',newline='\n') as f:
  f.write('solid PoseDoll_O18_mm\n')
  for t in full:
   n=np.cross(t[1]-t[0],t[2]-t[0]);n/=max(np.linalg.norm(n),1e-30)
   f.write('facet normal '+' '.join(format(float(v),'.17g') for v in n)+'\nouter loop\n')
   for vertex in t:f.write('vertex '+' '.join(format(float(v),'.17g') for v in vertex)+'\n')
   f.write('endloop\nendfacet\n')
  f.write('endsolid PoseDoll_O18_mm\n')
 return 'ASCII_FLOAT64'

def main():
 changes=g.read(OUT/'changes.json');p,m,pr,states,prov=load_o17()
 new={k:from_tri_exact(v).simplify(1e-4) for k,v in np.load(OUT/'changed_parts.npz').items()}
 removed={k for r in changes['replacements'] for k in r['replaces']}|set(changes['removed_stock_parts'])
 rows=[];print_ids={};folder=BENCH/'print_batch';folder.mkdir(parents=True,exist_ok=True)
 for oldrow in g.read(OLD/'print_batch/manifest.json')['rows']:
  row=copy.deepcopy(oldrow);instances=[i for i in row['instances'] if i['part'] not in removed]
  if not instances:continue
  row['instances']=instances;row['quantity_by_character']={'universal':len(instances)};row['geometry_source']='O17 unchanged';rows.append(row)
  for i in instances:print_ids[i['part']]=row['id']
  for ext in ('stl','3mf'):shutil.copy2(OLD/'print_batch'/(row['id']+'.'+ext),folder/(row['id']+'.'+ext))
 for index,(k,s) in enumerate(new.items(),1):
  pid=f'H{index:03}';bedshape,bed=orient(s);bedshape=bedshape.simplify(1e-4)
  assert solid_count(bedshape)==1
  stl_format=stl(folder/(pid+'.stl'),bedshape);print_io17.write_3mf(folder/(pid+'.3mf'),{pid:bedshape})
  rows.append({'id':pid,'instances':[{'character':'universal','part':k,'body':m[k]['body'],'print_id':pid}],
   'quantity_by_character':{'universal':1},'stl':'print_batch/'+pid+'.stl','stl_sha256':g.sha(folder/(pid+'.stl')),
   'bed':bed,'stl_format':stl_format,'geometry_source':'O18 one-piece carrier','material_note':'PETG prototype; qualify washer reaction roof, side-loading openings and layer direction with Q001 coupon.'})
  print_ids[k]=pid;print('PRINT',pid,k,flush=True)
 count=sum(r['quantity_by_character']['universal'] for r in rows);assert count==188
 expected={r['id']+'.'+ext for r in rows for ext in ('stl','3mf')}
 assert folder.resolve().is_relative_to((H/'bench/revO18').resolve())
 for oldfile in folder.iterdir():
  if oldfile.suffix in ('.stl','.3mf') and oldfile.name not in expected:oldfile.unlink()
 g.write(folder/'manifest.json',{'schema':'POSEDOLL-O18-PRINT/1','status':'DIGITAL_CANDIDATE_COUPON_FIRST','units':'mm','hardware_model':'universal',
  'rows':rows,'print_types':len(rows),'print_pieces':count,'physical_tested':False,'coupon_excluded_from_assembly_count':True,'source_snapshot':'5a5ac22 / O17'})
 with (BENCH/'PRINT_UNIVERSAL.csv').open('w',newline='',encoding='utf-8-sig') as f:
  w=csv.writer(f);w.writerow(['print_id','quantity','supports_required','file','parts'])
  for r in rows:w.writerow([r['id'],r['quantity_by_character']['universal'],r['bed']['supports_required'],r['stl'],'; '.join(i['part'] for i in r['instances'])])
 q=from_tri_exact(np.load(OUT/'coupon.npz')['Q001']);qbed,bed=orient(q);qbed=qbed.simplify(1e-4)
 cf=BENCH/'coupon';cf.mkdir(exist_ok=True);stl(cf/'Q001.stl',qbed);print_io17.write_3mf(cf/'Q001.3mf',{'Q001':qbed})
 from layout_fullbody import libraries
 rotor=from_tri_exact(np.load(H/'generated/revO15/runs/o15_20260929_r1/hinge_parts.npz')['lever_cup']) ^ box([-50,-50,-50],[14,50,50])
 assert rotor.status()==md.Error.NoError and 3000<rotor.volume()<3100,(rotor.status(),rotor.volume(),rotor.bounding_box())
 shift=-np.array(rotor.bounding_box())[:3]+[8,8,0];rotorbed=rotor.translate(shift);rotorinfo=inspect(rotorbed)
 assert rotorinfo['flat_contact_area_mm2']>1 and rotorinfo['COM_over_model_contact_hull']
 rotorinfo.update(rotation=np.eye(3).tolist(),translation_mm=shift.tolist(),supports_required=True,orientation_scope='Known flat underside; support and layer strength need slicer/coupon review')
 stl(cf/'Q002.stl',rotorbed);print_io17.write_3mf(cf/'Q002.3mf',{'Q002':rotorbed})
 g.write(cf/'Q002.json',{'id':'Q002','quantity':1,'part':'Matching hinge rotor for Q001 coupon','included_in_full_doll_count':False,'bed':rotorinfo,'stl_sha256':g.sha(cf/'Q002.stl')})
 g.write(cf/'manifest.json',{'id':'Q001','quantity':1,'part':'Detached one-piece hinge parent housing','included_in_full_doll_count':False,'bed':bed,'stl_sha256':g.sha(cf/'Q001.stl'),'physical_tested':False})
 # Each integrated housing removes two M3x20 bolts and two M3 nuts.
 delta=collections.Counter(m[k]['sku'] for k in changes['removed_stock_parts']);assert delta=={'SCREW_M3_L20':28,'NUT_M3':28}
 proc=g.read(OLD/'procurement.json');proc['status']='O18_HOUSING_SIMPLIFICATION_PROTOTYPE';newrows=[]
 for row in proc['characters'][0]['rows']:
  row['net_quantity']-=delta[row['sku']];assert row['net_quantity']>=0
  if not row['net_quantity']:continue
  row['optional_spares']=min(row['optional_spares'],int(np.ceil(row['net_quantity']*.1)));row['suggested_total']=row['net_quantity']+row['optional_spares'];newrows.append(row)
 proc['characters'][0]['rows']=newrows;g.write(BENCH/'procurement.json',proc)
 g.write(OUT/'bom_comparison.json',{'O16_print_pieces':273,'O17_print_pieces':202,'O18_print_pieces':count,'O17_print_types':124,'O18_print_types':len(rows),
  'printed_pieces_removed':14,'removed_stock_quantities':dict(delta),'total_individual_items_removed_vs_O17':70,
  'print_reduction_vs_O17_percent':14/202*100,'print_reduction_vs_O16_percent':(273-count)/273*100,
  'raw_channels_before':46,'raw_channels_after':46,'semantic_dof_before':41,'semantic_dof_after':41,
  'joint_preload_hardware_removed':0,'sensor_or_magnet_mount_removed':0,'optional_coupon_pieces':2})
 for name in ('profiles','harness'):shutil.copytree(OLD/name,BENCH/name,dirs_exist_ok=True)
 profile=g.read(BENCH/'profiles/device_profile.json');profile['schema']='POSEDOLL-O18-DEVICE/1';profile['profile_id']='o18_usb_universal_v1'
 profile['source_geometry']={'revision':'O18','base':'O17 / O16 Quinn lineage','raw_joint_centres_unchanged':True,'changes_file':'verification/changes.json'}
 g.write(BENCH/'profiles/device_profile.json',profile)
 cal=g.read(BENCH/'profiles/calibration_INCOMPLETE.json');cal['schema']='POSEDOLL-O18-CALIBRATION/1';cal['profile_sha256']=digest(profile);g.write(BENCH/'profiles/calibration_INCOMPLETE.json',cal)
 g.write(BENCH/'profiles/measurement_SYNTHETIC.json',{'status':'NO_O18_HARDWARE_CAPTURE','runtime_schema':'O17 measurement / P17R USB retained','note':'Recalibrate physical O18; no previous hardware calibration is asserted valid.'})
 contract=g.read(OLD/'target_adapter_contract.json');contract['schema']='POSEDOLL-O18-TARGET-CONTRACT/1'
 for target in contract['targets']:
  target['device_profile_id']='o18_usb_universal_v1';target['o18_live_adapter_implemented']=False;target['o18_capture_save_reopen_test']='NOT_RUN'
 contract['o18_note']='O18 housing changes preserve the O17 kinematics and P17R protocol; production UE target adapters remain unverified.'
 g.write(BENCH/'target_adapter_contract.json',contract)
 # The kinematics and wire protocol did not change. Keep the validated runtime
 # byte-identical, including its versioned measurement schema and P17R protocol.
 source=BENCH/'source';source.mkdir(exist_ok=True)
 for name in ('device.py','usb_capture.py','test_device.py','test_usb.py','codec_fixture.bin'):shutil.copy2(OLD/'source'/name,source/name)
 page_export(changes,new,removed,print_ids,rows,count)
 print('O18',len(rows),'print types;',count,'pieces; 56 fasteners removed',flush=True)

def page_export(changes,new,removed,print_ids,rows,count):
 PAGE.mkdir(parents=True,exist_ok=True)
 data=g.read(H/'tutorials/full-doll-o17/scene_universal.json');oldraw=np.frombuffer((H/'tutorials/full-doll-o17/geometry_universal.bin').read_bytes(),dtype='<f4').reshape(-1,6)
 arrays={k:oldraw[v['first']:v['first']+v['count']].copy() for k,v in data['meshes'].items()}
 centers={};mesh_ids={}
 def mesh(mid,s):
  tt=tri(s.simplify(.015)).astype(np.float32);nn=np.cross(tt[:,1]-tt[:,0],tt[:,2]-tt[:,0]);nn/=np.maximum(np.linalg.norm(nn,axis=1)[:,None],1e-30)
  arrays[mid]=np.concatenate([tt,np.repeat(nn[:,None,:],3,axis=1)],axis=2).reshape(-1,6)
 for i,(k,s) in enumerate(new.items()):
  mid='O18_'+str(i);mesh(mid,s);mesh_ids[k]=mid;centers[k]=np.array(mesh_record(s)['COM_mm'])
 data['scenes']=[s for s in data['scenes'] if not s['pose'].startswith('detail_')]
 for scene in data['scenes']:
  orig={o['label']:o for o in scene['objects']};objects=[o for o in scene['objects'] if o['label'] not in removed]
  for k,s in new.items():
   o=copy.deepcopy(orig[k]);A=np.asarray(o['matrix']).reshape(4,4);o['mesh']=mesh_ids[k];o['print_id']=print_ids[k];o['center']=(A[:3,:3]@centers[k]+A[:3,3]).tolist();objects.append(o)
  scene['objects']=objects;scene['caption']='O18实际CAD：14处单轴关节外壳并入连接架，去掉56件壳体紧固件。姿势示意仍有已知干涉，不能据此判定实物可达。'
 # Focused comparison includes the four removed fasteners in the O17 assembly.
 p,m,pr,states,prov=load_o17();state=next(s for s in states if s['id']=='hand_l.deviate');key=state['id']+'/base_service_half';frame='frame/'+state['parent'];A=m[key]['transform'];I=np.linalg.inv(A)
 objects=[]
 def obj(mid,label,shape,offset,role='print',pid=None,color=None):
  mesh(mid,shape);M=g.homogeneous(np.eye(3),offset)
  objects.append({'mesh':mid,'label':label,'role':role,'color':color or [.42,.63,.49],'group':'all','print_id':pid,'sku':None,
   'matrix':M.ravel().tolist(),'center':(np.array(mesh_record(shape)['COM_mm'])+offset).tolist(),'explode':[0,0,0],'body':'detail'})
 obj('detail_old_frame','O17 / carrier',g.move(p[frame],I),[-50,0,0])
 obj('detail_old_half','O17 / removable half',g.move(p[key],I),[-50,18,0])
 for i,suffix in enumerate(('case_screw_0','case_screw_1','case_nut_0','case_nut_1')):
  obj('detail_old_hardware_'+str(i),'O17 / '+suffix,g.move(p[state['id']+'/'+suffix],I),[-50,0,-12],'metal',color=[.67,.7,.71])
 shape=g.move(new[frame],I@m[frame]['transform'])
 obj('detail_new','O18 / one-piece carrier',shape,[50,0,0],pid=print_ids[frame],color=[.28,.42,.57])
 data['scenes'].append({'pose':'detail_housing','label':'外壳合一 · O17 / O18对照','objects':objects,'reference_bones':[],'view_center':[0,0,8],'view_radius':100,
  'caption':'左：O17两件外壳和4件壳体紧固件；右：O18一件连续承力架。测量轴、预紧螺栓、传感器和磁铁均保留。'})
 # Actual coupon with insertion path positions; no invented deformation.
 from layout_fullbody import libraries
 lib,_,_=libraries()['hinge'];coupon=from_tri_exact(np.load(OUT/'coupon.npz')['Q001']);objects=[]
 obj('coupon','O18 / Q001 coupon',coupon,[0,0,0],pid='Q001',color=[.28,.42,.57])
 obj('nut_entry','M3 nut before side insertion',lib['M3_nut'],[0,18,0],'metal',color=[.67,.7,.71])
 obj('washer_entry','M3 reaction washer before side insertion',lib['M3_reaction_washer'],[0,31,0],'metal',color=[.67,.7,.71])
 data['scenes'].append({'pose':'detail_access','label':'Q001小样 · 螺母与垫片侧装','objects':objects,'reference_bones':[],'view_center':[0,8,4],'view_radius':48,
  'caption':'先向通道内侧推入M3螺母和反力垫片，再安装转臂、肩螺栓、预紧件、磁铁总成与传感板。先做裸连接架装配；Q001只用于工艺试验，不计入188件整机数量。'})
 used={o['mesh'] for scene in data['scenes'] for o in scene['objects']};meshes={};blocks=[];offset=0
 for mid,arr in arrays.items():
  if mid not in used:continue
  meshes[mid]={'first':offset,'count':len(arr)};offset+=len(arr);blocks.append(arr)
 data['meshes']=meshes;data['print_index']=rows
 data['status']='O18 结构简化候选 · 188件打印件 · 整机仍有已知干涉，先做Q001小样'
 data['coverage']=['O17已冻结：5a5ac22 / posedoll-o17-prototype-20260930；349文件和ZIP校验通过。',
  '14处单轴外壳合一，打印件202→188；去掉28枚M3×20螺钉和28枚M3螺母。',
  '14处螺母与垫片侧装通道逐一检查；原垫片反力面保留。强度、打印配合与保持力仍待实测。',
  '46路测量、41个语义旋转自由度、原轴线与参考姿态均保留；P17R USB固件沿用O17。',
  '整机干涉未消除：直接削除骨盆碰撞区会将骨盆架切为6个分离实体，该方案未采用。',
  '24姿势的增量回归只检查本轮改变的承力架；不能代替全域含线束避碰检查。',
  '无外部摄像头；根部与手指未测量。目标接触和穿模交给UE后期；Manny/Quinn端到端尚未实测。']
 g.write(PAGE/'scene_universal.json',data);(PAGE/'geometry_universal.bin').write_bytes(np.concatenate(blocks).astype('<f4').tobytes())
 app=(H/'tutorials/full-doll-o17/app.js').read_text(encoding='utf-8-sig').replace('revO17','revO18').replace('O17','O18').replace("'打印件 273 → '","'打印件 202 → '")
 app=app.replace("o.print_id+' / '+labelZh(o.label)+' · 下表可下载'","o.print_id+' / '+labelZh(o.label)+(o.print_id==='Q001'?' · 页面小样链接下载':' · 下表可下载')")
 (PAGE/'app.js').write_text(app,encoding='utf-8');shutil.copy2(H/'tutorials/full-doll-o17/style.css',PAGE/'style.css')
 html=(H/'tutorials/full-doll-o17/index.html').read_text(encoding='utf-8-sig').replace('revO17','revO18').replace('REVO17','REVO18').replace('O17','O18')
 html=html.replace('202 件','188 件').replace('124种打印件',str(len(rows))+'种打印件')
 html=html.replace('68组零件合并，装配通道保留。','14处外壳合一，再少70个零件。')
 html=html.replace('O16已保存。O18将传感板托夹与磁铁座盖分别合一，移除电池和桌面网关。保留所有关节中心、传感器位置和46路测量，以USB直接采集。','O17已冻结。O18把14处单轴关节的可拆半壳并入连接架，螺母和垫片改为侧装。少14件打印件、28枚螺钉和28枚螺母，保留原测量轴和预紧机构。')
 html=html.replace('N编号为O18新件，P编号为沿用件。先打印小样验证卡扣和磁铁座，再决定整机加工。','H编号为O18新连接架，N和P编号沿用O17。Q001为独立装配试验小样，不计入整机数量。先验证侧装通道、垫片承力面与预紧保持，再决定整机加工。')
 html=html.replace('68组实际CAD合并','14处单轴外壳合一')
 html=html.replace('本轮检查一体件可打印实体、装配通道、外形包含关系、保留的机械FK、USB协议与查看器。','本轮检查13件新承力架、14处侧装通道、垫片反力面、24姿势增量碰撞及原测量链兼容。')
 html=html.replace('<span id="stats"></span>','<a href="../../bench/revO18/coupon/Q001.stl" download>Q001外壳小样 STL</a><a href="../../bench/revO18/coupon/Q001.3mf" download>3MF</a><a href="../../bench/revO18/coupon/Q002.stl" download>Q002配套转臂 STL</a><span id="stats"></span>')
 (PAGE/'index.html').write_text(html,encoding='utf-8')
 g.write(OUT/'viewer_geometry.json',{'status':'EXPORTED','actual_cad':True,'scenes':len(data['scenes']),'parts_per_full_scene':len(data['scenes'][0]['objects']),'print_types':len(rows),'print_pieces':count})

if __name__=='__main__':main()
