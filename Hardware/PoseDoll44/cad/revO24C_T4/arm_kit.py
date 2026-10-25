"""O24C-T4: intersecting two-hinge wrist, with unchanged T3 elbow/roll.

Millimetres. The test wrist IS the installed wrist. No force or wear result is
inferred from nominal CAD. Each pair of O22 stacks adjusts only one axis.
"""
from pathlib import Path
import sys, importlib.util, json, csv
sys.dont_write_bytecode=True
HERE=Path(__file__).resolve().parent; H=HERE.parents[1]; ROOT=H.parents[1]
sp=importlib.util.spec_from_file_location('baseline_t3_arm',H/'cad/revO24C_T3/arm_kit.py')
t3=importlib.util.module_from_spec(sp);sp.loader.exec_module(t3)
for k in ('a','md','np','trimesh','box','cyl','tube','beam','rot','moved','hexagon','nut','screw','washer','mesh','sha','put','X','Y','Z','COLORS','FORE','UPPER','R_OFFSET','PROFILE','SPECS','Design'):
 globals()[k]=getattr(t3,k)
sys.path.insert(0,str(HERE))
OUT=H/'bench/revO24C_T4';REVISION='O24C-T4'
SEAT=10.0

def wrist(d,h=1):
 # All four screws terminate outside the central axis intersection. Four
 # ordinary nuts and reaction washers are inserted at the Z=0 split plane.
 core=box([-7.8,-7.8,-8.2],[7.8,7.8,8.2])
 core+=cyl([-10,0,0],[10,0,0],8.2)+cyl([0,-10,0],[0,10,0],8.2)
 for axis in ['Y','X']:
  for sign in [-1,1]:
   vec=sign*(Y if axis=='Y' else X)
   M=a.T(vec*SEAT)@(np.eye(4) if axis=='Y' and sign==1 else rot(X,180) if axis=='Y' else rot(Z,-90*sign))
   core-=t3.seat_cut(M)
   start=len(d.parts);t3.stack(d,'W'+axis+('M_' if sign<0 else 'P_'),'W',M,h)
   for p in d.parts[start:]:p['frame']='flex'
 for x in [-5,5]:
  for y in [-5,5]:
   pre=f'WC{x}_{y}'
   core-=cyl([x,y,-9],[x,y,9],1.15)+hexagon([x,y,-8.3],Z,4.35,3.7)
   d.fastener(pre+'B',2,16,[x,y,8.7],-Z,'W','flex')
   d.metal(pre+'W','W2',washer([x,y,8.2],Z,5,2.2,.5),'W','flex',note='光滑面朝十字芯顶面（−Z）。')
   d.metal(pre+'N','N2',nut([x,y,-6.2],Z,2,4,1.6),'W','flex',note='普通M2，无塑料圈；从−Z面深槽装入到底，不能悬在槽口。')
 for sign,n in [(-1,'02'),(1,'03')]:
  s=core^box([-25,-25,-9 if sign<0 else 0],[25,25,0 if sign<0 else 9])
  d.print('W4-'+n,'十字芯 '+('下半' if sign<0 else '上半'),s,'W','flex',np.eye(4) if sign>0 else rot(X,180),note='Z=0合模面朝打印板。四颗普通M3及四片9×3.2×0.8反力垫先放进下半槽，再合上；反力壁厚2.8mm。')
 # Proximal fork has no central shaft. Its real R square interface stays at
 # Z=25, with the same 80.496305 mm E-W separation as T3.
 # 2.8mm below the M3 cross-hole, rather than a fragile 1.1mm lower lip.
 fork=box([-8.2,-8.2,20.5],[8.2,8.2,29.8])
 for sign in [-1,1]:
  ear=cyl([0,sign*11,0],[0,sign*14,0],8.2)-cyl([0,sign*10.9,0],[0,sign*14.1,0],2.125)
  stem=beam([0,sign*12.5,4],[0,sign*12.5,20],2.8)+beam([0,sign*12.5,20],[0,sign*5.5,25],2.8)
  near=cyl([0,-22,0],[0,22,0],8.6)
  slab=box([-20,min(sign*11,sign*14),-10],[20,max(sign*11,sign*14),15])
  stem=(stem-near)+(stem^near^slab)
  stem-=cyl([0,-22,0],[0,22,0],6.2)
  fork+=ear+stem
 fork-=box([-5.15,-5.15,20],[5.15,5.15,29.9])+box([-.4,-8.3,20.4],[.4,-5.1,29.9])
 fork-=cyl([-15,0,25],[15,0,25],1.7)+hexagon([-8.3,0,25],X,5.8,2.8)
 for y in [-8.5,8.5]:fork-=cyl([0,y,27.9],[0,y,30.1],2.15)
 d.print('W4-01','前臂侧屈伸叉／T3方键接口',fork,'W',orientation=rot(X,90),note='两侧转动耳厚3mm，耳轴为Y。绿色内外摩擦垫的光滑面均朝耳；上端方孔接原R3-04或F3-M。')
 # Distal fork rotates around the cross-core X axis, after Y flexion.
 output=box([-3,-3,-31],[3,3,-20])
 for sign in [-1,1]:
  ear=cyl([sign*11,0,0],[sign*14,0,0],8.2)-cyl([sign*10.9,0,0],[sign*14.1,0,0],2.125)
  stem=beam([sign*12.5,0,-4],[sign*12.5,0,-17],2.8)+beam([sign*12.5,0,-17],[0,0,-21],2.8)
  near=cyl([-22,0,0],[22,0,0],8.6)
  slab=box([min(sign*11,sign*14),-20,-20],[max(sign*11,sign*14),20,10])
  stem=(stem-near)+(stem^near^slab)
  stem-=cyl([-22,0,0],[22,0,0],6.2)
  output+=ear+stem
 # Keep the old palm seating surface free of the fork-root fillet.
 output=(output^box([-30,-30,-21.8],[30,30,20]))+box([-3,-3,-31],[3,3,-21.7])
 output-=cyl([-8,0,-27],[8,0,-27],1.15)
 d.print('W4-04','手掌侧偏摆叉／6mm掌柄方键',output,'W','hand',rot(Y,90),role='rotor',note='两侧3mm摩擦耳绕X轴；末端6mm方键接原W3-09或F3-W。')
 # Exact unchanged palm and fixture geometries, plus existing interface metal.
 oldw=Design();t3.wrist(oldw)
 for p in oldw.parts:
  if p['id']=='W3-09' or p['id'].startswith(('WPALM_','W_R_')):
   p=p.copy()
   if p['frame']=='ball':p['frame']='hand'
   if p['id']=='W3-09':p['note']='沿用T3同一STL；6.4mm方孔接W4-04，普通M2＋0.5mm垫圈＋M2×14固定。'
   d.parts.append(p)

