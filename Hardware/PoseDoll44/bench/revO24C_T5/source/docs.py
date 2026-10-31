"""Repository design and print notes; no measured results are invented."""
from publish import *
import csv

def main():
 rows=json.loads((OUT/'assembly.json').read_text('utf8'))['parts'];P={r['id']:r for r in rows};new=['H5-01','R5-01','W5-01'];old=['H3-01 + H3-02','R3-01 + R3-02','W4-02 + W4-03']
 change='<table><tr><th>重印新件，各 1 个</th><th>替代旧件</th><th>改动</th></tr>'
 for id,was,note in zip(new,old,['肘固定叉一体化；两组反力五金从背面滑入','旋转固定芯一体化；反力垫侧壁加厚','双轴腕十字芯一体化；四组五金从同一底面滑入']):
  change+=f'<tr><td><a href="stl_print/{id}.stl">{id}</a></td><td>{was}</td><td>{note}</td></tr>'
 change+='</table>'
 intro='<h1>O24C-T5 · 取消承力座合模缝</h1><p><b>H3-01 / H3-02 不必分成两件。现在改为一体 H5-01，并保留你已认可的 H 摩擦结构。</b>R 固定芯和双轴腕十字芯也取消类似接缝。新版仍是实际手臂关节，配原有可拆加载杆分别测试。</p>'
 intro+='<p>2026-10-25 实物反馈：用户认为 T3/T4 的 H 摩擦力合格、可用，但强拧后固定座接缝张开，反复摆动后趋于扩大。这是定性反馈，没有测得力矩或循环寿命。<b>T5 新结构尚未实测。</b></p>'
 start=intro+change+'<p><a class="button" href="printing/REPRINT_T5_three_parts.3mf">只打印三个替换件</a>　<a class="button" href="tutorial/index.html#H-1">从 H 第 1 步装配</a>　<a href="O24C-T5_print_and_assembly.zip">完整离线包 ZIP</a></p>'
 start+='<img src="images/three_modules.png" alt="T5 实际 H、R、双轴腕，使用相同的 O22 碟簧堆叠" style="width:100%;max-height:560px;object-fit:contain"><h2>已经打印过 T4</h2><p>保留 H3-03、R3-03、R3-04、W4-01、W4-04、W3-09，及 F3-H / R / W / M 四个附件和 C3-01 试片，共 11 个原样件。只装 H 时，先替换 H5-01 即可；重印盘也提供另外两个新承力座。</p><p>五金没有新增规格。拆除旧半体的合模五金后，减少 8 颗螺钉、8 片小垫圈、8 颗螺母；七组主肩钉、A8 及摩擦垫全部复用。<a href="HARDWARE.html">查看准确数量</a>。</p>'
 start+='<h2>第一次打印整套</h2><p><a href="printing/ALL_H_R_W_T5.3mf">完整一盘：14 个打印件</a>，含 9 个实际关节件、4 个可拆测试附件、1 个可选试片。用 A1 mini / 0.4 mm / PLA 工程，保留零件朝向；详情见<a href="ONE_PRINT.html">打印说明</a>。</p><h2>先试配，再预紧</h2><p>先清理侧装入口、反力垫槽和轴孔，确认五金能手动滑到位。反力垫先装、普通 M3 后装；螺钉未旋入前扶住五金，防止从入口掉出。轴肩螺钉旋入后将五金留在槽内，入口不用另加封盖。</p><p>H 已验证的摩擦堆叠未改，但一体座会改变刚度和打印方向。仍须从轻接触重新调整，检查裂纹、松旷和回松，不照搬旧版拧紧圈数。</p><p><a href="viewer/index.html">实臂联装与活动预览</a> · <a href="DESIGN_REVIEW.html">为什么改、哪些没有合并</a> · <a href="verification/delivery.json">数字交付检查</a></p>'
 write_doc('START_HERE','O24C-T5 打印与装配',start)
 review=intro+change+'''<h2>原来的两片为什么会张开</h2><p>原分件便于从开放合模面放入普通 M3 和反力垫；但接缝贯穿了肘固定叉的承力区域，预紧、摆动及装配误差可能使两片产生相对变形。用户报告已足以说明这个连接不够稳妥。仅凭描述不能确定是螺母顶槽、打印尺寸、装配扭矩还是多种因素共同造成，也没有做断口检查或载荷测量。</p><p>T5 并非直接粘合原两半 STL：固定座重新建为连续实体，取消原合模孔，并为五金增加侧向装入口。反力壁仍为 2.8 mm；入口只开在反力壁后方。螺母六角导槽负责止转，拧入的肩钉防止它沿入口退出。H 两颗内部螺母绕自身轴转了 30°，让平行平面与滑槽对齐；规格没有变化。</p>
<img src="images/H_ports.png" alt="H5-01 背面两组侧装入口，固定叉为连续一体" style="width:100%;max-height:540px;object-fit:contain">
<h2>检查其他零件后的决定</h2><table><tr><th>部位</th><th>处理及原因</th></tr>
<tr><td>R3-01 / R3-02</td><td>原固定芯也从承力区分开，合并为 R5-01。主体 X 宽由 10 改为 13 mm；9.3 mm 反力垫槽两侧名义壁厚由 0.35 增至 1.85 mm。10 mm 输入方键、轴心和端面位置不动。</td></tr>
<tr><td>W4-02 / W4-03</td><td>合并为 W5-01，四个反力组件从 −Z 同一面先装入，再套两只运动叉。完整的另一面连成一体；取消四组 M2×16 合模五金。两根轴仍在同一腕中心相交。</td></tr>
<tr><td>H3-03、W4-01 / W4-04</td><td>保持原一体运动叉和 3 mm 摩擦耳，不再削薄。与固定座是相对转动的零件，必须保持分离。检查了网格连通、现有装入路径和采样活动范围；没有新增薄的拼接压板。</td></tr>
<tr><td>R3-03 / R3-04</td><td>保留可更换摩擦转盘与输出壳。内部 12 mm 垫圈、7 mm 螺钉头不能通过 6.4 mm 中央调节通道；简单合并会封死正常装入路径。两颗 M2×14 连接仍需坐正并检查松动。这里不是拆开固定反力座的接缝。</td></tr>
<tr><td>W3-09、F3 测试附件、C3-01</td><td>保留。掌柄和加载杆需替换使用；测试附件与实际臂共用同一个关节。方键连接螺钉负责连接结构，不调关节摩擦。</td></tr></table>
<h2>关键名义尺寸与装配公差</h2><p>滑槽六角对边 5.8 mm，适配 AF5.5 的普通 M3；轴向槽深 2.8 mm，适配高 2.4 mm 螺母。反力垫槽宽 9.3 mm、轴向厚 1.1 mm，适配 9×3.2×0.8 mm 垫圈。比旧开放槽增加装入余量，扩展只向反力壁后方。公差仍需由实际打印确认；槽若过紧，先清支撑、毛刺，不能靠肩钉强拉到位。</p>
<p>每组压紧链：螺钉头 → 孔4.3头下垫 → 两片反向A8 → 外摩擦垫 → 3 mm转动耳/转盘 → 内摩擦垫 → 连续反力座 → 孔3.2反力垫 → 普通M3。七组尺寸与 T4 相同，没有增加轴承来绕过摩擦面。钢垫圈也可能相对滑动，不能直接把两个接触面积换算成加倍持姿力矩。</p>
<img src="images/W_ports.png" alt="腕部一体十字芯与四组底面入口" style="width:100%;max-height:540px;object-fit:contain">
<h2>保留的设计约束</h2><p>肘、前臂扭转及腕轴仍对齐原 Quinn 参考；E—W 为 80.496305 mm，腕先绕 Y 屈伸、再绕随动 X 偏摆。名义目标：H 0～145°，R −85～80°，腕屈伸 −65～70°、偏摆 −20～30°。560 mm 是既有整偶参考比例，完整人偶最终外廓小于 600 mm 的约束仍需整机阶段核验。肩部、布线、测角集成不由本套件验收。</p>
<h2>这轮验证能说明什么</h2><p>检查包括真实制造网格、单一连通实体、七处连续反力环和螺母止转、扳手直线入口、不同碟簧叠高下的名义干涉、逐件装入和模块对接、选定姿态采样、切片及网页动画。它们不能证明打印材料的强度、蠕变、耐磨和长期持姿。侧装口周围仍需在实物中重点观察，不能把“一体”理解成任意拧紧都不会坏。</p>'''
 write_doc('DESIGN_REVIEW','T5 结构复核',review)
 assembly='''<h1>T5 装配要点</h1><p><a class="button" href="tutorial/index.html#H-1">打开逐件动画</a>　<a href="TUTORIAL.html">130 步索引</a></p>
<table><tr><th>样件</th><th>一体件与入口</th><th>顺序</th></tr><tr><td>H</td><td>H5-01，背面 −X 侧</td><td>两组反力垫→普通M3→内摩擦垫→H3-03→外部碟簧堆叠→加载杆</td></tr><tr><td>R</td><td>R5-01，−Y 侧</td><td>反力垫→普通M3→预装转盘背面M2→转盘与主肩钉→输出壳→加载杆</td></tr><tr><td>W</td><td>W5-01，−Z 面四组入口</td><td>八件内部五金全部先装→Y叉及两侧堆叠→X叉及两侧堆叠→掌柄或加载杆</td></tr></table>
<p>坐标用于和三维动画对应。实物装配时把正在使用的入口朝上；尚未穿肩钉时，五金可以从入口滑出。托住它们，必要时只临时遮住入口，不能把胶带夹进摩擦面、孔或碟簧。肩钉旋入后不需要另加堵头。</p>
<h2>垫圈和螺母朝向</h2><p><b>所有螺母均为普通螺母，无尼龙圈。</b>内部反力垫是 9×3.2×0.8，光滑面朝打印反力壁；普通M3平整承压面贴反力垫。两片12×4.3×1摩擦垫的光滑面相向，夹住打印转动耳。小平垫光滑面朝打印件。9×4.3×0.8头下垫两面都贴金属，平整、去毛刺即可，不强制正反。</p><p>A8第一片内孔凸边朝螺钉头，第二片翻面朝关节，两片内孔凸边相对。自由叠高约1.2 mm，两片压平厚约0.8 mm；不能压平。动画中的高度和圈数不是紧固标准。</p>
<h2>调节与防松</h2><p>从轻接触开始，两侧交替小步试调，每步最多约1/24圈，摆动后再测。这个步长不是规定扭矩；没有 A8 实物力曲线，不能给出可靠的统一紧固扭矩。H 的旧手感可作对比，新打印方向和刚度改变后仍需重新调整。</p><p>轴肩螺钉用3 mm内六角；M3圆柱头用2.5 mm，M2用1.5 mm。R主肩钉调整前先卸加载杆或腕及其横向螺钉，再从中央通道伸入扳手；退出工具后才转动关节。</p><p>止转槽只防止螺母跟转，并不保证肩钉不回松。画螺钉头见证线，短测后复查。需要锁固时，按适用材料和具体产品说明在金属螺纹使用可拆卸低强度方案，避免进入塑料、摩擦面和光杆。出现发白、裂纹、明显松旷或硬卡立即退出检查。</p>'''
 write_doc('ASSEMBLY','T5 装配要点',assembly)
 test='''<h1>T5 实测：先验证一体座，再检查持姿与磨损</h1><p>已有证据仅为用户对旧 H 摩擦力的定性认可；T5 还没有打印和测试结果。先测 H5-01，比较相同 H3-03、垫圈和碟簧下的稳定性，再测 R 和双轴腕。</p>
<ol><li>去支撑后，检查三个一体件的入口和反力壁。垫圈、普通M3应能沿入口滑入；肩钉光杆应可滑入轴孔。不用螺钉拉正五金。记录材料、打印方向、层高和异常。</li><li>从轻接触调至可用手感。画肩钉头见证线，记录碟簧叠高和关节间隙；不能把两片压平。先慢摆约50次磨合，静置30分钟，复查后再建立基线。</li><li>分别检查目标活动范围和组合姿势。观察侧装口周围、反力壁、叉耳根部及R输出壳连接；记录裂纹、发白、永久变形和松旷。端点有硬碰时停下。</li><li>用原100 mm加载杆测启动力和稳定拖动力。使被测轴竖直、杆水平，沿力孔切向水平拉，减小杆自重影响；腕每次只测一根轴，另一轴回零。按真实垂直力臂计算 τ=F×L。</li><li>在固定载荷下保持10分钟，记录角漂移；另做24小时静置后的回松、间隙和蠕变复查。两次测量之间是否补紧必须记录，不把补紧后的数值误作未衰减。</li><li>在0 / 100 / 500 / 1000次累计循环节点复测。记录掉粉、磨痕、头标记偏移和需要补紧的次数。先排除方键、加载杆或外壳连接松动，再判断关节摩擦。</li></ol>
<table><tr><th>轴</th><th>本轮比较门槛</th><th>100 mm垂直力臂对应拉力</th><th>目标范围</th></tr><tr><td>H</td><td>0.040 N·m</td><td>0.40 N</td><td>0～145°</td></tr><tr><td>R</td><td>0.020 N·m</td><td>0.20 N</td><td>−85～80°</td></tr><tr><td>腕 Y / X，各轴</td><td>0.006 N·m</td><td>0.060 N</td><td>Y −65～70°；X −20～30°</td></tr></table>
<p>这些是沿用的样件比较门槛，不是完整人偶额定负载，也未由本轮实物确认达到。低力值应使用合适量程和分辨率的量具；没有量具时先记录手感与保持漂移，不虚构力矩数值。独立样件通过后仍需整臂负载复核。</p><p><a href="test_record.csv">空白测试记录 CSV</a>，不包含假设通过的数据。优先对比旧 H 与 T5 的间隙增长、回松和相同负载下的漂移。</p>'''
 write_doc('TEST_PLAN','T5 实测计划',test)
 path=OUT/'test_record.csv'
 if not path.exists():
  with path.open('w',encoding='utf-8-sig',newline='') as f:
   w=csv.writer(f);w.writerow(['date','module_axis','material','print_profile','cycles','preload_pair_height_mm','locking_method','retightened_since_previous','lever_mm','breakaway_N','running_N','hold_load_N','drift_deg_10min','backlash','crack_or_whitening','wear','head_mark_moved','notes'])
 printguide='''<h1>T5 打印工程</h1><p><a class="button" href="printing/REPRINT_T5_three_parts.3mf">已打印 T4：只补三个一体座</a>　<a class="button" href="printing/ALL_H_R_W_T5.3mf">首次打印：全套14件一盘</a></p>'''+change+'''<p>两份工程二选一；整盘已经包含三个新件，不需要再重复打印补件盘。只有 H 需要装配时，也可在补件盘中仅保留 H5-01。</p><h2>设置与方向</h2><p>A1 mini 180×180 mm，0.4 mm 喷嘴、PLA、0.12 mm层高、5圈墙、100%填充、自动普通支撑、3 mm外沿。项目使用原始 STL，整盘仅在打印平面内旋转排布；不要自动改成其他侧面朝下。</p><table><tr><th>件</th><th>工程中的朝下表面</th><th>清理要点</th></tr><tr><td>H5-01</td><td>负Y侧的外端承压面</td><td>两侧阶梯式金属入口和薄的反力垫槽，确保支撑、毛刺不留在滑槽内</td></tr><tr><td>R5-01</td><td>Z=0外端承压面</td><td>反力垫槽顶部有短跨桥，检查下垂；不随意磨薄承压面</td></tr><tr><td>W5-01</td><td>完整+Z面；四组−Z入口朝上</td><td>四组入口分别试装反力垫、普通M3；不破坏连续外侧反力壁</td></tr></table><p>槽内最薄空隙为1.1 mm。实际桥接下垂和支撑残留仍需试印检查。打印后先空装五金；如需修整，只去除毛刺/支撑，不扩大到失去止转，也不用拧紧来压裂槽壁。</p>'''
 for name,label in [('REPRINT_T5_three_parts','补件盘，3件'),('ALL_H_R_W_T5','完整盘，14件')]:
  plate=json.loads((OUT/'printing'/('plates.json' if name.startswith('REPRINT') else 'combined_plate.json')).read_text('utf8'))['plates'][0]
  svg='<svg viewBox="0 0 220 210" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="'+label+'"><rect x="20" y="10" width="180" height="180" fill="#eef2e9" stroke="#375e50"/>'
  for item in plate['items']:
   bb=np.array(item['bounds_mm']).reshape(2,3);w,h=(bb[1]-bb[0])[:2];x=20+bb[0,0];y=190-bb[1,1]
   svg+=f'<rect x="{x:.2f}" y="{y:.2f}" width="{w:.2f}" height="{h:.2f}" fill="#a6c9b8" stroke="#467868" stroke-width="0.4"/><text x="{x+w/2:.2f}" y="{y+h/2:.2f}" font-size="3.5" text-anchor="middle" fill="#203d34">{item["id"]}</text>'
  svg+='<text x="110" y="201" text-anchor="middle" font-size="4">180 × 180 mm · 示意为零件包围框，实际轮廓见3MF</text></svg>'
  printguide+='<h2>'+label+'</h2><div style="max-width:650px">'+svg+'</div>'
 printguide+='<h2>全套打印件复用表</h2><table><tr><th>编号</th><th>名称</th><th>装配包围尺寸 mm</th><th>处理</th></tr>'
 for r in rows:
  if r['printable']:
   sizes=' × '.join(f'{x:.2f}' for x in np.array(r['bounds_mm'][1])-r['bounds_mm'][0])
   printguide+=f'<tr><td><a href="{r["stl"]}">{r["id"]}</a></td><td>{r["label"]}</td><td>{sizes}</td><td>'+('重印' if r['id'] in new else '与T4逐字节相同，复用')+'</td></tr>'
 printguide+='</table><p>项目只离线切片检查，没有发送到打印机。STL 坐标以 mm 为单位；网页和 Blender 使用同一制造网格。打印工艺与实际材料的可靠性仍需按测试计划确认。</p>'
 write_doc('ONE_PRINT','T5 打印工程',printguide)
 (OUT/'VERSION.txt').write_text('O24C-T5 / 2026-10-25\nNew: H5-01, R5-01, W5-01. 11 printed parts reused from T4.\nH friction qualitative approval belongs to T3/T4 hardware. T5 physical testing remains pending.\nGeometry SHA256: '+sha(OUT/'assembly_meshes.npz')+'\n',encoding='utf8')
 print('DOCS ready',flush=True)

if __name__=='__main__':main()
