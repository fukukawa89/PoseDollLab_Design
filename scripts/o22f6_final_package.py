"""Release only after final native meshes, all paths, and allowed-hole exceptions verify."""
from pathlib import Path
import json,copy,shutil,html,csv,zipfile,hashlib,collections,sys,datetime
import numpy as np
from shapely.geometry import LineString
import o22f6_final as f
h=f.h;f.configure()
LOCATIONS={
 'P035':'头部 C14 四角连接孔、PCB 夹螺母位',
 'P051':'左上臂 C14 四角连接孔、沉孔和螺母位',
 'P071':'右上臂 C01 肩轴孔及邻近五金孔口',
 'P073':'右上臂 C14 四角连接孔、沉孔和螺母位',
 'P093':'左大腿 C01 肩轴孔及邻近五金孔口',
 'P095':'左大腿 C14 下方四孔；重点清理 H2、H4 中的 T202、T203',
 'P117':'右大腿 C14 四角连接孔、沉孔和螺母位',
 'P130':'右脚 C14 四组肩轴/M3 孔、垫片槽、螺母位及四角连接孔',
 'W007':'左小腿磁铁盖固定螺孔及邻接肩轴通道',
 'W016':'左脚肩轴孔、球关节 M3 螺母/垫片侧入口',
 'W017':'右脚肩轴孔、球关节 M3 螺母/垫片侧入口',
 'X038':'骨盆两侧大腿调节螺母入口与壳体固定孔',
 'X046':'胸架肩轴孔、头部调节螺母入口与壳体固定孔',
 'X058':'左上臂调节螺母入口、壳体孔及肘部邻接五金孔口',
 'X062':'右锁骨/右上臂壳体孔、肩轴孔及磁铁盖固定螺孔',
 'X066':'右上臂壳体固定孔与肘部肩轴孔',
}
CSS='body{font:16px/1.65 system-ui,"Microsoft YaHei",sans-serif;max-width:1160px;margin:32px auto;padding:0 24px;color:#20383e;background:#f4f7f5}h1{font-size:30px}h2{margin-top:28px;font-size:22px}.note{padding:16px;background:#fff0d8;border-left:5px solid #bf792d}.ok{padding:16px;background:#e3f2eb;border-left:5px solid #37866c}table{border-collapse:collapse;width:100%;background:#fff;margin:16px 0}td,th{padding:10px;border:1px solid #cfded8;text-align:left}a{color:#126c81}li{margin:9px 0}.muted{color:#627974;font-size:14px}svg{max-width:380px;width:100%;height:auto}code{font-size:14px}'
def write(p,s):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(s,encoding='utf-8')
def page(title,body):return '<!doctype html><html lang="zh-CN"><meta charset="utf-8"><link rel="icon" href="data:,"><meta name="viewport" content="width=device-width,initial-scale=1"><title>'+title+'</title><style>'+CSS+'</style><p><a href="index.html">彩色拆撑 3D</a> · <a href="合盘布局.html">打印盘布局</a> · <a href="打印与拆撑.html">打印与拆撑</a> · <a href="检查与例外.html">检查与例外</a></p>'+body+'</html>'
def edge_review():
 from o22_f3_gcode import extract_detailed
 from o22_cross_section_geometry import polygon
 rows=[];expected={('D05','P018'),('D11','P002')}
 for p in f.manifest()['plates']:
  pid=p['id'];r=json.loads((f.WORK/f'plates/{pid}/deposited_retained_clearance.json').read_text());assert r['project_sha256']==h.sha(f.OUT/f'projects/{pid}_O22F6_PLA_final.3mf');assert set(r['guard_part_ids'])=={q['id']for q in f.manifest()['rows']}-f.RESTORE
  if not r['flagged_layers']:continue
  rep,raw,*_=extract_detailed(h.SRC/p['project'],arc_tolerance_mm=.02,max_arc_segment_mm=.6);a=np.asarray(raw).reshape(-1,9)
  for flag in r['flagged_layers']:
   assert flag['segment_count']==len(flag['segments'])==6 and abs(flag['z_mm']-15.4)<.001
   xy=np.mean(np.array([q['xy']for q in flag['segments']]).reshape(-1,2),axis=0);owners=[it for it in p['items']if it['bounds_mm'][0]<=xy[0]<=it['bounds_mm'][3]and it['bounds_mm'][1]<=xy[1]<=it['bounds_mm'][4]];assert len(owners)==1;it=owners[0];assert(pid,it['id'])in expected
   n=np.load(f.OUT/f"parts/{it['id']}.npz");body=h.solid(n['v'],n['f']);support=h.solid(n['fin_v'],n['fin_f'])+h.solid(n['teeth_v'],n['teeth_f']);U=np.array(it['rotation_matrix']);t=np.array(it['translation_mm']);z=flag['z_mm'];bodypg=polygon(body.slice(z-p['profile']['layer']/2));suppg=polygon(support.slice(z-p['profile']['layer']/2));ds=[];db=[];matches=[]
   for q in flag['segments']:
    pts=(np.c_[q['xy'],[z,z]]-t)@U;line=LineString(pts[:,:2]);ds.append(line.distance(suppg));db.append(line.distance(bodypg));samez=a[(abs(a[:,5]-z)<.001)&(a[:,7]==0)];target=np.array(q['xy']);near=np.flatnonzero(np.max(abs(samez[:,[0,1,3,4]]-target.reshape(-1)),axis=1)<.002);matches.append(bool(len(near)and abs(samez[near[0],8]-q['width_mm'])<.002))
   assert all(matches)and min(ds)>.5 and max(db)<1e-5,(pid,matches,ds,db)
   rows.append(dict(plate=pid,id=it['id'],project_sha256=r['project_sha256'],z_mm=z,area_mm2=flag['area_mm2'],segment_count=6,all_flagged_segments_also_present_in_F5=True,minimum_centerline_distance_to_support_mm=min(ds),maximum_centerline_distance_to_body_mm=max(db),interpretation='Existing body-tip widened perimeter, not a support. Raw cavity-screen flags are preserved.',review_resolved=True))
 assert {(r['plate'],r['id'])for r in rows}==expected
 h.put(f.WORK/'body_edge_path_review.json',rows);print('EDGE_REVIEW_COMPLETE',len(rows),flush=True);return rows

