"""T5 one-part lessons with physically checked side-loading reaction hardware."""
from arm_kit import *
from publish import smooth,page
import shutil,collections,html
ZERO=[0.,0.,0.]
ROWS=json.loads((OUT/'assembly.json').read_text('utf8'))['parts']
P={r['id']:r for r in ROWS if r['station']!='C'}
EDITION='T5-一体承力座-20261025'

def tool(p):
 s=p['sku'] or ''
 if s=='AX4':return '3 mm 内六角扳手；槽内普通螺母已止转'
 if s.startswith('M2x'):return '1.5 mm 内六角扳手'
 if s.startswith('M3x'):return '2.5 mm 内六角扳手'
 if s=='N2':return '镊子；必要时 4 mm 小扳手'
 if s=='N3':return '镊子；必要时 5.5 mm 小扳手'
 return '手放 / 镊子；不要用螺钉硬拉错位零件'

class Lesson:
 def __init__(self,st):self.station=st;self.steps=[];self.state={};self.chapter='准备';self.added=[]
 def step(self,title,text,kind='check',ids=None,paths=None,detail='',toolname='手动核对'):
  ids=ids or [];paths=paths or {};before={k:v[:] for k,v in self.state.items()}
  for id,path in paths.items():self.state[id]=path[-1][:]
  if kind=='remove':
   for id in ids:del self.state[id]
  self.steps.append(dict(n=len(self.steps)+1,chapter=self.chapter,title=title,text=text,kind=kind,ids=ids,paths=paths,before=before,after={k:v[:] for k,v in self.state.items()},detail=detail,tool=toolname))
 def add(self,id,text,direction=ZERO,end=ZERO,title=None,detail=''):
  assert id in P and id not in self.added,id
  self.added.append(id);start=(np.array(end)+direction).tolist()
  self.step(title or ('装入 '+id),text,'add',[id],{id:[start,list(end)]},detail,tool(P[id]))
 def check(self,title,text,ids=None,detail=''):self.step(title,text,ids=ids,detail=detail)
 def remove(self,id,direction,text):
  start=self.state[id];end=(np.array(start)+direction).tolist()
  self.step('拆下 '+id,text,'remove',[id],{id:[start,end]},toolname=tool(P[id]))
 def rom(self,title,text):self.step(title,text,'rom',detail='此处为名义范围演示；实物遇阻即停，不能以动画代替实际验证。')

def prep(L,what):
 L.check('开始前：确认版本、去支撑、分五金',what+'。本教程使用 T5 网格；三处承力座改为一体，原摩擦堆叠保留。每一步新增一件，完成装入再按下一步。检查点会暂停连续播放。',detail='清除支撑和孔内毛刺；摩擦面平整干燥。全部螺母均为普通螺母、无塑料圈。新零件装前先试配；不要扩孔过量或用螺钉把翘缝硬拉平。')
 L.check('分清五种垫圈与两片碟簧', '平垫尺寸均按外径×内径×厚度：5×2.2×0.5、7×3.2×0.5、9×3.2×0.8、9×4.3×0.8、12×4.3×1 mm。A8 是 8×4.2×0.4、单片自由高约 0.6 mm 的碟簧。',detail='绿色只标光滑面；蓝色用来识别 A8 碟簧，不要求实物颜色。螺钉标注长度不含头；动画显示装入方向，实际必须旋入金属螺纹，不能直推穿过。')

def capture(L,pre,d):
 L.add(pre+'RW','先从侧向的窄槽滑入 9×3.2×0.8 mm 反力垫，光滑面朝轴孔外侧的连续反力壁。滑到底、对准轴孔；不要从中心轴孔硬塞，也不要拿成孔 4.3 mm 的头下垫。',d,title=pre+' 侧装反力垫 · 先装')
 L.steps[-1]['camera']=port_camera(L.station,pre)
 L.add(pre+'N','再从相邻六角导槽滑入普通 M3×0.5（对边 5.5、高 2.4 mm），平整承压面贴反力垫，两平行平面与导槽对齐。无塑料圈。装到底后中心孔对齐。',d,title=pre+' 侧装普通 M3 · 后装',detail='装入口朝上或用手托住未穿螺钉的五金；此时尚未锁住，翻动可能掉出。必要时仅临时封入口，不把胶带贴到摩擦面或轴孔；肩钉旋入后再移除。入口无需封盖。')
 L.steps[-1]['camera']=port_camera(L.station,pre)

