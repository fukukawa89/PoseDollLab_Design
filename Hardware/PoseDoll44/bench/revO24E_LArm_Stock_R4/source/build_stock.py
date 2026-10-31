"""Common-hardware arm trial. Frozen O24E and T6 are read-only inputs."""
from pathlib import Path
import sys,json,copy,math,csv,hashlib
sys.dont_write_bytecode=True
HERE=Path(__file__).resolve().parent;H=HERE.parents[1];OUT=H/'bench/revO24E_LArm_Stock_R4'
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

def oval_loft(keys,segments=64,subdivisions=6):
 """Closed oval sections with zero-slope radius transitions; no imported key holes."""
 keys=sorted(keys);rings=[]
 for a,b in zip(keys[:-1],keys[1:]):
  for u in np.linspace(0,1,subdivisions,endpoint=False):
   h=u*u*(3-2*u);rings.append((a[0]+u*(b[0]-a[0]),a[1]+h*(b[1]-a[1]),a[2]+h*(b[2]-a[2])))
 rings.append(keys[-1]);v=[];f=[]
 for z,rx,ry in rings:
  for t in np.linspace(0,2*np.pi,segments,endpoint=False):v.append([rx*np.cos(t),ry*np.sin(t),z])
 for i in range(len(rings)-1):
  for j in range(segments):
   a=i*segments+j;b=i*segments+(j+1)%segments;c=b+segments;d=a+segments;f.extend([[a,b,c],[a,c,d]])
 bot=len(v);v.append([0,0,rings[0][0]]);top=len(v);v.append([0,0,rings[-1][0]])
 for j in range(segments):f.append([bot,(j+1)%segments,j]);f.append([top,(len(rings)-1)*segments+j,(len(rings)-1)*segments+(j+1)%segments])
 return md.Manifold(md.Mesh64(np.asarray(v),np.asarray(f,dtype=np.uint64)))

def service_cavity():
 return cyl([0,0,-10],[0,0,-1],6.35)+oval_loft([(-22,3.75,3.75),(-10,6.35,6.35)])+cyl([0,0,-65],[0,0,-22],3.75)

def service_window(axis=1):
 # Rounded rectangular side port: washers enter here; surrounding rails close below it.
 r=1.5;x=6.7;z0=-16;z1=-6.3
 cut=box([-x+r,-30,z0],[x-r,30,z1])+box([-x,-30,z0+r],[x,30,z1-r])
 for xx in [-x+r,x-r]:
  for zz in [z0+r,z1-r]:cut+=cyl([xx,-30,zz],[xx,30,zz],r)
 return cut if axis==1 else moved(cut,rot([0,0,1],90))