def build(h=1):
 d=Design();t3.hinge(d,h);t3.roll(d,h);wrist(d,h)
 n=len(d.parts);t3.fixtures(d)
 for p in d.parts[n:]:
  if p['frame']=='ball':p['frame']='hand'
 return d

def transforms(mode='arm',q=0,r=0,w=0,v=0):
 hr=rot(Y,-q);rr=rot(Z,90-r);flex=rot(Y,w);hand=flex@rot(X,v)
 if mode=='arm':
  wf=hr@rr@a.T([0,0,-FORE])
  return {'H':{'fixed':np.eye(4),'rotor':hr},'R':{'fixed':hr@a.T([0,0,-R_OFFSET]),'rotor':hr@a.T([0,0,-R_OFFSET])@rr},'W':{'fixed':wf,'flex':wf@flex,'hand':wf@hand}}
 wf=a.T([65,0,0])
 return {'H':{'fixed':a.T([-65,0,0]),'rotor':a.T([-65,0,0])@hr},'R':{'fixed':np.eye(4),'rotor':rr},'W':{'fixed':wf,'flex':wf@flex,'hand':wf@hand}}

def export():
 # Reuse the proven serialiser with this module's geometry and transforms.
 f=t3.export
 f.__globals__.update(build=build,OUT=OUT,REVISION=REVISION,transforms=transforms)
 f()
 oldname=OUT/'O24C_T3_installed_forearm.glb';oldname.replace(OUT/'O24C_T4_installed_forearm.glb')
 assembly=json.loads((OUT/'assembly.json').read_text('utf8'))
 assembly.update(wrist_axis_order='Ry(flex) @ Rx(deviation)',wrist_axes_at_W=True,wrist_physical_test_passed=False)
 put(OUT/'assembly.json',assembly)

if __name__=='__main__':export()