def port_camera(st,pre=''):
 return dict(yaw=(-2.7 if pre=='HL_' else 2.7),pitch=.3) if st=='H' else dict(yaw=-1.85,pitch=.35) if st=='R' else dict(yaw=-1.1,pitch=-1.25)


def inner(L,pre,d):L.add(pre+'F1','12×4.3×1 mm 内侧摩擦垫贴固定座端面，光滑面朝外，稍后贴 3 mm 厚的转动耳 / 转盘。两侧同规格、无毛刺。',d,title=pre+' 内侧摩擦垫')

def outer(L,pre,d):
 L.add(pre+'F2','12×4.3×1 mm 外侧摩擦垫，光滑面朝内、朝转动耳 / 转盘。两片摩擦垫的光滑面相向，中间夹打印件。',d,title=pre+' 外侧摩擦垫')
 L.add(pre+'S1','第一片 A8：内孔的凸边朝外、朝螺钉头，外圆边朝关节。请同时看右侧剖面示意和三维方向箭头。',d,title=pre+' A8 第 1 片 · 凸边朝外',detail='只放一片，先辨认内孔和外圆哪一边更高；不是平垫圈。')
 L.add(pre+'S2','第二片 A8 翻面：内孔的凸边朝内、朝关节。它与第一片的内孔凸边相对，形成反向串联的一对。',d,title=pre+' A8 第 2 片 · 凸边朝内',detail='两片自由叠高约 1.2 mm；同向套叠不是本设计。动画是名义预紧位置，不要求用扳手拧到画面中的高度。')
 L.add(pre+'HW','9×4.3×0.8 mm 头下平垫放在碟簧外面；两侧都是金属，去毛刺、保持平整即可，没有强制正反。勿错用 9×3.2 反力垫。',d,title=pre+' 头下平垫 · 孔 4.3 mm')
 L.add(pre+'AX','插入 O22 轴肩螺钉：光杆 Φ4×8、M3×0.5 螺纹长 6、头 Φ7×3。用 3 mm 内六角旋进槽内普通螺母。先转到轻接触，不立即拧紧。',d,title=pre+' 轴肩螺钉 · 先轻接触',detail='槽内螺母负责止转，手不必悬空捏螺母。若金属螺纹一开始就卡，退出检查孔对中和螺纹；不能靠加力越过。')

def fasten(L,pre,nd,wd,context):
 L.add(pre+'N',context+'：普通 '+P[pre+'N']['spec']+'，从六角槽开口装到底，平整面朝承压侧。',nd,title=context+' · 普通螺母')
 L.add(pre+'W',context+'：'+P[pre+'W']['spec']+'，光滑面贴打印件，另一面朝螺钉头。',wd,title=context+' · 平垫圈')
 L.add(pre+'B',context+'：'+P[pre+'B']['spec']+'。从垫圈侧旋入普通螺母，轻合紧。此连接负责固定结构，不调关节摩擦。',wd,title=context+' · '+P[pre+'B']['sku'])

def adjustment(L,ids,axes):
 L.check('消间隙，再小步调整预紧',axes+'。从轻接触开始，每次最多约 1/24 圈，来回活动并观察两侧。先消除可见松旷，再测启动力；不要把 A8 压平。',ids,detail='1/24 圈是试调步长，不是规定紧固扭矩。两片总实心厚约 0.8 mm；CAD 的 0.9～1.2 mm 高度检查不是弹力标定。若越调越涩、发白或裂开，停下检查。')
 L.check('做防松标记并记录基线','在螺钉头与相邻固定件画对齐见证线。普通螺母被槽止转，并不等于螺钉已经防松。往返后检查头是否回松，并记录碟簧高度和锁固状态。',ids,detail='需要锁固时，按选定产品说明采用适用于金属螺纹的可拆卸低强度锁固方案；避免胶液进入塑料摩擦面。未完成锁固实测前仅作受控台架测试。')

