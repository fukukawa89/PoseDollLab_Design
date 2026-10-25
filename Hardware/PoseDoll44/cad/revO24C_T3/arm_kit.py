"""O24C-T3: actual elbow, axial-roll and wrist modules, millimetres.

The installed forearm and the three specimens share EXACTLY the same solids.
Only detachable load arms are bench-only. Frozen O24C/T1/T2 files are read-only.
"""
from pathlib import Path
import sys, json, csv, math
sys.dont_write_bytecode=True
HERE=Path(__file__).resolve().parent; H=HERE.parents[1]; ROOT=H.parents[1]
OUT=H/'bench/revO24C_T3'
sys.path.insert(0,str(H/'cad/revO24C_T1'))
import kit as old
from kit import a, md, np, trimesh, box, cyl, tube, beam, rot, moved, hexagon, nut, screw, washer, mesh, sha, put, X, Y, Z
sys.path.insert(0,str(HERE))
REVISION='O24C-T3'
PROFILE=json.loads((H/'bench/revO24/profiles/arm_profile.json').read_text('utf8'))
FORE=PROFILE['forearm_mm']; UPPER=PROFILE['upperarm_mm']
R_OFFSET=36.0
COLORS={'structure':[.32,.65,.60], 'rotor':[.93,.59,.23], 'metal':[.65,.69,.74],
        'spring':[.25,.44,.84], 'friction':[.67,.39,.22], 'magnet':[.76,.23,.29], 'fixture':[.60,.62,.67]}
SPECS={
 'AX4':'O22 轴肩螺钉：光杆 Φ4×8，M3×0.5 螺纹长6，头Φ7×3，内六角3 mm',
 'A8':'A8 碟簧：外径8、内径4.2、料厚0.4、自由高约0.6 mm；实物曲线待测',
 'FW4':'M4 大平垫圈：12×4.3×1.0 mm，钢',
 'W4':'M4 平垫圈：9×4.3×0.8 mm，钢',
 'RW3':'M3 大平垫圈：9×3.2×0.8 mm，钢（O22）',
 'N3':'普通 M3×0.5 六角螺母 AF5.5×2.4，无尼龙圈',
 'N4':'普通 M4×0.7 六角螺母 AF7×3.2，无尼龙圈',
 'N2':'普通 M2×0.4 六角螺母 AF4×1.6，无尼龙圈',
 'NL2':'M2 尼龙锁紧螺母 AF4，高≤3 mm；仅球体合模两颗',
 'W3':'M3 平垫圈：7×3.2×0.5 mm，钢',
 'W2':'M2 平垫圈：5×2.2×0.5 mm，钢',
 'GUIDE_M2_D2P5_L6':'腕导向轴肩螺钉：Φ2.5×6 / M2×0.4 螺纹长4，头Φ4.8×2.4，内六角2 mm',
}
for d,ls in [(2,[6,12,14,16,20]),(3,[12,16,18,20]),(4,[35])]:
 for l in ls:SPECS[f'M{d}x{l}']=f'M{d}×{l} 内六角圆柱头螺钉，公制粗牙；长度不含头'

class Design:
 def __init__(self): self.parts=[]; self.stacks=[]
 def add(self,id,label,s,station,frame='fixed',printed=False,orientation=None,role='structure',sku=None,note='',bench=False):
  assert not s.is_empty() and str(s.status())=='Error.NoError',id
  self.parts.append(dict(id=id,label=label,s=s,station=station,frame=frame,printable=printed,
   orientation=np.eye(4) if orientation is None else orientation,role=role,sku=sku,
   spec=SPECS.get(sku,label) if sku else '',note=note,bench_only=bench))
 def print(self,id,label,s,st,frame='fixed',orientation=None,note='',role='structure',bench=False):
  self.add(id,label,s,st,frame,True,orientation,role,note=note,bench=bench)
 def metal(self,id,sku,s,st,frame='fixed',role='metal',note='',label=None):
  self.add(id,label or SPECS[sku],s,st,frame,sku=sku,role=role,note=note)
 def fastener(self,id,d,l,p,axis,st,frame='fixed'):
  self.metal(id,f'M{d}x{l}',screw(p,axis,d,l),st,frame)