def roll(d,pre,fixed,out,W,parallel=1):
 """Large standard washer captured between a fixed rear seat and bolted lid.
 The four-disc shoulder pack retains two series groups and stock screw lengths.
 """
 t=2.3-.8*(parallel-1);h=1+.8*(parallel-1)
 body=cyl([0,0,0],[0,0,8],11.5)+oval_loft([(7,11.5,11.5),(16,6.2,6.2)])
 lid=tube([0,0,-2],[0,0,0],11.5,8.2)
 lug_x=20 if pre=='RF' else 16
 for x in [-lug_x,lug_x]:
  body+=box([min(x,0)-3.8,-4.5,0],[max(x,0)+3.8,4.5,8])
  lid+=box([min(x,0)-3.8,-4.5,-6.0],[max(x,0)+3.8,4.5,0])
  # The shallow lip stays outside the rotor core. Lugs lie outside the disc.
  body-=cyl([x,0,-.1],[x,0,8.1],1.7)
  lid-=cyl([x,0,-6.1],[x,0,.1],1.7)+k.hexagon([x,0,-6.1],[0,0,1],5.65,4.5)
  d.metal(pre+f'_lid_bolt_{x}',fixed,moved(k.screw([x,0,8.5],[0,0,-1],3,16),W),'M3x16')
  d.metal(pre+f'_lid_washer_{x}',fixed,moved(k.washer([x,0,8],[0,0,1],7,3.2,.5),W),'W3')
  # Exact T6 NL3 shape turned so nylon is at the free tip.
  n=moved(ts('R_N'),T([x,0,.5])@rot([1,0,0],180))
  d.metal(pre+f'_lid_nut_{x}',fixed,moved(n,W),'NL3',note='压盖专用闭合六角窝；尼龙朝螺钉尖端。')
 body-=roll_cavity()
 # Clear the middle of the thicker lug bars; only the annular lip catches W6L.
 lid-=cyl([0,0,-6.1],[0,0,.1],8.2)
 lid-=tube([0,0,-6.01],[0,0,-2],13.1,0.01)
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
 f=(ts('H6-01')^box([-60,-60,-8.21],[60,60,8.21]))+tube([0,-3.3,0],[0,3.3,0],8.2,1.7)
 # Rebuild the moving yoke without its obsolete square socket, slit or M3 cross-hole.
 r=oval_loft([(-27.7,7,8.2),(-23,7,8.2),(-19,5.5,7)])
 for side in [-1,1]:
  ear=tube([0,side*11,0],[0,side*14,0],8.2,2.125)
  stem=beam([0,side*12.5,-4],[0,side*12.5,-16],3.5)+beam([0,side*12.5,-16],[0,side*6,-23],3.5)
  near=cyl([0,-25,0],[0,25,0],8.6);slab=box([-20,min(side*11,side*14),-30],[20,max(side*11,side*14),15])
  stem=(stem-near)+(stem^near^slab);stem-=cyl([0,-25,0],[0,25,0],6.2);r+=ear+stem
 d.hinges.append(dict(id=pre,fixed_frame=fixed,output_frame=out,M=M.tolist(),source='T6 H6-01 / H3-03; functional ears, sockets and hardware unchanged'))
 return moved(f,M),moved(r,M)

R2=H/'bench/revO24E_LArm_Stock_R3'  # frozen immediate predecessor
SPECS['N3']='M3×0.5 普通六角螺母，AF5.5×2.4 mm；两颗对顶，仅用于压盖'

def holding_pads():
 # Non-load-bearing radial locating pads, 0.06 mm radial nominal interference.
 # Work face stays 0.18 mm below FW4 front; force stays metal/printed-ear as before.
 # The three pads retain the entire inner stack before fork closure.
 pads=[]
 for angle in [30,150,270]:
  pad=box([5.94,-.65,9.25],[7.35,.65,10.55])+box([6.10,-.65,10.55],[7.35,.65,10.82])
  # Lead-in ramps are convex hulls with rounded/relieved ends, not sharp notches in the bone.
  pad=pad.hull()
  pads.append(moved(pad,rot([0,0,1],angle)))
 return union(pads)

def pad_frame(axis):
 axis=np.asarray(axis,float);u=np.eye(3)[np.argmin(abs(axis))];x=np.cross(u,axis);x/=np.linalg.norm(x);y=np.cross(axis,x)
 A=np.eye(4);A[:3,:3]=np.c_[x,y,axis];return A

