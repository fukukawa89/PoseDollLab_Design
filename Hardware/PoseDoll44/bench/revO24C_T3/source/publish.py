from arm_kit import *
import base64,html,shutil,zipfile,importlib.util
sp=importlib.util.spec_from_file_location('old_pages',H/'cad/revO24C_T1/package.py');pages=importlib.util.module_from_spec(sp);sp.loader.exec_module(pages)

def page(title,body):
 nav='<nav><a href="START_HERE.html">打印入口</a><a href="viewer/index.html">联装三维 / 零件定位</a><a href="ASSEMBLY.html">装配顺序</a><a href="TEST_PLAN.html">测试方法</a><a href="DESIGN.html">设计边界</a><a href="BOM.csv">五金清单</a></nav>'
 return '<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>'+title+'</title><link rel="icon" href="data:,"><style>'+pages.STYLE+'</style></head><body>'+nav+body+'</body></html>'

def lessons():
 s=[]
 def add(st,title,ids,body):s.append(dict(station=st,title=title,ids=ids,text=body,number=len(s)+1))
 add('H','固定叉的第一半',['H3-01'],'X=0平面朝上，另一半先放旁边。H是实际肘关节，夹持上端方形骨杆。')
 for side,pre in [('左','HL_'),('右','HR_')]:
  add('H',side+'侧普通M3螺母',[pre+'N'],'普通M3 AF5.5×2.4，无塑料圈。放入合模面六角槽，平整承压面朝反力垫。')
  add('H',side+'侧反力垫',[pre+'RW'],'M3大垫圈9×3.2×0.8。光滑面朝固定叉反力壁。不是7mm小垫圈。')
 add('H','合上固定叉',['H3-02'],'沿X方向合拢，检查两颗调节螺母和两片反力垫均平放，不用螺钉硬拉错位的半件。')
 for z in [28,36]:
  add('H','固定叉合模普通螺母',['HC'+str(z)+'N'],'普通M3，装进前侧六角槽。')
  add('H','合模垫圈',['HC'+str(z)+'W'],'7×3.2×0.5，光滑面朝打印件。螺钉头放在后侧，避免深屈肘干涉。')
  add('H','合模螺钉 M3×12',['HC'+str(z)+'B'],'2.5mm内六角。交替轻紧两颗，内藏普通螺母止转。')
 for pre in ['HL_','HR_']:add('H','内侧摩擦垫',[pre+'F1'],'12×4.3×1.0钢垫圈；光滑面朝接下来装入的转动叉。')
 add('H','装入转动叉',['H3-03'],'从远端沿骨轴套入，使两侧3mm转动耳对准轴孔；这里不装684ZZ轴承。保留方键座的夹紧缝，不要用胶填满。')
 for pre in ['HL_','HR_']:
  add('H','外侧摩擦垫',[pre+'F2'],'12×4.3×1.0，光滑面朝转动耳，与内侧垫圈光滑面相向。')
  add('H','第一片 A8',[pre+'S1'],'内孔凸边朝螺钉头；外圆边朝关节。')
  add('H','第二片 A8 翻面',[pre+'S2'],'内孔凸边朝关节；两片内孔边相对，不能同向套叠。')
  add('H','头下金属垫圈',[pre+'HW'],'9×4.3×0.8，两面均贴金属，去毛刺即可。')
  add('H','O22轴肩调节螺钉',[pre+'AX'],'Φ4×8光杆、M3螺纹长6，用3mm内六角。先调到轻接触，左右交替微调；普通螺母已捕获，不需要悬空扶住它。')
 add('H','连接实臂R，或装H加载杆',['H_R_N','H_R_W','H_R_B'],'选R上端方键或F3-H。普通M3螺母在转动叉前侧；7×3.2×0.5垫圈光滑面朝叉；M3×18从后侧旋入。不要直接换长螺钉。')
 add('R','固定芯第一半',['R3-01'],'上端10mm方键接H，旋转轴沿骨轴；这里也不装MR126ZZ。')
 for id,title in [('R_N','普通M3调节螺母'),('R_RW','M3反力垫'),('R3-02','合拢固定芯')]:add('R',title,[id],'反力垫9×3.2×0.8光滑面朝固定芯端壁；普通M3无塑料圈，先在合模面装好金属件再合拢。')
 for y in [-7.4,7.4]:
  add('R','固定芯合模螺母',['RC'+str(y)+'N'],'普通M2 AF4×1.6，装入负X侧槽。')
  add('R','固定芯合模垫圈',['RC'+str(y)+'W'],'5×2.2×0.5，光滑面朝固定芯。')
  add('R','固定芯 M2×12',['RC'+str(y)+'B'],'1.5mm内六角，轻紧到两半贴合。')
 add('R','先准备独立转盘',['R3-03','RO-8.5N','RO8.5N'],'转盘尚未套到固定芯时，把两颗普通M2装进背面六角槽。装上去以后背面会被固定芯挡住。')
 add('R','内侧摩擦垫',['R_F1'],'12×4.3×1.0，光滑面朝转盘。')
 add('R','带螺母的转盘就位',['R3-03'],'沿轴向套到内侧垫圈，厚3mm的圆盘是磨损件，骨轴不偏移。')
 for id,title,txt in [('R_F2','外侧摩擦垫','12×4.3×1.0，光滑面朝转盘。'),('R_S1','第一片 A8','内孔凸边朝螺钉头。'),('R_S2','第二片 A8','翻面，内孔凸边朝转盘，两片内孔边相对。'),('R_HW','头下垫圈','9×4.3×0.8，两面去毛刺。'),('R_AX','O22轴肩螺钉','Φ4×8/M3牙长6，3mm内六角；先消除松旷，再按实测保持力微调。')]:add('R',title,[id],txt)
 add('R','罩上实际输出壳',['R3-04'],'壳体围住预紧组件，输出方键位于骨轴上。中央6.4mm通道保留，不要塞入胶或支撑残渣。')
 for y in [-8.5,8.5]:
  add('R','输出壳垫圈',['RO'+str(y)+'W'],'5×2.2×0.5，光滑面朝壳体。')
  add('R','输出壳 M2×14',['RO'+str(y)+'B'],'只能用14mm；更长的螺钉会伸入固定芯的旋转区域。')
 add('R','实际腕部或径向测试杆',['F3-R','FR_B','FR_W','FR_N'],'联装时接W。独立测试时换F3-R，用额外一套M3×20、7×3.2×0.5垫圈和普通M3螺母；力孔到轴线100mm。')
 add('W','球体第一半',['W3-01'],'先装内部金属件；此时不要装两颗外侧导向轴肩螺钉。')
 for side in [-1,1]:
  add('W','导向螺钉的普通M2螺母',['Wguide_nut_'+str(side)],'AF4×1.6，普通型。肩部最终压0.5mm钢垫圈，再压这颗金属螺母。')
  add('W','导向肩部钢垫圈',['Wguide_w_'+str(side)],'5×2.2×0.5，尺寸不能换回0.3；仅金属接触，平整无毛刺。')
 add('W','磁铁占位块',['W3-03'],'机械测试装打印占位块；传感电子未随本版定型。')
 add('W','合拢球体',['W3-02'],'保持两侧螺母和垫圈平放，避免挤入合模缝。')
 for z in [-5.5,5.5]:
  add('W','球体的尼龙锁紧螺母',['Wball_nut_'+str(z)],'这两颗是全套唯一的尼龙锁紧螺母：AF4、高≤3。金属端朝螺钉来向（+X），塑料圈端朝外（−X）。到塑料圈变紧属锁紧阻力，要旋过，不能按压穿过。')
  add('W','球体合模 M2×14',['Wball_bolt_'+str(z)],'1.5mm内六角，已捕获的尼龙螺母止转；两半贴合即停，不挤变形球面。')
 for side,cu,li in [(-1,'W3-08','W3-04'),(1,'W3-07','W3-05')]:
  add('W','在一旁准备球窝',[cu],'球窝尚未包上球体。衬片入口朝球心敞开。')
  add('W','装入T3衬片',[li],'从球心方向直入。使用有垫圈直入避让的T3衬片；0.7mm薄壁属于可替换摩擦件，不是主承力桥。')
  for x in [-8.5,8.5]:
   pre='WL'+str(side)+'_'+str(x)
   add('W','衬片普通M2螺母',[pre+'N'],'AF4×1.6，放在球窝外侧槽中，不用尼龙型。')
   add('W','衬片0.5mm垫圈',[pre+'W'],'5×2.2×0.5，从球心侧直入，光滑面朝衬片。')
   add('W','衬片 M2×6',[pre+'B'],'从球心侧旋入。此时球窝尚未包住球，扳手有入口。贴合即可，不压裂薄衬片耳。')
  add('W','带衬片的球窝包上球',[cu,li],'沿左右方向合拢到球体两侧；导向肩钉尚未安装，螺钉头不会挡住这条装入路径。')
 for side in [-1,1]:add('W','现在装导向轴肩螺钉',['Wguide_'+str(side)],'Φ2.5×6光杆、M2螺纹长4，2mm内六角。先让球在中立位，再从球窝外侧穿过弧槽旋入内藏普通M2；肩部只夹金属垫圈和螺母。')
 for x in [-8,8]:
  pre='WP'+str(x)
  add('W','预紧普通M4螺母',[pre+'N'],'AF7×3.2，无塑料圈，装入厚耳的外侧六角槽；平整面朝槽底。')
  for suf,title,txt in [('W0','耳外金属垫圈','9×4.3×0.8，光滑面朝打印耳。'),('S1','第一片 A8','内孔凸边朝螺钉头。'),('S2','第二片 A8','翻面，内孔凸边朝球窝；两片内孔边相对。'),('W1','头下金属垫圈','9×4.3×0.8，去毛刺，两面均贴金属。'),('B','M4×35 预紧螺钉','用3mm内六角；从轻接触开始，两处交替微调。A8内孔由M4螺杆导向，不可改M3。')]:add('W',title,[pre+suf],txt)
 add('W','实际掌柄',['W3-09','WPALM_N','WPALM_W','WPALM_B'],'联装选W3-09：普通M2、5×2.2×0.5垫圈光滑面朝掌柄、M2×14。独立测力时换F3-W和其M2×20紧固件。')
 add('W','连接实际前臂或测试夹持柄',['W_R_N','W_R_W','W_R_B','F3-M'],'联装选R输出方键，独立测试选F3-M；同一套M3×20、普通M3、7×3.2×0.5垫圈。只夹夹持柄，不能用台钳夹球窝。')
 return s