def collect():
 m=f.manifest();stage=json.loads((f.WORK/'staging.json').read_text());assert h.sha(h.SRC/'manifest.json')==stage['source_manifest_sha256'];assert h.sha(f.CAND/'manifest.json')==stage['candidate_manifest_sha256'];geos={r['id']:r for r in json.loads((f.WORK/'geometry_verification.json').read_text())['rows']};subset={r['id']:r for r in json.loads((f.WORK/'support_subset_proof.json').read_text())};rows=json.loads((f.WORK/'viewer_rows.json').read_text());plate_results=[];preserved=[]
 assert len(rows)==len(geos)==len(subset)==150
 for p in m['plates']:
  pid=p['id'];path=f.OUT/f'projects/{pid}_O22F6_PLA_final.3mf';digest=h.sha(path);vp=f.WORK/f'plates/{pid}';r=json.loads((vp/'support_paths.json').read_text());sl=json.loads((vp/'slice.json').read_text());mesh=json.loads((vp/f'{pid}_native_mesh.json').read_text());holes=json.loads((vp/'deposited_hole_clearance.json').read_text());cleared=json.loads((vp/'deposited_retained_clearance.json').read_text())
  assert all(d['project_sha256']==digest for d in [r,sl,mesh,holes,cleared]),(pid,'stale_report')
  assert r['scope_part_ids']is None and r['candidate_label'].endswith('_full')and r['native_review_resolved']and r['external_island_count']==0 and r['critical_external_count']==0,(pid,'unresolved_native_paths')
  assert sl['complete']and sl['object_profiles_verified']and sl['original_plate_layout_preserved']and sl['sacrificial_hole_fill_disabled'];assert mesh['native_mesh_preserved']and mesh['automatic_supports_disabled'];assert holes['generated_support_paths']==cleared['generated_support_paths']==0
  assert h.sha(h.SRC/p['project'])==p['project_sha256'];preserved.append(dict(path=p['project'],sha256=p['project_sha256'],verified_unchanged=True))
  v=dict(id=pid,project=f'projects/{pid}_O22F6_PLA_final.3mf',project_sha256=digest,objects=len(p['items']),layer_height_mm=p['profile']['layer'],native_mesh_verified=True,whole_plate_native_paths_checked=True,external_island_count=0,critical_external_count=0,native_review_passed=True,restored_support_type_ids=sorted({it['id']for it in p['items']}&f.RESTORE),whole_plate_cavity_raw_passed=holes['passed'],whole_plate_cavity_flagged_layers=len(holes['flagged_layers']),retained_clearance_raw_passed=cleared['passed'],retained_clearance_flagged_layers=len(cleared['flagged_layers']),generated_support_paths=0,physical_print_tested=False);plate_results.append(v)
 for row in rows:
  pid=row['id'];g=geos[pid];old=next(r for r in m['rows']if r['id']==pid);assert h.sha(f.OUT/f'parts/{pid}.npz')==g['npz_sha256']==subset[pid]['source_npz_sha256'];assert h.sha(h.SRC/f'parts/{pid}.npz')==g['source_npz_sha256']==old['npz_sha256'];assert g['body_vertices_and_faces_identical_to_F5']and subset[pid]['support_subset_of_F5'];assert (g['after_support_in_guard_mm3']>1e-6)==(pid in f.RESTORE)
  row.update(f6_status='RELEASED_DIGITAL_CHECKS_PASSED',native_review_passed=True,native_pending=False,physical_print_tested=False,all_fastener_clearance_support_free=pid not in f.RESTORE,clearance_exception_location=LOCATIONS.get(pid),source_support_restoration_authorized=pid in f.RESTORE)
  preserved.append(dict(path=f'parts/{pid}.npz',sha256=old['npz_sha256'],verified_unchanged=True))
 return m,rows,plate_results,preserved

