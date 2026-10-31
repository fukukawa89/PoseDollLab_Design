"""T6 manufacturing, assembly and physical-test instructions."""
from arm_kit import *
from publish import write_doc
import html,csv,collections

NEW=['H6-01','R6-01','W6-01']
def changes():
 return '''<table><tr><th>样件</th><th>必须重印</th><th>替换旧件</th><th>继续复用</th></tr>
<tr><td>H 肘</td><td><a href="stl_print/H6-01.stl">H6-01</a></td><td>H5-01</td><td>H3-03、F3-H</td></tr>
<tr><td>R 前臂旋转</td><td><a href="stl_print/R6-01.stl">R6-01</a></td><td>R5-01</td><td>R3-03、R3-04、F3-R</td></tr>
<tr><td>W 双轴腕</td><td><a href="stl_print/W6-01.stl">W6-01</a></td><td>W5-01</td><td>W4-01、W4-04、W3-09、F3-W、F3-M</td></tr>
<tr><td>试配工具</td><td><a href="stl_print/C6-01.stl">C6-01（建议先印）</a></td><td>原C3-01不能检验新锁母窝</td><td>试片不装在人偶上</td></tr></table>'''

def hardware_page():
 rows=json.loads((OUT/'assembly.json').read_text('utf8'))['parts']
 old=json.loads((H/'bench/revO24C_T5/assembly.json').read_text('utf8'))['parts']
 count=lambda rs:collections.Counter(r['sku'] for r in rs if r['sku'])
 new=count(rows);prior=count(old)
 diff=[dict(sku=s,spec=SPECS[s],T5=prior[s],T6=new[s],delta=new[s]-prior[s]) for s in sorted(prior.keys()|new.keys())]
 put(OUT/'hardware_delta_from_T5.json',diff)
 body='''<h1>T6补购：7颗锁母、21片平垫</h1>
<p>按已经备齐T5全套计算。7颗O22轴肩螺钉、14片A8、14片大摩擦垫全部复用。只有主肩钉的反力组件改变；方键、掌柄、加载杆连接五金继续使用原型号。</p>
<div class="note"><b>七处主肩钉用NL3尼龙锁母；附件仍用普通N2/N3。</b>取下旧7颗主肩钉普通M3和7片9×3.2×0.8反力垫，分袋保存，不要混回T6预紧堆叠。</div>
<table><tr><th>需补齐</th><th>采购参数</th><th>新增用量</th><th>T6用途</th></tr>
<tr><td>NL3</td><td>M3×0.5，DIN985尼龙锁紧螺母，金属本体；对边5.32～5.50，总高3.70～4.00，金属六角段高≥2.15 mm。建议普通钢镀锌。</td><td>7颗，可买10颗留备件</td><td>H两颗、R一颗、W四颗</td></tr>
<tr><td>W4</td><td>钢平垫，外径9、内径4.3、厚0.8 mm</td><td>14片</td><td>每组内部增加两片；原头下7片仍保留，全套共21片</td></tr>
<tr><td>W3</td><td>钢平垫，外径7、内径3.2、厚0.5 mm</td><td>7片</td><td>替换旧反力垫；原附件3片仍保留，全套共10片</td></tr></table>
<p>尺寸顺序为外径×内径×厚度。不要买总高4.5 mm的锁母，不要买全尼龙螺母，不要用0.8 mm厚M3垫替代0.5 mm。已有同规格余料可抵扣补购数量。不同商家的尺寸需用卡尺核对。</p>
<p>参考：<a href="https://konarik.cz/en/produkt/selflocking-hexagon-nut-din985/">DIN985 M3尺寸表</a>；<a href="https://www.pemnet.com/products-overview/products-nuts/nuts-locking-nuts/">PennEngineering锁紧原理及重复使用限制</a>。来源不代表手头商品已通过检验。试验优先用新锁母；反复拆装后锁紧阻力明显下降则更换。</p>
<h2>完整五金对照</h2><table><tr><th>型号</th><th>参数</th><th>T5</th><th>T6</th><th>增减</th></tr>'''
 for r in diff:body+='<tr>'+''.join('<td>'+html.escape(str(r[k]))+'</td>' for k in ['sku','spec','T5','T6','delta'])+'</tr>'
 body+='</table><p>数量含实际掌柄与替换测力杆各自的连接五金；拆下重装不重复计数，掌柄与测力杆不能叠装。没有新增肩钉型号。</p>'
 write_doc('HARDWARE','T6五金补购与复用',body)