def disc(y,h,flipped=False):
 p=np.array([[2.1,h-.4],[4,0],[4,.4],[2.1,h]])
 if flipped:p[:,1]=h-p[:,1];p=p[::-1].copy()
 return moved(md.CrossSection([p]).revolve(circular_segments=64),rot(X,-90)).translate([0,y,0])

def stack(d,prefix,st,M,h=1.0):
 """Fixed face u=0; rotor u=1..4, actual O22 screw and spring pair.
 Nut -6..-3.6; reaction -3.6..-2.8; shoulder counterbore floor -1.9.
 M maps local +Y outward from the fixed seat. All hardware is stationary.
 """
 def met(suf,sku,s,role='metal',note=''):d.metal(prefix+suf,sku,moved(s,M),st,role=role,note=note)
 met('N','N3',nut([0,-6,0],Y,3,5.5,2.4),note='普通螺母装在合模六角槽内；平整承压面朝反力垫。')
 met('RW','RW3',washer([0,-3.6,0],Y,9,3.2,.8),note='光滑面朝固定座反力壁（远离螺母）。')
 for i,u in enumerate([0,4]):met('F'+str(i+1),'FW4',washer([0,u,0],Y,12,4.3,1),'friction','光滑面朝中间3mm转动耳；粗糙面去毛刺。')
 for i in range(2):met('S'+str(i+1),'A8',disc(5+i*h/2,h/2,i==1),'spring','两片内孔凸边相对；第一片凸边朝螺钉头，第二片朝关节。不得同向套叠。')
 met('HW','W4',washer([0,5+h,0],Y,9,4.3,.8),note='头下金属垫，去毛刺。')
 head=5.8+h
 bolt=cyl([0,head-14,0],[0,head-8,0],1.5)+cyl([0,head-8,0],[0,head,0],2)+cyl([0,head,0],[0,head+3,0],3.5)
 bolt-=hexagon([0,head+3.01,0],-Y,3,1.7)
 met('AX','AX4',bolt,note='只拧外侧3mm内六角；内藏普通螺母止转。标记头位，短测后再作金属螺纹锁固。')
 d.stacks.append(dict(id=prefix,kind='shoulder',pair_height=h,nut_full_height=2.4,shoulder_floor_gap_mm=head-8+1.9,tip_past_nut_mm=-(head-14)-6,pressure_path='head / W4 / A8 opposed pair / FW4 / 3mm rotor / FW4 / fixed seat / RW3 / captive N3; no ball bearing',thread_pitch=.5))

def seat_cut(M):
 s=cyl([0,-8.1,0],[0,.1,0],1.7)+cyl([0,-1.9,0],[0,.1,0],2.125)
 s+=hexagon([0,-6.1,0],Y,5.8,2.6)+cyl([0,-3.65,0],[0,-2.8,0],4.65)
 return moved(s,M)

def through(d,id,p,st,frame='fixed',length=12):
 """X direction screw through 10mm wide printed key. Captive plain N3."""
 p=np.array(p,float)
 d.fastener(id+'B',3,length,p+np.array([5.5,0,0]),-X,st,frame)
 d.metal(id+'W','W3',washer(p+np.array([5,0,0]),X,7,3.2,.5),st,frame,note='光滑面朝打印件。')
 d.metal(id+'N','N3',nut(p+np.array([-5,0,0]),X,3,5.5,2.4),st,frame,note='普通螺母；装入外侧六角槽。')

