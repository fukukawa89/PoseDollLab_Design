from deliver_stock import *

def run():
 inventory();tutorial();preview()
 kit=load(OUT/'kit.json');review=load(OUT/'verification/merge_review.json');env=load(OUT/'envelope.json');plates=load(OUT/'printing/plates.json')['plates'];targets=load(OUT/'verification/holding_targets.json')['rows'];steps=load(OUT/'tutorial/steps.json')
 links='<p><a href="START_HERE.html">入口</a> · <a href="MERGE_REVIEW.html">分件审查</a> · <a href="PRINTING.html">重打清单</a> · <a href="HARDWARE.html">五金</a> · <a href="assembly_guide/index.html">逐步动画</a> · <a href="preview/index.html">整臂三维</a></p>'
 def pg(file,title,body):page(file,title,links+body)
 body='<div class="box"><b>R2 → R3：只需新打印 S4-P010 一体腕叉手掌。</b><br>替代旧 S2-P010 手掌＋S2-P011 腕输出叉；其余10个R2打印件均逐字节复用。整臂减为11个打印件、130件标准五金，无新增五金规格。</div>'
 body+='<p>合并固定件的思路成立，但仍要保留装入五金所必需的盖。当前教程中 P004 配 P001 压盖，P002 则配 P006。三只压盖在使用时固定，在装配时必须打开让18 mm防脱大垫进入，不能直接封死。</p>'
 body+='<div class="grid">'+''.join(f'<div class="card"><a href="{url}"><b>{title}</b></a><p>{note}</p></div>' for url,title,note in [('MERGE_REVIEW.html','哪些可以合并','四组固定连接逐一审查与阻挡对照'),('PRINTING.html','只重打一件','单件升级3MF与整臂11件3MF分别提供'),('assembly_guide/index.html','新版逐步安装动画','不再包含单独套掌部和掌部螺钉步骤'),('preview/index.html','检查新整臂','七轴、原活动范围和电子预留开关')])+'</div>'
 body+=f'<p>名义网格估算质量 {env["estimated_mass_g"]:.2f} g。原7个自由度、骨轴、骨长、A字姿态和活动范围保持不变。H/W已接受状态继续保留；本轮是固定接口的合并，不要求先重测H/W。</p><img src="images/arm.png" alt="R3一体掌部的完整单臂">'
 body+='<p><a href="O24E_left_arm_stock_R4.blend">可编辑Blender</a> · <a href="O24E_left_arm_stock_R4.glb">GLB</a> · <a href="HARDWARE_REUSE_BUY.csv">复用与补购表</a></p><div class="box warn">已完成计算几何、装配和离线切片检查。打印实物的保持力、装配公差、强度、蠕变与循环寿命尚未实测。电子附件仍处于空间预留阶段，不计入本次物料。</div>'
 pg('START_HERE.html','O24E R3 · 固定分件合并版',body)
 body='<p>固定连接不一定需要永久分件；判断依据还包括五金如何装入、捕获、防松，以及是否需要拆卸维护。本次把R2所有处于同一运动坐标系的打印件分组检查，共4组。不同运动坐标系之间仍承担7个自由度，不做焊死式合并。</p>'
 body+=table(['R2配对','装后相对运动','决定','具体原因'],[('P001＋P004','无','保留分体','肩俯仰盖最后捕获18 mm大垫；盖孔只有16.4 mm。'),('P002＋P006','无','保留分体','上臂旋转盖同样是五金装入口及双向防脱挡止。'),('P003＋P008','无','保留分体','前臂旋转盖同理，宽孔距用于避开肘叉并装入标准螺钉。'),('P010＋P011','无','合并为S4-P010','没有内部被困五金；整件可沿原腕叉路径装入，掌部方键与4件固定五金均可取消。')])
 body+='<h2>用实际几何复核压盖</h2>'+table(['模块','盖打开时大垫装入最大重叠/mm³','假设盖与座合并后的最大重叠/mm³'],[(r['old_parts'][0]+' / '+r['old_parts'][1],f'{r["cover_removed_washer_entry_max_overlap_mm3"]:.5f}',f'{r["fused_cover_washer_entry_max_overlap_mm3"]:.2f}') for r in review['reviewed_fixed_pairs'][:3]])
 body+='<p>因此“不转动”并不是这三只盖多余的证据。改成侧装大垫仍需设计能恢复挡止的封口；暂停打印埋入五金会改变制造和维修方式，且不再是当前可拆装的试装流程。本版保留已验证的盖与双螺钉锁固。</p>'
 body+='<h2>一体手腕的处理</h2><img src="images/unified_hand.png" alt="S4-P010一体腕叉手掌"><p>重建掌部连接为连续渐变截面，填实旧方键间隙及横穿钉区域，去掉无用锁母凸座。保留掌纹、手背标记、拇指轮廓、R2加粗腕叉、两个摩擦耳和侧面磁铁座。没有简单把两个互不相连的网格放进同一个STL。</p>'
 body+='<p>整件重新通过腕中心装入路径、四侧内层五金先装的顺序、7轴850个运动采样及电子刚体预留检查；磁铁从原+Y入口仍可装入。两个原件不能再单独更换，今后若一体件损坏需要更换整件；本次机械试装可因此省去1个打印件和4件五金。</p><p><a href="verification/merge_review.json">审查数据</a> · <a href="verification/hinge_wrist_paths.json">H/W装入验证</a> · <a href="verification/motion_dense.json">活动范围验证</a></p>'
 pg('MERGE_REVIEW.html','R3 · 固定分件逐组审查',body)
 rows=[]
 for p in kit['structural_parts']:
  old=p.get('source_r2_print');rows.append(dict(new_part=p['part_number'],old_parts=old or 'S2-P010 + S2-P011',action='直接复用R2实物；无需重打' if old else '新打印1件，替代原来2件',stl=p['stl'],sha256=p['sha256'],byte_identical_to_R2=bool(old)))
 csvfile('REPRINT_AND_REUSE.csv',list(rows[0]),rows)
 body='<div class="box"><b>已经按R2打印过：只打印 S4-P010，1件。</b><br>未开始打印：使用整臂11件工程。两种工程是替代选项，不需要都打印。编号保留原槽位：P011已撤销，P012不改号。</div>'
 body+=table(['用途','原生3MF','件数','离线切片'],[(('仅升级R2' if p['replacement'] else '从零打印整臂'),f'<a href="{p["file"]}">{p["id"]}</a>',p['count'],f'<a href="verification/slice_{p["id"]}.json">通过／零网格修复</a>') for p in plates])
 body+=table(['R3件号','原R2件号','处理','生产文件'],[(r['new_part'],r['old_parts'],r['action'],f'<a href="{r["stl"]}">STL</a>') for r in rows])
 body+='<p><a href="REPRINT_AND_REUSE.csv">逐件重打／复用清单</a>。复用结论以R2为基准；R1旧叉与骨杆不自动视为R2同件。打印参数沿用0.4 mm喷嘴、PLA、0.12 mm层高、5壁、100%填充、自动支撑、3 mm裙边。不要整体缩放修配孔径。新件清理重点仍为腕叉摩擦耳孔和磁铁入口。</p>'
 pg('PRINTING.html','R3 · 只需重打印一件',body)
 bom=load(OUT/'BOM_totals.json');body='<div class="box">130件标准五金；相对R2减少 M2×20螺钉1颗、W2平垫2片、NL2锁母1颗。减少的4件保存作备件，不再装到一体手掌。若继续使用旧R2的分体手掌，仍须保留原4件固定五金。其他五金位置、规格、预紧与锁固均保持。</div>'
 body+=table(['规格','需求','尺寸','来源'],[(r['sku'],r['required'],r['spec'],r['reuse_source']) for r in bom['rows']])
 body+='<p>历史O22/T6清单不等于现有库存。仍优先复用合格同规格件；NL3不可用普通螺母代替，W3必须是7×3.2×0.5，W6L必须是18×6.4×1.5。A8外形一致不代表弹力已测。</p><p><a href="HARDWARE_REUSE_BUY.csv">需求／库存填写表</a> · <a href="HARDWARE_DETAIL.csv">逐件五金位置</a></p>'
 pg('HARDWARE.html','R3 · 五金复用与减少项',body)
 body='<div class="box">先分别装好RP、RU、RF，再连接肩、肘、腕。腕中心先备齐四侧内五金，再从远端放入一体腕叉手掌。取消原“套手掌”和掌部M2固定步骤；四组腕肩钉仍各自调节预紧。</div><p><a href="assembly_guide/index.html">打开新版逐步动画与零件朝向放大</a></p>'
 for m in steps['modules']:body+='<details><summary>'+m['label']+f' · {len(m["steps"])}步</summary>'+table(['步','件号／动作','操作'],[(s['number'],', '.join(s['part_numbers'])+'<br>'+esc(s['title']),esc(s['note'])) for s in m['steps']])+'</details>'
 pg('ASSEMBLY.html','R3 · 装配教程',body)
 body='<p>已接受的T6 H/W状态保留。以下记录针对整只单臂的打印配合与实际效果，不是开工前再次验收H/W。新一体件应先检查摩擦耳、叉根、渐变掌颈与磁铁口的支撑清理。</p>'
 body+=table(['轴','范围/°','保持目标/N·m'],[(r['label'],str(r['limits_deg']),f'{r["hold_target_Nm"]:.4f}') for r in targets])
 body+='<ol><li>按动画低预紧装配，检查三只盖及其捕获大垫；腕部四个肩钉分别经过尼龙锁固段。</li><li>走完七轴范围并观察一体掌部是否碰擦、卡点或串动。</li><li>按原R2试装方式记录轴向间隙、保持力、60秒角漂和0/10/20/50/100次循环；保留补紧和磨屑记录。</li></ol><p>力矩目标由本版质量和既有假设计算，不是螺钉拧紧扭矩，也不是已测能力。A8弹力、摩擦系数、打印各向异性、蠕变及疲劳仍未实测。</p><p><a href="verification/holding_targets.json">保持目标计算</a> · <a href="TRIAL_LOG.csv">空白实装记录</a></p>'
 pg('TEST_PLAN.html','R3 · 单臂试装记录',body)
 csvfile('TRIAL_LOG.csv',['axis','label','cycles','date','fit_notes','hold_plus_Nm','hold_minus_Nm','drift_60s_deg','axial_play_mm','retightened','result'],[dict(axis=a['id'],label=a['label'],cycles=n) for a in PROFILE['axes'] for n in [0,10,20,50,100]])
 body='<p>本轮合并保留原腕角链、磁铁入口和6组传感器的空间预留；一体手掌与原腕输出叉使用同一坐标系。电子刚体包络已针对R3再次检查。动态线束、电子支架、磁铁锁盖和角度标定仍未发布生产版，不需要安装它们来进行本次机械测试。</p><p>走线约束沿用6根AWG30、束径预留3.5 mm、动态弯曲半径至少10 mm；避开承压层、摩擦堆叠、捕获环唇和调节工具孔。腕板固定前臂，磁铁随一体掌部转动，角链仍为Ry(屈伸)·Rx(偏摆)。</p><p><a href="electronics/interface_reservations.json">预留坐标／板型／检查范围</a> · <a href="electronics/reserved_layout.glb">预留模型GLB</a></p>'
 pg('ELECTRONICS_RESERVATION.html','R3 · 电子预留继承',body)
 # Viewer uses the exact mechanical meshes; optional electronic reservation bodies stay outside trial inventory.
 p=OUT/'preview/data.js';d=json.loads(p.read_text('utf8').removeprefix('window.O24D=').removesuffix(';'));raw=bytearray(base64.b64decode(d['geometry']));cursor=len(raw)//24;z=np.load(OUT/'electronics/reserved_meshes.npz')
 for q in load(OUT/'electronics/reserved_parts.json'):
  i=str(q['i']);v=z[i+'v'];f=z[i+'f'];m=trimesh.Trimesh(v,f,process=False);ar=np.concatenate([v[f],np.repeat(m.face_normals[:,None,:],3,axis=1)],axis=2).reshape(-1,6).astype('<f4');d['parts'].append(dict(name=q['name'],frame=q['frame'],role=q['role'],source_features=['electronics','reserved'],reservation=True,bounds_mm=m.bounds.tolist(),color=[.15,.65,.4] if q['role']=='pcb' else [.85,.2,.15],first=cursor,count=len(ar)));cursor+=len(ar);raw.extend(ar.tobytes())
 d.update(geometry=base64.b64encode(raw).decode(),mechanical_count=141,reservation_count=12);p.write_text('window.O24D='+json.dumps(d,ensure_ascii=False,separators=(',',':'))+';',encoding='utf8')
 p=OUT/'preview/viewer.js';s=p.read_text('utf8').replace('function selected(p){','function selected(p){if(p.reservation&&!$(\'#electronics-reserved\').checked)return false;').replace("if(!$('#hardware').checked&&!['structure','rotor','shell'].includes(p.role))continue;","if(!p.reservation&&!$('#hardware').checked&&!['structure','rotor','shell'].includes(p.role))continue;").replace("$('#parts').textContent=D.parts.length;","$('#parts').textContent=D.mechanical_count;").replace("['bones','helpers','hardware','shell','harness']","['bones','helpers','hardware','shell','harness','electronics-reserved']").replace('显示 ${visible} / ${D.parts.length} 个机械实物件 · mm','显示 ${visible} 件 · 机械141件，另有12个可选电子包络 · mm');p.write_text(s,encoding='utf8')
 p=OUT/'preview/index.html';s=p.read_text('utf8').replace('O24E · 常见五金左臂试装','O24E R3 · 固定分件合并版').replace('<strong>12</strong>','<strong>11</strong>').replace('优先复用 O22 / T6 常见五金；零金属定制、零切短。无电路。','P010＋P011合并为S4-P010。其余10个R2打印件可复用；减少4件掌部五金。').replace('<div class="checks">','<div class="checks"><label><input type="checkbox" id="electronics-reserved"> 电子空间预留（附件未发布）</label>').replace('<a href="../START_HERE.html">','<a href="../MERGE_REVIEW.html">固定分件审查</a><a href="../assembly_guide/index.html">新版逐步动画</a><a href="../START_HERE.html">');p.write_text(s,encoding='utf8')
 print('R3 DOCS',steps['steps'],'base steps; 11 prints / 130 hardware; upgrade only S4-P010',flush=True)
if __name__=='__main__':run()