def hinge():
 L=Lesson('H');prep(L,'H 是实际肘屈伸关节，配 F3-H 可拆 100 mm 加载杆')
 L.chapter='01 · 固定座内的反力组件'
 L.add('H5-01','一体肘固定座放稳，把背面的负 X 侧装入口朝上。H3-01/02 已合并，原两组 M3×12 合模五金全部省去。',[0,0,25])
 L.steps[-1]['camera']=port_camera('H')
 for pre in ['HL_','HR_']:capture(L,pre,[-25,0,0])
 L.check('核对连续反力壁与侧装五金','两组反力垫和普通 M3 都已到槽底、孔对齐。现在没有需要拉紧的合模缝；入口是有意保留的装配通道。保持五金不掉出，再安装转动叉。',['H5-01','HL_N','HR_N'])
 L.chapter='02 · 肘转动叉与两侧碟簧'
 for sign,pre in [(-1,'HL_'),(1,'HR_')]:inner(L,pre,[0,sign*25,0])
 L.add('H3-03','从下方开口沿骨轴方向套入转动叉，两只 3 mm 耳放在内侧摩擦垫外侧。对中孔，不掰开叉臂。',[0,0,-40])
 for sign,pre in [(-1,'HL_'),(1,'HR_')]:outer(L,pre,[0,sign*25,0])
 L.chapter='03 · 装独立测力附件'
 L.add('F3-H','把 F3-H 的方键从转动叉末端套入，对齐横向孔。它可拆卸；测试的是同一个实臂关节。',[0,0,-35])
 fasten(L,'H_R_',[25,0,0],[-25,0,0],'加载杆连接')
 L.chapter='04 · 预紧、活动与实测'
 adjustment(L,['HL_AX','HR_AX'],'左右两颗肩钉交替调节')
 L.rom('慢慢检查肘屈伸范围','固定上端实体夹持段，慢慢摆动加载杆，名义目标 0°～145°。不要夹转动耳或碟簧；接近末端尤其注意硬碰、发白和松旷。')
 L.check('测持姿，而不只摸手感','100 mm 垂直力臂时，0.40 N 对应 0.040 N·m。测启动力、持续拖动力和 10 分钟保持漂移；50 次磨合后复查。',detail='用力的方向必须与力臂垂直；加载杆自重和夹具方向会影响读数。按测试计划记录，不能只凭动画判断合格。')
 return L