def build():
 assert sha(R2/'production_meshes.npz')=='131f5773614d53e33adcd16ac34a69802cda4ff049abefa3ada9da397af0b0d9'
 a=load(R2/'production_assembly.json')['parts'];z=np.load(R2/'production_meshes.npz');d=Design();ints=load(R2/'interfaces.json');d.rolls=copy.deepcopy(ints['rolls']);d.hinges=copy.deepcopy(ints['hinges']);rmap={r['id']:r for r in d.rolls}
 for old in a:
  i=str(old['i']);solid=md.Manifold(md.Mesh64(np.array(z[i+'v'],copy=True),np.array(z[i+'f'],dtype=np.uint64,copy=True)))
  p={key:old[key] for key in ['name','frame','role','sku','note','source']};p['s']=solid;p['pn']=old['part_number'].replace('S3-','S4-');p['source_r2_print']=old['part_number'] if old['role']=='structure' else None
  name=p['name']
  if '_lid_' in name:
   r=rmap[name[:2]];W=np.array(r['W']);x=int(name.split('_')[-1]);L=np.linalg.inv(F0[p['frame']])@W
   if '_bolt_' in name:
    p['s']=moved(k.screw([x,0,-1.6],[0,0,1],3,16),L);p['note']='R4反向安装：螺钉头进入原压盖六角窝，螺纹端朝固定座背面；保留M3×16。'
   elif '_nut_' in name:
    p['s']=moved(k.nut([x,0,8.5],[0,0,1],3,5.5,2.4),L);p['sku']='N3';p['note']='压盖第一颗普通M3，背面W3外侧；先轻贴合，再用薄5.5开口扳手保持不转，对顶第二颗。'
  if name in ['SHOULDER_PITCH','UPPER_ARM','KEEP_E-P019']:
   B=np.array(d.hinges[0 if name=='SHOULDER_PITCH' else 1]['M']) if name!='KEEP_E-P019' else F0['l_wrist_flex']
   axes=[[0,-1,0],[0,1,0]] if name!='KEEP_E-P019' else [[0,-1,0],[0,1,0],[-1,0,0],[1,0,0]]
   for ax in axes:p['s']+=moved(holding_pads(),np.linalg.inv(F0[p['frame']])@B@pad_frame(ax))
   p['source_r2_print']=None;p['source']=old['part_number'];p['note']+=' R4：内FW4外围新增3处轻夹持定位筋，托住其后的NL3/W3/W4散件。筋端低于摩擦面0.18 mm，不承担预紧或防脱；装后先做轻翻转不掉片检查。'
  d.parts.append(p)
 for r in d.rolls:
  W=np.array(r['W'])
  for x in [-r['lug_x_mm'],r['lug_x_mm']]:
   name=r['id']+f'_lid_jam_{x}';d.metal(name,r['fixed_frame'],moved(k.nut([x,0,10.9],[0,0,1],3,5.5,2.4),W),'N3',note='第二颗普通M3：保持第一颗不转，与第一颗对顶；不能两颗一起向打印件猛拧。两颗均为正常高度2.4 mm，不用薄螺母。')
   d.parts[-1].update(pn='S4-H'+str(135+len([p for p in d.parts if '_lid_jam_' in p['name']])).zfill(3),source_r2_print=None)
  r['required_parts']+= [r['id']+f'_lid_jam_{x}' for x in [-r['lug_x_mm'],r['lug_x_mm']]]
 return d

def save():
 OUT.mkdir(exist_ok=True);d=build();data=[];z={};prints=[];hardware=[]
 for folder in ['verification','profiles','stl_print','parts_assembly','images','printing','tutorial','preview','source']:(OUT/folder).mkdir(exist_ok=True)
 for i,p in enumerate(d.parts):
  pn=p["pn"]
  v,f=e.base.a.mesh_data(p['s']);m=trimesh.Trimesh(v,f,process=False)
  z[str(i)+'v']=v;z[str(i)+'f']=f
  row={key:val for key,val in p.items() if key!='s'};row.update(i=i,part_number=pn,bounds_mm=m.bounds.tolist(),volume_mm3=m.volume)
  data.append(row)
  r=dict(part_number=pn,feature=p['name'],frame=p['frame'],sku=p['sku'],role=p['role'],spec=SPECS.get(p['sku'],p['note']),notes=p['note'],source=p['source'],quantity=1)
  if p['role']=='structure':
   r['source_r2_print']=p['source_r2_print'];r['components']=len([x for x in p['s'].decompose() if x.volume()>.01]);r['printable']=True;prints.append(r)
  else:hardware.append(r)
 np.savez_compressed(OUT/'production_meshes.npz',**z)
 put(OUT/'production_assembly.json',dict(parts=data,units='mm',revision='O24E_LArm_Stock_R4',physical_tested=False))
 put(OUT/'kit.json',dict(structural_parts=prints,hardware=hardware,custom_metal_count=0,cut_hardware_count=0,physical_tested=False,manufacturing_release=False))
 put(OUT/'profiles/arm_profile.json',PROFILE);put(OUT/'profiles/poses.json',POSES);put(OUT/'interfaces.json',dict(rolls=d.rolls,hinges=d.hinges))
 print('BUILT',len(prints),'printed',len(hardware),'hardware','components',[(r['feature'],r['components']) for r in prints],flush=True)
 return d
if __name__=='__main__':save()
