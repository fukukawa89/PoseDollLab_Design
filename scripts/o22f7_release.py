"""Release and zip only after the final geometry, function and native-path gates."""
from pathlib import Path
import json,copy,shutil,hashlib,zipfile,sys,re,html,urllib.parse
import numpy as np
from shapely.geometry import LineString
import o22f7 as r
from o22f6_final_package import LOCATIONS,CSS
h=r.h

def write(p,s):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(s,encoding='utf8')
def page(title,content):return '<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><link rel="icon" href="data:,"><title>'+title+'</title><style>'+CSS+'</style><p><a href="index.html">实际网格与拆撑</a> · <a href="合盘布局.html">合盘布局</a> · <a href="打印与拆撑.html">打印说明</a> · <a href="检查与例外.html">检查记录</a></p>'+content+'</html>'
def edge_review():
 from o22_f3_gcode import extract_detailed
 from o22_cross_section_geometry import polygon
 rows=[]
 for p in r.manifest()['plates']:
  pid=p['id'];rep=r.read(r.WORK/f'plates/{pid}/deposited_retained_clearance.json');assert rep['project_sha256']==h.sha(r.OUT/f'projects/{pid}_O22F7_PLA_final.3mf')
  if not rep['flagged_layers']:continue
  _,raw,*_=extract_detailed(r.BASE/p['project'],arc_tolerance_mm=.02,max_arc_segment_mm=.6);a=np.asarray(raw).reshape(-1,9)
  for flag in rep['flagged_layers']:
   assert flag['segment_count']==len(flag['segments'])==6 and abs(flag['z_mm']-15.4)<.001
   xy=np.mean([q['xy']for q in flag['segments']],axis=(0,1));owners=[it for it in p['items']if it['bounds_mm'][0]<=xy[0]<=it['bounds_mm'][3]and it['bounds_mm'][1]<=xy[1]<=it['bounds_mm'][4]];assert len(owners)==1;it=owners[0];assert(pid,it['id'])in[('D05','P018'),('D11','P002')]
   n=np.load(r.OUT/f"parts/{it['id']}.npz");body=h.solid(n['v'],n['f']);support=h.solid(n['fin_v'],n['fin_f'])+h.solid(n['teeth_v'],n['teeth_f']);M=np.array(it['rotation_matrix']);t=np.array(it['translation_mm']);z=flag['z_mm'];bp=polygon(body.slice(z-p['profile']['layer']/2));sp=polygon(support.slice(z-p['profile']['layer']/2));matches=[];ds=[];db=[]
   for q in flag['segments']:
    pts=(np.c_[q['xy'],[z,z]]-t)@M;line=LineString(pts[:,:2]);ds.append(line.distance(sp));db.append(line.distance(bp));samez=a[(abs(a[:,5]-z)<.001)&(a[:,7]==0)];near=np.flatnonzero(np.max(abs(samez[:,[0,1,3,4]]-np.array(q['xy']).reshape(-1)),axis=1)<.002);matches.append(bool(len(near)and abs(samez[near[0],8]-q['width_mm'])<.002))
   assert all(matches)and min(ds)>.5 and max(db)<1e-5,(pid,matches,ds,db)
   rows.append(dict(plate=pid,id=it['id'],project_sha256=rep['project_sha256'],raw_flag=flag,all_paths_identical_to_released_F6=True,minimum_distance_to_support_mm=min(ds),maximum_distance_to_body_mm=max(db),resolved_as_existing_body_edge_not_support=True))
 assert{(x['plate'],x['id'])for x in rows}=={('D05','P018'),('D11','P002')};h.put(r.WORK/'body_edge_path_review.json',rows);return rows