def package():
 edges=edge_review();m,rows,prs,preserved=collect();assert len(prs)==14
 # The release gate above is evaluated before changing any release-status file.
 for row in rows:
  pid=row['id'];d=json.loads((f.OUT/f'design/{pid}.json').read_text());d.update(f6_status=row['f6_status'],native_pending=False,physical_print_tested=False,f6_hole_clearance=row);h.put(f.OUT/f'design/{pid}.json',d)
  h.put(f.OUT/f'verification/parts/{pid}/geometry.json',row);shutil.copy2(f.WORK/f'initial/{pid}.json',f.OUT/f'verification/parts/{pid}/guard_definitions.json');dest=f.OUT/f'verification/guards/{pid}.npz';dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(f.WORK/f'guards/{pid}.npz',dest)
  record=json.loads((f.OUT/f'records/{pid}.json').read_text());record['summary']=row;h.put(f.OUT/f'records/{pid}.json',record);write(f.OUT/f'records/{pid}.js','window.AUDIT_DETAILS['+json.dumps(pid)+']='+json.dumps(row,ensure_ascii=False,separators=(',',':'))+';')
  if row['original_F5_support_restored']:
   original=json.loads((f.WORK/f'initial/{pid}.json').read_text());features=[q for q in original['features']if q['fin_mm3']+q['tooth_mm3']>1e-6];h.put(f.OUT/f'verification/parts/{pid}/authorized_hole_support.json',dict(id=pid,npz_sha256=row['npz_sha256'],original_F5_restored_exactly=True,reason='Hole-clear trials left unsupported starts or external free paths; the user authorized restoring original removable supports if needed.',clearance_location=LOCATIONS[pid],features=features,features_overlap_each_other_do_not_sum=True,original_stem_removal_record_order=row['stem_removal_record_order'],original_fin_removal_stages=row['removal_stages']))
 for p in prs:
  dest=f.OUT/f"verification/plates/{p['id']}";dest.mkdir(parents=True,exist_ok=True)
  for q in(f.WORK/f"plates/{p['id']}").glob('*.json'):shutil.copy2(q,dest/q.name)
 summary=dict(version='O22F6-PLA-Final',status='RELEASED_DIGITAL_CHECKS_PASSED',complete=True,release_criteria_passed=True,types=150,main_instances=186,optional_instances=7,total_instances=193,plates=14,source_types_with_support_in_fastener_guard=sum(r['before_support_in_guard_mm3']>1e-6 for r in rows),cleared_modified_type_count=sum(r['support_geometry_changed']for r in rows),restored_original_support_type_ids=sorted(f.RESTORE),restored_original_support_instances=sum(len(r['instances'])for r in rows if r['id']in f.RESTORE),all_body_meshes_identical_to_F5=True,all_fastener_cavities_support_free=False,hole_review_passed_with_authorized_exceptions=True,retained_clearance_type_count=150-len(f.RESTORE),retained_clearance_additional_body_edge_review=edges,native_passed_plates=[p['id']for p in prs],external_islands=0,critical_external_runs=0,generated_support_paths=0,physical_print_tested=False,screening_thresholds_unchanged_from_F5=True,plate_results=prs,guard_policy=json.loads((f.WORK/'inventory.json').read_text())['guard_policy'])
 h.put(f.OUT/'verification/summary.json',summary);h.put(f.OUT/'verification/F5_original_preservation.json',dict(original_manifest_sha256=h.sha(h.SRC/'manifest.json'),files=preserved,all_14_native_projects_and_150_parts_verified_unchanged=True));h.put(f.OUT/'verification/body_edge_path_review.json',edges)
 for name in ['geometry_verification.json','support_subset_proof.json','staging.json','rejected_experiment_summary.json']:
  if(f.WORK/name).exists():shutil.copy2(f.WORK/name,f.OUT/'verification'/name)
 manifest=dict(version=summary['version'],status=summary['status'],complete=True,main_instances=186,sample_instances=7,samples_embedded_in_main_plates=True,type_count=150,main_plate_count=14,sample_plate_count=0,physical_tested_type_ids=[],physical_print_tested=False,body_changed_from_F5_type_ids=[],restored_original_support_type_ids=sorted(f.RESTORE),rows=rows,plates=copy.deepcopy(m['plates']),summary='verification/summary.json')
 for p in manifest['plates']:
  v=next(x for x in prs if x['id']==p['id']);p.update(project=v['project'],project_sha256=v['project_sha256'],proof=f"verification/plates/{p['id']}/support_paths.json",native_review_passed=True,title='O22F6 PLA 最终版')
 h.put(f.OUT/'manifest.json',manifest);write(f.OUT/'audit-data.js','window.AUDIT='+json.dumps(manifest,ensure_ascii=False,separators=(',',':'))+';window.AUDIT_DETAILS={};window.AUDIT_MESHES={};')
 (f.OUT/'零件与打印盘对照.csv').write_text((h.SRC/'零件与打印盘对照.csv').read_text(encoding='utf-8-sig').replace('_O22F5_PLA_fins.3mf','_O22F6_PLA_final.3mf'),encoding='utf-8-sig')
 exceptions=[r for r in rows if r['id']in f.RESTORE]
 exception_lines=[r['id']+' / '+', '.join(x['address']for x in r['instances'])+'：'+LOCATIONS[r['id']]for r in exceptions]
 lines=['O22F6 PLA 最终版','全部 14 盘已通过数字几何、原生网格及完整 G-code 悬空/承托检查。','检查记录日期：2026-10-15','', '范围：150 种零件，193 个实例（186 正式件 + 7 可选小样）。', '49 种保留清孔改动；16 种为恢复承托使用原 F5 支撑（共 18 个实例）。', '其余 85 种无需清孔改形。150 种永久本体均与 F5 完全一致。', 'F5 原文件和此前未放行候选均保留；请本次使用 projects/ 下文件名含 PLA_final 的 3MF。','', '打印：','1. 在 OrcaSlicer 中以项目打开 projects/Dxx_O22F6_PLA_final.3mf；14 个工程均含已核验 G-code。','2. 使用保存的 Bambu Lab A1 mini / 0.4 mm 喷嘴 / PLA 参数。D01、D02 层高 0.16 mm，其余 0.20 mm，首层均 0.20 mm。','3. 保持按层打印、原摆放、各对象专用参数及关闭自动支撑；必要的可拆支撑已经建模在文件里。','4. 本次检查对应保存的 193 个实例，包括 7 个已标注的可选小样。改动对象、朝向或参数并重新切片后，以新预览重新核对。','', '恢复孔位支撑的例外：','按照本次授权，以下 16 种保留 F5 孔内/孔口承托，不能视为打印后自动通孔。支撑与保护区的交叠包含微小边界，不代表每个列出的孔都会完全堵住。',*exception_lines,'', 'P095 特别说明：','D01-01 的 P095 恢复了原承托，下方四孔中的 H2、H4 仍须清理 T202、T203 细齿。', '在 index.html 选择 P095，打开本体半透明，可逐根显示 T202、T203；先从外侧断根，保持孔内段完整并按显示方向抽出。','这两个孔原先堵住与建模支撑有关；更换 PLA 本身不会移除这些支撑。','', '拆撑与安装：','打开 index.html 或双击“打开3D与安装说明.cmd”。蓝色保留，橙色鳍和黄色连接齿移除；网页颜色仅用于识别，实际同一种 PLA 打印。','冷却后扶住厚壁，从外侧剪断连接齿及挡住退出方向的齿根，按页面顺序拆鳍。孔内长细齿保持完整，避免剪碎留在孔中。','清理螺钉通道、沉孔和螺母位后再安装五金，保持原孔尺寸。详细位置和抽出方向见“打印与拆撑.html”。','安装顺序沿用附带的 assembly/tutorials/assembly-o22/index.html；D / C / A 编号对照保持。','', '核验结论与范围：','14/14 盘通过；悬空起印区 0，未解决外部悬空路径 0；自动生成支撑路径 0。','134 种未恢复孔位支撑的零件均无支撑实体进入螺钉/沉孔/螺母位保护区。','D05/P018、D11/P002 在 Z=15.40 mm 各有一处原始孔边路径告警：复核为 F5 已有的本体尖角加宽，路径距支撑约 0.53 mm；原始记录保留。','验证阈值沿用 F5，没有为本次放行放宽悬空筛查。上述均为数字检查，本批尚未实物试打。','verification/ 保存逐盘报告、逐件几何与孔位例外、原文件保全和构建来源；SHA256SUMS.txt 可核对文件完整性。']
 assert summary['restored_original_support_instances']==18
 (f.OUT/'先读我.txt').write_text('\n'.join(lines)+'\n',encoding='utf-8-sig')
 exc_rows=''.join('<tr><td><a href="index.html?id='+r['id']+'">'+r['id']+'</a></td><td>'+', '.join(x['address']for x in r['instances'])+'</td><td>'+html.escape(LOCATIONS[r['id']])+'</td></tr>'for r in exceptions)
 printing='<h1>O22F6 · PLA 打印与拆撑</h1><div class="ok">14 盘均已通过完整数字检查。使用 <b>PLA_final.3mf</b> 项目；150 种本体与 F5 完全一致。</div><h2>打印设置</h2><p>A1 mini · 0.4 mm 喷嘴 · PLA · 按层打印。D01、D02 为 0.16 mm，其余盘 0.20 mm，首层均 0.20 mm。保留项目内各对象参数、位置和朝向，自动支撑关闭，文件中已包含可拆支撑与已核验 G-code。</p><h2>先拆撑，再装五金</h2><ol><li>冷却后扶住厚壁。蓝色永久本体保留，橙色鳍与黄色连接齿移除；这些颜色仅供网页识别，打印只需同一种 PLA。</li><li>先从外侧剪断黄色连接齿，清除挡住退出方向的齿根，再按每件页面的顺序拆出橙色鳍。</li><li>孔腔长细齿先断根，保持孔内段完整，依图示方向整根抽出。交叉齿可能需额外剪开，避免剪碎后残留在孔道。</li><li>核对螺钉通道、沉孔和螺母位均已清理，保持原孔尺寸，再安装五金。</li></ol><div class="note"><b>P095 · D01-01：</b>为消除悬空，已恢复 F5 承托；下方四孔中的 H2、H4 仍需清理 <b>T202、T203</b>。<a href="index.html?id=P095">打开 P095 三维拆撑视图</a>，勾选“本体半透明”，在“孔腔细齿”中逐根显示，并按页面方向抽出。</div><h2>保留孔位支撑的 16 种零件</h2><p>共 18 个实例；P130 在三处盘位重复出现。表中列出需重点检查的区域，部分属于孔口微小边界交叠。</p><table><tr><th>零件</th><th>盘位</th><th>清理位置</th></tr>'+exc_rows+'</table><p><a href="assembly/tutorials/assembly-o22/index.html">打开 26 步安装图解</a> · <a href="零件与打印盘对照.csv">完整编号对照</a></p><p class="muted">全部结论来自数字检查，本批尚未实物试打。</p>'
 for name in ['p095_t202_fixed.png','p095_t203_fixed.png']:
  target=f.OUT/'verification/figures'/name;target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(h.R/'output/playwright'/name,target)
 printing+='<h2>P095 孔内细齿识别</h2><p>半透明蓝色是永久本体，黄色是单独显示的孔内细齿；这两张图隐藏了橙色支撑鳍。完整支撑和抽出顺序请打开上方三维视图。</p><figure><img style="width:100%;max-width:850px" src="verification/figures/p095_t202_fixed.png" alt="P095 T202 细齿位置"><figcaption>T202：先从外侧断根，再整根抽出。</figcaption></figure><figure><img style="width:100%;max-width:850px" src="verification/figures/p095_t203_fixed.png" alt="P095 T203 细齿位置"><figcaption>T203：保持孔内段完整，依三维视图所示方向退出。</figcaption></figure>'
 write(f.OUT/'打印与拆撑.html',page('O22F6 PLA 打印与拆撑',printing))
 pt=''.join('<tr><td>'+p['id']+'</td><td>'+str(p['objects'])+'</td><td>'+str(p['layer_height_mm'])+'</td><td>0 / 0</td><td>'+(', '.join(p['restored_support_type_ids'])or'无')+'</td><td><a href="'+p['project']+'">3MF</a> · <a href="verification/plates/'+p['id']+'/support_paths.json">检查</a></td></tr>'for p in prs)
 review='<h1>检查与允许的孔位支撑例外</h1><div class="ok"><b>14/14 盘通过。</b>150 种永久本体保持 F5 原样，网格连通与底部承托通过；最终 3MF 网格、PLA 参数与全盘 G-code 均已核对。</div><p>49 种保留清孔改动，16 种恢复原支撑。恢复范围由上一候选的悬空告警确定，按本次授权保留；未放宽 F5 的路径筛查阈值。</p><table><tr><th>盘</th><th>实例</th><th>层高 mm</th><th>悬空起印 / 未解决路径</th><th>恢复孔位支撑的零件</th><th>文件</th></tr>'+pt+'</table><h2>孔位检查的解释</h2><p>134 种未恢复支撑的零件在五金孔位保护区内没有支撑实体交叠。16 种例外详见<a href="打印与拆撑.html">拆撑清单</a>；全盘原始孔内路径报告仍记录这些实际存在的支撑，未改写为“全孔畅通”。</p><p>D05/P018、D11/P002 在 Z=15.40 mm 的两处小面积孔边告警已逐段复核：均为 F5 已有本体尖角的加宽路径，中心线距支撑约 0.53 mm。<a href="verification/body_edge_path_review.json">查看复核记录</a>。</p><h2>检查边界</h2><p>路径检查采用与 F5 相同的承托覆盖和桥接端点方法：未锚定/单端自由段超过 1 mm、双端自由段超过 3 mm 进入筛查，并单独检查悬空起印区。阈值用于数字筛查，本批未进行实物试打或材料下垂标定。</p><p><a href="verification/summary.json">完整汇总</a> · <a href="verification/F5_original_preservation.json">F5 原文件保全</a> · <a href="verification/support_subset_proof.json">支撑子集与拆除方向依据</a> · <a href="manifest.json">最终批次清单</a></p>'
 write(f.OUT/'检查与例外.html',page('O22F6 检查与例外',review))
 layouts=[]
 for p in manifest['plates']:
  rects=[]
  for it in p['items']:
   a=it['bounds_mm'];x,y,w0,h0=a[0],180-a[4],a[3]-a[0],a[4]-a[1];color='#e9b27b'if it['id']in f.RESTORE else'#b4d8cc';label=it['object_name'].split()[0]+' '+it['id'];rects.append(f'<g><title>{html.escape(label)}</title><rect x="{x:.3f}" y="{y:.3f}" width="{w0:.3f}" height="{h0:.3f}" fill="{color}" stroke="#527c72" stroke-width=".4"/><text x="{x+w0/2:.3f}" y="{y+h0/2:.3f}" font-size="3" text-anchor="middle">{html.escape(label)}</text></g>')
  svg='<svg viewBox="-3 -3 186 186" role="img" aria-label="'+p['id']+' 打印盘位置图"><rect x="0" y="0" width="180" height="180" fill="white" stroke="#527c72"/>'+''.join(rects)+'</svg>';links=' / '.join('<a href="index.html?id='+it['id']+'">'+html.escape(it['object_name'])+'</a>'for it in p['items']);layouts.append('<h2>'+p['id']+' · <a href="'+p['project']+'">打开 PLA 最终 3MF</a></h2>'+svg+'<p>'+links+'</p>')
 write(f.OUT/'合盘布局.html',page('O22F6 打印盘布局','<h1>14 盘 · D 系列布局</h1><p>位置与 F5 相同。图为 180 × 180 mm 平台上的对象包围框；橙色表示本版保留孔位支撑的零件。编号可打开对应三维拆撑视图。</p>'+''.join(layouts)))
 provenance=dict(source_manifest_sha256=h.sha(h.SRC/'manifest.json'),candidate_manifest_sha256=h.sha(f.CAND/'manifest.json'),staging_manifest_sha256=h.sha(f.WORK/'staging.json'),slicer='OrcaSlicer 2.4.2',scripts={name:h.sha(h.R/'scripts'/name)for name in ['o22f6_holeclear.py','o22f6_final.py','o22f6_deposited_holes.py','o22f6_final_viewer.py','o22f6_final_package.py','audit_revo22_f5_native271.py','verify_revo22_x062_endpoints256.py']})
 h.put(f.OUT/'verification/build_provenance.json',provenance)
 print('FINAL_RELEASE_FILES_READY',summary['status'],flush=True)