def docs():
 bom=json.loads((OUT/'BOM.json').read_text('utf8'));rows=json.loads((OUT/'assembly.json').read_text('utf8'))['parts']
 assembly='''# O24C-T3 · 实际手臂关节样件装配

本版有三套完整样件：H肘屈伸、R前臂轴向旋转、W两轴腕部。P1～P3的16个打印件直接组成联装模型；P4的4个附件仅用于夹持和100mm加载，不是放大的替代关节。网页“分步定位”在完整模型上高亮零件，爆炸图仅帮助识别，不代表实际装入路径。

![实尺寸联装](images/installed.png)

## 打印和复用

| 工程 | 零件 | 用途 |
|---|---|---|
| [P0试配](printing/P0_fit.3mf) | C3-01 | 先检查光杆、普通螺母、方孔；不装入样件 |
| [P1肘](printing/P1_H_elbow.3mf) | H3-01～03 | 实际肘关节3件 |
| [P2旋转](printing/P2_R_roll.3mf) | R3-01～04 | 实际前臂旋转关节4件 |
| [P3腕](printing/P3_W_wrist.3mf) | W3-01～09 | 实际腕部9件 |
| [P4附件](printing/P4_removable_test_tools.3mf) | F3-H、F3-R、F3-W、F3-M | 3根加载杆及腕部夹持柄 |

全部单位mm。A1 mini / 0.4mm喷嘴 / PLA / 0.12mm层高 / 5圈墙 / 100%填充 / 自动支撑。沿用工程方向；孔和槽中必须去净支撑。两半件合模面朝下；不要靠压弯半件或强拧螺钉来补偿打印误差。摩擦耳厚3mm，去毛刺但不要随意磨薄。光杆应滑入Φ4.25导向孔；过紧先停止并记录C3试片结果。

旧H、R的打印件不混装。T2-H是通用摩擦样条，不是这次的实臂样件。若已打印且无损，旧T1-S1/S2/S3的W01、W02、W03可对应复用W3-01、02、03；T3的W3-04～09重新打印，其中衬片增加了垫圈直入通道。未打印的用户直接使用本包全部新文件。原T1、T2和O24D文件未覆盖。

## 先区分五金

普通M2/M3/M4螺母均无塑料圈，进入对应六角槽止转。全套只有球体合模的两颗M2使用尼龙锁紧螺母：金属螺纹端朝螺钉来向，尼龙圈端朝螺钉露出方向。在尼龙圈处要用工具旋过，不能按压穿过。不要把高3mm的M2尼龙型放进高1.6mm普通型槽里。

摩擦用12mm大垫圈：光滑面朝3mm转动耳/转盘，两片光滑面相向；先清除锐毛刺。小垫圈或反力垫：光滑面朝打印件；两侧都是金属时只要求平整去毛刺。绿色面是网页识别提示，实物不用涂色。

A8是碟簧，不是开口弹簧垫圈。每组两片，第一片内孔凸边朝螺钉头，第二片翻面朝关节，两片内孔边相对；自由叠高约1.2mm。蓝色弹簧仅为识别。不要同向套叠，更不能把两片压成0.8mm平片。

## H 装配顺序

1. H3-01合模面朝上，装入两颗普通M3调节螺母和两片9×3.2×0.8反力垫，再合上H3-02。
2. 用两套普通M3、7×3.2×0.5垫圈和M3×12固定两半。螺钉头朝后，按模型方向，避免屈肘干涉。
3. 两侧固定叉端面各放一片12×4.3×1大垫圈，光滑面向外。H3-03从远端沿骨轴套入，对准两侧孔。
4. 每侧依次放外侧12mm大垫圈（光滑面向内）、相对的两片A8、9×4.3×0.8头下垫、O22肩螺钉Φ4×8/M3牙长6。3mm内六角调节，内藏普通螺母止转。
5. 先轻接触，左右交替微调，不靠轴孔过盈持姿。H3-03方孔装实际R模块上端，或单独测试时装F3-H。用M3×18、0.5mm垫圈及普通M3；垫圈光滑面朝叉。保留方键座夹紧缝。

## R 装配顺序

1. R3-01合模面装普通M3及9mm反力垫，合上R3-02，用两套M2×12、0.5mm垫圈及普通M2固定。
2. 在桌面先给R3-03背面放两颗普通M2壳盖螺母，随后才装转盘；安装后背面会被固定芯挡住。
3. 固定芯端面起依次为12mm大垫圈、3mm转盘、12mm大垫圈、相对A8两片、9mm头下垫、O22肩螺钉。两大垫圈光滑面夹转盘。
4. 罩上R3-04，用两套M2×14及0.5mm垫圈紧固到预装普通螺母。这里不能用M2×16，螺钉末端可能进入固定芯的旋转区域。
5. 单独测试装F3-R并用额外的M3×20、普通M3和0.5mm垫圈。联装时取下F3-R，装实际W上桥。R预紧调整工具从输出中心通道伸入；先卸W和横穿方键的连接螺钉，再用3mm内六角调节。

## W 装配顺序

1. W3-01内先装两颗普通M2导向螺母、两片5×2.2×0.5钢垫圈及W3-03磁铁占位块，合上W3-02。用两颗M2×14及两颗M2尼龙锁紧螺母固定球体。两颗外侧导向轴肩螺钉暂不装。
2. 上桥W3-08先定位。在一旁将W3-04、05衬片分别从球心方向装入W3-06、07。衬片耳每处用普通M2、0.5mm垫圈和M2×6；螺钉从球心侧旋入，垫圈光滑面朝衬片。此时球窝尚未包住球，工具有入口。
3. 带衬片的两个球窝从左右包上球体，然后让球回到中立位。现在才从外侧装Φ2.5×6/M2牙长4的导向肩钉，用2mm内六角，肩部夹钢垫圈和金属螺母，不夹薄塑料小环。
4. 厚耳外侧装两颗普通M4 AF7×3.2，承压面朝槽底。另一侧每处依次为9×4.3×0.8垫圈（光滑面朝耳）、相对A8两片、9mm头下垫、M4×35。用3mm内六角，两处交替微调。不要换M3，A8由M4杆导向。
5. 联装用W3-09掌柄、普通M2、0.5mm垫圈及M2×14。独立测力换F3-W，用M2×20、两片0.5mm垫圈及普通M2；另将F3-M装入上桥作为台钳夹持柄。不可夹压球窝来增加摩擦。
6. 腕部球窝需要对称向内微移来消除球面名义间隙；保持上桥两侧仍有间隙，不能先顶住上桥。若球心偏移、某一侧先顶住、导向槽卡死或球不圆，不继续加力。

## 联装、预紧和锁固

R上端方键沿骨轴插入H，固定芯的连接孔对准H的横孔。R转子中立钟位为+90°，对应既有前臂零位−90°定义；转到能让R下端方键的横孔与W上桥横孔一致的位置后插入W。取下所有加载杆和腕夹持柄。连接后肘心E到球心W仍是80.496305mm。16个关节打印件与独立测试件完全相同，没有临时放大版内核。

先在约1.2mm自由叠高附近轻接触，先消除松旷再测扭矩。每次约1/24圈以内，H左右、W两处交替。H/R的0.9～1.2mm仅是数字堆叠核对区间，不是保证达到某个力的档位；W所需力很小，优先在接近自由高度处调。名义下限0.90mm，若达不到目标也不要继续压平。叠高可通过“头下垫外面到相邻大垫外面距离，减去0.8mm头下垫厚”估算；用卡尺轻触，别再压缩碟簧。记录具体测量位置和实测厚度。

捕获普通螺母只防螺母跟转，不能证明螺钉不回松。先做头部记号和短测；预紧选定后可在拆开的金属螺纹上按产品说明用低强度、可拆的金属螺纹锁固剂，避免接触PLA、衬片、碟簧及摩擦面。未确认材料兼容和固化条件就先用标线检查，不对涂胶效果作保证。记录“无锁固/锁固产品/固化时间”，长测中头位移动即判失败；不能边磨损测试边无记录地补拧。

本版未给拧紧扭矩值，因为用户这批A8力—位移曲线和打印材料摩擦系数尚未测量。不能把扳手手感当成持姿力。固定接口若仍晃动，先检查支撑、方键尺寸和夹紧缝；不能靠把关节预紧到转不动来掩盖接口松旷。
'''
 test='''# O24C-T3 · 活动范围、持姿、磨损测试

所有实物状态均为待测。用户已报告旧T1 H持姿不足；此前“假设通过”不能作为新设计证据。先测孔和方键，再装低预紧样件，最后测保持力；一次只改变一个预紧量。

## 目标与测力

| 样件 | 角度目标 | 初始筛选保持力矩 | 100mm垂直力臂所需力 |
|---|---|---|---|
| H 肘 | 0～145° | 0.040 N·m | 0.40 N |
| R 前臂旋转 | −85～80° | 0.020 N·m | 0.20 N |
| W 腕 | 屈伸−65～70°，偏摆−20～30° | 两方向各0.006 N·m | 0.060 N |

H可另做0.130N·m／1.30N的高载筛选，但这只检验此肘模块的扭矩余量，不等于肩部三轴封装、承载或全人偶通过。各指标是既有项目的初始筛选目标，不是已经测得的能力。

最好把被测转轴竖直，让测力计沿水平切线拉100mm孔。τ=F×到该转轴的垂直距离；不是永远拿杆长乘力。R的力孔在径向100mm处，H/W在各自中立坐标离关节100mm。W逐轴回零再测另一轴，不在复合姿态中直接套用100mm。重力挂重时计入加载杆、掌柄等运动件的重量和重心，并记录力臂；简单0.4N约40.8g、0.2N约20.4g、0.06N约6.12g只是忽略附件自重的换算，不能直接当挂重合格值。

区分启动力和稳定拖动力。加载时不能把手指抵在关节两侧制造额外夹紧力；H夹上端方杆，R夹上端方键，W夹F3-M方柄。夹具必须固定可靠。

## 顺序与记录

1. C3试片记录实际孔径、4mm肩轴插入力、普通螺母能否入槽、方键间隙。确认3mm摩擦耳平整、球合模无台阶、薄衬片无裂纹。若不合格，先修正打印工艺，不靠螺钉硬拉。
2. 低预紧先跑活动范围；检查硬碰、导向槽卡滞、球心横移、接口松旷。再用目标预紧重复。到极限出现硬阻挡就停，记录真实角度，不硬掰到网页数字。
3. 轻摆50次，静置30分钟，允许一次有记录的重新设定预紧。然后做10分钟静态保持，初始筛选漂移≤2°。同时记录螺钉头标线；头位变化是松动，不算正常磨合。
4. 在0、100、500、1000次往复后记录启动力、拖动力、保持漂移和回差；不清零磨损记录。初始筛选：力矩变化≤20%、无裂纹、无金属脱出、接口无新增松旷。发现裂纹或突变立刻停。
5. 相同姿态放置24小时后重测，检查PLA蠕变和弹簧预紧丢失。用固定机位拍照区分关节转动与方键松动。
6. 三件单测后去掉F3附件，联成真实肘—腕段再测：E-W=80.496305mm，量整段运动质量和重心，按实际姿态算重力矩。确认同样预紧在真实联装负载下能保持；此步未通过不能推进为“已验证手臂”。

记录表在test_records/。空白表示没测，不表示合格。文件生成器不会覆盖已有实测表。主记录包括打印材料、层高、孔处理、弹簧叠高、摩擦面处理、锁固方式、环境温度、力臂、循环数和照片。润滑会改变摩擦，持姿面不要随意上油。

## 尚未验证

真实摩擦系数、用户A8的力曲线、耐久、层间强度、蠕变、实际组装间隙都需要打印测试。数字模型只核对名义几何与装配路径，不能证明承载。R当前为可连续旋转的机械芯，测试按−85～80°限位；没有已定型的硬止挡和穿线方案。传感器、肩部、锁骨、完整人体包络不在本套实物资格范围内。
'''
 design=f'''# O24C-T3 · 设计依据与范围

本版用原UE Quinn的560mm参考人体尺度，实际肘心E、腕心W不动，E-W={FORE:.9f}mm。H物理轴穿E，R沿E-W骨轴，W保留D22球心和既有Rx(偏摆)×Ry(屈伸)顺序。独立样件和联装视图共用同一份网格；只更换加载附件。这是实际肘—前臂—腕模块的打印测试设计，不是再次把关节放大的通用摩擦样条。

![三类模块](images/three_modules.png)

## 如何借鉴O22

H采用两侧O22 Φ4×8/M3牙长6轴肩螺钉，每侧用两片A8反向串联压紧完整3mm转动耳。R沿骨轴使用同一套直接端面摩擦预紧，采用一个同轴转盘，取消原T1的长光轴、两滚珠轴承和偏置浮动压板。W保留球/衬片/弧槽导向原理，预紧耳增厚，加两组A8和M4×35；普通M4螺母被六角槽捕获。

H每个摩擦面、R转盘摩擦面的名义接触面积约98.17mm²（通过0.02mm虚拟压入计算），旧T1 H环形面积约46.6mm²。面积变大不直接等于扭矩按面积增加；保持力取决于轴向压力、摩擦系数、有效半径、变形和磨损。钢垫圈可滑动，不能把两面扭矩简单乘二。A8增加弹性预紧行程，但这批弹簧的力曲线尚未知。

H/R反力壁2.8mm；W负侧耳厚7mm，普通M4槽后反力壁3.7mm，槽周围名义最窄约2.25mm。H上端为居中骨杆及连接叉，R输出方键居中，W上桥为实际骨杆接口。方键配合10/10.3mm并有夹紧缝；0.15mm单边是装配间隙，不是活动部件的安全间距。最低间隙和螺纹余量见verification/，这些是名义值，不含FDM翘曲或钢件公差。

## 验证边界

导出STL重新读入检查封闭性和连通性；导出孔和球面网格拟合轴心；H/R/W实尺寸联装姿态采样；独立加载附件姿态采样；合模、螺母、垫圈、球窝和模块的进件路径；轴肩堆叠0.9/1.0/1.1/1.2mm；主要调节工具直入空间；OrcaSlicer离线切片。只对已生成报告中的检查范围负责，离散采样不等于所有连续组合证明。

本版没有把完整O24C肩部或锁骨改成可打印产品，也没有完成传感PCB、磁铁闭环、布线、R硬限位或全人偶最终装配。上臂参考长仍为{UPPER:.9f}mm，H上端是供后续上臂连接的真实居中接口，但到旧肩部/上臂旋转机构的最终转接未在此包定型。完整人偶仍要求<600mm；560mm是参考人体，580mm是后续包络预算，本包不能据此宣称完整人偶高度已实测合格。

## 追溯

原始参考：cad/revO24/arm.py、cad/revO24C/compact_arm.py。O22 G1装配堆叠见tutorials/assembly-o22/ASSEMBLY.zh-CN.md，现货尺寸来自O12/O22修正及用户确认。T1的S1球体金属导向座和S3衬片入口保留，T3衬片另加直入垫圈避让。

碟簧排列和工作行程的一般依据：[SPIROL设计指南](https://www.spirol.com/assets/files/dsc-disc-spring-design-guide-us.pdf)。它不是用户A8批次的力值证书。螺纹锁固与标线检查不构成实测抗松动结论。

后续推进完整人偶必须先读取本版实测记录。旧H失败、T3未测两个状态都不得覆盖成“通过”。O24D既有文件保持原样。
'''
 assembly=assembly.replace('16个','15个').replace('W3-01～09 | 实际腕部9件','W3-01～05、07～09 | 实际腕部8件')
 assembly=assembly.replace('上桥W3-08先定位。在一旁将W3-04、05衬片分别从球心方向装入W3-06、07。','在一旁将W3-04衬片装入W3-08固定侧球窝与骨杆桥一体件，将W3-05装入W3-07浮动球窝。两者均从球心方向装入。')
 assembly=assembly.replace('腕部球窝需要对称向内微移来消除球面名义间隙；保持上桥两侧仍有间隙，不能先顶住上桥。若球心偏移、某一侧先顶住、导向槽卡死或球不圆，不继续加力。','负侧球窝与骨杆桥已连成一件W3-08，固定腕的位置基准；只让W3-07浮动侧向内微移消除间隙，两颗预紧螺钉交替微调。浮动耳与上桥仍须有间隙，不能顶住上桥形成压力旁路。球面名义径向配合间隙0.05mm，压紧时存在约0.06mm量级的就座移动，实际值受打印误差影响；这不是允许整个球窝沿螺钉窜动。若目视可见窜动、导向槽卡死或球不圆，先停止。')
 assembly += '\n固定侧一体件中两处连续连接承担反力，不另打印W3-06。导向轴肩螺钉最终按金属锁固要求处理；试装和短测先标记，未确认材料兼容与锁固固化条件时不把耐久结果标作通过。\n'
 design=design.replace('W保留球/衬片/弧槽导向原理，预紧耳增厚，加两组A8和M4×35；普通M4螺母被六角槽捕获。','W保留球/衬片/弧槽导向原理，负侧球窝与骨杆桥一体定位，正侧浮动。预紧耳增厚，加两组A8和M4×35；普通M4螺母被六角槽捕获。避免整组球窝沿贯穿螺钉窜动。')
 for name,txt in [('ASSEMBLY',assembly),('TEST_PLAN',test),('DESIGN',design)]:
  (OUT/(name+'.zh-CN.md')).write_text(txt,encoding='utf8');(OUT/(name+'.html')).write_text(page('O24C-T3 '+name,pages.mdhtml(txt)),encoding='utf8')
 bt='<table><tr><th>五金规格</th><th>数量</th><th>样件</th></tr>'+''.join('<tr><td>'+html.escape(b['spec'])+'</td><td>'+str(b['qty'])+'</td><td>'+','.join(b['stations'])+'</td></tr>' for b in bom)+'</table>'
 (OUT/'HARDWARE.html').write_text(page('O24C-T3 五金', '<h1>整套五金与方向</h1><p>数量包含三件可分别固定和加载所需的附件紧固件。联装后拆下F3附件，多出的螺钉收存。你已确认有O22轴肩螺钉与A8，但请核对数量：本套需要3颗和10片。不要按外观替换螺母高度、肩长或垫圈厚度。</p>'+bt+'<p>0.5mm M2垫圈已写入新模型。本版不使用M6大垫圈。重点核对M3×18（H方键）、M2×14（R壳盖）、M4×35（W预紧）；参数不同不能直接换长。</p><p>每件金属零件的编号、具体位置和朝向见三维零件下拉框与装配手册。只有球体合模两颗M2使用尼龙锁紧型。</p>'),encoding='utf8')
 lessons_data=lessons();put(OUT/'assembly_steps.json',lessons_data)
 (OUT/'PARTS.html').write_text(page('O24C-T3 零件表','<h1>逐件编号与参数</h1><table><tr><th>编号</th><th>名称 / 规格</th><th>装配注意</th></tr>'+''.join('<tr><td>'+r['id']+'</td><td>'+html.escape(r['label'])+'<br>'+html.escape(r['spec'])+'</td><td>'+html.escape(r['note'])+'</td></tr>' for r in rows)+'</table>'),encoding='utf8')
 (OUT/'test_records').mkdir(exist_ok=True)
 columns=['样件','日期','材料/批次','打印层高','孔/摩擦面处理','弹簧叠高mm','锁固产品/固化时间','环境温度C','轴/姿态','力臂mm','循环数','启动力N','拖动力N','保持10min漂移deg','24h漂移deg','头标线变化','接口回差','裂纹/磨屑','照片','结论']
 for st in ['H','R','W']:
  p=OUT/'test_records'/(st+'_measurements.csv')
  if not p.exists():
   with p.open('w',encoding='utf-8-sig',newline='') as f:w=csv.writer(f);w.writerow(columns);w.writerow([st]+['']*(len(columns)-1))
 body='<p class="eyebrow">O24C-T3 · MECHANICAL TEST / UNTESTED</p><h1>把三个样件接回真实骨轴</h1><div class="hero"><div><p>H肘、R前臂旋转、W腕部，共用实臂尺寸和同一份零件。肘心到腕心 <b>80.496305 mm</b>。</p><a class="button" href="viewer/index.html">查看实尺寸联装</a><a class="button" href="ASSEMBLY.html">打印与装配</a><a class="button" href="PoseDoll_O24C_T3_Arm_Test_Kit.zip">完整下载包</a><p class="note">数字几何已检查，实际持姿和磨损待测。H/R/W先分别测，再去掉加载附件联装复测。肩部、锁骨及全人偶尚未完成验证。</p></div><img src="images/installed.png" alt="同一零件联装为实际肘—前臂—腕"></div><div class="cards"><div class="card"><b>H</b>两侧同轴碟簧<br>实际肘叉，目标0–145°</div><div class="card"><b>R</b>沿骨轴的摩擦转盘<br>目标−85–80°</div><div class="card"><b>W</b>球窝弹性预紧<br>保留D22球心和现货导向肩钉</div></div><h2>先打印哪一盘</h2><p>先P0试配；P1～P3是16个实际关节零件。P4只有4个可拆加载/夹持附件。若旧W01～03无损可复用；H、R及W04～09改用本包新件。</p>'+''.join('<p><a href="'+p['file']+'">'+p['id']+' · '+str(p['count'])+'件</a></p>' for p in json.loads((OUT/'printing/plates.json').read_text('utf8'))['plates'])+'<p><a href="HARDWARE.html">五金参数与数量</a> · <a href="PARTS.html">每个零件说明</a> · <a href="TEST_PLAN.html">测力与磨损记录方法</a> · <a href="DESIGN.html">依据及未验证范围</a></p><h2>检查报告</h2><p>名义尺寸和离散采样，不能代替实物承载验证。</p>'+''.join('<p><a href="verification/'+x+'.json">'+x+'</a></p>' for x in ['geometry','installed_rom','bench_rom','assembly_paths','module_insertion','ue_alignment','mechanics','slicing','browser','delivery'])
 body=body.replace('16个','15个')
 (OUT/'START_HERE.html').write_text(page('O24C-T3 实际手臂三样件',body),encoding='utf8')
 (OUT/'README.txt').write_text('O24C-T3 actual elbow / forearm roll / wrist test kit\nOpen START_HERE.html; offline viewer works from file without CDN.\n15 actual joint prints + 4 removable test tools + 1 optional fit coupon.\nSee ASSEMBLY.html and TEST_PLAN.html. Physical holding/wear UNTESTED.\nW3-08 is integral fixed socket + bridge. No separate W3-06.\nThis does not qualify the shoulder, clavicle, electronics, wiring or full doll.\n',encoding='utf8')