def gates():
 geom=r.read(r.WORK/'geometry_summary.json');audit=r.read(r.WORK/'whole_batch_audit.json');continuous=r.read(r.WORK/'continuous_summary.json');fit=r.read(r.WORK/'fit_summary.json');assert geom['passed']and continuous['passed']and fit['passed'];assert geom['types']==150 and len(continuous['rows'])==fit['instances']==9
 by={x['id']:x for x in geom['rows']}
 for row in geom['rows']:assert row['npz_sha256']==h.sha(r.OUT/f"parts/{row['id']}.npz")
 for row in continuous['rows']:assert row['passed']and row['body_sha256']==by[row['id']]['body_sha256'] and all(q['passed']and q['minimum_certified_gap_lower_bound_mm']>.05 for q in row['groups'])
 currentfit=[]
 for f in(r.WORK/'fit').glob('*.json'):
  row=r.read(f);assert row['passed']and row['body_sha256']==by[row['id']]['body_sha256'];currentfit.append(row)
 assert len(currentfit)==9
 for a in audit['rows']:assert a['source_npz_sha256']==h.sha(r.BASE/f"parts/{a['id']}.npz")
 prs=[]
 for p in r.manifest()['plates']:
  pid=p['id'];dest=r.OUT/f'projects/{pid}_O22F7_PLA_final.3mf';digest=h.sha(dest);vp=r.WORK/f'plates/{pid}';paths=r.read(vp/'support_paths.json');mesh=r.read(vp/f'{pid}_native_mesh.json');sl=r.read(vp/'slice.json');hole=r.read(vp/'deposited_hole_clearance.json');clear=r.read(vp/'deposited_retained_clearance.json')
  assert all(x['project_sha256']==digest for x in[paths,mesh,sl,hole,clear]),(pid,'stale proof')
  assert paths['scope_part_ids']is None and paths['candidate_label'].endswith('_full')and paths['native_review_resolved']and paths['external_island_count']==paths['critical_external_count']==0,(pid,'native paths')
  assert mesh['native_mesh_preserved']and mesh['automatic_supports_disabled']and all(all(v==0 for v in q.values())for q in mesh['native_mesh_repairs'])
  assert sl['complete']and sl['object_profiles_verified']and sl['sacrificial_hole_fill_disabled']and sl['original_plate_layout_preserved'];assert hole['generated_support_paths']==clear['generated_support_paths']==0
  assert set(clear['guard_part_ids']) & {x['id']for x in p['items']} == {x['id']for x in p['items']}-r.RESTORE,(pid,'missing eligible guard coverage')
  with zipfile.ZipFile(dest)as z:
   settings=json.loads(z.read('Metadata/project_settings.config'));assert settings['filament_type']==['PLA']and settings['printer_model']=='Bambu Lab A1 mini'and settings['nozzle_diameter']==['0.4']and settings['enable_support']=='0';assert settings['print_sequence']=='by layer';assert float(settings['layer_height'])==p['profile']['layer']and float(settings['initial_layer_print_height'])==.2
   gcode=z.read('Metadata/plate_1.gcode');assert hashlib.sha256(gcode).hexdigest()==sl['gcode_sha256']
  prs.append(dict(id=pid,project=f'projects/{pid}_O22F7_PLA_final.3mf',sha256=digest,objects=len(p['items']),layer_height_mm=p['profile']['layer'],passed=True,external_islands=0,critical_external_runs=0,automatic_mesh_repairs=0,generated_support_paths=0,byte_identical_inherited_native_paths=bool(paths.get('byte_identical_mesh_and_gcode_inherited')),hole_support_exception_ids=sorted({x['id']for x in p['items']}&r.RESTORE)))
 edges=edge_review();return geom,continuous,currentfit,prs,edges

