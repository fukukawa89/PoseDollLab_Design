"""Freeze a reviewable prototype batch, not a manufacturing qualification."""
from common import *
import shutil,zipfile,datetime
PAGE=H/'tutorials/full-doll-o15'

def check_hashes(d):
 for p,h in d.items():
  assert sha(p)==h,('STALE',p)

def final_firmware():
 old=read(OUT/'firmware_builds.json');d={**old,'prior_report_sha256':sha(OUT/'firmware_builds.json'),'build_wrapper_rechecked':True};d['sources_sha256']={p:sha(R/p) for p in old['sources_sha256']}
 for r in d['roles']:
  root=Path(r['build_directory']);r['artifact_sha256']={p:sha(root/p) for p in r['artifact_sha256']};log=OUT/('build_wrapper_'+r['role']+'.log');assert 'Project build complete' in log.read_text(encoding='utf8');r['build_log_sha256']=sha(log);r['build_log']=str(log)
 save('firmware_builds_final.json',d)

def main():
 manifest=read(OUT/'print_batch_manifest.json');slicing=read(OUT/'print_slicing/report.json');assert len(manifest['rows'])==242;check_hashes(manifest['input_sha256']);assert slicing['status']=='GEOMETRIC_DIAGNOSTIC_PASS' and not slicing['failures'];assert slicing['manifest_sha256']==sha(OUT/'print_batch_manifest.json')
 for r in manifest['rows']:
  assert r['bed']['components']==1 and r['bed']['flat_contact_area_mm2']>.25;assert sha(H/r['stl'])==r['stl_sha256']
 for c in ('quinn','manny'):
  d=read(OUT/f'harness/{c}_final_audit.json');assert d['status']=='SAMPLED_STRUCTURE_CLEAR' and not d['hard_findings'];assert d['raw_report_sha256']==sha(OUT/f'harness/{c}_complete_tail_audit.json');check_hashes(d['input_sha256'])
 e=read(OUT/'electronics_export.json')
 for b in e['boards']:
  assert b['erc_violations']==b['drc_violations']==b['unconnected']==0;check_hashes(b['source_sha256'])
  for name,h in b['output_sha256'].items():assert sha(BENCH/'electronics'/b['board']/name)==h
 check_hashes(read(OUT/'load_budget.json')['input_sha256']);check_hashes(read(OUT/'procurement.json')['source_sha256']);assert read(OUT/'ue_bridge_result.json')['passed'];assert '64 passed' in (OUT/'bridge_test.log').read_text(encoding='utf8');assert all(x['conditional_budget_ok'] for c in read(OUT/'harness/cut_and_binding_plan.json')['characters'] for x in c['power_results'])
 final_firmware();ref=read(OUT/'reference_deviations.json');loads=read(OUT/'load_budget.json');proc=read(OUT/'procurement.json');counts={c:{'types':sum(r['quantity_by_character'][c]>0 for r in manifest['rows']),'pieces':sum(r['quantity_by_character'][c] for r in manifest['rows'])} for c in ('quinn','manny')}
 summary={'status':'DIGITAL_PROTOTYPE_BATCH_READY_FOR_PHYSICAL_VALIDATION','run':'o15_20260929_r1','requirements':{'height_reference_mm':480,'backup_910mm_preserved':True,'capture':'static pose','mass_hard_cap':None,'manual_support_allowed':True,'custom_machined_metal_required':False},'characters':[{'character':c,'print':counts[c],'mass_budget_kg':next(r['modeled_mass_kg'] for r in loads['characters'] if r['character']==c),'worst_sample_gravity_Nm':max(abs(r['gravity_torque_Nm']) for r in next(x['worst_sample_per_raw_axis'] for x in loads['characters'] if x['character']==c)),'maximum_semantic_endpoint_deviation_mm':next(r['maximum_endpoint_error_mm'] for r in ref['characters'] if r['character']==c),'maximum_axis_origin_deviation_mm':next(r['maximum_axis_origin_error_mm'] for r in ref['characters'] if r['character']==c)} for c in ('quinn','manny')],'checks':{'unique_STL_generic_slices':242,'equipment_and_rigid_tail_cases_each':689,'fine_raw_motion_steps_each':416,'electronic_native_ERC_DRC':'both boards zero violations/unconnected','firmware':'BODY and G0 build pass; no physical flash','bridge_tests':64,'real_UE_test':'synthetic raw46 -> production BridgeCore -> UE; normal capture1, missing/CRC/reboot capture0'},'deferred_to_one_physical_batch':['actual FDM strength, preload, creep, wear and retention','full-body hand/tool access and assembly tolerances','flexible moving-wire route, pull force, fatigue and service loops','supply transients, thermal rise, SPI/wireless waveforms and ESD robustness','all46 measured zeros, signs, magnet accuracy, discontinuity and lost-chain recovery'],'continuous_collision_proof':False,'hardware_tests_fabricated':False,'numeric_proportion_acceptance_user_approved':False}
 save('FINAL_BATCH_SUMMARY.json',summary);(BENCH/'FINAL_BATCH_SUMMARY.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
 # Web guide is usable offline; no fetch, external code or remote font.
 shutil.copyfile(PAGE/'guide.html',BENCH/'guide.html');shutil.copyfile(PAGE/'style.css',BENCH/'style.css');g=(BENCH/'guide.html').read_text(encoding='utf8').replace('href="index.html"','href="http://127.0.0.1:8769/tutorials/full-doll-o15/index.html"');(BENCH/'guide.html').write_text(g,encoding='utf8')
 (BENCH/'README.zh-CN.md').write_text('''# PoseDoll O15：整机统一测试包

先打开 guide.html（离线可读），再按一种体型的清单下单。默认 Quinn，Manny 为备选，不要两套一起买。

- 每套273件打印件，含外置网关盒与焊接间距块；214种该体型使用的文件。
- print_batch：已摆放的STL与仅含几何的3MF。没有可直接上机的G-code；服务商按PETG/0.4喷嘴/0.2层高/6壁/100%填充重新切片并保留要求的支撑。
- PRINT_QUINN / PRINT_MANNY：对应体型的数量与用途。不要仅凭文件个数估算数量。
- PROCUREMENT_QUINN / PROCUREMENT_MANNY：现成金属、磁铁、电子件净数量与可选备件；另读线束和工具要求。
- electronics：中央采集板与传感小板的Gerber、钻孔、BOM、贴片坐标和加工说明。
- harness：逐段线长、6条链、46个节点及线色。由线束厂制作和测试0.5mm接口短尾线；软线服务环仍需实物整理。
- commissioning：空白实测标定模板、CAD角度参考、配对说明。默认MAC未配对，空白标定不能启用正式捕捉。
- evidence：实际数字检查结果及边界；不是制造合格证。

查看器：http://127.0.0.1:8769/tutorials/full-doll-o15/index.html

已完成数字样机与一次性实物验证的准备；强度、摩擦、耐久、完整手工装配和带线性能等待这批样机实测。允许手托，整机不设1.2kg硬门槛。打印和采购后按guide.html顺序集中记录，不把缺失、故障或未标定读数当作有效姿势。
''',encoding='utf8')
 for char in ('quinn','manny'):
  lines=['# '+char.title()+' 打印数量','', '只打印本表列出的编号；单位mm，数量为净数量。','', '| 编号 | 数量 | 需要支撑 | 对应部位 |','|---|---:|---|---|']
  for r in manifest['rows']:
   q=r['quantity_by_character'][char]
   if q:lines.append('| '+r['id']+' | '+str(q)+' | '+('是' if r['bed']['supports_required'] else '按实际切片复核')+' | '+'、'.join(x['part'] for x in r['instances'] if x['character']==char)+' |')
  (BENCH/f'PRINT_{char.upper()}.zh-CN.md').write_text('\n'.join(lines)+'\n',encoding='utf8')
  lines=['# '+char.title()+' 采购数量','', '现有小样能复用的标准金属件可扣除。塑料件按整机编号，不混用旧底座。','', '| 规格 | 净数量 | 可选备件 | 建议总数 |','|---|---:|---:|---:|']
  for r in next(x['rows'] for x in proc['characters'] if x['character']==char):lines.append('| '+r['name_zh']+' | '+str(r['net_quantity'])+' | '+str(r['optional_spares'])+' | '+str(r['suggested_total'])+' |')
  lines+=['','另外准备：24AWG电源主线、26AWG的GH插头短线、30AWG信号、32AWG局部引线；长度见harness。工具、绑线带、绝缘、标签、USB数据线和PCBA/线束加工服务见guide.html。没有定制金属加工件。','GH端子必须SSHL-002T-P0.2，不能用SHL系列端子替代；压接端使用26–30AWG、绝缘外径0.76–1.0mm，24AWG只能在插头外转接。']
  (BENCH/f'PROCUREMENT_{char.upper()}.zh-CN.md').write_text('\n'.join(lines)+'\n',encoding='utf8')
 # Record sheet has no automatic pass flags.
 template={'schema':'O15-BATCH-RECORD/1','batch':None,'material':None,'printer':None,'character':None,'rows':[{'item':x,'result':None,'evidence':None} for x in summary['deferred_to_one_physical_batch']]};(BENCH/'PHYSICAL_TEST_RECORD_BLANK.json').write_text(json.dumps(template,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
 docs=H/'docs/REVIEW_REQUEST_REVO15.zh-CN.md';docs.write_text('''# O15 完整数字样机与统一实物批次审查

用户要求：按现有试用件正常可用的条件继续整机设计；不在每个硬件测试点停下；最后一次交付全部采购/打印资料。仍不把条件假设记成实测通过。480mm参考，910mm备用不变；静态采集；无1.2kg硬门槛；允许手托；优先家用FDM+现成金属小件。

入口：cad/revO15/WORK.md、generated/revO15/runs/o15_20260929_r1/FINAL_BATCH_SUMMARY.json、bench/revO15/guide.html、tutorials/full-doll-o15/。本轮尚未额外提交commit；请以随后提交的工作树内容审查。

本轮包括全身关节/实体连接架/头手足/背部控制盒和电池盒、46个编码器、6条静态采集链、一块中央BODY载板+外置G0、固件与生产桥接器、打印与电子加工资料。每个体型273件打印件，214种文件；两型合计242种几何。

实际检查：局部装配/PCB保持几何；原始关联附件与最终连接架416步原始角度路径；新增设备和全部刚性FFC尾线各689个离散工况；原生KiCad ERC/DRC及连通性；BODY/G0构建；64项桥接测试；真实UE接收合成PDG15经生产桥接的正常/缺失/CRC/boot反例；242个STL真实通用切片、支撑底层凸包与逐层挤出重心检查。范围和哈希在对应报告中，不能据此宣称连续扫掠/强度/疲劳已证明。

请重点审查：
1. 多轴与全身手工装配路径、工具可达性、打印层方向和最薄受力截面。局部几何连通不能代替完整结构强度；最终控制盒盖加大螺母柱上段、GH插头按原厂8.75mm宽度修正。
2. 原因明确的FFC让位槽：Quinn最大切除约0.58%；Manny前臂的两个亚层厚度碎屑移除并记录，不是删掉受力零件。尾线与自身绝缘转换包封的2.45mm³重叠是同一实物两个包络，所有31694条原始见证保留并明确归类，没有忽略两个独立硬件的碰撞。
3. 柔性导线仍无力学/疲劳/连续碰撞证明。长度由689个端点跨度+服务环余量计算；24AWG电源连续分支、26AWG短引线转GH，30AWG信号，32AWG局部尾线。实际绕法、夹线和手感留同批实测。
4. 中央C1原生ERC/DRC为0，但尚无供电瞬态、热、SPI、ESD/RF实测。最远端条件预算仅约42mV余量；电阻和电流是假设边界，实际不能越过3.0V最低供电。
5. 保持力/回差/材料蠕变/疲劳均未测。质量约1.65–1.67kg是逐件+线束预算，用户允许手托；不得靠加大预紧掩盖承压问题。
6. 46原始量合成41测量语义+3固定骨盆，6链同一个物理BODY失效域；静态窗口保留数据完整性与新鲜度，不是恢复旧60Hz指标。MAC默认未配对，标定表为空；缺失/故障不允许保存。
7. UE语义端点与真实外形不同。参考末端最大偏差约16mm，轴心最大偏差约53mm；没有用户批准的数值容差，不得宣称骨架位置完全一致。

制造验收和完整实物功能仍未放行。现在交付的是完整数字样机和统一试制/验证批次，不是已经做好的实体人偶。
''',encoding='utf8')
 chosen=['FINAL_BATCH_SUMMARY.json','print_batch_manifest.json','print_slicing/report.json','reference_deviations.json','load_budget.json','load_kinematics_validation.json','electronics_export.json','firmware_builds_final.json','ue_bridge_result.json','module_validation.json','pcb_retention.json','assembly_order_checks.json','raw46_wiring_candidate.json','raw46_mapping_candidate.json','harness/cut_and_binding_plan.json']
 chosen += [f'harness/{c}_{suffix}.json' for c in ('quinn','manny') for suffix in ('final_audit','complete_tail_audit','tails_final','frame_reliefs')]
 evidence={str(OUT/n):sha(OUT/n) for n in chosen};seal={'status':summary['status'],'reports_sha256':evidence,'source_sha256':{str(p):sha(p) for p in Path(__file__).parent.glob('*.py')},'physical_validation_pending':True};save('FINAL_EVIDENCE_INDEX.json',seal)
 for char in ('quinn','manny'):
  dst=BENCH/f'PoseDoll_O15_{char.title()}_Prototype.zip'
  with zipfile.ZipFile(dst,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
   files={}
   def add(src,name):assert src.exists(),src;files[name]=sha(src);z.write(src,name)
   for name in ['README.zh-CN.md','guide.html','style.css','FINAL_BATCH_SUMMARY.json','PHYSICAL_TEST_RECORD_BLANK.json',f'PRINT_{char.upper()}.zh-CN.md',f'PROCUREMENT_{char.upper()}.zh-CN.md']:add(BENCH/name,name)
   add(docs,'REVIEW_REQUEST_REVO15.zh-CN.md')
   for r in manifest['rows']:
    if r['quantity_by_character'][char]:
     for ext in ('stl','3mf'):add(BENCH/'print_batch'/(r['id']+'.'+ext),'print_batch/'+r['id']+'.'+ext)
   subset={**manifest,'selected_character':char,'rows':[r for r in manifest['rows'] if r['quantity_by_character'][char]],'instances':[r for r in manifest['instances'] if r['character']==char]};z.writestr('print_batch/manifest.json',json.dumps(subset,ensure_ascii=False,indent=2))
   for folder in ('electronics','harness','commissioning'):
    for p in (BENCH/folder).rglob('*'):
     if p.is_file():add(p,p.relative_to(BENCH).as_posix())
   for n in chosen:add(OUT/n,'evidence/'+n)
   add(OUT/'FINAL_EVIDENCE_INDEX.json','evidence/FINAL_EVIDENCE_INDEX.json')
   fw=R/'Firmware/PoseDollFullBody/revO15'
   for p in fw.rglob('*'):
    if p.is_file() and '.local' not in p.relative_to(fw).parts and p.suffix in ('.c','.h','.ps1','.txt','.defaults','.projbuild'):add(p,'firmware_source/'+p.relative_to(fw).as_posix())
   z.writestr('PACKAGE_SHA256.json',json.dumps(files,ensure_ascii=False,indent=2))
  with zipfile.ZipFile(dst) as z:assert z.testzip() is None;assert not any(n.endswith('.gcode') for n in z.namelist())
  print('PACKAGE',char,dst.stat().st_size,sha(dst),flush=True)
 print('FINAL DIGITAL BATCH READY',counts,flush=True)
if __name__=='__main__':main()