def hinge(d,h=1):
 # Fixed fork halves: actual upper-bone centreline is X=Y=0, not a bench base.
 parent=box([-5,-5,18],[5,5,42])
 for side in [-1,1]:
  M=a.T([0,side*10,0])@(np.eye(4) if side==1 else rot(X,180))
  parent+=cyl([0,side*3,0],[0,side*10,0],8.2)
  parent+=beam([0,side*6.5,0],[0,side*6.5,17],3.5)+beam([0,side*6.5,17],[0,0,22],3.5)
  parent-=seat_cut(M)
  stack(d,'H'+('L' if side<0 else 'R')+'_','H',M,h)
 parent-=box([2.9,-5.1,17.5],[6,5.1,25.5])
 for z in [28,36]:
  parent-=cyl([-10,0,z],[10,0,z],1.7)+hexagon([5.1,0,z],-X,5.8,2.7)
  d.fastener('HC'+str(z)+'B',3,12,[-5.5,0,z],X,'H')
  d.metal('HC'+str(z)+'W','W3',washer([-5.5,0,z],X,7,3.2,.5),'H',note='光滑面朝打印件；螺钉头在后侧，留出屈肘空间。')
  d.metal('HC'+str(z)+'N','N3',nut([2.6,0,z],X,3,5.5,2.4),'H')
 for side,n in [(-1,'01'),(1,'02')]:
  s=parent^box([-25 if side<0 else 0,-25,-10],[0 if side<0 else 25,25,43])
  d.print('H3-'+n,'肘固定叉合模半件 '+str(side),s,'H',orientation=rot(Y,-90*side),note='X=0合模面朝下；先装两组普通M3螺母及9mm反力垫，再合拢。完整反力壁厚2.8mm。')
 rotor=box([-8.2,-8.2,-27.7],[8.2,8.2,-19])
 rotor-=box([-5.15,-5.15,-27.8],[5.15,5.15,-19.8])
 rotor-=box([-.4,-8.3,-27.8],[.4,-5.1,-19.8])
 for side in [-1,1]:
  ear=cyl([0,side*11,0],[0,side*14,0],8.2)-cyl([0,side*10.9,0],[0,side*14.1,0],2.125)
  stem=beam([0,side*12.5,-4],[0,side*12.5,-17],2.8)+beam([0,side*12.5,-17],[0,side*6,-23],2.8)
  # Keep the friction ear exactly 3mm thick and clear both free washers.
  near=cyl([0,-20,0],[0,20,0],8.6)
  slab=box([-15,min(side*11,side*14),-20],[15,max(side*11,side*14),10])
  stem=(stem-near)+(stem^near^slab)
  stem-=cyl([0,-20,0],[0,20,0],6.2)
  rotor+=ear+stem
 rotor-=box([-5.15,-5.15,-27.8],[5.15,5.15,-19.8])
 rotor-=cyl([-12,0,-23.5],[12,0,-23.5],1.7)+hexagon([8.3,0,-23.5],-X,5.8,2.8)
 d.print('H3-03','肘转动叉／R模块方键接口',rotor,'H','rotor',rot(X,90),note='两侧转动耳均3mm；内嵌10.3mm方孔，R上端方键居骨轴。',role='rotor')
 # Interface screw belongs to H; fully seated plain nut, head accessible.
 d.fastener('H_R_B',3,18,[-8.7,0,-23.5],X,'H','rotor')
 d.metal('H_R_W','W3',washer([-8.7,0,-23.5],X,7,3.2,.5),'H','rotor')
 d.metal('H_R_N','N3',nut([5.8,0,-23.5],X,3,5.5,2.4),'H','rotor')

