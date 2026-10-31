"""T6 one-part lessons with physically checked side-loading reaction hardware."""
from arm_kit import *
from publish import smooth,page
import shutil,collections,html
ZERO=[0.,0.,0.]
ROWS=json.loads((OUT/'assembly.json').read_text('utf8'))['parts']
P={r['id']:r for r in ROWS if r['station']!='C'}
EDITION='T6-闭合六角锁母窝-20261025'

def tool(p):
 sku=p['sku'] or ''
 if sku=='AX4':return '3 mm 内六角；完整六角窝卡住尼龙锁母'
 if sku=='NL3':return '镊子 / C6-01环形推杆；只推金属端，对齐六角'
 if sku.startswith('M2x'):return '1.5 mm 内六角扳手'
 if sku.startswith('M3x'):return '2.5 mm 内六角扳手'
 if sku=='N2':return '镊子；必要时 4 mm 小扳手'
 if sku=='N3':return '镊子；必要时 5.5 mm 小扳手'
 return '手放 / 镊子；清除毛刺，不靠螺钉强拉入位'

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
 L.check('开始前：T6版本与锁母试配',what+'。重印三件固定座，运动件与肩钉沿用T5。先试C6-01的1点竖孔和3点横孔；锁母六角应能到底、不能连续转动。',detail='正式件六角对边5.65mm。先清支撑；太紧只清毛刺，不靠肩钉硬拉；松到能转过一个六角面或出现发白时停止。2点孔5.75仅作打印误差对照，不代表可随意扩大正式件。')
 L.check('分清锁母、普通螺母及四种平垫','7颗主肩钉使用M3×0.5尼龙锁紧螺母，DIN985，对边5.5、总高3.7～4.0。方键与附件仍用普通M2/M3。平垫为5×2.2×0.5、7×3.2×0.5、9×4.3×0.8、12×4.3×1 mm。',detail='旧9×3.2×0.8反力垫本版停用。每组内部必须是1片7×3.2×0.5加2片9×4.3×0.8；另有1片9×4.3×0.8仍放螺钉头下。蓝色标尼龙圈或A8，绿色标光滑面。')

def capture(L,pre,d):
 port=next(p for p in json.loads((OUT/'access_ports.json').read_text('utf8')) if p['prefix']==pre)
 direction=(np.array(port['entry'])*25).tolist()
 L.add(pre+'N','从圆形轴向入口装入M3×0.5尼龙锁紧螺母：蓝色尼龙圈先进入深处，金属承压端朝外。对齐六角后推到底，金属六角段必须进入完整六角窝。',direction,title=pre+' 尼龙锁母 · 先装',detail='总高3.7～4.0、对边≤5.5mm。不是全塑料螺母，也不是4.5mm高型号。可用C6-01环形推杆轻推金属端。六角未入窝时不要用肩钉拉入；入口朝上，尚未夹紧前托住五金。')
 L.steps[-1]['camera']=port_camera(L.station,pre)
 L.add(pre+'RW','7×3.2×0.5 mm薄M3平垫装在锁母金属端。两面均贴金属，无强制正反，平整去毛刺；绝不能装旧9×3.2×0.8反力垫。',direction,title=pre+' 薄反力垫 · 7×3.2×0.5')
 L.steps[-1]['camera']=port_camera(L.station,pre)
 for i in [1,2]:
  L.add(pre+'K'+str(i),'第'+str(i)+'片9×4.3×0.8 mm内置金属间隔垫。沿轴向放进大圆窝；两片叠高1.6mm，支承后续内摩擦垫。两面均贴金属，无强制正反。',direction,title=pre+' 内置间隔垫 '+str(i)+' / 2',detail='孔必须4.3mm，以避让Φ4肩部；不能漏装、改厚度或拿成孔3.2mm垫圈。头下还有同规格第3片，后面单独安装。')
  L.steps[-1]['camera']=port_camera(L.station,pre)

def port_camera(st,pre=''):
 import math
 if not pre:pre={'H':'HR_','R':'R_','W':'WYP_'}[st]
 ports=json.loads((OUT/'access_ports.json').read_text('utf8'));v=np.array(next(p for p in ports if p['prefix']==pre)['entry'])
 return dict(yaw=float(math.atan2(v[1],v[0])),pitch=float(np.clip(math.asin(float(np.clip(v[2],-1,1))),-1.25,1.25)) if abs(v[2])>.8 else .25)