def section_svg():
 # Deliberately a labelled exploded sequence, not a scale drawing.
 pieces=[('肩钉头','#8b9ca2',48),('头下W4','#9aadb1',32),('A8×2','#477ab4',56),('外FW4','#9aadb1',35),('3mm运动耳','#d99958',82),('内FW4','#9aadb1',35),('W4×2','#91bca9',65),('薄W3','#9aadb1',35),('NL3金属端','#8b9ca2',55),('尼龙圈','#245fd2',30)]
 x=30;svg='<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 780 175" role="img" aria-label="T6压紧链，从肩钉头到尼龙圈的示意，非比例图"><path d="M20 84 H752" stroke="#9aa" stroke-dasharray="5 4"/>'
 for label,color,w in pieces:
  svg+=f'<rect x="{x}" y="55" width="{w}" height="58" rx="4" fill="{color}"/><text x="{x+w/2}" y="{138 if len(label)>4 else 37}" font-size="12" text-anchor="middle" fill="#264538">{label}</text>'
  x+=w+16
 svg+='<text x="390" y="169" font-size="12" text-anchor="middle">轴向顺序示意 · 蓝色圈在尖端侧 · 内部两片W4不能漏装</text></svg>'
 return svg

def main():
 rows=json.loads((OUT/'assembly.json').read_text('utf8'))['parts'];lessons=json.loads((OUT/'tutorial/steps.json').read_text('utf8'))['lessons']
 steps=' / '.join(st+' '+str(len(l['steps']))+'步' for st,l in lessons.items())
 start='''<div class="hero"><div><p class="eyebrow">O24C-T6 · 2026-10-25 · 实物待测</p><h1>锁住肩钉，继续验证持姿。</h1><p>H、R、双轴腕统一改用完整六角窝中的尼龙锁紧螺母，复用现有O22肩钉和运动件。目标是至少100次活动无需补紧；当前交付是可打印测试版，尚无T6实测结果。</p><a class="button" href="tutorial/index.html">逐件装配动画</a><a class="button" href="ONE_PRINT.html">选打印工程</a><a href="HARDWARE.html">补购清单</a></div><img src="images/three_modules.png" alt="使用T6制造网格的H、R、W三个实际手臂关节"></div>
<div class="cards"><div class="card"><b>3件</b>必须重印的固定座</div><div class="card"><b>7颗</b>现有肩钉全部复用</div><div class="card"><b>100次</b>不中途补紧的待验证目标</div></div>'''
 start+='<h2>从T5升级</h2>'+changes()+'''<p><a class="button" href="printing/REPRINT_T6_three_parts.3mf">重印三件，一盘</a><a class="button" href="printing/FIT_T6_locknut_coupon.3mf">先印锁母试配片</a><a href="printing/ALL_H_R_W_T6.3mf">首次制作：全套14件一盘</a></p><p>补购7颗M3尼龙锁母、14片9×4.3×0.8平垫、7片7×3.2×0.5平垫。已有同规格余料可抵扣。</p>
<h2>先确认四件事</h2><ol><li>锁母总高≤4.0mm，金属六角进入窝底；不能随肩钉连续转动。</li><li>内部顺序是锁母、薄M3垫、两片M4间隔垫；旧0.8mm厚小孔反力垫不再使用。</li><li>肩钉完整穿过尼龙圈，肩部不顶住小孔垫；遇尼龙阻力不等于预紧完成。</li><li>调好后建立0次基线，在10/20/50/100次记录，不补紧。需要补紧即记录本轮未通过。</li></ol>'''
 start+=f'<p>动画共 {steps}。蓝色区分尼龙圈和A8，绿色标光滑面；每个零件各一步，肩钉另有旋入过程。</p>'
 start+='<p><a href="DESIGN_REVIEW.html">设计与数字检查范围</a> · <a href="TEST_PLAN.html">100次测试方法</a> · <a href="O24C-T6_print_and_assembly.zip">完整离线包</a> · <a href="viewer/index.html">装入实际手臂后的三维模型</a></p>'
 write_doc('START_HERE','T6打印与装配入口',start)

 review='''<h1>T6：防松、止转与金属预紧链</h1><p>T5 H初始摩擦可用，但用户反复活动十几次后观察到螺钉尖端缩进，重新拧入后恢复；这强烈支持肩钉旋退。T6优先补齐防松，同时减少预紧链对打印承压壁的依赖。</p>
<h2>为何不能只换一颗螺母</h2><p>T5轴向槽只为2.4mm普通螺母留2.8mm空间，肩钉从承压面起伸入约3.4～3.7mm，不能直接容纳3.7～4.0mm尼龙锁母并留足穿出量。T6重排了内部支承，把螺母金属承压面向肩钉移动1.5mm，现有Φ4×8 / M3×6肩钉得以保留。</p>
<h2>完整六角窝，而非侧向开放滑槽</h2><p>七处都改成轴向装入。锁母尼龙端先进入深处，金属六角由六面连续侧壁包围；正式窝AF5.65，适配AF5.32～5.50，最小金属六角段约1.9mm处在闭合止转区内。±10°及±30°旋转探测均与实体侧壁干涉，说明名义尺寸下不能越过六角面持续旋转。配合间隙仍可能产生少量初始角位移，不等于实物绝无间隙，也不代表打印槽承扭强度已经通过。</p>
<p>H、R、W一体外壳保持T5外廓，原侧槽封闭；肩钉孔中心、3mm运动耳及连接方键不变。闭合六角周围检查了连续实体，未用薄压板或重新拆成承力半壳。C6-01分别提供竖向、横向试配窝，以暴露打印方向造成的误差。</p>'''
 review+=section_svg()+'''<h2>预紧链如何改变</h2><p>旧9×3.2×0.8反力垫改为7×3.2×0.5；其前方新增两片9×4.3×0.8钢垫，支承原内摩擦垫。名义主压紧链经金属件闭合，打印座主要定位和承受螺母止转反力；实际尺寸误差仍可能让外缘塑料分担压力。无需削薄原运动耳，不增加肩钉长度，也不加大关节外廓。</p>
<p>两片间隔垫的大孔避让Φ4肩部，薄M3垫在肩端之后承压。名义A8叠高0.9～1.2mm检查中，肩端到小孔垫间隙为0.3～0.6mm，螺钉尖端超出4.0mm锁母为0.9～1.2mm。这不是所有五金与打印公差叠加后的保证，A8叠高也不是指定预紧量。实际须核对肩长、螺纹长、垫厚和尖端倒角，确保肩部未顶死、尼龙圈完全啮合。</p>
<h2>复用与范围</h2><p>10件运动件、掌柄及附件STL与T5逐字节相同。三件固定座外廓相同；Quinn参考的肘—腕80.496305mm不变，腕轴顺序Ry屈伸后随动Rx偏摆。目标H 0～145°，R −85～80°，腕屈伸−65～70°、偏摆−20～30°。完整人偶小于600mm仍是后续整机要求，本次不把三个样件视为整机验收。</p>
<h2>验证边界</h2><p>数字检查包括单一连通/封闭网格、真实制造网格干涉、轴心、七处完整六角壁与最小/最大锁母包络、预紧几何余量、工具入口、每一步装配路径、实际臂与独立台架活动采样、STL和3MF一致、离线切片及浏览器动画。螺纹与变形后的尼龙用简化包络显示，没有模拟螺旋啮合、尼龙力矩、打印破坏、磨损或持姿力。</p><p>报告：<a href="verification/mechanics.json">锁母与预紧检查</a> · <a href="verification/reuse.json">复用检查</a> · <a href="verification/installed_rom.json">联装活动采样</a> · <a href="verification/tutorial_paths.json">逐件装入路径</a> · <a href="verification/delivery.json">交付核验</a>。实物结果只能由下一轮100次测试确认。</p>'''
 write_doc('DESIGN_REVIEW','T6设计复核',review)

 assembly='''<h1>T6装配要点</h1><p><a class="button" href="tutorial/index.html">逐件动画</a> <a href="TUTORIAL.html">全部步骤索引</a></p>
<p>先用卡尺确认锁母总高3.7～4.0、AF≤5.5，肩钉光杆长8、M3螺纹长6，以及平垫厚度。先印C6-01试配；清除窝内支撑，不能让金属六角停在圆形入口里。槽太松到能转过一个六角面、太紧需要用螺钉强拉、或壁面发白时均不要继续。</p>
<h2>每组从固定座外侧轴向装入</h2><ol><li>NL3尼龙锁母：尼龙圈先朝深处，金属端朝肩钉方向。六角对齐，轻推到窝内。</li><li>W3薄反力垫：7×3.2×0.5，贴锁母金属端。</li><li>两片W4内部间隔垫：每片9×4.3×0.8，总厚1.6mm。</li><li>原内FW4：12×4.3×1，光滑面朝运动耳；装原3mm运动耳，再装外FW4，光滑面朝运动耳。</li><li>原两片反向A8：内孔凸边相对；再装原W4头下垫。</li><li>原肩钉：先对中金属螺纹，再用3mm内六角缓慢旋过尼龙圈。螺母由窝止转，只需转螺钉。</li></ol>'''
 assembly+=section_svg()+'''<p>内部小平垫及两片间隔垫两面均接触金属，不强制正反，但必须平整、去毛刺。摩擦垫两片光滑面相向；附件小垫光滑面贴打印件。尼龙圈颜色不作型号依据。</p>
<table><tr><th>样件</th><th>内部先装</th><th>再装</th><th>工具入口</th></tr><tr><td>H</td><td>两侧各1锁母+3平垫</td><td>原H3-03及外部摩擦/碟簧堆叠</td><td>两侧3mm内六角</td></tr><tr><td>R</td><td>Z=0端面1锁母+3平垫</td><td>先预装转盘背面M2，再装转盘、肩钉、输出壳</td><td>拆测力杆/腕和横向连接螺钉后，从中央通道调</td></tr><tr><td>W</td><td>四个轴端各1锁母+3平垫</td><td>Y前臂叉、X掌侧叉及其两侧堆叠</td><td>四个外侧3mm内六角</td></tr></table>
<p>肩钉未夹紧前，窝内五金可能沿入口掉出。一次让一个入口朝上；装叉时托住五金，必要时用临时胶带仅挡入口，随后全部移除，不能夹入摩擦面或轴孔。</p>
<h2>尼龙阻力与预紧是两回事</h2><p>到尼龙圈后难拧是锁紧阻力，不说明碟簧已压紧。金属螺纹一开始就卡、螺母未入六角窝或跟转，应退出检查。不可钻掉尼龙圈，不靠持续大力拧紧来克服错位。</p>
<p>确认螺钉完整穿过尼龙圈、有完整牙露出，且Φ4肩端没有顶在孔3.2的垫圈上。再从轻接触开始小步调节，H和每根腕轴两侧交替，单步最多约1/24圈。它不是规定扭矩；不能把碟簧压平，也不能因锁母阻力大而用电批猛拧。</p>
<p>若实物穿出量不足或肩部顶住，停止并核对实际肩长、螺纹长、螺母高度及垫厚，不通过磨薄打印耳或删除间隔垫解决。若反复拆装使锁母的锁紧阻力明显下降，更换新锁母再测试。</p>'''
 write_doc('ASSEMBLY','T6装配与朝向',assembly)

 test='''<h1>T6：100次活动不补紧测试</h1><p>先测H，再测R和腕的Y/X两轴。T6尚无实物结果，目标是排除T5早期肩钉旋退，同时观察残余的压实和磨损。</p>
<ol><li>记录材料、层高、墙数、五金实际尺寸；确认完整六角入窝、无发白裂纹、两片内部间隔垫齐全、尖端完全穿过尼龙、肩部未顶死。</li><li>调好到实际可用持姿后立即建立0次基线。肩钉头与固定座画见证线，同时拍尖端位置。不能用活动耳或会转的垫圈作固定参照；腕Y轴肩钉以其十字芯作固定参照。</li><li>选择并记录相同往返角度、速度和负载。一完整往返计1循环，同时记录单程次数。可分别采用H 20～120°、R −60～60°、腕Y −45～45°、腕X −15～20°；这是耐久测试建议区间，完整目标范围另行缓慢检查。</li><li>在0/10/20/50/100次记录启动力、拖动力、间隙、肩钉标记及尖端位置。中途不补紧；若必须补紧，本轮100次目标未通过，记录当时次数。不要先反复补紧磨合再重置计数隐藏早期衰减。</li><li>各节点用同一姿态和载荷保持10分钟，记录角漂移。100次后另静置24小时复查，区分循环松动与静置压实。掉粉、裂纹、硬卡、明显松旷或螺母持续转动时停止。</li></ol>
<h2>如何量阻力</h2><p>沿用100mm加载杆，令被测轴竖直、杆水平，沿力孔切向水平拉，以降低杆自重影响。τ=F×实际垂直力臂。腕一次只测一个轴，另一轴归零；先排除方键和壳体连接松动。</p>
<table><tr><th>轴</th><th>沿用的样件比较门槛</th><th>100mm力臂拉力</th><th>目标活动范围</th></tr><tr><td>H</td><td>0.040 N·m</td><td>0.40 N</td><td>0～145°</td></tr><tr><td>R</td><td>0.020 N·m</td><td>0.20 N</td><td>−85～80°</td></tr><tr><td>腕Y / X</td><td>各0.006 N·m</td><td>各0.060 N</td><td>Y −65～70°；X −20～30°</td></tr></table>
<p>这些只是历史样件的比较门槛，不是已达到的能力或完整人偶额定负载。低力值需要合适量程和分辨率。没有量具时记录同一载荷下的持姿、手感、间隙与照片，不虚构数值。</p>
<h2>通过与失败的记录</h2><p>最低要求：100次内没有补紧，肩钉和锁母没有持续旋退/转动，原来能保持的姿态与载荷仍能保持，无裂纹或明显间隙增长。阻力数据应同时给出起始、末值及测量重复性；用户尚未指定允许下降百分比，不能自行把明显衰减宣布为合格。</p>
<p>若肩钉标记转动或尖端回缩，防松仍未解决；若位置保持而阻力下降，再排查摩擦面磨损、打印件压实和弹性补偿。100次仅为本轮最低目标，不代表长期寿命认证。</p><p><a class="button" href="test_record.csv">下载空白测试记录</a></p>'''
 write_doc('TEST_PLAN','T6百次活动测试',test)
 with (OUT/'test_record.csv').open('w',encoding='utf-8-sig',newline='') as f:
  w=csv.writer(f);w.writerow(['日期','轴H_R_WY_WX','材料_打印参数','完整往返次数','单程次数','角度区间_速度_载荷','肩钉标记是否移动','尖端位置mm','锁母是否跟转','是否补紧','启动力N','拖动力N','实际力臂mm','保持载荷N','10分钟角漂移deg','间隙_发白_裂纹_掉粉','备注'])
  for st in ['H','R','WY','WX']:
   for n in [0,10,20,50,100]:w.writerow(['',st,'',n]+['']*13)

 printguide='''<h1>T6打印：三件重印，另有快速试配片</h1><p><a class="button" href="printing/REPRINT_T6_three_parts.3mf">已有T5：三件重印盘</a><a class="button" href="printing/FIT_T6_locknut_coupon.3mf">建议先印：锁母试片</a><a href="printing/ALL_H_R_W_T6.3mf">首次打印：全套14件一盘</a></p>'''
 printguide+=changes()+'''<p>三个关节只需重印H6-01、R6-01、W6-01。C6-01是可选但建议先印的试配工具；整盘已含它及三件新座，不要再重复打印补件盘。仅做H时可只保留H6-01。</p>
<h2>工艺与清理</h2><p>A1 mini 180×180mm，0.4mm喷嘴，PLA，0.12mm层高，5圈墙，100%填充，自动普通支撑，3mm外沿。保留工程的打印朝向；全套排布只作平面内旋转。工程包含模型与设置，未向打印机发送任务。</p>
<table><tr><th>件</th><th>朝下表面</th><th>重点</th></tr><tr><td>H6-01</td><td>负Y侧外端面</td><td>从两侧大圆入口清支撑，检查六角窝和叉根</td></tr><tr><td>R6-01</td><td>Z=0端面</td><td>清除深窝和肩钉通路的支撑，勿磨掉止转平面</td></tr><tr><td>W6-01</td><td>完整+Z面</td><td>四个横向六角窝都应试配，检查桥接下垂</td></tr><tr><td>C6-01</td><td>完整底板</td><td>1点为AF5.65竖孔，2点为AF5.75对照竖孔，3点为AF5.65横孔；一体小圆管可轻推螺母金属端</td></tr></table>
<p>正式件统一AF5.65。试片若显示横孔太紧，先清支撑和毛刺；若需要明显扩大或锁母可连续旋转，请记录实际螺母尺寸和打印误差，不靠强拧试装。0.15mm名义对边余量不是任意打印机的配合保证。</p>
<h2>全套STL</h2><table><tr><th>编号</th><th>名称</th><th>打印包围尺寸mm</th><th>处理</th></tr>'''
 for r in rows:
  if r['printable']:
   size=' × '.join(f'{v:.2f}' for v in np.array(r['print_bounds_mm'][1])-r['print_bounds_mm'][0])
   action='必须重印' if r['id'] in NEW else '新试配片，可选' if r['id']=='C6-01' else '与T5逐字节相同，复用'
   printguide+=f'<tr><td><a href="{r["stl"]}">{r["id"]}</a></td><td>{r["label"]}</td><td>{size}</td><td>{action}</td></tr>'
 printguide+='</table><p>所有尺寸单位mm。切片检查不代表实际打印强度、支撑清理或配合已通过；先试配后组装。</p>'
 write_doc('ONE_PRINT','T6打印工程与重印清单',printguide)
 hardware_page()
 (OUT/'VERSION.txt').write_text('O24C-T6 / 2026-10-25\nNew housings H6-01 R6-01 W6-01; optional C6-01 coupon. 10 printed parts reused from T5.\n7 existing O22 shoulder screws retained; 7 NL3 + 14 W4 + 7 W3 additions.\nT6 physical 100-cycle tests PENDING.\nGeometry SHA256: '+sha(OUT/'assembly_meshes.npz')+'\n',encoding='utf-8')
 print('T6 DOCS ready',flush=True)

if __name__=='__main__':main()