def roll(d,h=1):
 M=rot(X,-90) # +Y -> -Z; fixed face at local Z=0, installed E-36.
 body=box([-5,-10.9,0],[5,10.9,8])+box([-5,-5,7],[5,5,16])
 body-=seat_cut(M)
 body-=cyl([-12,0,12.5],[12,0,12.5],1.7)
 for y in [-7.4,7.4]:
  body-=cyl([-9,y,4],[9,y,4],1.15)+hexagon([-5.1,y,4],X,4.35,1.9)
  d.fastener('RC'+str(y)+'B',2,12,[5.5,y,4],-X,'R')
  d.metal('RC'+str(y)+'W','W2',washer([5,y,4],X,5,2.2,.5),'R',note='光滑面朝打印件。')
  d.metal('RC'+str(y)+'N','N2',nut([-5,y,4],X,2,4,1.6),'R')
 for side,n in [(-1,'01'),(1,'02')]:
  d.print('R3-'+n,'轴向旋转固定芯合模半件 '+str(side),body^box([-20 if side<0 else 0,-20,-1],[0 if side<0 else 20,20,17]),'R',orientation=rot(Y,-90*side),note='合模面朝下，捕获普通M3螺母及反力垫；上端10mm方键与H相接。')
 stack(d,'R_','R',M,h)
 discbody=cyl([0,0,-4],[0,0,-1],12.5)-cyl([0,0,-4.1],[0,0,-.9],2.125)
 cup=tube([0,0,-11],[0,0,-4],12.5,6.3)+cyl([0,0,-13.7],[0,0,-11],12.5)+box([-5,-5,-24],[5,5,-13])
 cup-=cyl([0,0,-24.1],[0,0,-3.9],3.2)
 interface_z=R_OFFSET-FORE+25
 cup-=cyl([-12,0,interface_z],[12,0,interface_z],1.7)
 for y in [-8.5,8.5]:
  discbody-=cyl([0,y,-4.1],[0,y,-.8],1.15)+hexagon([0,y,-2.8],Z,4.35,1.9)
  cup-=cyl([0,y,-14.1],[0,y,-3.9],1.15)
  d.fastener('RO'+str(y)+'B',2,14,[0,y,-14.2],Z,'R','rotor')
  d.metal('RO'+str(y)+'W','W2',washer([0,y,-14.2],Z,5,2.2,.5),'R','rotor',note='光滑面朝外壳。')
  d.metal('RO'+str(y)+'N','N2',nut([0,y,-2.6],Z,2,4,1.6),'R','rotor')
 d.print('R3-03','同轴摩擦转盘／可更换磨损件',discbody,'R','rotor',note='厚3mm；M2普通螺母先装在背面六角槽。转盘与头下碟簧同轴，无滚珠轴承旁路。',role='rotor')
 d.print('R3-04','旋转输出壳／居中方键骨杆',cup,'R','rotor',rot(X,180),note='中央6.4mm通道供3mm内六角调节；先取下W连接螺钉再伸入工具。',role='rotor')

