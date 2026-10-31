"""Chinese instructions, exact-mesh step viewer, records and release packaging."""
from spring_hinge import *
import base64,shutil,zipfile,html,re,importlib.util
spec=importlib.util.spec_from_file_location('t1_pages',H/'cad/revO24C_T1/package.py')
old_pages=importlib.util.module_from_spec(spec);spec.loader.exec_module(old_pages)

def lessons():
    s=[]
    def step(title,ids,text,tool='手放 / 镊子仅用于放置',path=None,kind='add',camera='front'):
        s.append(dict(number=len(s)+1,title=title,ids=ids,text=text,tool=tool,path=path or [[0,25,0],[0,0,0]],kind=kind,camera=camera))
    step('确认新件与基座方向',['H2-01'],'只使用 H2-01 / H2-02 / H2-03。小轴孔的一面为正面，大圆腔为背面。本样件所有 M3 螺母都是普通螺母，无尼龙圈。',path=[[0,0,0],[0,0,0]])
    step('从背面放入反力垫',['M03'],'用 O22 的 M3 大垫圈 9×3.2×0.8，光滑面朝孔内反力壁。它应平放在大圆腔最深处；不能换成 T1 的 7×3.2×0.5 小垫圈。',path=[[0,-25,0],[0,0,0]],camera='rear')
    step('单独拿出止转后盖',['H2-03'],'先在基座旁装好后盖上的螺母。带圆形凸台和六角槽的一面朝你；这时还不合上基座。',path=[[48,-25,0],[48,0,0]],camera='front')
    step('把调节螺母放入后盖',['M02'],'普通 M3×0.5、对边5.5、高2.4。平整承压面朝凸台开口，之后贴反力垫。螺母应进入六角槽，不能自由转一圈。不要用带塑料圈的锁紧螺母。',path=[[48,22,0],[48,0,0]])
    step('带螺母的后盖合到基座',['H2-03','M02'],'托住螺母，把圆形凸台从背面直送入大圆腔。后盖平面贴住基座背面；不能用螺钉硬拉未入位的后盖。',kind='move',path=[[48,0,0],[48,-25,0],[0,-25,0],[0,0,0]],camera='rear')
    for i in [1,2]:step(f'放入第 {i} 颗后盖固定螺母',[f'C_N{i}'],'普通 M3×0.5，AF5.5，高2.4；平整承压面朝六角槽底。装进基座正面的六角槽，应沉入表面，不能突出。')
    for i in [1,2]:
        step(f'后盖第 {i} 处放小垫圈',[f'C_W{i}'],'M3 平垫圈 7×3.2×0.5，光滑面贴后盖。可从旧 H 拆用，先检查是否变形。',path=[[0,-25,0],[0,0,0]],camera='rear')
        step(f'旋入后盖第 {i} 颗固定螺钉',[f'C_S{i}'],'M3×12 内六角圆柱头螺钉，从背面旋入已被六角槽固定的普通螺母。先对牙，再轻紧；两颗交替贴合即可，不用把 PLA 压变形。','2.5 mm 内六角扳手',path=[[0,-25,0],[0,0,0]],camera='rear')
    step('检查后盖与反力座',[],'后盖不能晃动，中央螺母不能跟转，反力垫不能倾斜。后盖只负责定位螺母；主要压力经螺母→反力垫→整体反力座传递。','目视 / 轻推检查',kind='check')
    step('放内侧大垫圈',['F01'],'M4 大垫圈 12×4.3×1.0，光滑面朝外，即朝接下来要装的转动杆。先使正面朝上，支撑或夹稳基座，再叠装。')
    step('放整体转动杆',['H2-02'],'圆盘孔对准轴心。圆盘厚3.00 mm，两面去毛刺且平整；转动杆要能在金属轴肩上自由转动，不能先靠孔壁过盈产生阻力。')
    step('放外侧大垫圈',['F02'],'第二片 12×4.3×1.0，光滑面朝内，贴转动杆。现在两片大垫圈的光滑面相向，夹住转动杆圆盘。')
    step('放第一片 A8 碟簧',['SP01'],'8×4.2×0.4，自由高约0.6。内孔附近凸起的边朝外（朝未来的螺钉头）；外圆边靠外侧大垫圈。蓝色只为识别碟簧，实物不需涂色。')
    step('第二片碟簧翻面安装',['SP02'],'第二片要翻面：内孔凸起边朝内（朝固定座）。两片在内孔边相对接触，外圆边分开。不能同向套叠；不要用开口弹簧垫圈替代。')
    step('放头下普通 M4 垫圈',['M04'],'M4 普通平垫圈 9×4.3×0.8，放在碟簧外侧。这一片两面均贴金属，没有强制正反；两面均须去毛刺，能自由套过 Φ4 光杆。')
    step('旋入 O22 轴肩螺钉',['AX01'],'光杆Φ4×8，M3×0.5螺纹长6，头Φ7×3。先用手轻旋对牙，再用3 mm内六角。它是旋入普通螺母，不是直接压过去；动画中的螺纹为简化外形。','3 mm 内六角扳手',path=[[0,25,0],[0,0,0]])
    step('从轻接触开始调整',[],'转动杆仍要能动。消除松旷后，每次只微调约1/24圈并复测。优先试两片总高1.10、1.00 mm；名义下限0.90 mm。不要拧到碟簧压平或靠孔底顶死来获得阻力。详见手册中的实测高度方法。','3 mm 内六角 / 卡尺 / 记号笔',kind='check')
    step('检查活动范围',[],'先低预紧，再以目标预紧检查：肩部工况−45°～165°，肘部工况0°～145°。下方角度滑块只演示几何，不代表持姿已通过。','夹具 / 量角器',kind='rom')
    step('先测肘，再测肩',[],'先筛选0.040 N·m，再尝试0.130 N·m。在100 mm力臂上分别是0.40 N和1.30 N。保持10分钟并记录漂移；标记轴肩螺钉头相对基座的位置。螺母止转不等于螺钉不会回松。','测力计或称量砝码 / 固定视角照片',kind='check')
    return s