def smooth(p):
 id=p['id'];st=p['station']
 if id.startswith(('HL_','HR_')):
  sign=-1 if id.startswith('HL_') else 1
  if id.endswith(('F1','RW')):return [0,sign,0]
  if id.endswith('F2'):return [0,-sign,0]
 if id in ['R_F1','R_RW']:return [0,0,-1]
 if id=='R_F2' or (id.startswith('RO') and id.endswith('W')):return [0,0,1]
 if id.startswith('HC') and id.endswith('W') or id=='H_R_W':return [1,0,0]
 if id.startswith('WL') and id.endswith('W'):return [0,-1 if id.startswith('WL-1') else 1,0]
 if id.startswith('WP') and id.endswith('W0'):return [0,-1,0]
 if id in ['W_R_W','WPALM_W','FR_W','FW_W1'] or id.startswith('RC') and id.endswith('W'):return [-1,0,0]
 if id=='FW_W2':return [1,0,0]
 return [0,0,0]

def viewer():
 data=json.loads((OUT/'assembly.json').read_text('utf8'));z=np.load(OUT/'assembly_meshes.npz');chunks=[];count=0
 for r in data['parts']:
  v=z['v'+str(r['index'])];f=z['f'+str(r['index'])];tri=v[f];n=np.cross(tri[:,1]-tri[:,0],tri[:,2]-tri[:,0]);norm=np.linalg.norm(n,axis=1);n=n/np.maximum(norm[:,None],1e-15)
  packed=np.concatenate([tri,np.repeat(n[:,None,:],3,axis=1)],axis=2).reshape(-1,6).astype('<f4');chunks.append(packed);r.update(start=count,count=len(packed),smooth=smooth(r));count+=len(packed)
 data.update(geometry=base64.b64encode(np.vstack(chunks).tobytes()).decode(),geometry_sha256=sha(OUT/'assembly_meshes.npz'),steps=lessons())
 (OUT/'viewer').mkdir(exist_ok=True);(OUT/'viewer/data.js').write_text('window.KIT='+json.dumps(data,ensure_ascii=False,separators=(',',':'))+';',encoding='utf8')
 for name in ['viewer.js','viewer.html']:
  shutil.copyfile(HERE/name,OUT/'viewer'/('index.html' if name.endswith('.html') else 'viewer.js'))

