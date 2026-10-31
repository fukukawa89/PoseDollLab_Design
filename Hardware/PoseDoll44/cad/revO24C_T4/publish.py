from arm_kit import *
import html,base64,shutil,zipfile,hashlib,importlib.util
sp=importlib.util.spec_from_file_location('t3_pages_for_reuse',H/'cad/revO24C_T3/publish.py');oldpub=importlib.util.module_from_spec(sp);sp.loader.exec_module(oldpub)
pages=oldpub.pages

def page(title,body):
 nav='<nav><a href="START_HERE.html">打印入口</a><a href="tutorial/index.html">逐件动画</a><a href="ONE_PRINT.html">一盘打印</a><a href="HARDWARE.html">补购五金</a><a href="viewer/index.html?mode=W">双轴腕三维</a><a href="TEST_PLAN.html">实测方法</a></nav>'
 return '<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>'+title+'</title><link rel="icon" href="data:,"><style>'+pages.STYLE+'</style></head><body>'+nav+body+'</body></html>'

def lessons():
 steps=[s for s in oldpub.lessons() if s['station']!='W']
 def add(title,ids,text):steps.append(dict(station='W',title=title,ids=ids,text=text,number=len(steps)+1))
 add('先识别屈伸叉、偏摆叉及十字芯',['W4-01','W4-02','W4-03','W4-04'],'带10.3mm大方孔的是前臂屈伸叉；带6mm小方榫的是掌侧偏摆叉。两轴在十字芯中心相交。颜色仅为网页识别，实物可用笔分别标Y和X。')
 add('下半十字芯，合模平面朝上',['W4-02'],'有四个深六角入口的是下半；先不要合上。以下四组M3反力组件都从合模面放入，不要尝试从外侧轴孔塞入。')
 for axis in ['Y','X']:
  for sign in [-1,1]:
   pre='W'+axis+('M_' if sign<0 else 'P_');side=('−' if sign<0 else '+')+axis
   add(side+' 普通M3反力螺母',[pre+'N'],'M3×0.5，AF5.5、高2.4，无塑料圈。平整承压面朝外侧反力垫；不要用尼龙锁紧螺母替代。')
   add(side+' 9mm反力垫',[pre+'RW'],'9×3.2×0.8 mm钢垫圈。光滑面朝十字芯外侧反力壁，粗面朝普通螺母；先去毛刺。')
 add('合上十字芯',['W4-03'],'沿Z合拢，四颗M3和四片反力垫必须留在各自槽内；两半无翘缝才继续。不要用螺钉强行拉平。')
 for x in [-5,5]:
  for y in [-5,5]:
   pre=f'WC{x}_{y}'
   add('十字芯合模：普通M2',[pre+'N'],'AF4×1.6，无塑料圈。从下半外侧的深六角槽装入到底，不能停在槽口。')
   add('十字芯合模：0.5mm平垫',[pre+'W'],'5×2.2×0.5 mm，光滑面朝上半十字芯，粗面朝螺钉头。')
   add('十字芯合模：M2×16',[pre+'B'],'用1.5mm内六角。四颗交替轻紧至合模面贴合；先完成此步，再装两只叉，避免工具入口被遮住。')
 for axis,piece,label,direction in [('Y','W4-01','前后屈伸','从十字芯的+Z侧，沿前臂方向套入'),('X','W4-04','左右偏摆','从十字芯的−Z侧，沿手掌方向套入')]:
  for sign in [-1,1]:
   pre='W'+axis+('M_' if sign<0 else 'P_')
   add(axis+'轴内侧摩擦垫',[pre+'F1'],'12×4.3×1.0 mm钢垫圈，光滑面朝外、朝即将放入的3mm叉耳。沿该轴从外侧放到十字芯端面。')
  add(label+'叉就位',[piece],direction+'，让两只耳位于内侧垫圈外面，孔对中；不要掰开叉臂。模型中叉耳厚3mm，肩钉孔Φ4.25。')
  for sign in [-1,1]:
   pre='W'+axis+('M_' if sign<0 else 'P_');side=('−' if sign<0 else '+')+axis
   add(side+' 外侧摩擦垫',[pre+'F2'],'12×4.3×1.0 mm，光滑面朝内、朝叉耳。两片12mm垫圈的光滑面相向，中间夹3mm打印耳。')
   add(side+' 第一片A8',[pre+'S1'],'8×4.2×0.4，自由高约0.6 mm。内孔凸边朝外、朝螺钉头；外圆边朝内、朝关节。')
   add(side+' 第二片A8翻面',[pre+'S2'],'与上一片反向：内孔凸边朝关节。两片内孔凸边相对；自由叠高约1.2mm。不能同向套叠。')
   add(side+' 头下平垫',[pre+'HW'],'9×4.3×0.8 mm。两侧均贴金属，去毛刺、保持平整即可；不要错拿9×3.2的反力垫。')
   add(side+' O22轴肩螺钉',[pre+'AX'],'光杆Φ4×8、M3×0.5螺纹长6、头Φ7×3、3mm内六角。螺母已止转，只旋外侧螺钉。先轻接触，待同轴另一侧装好后交替微调，不压平碟簧。')
 add('沿用T3掌柄',['W3-09'],'套到6mm方榫上，对准Z=−27的横孔；这里用实际掌柄。独立测力时可换原F3-W 100mm加载杆。')
 add('掌柄普通M2',['WPALM_N'],'AF4×1.6，放入掌柄外侧六角槽；无塑料圈。')
 add('掌柄平垫0.5mm',['WPALM_W'],'5×2.2×0.5 mm，光滑面朝掌柄。')
 add('掌柄M2×14',['WPALM_B'],'1.5mm内六角；固定掌柄方键，不用来调节腕关节摩擦。')
 add('接前臂或独立夹持柄',['F3-M','W_R_N','W_R_W','W_R_B'],'联装接R3-04；独立测试改插F3-M。普通M3置六角槽，7×3.2×0.5垫圈光滑面朝叉，M3×20从相对一侧旋入。只夹F3-M方柄，不夹两只活动叉。')
 add('可选：换100mm加载杆',['F3-W','FW_W1','FW_W2','FW_N','FW_B'],'卸下实际掌柄及其M2×14。换F3-W、M2×20、两片5×2.2×0.5垫圈和普通M2；两片垫圈光滑面朝加载杆。已打印的T3附件可直接复用。')
 add('先调屈伸，再调偏摆',['WYM_AX','WYP_AX','WXM_AX','WXP_AX'],'回中立位。先调连接前臂叉的Y轴两颗，再调连接掌柄叉的X轴两颗，各轴两侧交替微调。每次最多约1/24圈，先消松旷后测力；它是微调步长，不是保证安全的紧固扭矩。四颗螺钉画见证线。')
 for i,s in enumerate(steps):s['number']=i+1
 return steps

