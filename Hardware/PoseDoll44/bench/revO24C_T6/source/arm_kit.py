"""T6: closed captive nylocs, metal compression stack, unchanged O22 screws.
Rigid geometry checks do not certify prevailing torque or printed strength.
"""
from pathlib import Path
import importlib.util,sys,json
sys.dont_write_bytecode=True
HERE=Path(__file__).resolve().parent;H=HERE.parents[1];ROOT=H.parents[1]
sp=importlib.util.spec_from_file_location('baseline_t4',H/'cad/revO24C_T4/arm_kit.py');t4=importlib.util.module_from_spec(sp);sp.loader.exec_module(t4)
for k in ('a','md','np','trimesh','box','cyl','tube','beam','rot','moved','hexagon','nut','screw','washer','mesh','sha','put','X','Y','Z','COLORS','FORE','UPPER','R_OFFSET','PROFILE','SPECS','Design','transforms'):
 globals()[k]=getattr(t4,k)
t3=t4.t3
sys.path.insert(0,str(HERE))
OUT=H/'bench/revO24C_T6';REVISION='O24C-T6'
SPECS['NL3']='M3×0.5 尼龙锁紧螺母 DIN 985：对边5.32～5.50，总高3.70～4.00 mm；金属六角段高≥2.15；非全尼龙螺母'
PORTS=[]
HEX_AF=5.65
NUT_FACE=-2.1;NUT_HEIGHT=4.0;NUT_HEX_HEIGHT=2.4

def nyloc(af=5.5,height=4.,hexheight=2.4):
 # Nylon is shown in its assembled shape; no helical/interference simulation.
 return (hexagon([0,NUT_FACE-hexheight,0],Y,af,hexheight)
         +cyl([0,NUT_FACE-height,0],[0,NUT_FACE-hexheight+.01,0],min(2.65,af/2))) - cyl([0,NUT_FACE-height-.1,0],[0,NUT_FACE+.1,0],1.52)

def access_seat(M,clock=0,af=HEX_AF):
 # All six flats are closed. No side loading slot crosses the hex socket.
 hx=moved(hexagon([0,-6.35,0],Y,af,4.30),rot(Y,clock))
 chambers=cyl([0,-2.,0],[0,.08,0],4.65)+cyl([0,-2.35,0],[0,-1.94,0],3.65)
 return moved(hx+chambers+cyl([0,-8.2,0],[0,.1,0],1.7),M)