def wrist(d,h=1):
 # S1 ball and stock guide pins remain interchangeable. T3 liners have an
 # additional straight washer-entry relief, checked as a swept assembly path.
 k=old.Kit();old.wrist(k)
 selected={'W01','W02','W03','W04','W05'}
 for p in k.parts:
  if p['id'] not in selected and not (p['id'].startswith('Wball_') or p['id'].startswith('Wguide')):continue
  id='W3-'+p['id'][1:] if p['id'] in selected else p['id']
  pr=p['printable'];sku=None
  if not pr:
   if p['id'].startswith('Wball_bolt'):sku='M2x14'
   elif p['id'].startswith('Wball_nut'):sku='NL2'
   elif p['id'].startswith('Wguide_w'):sku='W2'
   elif p['id'].startswith('Wguide_nut'):sku='N2'
   else:sku='GUIDE_M2_D2P5_L6'
  solid=p['s'];note=p['note'];label=p['label']
  if p['id'] in ['W04','W05']:
   side=-1 if p['id']=='W04' else 1
   for xx in [-8.5,8.5]:solid-=cyl([xx,side*7.0,0],[xx,side*12.25,0],2.7)
   label='T3 球面衬片（直入垫圈避让） '+str(side);note='保持内R11.05/外R11.75及D2.94导向槽；新增D5.4垫圈直入通道。不能用旧T1衬片替代本装配流程。'
  d.add(id,label,solid,'W',p['frame'],pr,k.prints[p['id']]['orientation'] if pr else None,p['role'],sku,note)
 slot=a.union(moved(cyl([0,s*9.8,0],[0,s*18,0],1.47),rot(X,deg)) for s in [-1,1] for deg in np.linspace(-23,33,57))
 for sign,n in [(-1,'06'),(1,'07')]:
  side=box([-22,9.6 if sign>0 else -22,-9.3],[22,22 if sign>0 else -9.6,28])
  cup=((old.sph(14)-old.sph(11.75))^side)-slot
  pockets=[]
  for xx in [-8.5,8.5]:
   sx=np.sign(xx)
   rc=beam([sx*5.2,sign*10.1,4],[xx,sign*12.8,4],.95)
   pocket=md.Manifold.batch_hull([rc,rc.translate([0,-sign*4,0])])+box([xx-2.2,min(sign*8,sign*13.55),-4.4],[xx+2.2,max(sign*8,sign*13.55),4.4])
   boss=box([xx-2.8,min(sign*11.6,sign*18.3),-5.2],[xx+2.8,max(sign*11.6,sign*18.3),5.2])-pocket
   boss-=cyl([xx,sign*9,0],[xx,sign*12.25,0],2.7)+cyl([xx,sign*10,0],[xx,sign*20,0],1.15)+hexagon([xx,sign*14.8,0],sign*Y,4.35,4)
   cup+=boss
   pockets.extend([pocket,cyl([xx,sign*9,0],[xx,sign*12.25,0],2.7)])
   d.fastener('WL'+str(sign)+'_'+str(xx)+'B',2,6,[xx,sign*11.7,0],sign*Y,'W')
   d.metal('WL'+str(sign)+'_'+str(xx)+'W','W2',washer([xx,sign*11.7,0],sign*Y,5,2.2,.5),'W',note='0.5mm厚，光滑面朝衬片；本版螺钉头基准11.7mm。')
   d.metal('WL'+str(sign)+'_'+str(xx)+'N','N2',nut([xx,sign*14.8,0],sign*Y,2,4,1.6),'W',note='普通M2，槽内止转；不用尼龙锁紧型。')
  # Two full 4mm wide webs, not the old slender standalone arms.
  for xx in [-8,8]:
   cup+=box([xx-2,min(sign*10.0,sign*13.5),3.5],[xx+2,max(sign*10.0,sign*13.5),22.8])
   lo,hi=(9.5,13.5) if sign>0 else (-16.5,-9.5)
   cup+=box([xx-6,lo,12.5],[xx+6,hi,25.5])
   cup-=cyl([xx,-20,19],[xx,20,19],2.2)
   if sign<0:cup-=hexagon([xx,-16.6,19],Y,7.35,3.4)
  cup-=slot+old.sph(11.75)+a.union(pockets)
  d.print('W3-'+n,'带碟簧预紧耳的腕球窝 '+str(sign),cup,'W',orientation=rot(X,90*sign),note='保留S3朝球心开放的衬片入口。负Y侧加厚到7mm，M4普通螺母槽后有3.7mm反力壁；槽边最窄约2.25mm。')
 # Actual centred wrist bridge; no enlarged bench base.
 bridge=box([-13,-6,16],[13,6,23])+box([-8.2,-8.2,21],[8.2,8.2,29.8])
 bridge-=box([-5.15,-5.15,20],[5.15,5.15,29.9])
 bridge-=box([-.4,-8.3,20.2],[.4,-5.1,29.9])
 bridge-=cyl([-12,0,25],[12,0,25],1.7)+hexagon([-8.3,0,25],X,5.8,2.8)
 bridge-=cyl([8.2,0,25],[14,0,25],3.65)+cyl([-14,0,25],[-8.2,0,25],3.65)
 for y in [-8.5,8.5]:bridge-=cyl([0,y,27.9],[0,y,30.1],2.15)
 for xx in [-8,8]:bridge-=cyl([xx,-9,19],[xx,9,19],2.2)
 # Fix the negative cup to the bone bridge. With two floating cups the entire
 # bolt/cup/ball group would otherwise slide along Y in the bridge holes.
 # The positive cup alone moves for preload; its remaining gap is not a
 # substitute for a positive location of the socket assembly.
 fixed_cup=next(p for p in d.parts if p['id']=='W3-06')
 bridge+=fixed_cup['s']
 for xx in [-8,8]:bridge+=tube([xx,-9.7,19],[xx,-5.8,19],4.7,2.2)
 d.parts.remove(fixed_cup)
 d.print('W3-08','固定侧球窝与骨杆桥一体件',bridge,'W',orientation=rot(X,90),note='取代独立W3-06及旧分体桥；两处连续反力连接固定负Y球窝，只有W3-07浮动预紧。方孔10.3mm直接接R；球心名义坐标不动。')
 d.fastener('W_R_B',3,20,[8.7,0,25],-X,'W')
 d.metal('W_R_W','W3',washer([8.2,0,25],X,7,3.2,.5),'W',note='光滑面朝固定桥。')
 d.metal('W_R_N','N3',nut([-8.2,0,25],X,3,5.5,2.4),'W')
 for xx in [-8,8]:
  pre='WP'+str(xx)
  d.metal(pre+'N','N4',nut([xx,-16.4,19],Y,4,7,3.2),'W',note='普通M4；从负Y外侧装入六角槽，承压面朝槽底，不使用尼龙型。')
  for suf,y in [('W0',13.5),('W1',14.3+h)]:d.metal(pre+suf,'W4',washer([xx,y,19],Y,9,4.3,.8),'W',note='下垫光滑面朝打印耳；上垫两面去毛刺。')
  for i in range(2):d.metal(pre+'S'+str(i+1),'A8',disc(14.3+i*h/2,h/2,i==1).translate([xx,0,19]),'W',role='spring',note='内孔凸边相对。M4螺杆直接导向A8，不能用M3螺杆替换。')
  head=15.1+h
  d.fastener(pre+'B',4,35,[xx,head,19],-Y,'W')
  d.stacks.append(dict(id=pre,kind='M4',underhead=head,nut_exit=-16.4,protrusion_mm=35-(head+16.4),minimum_two_threads_mm=1.4,pair_height=h))
 palm=box([-5,-11,-45],[5,11,-22])-box([-3.2,-3.2,-31.2],[3.2,3.2,-21.9])
 palm-=cyl([-10,0,-27],[10,0,-27],1.15)+hexagon([-5.1,0,-27],X,4.35,1.9)
 palm-=cyl([0,-12,-40],[0,12,-40],1.8)
 d.print('W3-09','实际掌部握柄（非100mm测试杆）',palm,'W','ball',rot(X,90),note='方键套住原球颈；尺寸10×22×23，保留腕中心。',role='rotor')
 d.fastener('WPALM_B',2,14,[5.5,0,-27],-X,'W','ball')
 d.metal('WPALM_W','W2',washer([5,0,-27],X,5,2.2,.5),'W','ball',note='光滑面朝掌柄。')
 d.metal('WPALM_N','N2',nut([-5,0,-27],X,2,4,1.6),'W','ball')