def roll():
 L=Lesson('R');prep(L,'R 是沿前臂骨轴的旋转关节，配 F3-R 可拆 100 mm 加载杆')
 L.chapter='01 · 固定芯和预装转盘螺母'
 L.add('R5-01','一体旋转固定芯，主体宽 13 mm，输入方键仍为 10 mm。负 Y 侧有反力垫和螺母入口，朝上或用手托住五金；不再装原两组 M2×12 合模五金。',[0,0,25])
 L.steps[-1]['camera']=port_camera('R')
 capture(L,'R_',[0,-25,0])
 L.check('确认反力垫与普通 M3 就位','五金沿导槽到底且孔同轴。先扶住未穿螺钉的五金，再预装转盘。',['R5-01','R_N','R_RW'])
 park=[-55,0,0]
 L.add('R3-03','先把薄转盘放在旁边，露出背面的两个小六角槽；不要立即贴到固定芯上。',[0,0,25],park,title='在旁边预装 R3-03 转盘')
 for y in [-8.5,8.5]:L.add('RO'+str(y)+'N','普通 M2（对边 4、高 1.6、无塑料圈）装进转盘背面六角槽。后续壳体螺钉用这两颗；转盘就位后再装会被挡住。',[0,0,20],park,title='转盘背面 · 预装普通 M2')
 L.chapter='02 · 转盘与单组碟簧'
 inner(L,'R_',[0,0,-25])
 ids=['R3-03','RO-8.5N','RO8.5N'];paths={id:[park,[-55,0,-30],[0,0,-30],[0,0,0]] for id in ids}
 L.step('带螺母的转盘整体就位','扶住两颗已埋入的 M2，先移到固定芯端面外侧，再对准轴孔贴上内摩擦垫。不要把螺母掉到摩擦面里。','move',ids,paths)
 outer(L,'R_',[0,0,-25])
 L.check('先粗调主肩钉','此时外壳尚未盖上，3 mm 内六角可直接到达主肩钉。旋到轻接触，转盘能受控转动、不明显晃动即可。',['R_AX'],detail='后续仍可经输出壳中心通道调节，但必须先拆 F3-R 的横向固定螺钉；不能把扳手硬顶在横螺钉上。')
 L.chapter='03 · 输出壳和测力杆'
 L.add('R3-04','从末端沿轴线罩住碟簧堆叠，两个壳体孔对准转盘已埋螺母。',[0,0,-30])
 for y in [-8.5,8.5]:
  pre='RO'+str(y)
  L.add(pre+'W','5×2.2×0.5 mm，光滑面朝输出壳，粗面朝螺钉头。',[0,0,-25],title='输出壳连接 · M2 平垫')
  L.add(pre+'B','M2×14 从末端穿入并旋进预装普通 M2。两颗交替轻紧，壳体合面贴合即可。',[0,0,-25],title='输出壳连接 · M2×14',detail='用 1.5 mm 内六角。此处不调持姿摩擦，不要用更长螺钉顶住固定芯。')
 L.add('F3-R','沿输出方键装上 F3-R，横向 100 mm 力臂伸出。对准横孔。',[0,0,-35])
 fasten(L,'FR_',[-25,0,0],[25,0,0],'测力杆固定')
 L.chapter='04 · 调节入口与复核'
 L.remove('FR_B',[25,0,0],'先旋出 M3×20 横向螺钉，卸下后放到旁边；下一步取垫圈。它会挡住中心调节通道。')
 L.remove('FR_W',[25,0,0],'取下外侧平垫圈放好。')
 L.remove('FR_N',[-25,0,0],'取下槽内普通 M3 放好，避免卸杆时掉落。')
 L.remove('F3-R',[0,0,-35],'沿方键卸下加载杆，露出输出壳中心通道。')
 L.check('经中心通道微调 R 主肩钉','3 mm 内六角沿输出壳中心直达 R_AX，只调这颗主肩钉。每次最多约 1/24 圈，调后退出工具再转动关节。',['R_AX'],detail='不是去拧输出壳的两颗 M2×14；调节时横向固定螺钉和测试杆均已卸下。')
 # Reuse removed parts, explicitly as reinstall moves rather than new purchases.
 for id,delta in [('F3-R',[0,0,-35]),('FR_N',[-25,0,0]),('FR_W',[25,0,0]),('FR_B',[25,0,0])]:
  L.step('装回 '+id,'装回刚才拆下的同一件。'+('M3×20 只负责固定测力杆，轻合紧即可。' if id=='FR_B' else '按原孔位与朝向装回。'),'reinstall',[id],{id:[delta,ZERO]},toolname=tool(P[id]))
 adjustment(L,['R_AX'],'若还需调整，重复刚才的卸杆—调主肩钉—装回步骤')
 L.rom('检查前臂旋转范围','固定芯保持静止，转动输出壳与力臂；本独立教程以当前装配姿态为 0°，演示 −85°～80°。联装手臂的安装零位另有 90°定向，不应当成额外活动角。')
 L.check('记录旋转关节保持力','100 mm 垂直力臂时，0.20 N 对应 0.020 N·m。记录启动力、拖动力、保持漂移及回松；退出工具后再测。',detail='加载杆与 R3-04 不能相互晃动；先排除方键固定松旷，再评价关节摩擦。')
 return L