def smooth(p):
 id=p['id']
 for axis,vec in [('X',np.array([1,0,0])),('Y',np.array([0,1,0]))]:
  for side,sign in [('M',-1),('P',1)]:
   pre='W'+axis+side+'_'
   if id.startswith(pre):
    if id.endswith(('F1','RW')):return (vec*sign).tolist()
    if id.endswith('F2'):return (-vec*sign).tolist()
 if id.startswith('WC') and id.endswith('W'):return [0,0,-1]
 return oldpub.smooth(p)

def viewer():
 data=json.loads((OUT/'assembly.json').read_text('utf8'));z=np.load(OUT/'assembly_meshes.npz');chunks=[];count=0
 for r in data['parts']:
  v=z['v'+str(r['index'])];f=z['f'+str(r['index'])];tri=v[f];n=np.cross(tri[:,1]-tri[:,0],tri[:,2]-tri[:,0]);n/=np.maximum(np.linalg.norm(n,axis=1)[:,None],1e-15)
  packed=np.concatenate([tri,np.repeat(n[:,None,:],3,axis=1)],axis=2).reshape(-1,6).astype('<f4');chunks.append(packed);r.update(start=count,count=len(packed),smooth=smooth(r));count+=len(packed)
 data.update(geometry=base64.b64encode(np.vstack(chunks).tobytes()).decode(),geometry_sha256=sha(OUT/'assembly_meshes.npz'),steps=lessons())
 (OUT/'viewer').mkdir(exist_ok=True);(OUT/'viewer/data.js').write_text('window.KIT='+json.dumps(data,ensure_ascii=False,separators=(',',':'))+';',encoding='utf8')
 for name in ['viewer.js','viewer.html']:shutil.copyfile(HERE/name,OUT/'viewer'/('index.html' if name.endswith('.html') else name))