def package():
 (OUT/'source').mkdir(exist_ok=True)
 for p in HERE.iterdir():
  if p.suffix in ['.py','.js','.html']:shutil.copyfile(p,OUT/'source'/p.name)
 refs=[H/'cad/revO24/arm.py',H/'cad/revO24C/compact_arm.py',H/'cad/revO24C_T1/kit.py',H/'cad/revO24C_T1/printing.py',H/'bench/revO24C/assembly_meshes.npz',H/'bench/revO24C_T1/assembly_meshes.npz',H/'bench/revO24C_T2_H/assembly_meshes.npz']
 put(OUT/'reference_baselines.json',{str(p.relative_to(ROOT)):sha(p) for p in refs})
 excluded={'manifest.json','PoseDoll_O24C_T3_Arm_Test_Kit.zip'}
 files=[p for p in OUT.rglob('*') if p.is_file() and p.name not in excluded and '.blend1' not in p.name]
 put(OUT/'manifest.json',dict(revision=REVISION,geometry_sha256=sha(OUT/'assembly_meshes.npz'),files=[dict(path=p.relative_to(OUT).as_posix(),sha256=sha(p),bytes=p.stat().st_size) for p in sorted(files)]))
 with zipfile.ZipFile(OUT/'PoseDoll_O24C_T3_Arm_Test_Kit.zip','w',zipfile.ZIP_DEFLATED) as z:
  for p in files+[OUT/'manifest.json']:z.write(p,p.relative_to(OUT).as_posix())
 print('PACKAGED',len(files),'files',flush=True)

if __name__=='__main__':
 if '--package' in sys.argv:package()
 else:docs();viewer()
