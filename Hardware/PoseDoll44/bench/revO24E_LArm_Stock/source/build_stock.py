"""Common-hardware arm trial. Frozen O24E and T6 are read-only inputs."""
from pathlib import Path
import sys,json,copy,math,csv,hashlib
sys.dont_write_bytecode=True
HERE=Path(__file__).resolve().parent;H=HERE.parents[1];OUT=H/'bench/revO24E_LArm_Stock'
sys.path.insert(0,str(H/'cad/revO24E'))
import build as e
import numpy as np
import manifold3d as md
import trimesh
T,rot,moved,box,cyl,tube,beam,union=e.T,e.rot,e.moved,e.box,e.cyl,e.tube,e.beam,e.union
sys.path.insert(0,str(H/'cad/revO24C_T1'));import kit as k
load=lambda p:json.loads(p.read_text('utf8'))
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def put(p,v):
 p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(v,ensure_ascii=False,indent=2),encoding='utf8')
SRC=H/'bench/revO24E_LArm_Mech';T6=H/'bench/revO24C_T6'
PROFILE=load(SRC/'profiles/arm_profile.json');POSES=load(SRC/'profiles/poses.json');ROOT='l_clavicle_elevate'
def frames(q=None):
 f={};q=q or {}
 for n in PROFILE['nodes']:
  M=(f[n['parent']] if n['parent'] else np.eye(4))@T(n['offset_mm'])
  if n['axis'] is not None:M=M@rot(n['axis'],q.get(n['id'],0)+n['zero_deg'])
  f[n['id']]=M
 return f
F0=frames();FA=frames(POSES['neutral']['angles'])
TD=load(T6/'assembly.json');TZ=np.load(T6/'assembly_meshes.npz');TP={p['id']:p for p in TD['parts']}
def ts(id):
 i=str(TP[id]['index']);return md.Manifold(md.Mesh64(np.array(TZ['v'+i],copy=True),np.array(TZ['f'+i],dtype=np.uint64,copy=True)))
ED=load(SRC/'production_assembly.json');EZ=np.load(SRC/'production_meshes.npz');EP={p['name']:p for p in ED['parts']}
def es(id):
 i=str(EP[id]['i']);return md.Manifold(md.Mesh64(np.array(EZ[i+'v'],copy=True),np.array(EZ[i+'f'],dtype=np.uint64,copy=True)))
SPECS={r['编号']:r['规格'] for r in csv.DictReader((T6/'BOM.csv').read_text('utf-8-sig').splitlines())}
SPECS.update(W6L='既有大平垫规格（交接记录）：18×6.4×1.5 mm，钢；本版只取1.5厚',M3x16='M3×16 内六角圆柱头螺钉，未切短',M2x18='M2×18 内六角圆柱头螺钉，未切短',NL2='M2×0.4 DIN985，AF4×总高3 mm')

class Design:
 def __init__(self):self.parts=[];self.rolls=[];self.hinges=[]
 def add(self,name,fr,s,role='structure',sku=None,note='',source=None):
  assert not s.is_empty() and str(s.status())=='Error.NoError',name
  self.parts.append(dict(name=name,frame=fr,s=moved(s,np.linalg.inv(F0[fr])),role=role,sku=sku,note=note,source=source))
 def metal(self,name,fr,s,sku,role='metal',note=''):self.add(name,fr,s,role,sku,note)
 def by(self,n):return next(p for p in self.parts if p['name']==n)
 def join(self,name,fr,solids,note=''):self.add(name,fr,union(solids),note=note)

def roll_cavity():
 return cyl([0,0,-.1],[0,0,1.6],9.15)+cyl([0,0,1.45],[0,0,2.35],4.65)+cyl([0,0,2.2],[0,0,2.9],3.65)+k.hexagon([0,0,2.7],[0,0,1],5.65,4.4)+cyl([0,0,7],[0,0,17],1.7)