def inner(L,pre,d):L.add(pre+'F1','12×4.3×1 mm 内侧摩擦垫贴固定座端面，光滑面朝外，稍后贴 3 mm 厚的转动耳 / 转盘。两侧同规格、无毛刺。',d,title=pre+' 内侧摩擦垫')

def outer(L,pre,d):
 L.add(pre+'F2','12×4.3×1 mm外摩擦垫，光滑面朝内，贴3mm运动耳；与内摩擦垫光滑面相向。',d,title=pre+' 外摩擦垫')
 L.add(pre+'S1','第一片A8：内孔凸边朝外、朝螺钉头。',d,title=pre+' A8第1片 · 凸边朝外')
 L.add(pre+'S2','第二片A8翻面：内孔凸边朝关节，与第一片内孔凸边相对。',d,title=pre+' A8第2片 · 凸边朝内',detail='反向串联；自由叠高约1.2mm，不能同向套叠，也不能压平。')
 L.add(pre+'HW','9×4.3×0.8 mm头下垫；这是本组第3片同规格垫圈，前两片已在固定座内。两面均贴金属，去毛刺即可。',d,title=pre+' 头下平垫 · 第3片同规格')
 port=next(p for p in json.loads((OUT/'access_ports.json').read_text('utf8')) if p['prefix']==pre)
 axis=np.array(port['entry']);end=(axis*5).tolist()
 L.add(pre+'AX','复用O22肩钉：Φ4×8，M3×0.5螺纹长6，头Φ7×3，3mm内六角。先穿过外部堆叠，对准锁母金属螺纹端。',d,end=end,title=pre+' 肩钉对中 · 先接金属螺纹')
 L.step(pre+' 旋过尼龙圈，再到轻接触','用3mm内六角缓慢旋入。金属螺纹初段应顺畅，遇尼龙圈后阻力增大属正常。确认螺母留在六角窝内不跟转，再继续至各垫片刚贴合。','move',[pre+'AX'],{pre+'AX':[end,ZERO]},detail='动画旋入圈数仅为名义路径，不是紧固标准。尼龙阻力≠碟簧已压紧；不要钻掉尼龙、润滑摩擦面，或靠猛拧压平碟簧。金属段初始就卡时退出检查。',toolname='3mm内六角；托住固定座，不需手捏螺母')
 origin=np.array(port['M'])[:3,3].tolist()
 L.steps[-1]['posePaths']={pre+'AX':[dict(before=ZERO,pivot=origin,axis=axis.tolist(),angle=0.,after=end),dict(before=ZERO,pivot=origin,axis=axis.tolist(),angle=-3600.,after=ZERO)]}

def fasten(L,pre,nd,wd,context):
 L.add(pre+'N',context+'：普通 '+P[pre+'N']['spec']+'，从六角槽开口装到底，平整面朝承压侧。',nd,title=context+' · 普通螺母')
 L.add(pre+'W',context+'：'+P[pre+'W']['spec']+'，光滑面贴打印件，另一面朝螺钉头。',wd,title=context+' · 平垫圈')
 L.add(pre+'B',context+'：'+P[pre+'B']['spec']+'。从垫圈侧旋入普通螺母，轻合紧。此连接负责固定结构，不调关节摩擦。',wd,title=context+' · '+P[pre+'B']['sku'])

def adjustment(L,ids,axes):
 L.check('确认穿过尼龙圈，再小步调预紧',axes+'。先检查肩钉尖端已经完整穿过尼龙圈并露出完整螺纹；确认肩部没有顶住孔3.2的薄垫。再交替小步调到可用持姿，每步最多约1/24圈。',ids,detail='名义碟簧叠高0.9～1.2mm时，肩端间隙0.3～0.6mm、尖端穿出0.9～1.2mm；不是实物公差保证或弹力标定。实际尺寸不符就停下核对，不能补拧到碟簧压平来换取穿出量。')
 L.check('建立0次基线，100次内不补紧','在肩钉头和固定参考件画见证线，记录尖端位置、间隙、启动力与拖动力。调节结束计为0次，之后在10、20、50、100次检查；不中途补紧。',ids,detail='一次完整往返算一循环，同时记录单程次数。锁母若随螺钉持续转动、槽壁发白或裂开，立即停止。若必须补紧，本轮100次目标未通过；不能磨合50次后重新计数掩盖早期衰减。')