def wrist():
 L=Lesson('W');prep(L,'W 是两个相交转轴的 T5 腕：前臂叉做屈伸、掌侧叉做偏摆，最后可换测力杆')
 L.chapter='01 · 十字芯内的四组反力组件'
 L.add('W5-01','一体十字芯，负 Z 面有四组入口。将这个入口面朝上放稳；完整的另一面没有合模缝。原四组 M2×16 合模五金全部省去。',[0,0,25])
 L.steps[-1]['camera']=port_camera('W')
 for pre in ['WYM_','WYP_','WXM_','WXP_']:capture(L,pre,[0,0,-25])
 L.check('先装完八件内部五金，再套两只叉','四片孔 3.2 mm 反力垫和四颗普通 M3 都已就位。肩钉未旋入前，托住或临时遮住入口防掉；胶带不能覆盖摩擦面。装叉后不能依靠强行推压来补装内部五金。',['W5-01','WYM_N','WYP_N','WXM_N','WXP_N'])
 for axis,piece,offset,label in [('Y','W4-01',[0,0,40],'前臂侧屈伸叉'),('X','W4-04',[0,0,-40],'掌侧偏摆叉')]:
  L.chapter=('02' if axis=='Y' else '03')+' · '+label+'与碟簧'
  vec=Y if axis=='Y' else X
  for sign in [-1,1]:inner(L,'W'+axis+('M_' if sign<0 else 'P_'),(vec*sign*25).tolist())
  L.add(piece,label+'从'+('上方前臂端' if axis=='Y' else '下方掌端')+'套入，两只 3 mm 耳在内侧垫圈外侧。大方孔属于前臂侧，小方榫属于手掌侧；不要把两叉装反。',offset)
  for sign in [-1,1]:outer(L,'W'+axis+('M_' if sign<0 else 'P_'),(vec*sign*25).tolist())
  L.check(axis+'轴两侧先保持轻接触','两侧肩钉均已旋入普通 M3，再交替消除明显间隙。检查两对 A8 都是内孔凸边相对，未同向套叠。',['W'+axis+'M_AX','W'+axis+'P_AX'])
 L.chapter='04 · 实际掌柄与独立夹持柄'
 L.add('W3-09','将实际掌柄沿 6 mm 方榫装到底，对齐横向孔。掌柄与 T3 相同，可以直接复用。',[0,0,-35])
 fasten(L,'WPALM_',[-20,0,0],[20,0,0],'实际掌柄固定')
 L.add('F3-M','将 F3-M 的 10 mm 方键从前臂端插入大方孔，横孔对齐。独立测试只夹它的实心大方柄；不夹腕叉和弹簧。',[0,0,35])
 fasten(L,'W_R_',[-25,0,0],[25,0,0],'前臂夹持柄固定')
 L.chapter='05 · 分别调两根腕轴'
 adjustment(L,['WYM_AX','WYP_AX','WXM_AX','WXP_AX'],'腕回中立；先调前臂叉 Y 轴两颗，再调掌侧叉 X 轴两颗；每根轴的两侧交替')
 L.rom('分别检查屈伸与偏摆','先让偏摆回零，屈伸 −65°～70°；再让屈伸回零，偏摆 −20°～30°。动画顺序是先绕 Y 屈伸，再绕随动 X 偏摆；实物两轴组合也需慢慢检查。')
 L.chapter='06 · 换装 100 mm 测力杆'
 L.remove('WPALM_B',[20,0,0],'用 1.5 mm 内六角旋出 M2×14，保存；测力杆会改用 M2×20。')
 L.remove('WPALM_W',[20,0,0],'卸下这片 5×2.2×0.5 平垫，与掌柄五金一起保存。')
 L.remove('WPALM_N',[-20,0,0],'取下普通 M2 螺母，与掌柄五金一起保存。')
 L.remove('W3-09',[0,0,-35],'沿方榫卸下实际掌柄；不要扳动腕叉来硬拔。掌柄与测力杆是替换使用，不能叠装。')
 L.add('F3-W','将原 F3-W 100 mm 加载杆套到同一掌侧方榫，孔对齐。此次测的是同一个实臂腕关节。',[0,0,-35])
 L.add('FW_W2','在螺母一侧先放 5×2.2×0.5 平垫，光滑面朝加载杆，粗面朝即将安装的普通螺母。',[-25,0,0],title='测力杆负侧 · M2 平垫')
 L.add('FW_N','普通 M2，无塑料圈。平整承压面贴刚装的外侧垫圈；这里没有封闭止转槽，需要 4 mm 扳手扶住。',[-25,0,0],title='测力杆负侧 · 普通 M2',detail='这是实际外露螺母位置；不要换成尼龙锁紧螺母增加装配阻力。')
 L.add('FW_W1','另一侧也放一片 5×2.2×0.5 平垫，光滑面朝加载杆，粗面朝螺钉头。',[25,0,0],title='测力杆正侧 · M2 平垫')
 L.add('FW_B','M2×20 从正侧穿过两片垫圈与加载杆，旋入普通 M2。1.5 mm 内六角配 4 mm 小扳手，轻合紧方键连接。',[25,0,0],title='测力杆固定 · M2×20',detail='不要用掌柄的 M2×14 代替。这里夹紧加载杆，不用于调两根腕轴的摩擦。')
 L.check('分别测两个轴，记录结果','用软钳口夹 F3-M。每次让被测轴竖直、加载杆水平，在 100 mm 力孔切向水平拉；另一轴保持 0°。0.060 N 对应 0.006 N·m。',detail='先记录启动力、拖动力和 10 分钟漂移，再按 0/100/500/1000 次循环复查。另一个轴跟着动时读数作废；不能用手扶杆同时读数。详见测试计划。')
 L.check('测试后装回实际掌柄','逆序卸 FW_B、两片垫圈、普通 M2 和 F3-W。装回 W3-09、其普通 M2、0.5 mm 平垫和 M2×14。可跳回“实际掌柄与独立夹持柄”章节重播。',detail='保存两套五金，避免把 M2×20 与 M2×14 混用。独立腕合格后仍需与 H/R 联装再测；不代表整个人偶已通过。')
 return L