def assemble():
 geom,continuous,fit,prs,edges=gates();by={x['id']:x for x in geom['rows']};m=r.read(r.OUT/'manifest.json');changed=geom['changed_body_types'];m.update(version='O22F7-PLA-Final',status='RELEASED_DIGITAL_CHECKS_PASSED',complete=True,body_changed_from_F5_type_ids=changed,summary='verification/summary.json')
 for row in m['rows']:
  pid=row['id'];g=by[pid];row.update(npz_sha256=g['npz_sha256'],native_pending=False,native_review_passed=True,f7_status=m['status'],body_changed=g['body_changed'],body_vertices_and_faces_identical_to_F5=not g['body_changed'],retained_hole_support_exception=pid in r.RESTORE,original_F5_support_restored=pid in r.RESTORE and pid not in changed,all_fastener_clearance_support_free=pid not in r.RESTORE,geometry_proof=f'verification/geometry_final/{pid}.json',support_geometry_changed=g['fin_material_removed_mm3']>1e-6 or g['new_support_teeth_mm3']>1e-6 or row.get('support_geometry_changed',False),physical_print_tested=False)
  n=np.load(r.OUT/f'parts/{pid}.npz');row['support_volume_mm3']=(h.solid(n['fin_v'],n['fin_f'])+h.solid(n['teeth_v'],n['teeth_f'])).volume()
  d=r.read(r.OUT/f'design/{pid}.json');d['f7_status']=m['status'];d['native_pending']=False;d['f7_verification']=g
  if pid in changed and 'f6_hole_clearance'in d:d['inherited_f6_hole_clearance']=d.pop('f6_hole_clearance')
  h.put(r.OUT/f'design/{pid}.json',d);h.put(r.OUT/f'records/{pid}.json',dict(summary=row,geometry=g,verification=f'verification/geometry_final/{pid}.json'));write(r.OUT/f'records/{pid}.js','window.AUDIT_DETAILS['+json.dumps(pid)+']='+json.dumps(row,ensure_ascii=False,separators=(',',':'))+';')
 for p in m['plates']:
  pp=next(x for x in prs if x['id']==p['id']);p.update(project=pp['project'],project_sha256=pp['sha256'],native_review_passed=True,proof=f"verification/plates/{p['id']}/support_paths.json",title='O22F7 PLA 最终版')
 h.put(r.OUT/'manifest.json',m);write(r.OUT/'audit-data.js','window.AUDIT='+json.dumps(m,ensure_ascii=False,separators=(',',':'))+';window.AUDIT_DETAILS={};window.AUDIT_MESHES={};')
 for sub in['geometry_final','geometry','removal','contacts','continuous','fit','guards','initial']:shutil.copytree(r.WORK/sub,r.OUT/'verification'/sub,dirs_exist_ok=True)
 for name in['whole_batch_audit.json','geometry_summary.json','continuous_summary.json','fit_summary.json','P002_clearance_adjustment.json','P002_pose71.json','body_edge_path_review.json','viewer_mesh_equality.json']:shutil.copy2(r.WORK/name,r.OUT/'verification'/name)
 for p in prs:
  dest=r.OUT/f"verification/plates/{p['id']}";dest.mkdir(parents=True,exist_ok=True)
  for q in(r.WORK/f"plates/{p['id']}").glob('*.json'):shutil.copy2(q,dest/q.name)
 summary=dict(version=m['version'],status=m['status'],types=150,main_instances=186,optional_instances=7,total_instances=193,plates=14,body_changed_types=changed,unchanged_body_types=142,modified_installed_parts=9,modified_installed_elbows=18,modified_printed_instances_including_sample=10,new_contact_teeth_by_type={pid:len(r.read(r.OUT/f'design/{pid}.json').get('r1_native_contacts',[]))for pid in changed},all_native_plates_passed=True,external_islands=0,critical_external_runs=0,generated_support_paths=0,local_continuous_movement_instances=9,whole_device_sampled_pose_checks=sum(x['pose_count']for x in fit),valid_sampled_checks=sum(x['valid_pose_count']for x in fit),existing_infeasible_pose_checks=sum(x['pose_count']-x['valid_pose_count']for x in fit),hole_support_exception_ids=sorted(r.RESTORE),all_holes_automatically_clear_after_print=False,physical_print_tested=False,strength_or_fatigue_tested=False,full_continuous_whole_device_motion_proven=False,plate_results=prs)
 h.put(r.OUT/'verification/summary.json',summary);h.put(r.OUT/'RELEASED.json',dict(status=m['status'],version=m['version'],date='2026-10-16',complete=True,summary='verification/summary.json'))
 js=(r.OUT/'viewer.js').read_text('utf8').replace('data.original_F5_support_restored','data.retained_hole_support_exception').replace('d.original_F5_support_restored','d.retained_hole_support_exception')
 js=js.replace("(data.support_geometry_changed?'保留通过检查的孔位避让。':'保留 F5 支撑形状。')", "(data.body_changed?'支撑已按本版补强复核。':data.retained_hole_support_exception?'保留已核验的孔位承托。':'保留已核验的支撑与孔位避让。')")
 js=js.replace('P095、P073 的新增细齿','P095、P073、P051 的新增细齿');write(r.OUT/'viewer.js',js)
 for p in(r.OUT/'elbows').glob('*/index.html'):
  text=p.read_text('utf8').replace('<div id="status" class="status">数字检查进行中；尚未放行打印。</div>', '<div id="status" class="status passed">已通过本版数字检查。永久本体、关节活动、可拆支撑和所在整盘 G-code 均已核验。</div>');write(p,text)
 docs(m,summary,by,prs)
 sources=['core.py','hinge.py','twist.py','three_axis.py','wide_tut.py','tut.py','ankle_core.py','carriers_swept.py','endforms.py','equipped.py'];sourcefiles={str(p.relative_to(h.R)):h.sha(p)for p in[h.R/'Hardware/PoseDoll44/cad/revO15'/name for name in sources]};sourcefiles.update({str(p.relative_to(h.R)):h.sha(p)for p in[h.B/'profiles/device_profile.json',h.B/'profiles/default_pose.json',h.B/'mechanical/sensor_fit.json',h.B/'mechanical/end_axis_fit.json']});h.put(r.OUT/'verification/source_inputs.json',dict(files=sourcefiles,source_F6_manifest_sha256=h.sha(r.BASE/'manifest.json'),source_R1_release_sha256=h.sha(r.R1/'RELEASED.json'),no_kinematic_profile_or_mechanical_source_modified=True))
 for p in list((h.R/'scripts').glob('o22f7*.py'))+list((h.R/'scripts').glob('o22f7*.cmd')):shutil.copy2(p,r.OUT/'verification'/p.name)
 print('RELEASE_ASSEMBLED',summary,flush=True)