def mdpage(title,body):
    style=old_pages.STYLE
    nav='<nav><a href="START_HERE.html">新版入口</a><a href="viewer/index.html">逐步装配 / 三维</a><a href="ASSEMBLY.html">装配说明</a><a href="TEST_PLAN.html">测试方法</a><a href="BOM.csv">五金清单</a></nav>'
    return f'<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{title}</title><link rel="icon" href="data:,"><style>{style}</style></head><body>{nav}{body}</body></html>'

def docs():
    assembly='''# O24C-T2-H · 碟簧预紧样件

这是替代旧 H 机械方案的新测试件，不能混装旧 H01～H08。用户已报告旧 H 持姿明显不足；不能再把旧 H 当作“实物验证通过”。本版只验证 H，不代表 R、W 或完整人偶已经验证。

![新样件实际模型](images/assembled.png)

## 需要重新打印什么

| 编号 | 名称 | 数量 | 要点 |
|---|---|---:|---|
| H2-01 | 整体反力座 | 1 | 连续反力壁；无旧 H04 的悬臂压板 |
| H2-02 | 100 mm 整体转动杆 | 1 | 3 mm 厚、Φ4.25 轴孔；没有轴承 |
| H2-03 | 普通螺母止转后盖 | 1 | 六角槽固定螺母，正面只需一把内六角调节 |
| H2-C01 | 试配片，可先单独打印 | 1 | 三个孔从左到右4.15 / 4.25 / 4.35，六角槽AF5.8 |

完整样件打印工程是 [P1_H2_sample.3mf](printing/P1_H2_sample.3mf)，内含前三件。试配片单独在 [P0_H2_fit.3mf](printing/P0_H2_fit.3mf)。不要把试配片装进关节。

A1 mini、0.4 mm喷嘴、PLA、0.12 mm层高、5圈墙、100%填充；使用工程中的方向与支撑设置。H2-01小孔正面朝下，H2-03平背面朝下，H2-02平放。先清理孔、螺母槽与摩擦面上的支撑和象脚，不把3 mm圆盘磨薄来强行适配。4 mm光杆应能滑过转动孔；孔紧或槽不能装入时先停止，记录实际尺寸，不靠大扭矩硬拉。

## 五金清单与复用

| 五金 | 净数量 | 来源 / 参数 |
|---|---:|---|
| O22轴肩螺钉 | 1 | 光杆Φ4×8，M3×0.5螺纹长6，头Φ7×3，内六角3 mm；用户确认已有 |
| A8碟簧 | 2 | 8×4.2×0.4，自由高约0.6 mm；用户确认已有 |
| M4大平垫圈 | 2 | 钢制12×4.3×1.0，可拆用旧H |
| M4普通平垫圈 | 1 | 钢制9×4.3×0.8，可拆用旧H后桥 |
| M3大平垫圈 | 1 | 钢制9×3.2×0.8，O22规格；不能用7×3.2×0.5替代 |
| 普通M3六角螺母 | 3 | M3×0.5，AF5.5，高2.4，无尼龙圈；可拆用旧H转子 |
| M3×12内六角圆柱头螺钉 | 2 | 2.5 mm内六角；可拆用旧H转子 |
| M3小平垫圈 | 2 | 钢制7×3.2×0.5；可拆用旧H |

本样件不使用684ZZ轴承、D4×45光轴、旧H的M3×30预紧螺钉或尼龙锁紧螺母。不要为了继续利用它们而加回新摩擦链。旧件保存好，方便对照。

## 压紧力怎样传递

轴肩螺钉头 → M4普通垫 → 两片反向碟簧 → 外侧大垫 → 转动杆 → 内侧大垫 → 整体反力座 → M3反力垫 → 内藏普通M3螺母 → 螺钉。

后盖只负责定位和阻止螺母转动，不用后盖的薄边承担主要预紧。它的凸台与反力垫之间名义留0.15 mm，螺母直接顶反力垫。反力座内部承压壁名义厚2.8 mm；其强度和松弛仍需实测。

![碟簧方向及高度量法](images/spring_stack.svg)

碟簧负责在小位移内提供弹性预紧；摩擦来自受压接触面。增加碟簧不等于自动增大摩擦系数，也不保证长期不掉力矩。两片反向串联用于增加可用位移，不是把单片弹力简单翻倍。

## 逐步装配

每一步的实际零件和运动方向也可在 [逐步装配页](viewer/index.html) 查看。先夹稳或托稳基座，换面时用手托住尚未固定的垫圈。不要把动画里悬空停住的零件当成实物能自动固定。

'''
    for s in lessons():
        assembly+=f'### {s["number"]}. {s["title"]}\n\n'
        if s['ids']:assembly+='本步零件：'+ ' / '.join(s['ids'])+'。\n\n'
        assembly+=s['text']+'\n\n工具：'+s['tool']+'。\n\n'
    assembly+='''## 预紧高度：先实测，不把圈数当力

本版模型用两片总高1.00 mm作展示；不是要求装到这个数值才算正确。若单片自由高0.60、材料厚0.40，则两片反向的自由总高约1.20，压平总高0.80。试验先从1.10、1.00逐步比较；0.90对应名义75%压缩。没有本批碟簧的力—位移数据，不继续压到0.80或反向翻碟。

量法：以H2-01的平整背面为A面（避开后盖及其螺钉），轴肩螺钉头最外端为B面。用卡尺保持与轴平行量A—B。名义总高D = 16.80 + 两片碟簧总高；例如D=17.80对应1.00 mm。实际要减去实测的“基座厚度 + 两片大垫厚度 + 转动圆盘厚度 + 头下普通垫厚度 + 螺钉头高”，不能直接假定它们恰好合计16.80。A面在后盖外侧露出，量爪不能搭在后盖或固定螺钉头上。

如果量爪无法稳定贴住这两个面，不用一个不可靠的小数继续加压。先记录轻接触位置、小幅调整量和实际持姿；达到合理压缩范围仍轻拨即动，本版就应判为未通过，不以继续拧紧掩盖。

普通螺母被槽固定后，调节过程只需正面一把内六角。它解决装配时的止转，不构成对轴肩螺钉的独立防松锁。做双向循环时检查螺钉头相对基座的记号；回松则本版锁固未通过。首次对比不加胶、不润滑摩擦面，便于分辨压紧不足、磨损和螺钉回转。

## 与 O22 的关系和验证边界

轴肩、垫圈、两片碟簧和普通螺母的层次依据仓库O22装配说明G1；螺纹长6 mm及反力座深度参考O12现货样件。此前O22沿用的实物经验是选择这一结构的理由，不是新H已经通过的证据。

数字检查包括4个簧片高度下844个活动姿态、装入路径、力链接触、轴肩底部余量、普通螺母止转、直杆工具空间和离线切片。不包括实际接触压力、材料强度、碟簧弹力或持姿寿命。尺寸检查通过后仍按 [测试计划](TEST_PLAN.html) 记录实测结果。

参考：[SPIROL碟簧设计指南](https://www.spirol.com/assets/files/dsc-disc-spring-design-guide-us.pdf)；[SPIROL压缩范围说明](https://my.spirol.com/resources/white-papers/how-deflection-range-affects-the-performance-of-disc-springs/)。这些资料支持一般原理，不代表用户现有A8碟簧具有其中某个型号的力值。
'''
    test='''# O24C-T2-H · 持姿与磨损测试

当前状态：新样件未经过实物验证；旧H已由用户报告持姿不足。不要填写假定通过的数据，不把旧H的循环次数接到新件上。

## 先回答最关键的问题

先做肘部工况0.040 N·m，再做肩部工况0.130 N·m。这两个值来自O24C/T1原有台架筛选预算；未来完整人偶仍须按真实质量和力臂重算。

固定座夹稳，只夹固定座，不能夹住转动杆、垫圈或轴肩头。先确认后盖与内部螺母不动、转动杆无明显轴向晃动，随后微调轴肩螺钉。先试轻接触，再以两片总高约1.10、1.00 mm比较；名义0.90以下不继续拧紧求持姿。

用记号笔标螺钉头相对固定座的位置；同时给两片大垫圈边缘做小记号，观察摆动时哪些界面在滑。只在外缘标记，不能涂到摩擦面。

## 力矩怎么量

优先把转轴竖直、转动杆放在水平面，用水平方向、垂直杆的力拉100 mm孔：τ=F×实测垂直力臂。名义100 mm时，0.040 N·m对应0.40 N，0.130对应1.30 N。正反向各3次，分别记录刚启动和持续转动的力，不把内六角拧紧力矩当成关节力矩。

若水平摆杆挂砝码测持姿，要计算杆和随动件的自重力矩，以及挂钩和线的重量。忽略自重时40.8 g / 132.6 g只是换算值，不能照挂后就称达到目标。实际总力矩=9.80665×（挂载总质量kg×实测孔距m + 随动件质量kg×重心水平力臂m）。不确定重心就改用前一种竖轴水平拉力法。

## 分阶段记录

1. 磨合前：低预紧下检查−45°～165°；肘部单列0°～145°。卡点、孔壁摩擦与摩擦面阻力分别记录。
2. 调到目标后慢速往返50次，静置30分钟，允许重新调节一次，记录为磨合后基线。一个循环为0°→120°→0°，约5～10次/分钟。
3. 在目标载荷下保持10分钟，记录0、1、5、10分钟角度。初轮筛选：漂移≤2°，没有持续滑落、裂纹、螺钉头转动或夹具自身移动。
4. 累计100、500、1000次分别复测正反向起动/运行力矩、10分钟持姿、轴向晃动和见证线。先测再补紧；同一设定力矩变化≤20%作为本轮比较门槛。
5. 目标预紧下静置24小时，再测力矩和见证线。螺钉没转但力矩下降，与螺钉确实回松分开记录。拆检两面磨粉、压痕、孔磨损和碟簧是否恢复。

如果合理预紧范围内仍轻拨即动，或拧一点就从松变卡，先记录为“不通过”，不要跳到1000次。若螺钉自行转动，则锁固需再设计；若转动杆本身弯曲，要区分杆变形与关节滑动。纸质5°刻度只用于ROM，2°漂移用固定相机或更细量角工具判断。

## 测试之后才做的决策

先比较旧H与新H在相同加载方式下的可调范围、持姿与磨损。只有新H既能保持姿势又能顺畅移动，才把有效结构缩回完整手臂的封装。肩部/肘部中心、UE骨段中心线和整偶小于600 mm的要求仍有效；本台架不是整偶关节的外形定稿。R/W与O24D的相应结构不能自动沿用“已通过”的结论。

记录表在 [measurements.csv](test_records/measurements.csv)，空白代表待测；填写样件、材料、打印参数、实测五金尺寸和任何打磨情况。
'''
    design='''# O24C-T2-H · 设计依据与交接

日期：2026-10-24。用户只安装了T1的H样件，报告光轴支撑松、手压两侧后转子仍几乎无持姿阻力，并要求借鉴O22碟簧重新试制。这里记录的是用户的定性观察，没有捏造力矩、材料或磨损测量。

## 旧H可从模型确定的内容

T1的H04/H05用于支承和锁住D4光轴；684ZZ轴承允许转子绕轴转动。夹住光轴不等于给转子提供持姿力矩。持姿另外依赖H03与H04固定压板，通过偏置的两颗M3×30压紧转子端面。模型没有弹性预紧元件，也没有真实接触压力与变形结果。无法仅凭此次描述断定实物是哪里先接触、哪一处失去压力，更不能归咎于用户没拧紧。

## 新样件改变的机制

去掉独立光轴、轴承和偏置夹板，用O22的D4×8/M3×6轴肩直接同时提供转轴与同轴拉紧。反向A8碟簧串联提供弹性行程，两片12×4.3×1钢垫夹住3 mm打印转动圆盘。完整底座与9×3.2×0.8金属反力垫承压，后盖捕获普通M3螺母。无需一手扶螺母、一手扶螺钉来穿过尼龙圈。

名义端面接触面积从T1每侧约46.6 mm²变为约98.6 mm²，有助于降低同载荷平均压强；这本身不是摩擦力矩倍增。新环面的均压有效半径约4.38 mm，比旧窄环还小。大垫圈没有键止转，因此不得直接假定两面摩擦力矩都能全部相加。

仅作敏感性分析：按摩擦系数0.1～0.3、一个有效面，达到0.130 N·m约需99～297 N轴向力；按两个有效面约需49～148 N。摩擦系数、有效面数和用户A8簧片的弹力均未测量。这些不是已达成值，也不是塑料件或螺钉的额定承载力。

## 尺寸与保留的约束

固定座44×32×8，后盖36×18，转动杆轴心至加载孔100 mm，圆盘Φ16×3。转轴Y、原点(0,0,0)，杆中性中心线通过该轴。模型保留−45°～165°单轴活动检查。较大的固定座是测量夹具，不作为完整人偶外壳尺寸；最终UE骨架对齐、常规人类ROM和整偶高度<600 mm仍需重新集成验证。

后盖鼻端离反力垫0.15 mm；六角槽角外最小壁厚约2.55 mm；反力壁2.8 mm。主螺母完整啮合名义2.4 mm，4种弹簧高度下轴肩底余量0.6～0.9 mm；已做假设尺寸波动检查，但没有供应商公差承诺。环形承压壁是连续结构，无旧H04那样的窄边连接。

螺母止转用于方便装配，不是轴肩螺钉的独立防松。当前仍以O22同类做法加双向循环/见证线筛选；如果回松，必须修改锁固，不把加大预紧当作解决方案。H2未做实测，不向R/W或O24D宣称通过。

## 依据

- 仓库 Hardware/PoseDoll44/tutorials/assembly-o22/ASSEMBLY.zh-CN.md 的G1与五金表。
- 仓库 Hardware/PoseDoll44/cad/revO12/build_taobao_bench.py 的6 mm螺纹现货堆叠和轴肩底余量。
- 用户确认现有Φ4×8/M3×6轴肩螺钉与A8碟簧可用。
- [SPIROL设计指南](https://www.spirol.com/assets/files/dsc-disc-spring-design-guide-us.pdf)与[工作压缩范围说明](https://my.spirol.com/resources/white-papers/how-deflection-range-affects-the-performance-of-disc-springs/)，仅用于一般碟簧原理。

源文件在随包source目录；CAD/STL、动画和Blender均来自相同参数模型。verification目录分别记录刚体几何、装配路径、工具、切片和页面检查。原T1文件与既有test_records不改写。
'''
    for name,text in [('ASSEMBLY',assembly),('TEST_PLAN',test),('DESIGN',design)]:
        (OUT/(name+'.zh-CN.md')).write_text(text,encoding='utf8')
        (OUT/(name+'.html')).write_text(mdpage(REVISION+' · '+name,old_pages.mdhtml(text)),encoding='utf8')