def fixtures(d):
 # These three fixtures are explicitly absent from the installed arm.
 f=box([-5,-5,-28],[5,5,-20])+box([-5,-4,-100],[5,4,-27])+cyl([0,-4,-100],[0,4,-100],5)
 f-=cyl([-8,0,-23.5],[8,0,-23.5],1.7)+cyl([0,-6,-100],[0,6,-100],1.8)
 d.print('F3-H','H专用100mm加载杆／可拆',f,'H','rotor',rot(X,90),bench=True,role='fixture')
 z=R_OFFSET-FORE+25
 f=box([-8.2,-8.2,-24],[8.2,8.2,-14.7])-box([-5.15,-5.15,-24.1],[5.15,5.15,-14.6])
 for y in [-8.5,8.5]:f-=cyl([0,y,-16.5],[0,y,-14.6],2.15)
 f+=box([-4,7,z-3],[4,100,z+3])+cyl([0,100,z-3],[0,100,z+3],5)
 f-=cyl([-12,0,z],[12,0,z],1.7)+hexagon([-8.3,0,z],X,5.8,2.8)+cyl([0,100,z-4],[0,100,z+4],1.8)
 d.print('F3-R','R专用径向100mm加载杆／可拆',f,'R','rotor',bench=True,role='fixture',note='测试时使用FR M3×20及普通螺母；与W互换，不能同时安装。')
 d.fastener('FR_B',3,20,[8.7,0,z],-X,'R','rotor')
 d.metal('FR_W','W3',washer([8.2,0,z],X,7,3.2,.5),'R','rotor')
 d.metal('FR_N','N3',nut([-8.2,0,z],X,3,5.5,2.4),'R','rotor')
 for p in d.parts[-3:]:p['bench_only']=True
 k=old.Kit();old.wrist(k);s=next(p['s'] for p in k.parts if p['id']=='W09')
 d.print('F3-W','W专用100mm加载杆／可拆',s,'W','ball',rot(X,90),bench=True,role='fixture',note='与实际掌柄互换；使用原T1 M2×20及两片0.5垫圈、普通M2螺母。')
 mount=box([-5,-5,21],[5,5,30.3])+box([-10,-10,30.2],[10,10,50])
 mount-=cyl([-7,0,25],[7,0,25],1.7)
 d.print('F3-M','W独立测试用夹持柄／可拆',mount,'W',orientation=rot(X,180),bench=True,role='fixture',note='借用W_R连接螺钉。只夹持20mm方柄，不夹压球窝。')
 d.fastener('FW_B',2,20,[6.5,0,-27],-X,'W','ball')
 d.metal('FW_W1','W2',washer([6,0,-27],X,5,2.2,.5),'W','ball')
 d.metal('FW_W2','W2',washer([-6.5,0,-27],X,5,2.2,.5),'W','ball')
 d.metal('FW_N','N2',nut([-8.1,0,-27],X,2,4,1.6),'W','ball')
 for p in d.parts[-4:]:p['bench_only']=True
 coupon=box([0,0,0],[62,28,4])
 for x,diam in [(7,4.15),(20,4.25),(33,4.35)]:coupon-=cyl([x,7,-.1],[x,7,4.1],diam/2)
 coupon-=hexagon([8,20,1],Z,5.8,3.1)+hexagon([25,20,1],Z,7.35,3.1)+box([44,7,-.1],[54.3,17.3,4.1])
 d.print('C3-01','轴孔／普通螺母／方键试配片',coupon,'C',bench=True,role='fixture',note='三孔左至右4.15/4.25/4.35；六角AF5.8、7.35；方孔10.3。不是装配零件。')