def orientation(p):
 id=p['id'];s=p['sku'];b=np.array(p['bounds_mm']);center=b.mean(0);normal=np.array(smooth(p),float);kind=None;target='';target_id=None;note='';instruction='';metal=False
 if s in ['FW4','RW3','W4','W3','W2']:
  kind='washer';metal=s=='W4'
  if metal:
   pre=id[:-2];normal=center-np.array(P[pre+'F2']['bounds_mm']).mean(0);normal/=np.linalg.norm(normal)
  assert np.linalg.norm(normal)>.9,(id,normal)
  target='螺钉头 / 碟簧（无强制正反）' if metal else '转动耳 / 转盘' if s=='FW4' else '固定座反力壁' if s=='RW3' else '相邻打印件'
  instruction='两面均贴金属，无强制正反；去毛刺并保持平整。绿色仅用于辨认其中一面。' if metal else '绿色光滑面朝'+target+'；冲压粗糙面朝相反一侧，先去毛刺。'
  title=s+' · '+p['spec'];face_label='光滑面'+(' · 正反均可' if metal else ' → '+target);opposite='另一面 · 去毛刺'
 elif s in ['N2','N3']:
  kind='plain';pair=id[:-1]+('RW' if id.endswith('_N') and id[:-1]+'RW' in P else 'W')
  if id=='FW_N':pair='FW_W2'
  other=P[pair];normal=np.array(other['bounds_mm']).mean(0)-center;normal/=np.linalg.norm(normal);target='垫圈 / 螺钉头侧';target_id=pair
  instruction='普通螺母，两端都只有金属螺纹，无塑料圈。平整承压面朝垫圈；两面相同时可互换。螺钉从箭头所指的承压侧旋入。'
  title=s+' · 普通螺母，无尼龙圈';face_label='平整承压面 → 垫圈';opposite='另一金属螺纹端 · 无塑料圈'
 elif s=='A8':
  kind='spring';pre=id[:-2];out=np.array(P[pre+'HW']['bounds_mm']).mean(0)-np.array(P[pre+'F2']['bounds_mm']).mean(0);out/=np.linalg.norm(out);normal=out*(1 if id.endswith('S1') else -1);target='外侧螺钉头' if id.endswith('S1') else '内侧关节';title='A8 第 '+('1' if id.endswith('S1') else '2')+' 片 · 内孔凸边方向'
  instruction='内孔凸边朝'+target+'；两片反向，内孔凸边相对。';note='单片自由高约 0.6 mm；两片约 1.2 mm。不能同向套叠，也不能压平到约 0.8 mm。';face_label='内孔凸边 → '+target;opposite='外圆边在相反一侧'
 else:return None
 axis=int(np.argmax(abs(normal)));depth=b[1,axis]-b[0,axis];face=center+normal*depth/2;radius=max(np.delete(b[1]-b[0],axis))/2
 if kind=='washer':bore={'FW4':2.15,'RW3':1.6,'W4':2.15,'W3':1.6,'W2':1.1}[s]
 else:bore=2.1 if kind=='spring' else float(s[1:])/2
 if kind=='spring':face[(axis+1)%3]+=bore
 return dict(kind=kind,normal=normal.tolist(),center=center.tolist(),face=face.tolist(),depth=float(depth),radius=float(radius),bore=bore,title=title,face_label=face_label,opposite_label=opposite,target=target,target_id=target_id,instruction=instruction,note=note or '朝向标记仅帮助辨认，不要求实物着色。',metal_only=metal)