def graphics():
    folder=OUT/'images';folder.mkdir(exist_ok=True)
    svg='''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1000 540" width="1000" height="540">
<rect width="1000" height="540" fill="#f5f7ef"/><g font-family="Microsoft YaHei,Arial" fill="#234b41">
<text x="40" y="42" font-size="24" font-weight="bold">两片反向碟簧：内孔边相对，外圆边分开</text>
<text x="40" y="73" font-size="15">侧面示意，锥度夸大；蓝色是识别色，不是五金颜色要求。</text>
<path d="M155 130V295 M810 130V295" stroke="#916341" stroke-width="16"/>
<path d="M200 130L480 181V202L200 151Z M200 295L480 244V223L200 274Z" fill="#4079b3"/>
<path d="M480 181L760 130V151L480 202Z M480 244L760 295V274L480 223Z" fill="#6f9bc6"/>
<path d="M90 212H895" stroke="#657b73" stroke-width="2" stroke-dasharray="8 6"/>
<text x="72" y="325" font-size="17">外侧大平垫圈</text><text x="755" y="325" font-size="17">头下普通平垫圈</text>
<text x="235" y="112" font-size="18">SP01 · 内孔凸边朝右 →</text>
<text x="525" y="112" font-size="18">← SP02 · 内孔凸边朝左</text>
<text x="364" y="270" font-size="17">两片内孔边在这里相对</text>
<text x="44" y="370" font-size="18">← 固定座 / 转动杆方向</text><text x="736" y="370" font-size="18">螺钉头方向 →</text>
<path d="M40 394H960" stroke="#cad7cb"/>
<text x="40" y="430" font-size="18">高度测量：A = 整体反力座背面；B = 轴肩螺钉头顶面。</text>
<text x="40" y="461" font-size="18">名义 A—B = 16.80 mm + 两片碟簧总高；实际须减去实测刚性堆叠厚度。</text>
<text x="40" y="493" font-size="16">两片总高约 1.20 mm 自由 → 1.10 / 1.00 mm 试调 → 0.90 mm 名义下限；不压平。</text>
<text x="40" y="521" font-size="14">普通螺母被捕获是便于装配，不等于螺钉不会回松；以实测持姿与见证线判断。</text>
</g></svg>'''
    (folder/'spring_stack.svg').write_text(svg,encoding='utf8')
    for plate in json.loads((OUT/'printing/plates.json').read_text('utf8'))['plates']:
        shapes=['<svg xmlns="http://www.w3.org/2000/svg" width="720" height="760" viewBox="0 0 180 190"><rect width="180" height="190" fill="#f5f7ef"/><rect x="1" y="1" width="178" height="178" fill="none" stroke="#9db5aa" stroke-width=".3"/>']
        for item in plate['items']:
            m=trimesh.load(OUT/item['stl'],process=True);xy=m.vertices[:,:2]+item['offset_mm'][:2]
            for tri in m.faces:shapes.append('<path d="M'+' L'.join(','.join(f'{n:.3f}' for n in xy[j]) for j in tri)+'Z" fill="#76a99a"/>')
            lo=xy.min(0);hi=xy.max(0);shapes.append(f'<text x="{(lo[0]+hi[0])/2:.2f}" y="{hi[1]+4:.2f}" text-anchor="middle" font-family="Arial" font-size="3">{item["id"]}</text>')
        shapes.append(f'<text x="5" y="186" font-size="4" font-family="Arial">{plate["id"]} / A1 mini / mm</text></svg>')
        (OUT/'printing'/(plate['id']+'.svg')).write_text(''.join(shapes),encoding='utf8')

