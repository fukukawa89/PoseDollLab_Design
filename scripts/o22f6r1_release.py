"""Release gate and self-contained supplement packaging. Never weakens checks."""
import json,copy,shutil,hashlib,zipfile,re
import numpy as np
import o22f6r1_p095 as r
h=r.h

def release():
 o,w=r.OUT,r.WORK;project=o/f'projects/D01_O22F6_{r.SUFFIX}.3mf';project_sha=h.sha(project)
 paths=json.loads((w/'plates/D01/support_paths.json').read_text());sliced=json.loads((w/'plates/D01/slice.json').read_text());mesh=json.loads((w/'plates/D01/D01_native_mesh.json').read_text());holes=json.loads((w/'plates/D01/deposited_retained_clearance.json').read_text())
 assert paths['project_sha256']==sliced['project_sha256']==holes['project_sha256']==project_sha
 assert paths['scope_part_ids'] is None and paths['candidate_label'].endswith('_full')
 assert paths['native_review_resolved'] and paths['critical_external_count']==paths['external_island_count']==0
 assert holes['passed'] and not holes['flagged_layers'] and sliced['complete']
 current=dict(np.load(o/'parts/P095.npz'));before=dict(np.load(r.BASE/'parts/P095.npz'));fitbase=dict(np.load(w/'before_native_contact_repair/P095.npz'))
 fit=json.loads((w/'fit_and_pose.json').read_text());assert fit['passed'] and fit['source_revised_npz_sha256']==h.sha(w/'before_native_contact_repair/P095.npz')
 assert all(np.array_equal(current[k],fitbase[k]) for k in ['v','f','fin_v','fin_f'])
 oldbody=h.solid(before['v'],before['f']);body=h.solid(current['v'],current['f']);fin=h.solid(current['fin_v'],current['fin_f']);teeth=h.solid(current['teeth_v'],current['teeth_f']);oldfin=h.solid(before['fin_v'],before['fin_f']);oldteeth=h.solid(before['teeth_v'],before['teeth_f']);added=h.solid(current['r1_added_body_v'],current['r1_added_body_f']);guard=r.npzsolid(w/'guards/P095.npz')
 assert abs((oldbody-body).volume())<1e-5 and abs((body-(oldbody+added)).volume())<1e-5
 assert (added^guard).volume()<1e-6 and(fin^body).volume()<1e-6
 assert abs((fin-oldfin).volume())<1e-6 and abs((oldteeth-teeth).volume())<1e-5
 assert len(h.material_components(body))==len(h.material_components(body+fin+teeth))==1
 assert all(c.bounding_box()[2]<1e-5 and c.slice(.05).area()>.005 for c in h.material_components(fin))
 geo=json.loads((w/'revision_geometry.json').read_text());geo.update(status='digital_checks_passed',revised_npz_sha256=h.sha(o/'parts/P095.npz'),tooth_vertices_and_faces_identical=False,extra_removable_tooth_mm3=float((teeth-oldteeth).volume()),support_guard_occupation_change_mm3=float(((fin+teeth)^guard).volume()-((oldfin+oldteeth)^guard).volume()),original_teeth_preserved=True,body_mesh_identical_to_pose_checked_mesh=True)
 assert geo['support_guard_occupation_change_mm3']>=-1e-5
 removal=json.loads((w/'final_removal.json').read_text());assert removal['passed'] and removal['npz_sha256']==h.sha(o/'parts/P095.npz')
 geo.update(original_teeth_preserved=True,continuous_downward_fin_exit=False,revised_fin_removal_verified=True,final_removal_proof='final_removal.json',continuous_exit_proof='See final_removal.json: original subset proof plus continuous sweeps of all added cut stubs; S01/S03 exit together and S06 exits diagonally.')
 h.put(w/'geometry_final.json',geo)
 fit.update(final_npz_sha256=h.sha(o/'parts/P095.npz'),final_body_arrays_identical_to_tested_mesh=True,post_fit_change='Only removable connector geometry; permanent body and fin arrays unchanged')
 scope=json.loads((w/'scope.json').read_text())
 for row in scope['rows']:
  pid=row['id'];assert h.sha(r.BASE/f'parts/{pid}.npz')==row['before_sha256']
  if pid!='P095':assert h.sha(o/f'parts/{pid}.npz')==row['before_sha256']
  row['after_sha256']=h.sha(o/f'parts/{pid}.npz')
 other=[]
 for p in sorted((r.BASE/'projects').glob('*.3mf')):
  pid=p.name[:3]
  if pid=='D01':continue
  q=json.loads((r.OLDWORK/f'plates/{pid}/support_paths.json').read_text());assert q['project_sha256']==h.sha(p) and q['native_review_resolved'] and q['scope_part_ids'] is None
  other.append(dict(plate=pid,filename=p.name,sha256=h.sha(p),native_path_checks_passed=True,reused_without_modification=True))
 assert len(other)==13
 d=json.loads((o/'design/P095.json').read_text());overrides=json.loads((w/'profile_overrides.json').read_text()).get('P095',{})
 d.update(f6_status='R1_digital_checks_passed',native_pending=False,physical_print_tested=False,r1_process_overrides=overrides,f6r1_elbow_revision=geo,f6_support_policy='Original hole support exception retained; locally relieved fins and five additional removable contacts, including two hole-support exceptions')
 h.put(o/'design/P095.json',d)
 for src,dst in [('geometry_final.json','geometry.json'),('native_contact_repair.json','native_contact_repair.json'),('viewer_mesh_equality.json','viewer_mesh_equality.json'),('rod_joint_diagnosis.json','rod_joint_diagnosis.json'),('final_removal.json','final_removal.json')]:shutil.copy2(w/src,o/'verification'/dst)
 h.put(o/'verification/fit_and_pose.json',fit);h.put(o/'verification/scope.json',scope)
 shutil.copytree(w/'plates/D01',o/'verification/D01',dirs_exist_ok=True)
 contacts=d['r1_native_contacts'];assert len(contacts)==5 and all(q['continuous_cut_stub_exit_clear']for q in contacts)
 report=dict(version='O22F6-R1-P095-elbows',release_date='2026-10-16',scope='D01 replacement supplement for O22F6 PLA Final; other thirteen plates are reused by exact SHA256',project=project.relative_to(o).as_posix(),project_sha256=project_sha,plate_instances=12,permanent_parts_changed=['P095'],permanent_change='Two R1.8 mm rounded elbow fills; approximately 11.99 mm3 added; no intentional body subtraction',geometry=geo,native_full_plate_passed=True,external_islands=0,critical_external_paths=0,other_previously_clear_parts_remain_clear=True,pose_sampling=dict(total=fit['pose_count'],excluded_preexisting_collision_poses=fit['excluded_pose_count'],remaining_samples=fit['examined_poses_without_detected_preexisting_collision'],new_interference_in_remaining_samples=False,continuous_combined_motion_proven=False),process_overrides_for_P095=overrides,hole_support_exception='P095 original removable supports and two added contact branches occupy screw/counterbore clearance. User-authorized printability fallback; clear before assembly.',other_plates=other,physical_print_tested=False,physical_strength_or_fatigue_tested=False)
 h.put(o/'verification/release.json',report);h.put(o/'RELEASED.json',dict(version=report['version'],project_sha256=project_sha,physical_print_tested=False))
 html=(o/'index.html').read_text(encoding='utf8');html=html.replace('id="status" class="status">数字检查进行中；尚未放行打印。','id="status" class="status passed">D01 完整原生路径检查通过：0 个外部孤岛、0 段超限悬空；网格与孔位复核通过。尚未实物打印或强度测试。');(o/'index.html').write_text(html,encoding='utf8')
 (o/'release-status.js').write_text("document.getElementById('status').classList.add('passed');document.getElementById('status').textContent='D01 完整原生路径检查通过：0 个外部孤岛、0 段超限悬空；网格与孔位复核通过。尚未实物打印或强度测试。';",encoding='utf8')
 note='''O22F6 R1 — P095 转角补强修订包（2026-10-16）

使用：用 projects/D01_O22F6_PLA_R1_P095_elbows.3mf 替换原 O22F6 的 D01。
其余 D02–D14 继续使用 O22F6_PLA_Final 原文件；本包 verification/release.json 列出其 SHA256。
D01 仍包含原来的 12 个实例，唯一发生改动的零件是 P095（D01-01）。
打印机：Bambu A1 mini / 0.4 mm 喷嘴 / PLA；层高 0.16 mm，首层 0.20 mm。
保留文件内朝向、参数和自带支撑，勿叠加自动支撑。

原因：两段直径 3.6 mm 的平端圆杆在 L 转折点相接，没有补圆滑接头。
两个缺口都存在于原始模型中，与缺少打印支撑或 PETG 无关，换 PLA 不会消除。
本次两处各补 R1.8 mm 接头，合计新增永久材料约 11.99 mm³。
永久零件的总尺寸、螺丝安装空间保持；转角附近支撑鳍作小量避让。
另增五处可剪连接齿以承托实际切片路径，其中两处进入孔位保护空间；
按用户已授权的承托例外保留，打印后必须清理。
具体 P095 切片覆盖参数见 verification/release.json 的 process_overrides_for_P095。

拆撑：新补圆的蓝色接头属于永久零件，不能剪掉。
先按预览中的红点剪开新增细齿，并剪清原有连接齿与挡路的齿根。
S01 与 S03 连为一组，同时向下退出；S06 沿预览绿色箭头斜向外下方退出。
其他鳍保持原相对顺序向下拆除。完整顺序和方向见 verification/final_removal.json。
拆撑定位下拉菜单可高亮这些支撑，红点和绿色箭头仅为说明标记，不会打印。
清理孔口剩余的上端短齿；新增的圆滑转角属于永久本体，不可剪掉。
P095 的原有孔位承托例外仍保留；清理孔道、沉孔，再装螺丝。
剪齿时托住附近本体，避免把上方圆柱体当杠杆硬掰连接杆。

查看：打开 index.html 可同步旋转修订前后的实际模型。可选转角 A、B 和整体视图，
也可显示实际支撑或用金色突出新增永久材料。局部视图有裁切，不代表端部敞开。

验证：D01 全盘原生 G-code 复核，0 外部孤岛、0 超限悬空路径；12 个实例网格
与实际打印文件一致，切片无网格修复。原已清孔的其他零件继续通过出丝孔位检查。
补强的装配检查采样 784 个姿态；293 个存在原模型已有碰撞，单列为不可达采样。
其余 491 个采样未检出新增干涉。此检查不等于证明所有连续组合运动都无碰撞。
未做实物打印、载荷或疲劳试验，不能据此承诺连接杆不会断裂。
原 O22F5、O22F6 文件未被覆盖。
'''
 (o/'先读我.txt').write_text(note,encoding='utf8')
 # Every referenced local asset in the standalone preview must be delivered.
 for ref in re.findall(r'(?:href|src)="([^"#]+)',(o/'index.html').read_text(encoding='utf8')):
  if ref.startswith(('data:','http:','https:')):continue
  assert(o/ref).exists(),ref
 for file in ['comparison.png','overview.png']:
  assert(o/file).exists(),'Visual review screenshot is required before archive'
 sums={p.relative_to(o).as_posix():h.sha(p)for p in sorted(o.rglob('*'))if p.is_file()and p.name!='SHA256SUMS.txt'}
 (o/'SHA256SUMS.txt').write_text(''.join(v+'  '+k+'\n'for k,v in sums.items()),encoding='utf8')
 zpath=h.B/'O22F6R1_P095_转角补强_20261016.zip'
 assert not zpath.exists(),'Never overwrite a delivered archive'
 with zipfile.ZipFile(zpath,'w',zipfile.ZIP_DEFLATED,compresslevel=6)as z:
  for p in sorted(o.rglob('*')):
   if p.is_file():z.write(p,o.name+'/'+p.relative_to(o).as_posix())
 with zipfile.ZipFile(zpath)as z:
  assert z.testzip() is None
  for name,expected in sums.items():assert hashlib.sha256(z.read(o.name+'/'+name)).hexdigest()==expected
 integrity=dict(archive=str(zpath),bytes=zpath.stat().st_size,sha256=h.sha(zpath),files=len(sums)+1,all_archived_files_hash_verified=True,project=str(project),project_sha256=project_sha)
 h.put(w/'delivery_integrity.json',integrity);print(json.dumps(integrity,ensure_ascii=False,indent=2))
if __name__=='__main__':release()