def docs(m,summary,by,prs):
 changed=summary['body_changed_types'];names={'P002':'腰部','P018':'胸部','P035':'头部','P051':'左上臂','P073':'右上臂','P095':'左大腿','P117':'右大腿','P130':'左右脚'};LOCATIONS['P130']='左右脚 C14：肩轴/M3 孔、垫片槽、螺母位及四角连接孔'
 changedtable=''.join('<tr><td><a href="elbows/'+pid+'/index.html">'+pid+'</a></td><td>'+names[pid]+'</td><td>'+str(round(by[pid]['body_added_mm3'],2))+'</td><td>'+str(summary['new_contact_teeth_by_type'][pid])+'</td></tr>'for pid in changed)
 exceptions=''.join('<tr><td><a href="index.html?id='+pid+'">'+pid+'</a></td><td>'+html.escape(LOCATIONS[pid])+'</td></tr>'for pid in sorted(r.RESTORE))
 printtext='<h1>O22F7 · PLA 打印与拆撑</h1><div class="ok">完整 14 盘，150 类、193 个实例（186 正式件及 7 个可选小样）。全部盘通过数字网格和完整 G-code 悬空/承托检查。使用本包全部 D01–D14 工程。</div><h2>打印设置</h2><p>OrcaSlicer 中以项目打开 projects/ 下的 O22F7_PLA_final.3mf。Bambu Lab A1 mini · 0.4 mm 喷嘴 · PLA · 按层打印。D01、D02 层高 0.16 mm，其余盘 0.20 mm，首层均 0.20 mm。保留对象参数、盘位和朝向；自动支撑关闭，模型内已包含可拆承托与核验后的 G-code。</p><h2>先拆撑，再装配</h2><ol><li>冷却后扶住厚壁，先剪清黄色连接齿及挡路齿根，再按三维页面顺序取下橙色支撑鳍。蓝色圆接头属于永久本体，不能剪除。</li><li>孔内细长齿先从外侧断根，保持孔内段完整，依图示方向抽出；清理螺钉通道、沉孔及螺母位后再装五金，保持原孔尺寸。</li><li><b>P095：</b>S01 与 S03 合为一组向下取出；S06 斜向外下方退出。H2/H4 原 T202、T203 细齿仍需清理；新增 5 根细齿中 2 根涉及孔位保护空间。</li><li><b>P073：</b>新增 1 根细齿涉及孔位保护空间；剪断后 S03 沿三维页绿色箭头斜向退出。</li><li><b>P051：</b>新增 2 根细齿，剪断后 S05 向下退出。红点为剪断位置，绿色箭头为退出方向，均只是页面标记。</li></ol><p><a href="elbows/P095/index.html">P095 剪齿定位</a> · <a href="elbows/P073/index.html">P073 剪齿定位</a> · <a href="elbows/P051/index.html">P051 剪齿定位</a></p><h2>转角修订</h2><p>8 类 C14 支架共对应 9 个安装件、18 处转角；另含一件 P130 可选小样。仅增加局部材料，原杆体、孔位、轴线、止挡、轴承配合与传感器安装位置保持。P002 一处接头按胸架空间保留小避让面，没有切削原杆体。</p><table><tr><th>零件 / 前后对比</th><th>位置</th><th>新增永久材料 mm³</th><th>新增可剪细齿</th></tr>'+changedtable+'</table><h2>孔位承托例外</h2><p>按此前接受的承托方案，以下 16 类仍可能在孔内或孔口有可拆支撑，不能把本包理解为打印完成即自动通孔。134 类支撑实体仍未进入所检查的孔位保护空间。</p><table><tr><th>零件</th><th>重点清理位置</th></tr>'+exceptions+'</table><p><a href="assembly/tutorials/assembly-o22/index.html">26 步安装图解</a> · <a href="零件与打印盘对照.csv">完整编号对照</a></p><p class="muted">本批尚未实物试打或做强度、疲劳验证。材料结合和拆撑手感需以实际打印件确认。</p>'
 write(r.OUT/'打印与拆撑.html',page('O22F7 PLA 打印与拆撑',printtext))
 pt=''.join('<tr><td>'+p['id']+'</td><td>'+str(p['objects'])+'</td><td>'+str(p['layer_height_mm'])+'</td><td>0 / 0</td><td><a href="'+p['project']+'">PLA 3MF</a> · <a href="verification/plates/'+p['id']+'/support_paths.json">完整路径证据</a></td></tr>'for p in prs)
 review='<h1>O22F7 · 检查记录</h1><div class="ok">14/14 盘通过；未解决悬空起印区 0，外部悬空路径 0，切片器自动修网格 0。阈值沿用原批次。</div><h2>功能保持</h2><p>150 类逐件检查，8 类 C14 修复同源转角缺口，其余 142 类本体与 F6 完全相同。全部新增材料均未进入所检查的螺丝保护空间，未改变轴线、孔位、配合与运动参数。</p><p>9 个安装实例通过本关节范围内的连续旋转包络检查：用包含新增材料的球包络、带符号距离和保守位移上界覆盖角度区间。另对整机进行 '+str(summary['whole_device_sampled_pose_checks'])+' 次姿态实例检查，其中 '+str(summary['valid_sampled_checks'])+' 次没有检出记录所列的原有碰撞；'+str(summary['existing_infeasible_pose_checks'])+' 次已有本体碰撞的姿态被排除并保留证据。整机抽查不等于全部关节组合的连续运动证明。</p><p>P002 初次直接补圆与胸架存在新增交叠；最终只修剪 0.306 mm³ 拟新增材料，该姿态新增材料间隙为 0.285 mm，原杆体完全保留。</p><h2>支撑和孔道</h2><p>全部 150 类实体连通、支撑落地。修改过的鳍及新增细齿剪断后的退出路径通过连续扫掠检查。16 类孔位承托例外沿用，并更新 P095、P073、P051 的剪齿定位。</p><p>D05/P018、D11/P002 在 15.40 mm 层的原始孔边提示经复核为已发布 F6 中相同的本体加宽路径，距离支撑超过 0.5 mm；不是新增支撑堵孔。原始报告与判定证据均保留。</p><h2>逐盘</h2><table><tr><th>盘</th><th>实例数</th><th>层高 mm</th><th>悬空区 / 未解路径</th><th>文件与证据</th></tr>'+pt+'</table><p>六盘重新切片并复查；八盘继承已核验的完整原生路径，其中 D01 为已验证的 P095 修订盘。继承盘的实际对象网格和 G-code 逐字节一致，只更新工程标签，包含校验依据。</p><p><a href="verification/whole_batch_audit.json">全件排查</a> · <a href="verification/continuous_summary.json">本关节连续运动</a> · <a href="verification/fit_summary.json">整机姿态抽查</a> · <a href="verification/geometry_summary.json">实体与孔位检查</a></p><p class="muted">以上均为数字验证；尚未实物打印、强度或疲劳试验。</p>'
 write(r.OUT/'检查与例外.html',page('O22F7 检查记录',review))
 text='O22F7 PLA 完整打印包\n2026-10-16\n\n14 盘 / 150 类 / 193 个实例（186 正式件 + 7 可选小样）。\n本包已整合全部修订，请统一使用 projects/ 下 D01–D14_O22F7_PLA_final.3mf。\n\n打印：Bambu Lab A1 mini / 0.4 mm 喷嘴 / PLA / 按层打印。\nD01、D02 层高 0.16 mm，其余 0.20 mm；首层均 0.20 mm。\n以项目打开，保留每个对象设置、盘位和朝向；自动支撑关闭，模型内已包含可拆承托。\n\n8 类 C14 转角已修订：P002、P018、P035、P051、P073、P095、P117、P130。\n对应 9 个安装件、18 处转角，P130 另有一件可选小样。原杆体、孔位、轴线与配合保持。\nP002 保留用于胸架运动的小避让面，仅从拟新增圆接头修剪，原杆体不变。\n\n拆撑重点：\n蓝色永久本体保留；橙色支撑鳍及黄色细齿移除。\nP095：S01+S03 一起向下取出，S06 斜向退出；原孔内 T202/T203 仍需清理。\nP073：新增细齿剪断后 S03 斜向退出。\nP051：新增两根细齿剪断后 S05 向下退出。\n在 index.html 选择零件，再点“转角前后与剪齿定位”，按红点剪断、按绿色箭头退出。\n16 类保留孔位承托例外，清理孔道和沉孔后再装五金；详见打印与拆撑.html。\n\n验证：全部 14 盘通过数字网格和完整 G-code 检查，未解决悬空问题 0。\n9 个安装实例的本关节连续转动检查通过；整机组合姿态抽查通过，但不代表全部关节组合的连续运动证明。\n本批尚未实物试打，未做强度或疲劳验证。\n\n双击 打开3D与安装说明.cmd，或打开 index.html 查看模型、打印盘和安装说明。\nverification/ 保存检查记录；SHA256SUMS.txt 保存整套文件校验值。\n'
 text=text.replace('双击 打开3D与安装说明.cmd，或打开 index.html 查看模型、打印盘和安装说明。','双击 打开3D与安装说明.cmd，或打开 index.html 查看模型、打印盘和安装说明。\n启动入口已于 2026-10-16 修复旧版页面串用问题。关闭之前的旧标签页后，重新双击本包入口；预览期间请保留启动窗口。')
 (r.OUT/'先读我.txt').write_text(text,encoding='utf-8-sig')