def viewer():
    data=json.loads((OUT/'assembly.json').read_text('utf8'));z=np.load(OUT/'assembly_meshes.npz');buf=[];parts=[];offset=0
    for p in data['parts']:
        if p['frame']=='coupon':continue
        i=p['index'];xyz=z['v'+str(i)][z['f'+str(i)]];n=np.cross(xyz[:,1]-xyz[:,0],xyz[:,2]-xyz[:,0]);n/=np.maximum(np.linalg.norm(n,axis=1)[:,None],1e-15)
        v=np.concatenate([xyz,np.repeat(n[:,None,:],3,axis=1)],axis=2).reshape(-1,6).astype('<f4');buf.append(v)
        face={'M03':1,'F01':1,'F02':-1,'C_W1':1,'C_W2':1}.get(p['id'],0)
        parts.append(dict(p,start=offset,count=len(v),smooth_face=face));offset+=len(v)
    dest=OUT/'viewer';dest.mkdir(exist_ok=True)
    (dest/'data.js').write_text('window.H2='+json.dumps(dict(revision=REVISION,parts=parts,steps=lessons(),geometry_sha256=sha(OUT/'assembly_meshes.npz'),geometry=base64.b64encode(np.concatenate(buf).tobytes()).decode()),ensure_ascii=False,separators=(',',':'))+';',encoding='utf8')
    for name in ['index.html','viewer.js','style.css']:shutil.copyfile(HERE/name,dest/name)