def roll(d,pre,fixed,out,W,parallel=1):
 """Large standard washer captured between a fixed rear seat and bolted lid.
 The four-disc shoulder pack retains two series groups and stock screw lengths.
 """
 t=2.3-.8*(parallel-1);h=1+.8*(parallel-1)
 body=cyl([0,0,0],[0,0,8],11.5)+box([-5,-5,7],[5,5,16])
 lid=tube([0,0,-2],[0,0,0],11.5,8.2)
 lug_x=20 if pre=='RF' else 16
 for x in [-lug_x,lug_x]:
  body+=box([min(x,0)-3.8,-4.5,0],[max(x,0)+3.8,4.5,8])
  lid+=box([min(x,0)-3.8,-4.5,-4.8],[max(x,0)+3.8,4.5,0])
  # The shallow lip stays outside the rotor core. Lugs lie outside the disc.
  body-=cyl([x,0,-.1],[x,0,8.1],1.7)
  lid-=cyl([x,0,-5],[x,0,.1],1.7)+k.hexagon([x,0,-4.9],[0,0,1],5.65,4.5)
  d.metal(pre+f'_lid_bolt_{x}',fixed,moved(k.screw([x,0,8.5],[0,0,-1],3,16),W),'M3x16')
  d.metal(pre+f'_lid_washer_{x}',fixed,moved(k.washer([x,0,8],[0,0,1],7,3.2,.5),W),'W3')
  # Exact T6 NL3 shape turned so nylon is at the free tip.
  n=moved(ts('R_N'),T([x,0,1.7])@rot([1,0,0],180))
  d.metal(pre+f'_lid_nut_{x}',fixed,moved(n,W),'NL3',note='压盖专用闭合六角窝；尼龙朝螺钉尖端。')
 body-=roll_cavity()
 # Clear the middle of the thicker lug bars; only the annular lip catches W6L.
 lid-=cyl([0,0,-5],[0,0,.1],8.2)
 lid-=tube([0,0,-4.81],[0,0,-2],13.1,0.01)
 d.add(pre+'_keeper',fixed,moved(lid,W),note='先装入W6L及内部金属，再装本压盖；两颗M3×16/NL3机械固定。与转子留径向和轴向间隙。')
 for old,new,dz,sku in [('R_N','N',.7,'NL3'),('R_RW','RW',.7,'W3'),('R_K1','BACK_W4',.7,'W4'),('R_F1','F1',0,'FW4'),('R_F2','F2',3-t,'FW4'),('R_HW','HW',.7,'W4'),('R_AX','AX',.7,'AX4')]:
  d.metal(pre+'_'+new,fixed,moved(ts(old).translate([0,0,dz]),W),sku,TP[old]['role'])
 d.metal(pre+'_ANCHOR',fixed,moved(k.washer([0,0,0],[0,0,1],18,6.4,1.5),W),'W6L',note='闭合挡止垫：外圆被座与压盖两面捕获；后有W4补强，预紧不穿过打印薄壁。')
 spec=dict(od=8.,id=4.2,t=.4)
 ztop=-(2+t)
 for group in range(2):
  for layer in range(parallel):
   solid=e.disc(spec,.5,flip=bool(group)).translate([0,0,-(.5+.4*(parallel-1))*group-.4*layer-.5])
   # Construct from the bottom upwards, then place exactly between F2 and HW.
   local=e.disc(spec,.5,flip=bool(group)).translate([0,0,ztop-h+group*(.5+.4*(parallel-1))+.4*layer])
   d.metal(pre+f'_A8_{group+1}_{layer+1}',fixed,moved(local,W),'A8','spring',note=f'第{group+1}组第{layer+1}片；同组并联，两组相对串联。')
 core=tube([0,0,-(1+t)],[0,0,-1],8,2.125)
 web=tube([0,0,-6],[0,0,-2.4],12.5,2.125)
 web-=tube([0,0,-(1+t)+.1],[0,0,0],13,8)
 rotor=core+web
 d.rolls.append(dict(id=pre,fixed_frame=fixed,output_frame=out,W=W.tolist(),lug_x_mm=lug_x,rotor_thickness_mm=t,parallel=parallel,series=2,pair_height_mm=h,anchor=pre+'_ANCHOR',keeper=pre+'_keeper',axle=pre+'_AX',nut=pre+'_N',required_parts=[p['name'] for p in d.parts if p['name'].startswith(pre+'_')]))
 return moved(body,W),moved(rotor,W)