def stats():
 current=json.loads((OUT/'assembly.json').read_text('utf8'));prior=json.loads((H/'bench/revO24C_T3/assembly.json').read_text('utf8'))
 def tally(data,station=None):
  result={}
  for p in data['parts']:
   if p['sku'] and (station is None or p['station']==station):result[p['sku']]=result.get(p['sku'],0)+1
  return result
 old=tally(prior,'W');new=tally(current,'W')
 diff=[dict(sku=s,spec=SPECS[s],T3_W_qty=old.get(s,0),T4_W_qty=new.get(s,0),delta=new.get(s,0)-old.get(s,0)) for s in sorted(old.keys()|new.keys())]
 put(OUT/'wrist_hardware_delta.json',diff)
 def env(data):
  bs=np.array([p['bounds_mm'] for p in data['parts'] if p['station']=='W' and not p['bench_only'] and p['id']!='W3-09' and not p['id'].startswith('WPALM_')])
  return (bs[:,1,:].max(0)-bs[:,0,:].min(0)).tolist()
 return current,diff,env(prior),env(current)

def docs():
 data,diff,oldenv,newenv=stats();steps=lessons();put(OUT/'assembly_steps.json',steps)
 body='''# O24C-T4 · 双轴碟簧腕装配

这是装在实际 O24C 手臂上的腕关节；四个新打印件不是放大的摩擦试块。两个正交轴在同一个 UE 腕中心相交：前臂叉绕 Y 做屈伸，掌侧叉绕随动 X 做偏摆。四个方向对应两个转动自由度；这里只改变腕结构，H、R保持T3原样。

![新版腕](images/W.png)

## 打印哪几件

已经有T3时，只需打印 [P3_W_new_only.3mf](printing/P3_W_new_only.3mf) 中的 **W4-01、W4-02、W4-03、W4-04，各1件**。W3-09掌柄、F3-W加载杆、F3-M夹持柄以及全部H3/R3原样复用。C3-01试配片也可复用。旧球体、球窝、衬片和导向肩钉不装入这版。

还没打印T3时，包内P1、P2提供原样H/R，P3提供新腕四件，P4提供原掌柄及4个可拆测试附件；P0是可选试配片。整套有12个实臂打印件、4个测试附件、1个试片。

| 新件 | 识别和作用 | 打印方向 |
|---|---|---|
| W4-01 | 带大方孔的前臂屈伸叉 | 工程中一侧摩擦耳面朝板 |
| W4-02 | 下半十字芯，底部四个深六角槽 | Z=0合模平面朝板 |
| W4-03 | 上半十字芯，四个小通孔 | Z=0合模平面朝板 |
| W4-04 | 带6mm小方榫的掌侧偏摆叉 | 工程中一侧摩擦耳面朝板 |

A1 mini、0.4mm喷嘴、PLA、0.12mm层高、5圈墙、100%填充、自动支撑、3mm外沿。保留工程方向。先清除孔、六角槽及摩擦面上的支撑和毛刺；合模平面不能有凸起。Φ4光杆应能滑入Φ4.25孔，3mm摩擦耳不要随意磨薄。试片4.15/4.25/4.35三个孔用于记录本机误差，不是三个互换设计。孔过紧或方键插不入时先停下，不能靠拧紧压裂零件。

## 五金朝向

**这版全套都是普通螺母，没有尼龙圈。** M3调节螺母藏在十字芯中，M2合模螺母在底面的深六角槽；只用外侧内六角即可旋紧。普通螺母被卡住只解决止转，仍需检查螺钉回松。

每一侧，从十字芯向外的顺序是：**内侧12mm摩擦垫 → 3mm叉耳 → 外侧12mm摩擦垫 → 反向A8两片 → 9mm头下垫 → 轴肩螺钉头**。芯内部为普通M3、9×3.2×0.8反力垫和2.8mm反力壁。光杆定位，轴向力经过摩擦耳；没有滚珠轴承旁路。

两片12×4.3×1.0摩擦垫的光滑面都朝叉耳。内部9×3.2×0.8反力垫光滑面朝打印壁。M2/M3小垫圈光滑面朝打印件。头下9×4.3×0.8垫圈两面都贴金属，平整去毛刺即可。网页绿色只是识别，不要求实物涂色。

A8第一片内孔凸边朝螺钉头，第二片翻面朝关节，**两片内孔凸边相对**。不是同向套叠，也不是开口弹簧垫圈。自由叠高约1.2mm；图中1.0mm仅为名义示意，不是应拧到的固定目标。两片平片厚合计0.8mm，不能压到这个状态。

## 实际装配顺序

1. W4-02平放，合模面朝上。四个侧向槽各装普通M3和反力垫；再合上W4-03。
2. 四颗普通M2从底部深六角槽装到底。上面放0.5mm小垫圈，用四颗M2×16交替轻紧。此时两只叉都没装，工具入口敞开。
3. 十字芯Y轴两端先放内侧12mm垫圈。把带大方孔的W4-01从前臂侧套入，再逐侧装外侧垫圈、两片反向A8、头下垫、O22轴肩螺钉。暂时只消除明显松旷。
4. 十字芯X轴两端同样先放内侧垫圈。把W4-04从掌侧套入，再装该轴两侧的外部堆叠。
5. 接W3-09实际掌柄，普通M2＋0.5mm垫圈＋M2×14；若独立测力则换F3-W及其M2×20、两片0.5mm垫圈和普通M2。
6. 上端插R3-04实际前臂，或独立测试插F3-M。普通M3＋7×3.2×0.5垫圈＋M3×20。只夹F3-M方柄。
7. 回中立位，先调前臂叉的Y轴两侧，再调掌侧叉的X轴两侧。每对交替微调，最多约1/24圈一步，立即重新测力。出现阻滞、开缝、发白、可见弯曲或到极限仍不持姿时停止，不继续猛拧。

四颗轴肩螺钉用3mm内六角；普通M3圆柱头用2.5mm，M2圆柱头用1.5mm。Y与X调节均在外侧；安装好的R仍需先卸W及横向连接螺钉，再从原中央通道调节R。

首次短测采用螺钉头见证线，反复检查回松。后续需要螺纹锁固时，确认适用材料后，只在清洁的金属螺纹用可拆卸低强度锁固方法，按产品要求固化；不让胶沾摩擦面、光杆或PLA。未锁固的状态不能当成长期持姿验证。这里不虚构一个紧固扭矩。

下面每个步骤对应网页的“分步定位”：完整模型作背景，高亮当前零件，可查看型号和光滑面。爆炸图只用于辨认，实际装入方向按文字执行。
'''
 for st in ['H','R','W']:
  body+='\n## '+st+'逐步定位\n'
  for s in steps:
   if s['station']==st:body+='\n'+str(s['number'])+'. **'+s['title']+'** · '+', '.join(s['ids'])+'。'+s['text']+'\n'
 write_doc('ASSEMBLY','双轴腕装配',body)
 test='''# O24C-T4 · 先测两个腕轴，再接回手臂

**T3球腕尚未实测；T4双轴腕也没有实测通过。** 本轮只完成数字设计、装配检查和打印工程。两个腕轴各自的目标保持力矩暂定 **0.006 N·m**，它是本轮比较门槛，不是完整人偶的额定负载。

## 先确认运动与松旷

装实际掌柄，分别转动Y轴和X轴；另一轴回零。目标屈伸−65°～70°、偏摆−20°～30°。两轴组合也慢慢试。遇硬碰、阻滞、塑料发白立即停，不用手硬掰到数字目标。检查十字芯两半、方键接口是否晃动；头下弹簧不应已压平。

## 用原100mm加载杆分别测两个轴

卸实际掌柄，换F3-W。装F3-M，用软钳口夹方柄，不能夹压腕叉。测试时只让被测轴受力，不用把另一个轴拧死。

| 被测轴 | 装置方向 | 在100mm力孔的拉力方向（中立位） |
|---|---|---|
| Y 屈伸 | 将Y轴摆成竖直，加载杆水平 | 沿局部X方向水平、切向拉 |
| X 偏摆 | 重新摆放，使X轴竖直，加载杆水平 | 沿局部Y方向水平、切向拉 |

每测一个轴，另一个轴回到0°。受测轴竖直、水平切向拉，可以减小加载杆自重对该轴的重力矩影响。中立时100mm垂直力臂：0.006 N·m对应0.060 N拉力，约6.1g力，**不是直接挂6.1g就一定准确**。量具分辨率宜0.01 N或更好；低量程做不到时，用实际测得的力臂和加载质量记录，不编造合格结论。

竖直摆放只减小被测轴上的重力矩，另一根水平轴仍可能受加载杆自重。另一轴必须能稳定保持0°；若它下垂或跟着动，这次单轴读数作废，先在不过度预紧的前提下恢复其中立保持。不能用手扶住加载杆同时读力，否则手会带入未知力矩。

一般姿态用 τ=F×d⊥，d⊥是轴线到拉力作用线的垂直距离，不一定等于杆长100mm。偏离中立后，拉力方向随杆转到切向。若改用重物，须计入掌柄/加载杆及移动件的自重和重心，且要防止同时给另一轴施加力矩。

## 调节和记录

1. 两侧交替从轻接触调起，每步最多约1/24圈。先记录启动力和持续拖动力，避免只记录“手感很紧”。
2. 往返50次磨合，放置30分钟，可记录一次复调；记下四颗头的标线、两侧弹簧高度、温度和材料批次。高度0.9～1.2mm只是CAD检查区间，不代表这些高度都适合实际弹簧。
3. 每个轴分别施加0.006 N·m，保持10分钟，暂以漂移≤2°为门槛。若太涩先回调，不靠压平弹簧解决持姿不足。
4. 在0、100、500、1000次各测启动力、拖动力和保持漂移；暂以力矩变化≤20%、无裂纹、无回松为比较门槛。24小时后复查蠕变和见证线。循环时避免撞机械限位；本版没有定型的角度硬限位。
5. 独立样件合格后接回同一套H/R，换实际掌柄，测试水平前臂、屈肘和腕组合姿态。H暂定0.040 N·m、R 0.020 N·m的旧门槛继续记录；不能由腕合格推断肩或整个人偶合格。

普通螺母止转不等于螺钉防松。若调节螺钉跟着关节反复转动而松开，先记录并停测；采用适用的金属螺纹锁固、固化后重新记录基线。不同锁固状态的结果分开比较。

[W记录空表](records/W_test.csv) · [H记录空表](records/H_test.csv) · [R记录空表](records/R_test.csv)。已有记录不会被生成过程覆盖。
'''
 write_doc('TEST_PLAN','腕部实测方法',test)
 env=lambda v:' × '.join(f'{x:.2f}' for x in v)
 design=f'''# O24C-T4 · 双轴腕设计说明

## 继承与改变

O24A的腕部是两根相交轴；本版采用该布局，加入可采购的O22摩擦堆叠与真实装配结构。O24A布局本身不是本轮直接打印的制造图。旧T3球腕保留，未把用户的担忧写成实测失败。

每根腕轴两侧各一颗Φ4×8/M3牙长6轴肩螺钉、一对反向A8、两片12mm钢摩擦垫；四颗普通M3和反力垫从十字芯合模面放入。轴向压力经过3mm叉耳，两轴分别调节。螺钉头外置，不需要悬空扶螺母。左右微调仍需交替，打印弹性和装配误差可能使两轴手感相互影响。

保留2.8mm反力壁、5.6mm名义圆截面叉臂、3mm摩擦耳。前臂方孔横向M3孔的下方保留2.8mm材料。两半十字芯以四颗M2×16闭合，不存在旧H04式单块阶梯板靠薄边连接的安排；这不等于完成强度或疲劳验证。

这一版用更多金属件换取独立、易观察的平面摩擦副。中立位腕机构外廓（含五金、方键、接口螺钉，不含实际掌柄及其紧固件）：T3约 **{env(oldenv)} mm**，T4约 **{env(newenv)} mm**，顺序为X×Y×Z。因此它并非各方向都比球腕更小；约40mm的横向尺寸是现有O22肩钉与双侧支撑的代价。动态外廓另随姿态变化。

## 骨架和运动学

UE Quinn Simple参考560mm人体比例；肘心E到腕心W仍是{FORE:.9f}mm，前臂旋转轴沿E—W。新腕两个物理孔轴都通过同一W，中立时正交。完整人偶小于600mm仍是后续要求；本包没有完成全身外廓测量。

本版使用 **Ry(腕屈伸) × Rx(腕偏摆)**：先屈伸，再绕随动X偏摆，与O24A一致。T3球腕原先是Rx偏摆×Ry屈伸，组合角不能把旧的数值原样当成等价姿态。网页、CAD、校验及本包profile使用同一新顺序；后续UE映射应根据矩阵重算或重新标定。

目标屈伸−65°～70°，偏摆−20°～30°；这是本项目的设计测试范围，不声称每个人都达到相同角度。前臂旋转仍由R负责。没有把腕部绕前臂轴的自由扭转混进两个腕轴。

## 检查与边界

检查包括导出网格连通/闭合、实际轴孔拟合、名义尺寸干涉、顺序装入路径、轴肩底部余量、螺纹覆盖、调节工具入口、切片导入以及网页矩阵。检查报告放在verification中，角度采样并非连续运动或全部九自由度组合的数学证明。

Φ4光杆对应Φ4.25名义孔；10mm方键对应10.3mm孔，单边0.15mm。光杆和塑料尺寸误差会带来实际回差；CAD零偏移不是实物零误差。T3 H在145°附近已有约0.389mm的名义包装间隙，本次未修改H，实物遇阻不能强摆。

A8实物载荷曲线、摩擦系数、打印强度、磨损和蠕变未知；不能从接触面积、CAD弹簧高度或切片成功推导持姿能力。钢垫圈也可能滑动，不把每个耳两面机械地算成两倍力矩。[SPIROL碟簧设计手册](https://www.spirol.com/assets/files/dsc-disc-spring-design-guide-us.pdf)说明反向串联可增加行程、压缩范围影响性能；这里只借用通用原理，不把其目录载荷当成手头A8的实测值。

只验证机械测试样件。本版没有传感器、磁铁及布线的定型集成；不能称为完成了UE实时采集系统。肩部、锁骨、完整人偶持姿和最终高度仍待后续设计验证。
'''
 write_doc('DESIGN','双轴腕设计边界',design)
 table='<table><tr><th>规格</th><th>T3腕及附件</th><th>T4腕及附件</th><th>净增加</th></tr>'+''.join('<tr><td>'+html.escape(r['spec'])+'</td><td>'+str(r['T3_W_qty'])+'</td><td>'+str(r['T4_W_qty'])+'</td><td>'+('+' if r['delta']>0 else '')+str(r['delta'])+'</td></tr>' for r in diff)+'</table>'
 bom=json.loads((OUT/'BOM.json').read_text('utf8'))
 full='<table><tr><th>规格</th><th>完整H/R/W及测试附件数量</th></tr>'+''.join('<tr><td>'+html.escape(r['spec'])+'</td><td>'+str(r['qty'])+'</td></tr>' for r in bom)+'</table>'
 (OUT/'HARDWARE_T3_T4.html').write_text(page('T3腕与T4腕数量差','<h1>T3 球腕 → T4 双轴腕：数量变化</h1><p><a href="HARDWARE.html">已买齐 O22 + T1-S2？请用这张补购表。</a> 本页仅比较两个腕版本，不代表需要重新购买。</p><p>两栏均包括该腕的掌柄、连接前臂五金和可拆测试附件；与H/R共享的五金未重复列入腕。负数表示新腕不再使用，保留供T3对比。净增加是数量差，不能用不同型号抵扣。</p>'+table+'<h2>完整三样件清单</h2><p>H/R保留T3；全部普通螺母、无尼龙圈。M2平垫厚0.5mm，沿用已购规格。所有长度单位mm。</p>'+full),encoding='utf8')
 with (OUT/'wrist_hardware_delta.csv').open('w',encoding='utf-8-sig',newline='') as f:
  wr=csv.writer(f);wr.writerow(['SKU','规格','T3腕含附件','T4腕含附件','净增加']);wr.writerows([r['sku'],r['spec'],r['T3_W_qty'],r['T4_W_qty'],r['delta']] for r in diff)
 (OUT/'records').mkdir(exist_ok=True)
 for st in ['H','R','W']:
  file=OUT/'records'/f'{st}_test.csv'
  if not file.exists():
   with file.open('w',encoding='utf-8-sig',newline='') as f:csv.writer(f).writerow(['样件','轴','日期','材料/批次','层高','表面/孔处理','姿态','两侧碟簧高度mm','锁固状态','温度C','循环数','垂直力臂mm','启动力N','拖动力N','保持10分钟漂移deg','24小时漂移deg','头见证线','回差','裂纹/磨屑','照片','结论'])
 plates=json.loads((OUT/'printing/plates.json').read_text('utf8'))['plates']
 start='<p class="eyebrow">O24C-T4 · 双轴碟簧腕 · 实物待测</p><h1>屈伸与偏摆，分别调摩擦</h1><div class="hero"><div><p>沿用O24A的相交双轴布局，加入O22轴肩螺钉与A8碟簧。新腕直接接当前T3的前臂；同一批零件用于独立测试和实尺寸联装。</p><a class="button" href="viewer/index.html?mode=W">查看双轴腕</a><a class="button" href="viewer/index.html">接回手臂查看</a><a class="button" href="PoseDoll_O24C_T4_Dual_Axis_Wrist_Kit.zip">下载完整包</a><p class="note">需新打印4件：W4-01～04。H/R、原掌柄及测试附件可复用。持姿能力及磨损尚未实测。</p></div><img src="images/W.png" alt="实际制造网格的双轴腕"></div><div class="cards"><div class="card"><b>Y 屈伸</b><br>−65°～70°<br>两侧碟簧交替微调</div><div class="card"><b>X 偏摆</b><br>−20°～30°<br>独立于Y轴的摩擦堆叠</div><div class="card"><b>同一腕中心</b><br>E—W 80.496305mm<br>H/R原样保留</div></div><h2>打印工程</h2><p>已有T3：只打印P3的4个新件。尚未打印：按需加P1、P2、P4，P0先试配。</p>'+''.join('<p><a href="'+p['file']+'">'+p['id']+' · '+str(p['count'])+'件</a></p>' for p in plates)+'<p><a href="ASSEMBLY.html">详细装配与五金朝向</a> · <a href="HARDWARE.html">新增五金及完整数量</a> · <a href="TEST_PLAN.html">分别测两个轴</a> · <a href="DESIGN.html">尺寸代价与未验证事项</a></p><h2>检查报告</h2><p>数字检查通过不等于实际持姿通过。看报告中的采样范围和限制。</p>'+''.join('<p><a href="verification/'+name+'.json">'+name+'</a></p>' for name in ['geometry','installed_rom','bench_rom','assembly_paths','module_insertion','ue_alignment','mechanics','slicing','reuse','browser','delivery'])
 start=start.replace('<h2>打印工程</h2>','<h2>整套准备：三个入口</h2><p><a class="button" href="tutorial/index.html">H / R / W 逐件动画</a><a class="button" href="HARDWARE.html">已购 O22 + T1-S2 的补购表</a><a class="button" href="printing/ALL_H_R_W_T4.3mf">一盘打印全部 17 件</a></p><p>17 件含 12 个关节件、4 个测试附件、1 个可选试片，各一件。当前打印套件为 H3 + R3 + W4；全部在一个 A1 mini 打印工程内，零件保持独立对象。<a href="ONE_PRINT.html">查看排盘与辨认图</a>。本次没有修改零件几何，已经打印的 T4 不需重印。</p><details><summary>只补打部分零件：旧分盘工程（与合盘重复，不要重复打印）</summary><h2>分盘补打</h2>')
 start=start.replace('<p><a href="ASSEMBLY.html">详细装配与五金朝向</a>','</details><p><a href="TUTORIAL.html">158 步索引与离线说明</a> · <a href="ASSEMBLY.html">装配手册</a>')
 (OUT/'START_HERE.html').write_text(page('O24C-T4打印入口',start),encoding='utf8')
 (OUT/'REBUILD.txt').write_text('源文件在仓库Hardware/PoseDoll44/cad/revO24C_T4；本包source为快照。重建需要同一仓库的revO24、revO24C_T1、revO24C_T3源文件及既有模板，不能把ZIP中的source当成独立CAD软件。STL、3MF、网页本身可离线使用。\n使用仓库Python依次运行arm_kit.py、audit.py、assembly_checks.py、bench_checks.py、print_projects.py；Blender运行render.py；Python运行publish.py生成页面。最后完成verify_delivery.py及publish.py --package。\n',encoding='utf8')
 put(OUT/'wrist_profile.json',dict(revision=REVISION,asset='/Game/Characters/Mannequins/Meshes/SKM_Quinn_Simple',units='mm',forearm_mm=FORE,reference_height_mm=560,fullbody_height_verified=False,rotation_order='Ry(flex_deg) @ Rx(deviation_deg)',axes=[dict(name='flex',axis=[0,1,0],parent='wrist_base',center=[0,0,0],range_deg=[-65,70]),dict(name='deviation',axis=[1,0,0],parent='flex',center=[0,0,0],range_deg=[-20,30])],physical_test_passed=False))