def records():
    folder=OUT/'test_records';folder.mkdir(exist_ok=True);p=folder/'measurements.csv'
    if not p.exists():
        with p.open('w',encoding='utf-8-sig',newline='') as f:
            w=csv.writer(f);w.writerow(['样件编号','日期','PLA及打印参数','实测尺寸和后处理','碟簧自由总高mm','碟簧安装总高mm','循环数','静置时长min','正向起动力矩Nm','反向起动力矩Nm','正向运行力矩Nm','反向运行力矩Nm','10分钟漂移deg','螺钉记号是否转动','轴向游隙mm','垫圈是否跟转','裂纹磨粉','判定','备注'])

def entry():
    body='''<p class="eyebrow">POSEDOLL LAB / 2026-10-24 / 新 H 样件</p><div class="hero"><div><h1>用碟簧直接预紧，<br>重新验证持姿。</h1><p>O24C-T2-H 沿用你已有的 O22 轴肩螺钉和 A8 碟簧。普通螺母藏在座内，调节时只操作正面一颗螺钉。</p><a class="button" href="viewer/index.html">逐步装配 · 22 步</a><a class="button" href="PoseDoll_O24C_T2_H_Test_Kit.zip">下载完整测试包</a></div><img src="images/assembled.png" alt="新H样件的实际CAD模型"></div>
<p class="note"><strong>旧 H 已报告持姿不足；本版仍待实测。</strong>这是新的机械样件，H2-01 / H2-02 / H2-03 不能与旧 H01～H08 混装。先测肘部 0.040 N·m，再尝试肩部 0.130 N·m；达不到就记录为未通过。</p>
<div class="cards"><div class="card"><b>3 件</b>样件主体打印件</div><div class="card"><b>1 颗</b>正面预紧调节螺钉</div><div class="card"><b>普通 M3</b>本样件无尼龙锁紧螺母</div></div>
<h2>打印这两份工程</h2><table><tr><th>工程</th><th>内容</th><th>切片估时 / PLA</th><th>文件</th></tr><tr><td>P0，可先试配</td><td>H2-C01 孔与螺母试配片</td><td>34分34秒 / 4.37 g</td><td><a href="printing/P0_H2_fit.3mf">3MF</a> · <a href="printing/P0_H2_fit.svg">盘位图</a></td></tr><tr><td>P1，完整新H</td><td>H2-01、H2-02、H2-03，各1</td><td>2小时11分11秒 / 20.34 g</td><td><a href="printing/P1_H2_sample.3mf">3MF</a> · <a href="printing/P1_H2_sample.svg">盘位图</a></td></tr></table>
<p>A1 mini / PLA / 0.4 mm喷嘴 / 0.12 mm层高 / 5圈墙 / 100%填充。已离线切片，未发送打印任务。估时包括机器准备；实际耗时以设备为准。</p>
<h2>沿用哪些五金</h2><p>轴肩螺钉Φ4×8 / M3螺纹长6：1颗；A8碟簧：2片。其余为现有M3普通螺母、M3×12螺钉与平垫圈。特别核对反力垫必须是O22的 <strong>9×3.2×0.8</strong>，不能拿T1的小垫圈代替。</p><a class="button" href="ASSEMBLY.html">完整参数与朝向</a><a class="button" href="BOM.csv">五金清单 CSV</a>
<h2>装配重点</h2><img src="images/spring_stack.svg" alt="两片碟簧内孔凸边相对安装，外圆边分开"><p>先把普通螺母装进止转后盖，再合到整体基座；从正面依次叠装大垫圈、转动杆、大垫圈、反向碟簧、普通垫圈和轴肩螺钉。渐进调整，不拧到压平。</p>
<h2>验证与记录</h2><p>4种碟簧高度、844个姿态的刚体干涉检查通过；装入路径、接触链、螺纹啮合、直杆工具和两个打印盘已检查。尚未证明实物强度、保持力、防松和耐磨。</p><ul><li><a href="TEST_PLAN.html">持姿与磨损测试方法</a> · <a href="test_records/measurements.csv">空白记录表</a></li><li><a href="DESIGN.html">原因分析与后续设计依据</a></li><li><a href="O24C_T2_H.blend">Blender装配</a> · <a href="O24C_T2_H.glb">GLB模型</a></li><li><a href="verification/mechanics.json">几何、装入与力链检查</a> · <a href="verification/slicing.json">离线切片检查</a></li></ul>'''
    (OUT/'START_HERE.html').write_text(mdpage(REVISION,body),encoding='utf8')
    (OUT/'index.html').write_text('<!doctype html><meta charset="utf-8"><meta http-equiv="refresh" content="0;url=START_HERE.html"><a href="START_HERE.html">打开新H样件</a>',encoding='utf8')