def hinge(d,pre,fixed,out,M,trim=True):
 for old in TP:
  if old.startswith(('HL_','HR_')):
   p=TP[old];d.metal(pre+'_'+old,fixed,moved(ts(old),M),p['sku'],p['role'],p['note'])
 f=ts('H6-01')
 if trim:f=f^box([-60,-60,-20],[60,60,18])
 r=ts('H3-03')+box([-5.6,-5.6,-26],[5.6,5.6,-20.2])
 d.hinges.append(dict(id=pre,fixed_frame=fixed,output_frame=out,M=M.tolist(),source='T6 H6-01 / H3-03; functional ears, sockets and hardware unchanged'))
 return moved(f,M),moved(r,M)

def build():
 d=Design()
 WP=F0['l_shoulder_flex']@T([0,-26,0])@rot([1,0,0],90)
 WU=F0['l_shoulder_abduct']@T([0,0,-36])@rot([0,0,1],90)
 WF=F0['l_elbow_flex']@T([0,0,-36])@rot([0,0,1],90)
 pfix,prot=roll(d,'RP',ROOT,'l_shoulder_flex',WP,2)
 ufix,urot=roll(d,'RU','l_shoulder_abduct','l_upperarm_roll',WU)
 ffix,frot=roll(d,'RF','l_elbow_flex','l_forearm_roll',WF)
 MS=F0['l_shoulder_flex']@rot([0,0,1],-90)
 ME=F0['l_elbow_flex']@rot([0,0,1],180)
 hs,hr=hinge(d,'HS','l_shoulder_flex','l_shoulder_abduct',MS)
 he,er=hinge(d,'HE','l_upperarm_roll','l_elbow_flex',ME)
 def point(M,v):return (M@np.r_[v,1])[:3]
 grip=box([-8,-10,-9],[8,6,9])
 d.join('ROOT',ROOT,[pfix,grip]+[beam([x,3,0],point(WP,[x,0,7]),3.8) for x in [-6,6]],'固定输入握持座；仅单臂试装，不包含锁骨两轴。')
 d.join('SHOULDER_PITCH','l_shoulder_flex',[prot,hs]+[beam(point(WP,[s*8,0,-6.5]),point(MS,[0,s*6.5,14.4]),3.5) for s in [-1,1]])
 d.join('SHOULDER_ABDUCT','l_shoulder_abduct',[hr,ufix], 'T6 H转动叉与新的RU固定芯连续连接。')
 d.join('UPPER_ARM','l_upperarm_roll',[urot,he]+[beam(point(WU,[s*9,0,-6.5]),point(ME,[0,-s*6.5,17]),3.5) for s in [-1,1]],'双肋围出中心工具口；轴线与骨长沿用O24E。')
 d.join('ELBOW_OUTPUT','l_elbow_flex',[er,ffix])
 MW=F0['l_wrist_flex'];wfix=moved(ts('W4-01')^box([-50,-50,-20],[50,50,22]),MW)
 d.join('FOREARM','l_forearm_roll',[frot,wfix]+[beam(point(WF,[s*8,0,-6.5]),point(MW,[0,s*12.5,20]),3.5) for s in [-1,1]],'保留T6腕叉摩擦耳，改为连续骨杆；中心留R调节工具口。')
 for W,fn,on,t in [(WP,'ROOT','SHOULDER_PITCH',1.5),(WU,'SHOULDER_ABDUCT','UPPER_ARM',2.3),(WF,'ELBOW_OUTPUT','FOREARM',2.3)]:
  p=d.by(fn);p['s']-=moved(roll_cavity(),np.linalg.inv(F0[p['frame']])@W)
  p=d.by(on);p['s']-=moved(cyl([0,0,-32],[0,0,-(1+t)],6.35),np.linalg.inv(F0[p['frame']])@W)
  p['s']-=moved(cyl([0,0,-65],[0,0,-6],3.75),np.linalg.inv(F0[p['frame']])@W)
 for pn in ['E-P017','E-P018','E-P019']:
  p=EP[pn];s=es(pn)
  if pn=='E-P017':
   s+=k.hexagon([-6.5,0,-27],[1,0,0],7,.6)
   s-=cyl([-18,0,-27],[18,0,-27],1.15)+cyl([6,0,-27],[18,0,-27],2.65)+k.hexagon([-18,0,-27],[1,0,0],4.3,11.5)
  d.add('KEEP_'+pn,p['frame'],moved(s,F0[p['frame']]),source=pn,note='掌部外形不变，重开锁母、垫片和穿钉让位；须重打。' if pn=='E-P017' else '复用O24E完整打印件，尺寸不变。')
 inv=load(SRC/'kit.json');selected={r['part_number']:r for r in inv['hardware'] if r['feature'].startswith(('l_E_W','l_palm_'))}
 for pn,r in selected.items():
  p=EP[pn];sku=r['sku'];sku={'M2x18_ISO4762':'M2x18','M2_WASHER_5x2.2x0.5':'W2','M2_NYLOC':'NL2'}.get(sku,sku)
  s=es(pn)
  if r['feature']=='l_palm_screw':
   s=k.screw([7,0,-27],[-1,0,0],2,20);sku='M2x20'
  if r['feature']=='l_palm_w1':s=k.washer([6.5,0,-27],[1,0,0],5,2.2,.5)
  note=SPECS[sku] if sku=='M2x20' else r['spec']
  if r['feature'].startswith('l_palm_w'):note='两片5×2.2×0.5平垫均放在掌部螺钉头下，不再左右各一片。'
  d.metal('KEEP_'+pn,p['frame'],moved(s,F0[p['frame']]),sku,p['role'],note)
 return d