def archive_and_verify():
 m=json.loads((f.OUT/'manifest.json').read_text());assert m['complete']and m['status']=='RELEASED_DIGITAL_CHECKS_PASSED';assert len(list((f.OUT/'projects').glob('*.3mf')))==14
 with(f.OUT/'零件与打印盘对照.csv').open(encoding='utf-8-sig',newline='')as stream:csvrows=list(csv.DictReader(stream))
 assert len(csvrows)==193 and all((f.OUT/r['project']).exists()for r in csvrows)
 for p in m['plates']:
  assert h.sha(f.OUT/p['project'])==p['project_sha256'];r=json.loads((f.OUT/p['proof']).read_text());assert r['project_sha256']==p['project_sha256']and r['native_review_resolved']and r['scope_part_ids']is None
 files=sorted(p for p in f.OUT.rglob('*')if p.is_file()and p.name!='SHA256SUMS.txt');write(f.OUT/'SHA256SUMS.txt','\n'.join(h.sha(p)+'  '+p.relative_to(f.OUT).as_posix()for p in files)+'\n')
 path=h.B/'O22F6_PLA_最终版_20261015.zip'
 with zipfile.ZipFile(path,'w',zipfile.ZIP_DEFLATED,compresslevel=6)as z:
  for p in sorted(q for q in f.OUT.rglob('*')if q.is_file()):z.write(p,f.OUT.name+'/'+p.relative_to(f.OUT).as_posix())
 checked=0
 with zipfile.ZipFile(path)as z:
  assert z.testzip()is None
  for line in(f.OUT/'SHA256SUMS.txt').read_text().splitlines():
   digest,name=line.split('  ',1);assert hashlib.sha256(z.read(f.OUT.name+'/'+name)).hexdigest()==digest==h.sha(f.OUT/name),name;checked+=1
  assert len(z.namelist())==checked+1
 result=dict(path=str(path),bytes=path.stat().st_size,sha256=h.sha(path),files_verified=checked,plate_projects=14,type_npz=150,csv_rows=193,all_csv_project_links_exist=True,all_final_native_checks_bound_to_delivered_hashes=True,complete=True,status=m['status']);h.put(f.WORK/'delivery_integrity.json',result);print(json.dumps(result,ensure_ascii=False),flush=True)

if __name__=='__main__':
 action=sys.argv[1]if len(sys.argv)>1 else'package'
 if action=='review':edge_review()
 elif action=='package':package()
 elif action=='archive':archive_and_verify()