def package():
    report=json.loads((OUT/'verification/mechanics.json').read_text('utf8'))
    assert report['passed'] and report['geometry_sha256']==sha(OUT/'assembly_meshes.npz')
    assert json.loads((OUT/'verification/slicing.json').read_text('utf8'))['passed']
    delivery=json.loads((OUT/'verification/delivery.json').read_text('utf8'))
    assert delivery['passed'] and delivery['geometry_sha256']==sha(OUT/'assembly_meshes.npz')
    assert all(sha(OUT/name)==value for name,value in delivery['viewer_assets_sha256'].items())
    dest=OUT/'source';dest.mkdir(exist_ok=True)
    for f in HERE.iterdir():
        if f.is_file():shutil.copyfile(f,dest/f.name)
    put(OUT/'STATUS.json',dict(revision=REVISION,date=DATE,stage='PRINTABLE_PROTOTYPE_PHYSICAL_TEST_PENDING',
        prior_T1_H_user_feedback='2026-10-24: support looseness and inadequate holding reported; no numerical torque measurement provided.',
        physical_tested=False,manufacturing_release=False,assembly_prints=3,optional_fit_coupon=1,parts_must_not_mix_with_T1=True))
    name='PoseDoll_O24C_T2_H_Test_Kit.zip';files={f.relative_to(OUT).as_posix():sha(f) for f in OUT.rglob('*') if f.is_file() and f.name not in [name,'MANIFEST.sha256.json'] and '__pycache__' not in f.parts}
    put(OUT/'MANIFEST.sha256.json',dict(revision=REVISION,files=files))
    with zipfile.ZipFile(OUT/name,'w',zipfile.ZIP_DEFLATED) as z:
        for n in [*files,'MANIFEST.sha256.json']:z.write(OUT/n,n)
    with zipfile.ZipFile(OUT/name) as z:
        assert z.testzip() is None
        assert all(hashlib.sha256(z.read(n)).hexdigest()==h for n,h in files.items())
    print('PACKAGE',name,(OUT/name).stat().st_size,'bytes',len(files),'files')

if __name__=='__main__':
    if '--package' in sys.argv:package()
    else:docs();graphics();viewer();records();entry()
