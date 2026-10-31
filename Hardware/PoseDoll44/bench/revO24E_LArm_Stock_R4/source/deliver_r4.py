from deliver_stock import inventory,preview,page,table,csvfile,esc
from build_stock import *
import base64,shutil,re

def run():
    inventory();kit=load(OUT/'kit.json');review=load(OUT/'verification/assembly_usability.json');guide=load(OUT/'assembly_guide/steps.json');plates=load(OUT/'printing/plates.json')['plates'];tools=load(OUT/'tooling/kit.json')['parts'];bom=load(OUT/'BOM_totals.json')
    # Assembly is offered exclusively in the new tool-aware player. The older
    # whole-arm preview cannot represent different offsets within a pin transfer.
    put(OUT/'tutorial/steps.json',dict(modules=[],steps=0,covered_part_numbers=[],assembly_angles={a['id']:0 for a in PROFILE['axes']},scope='Use assembly_guide/index.html for the authoritative 201-step tool-aware sequence.'))
    preview()
    links='<p><a href="START_HERE.html">入口</a> · <a href="ASSEMBLY_REVIEW.html">问题与修改</a> · <a href="PRINTING.html">重打清单</a> · <a href="HARDWARE.html">五金／工具</a> · <a href="assembly_guide/index.html">201步动画</a> · <a href="preview/index.html">整臂三维</a></p>'
    def pg(file,title,body):page(file,title,links+body)
    changed={'S4-P005':'肩外展内FW4座新增临时定位筋；RP采用托叉预装顺序','S4-P007':'肘内FW4座新增临时定位筋；RU采用托叉预装顺序','S4-P012':'双轴腕四侧内FW4座新增临时定位筋'}
    rows=[]
    for p in kit['structural_parts']:
        reused=bool(p.get('source_r2_print'));rows.append(dict(new_part=p['part_number'],R3_part=p['part_number'].replace('S4-','S3-'),action='直接复用，无需重打' if reused else '替换重打1件',reason='STL逐字节相同' if reused else changed[p['part_number']],stl=p['stl'],sha256=p['sha256'],installed_in_arm=True))
    for t in tools:rows.append(dict(new_part=t['part_number'],R3_part='',action='新打印1件工装，三模块重复使用',reason=t['kit_label'],stl=t['stl'],sha256=t['sha256'],installed_in_arm=False))
    csvfile('REPRINT_AND_REUSE.csv',list(rows[0]),rows);csvfile('TOOLING.csv',list(tools[0]),tools)
    body='<div class="box"><b>R3 → R4：替换重打 P005、P007、P012 各1件；另打印 J001托叉、J002导向针各1件。</b><br>其余8个R3打印件直接复用，包括P001/P002/P003压盖和一体P010。整臂仍为11件打印件，另有2件可重复使用的临时工装；136件五金。</div>'
    body+='<p>本版针对实装反馈：压盖使用普通M3对顶锁固；旋转模块在裸转子状态先捕获金属堆叠再合座；肩、肘和腕的内层五金先用定位筋留住再合叉。所有步骤明确由什么承托，避免在小窗口里徒手悬放散片。</p>'
    body+='<div class="grid">'+''.join(f'<div class="card"><a href="{u}"><b>{t}</b></a><p>{n}</p></div>' for u,t,n in [('printing/R4_REPRINT_3_PLUS_2.3mf','已有R3：只打印这5件','3件替换零件＋2件工装，同一打印盘'),('assembly_guide/index.html','新的201步安装动画','包含托叉、导向针、支承方式和8处定位保持检查'),('ASSEMBLY_REVIEW.html','两类问题的全臂审查','三只压盖、三组旋转预紧、八侧肩肘腕内层'),('HARDWARE.html','补齐12颗普通M3','复用O22常见件；不新增定制或切短五金')])+'</div>'
    body+='<img src="images/arm.png" alt="R4完整七轴单臂"><p><a href="O24E_left_arm_stock_R4.blend">Blender可编辑整臂</a> · <a href="O24E_left_arm_stock_R4.glb">GLB整臂</a> · <a href="REPRINT_AND_REUSE.csv">重打与复用表</a></p><div class="box warn">计算几何、工具空间与离线切片已检查。新定位筋的实际压入／留片效果、双螺母锁固保持及整体手感仍需实装确认；动画不是实际操作成功的录像。已接受的T6 H/W状态继续保留，不作为重新开工的前置测试。电子附件仍为预留。</div>'
    pg('START_HERE.html','O24E R4 · 可操作装配修订',body)
    body='<p>两点反馈都成立。R3把所有NL3一律禁止替换的说明过宽；压盖固定件与运动关节的预紧件可以采用不同锁固方式。R3的逐件路径也只说明零件几何能够经过，没有充分说明散片在这一过程中由谁承托。</p>'
    body+=table(['范围','发现的问题','本版处理'],[('P001/P004、P002/P006、P003/P008','固定压盖的NL3旋入阻力大','现有M3×16反向安装；头放旧六角窝，背面W3＋2颗普通M3对顶。压盖打印件不改。'),('P005、P007、P009的旋转预紧堆叠','小侧窗内无法用指尖逐片托住','外部托叉预排，整组侧入，正面导向针定位，轴向肩钉顶出针并捕获，抽出托叉后再预紧、合座。'),('肩外展和肘，合计4侧','翻面、合叉时内层散件容易掉','P005/P007每侧增加3处FW4外圆定位筋；不改变摩擦承压面。'),('双轴腕中心，4侧','四面都预排散片后合叉不可靠','P012四面同样增加定位筋；每一面轻翻转不掉片后才换面。'),('肩、肘、腕8组外预紧','在关节耳上逐片叠小件不便','都先在外部肩钉上套HW/A8/A8/FW4，再把整组旋入。'),('RF压盖工具','长套筒会碰到肘叉后方','明确使用两把5.5 mm薄开口扳手；不使用被挡住的长套筒。')])
    body+='<h2>压盖：普通螺母可以用，但不单独裸用一颗</h2><p>6支原M3×16及6片薄W3全部复用；原6颗压盖NL3退出该位置，改用12颗正常高度M3普通螺母（AF5.5，高2.4 mm）。螺钉头进入原六角窝，背面两颗螺母外仍有名义1.1 mm螺纹。先轻贴合第一颗，用薄扳手保持其不转，再锁紧第二颗使两颗对顶。操作后检查压盖贴座并画见证线。双螺母不消除打印材料蠕变，试装后仍需检查贴合与线位。</p><p>两颗正常高度螺母的对顶方法依据<a href="https://www.boltscience.com/pages/twonuts.htm">Bolt Science的双螺母说明</a>；其中试验并不是本版M3塑料夹层的实测结果。这里没有把“两个螺母随便拧上”视为已经锁固。11处运动关节的NL3继续保留。</p>'
    body+='<h2>临时定位筋的作用与限制</h2><img src="images/retained_wrist_centre.png" alt="P012四侧临时定位筋"><p>每面三处小筋只轻夹FW4的外圆，连同其后的NL3/W3/W4保持在内座。名义径向夹持量0.06 mm，筋顶低于摩擦面0.18 mm；不把筋压进正式金属承压层，也不靠筋承担防脱。固定骨架未切开，原连续横桥及骨杆外形保留。几何报告逐项列出这8处有意接触，没有把它们伪装成零干涉。</p><p>打印尺寸和垫片外径会影响配合。先在开放台面轻压、轻翻转检查：不能松脱，也不能硬砸。若过紧，只清理毛刺／极少量修整三处定位面后复核；若过松，停在该步调整打印配合，不能先合叉。实际留片力尚未实测。</p>'
    body+='<h2>托叉与导向针</h2><p>两个工装各打印1件，在RP/RU/RF反复使用。托叉只承担松散金属件重量，手指留在20×20 mm手柄上；模块需由软口台钳／桌夹固定、轴线朝上。导向针从裸转子开放正面进入，再由肩钉端面对接顶出；其大头始终在外部。肩钉与反力NL3捕获整组后，托叉从侧面抽出，之后才用肩钉压缩碟簧。禁止拿薄托叉当压簧杠杆。</p><p>通道检查从真正位于骨杆外部的肩钉起点开始；抽叉检查包含7 mm螺钉头，托叉开口为7.6 mm。工作姿态下试算了16 mm直径指腹在外手柄和开放座口的空间；这是明确的几何筛查尺寸，不能代替不同手型的实际操作体验。</p>'
    body+='<p><a href="verification/assembly_usability.json">防脱／工具／指腹包络／复用检查</a> · <a href="assembly_guide/verification/assembly_paths.json">201步路径与支承方式</a> · <a href="verification/motion_dense.json">850组活动姿态</a></p>'
    pg('ASSEMBLY_REVIEW.html','R4 · 装配问题逐项审查',body)
    body='<div class="box"><b>已有R3：选 R4_REPRINT_3_PLUS_2，5个对象。</b><br>从零制作：选 STOCK_ARM_01，包含11个整臂零件＋2件工装，共13个对象。两盘是替代选项，不需要重复打印。P011在R3已撤销，本版继续空号。</div>'
    body+=table(['工程','对象数','用途','切片'],[(f'<a href="{p["file"]}">{p["id"]}</a>',p['count'],'R3升级：3个替换件＋2个工装' if p['replacement'] else '完整单臂11件＋2个工装',f'<a href="verification/slice_{p["id"]}.json">离线检查通过</a>') for p in plates])
    body+=table(['R4件号','原R3件号','动作','原因','文件'],[(r['new_part'],r['R3_part'] or '—',r['action'],r['reason'],f'<a href="{r["stl"]}">STL</a>') for r in rows])
    body+='<p>工程采用A1 mini、0.4 mm喷嘴、PLA、0.12 mm层高、5壁、100%填充、自动支撑和3 mm裙边。清理三处定位筋的毛刺与支撑，避免削去整个筋；导向针需在4.25 mm通孔中顺滑通过，不能硬顶。不要整体缩放人偶零件修配孔径。</p>'
    pg('PRINTING.html','R4 · 重打3件，新增2件工装',body)
    body='<div class="box">相对R3：新增普通M3螺母12颗；压盖处退下NL3 6颗保存作备件。M3×16、W3、肩钉、摩擦垫与碟簧数量不变。整臂136件标准五金，零定制、零下料。O22清单存在NUT_M3，但历史数量不等于当前库存。</div>'
    body+=table(['规格','整臂数量','规格限制','优先来源'],[(r['sku'],r['required'],r['spec'],r['reuse_source']) for r in bom['rows']])
    body+='<h2>安装工具与临时打印工装</h2>'+table(['工具','数量','用途'],[('3 mm长杆内六角螺丝刀，有效直杆≥120 mm','1','11支肩钉，外部承托／旋入／预紧；长杆从骨杆外部开口到达深处螺钉头'),('2.5 mm内六角','1','6支反向压盖螺钉'),('5.5 mm薄开口扳手，厚≤2 mm','2','压盖双普通螺母对顶；裸转子阶段托住反力NL3'),('软口小台钳或桌夹','1','固定独立模块，保持轴线／操作座口朝上；夹具不得包围侧窗与穿钉入口'),('J001托叉、J002导向针','各1','打印件，可重复使用，不留在整臂内'),('卡尺／记号笔／软布','按需','碟簧高度、锁固见证线、轻翻转防落片检查')])
    body+='<p>压盖普通螺母必须是正常高度2.4 mm，不用两个薄螺母代替。其余11颗NL3仍是关节预紧的防松件；不要整体换成普通螺母。W3保持7×3.2×0.5，W6L保持18×6.4×1.5。</p><p><a href="HARDWARE_REUSE_BUY.csv">数量／复用／补齐表</a> · <a href="HARDWARE_DETAIL.csv">每颗五金的位置</a> · <a href="TOOLING.csv">临时打印工装</a></p>'
    pg('HARDWARE.html','R4 · 常见五金与工具',body)
    pg('ASSEMBLY.html','R4 · 完整逐步安装教程','<p><a href="assembly_guide/index.html">打开201步三维动画</a> · <a href="assembly_guide/STEP_CARDS.html">全部步骤文字卡</a></p><p>顺序已经重写；不要混用R3“先合固定座、再逐片侧塞”的步骤。前三章用裸转子与托具预装，再合座；肩肘腕内层先留片，外层都预先套在肩钉上。</p><p>动画中的RP_J001/RU_J001/RF_J001是同一件托叉的重复使用位置，不是要打印三件；导向针同理。装完后两件工装都取出。</p>')
    pg('ELECTRONICS_RESERVATION.html','R4 · 电子预留保持','<p>原7轴、UE骨轴、A字姿态与腕角链保持；一体P010继续复用。原6组传感器与12个刚体预留包络已针对R4再检查850组姿态，定位筋不占磁铁入口与既定空间。此次机械试装仍无需安装电子件。</p><p>未来走线从骨杆外侧的预留路径通过，保持轴向调节孔、侧装窗口与扳手空间可服务；6根AWG30线束预留直径3.5 mm、动态弯曲半径10 mm。具体线夹、动态线束碰撞／疲劳、电子支架与磁场标定尚未发布生产验证，不将旧整机剪线长度当作本臂下料长度。</p><p><a href="electronics/interface_reservations.json">接口与线束预留</a> · <a href="electronics/reserved_layout.glb">电子预留GLB</a></p>')
    pg('TEST_PLAN.html','R4 · 本次实装记录','<p>先检查3个新件与2个工装的打印配合；不要求重新验收已接受的T6 H/W作为开工前提。</p><ol><li>逐面压入FW4并轻翻转，记录8处是否留片、是否过紧；未留住不合叉。</li><li>记录3组托叉送入、针钉交接、抽叉是否顺手，是否需要把指尖伸入窗口。</li><li>检查6组普通M3双螺母对顶、压盖贴合和见证线；记录是否需要补紧。</li><li>低预紧检查7轴范围、轴向防脱，再按保持目标调整。记录0／10／20／50／100次活动后的间隙、磨屑、漂移及线位。</li></ol><p><a href="verification/holding_targets.json">保持目标（不是拧紧扭矩）</a> · <a href="TRIAL_LOG.csv">空白记录</a></p><p>本版实际保持力、指腹操作体验、定位筋寿命及打印蠕变仍需实测；计算几何不替代这些结果。</p>')
    csvfile('TRIAL_LOG.csv',['item','cycle','fit_or_support','hold_or_drift','axial_play','retightened','result'],[dict(item=a['id'],cycle=n) for a in PROFILE['axes'] for n in [0,10,20,50,100]]+[dict(item=x,cycle=0) for x in ['RP托叉','RU托叉','RF托叉','HS-L留片','HS-R留片','HE-L留片','HE-R留片','WY-L留片','WY-R留片','WX-L留片','WX-R留片']])
    # Optional rigid electronic reservations in the whole-arm preview.
    p=OUT/'preview/data.js';d=json.loads(p.read_text('utf8').removeprefix('window.O24D=').removesuffix(';'));raw=bytearray(base64.b64decode(d['geometry']));cursor=len(raw)//24;z=np.load(OUT/'electronics/reserved_meshes.npz')
    for q in load(OUT/'electronics/reserved_parts.json'):
        i=str(q['i']);v=z[i+'v'];f=z[i+'f'];m=trimesh.Trimesh(v,f,process=False);ar=np.concatenate([v[f],np.repeat(m.face_normals[:,None,:],3,axis=1)],axis=2).reshape(-1,6).astype('<f4');d['parts'].append(dict(name=q['name'],frame=q['frame'],role=q['role'],source_features=['electronics','reserved'],reservation=True,bounds_mm=m.bounds.tolist(),color=[.15,.65,.4] if q['role']=='pcb' else [.85,.2,.15],first=cursor,count=len(ar)));cursor+=len(ar);raw.extend(ar.tobytes())
    d.update(geometry=base64.b64encode(raw).decode(),mechanical_count=147,reservation_count=12);p.write_text('window.O24D='+json.dumps(d,ensure_ascii=False,separators=(',',':'))+';',encoding='utf8')
    p=OUT/'preview/viewer.js';s=p.read_text('utf8').replace('function selected(p){','function selected(p){if(p.reservation&&!$(\'#electronics-reserved\').checked)return false;').replace("if(!$('#hardware').checked&&!['structure','rotor','shell'].includes(p.role))continue;","if(!p.reservation&&!$('#hardware').checked&&!['structure','rotor','shell'].includes(p.role))continue;").replace("$('#parts').textContent=D.parts.length;","$('#parts').textContent=D.mechanical_count;").replace("['bones','helpers','hardware','shell','harness']","['bones','helpers','hardware','shell','harness','electronics-reserved']").replace('显示 ${visible} / ${D.parts.length} 个机械实物件 · mm','显示 ${visible} 件 · 机械147件，另有12个可选电子包络 · mm');s=s.replace('O24E_LArm_Stock_R3','O24E_LArm_Stock_R4').replace('本版生产 STL 相邻干涉：0 对。','本版非预期相邻干涉：0 对；8处定位筋压配另计。');p.write_text(s,encoding='utf8')
    p=OUT/'preview/index.html';s=p.read_text('utf8');s=re.sub(r'<details id="assembly-panel">.*?</details>','<p><a href="../assembly_guide/index.html"><b>打开201步安装动画（含托具与支承方式） ↗</b></a></p>',s,flags=re.S);s=s.replace('<script src="assembly.js"></script>','').replace('O24E · 常见五金左臂试装','O24E R4 · 可操作装配修订').replace('<strong>12</strong>','<strong>11</strong>').replace('优先复用 O22 / T6 常见五金；零金属定制、零切短。无电路。','普通M3压盖锁固；内垫片临时定位；新版托具装配。3个主件重打，其余8件复用。').replace('<div class="checks">','<div class="checks"><label><input type="checkbox" id="electronics-reserved"> 电子预留（附件未发布）</label>').replace('本版实际 STL 已检查活动范围；实装保持力与循环待测。','已检查活动范围；8处定位筋径向接触单独记录，实物配合待测。');p.write_text(s,encoding='utf8')
    print('R4 DOCUMENTS',len(guide['steps']),'guide steps; 3 replacement prints + 2 tools',flush=True)
if __name__=='__main__':run()