def main():
 catalog={id:dict(id=id,label=p['label'],spec=p['spec'] or p['note'],sku=p['sku'],tool=tool(p),printable=p['printable'],station=p['station'],frame=p['frame'],bounds=p['bounds_mm'],stl=p.get('stl'),orientation=orientation(p)) for id,p in P.items()}
 lessons={}
 for L in [hinge(),roll(),wrist()]:
  expected={id for id,p in P.items() if p['station']==L.station};assert set(L.added)==expected,(L.station,expected-set(L.added),set(L.added)-expected)
  for s in L.steps:s['orientation_ids']=[id for id in s['ids'] if catalog[id]['orientation']]
  lessons[L.station]=dict(steps=L.steps,total_parts=len(expected),printed=sum(P[id]['printable'] for id in expected),final_ids=list(L.state))
 data=dict(revision=REVISION,tutorial_edition=EDITION,geometry_sha256=sha(OUT/'assembly_meshes.npz'),catalog=catalog,lessons=lessons)
 dest=OUT/'tutorial';dest.mkdir(exist_ok=True);put(dest/'steps.json',data);(dest/'steps.js').write_text('window.LESSONS='+json.dumps(data,ensure_ascii=False,separators=(',',':'))+';',encoding='utf8')
 for src,name in [('tutorial.html','index.html'),('tutorial.js','tutorial.js'),('tutorial.css','style.css'),('orientation.js','orientation.js')]:shutil.copyfile(HERE/src,dest/name)
 summary='<h1>H / R / W 逐件动画装配</h1><p>使用 T5 真实制造网格。重印 H5-01、R5-01、W5-01；其余 11 个打印件直接复用。七组预紧堆叠不变，取消三处承力座的合模缝。</p>'
 for st,l in lessons.items():
  summary+=f'<h2>{st} · {len(l["steps"])} 步</h2><p><a class="button" href="tutorial/index.html#{st}-1">打开 {st} 动画</a> · {l["total_parts"]} 个不同实物零件；拆下再装回不会增加采购数量。</p><ol>'
  for s in l['steps']:summary+='<li><a href="tutorial/index.html#'+st+'-'+str(s['n'])+'">'+html.escape(s['title'])+'</a>：'+html.escape(s['text'])+'</li>'
  summary+='</ol>'
 summary+='<h2>操作</h2><p>拖动模型旋转、滚轮缩放；“看全局”显示已有装配，“看本步”放大新增件。“翻看另一面”核对垫圈和碟簧；“看朝向”转到对应端面。进度条可逐帧拖动，连续播放会停在检查点。离线请完整解压 ZIP 后打开 tutorial/index.html，不要只取一个网页文件。</p><p>动画采用名义刚性尺寸；金属螺纹、旋入扭矩、打印误差和实际弹性没有由动画认证。持姿与磨损仍需实测。</p>'
 (OUT/'TUTORIAL.html').write_text(page('T5逐件装配教程',summary),encoding='utf8')
 print('TUTORIAL',json.dumps({st:dict(steps=len(l['steps']),parts=l['total_parts']) for st,l in lessons.items()}),flush=True)

if __name__=='__main__':main()
