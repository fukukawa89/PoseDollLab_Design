"""O24C-T5: one-piece reaction housings, unchanged tested H friction stack.

The user's H friction approval is qualitative; T5 itself is not physically tested.
Side-loading metal seats replace load-bearing assembly seams, not simply fuse
closed cavities. Old designs remain read-only.
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
OUT=H/'bench/revO24C_T5';REVISION='O24C-T5'
PORTS=[]

def access_seat(M,entry,clock=0):
 """Axis/u locations unchanged. Hex flats form a sliding, anti-turn channel.
 Reaction washer retains the original 2.8mm continuous axial reaction wall.
 No assembly seam cuts that wall; the entry opens only BEHIND it.
 """
 entry=np.array(entry,float)
 nh=moved(hexagon([0,-6.3,0],Y,5.8,2.8),M@rot(Y,clock))
 # Side-loaded FDM slots need more clearance than the old open split pockets.
 # Enlarge only behind the bearing surface: .8 washer in a 1.1 mm slot.
 wh=moved(cyl([0,-3.9,0],[0,-2.8,0],4.65),M)
 bores=moved(cyl([0,-8.1,0],[0,.1,0],1.7)+cyl([0,-1.9,0],[0,.1,0],2.125),M)
 return bores+md.Manifold.batch_hull([nh,nh.translate(entry*16)])+md.Manifold.batch_hull([wh,wh.translate(entry*16)])

def build(h=1):
 d=t4.build(h)
 removed={'H3-01','H3-02','R3-01','R3-02','W4-02','W4-03'}
 d.parts=[p for p in d.parts if p['id'] not in removed and not p['id'].startswith(('HC','RC','WC'))]
 P={p['id']:p for p in d.parts};PORTS.clear()
 def seat(M,entry,prefix,body,clock=0):
  body-=access_seat(M,entry,clock)
  if clock:P[prefix+'N']['s']=moved(nut([0,-6,0],Y,3,5.5,2.4),M@rot(Y,clock))
  P[prefix+'N']['note']='普通M3，无尼龙圈；从侧向六角导槽装到底，使两平行平面贴合导轨。轴肩螺钉穿入后防止螺母侧向脱出。'
  P[prefix+'RW']['note']='9×3.2×0.8反力垫，从独立的窄入口先装；光滑面朝2.8mm反力壁。不要从轴孔硬塞。'
  PORTS.append(dict(prefix=prefix,M=M.tolist(),entry=np.array(entry).tolist(),body=body_id,clock_deg=clock,sliding_hex_AF=5.8,nut_axial_slot_mm=2.8,washer_slot_width=9.3,washer_axial_slot_mm=1.1,reaction_wall_mm=2.8))
  return body
 # Elbow: ports open towards -X, away from the fork connection and moving ears.
 body_id='H5-01';s=box([-5,-5,18],[5,5,42])
 for side in [-1,1]:
  s+=cyl([0,side*3,0],[0,side*10,0],8.2)
  s+=beam([0,side*6.5,0],[0,side*6.5,17],3.5)+beam([0,side*6.5,17],[0,0,22],3.5)
 s-=box([2.9,-5.1,17.5],[6,5.1,25.5])
 for side,pre in [(-1,'HL_'),(1,'HR_')]:
  M=a.T([0,side*10,0])@(np.eye(4) if side==1 else rot(X,180))
  s=seat(M,-X,pre,s,30)
 d.print('H5-01','一体肘固定叉／侧装反力组件',s,'H',orientation=rot(X,90),note='替代H3-01和H3-02，删除两组M3合模螺钉。负X背面先插反力垫，再插普通M3；不改变H3-03及两侧摩擦堆叠。')
 # Axial roll: widen only the fixed body, not its unchanged 10mm input key.
 # Washer side ligament increases from .35 to 1.85mm nominal.
 body_id='R5-01';s=box([-6.5,-10.9,0],[6.5,10.9,8])+box([-5,-5,7],[5,5,16])
 s-=cyl([-12,0,12.5],[12,0,12.5],1.7)
 s=seat(rot(X,-90),-Y,'R_',s)
 d.print('R5-01','一体前臂旋转固定芯／加厚侧壁',s,'R',note='替代R3-01/02，取消两组M2合模五金。主体宽13mm，输入方键仍10mm；反力垫侧壁名义1.85mm。入口在−Y侧。')
 # Wrist: one solid core with four ports on the -Z face. Keep all axes/ears.
 body_id='W5-01';s=box([-7.8,-7.8,-8.2],[7.8,7.8,8.2])
 s+=cyl([-10,0,0],[10,0,0],8.2)+cyl([0,-10,0],[0,10,0],8.2)
 for axis in ['Y','X']:
  for sign in [-1,1]:
   vec=sign*(Y if axis=='Y' else X)
   M=a.T(vec*10)@(np.eye(4) if axis=='Y' and sign==1 else rot(X,180) if axis=='Y' else rot(Z,-90*sign))
   s=seat(M,-Z,'W'+axis+('M_' if sign<0 else 'P_'),s)
 d.print('W5-01','一体双轴腕十字芯／四组底面装入口',s,'W','flex',rot(X,180),note='替代W4-02/03，取消四组M2×16合模五金。−Z入口面朝上放件；先反力垫后普通M3，转动叉及摩擦堆叠保持T4。打印时完整+Z面朝板。')
 return d

def export():
 f=t3.export;f.__globals__.update(build=build,OUT=OUT,REVISION=REVISION,transforms=transforms);f()
 (OUT/'O24C_T3_installed_forearm.glb').replace(OUT/'O24C_T5_installed_forearm.glb')
 data=json.loads((OUT/'assembly.json').read_text('utf8'));data.update(wrist_axis_order='Ry(flex) @ Rx(deviation)',wrist_axes_at_W=True,physical_tests_passed=False,user_feedback=dict(date='2026-10-25',component='T3/T4 H',friction='User reports adequate and usable',issue='H3-01/02 seam opens under strong tightening and grows during repeated motion',quantitative_torque_measured=False,T5_tested=False))
 put(OUT/'assembly.json',data);put(OUT/'access_ports.json',PORTS)

if __name__=='__main__':export()