def hinge():
 L=Lesson('H');prep(L,'H 是实际肘屈伸关节，配 F3-H 可拆 100 mm 加载杆')
 L.chapter='01 · 固定座内的反力组件'
 L.add('H6-01','一体肘固定座放稳，两侧外端是轴向圆形入口，逐侧朝上安装。T6封闭了原侧装滑槽，完整六角窝负责止转。',[0,0,25])
 L.steps[-1]['camera']=port_camera('H')
 for pre in ['HL_','HR_']:capture(L,pre,[-25,0,0])
 L.check('核对两组锁母和金属间隔垫','两组各有1颗尼龙锁母、1片薄M3垫、2片M4间隔垫，孔同轴。锁母六角已入窝，托住内部五金，再装原运动叉。',['H6-01','HL_N','HR_N'])
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
 L.check('测持姿，而不只摸手感','100 mm 垂直力臂时，0.40 N 对应 0.040 N·m。测启动力、持续拖动力和 10 分钟保持漂移；在0/10/20/50/100次记录，100次内不补紧。',detail='用力的方向必须与力臂垂直；加载杆自重和夹具方向会影响读数。按测试计划记录，不能只凭动画判断合格。')
 return L

def roll():
 L=Lesson('R');prep(L,'R 是沿前臂骨轴的旋转关节，配 F3-R 可拆 100 mm 加载杆')
 L.chapter='01 · 固定芯和预装转盘螺母'
 L.add('R6-01','一体旋转固定芯，主体宽 13 mm，输入方键仍为 10 mm。Z=0圆形端面是轴向装入口。该面朝上，先装入锁母及三片内部垫圈，侧面没有旧滑槽。',[0,0,25])
 L.steps[-1]['camera']=port_camera('R')
 capture(L,'R_',[0,-25,0])
 L.check('确认锁母与三片内部垫圈就位','锁母六角已进入完整窝，薄M3垫和两片M4垫顺序正确。先托住内部五金，再预装转盘。',['R6-01','R_N','R_RW'])
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
 L=Lesson('W');prep(L,'W 是两个相交转轴的 T6 腕：前臂叉做屈伸、掌侧叉做偏摆，最后可换测力杆')
 L.chapter='01 · 十字芯内的四组反力组件'
 L.add('W6-01','一体十字芯，四个轴向圆形入口在±X/±Y端面。逐个入口朝上安装；±Z面不再有侧装滑槽。',[0,0,25])
 L.steps[-1]['camera']=port_camera('W')
 for pre in ['WYM_','WYP_','WXM_','WXP_']:capture(L,pre,[0,0,-25])
 L.check('核对四组锁母与十二片内部垫圈','四颗尼龙锁母、四片7×3.2×0.5薄垫和八片9×4.3×0.8间隔垫已按顺序装入。肩钉未夹紧前托住五金；临时胶带只防掉，不夹进接触面。然后安装两只原运动叉。',['W6-01','WYM_N','WYP_N','WXM_N','WXP_N'])
 for axis,piece,offset,label in [('Y','W4-01',[0,0,40],'前臂侧屈伸叉'),('X','W4-04',[0,0,-40],'掌侧偏摆叉')]:
  L.chapter=('02' if axis=='Y' else '03')+' · '+label+'与碟簧'
  vec=Y if axis=='Y' else X
  for sign in [-1,1]:inner(L,'W'+axis+('M_' if sign<0 else 'P_'),(vec*sign*25).tolist())
  L.add(piece,label+'从'+('上方前臂端' if axis=='Y' else '下方掌端')+'套入，两只 3 mm 耳在内侧垫圈外侧。大方孔属于前臂侧，小方榫属于手掌侧；不要把两叉装反。',offset)
  for sign in [-1,1]:outer(L,'W'+axis+('M_' if sign<0 else 'P_'),(vec*sign*25).tolist())
  L.check(axis+'轴两侧先保持轻接触','两侧肩钉均已穿过尼龙锁母，再交替消除明显间隙。检查两对 A8 都是内孔凸边相对，未同向套叠。',['W'+axis+'M_AX','W'+axis+'P_AX'])
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
 L.check('分别测两个轴，记录结果','用软钳口夹 F3-M。每次让被测轴竖直、加载杆水平，在 100 mm 力孔切向水平拉；另一轴保持 0°。0.060 N 对应 0.006 N·m。',detail='先记录启动力、拖动力和 10 分钟漂移，再按 0/10/20/50/100次循环复查；100次内不补紧。另一个轴跟着动时读数作废；不能用手扶杆同时读数。详见测试计划。')
 L.check('测试后装回实际掌柄','逆序卸 FW_B、两片垫圈、普通 M2 和 F3-W。装回 W3-09、其普通 M2、0.5 mm 平垫和 M2×14。可跳回“实际掌柄与独立夹持柄”章节重播。',detail='保存两套五金，避免把 M2×20 与 M2×14 混用。独立腕合格后仍需与 H/R 联装再测；不代表整个人偶已通过。')
 return L