def links():
 bad=[];count=0
 for p in r.OUT.rglob('*.html'):
  for u in re.findall(r'(?:href|src)=["\']([^"\']+)',p.read_text('utf-8-sig')):
   if u.startswith(('http:','https:','data:','#','javascript:','mailto:'))or'${'in u:continue
   path=urllib.parse.unquote(u.split('#')[0].split('?')[0])
   if not path:continue
   count+=1
   if not(p.parent/path).exists():bad.append((str(p.relative_to(r.OUT)),u))
 assert not bad,bad;h.put(r.OUT/'verification/asset_links.json',dict(passed=True,local_links_checked=count))

def bundle():
 from verify_o22f7_assembly_guide import verify as verify_guide
 verify_guide()
 gates();links();assert(r.OUT/'RELEASED.json').exists();assert(r.OUT/'verification/ui_review.json').exists()
 files=sorted(p for p in r.OUT.rglob('*')if p.is_file()and p.name!='SHA256SUMS.txt'and '__pycache__'not in p.parts);checks={p.relative_to(r.OUT).as_posix():h.sha(p)for p in files};write(r.OUT/'SHA256SUMS.txt',''.join(v+'  '+k+'\n'for k,v in checks.items()));target=h.B/'O22F7_PLA_完整打印包_20261016.zip'
 with zipfile.ZipFile(target,'w',zipfile.ZIP_DEFLATED,compresslevel=6)as z:
  for p in files+[r.OUT/'SHA256SUMS.txt']:z.write(p,p.relative_to(r.OUT).as_posix())
 with zipfile.ZipFile(target)as z:
  assert z.testzip()is None;assert set(z.namelist())==set(checks)|{'SHA256SUMS.txt'}
  for k,v in checks.items():assert hashlib.sha256(z.read(k)).hexdigest()==v
 report=dict(archive=str(target),bytes=target.stat().st_size,sha256=h.sha(target),files=len(files)+1,verified_every_archived_file=True,complete=True);h.put(r.WORK/'delivery.json',report);write(target.with_suffix('.zip.sha256'),report['sha256']+'  '+target.name+'\n');print('DELIVERED',report,flush=True)
if __name__=='__main__':globals()[sys.argv[1]]()