def save():
 OUT.mkdir(exist_ok=True);d=build();data=[];z={};prints=[];hardware=[]
 for folder in ['verification','profiles','stl_print','parts_assembly','images','printing','tutorial','preview','source']:(OUT/folder).mkdir(exist_ok=True)
 for i,p in enumerate(d.parts):
  pn=f'S-{"P" if p["role"]=="structure" else "H"}{(len(prints)+1 if p["role"]=="structure" else len(hardware)+1):03d}'
  v,f=e.base.a.mesh_data(p['s']);m=trimesh.Trimesh(v,f,process=False)
  z[str(i)+'v']=v;z[str(i)+'f']=f
  row={key:val for key,val in p.items() if key!='s'};row.update(i=i,part_number=pn,bounds_mm=m.bounds.tolist(),volume_mm3=m.volume)
  data.append(row)
  r=dict(part_number=pn,feature=p['name'],frame=p['frame'],sku=p['sku'],role=p['role'],spec=SPECS.get(p['sku'],p['note']),notes=p['note'],source=p['source'],quantity=1)
  if p['role']=='structure':
   r['components']=len([x for x in p['s'].decompose() if x.volume()>.01]);r['printable']=True;prints.append(r)
  else:hardware.append(r)
 np.savez_compressed(OUT/'production_meshes.npz',**z)
 put(OUT/'production_assembly.json',dict(parts=data,units='mm',revision='O24E_LArm_Stock',physical_tested=False))
 put(OUT/'kit.json',dict(structural_parts=prints,hardware=hardware,custom_metal_count=0,cut_hardware_count=0,physical_tested=False,manufacturing_release=False))
 put(OUT/'profiles/arm_profile.json',PROFILE);put(OUT/'profiles/poses.json',POSES);put(OUT/'interfaces.json',dict(rolls=d.rolls,hinges=d.hinges))
 print('BUILT',len(prints),'printed',len(hardware),'hardware','components',[(r['feature'],r['components']) for r in prints],flush=True)
 return d
if __name__=='__main__':save()