def orientation(p):
 id=p['id'];s=p['sku'];b=np.array(p['bounds_mm']);center=b.mean(0);normal=np.array(smooth(p),float);kind=None;target='';target_id=None;note='';instruction='';metal=False
 if s in ['FW4','RW3','W4','W3','W2']:
  kind='washer';metal=s=='W4' or id.endswith('_RW')
  if metal:
   pre=id[:-2];normal=np.array(P[pre+'F2']['bounds_mm']).mean(0)-np.array(P[pre+'F1']['bounds_mm']).mean(0);normal/=np.linalg.norm(normal)
  assert np.linalg.norm(normal)>.9,(id,normal)
  target=('螺钉头 / 碟簧（无强制正反）' if id.endswith('HW') else '相邻金属件（无强制正反）') if metal else '转动耳 / 转盘' if s=='FW4' else '固定座反力壁' if s=='RW3' else '相邻打印件'
  instruction='两面均贴金属，无强制正反；去毛刺并保持平整。绿色仅用于辨认其中一面。' if metal else '绿色光滑面朝'+target+'；冲压粗糙面朝相反一侧，先去毛刺。'
  title=s+' · '+p['spec'];face_label='光滑面'+(' · 正反均可' if metal else ' → '+target);opposite='另一面 · 去毛刺'
 elif s=='NL3':
  kind='nylon';pre=id[:-1];normal=center-np.array(P[pre+'RW']['bounds_mm']).mean(0);normal/=np.linalg.norm(normal)
  target='螺钉尖端 / 六角窝深处';target_id=pre+'RW'
  instruction='蓝色尼龙圈先进入窝的深处；相反的金属承压端贴薄M3垫，螺钉先旋入金属端、最后穿过尼龙圈。'
  title='NL3 · M3×0.5尼龙锁紧螺母';face_label='尼龙圈 → 螺钉尖端';opposite='金属承压端 → 薄M3垫圈'
  note='图中蓝色表示尼龙圈，实际颜色可能不同。抵达尼龙后需要工具旋入，不能直推或钻掉圈。'
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
 if kind=='nylon':radius=2.2
 if kind=='washer':bore={'FW4':2.15,'RW3':1.6,'W4':2.15,'W3':1.6,'W2':1.1}[s]
 else:bore=2.1 if kind=='spring' else 1.52 if kind=='nylon' else float(s[1:])/2
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
 summary='<h1>H / R / W 逐件动画装配</h1><p>使用 T6 真实制造网格。重印 H6-01、R6-01、W6-01；10个运动件及附件直接复用，另有新C6-01试片。七组主肩钉改用尼龙锁母、完整六角窝和内部金属间隔垫。</p>'
 for st,l in lessons.items():
  summary+=f'<h2>{st} · {len(l["steps"])} 步</h2><p><a class="button" href="tutorial/index.html#{st}-1">打开 {st} 动画</a> · {l["total_parts"]} 个不同实物零件；拆下再装回不会增加采购数量。</p><ol>'
  for s in l['steps']:summary+='<li><a href="tutorial/index.html#'+st+'-'+str(s['n'])+'">'+html.escape(s['title'])+'</a>：'+html.escape(s['text'])+'</li>'
  summary+='</ol>'
 summary+='<h2>操作</h2><p>拖动模型旋转、滚轮缩放；“看全局”显示已有装配，“看本步”放大新增件。“翻看另一面”核对垫圈和碟簧；“看朝向”转到对应端面。进度条可逐帧拖动，连续播放会停在检查点。离线请完整解压 ZIP 后打开 tutorial/index.html，不要只取一个网页文件。</p><p>动画采用名义刚性尺寸；金属螺纹、旋入扭矩、打印误差和实际弹性没有由动画认证。持姿与磨损仍需实测。</p>'
 (OUT/'TUTORIAL.html').write_text(page('T6逐件装配教程',summary),encoding='utf8')
 print('TUTORIAL',json.dumps({st:dict(steps=len(l['steps']),parts=l['total_parts']) for st,l in lessons.items()}),flush=True)

if __name__=='__main__':main()