def build(h=1):
 d=Design();hinge(d,h);roll(d,h);wrist(d,h);fixtures(d);return d

def transforms(mode='arm',q=0,r=0,w=0,v=0):
 Hrot=rot(Y,-q)
 if mode=='arm':
  return {'H':{'fixed':np.eye(4),'rotor':Hrot},'R':{'fixed':Hrot@a.T([0,0,-R_OFFSET]),'rotor':Hrot@a.T([0,0,-R_OFFSET])@rot(Z,90-r)},'W':{'fixed':Hrot@rot(Z,90-r)@a.T([0,0,-FORE]),'ball':Hrot@rot(Z,90-r)@a.T([0,0,-FORE])@rot(X,v)@rot(Y,w)}}
 return {'H':{'fixed':a.T([-65,0,0]),'rotor':a.T([-65,0,0])@Hrot},'R':{'fixed':a.T([0,0,0]),'rotor':rot(Z,90-r)},'W':{'fixed':a.T([65,0,0]),'ball':a.T([65,0,0])@rot(X,v)@rot(Y,w)}}

def export():
 d=build();OUT.mkdir(parents=True,exist_ok=True);(OUT/'stl_print').mkdir(exist_ok=True);(OUT/'verification').mkdir(exist_ok=True)
 rows=[];arrays={};bom={};scene=trimesh.Scene();F=transforms()
 for i,p in enumerate(d.parts):
  m=mesh(p['s']);arrays['v'+str(i)]=m.vertices;arrays['f'+str(i)]=m.faces
  row={k:v for k,v in p.items() if k not in ['s','orientation']}
  row.update(index=i,color=COLORS[p['role']],bounds_mm=m.bounds.tolist(),volume_mm3=float(m.volume),components=len(p['s'].decompose()),watertight=bool(m.is_watertight))
  if p['printable']:
   pm=m.copy();M=p['orientation'].copy();pm.apply_transform(M);shift=-pm.bounds[0];M[:3,3]+=shift;pm.apply_translation(shift)
   file=OUT/'stl_print'/(p['id']+'.stl');pm.export(file)
   row.update(stl=file.relative_to(OUT).as_posix(),stl_sha256=sha(file),print_matrix=M.tolist(),print_bounds_mm=pm.bounds.tolist(),print_qty=1,stl_roundtrip_watertight=trimesh.load(file,process=True).is_watertight)
  if p['sku']:
   b=bom.setdefault(p['sku'],dict(sku=p['sku'],spec=p['spec'],qty=0,stations=set()));b['qty']+=1;b['stations'].add(p['station'])
  if not p['bench_only']:
   display=m.copy();display.apply_transform(F[p['station']][p['frame']]);display.apply_scale(.001);display.units='m';display.visual.vertex_colors=np.r_[np.array(COLORS[p['role']])*255,255].astype(np.uint8)
   scene.add_geometry(display,node_name=p['id'],geom_name=p['id'])
  rows.append(row)
 np.savez_compressed(OUT/'assembly_meshes.npz',**arrays);scene.export(OUT/'O24C_T3_installed_forearm.glb')
 put(OUT/'assembly.json',dict(revision=REVISION,units='mm',parts=rows,upperarm_mm=UPPER,forearm_mm=FORE,roll_face_offset_mm=R_OFFSET,reference_height_mm=560,fullbody_height_verified=False,scope='Elbow H + forearm roll R + wrist W. Same meshes in installed arm and independent specimens. Shoulder/clavicle retention not qualified.'))
 put(OUT/'verification/geometry.json',dict(passed=all(r['watertight'] and r['components']==1 and r.get('stl_roundtrip_watertight',True) for r in rows),geometry_sha256=sha(OUT/'assembly_meshes.npz'),parts=len(rows),printed=sum(r['printable'] for r in rows),bad=[r['id'] for r in rows if not r['watertight'] or r['components']!=1]))
 put(OUT/'verification/fastener_stacks.json',dict(rows=d.stacks,scope='Nominal envelope only; actual purchased screws and spring force must be checked.'))
 br=[dict(**{k:v for k,v in b.items() if k!='stations'},stations=sorted(b['stations'])) for b in bom.values()];put(OUT/'BOM.json',br)
 with (OUT/'BOM.csv').open('w',encoding='utf-8-sig',newline='') as f:
  wri=csv.writer(f);wri.writerow(['编号','规格','三样件共用一套数量','所在样件']);wri.writerows([b['sku'],b['spec'],b['qty'],','.join(b['stations'])] for b in br)
 print(json.dumps(dict(parts=len(rows),prints=sum(r['printable'] for r in rows),bad=[r['id'] for r in rows if r['components']!=1]),ensure_ascii=False),flush=True)

if __name__=='__main__':export()