def write_doc(name,title,content):
 if name=='ASSEMBLY':content='[打开 H / R / W 逐件动画教程](tutorial/index.html) · [全部步骤索引](TUTORIAL.html)\n\n'+content
 (OUT/(name+'.zh-CN.md')).write_text(content,encoding='utf8');(OUT/(name+'.html')).write_text(page(title,pages.mdhtml(content)),encoding='utf8')

def package():
 (OUT/'source').mkdir(exist_ok=True)
 for p in HERE.iterdir():
  if p.suffix in ['.py','.js','.html','.css']:shutil.copyfile(p,OUT/'source'/p.name)
 refs=[H/'cad/revO24/arm.py',H/'cad/revO24C_T1/kit.py',H/'cad/revO24C_T1/printing.py',H/'cad/revO24C_T3/arm_kit.py',H/'cad/revO24C_T3/publish.py',H/'bench/revO24C_T3/assembly_meshes.npz',H/'bench/revO24C_T3/manifest.json']
 put(OUT/'reference_baselines.json',{str(p.relative_to(ROOT)):sha(p) for p in refs})
 exclude={'manifest.json','PoseDoll_O24C_T4_Dual_Axis_Wrist_Kit.zip'}
 files=[p for p in OUT.rglob('*') if p.is_file() and p.name not in exclude and not p.name.endswith('.blend1')]
 put(OUT/'manifest.json',dict(revision=REVISION,geometry_sha256=sha(OUT/'assembly_meshes.npz'),files=[dict(path=p.relative_to(OUT).as_posix(),sha256=sha(p),bytes=p.stat().st_size) for p in sorted(files)]))
 with zipfile.ZipFile(OUT/'PoseDoll_O24C_T4_Dual_Axis_Wrist_Kit.zip','w',zipfile.ZIP_DEFLATED) as z:
  for p in files+[OUT/'manifest.json']:z.write(p,p.relative_to(OUT).as_posix())
 print('PACKAGED',len(files)+1,'files',flush=True)

if __name__=='__main__':
 if '--package' in sys.argv:package()
 else:docs();viewer()