def build(h=1):
 d=t4.build(h)
 removed={'H3-01','H3-02','R3-01','R3-02','W4-02','W4-03','C3-01'}
 d.parts=[p for p in d.parts if p['id'] not in removed and not p['id'].startswith(('HC','RC','WC'))]
 P={p['id']:p for p in d.parts};PORTS.clear();d.stacks=[]
 def seat(M,pre,body_id,s,clock=0):
  s-=access_seat(M,clock)
  n=P[pre+'N'];n.update(s=moved(nyloc(),M@rot(Y,clock)),sku='NL3',spec=SPECS['NL3'],label=SPECS['NL3'],note='从外侧轴向装入完整六角窝；尼龙圈先进入深处，金属承压面朝外侧垫圈。先对齐六角，不能靠螺钉强拉入窝。')
  rw=P[pre+'RW'];rw.update(s=moved(washer([0,-2.1,0],Y,7,3.2,.5),M),sku='W3',spec=SPECS['W3'],label=SPECS['W3'],note='T6薄反力垫7×3.2×0.5，贴锁母金属端；不是T5的9×3.2×0.8。两面均贴金属，平整去毛刺。')
  for j,u in [(1,-1.6),(2,-.8)]:
   d.metal(pre+'K'+str(j),'W4',moved(washer([0,u,0],Y,9,4.3,.8),M),n['station'],n['frame'],note='T6新增内置金属间隔垫，第'+str(j)+'片；9×4.3×0.8。两片共1.6 mm，不能漏装或用孔3.2的垫圈代替；两面均贴金属。')
  P[pre+'F1']['note']='原12×4.3×1内摩擦垫，光滑面朝3mm运动耳；背面由两片内置M4垫圈支承，固定座外环负责定位。'
  P[pre+'AX']['note']='复用Φ4×8 / M3×6肩钉；3mm内六角先旋入金属螺纹，再克服尼龙阻力。锁母由完整六角窝止转。调节后核对尖端穿过尼龙圈、有完整牙露出，且肩部未顶住小孔垫圈。'
  out=M[:3,:3]@Y
  PORTS.append(dict(prefix=pre,M=M.tolist(),entry=out.tolist(),body=body_id,clock_deg=clock,hex_AF=HEX_AF,nut_face_mm=NUT_FACE,nut_cavity_end_mm=-6.35,nut_height_max_mm=4.,min_hex_capture_mm=1.9,washer_chamber_diameter_mm=9.3,mode='axial_closed_hex'))
  head=5.8+h;tip=head-14;shoulder_end=head-8
  d.stacks.append(dict(id=pre,kind='shoulder',pair_height=h,thread_pitch=.5,nut_height=4.,nut_face_mm=NUT_FACE,
      shoulder_to_reaction_washer_gap_mm=shoulder_end-(-1.6),tip_past_nylon_mm=(NUT_FACE-4)-tip,
      full_metal_thread_engagement_mm=2.4,metal_spacer_height_mm=1.6,reaction_washer_thickness_mm=.5,
      pressure_path='head / W4 / A8 opposed pair / FW4 / 3mm rotor / FW4 / W4 + W4 / W3(.5) / captive NL3; printed socket locates and reacts torque, no thin plastic axial pressure wall'))
  return s
 s=box([-5,-5,18],[5,5,42])
 for side in [-1,1]:
  s+=cyl([0,side*3,0],[0,side*10,0],8.2)
  s+=beam([0,side*6.5,0],[0,side*6.5,17],3.5)+beam([0,side*6.5,17],[0,0,22],3.5)
 s-=box([2.9,-5.1,17.5],[6,5.1,25.5])
 for side,pre in [(-1,'HL_'),(1,'HR_')]:
  M=a.T([0,side*10,0])@(np.eye(4) if side==1 else rot(X,180));s=seat(M,pre,'H6-01',s,30)
 d.print('H6-01','T6一体肘固定叉／完整六角锁母窝',s,'H',orientation=rot(X,90),note='替换H5-01；两侧轴向先装NL3、薄M3反力垫及两片M4间隔垫，再装原H3-03。侧面不再有开放螺母滑槽。')
 s=box([-6.5,-10.9,0],[6.5,10.9,8])+box([-5,-5,7],[5,5,16])
 s-=cyl([-12,0,12.5],[12,0,12.5],1.7);s=seat(rot(X,-90),'R_','R6-01',s)
 d.print('R6-01','T6一体前臂旋转固定芯／完整六角锁母窝',s,'R',note='替换R5-01，轴向入口在Z=0端面；原R3-03/04及10mm方键接口不变。')
 s=box([-7.8,-7.8,-8.2],[7.8,7.8,8.2])+cyl([-10,0,0],[10,0,0],8.2)+cyl([0,-10,0],[0,10,0],8.2)
 for axis in ['Y','X']:
  for sign in [-1,1]:
   vec=sign*(Y if axis=='Y' else X)
   M=a.T(vec*10)@(np.eye(4) if axis=='Y' and sign==1 else rot(X,180) if axis=='Y' else rot(Z,-90*sign))
   s=seat(M,'W'+axis+('M_' if sign<0 else 'P_'),'W6-01',s)
 d.print('W6-01','T6一体腕十字芯／四个完整六角锁母窝',s,'W','flex',rot(X,180),note='替换W5-01；从±X/±Y四个轴向入口装内部五金，再装两只原运动叉。±Z面连续，腕中心和外廓不变。')
 s=box([0,0,0],[62,28,10])
 for x,af in [(8,HEX_AF),(24,5.75)]:s-=access_seat(a.T([x,16,10])@rot(X,90),af=af)
 s-=access_seat(a.T([43,0,5])@rot(X,180))
 s+=tube([55,21,9.9],[55,21,18],2.55,1.7)
 for x,num in [(8,1),(24,2),(43,3)]:
  for k in range(num):s-=cyl([x+(k-(num-1)/2)*2,25,9],[x+(k-(num-1)/2)*2,25,10.1],.55)
 d.print('C6-01','T6锁母窝试配片／一体环形推杆',s,'C',bench=True,role='fixture',note='1点：AF5.65竖孔；2点：AF5.75对照竖孔；3点：AF5.65横孔。正式件均AF5.65。圆柱端面仅推金属螺母端，中央孔避让螺纹。试片不参与关节装配。')
 return d

def export():
 f=t3.export;f.__globals__.update(build=build,OUT=OUT,REVISION=REVISION,transforms=transforms);f()
 (OUT/'O24C_T3_installed_forearm.glb').replace(OUT/'O24C_T6_installed_forearm.glb')
 data=json.loads((OUT/'assembly.json').read_text('utf8'));data.update(wrist_axis_order='Ry(flex) @ Rx(deviation)',wrist_axes_at_W=True,physical_tests_passed=False,user_feedback=dict(date='2026-10-25',component='T5 H',friction='Initially adequate, loses resistance after about ten cycles',issue='User saw screw tip retract and reappear after retightening; strong evidence of back-out with ordinary nuts and no locking',T6_tested=False),design_changes='Closed axial hex pockets, seven NL3, fourteen additional W4 spacer washers, seven W3 .5 replacing RW3 .8. Existing shoulder screws and moving parts retained.')
 put(OUT/'assembly.json',data);put(OUT/'access_ports.json',PORTS)

if __name__=='__main__':export()

