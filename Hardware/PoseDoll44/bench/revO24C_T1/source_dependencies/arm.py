"""O24A left arm: geometry-first design in mm, degrees, RH X-forward/Y-left/Z-up.

Run with the repository .venv. All writes are confined to bench/revO24.
This is a digital layout prototype, not a manufacturing release.
"""
from pathlib import Path
import sys, json, math, hashlib, csv
import numpy as np
import manifold3d as md
import trimesh
from scipy.spatial.transform import Rotation

HERE = Path(__file__).resolve().parent
H = HERE.parents[1]
REPO = H.parents[1]
OUT = H/'bench/revO24'
sys.path.insert(0, str(H/'cad/revE'))
import character_reference as ue

def put(p, value):
    p=Path(p); p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(json.dumps(value,ensure_ascii=False,indent=2,default=lambda x:x.tolist() if isinstance(x,np.ndarray) else float(x),allow_nan=False)+'\n',encoding='utf8')

def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def unit(v):
    v=np.asarray(v,float); return v/np.linalg.norm(v)
def T(p=(0,0,0),R=None):
    t=np.eye(4); t[:3,3]=p
    if R is not None:t[:3,:3]=R
    return t
def rot(axis,deg):return T(R=Rotation.from_rotvec(unit(axis)*math.radians(deg)).as_matrix())
def moved(s,t):return s.transform(np.asarray(t)[:3])
def union(ss):return md.Manifold.batch_boolean(list(ss),md.OpType.Add)
def box(lo,hi):return md.Manifold.cube(np.asarray(hi)-lo).translate(lo)
def sphere(p,r):return md.Manifold.sphere(r,24).translate(p)
def cylinder(a,b,r):
    a=np.array(a,float);b=np.array(b,float);z=unit(b-a)
    x=unit(np.cross(np.eye(3)[np.argmin(abs(z))],z));y=np.cross(z,x)
    return md.Manifold.cylinder(np.linalg.norm(b-a),r,circular_segments=40).transform(np.c_[x,y,z,a])
def tube(a,b,ro,ri):
    a=np.array(a,float);b=np.array(b,float);d=unit(b-a)
    return cylinder(a,b,ro)-cylinder(a-d*.02,b+d*.02,ri)
def beam(a,b,r):return cylinder(a,b,r)+sphere(a,r)+sphere(b,r)
def ring(axis,t0,t1,ro,ri):return tube(np.array(axis)*t0,np.array(axis)*t1,ro,ri)
def arc(axis_u,axis_v,radius,a0,a1,thick):
    angles=np.radians(np.linspace(a0,a1,max(5,int(abs(a1-a0)/8)+1)))
    pp=[radius*(np.cos(a)*np.array(axis_u)+np.sin(a)*np.array(axis_v)) for a in angles]
    return union(beam(a,b,thick) for a,b in zip(pp[:-1],pp[1:]))

AXES=[
 ('clavicle_protract','锁骨前伸 / 后收',[-20,20],[0,0,-1]),
 ('clavicle_elevate','锁骨抬高 / 下压',[-10,25],[1,0,0]),
 ('shoulder_flex','肩前举 / 后伸',[-45,165],[0,-1,0]),
 ('shoulder_abduct','肩外展',[-20,165],[1,0,0]),
 ('upperarm_roll','上臂内外旋',[-75,85],[0,0,-1]),
 ('elbow_flex','肘屈曲',[0,145],[0,-1,0]),
 ('forearm_roll','前臂旋前 / 旋后',[-85,80],[0,0,-1]),
 ('wrist_flex','腕屈曲 / 背伸',[-65,70],[0,1,0]),
 ('wrist_deviation','腕尺偏 / 桡偏',[-20,30],[1,0,0]),
]
COLORS={'structure':[.65,.79,.76],'rotor':[.91,.64,.27],'metal':[.48,.54,.61],
        'bearing':[.25,.31,.37],'friction':[.35,.21,.12],'pcb':[.05,.42,.29],
        'magnet':[.74,.23,.25],'connector':[.13,.16,.20],'reference':[.81,.82,.83]}

def reference():
    # Regenerate N pose from the original asset, never from O22/O23 profiles.
    c=ue.reference_character('quinn'); k=560/c['height_mm']
    pts={n:p*k for n,p in c['points'].items()}
    height=np.ptp(c['vertices_mm'][:,2])*k
    meta=dict(asset=c['probe']['mesh_asset'],engine=c['probe']['engine'],export_utc=c['probe']['utc'],
        neutral_height_mm=float(height),uniform_scale=ue.SCALE*k,
        coordinates='RH X forward, Y left, Z up; mm; column vectors',
        source_mesh_axes='[UE_Y, UE_X, UE_Z]',floor_shift_mm=c['shift_mm']*k,
        source_files={str((H/'reference/ue58'/f).relative_to(REPO)):sha(H/'reference/ue58'/f) for f in ['quinn_mesh_probe.json','quinn_geometry.json']},
        neutralization_source_sha256=sha(H/'cad/revE/character_reference.py'),forearm_zero_clocking_deg=-90,
        points_mm=pts,full_doll_envelope_budget_mm=580,strict_height_limit_mm=600,
        note='560 mm is the regenerated N-pose reference surface. 580 mm is a future full-doll packaging limit, not a measured complete O24 assembly.')
    # Keep source rotations so the target can be reconstructed independently of the mechanism.
    meta['bone_reference']=[b for b in c['probe']['mesh_reference'] if b['name'] in ['spine_05','clavicle_l','upperarm_l','lowerarm_l','hand_l','middle_01_l']]
    meta['neutral_rotations_RH']={n:ue.SWAP@c['neutral'][c['index'][n]][:3,:3]@ue.SWAP.T for n in ['clavicle_l','upperarm_l','lowerarm_l','hand_l']}
    return meta,c,k

def profile(ref):
    P=ref['points_mm'];C=np.array(P['clavicle_l']);S=np.array(P['upperarm_l']);E=np.array(P['lowerarm_l']);W=np.array(P['hand_l'])
    upper=float(np.linalg.norm(E-S));fore=float(np.linalg.norm(W-E))
    return dict(schema='POSEDOLL-O24-ARM/1',revision='O24A',reference=ref['asset'],
      neutral_height_mm=560,root=C,clavicle_vector=S-C,upperarm_mm=upper,forearm_mm=fore,
      hand_mm=float(np.linalg.norm(np.array(P['middle_01_l'])-W)),
      forearm_zero_clocking_deg=-90,
      axes=[dict(id=a,label=b,limits_deg=c,axis=d) for a,b,c,d in AXES],
      channel_count=9,physical_dof=9,protocol_compatibility='Design-stage 9-channel arm. Existing O22 46-channel firmware is not directly compatible.',
      pose_source='anatomical N pose; shoulder flex then abduct then humeral roll',
      units='mm/degree',manufacturing_release=False)

def frames(p,q=None):
    q=q or {}; a=lambda n:q.get(n,0.)
    F={'chest':T(p['root'])}
    F['collar_z']=F['chest']@rot([0,0,-1],a('clavicle_protract'))
    F['collar']=F['collar_z']@rot([1,0,0],a('clavicle_elevate'))
    F['shoulder_base']=F['collar']@T(p['clavicle_vector'])
    F['shoulder_pitch']=F['shoulder_base']@rot([0,-1,0],a('shoulder_flex'))
    F['shoulder_swing']=F['shoulder_pitch']@rot([1,0,0],a('shoulder_abduct'))
    F['upper']=F['shoulder_swing']@rot([0,0,-1],a('upperarm_roll'))
    F['elbow_base']=F['upper']@T([0,0,-p['upperarm_mm']])
    F['elbow']=F['elbow_base']@rot([0,-1,0],a('elbow_flex'))
    F['fore']=F['elbow']@rot([0,0,-1],p['forearm_zero_clocking_deg']+a('forearm_roll'))
    F['wrist_base']=F['fore']@T([0,0,-p['forearm_mm']])
    F['wrist_flex']=F['wrist_base']@rot([0,1,0],a('wrist_flex'))
    F['hand']=F['wrist_flex']@rot([1,0,0],a('wrist_deviation'))
    return F

class Assembly:
    def __init__(self):self.parts=[]
    def add(self,name,frame,s,role='structure',notes='',interfaces=()):
        if s.is_empty() or str(s.status())!='Error.NoError':raise ValueError(name+' invalid solid')
        self.parts.append(dict(name=name,frame=frame,s=s,role=role,notes=notes,interfaces=list(interfaces)))
    def sensor(self,name,parent,child,axis,at,board=12):
        """Magnets face outwards. PCB envelope includes IC and solder; connector is separate."""
        z=unit(axis);x=unit(np.cross(np.eye(3)[np.argmin(abs(z))],z));y=np.cross(z,x)
        M=np.c_[x,y,z,z*at]; K=np.eye(4);K[:3]=M
        self.add(name+'_magnet',child,moved(cylinder([0,0,0],[0,0,2.5],3),K),'magnet','D6x2.5 diametrically magnetized; axial airgap nominal 1.5 mm')
        self.add(name+'_pcb',parent,moved(box([-board/2,-5,4],[board/2,5,6]),K),'pcb','12x10 PCB with 2 mm populated envelope; no board redesign claimed')
        self.add(name+'_connector',parent,moved(box([-3,5,4],[3,9,7]),K),'connector','Reserved 6x4x3 plug envelope; vendor confirmation pending')
        # Open-backed holder; sensor can be removed axially, no glue on PCB.
        holder=box([-board/2-1.8,-6.8,3.5],[board/2+1.8,6.8,7.5])-box([-board/2-.25,-5.25,3.4],[board/2+.25,5.25,8])
        for side in [-1,1]:
            if name=='wrist_deviation':holder=holder+box([-1.2,min(side*5.5,side*6.7),-10],[1.2,max(side*5.5,side*6.7),4.2])
            else:holder=holder+beam([side*(5 if name=='wrist_flex' else 7),0,-5],[side*7,0,4],1.0)
        self.add(name+'_sensor_holder',parent,moved(holder,K),'structure','Cassette envelope; M2 cover retention and wiring route pending detail')

    def pivot(self,name,parent,child,axis,r=7,half=5,bearing_od=9,bore=4):
        """Two bearings, rotor hub, two friction faces, shaft and retained sensor.
        Bearing seats and paired metal washers are explicit; thread forms simplified.
        """
        a=np.array(axis,float);br=bearing_od/2;bw=4 if bore==4 else 3
        ear=14 if bore==4 else half+3.5+bw/2
        for sign in (-1,1):
            x=sign*ear
            self.add(f'{name}_ear_{sign}',parent,ring(a,x-bw/2-.7,x+bw/2+.7,r,br+.08),'structure',interfaces=[name])
            self.add(f'{name}_bearing_{sign}',parent,ring(a,x-bw/2,x+bw/2,br,bore/2+.03),'bearing',f'{int(bore)}x{int(bearing_od)}x{bw} mm nominal; bore tessellation allowance 0.03 mm',interfaces=[name])
            lo=sign*half;hi=sign*(half+.5)
            self.add(f'{name}_friction_{sign}',parent,ring(a,min(lo,hi),max(lo,hi),6,bore/2+.15),'friction','OD12 friction washer, 0.5 mm; coefficient must be measured',interfaces=[name])
            lo=sign*(half+.5);hi=sign*(half+1.5)
            self.add(f'{name}_pressure_{sign}',parent,ring(a,min(lo,hi),max(lo,hi),6,bore/2+.15),'metal','Metal pressure plate; preload path to be bench tested',interfaces=[name])
        self.add(name+'_hub',child,ring(a,-half,half,r-.6,bore/2+.08),'rotor',interfaces=[name])
        span=ear+bw/2+1
        self.add(name+'_shaft',child,cylinder(-a*span,a*span,bore/2),'metal','Precision shoulder shaft; thread and fits schematic',interfaces=[name])
        self.add(name+'_head',child,ring(a,span,span+2,bore,0.01),'metal',interfaces=[name])
        self.add(name+'_nut',child,ring(a,-span-2.5,-span,bore,bore/2-.1),'metal',interfaces=[name])
        self.sensor(name,parent,child,-a,span+3)
        return ear,span

def build(p):
    A=Assembly();L=p['upperarm_mm'];F=p['forearm_mm'];cv=np.array(p['clavicle_vector'])
    # Clavicle root uses staggered, single-sided journals. The mating right root is not part of this deliverable.
    A.add('chest_mount','chest',box([10,-13,19],[26,7,23])-cylinder([18,-9,18],[18,-9,24],1.7))
    A.add('clavicle_z_housing','chest',ring([0,0,1],15,25,6.6,4.58))
    A.add('clavicle_z_support','chest',beam([0,0,20],[16,0,21],3)-cylinder([0,0,14],[0,0,26],4.58))
    for z in [17,23]:A.add('clavicle_z_bearing_'+str(z),'chest',ring([0,0,1],z-2,z+2,4.5,2.03),'bearing')
    A.add('clavicle_z_shaft','collar_z',cylinder([0,0,5],[0,0,26],2),'metal')
    A.add('clavicle_z_rotor','collar_z',box([-2.5,-2.5,5],[16,2.5,8.5])-cylinder([7.4,0,0],[9.6,0,0],6.3),'rotor')
    A.add('clavicle_z_brake','chest',ring([0,0,1],14.5,15,6,2.15),'friction')
    A.add('clavicle_z_flange','collar_z',ring([0,0,1],13,14.5,6,2.08),'rotor')
    A.add('clavicle_elevation_housing','collar_z',ring([1,0,0],10,20,6.6,4.58))
    for x in [12,18]:A.add('clavicle_x_bearing_'+str(x),'collar_z',ring([1,0,0],x-2,x+2,4.5,2.03),'bearing')
    A.add('clavicle_x_shaft','collar',cylinder([0,0,0],[22,0,0],2),'metal')
    A.add('clavicle_x_brake','collar_z',ring([1,0,0],9.5,10,6,2.15),'friction')
    A.add('clavicle_x_flange','collar',ring([1,0,0],8,9.5,6,2.08),'rotor')
    A.add('clavicle_x_output','collar',box([-2,-2,-2],[2,7,2]),'rotor')
    A.sensor('clavicle_z','chest','collar_z',[0,0,1],27)
    A.sensor('clavicle_x','collar_z','collar',[1,0,0],24)
    # Straight clavicle segment follows the exact UE C-S line; local shoulder journal is centred on S.
    for side in [-1,1]:
        aa=cv*.13;bb=cv*.24+np.array([side*11,0,0]);cc=cv+np.array([side*7,-24,0])
        A.add('clavicle_link_'+str(side),'collar',beam(aa,bb,2.2)+beam(bb,cc,2.2))
    A.add('shoulder_pitch_housing','shoulder_base',ring([0,1,0],-28,-19,7.2,4.58))
    for y in [-26,-21]:A.add('shoulder_pitch_bearing_'+str(y),'shoulder_base',ring([0,1,0],y-2,y+2,4.5,2.03),'bearing')
    A.add('shoulder_pitch_shaft','shoulder_pitch',cylinder([0,-31,0],[0,-16,0],2),'metal')
    A.add('shoulder_pitch_flange','shoulder_pitch',ring([0,1,0],-18.5,-16,7,2.08),'rotor')
    A.add('shoulder_pitch_friction','shoulder_base',ring([0,1,0],-19,-18.5,6,2.15),'friction')
    A.sensor('shoulder_pitch','shoulder_base','shoulder_pitch',[0,-1,0],32)
    # Open medial half-ring keeps the forward/outward arm swing unobstructed.
    A.add('shoulder_open_yoke','shoulder_pitch',(arc([1,0,0],[0,1,0],16,180,360,3.0)-cylinder([-23,0,0],[23,0,0],4.58))^box([-30,-18.45,-10],[30,10,10]))
    for x in [-16,16]:
        A.add('shoulder_swing_ear_'+str(x),'shoulder_pitch',ring([1,0,0],x-2.6,x+2.6,6.4,4.58))
        A.add('shoulder_swing_bearing_'+str(x),'shoulder_pitch',ring([1,0,0],x-2,x+2,4.5,2.03),'bearing')
        A.add('shoulder_swing_stub_'+str(x),'shoulder_swing',cylinder([np.sign(x)*8,0,0],[np.sign(x)*20,0,0],2),'metal')
        A.add('shoulder_swing_washer_'+str(x),'shoulder_pitch',ring([1,0,0],np.sign(x)*12.5,np.sign(x)*13 if x>0 else -12.5,6,2.15) if x>0 else ring([1,0,0],-13,-12.5,6,2.15),'friction')
    A.add('shoulder_cross_head','shoulder_swing',tube([-12.5,0,0],[12.5,0,0],4,2.08),'rotor')
    A.sensor('shoulder_swing','shoulder_pitch','shoulder_swing',[-1,0,0],21)
    axial(A,'humeral','shoulder_swing','upper',12,34)
    A.add('upperarm_centered_tube','upper',tube([0,0,-35],[0,0,-L+22],5.5,3),'structure','Axis equals S-E bone line; 6 mm internal cable corridor')
    # Elbow: symmetrical cheeks, no translated offset of the hinge centre.
    ear,span=A.pivot('elbow','elbow_base','elbow',[0,1,0])
    for y in [-ear,ear]:A.add('elbow_fork_'+str(y),'elbow_base',(beam([0,0,22],[0,y,22],2.6)+beam([0,y,22],[0,y,0],2.6))-cylinder([0,-20,0],[0,20,0],4.58))
    axial(A,'forearm','elbow','fore',28,48)
    A.add('forearm_centered_tube','fore',tube([0,0,-49],[0,0,-F+28],6,3),'structure','Coaxial E-W; carries radial bearings and an independent friction brake')
    # Wrist universal: both axes at W; separate stub pins avoid crossing solid shafts.
    for y in [-10,10]:
        A.add('wrist_input_fork_'+str(y),'wrist_base',(beam([0,0,28],[0,y,28],2.2)+beam([0,y,28],[0,y,0],2.2))-cylinder([0,-15,0],[0,15,0],3.58))
        A.add('wrist_flex_ear_'+str(y),'wrist_base',ring([0,1,0],y-2,y+2,5.4,3.58))
        A.add('wrist_flex_bearing_'+str(y),'wrist_base',ring([0,1,0],y-1.5,y+1.5,3.5,1.53),'bearing')
        A.add('wrist_flex_stub_'+str(y),'wrist_flex',cylinder([0,np.sign(y)*4,0],[0,np.sign(y)*13,0],1.5),'metal')
        lo,hi=(7,7.5) if y>0 else (-7.5,-7)
        A.add('wrist_flex_friction_'+str(y),'wrist_base',ring([0,1,0],lo,hi,4.8,1.65),'friction','OD9.6 wrist friction disc; separate radial support')
    A.add('wrist_cross','wrist_flex',box([-5,-7,-3.5],[5,7,3.5]),'rotor')
    for x in [-9,9]:
        A.add('wrist_output_fork_'+str(x),'hand',(beam([x,0,0],[x,0,-16],2.2)+beam([x,0,-16],[0,0,-16],2.2))-cylinder([-15,0,0],[15,0,0],3.58))
        A.add('wrist_dev_ear_'+str(x),'hand',ring([1,0,0],x-2,x+2,5.4,3.58))
        A.add('wrist_dev_bearing_'+str(x),'hand',ring([1,0,0],x-1.5,x+1.5,3.5,1.53),'bearing')
        A.add('wrist_dev_stub_'+str(x),'wrist_flex',cylinder([np.sign(x)*4,0,0],[np.sign(x)*12,0,0],1.5),'metal')
        lo,hi=(6.2,6.7) if x>0 else (-6.7,-6.2)
        A.add('wrist_dev_friction_'+str(x),'hand',ring([1,0,0],lo,hi,4.8,1.65),'friction','OD9.6 wrist friction disc; preload closure pending')
    A.sensor('wrist_flex','wrist_base','wrist_flex',[0,-1,0],14)
    A.sensor('wrist_deviation','wrist_flex','hand',[1,0,0],14)
    A.add('hand_palm','hand',box([-3.5,-11,-45],[3.5,11,-18])+beam([0,0,-16],[0,0,-21],3.5),'structure','Rigid hand handle; finger articulation outside the arm scope')
    return A

def axial(A,name,parent,child,z0,z1):
    # Annular support surrounds the exact bone axis. Magnet is on the proximal end.
    axis=[0,0,-1]
    A.add(name+'_housing',parent,ring(axis,z0,z1,8.8,6.1),'structure','Split annular housing reserved for two 6x12x4 bearings')
    for side in [-1,1]:
        if name=='forearm':s=beam([0,side*2.5,-5.5],[0,side*8.5,-15],1.5)+beam([0,side*8.5,-15],[0,side*8.5,-z0-2],1.5)
        else:s=beam([side*8,0,-2],[side*8,0,-z0-2],2.6)
        A.add(name+'_stem_'+str(side),parent,s)
    for z in [z0+3,z1-3]:A.add(name+'_bearing_'+str(z),parent,ring(axis,z-2,z+2,6,3.03),'bearing','MR126ZZ 6x12x4 nominal; bore tessellation allowance 0.03 mm')
    A.add(name+'_shaft',child,tube([0,0,-z0+2],[0,0,-z1-2],3,1.5),'metal','6 mm hollow journal; wire cannot pass through the sensing magnet')
    A.add(name+'_rotor_flange',child,ring(axis,z1,z1+2,7.8,3.08),'rotor')
    A.add(name+'_brake',parent,ring(axis,z1-.5,z1,7.5,3.15),'friction','Brake separate from bearing radial support')
    A.sensor(name,parent,child,[0,0,1],-z0+4)

def poses():
    return {
      'neutral':('自然垂臂',{}),
      'forward':('向前伸手',dict(shoulder_flex=90)),
      'side':('侧平举',dict(shoulder_abduct=90)),
      'overhead_front':('向上举手',dict(shoulder_flex=160,clavicle_elevate=10)),
      'overhead_side':('侧向举高手',dict(shoulder_abduct=155,clavicle_elevate=15)),
      'back':('后伸手臂',dict(shoulder_flex=-40)),
      'elbow_max':('屈肘145度',dict(elbow_flex=145)),
      'carry':('屈肘托物',dict(shoulder_flex=20,elbow_flex=90,forearm_roll=-85)),
      'drink':('手靠近口部',dict(clavicle_protract=5,clavicle_elevate=10,shoulder_flex=81.634,shoulder_abduct=25.221,upperarm_roll=17.154,elbow_flex=131.907,forearm_roll=-56.777,wrist_flex=15.293,wrist_deviation=11.125)),
      'head':('手靠近头侧',dict(clavicle_protract=5,clavicle_elevate=10,shoulder_flex=88.496,shoulder_abduct=21.571,upperarm_roll=-2.308,elbow_flex=131.846,forearm_roll=-15.999,wrist_flex=21.283,wrist_deviation=-10.529)),
      'pronate':('旋前',dict(elbow_flex=90,forearm_roll=80)),
      'supinate':('旋后',dict(elbow_flex=90,forearm_roll=-85)),
      'wrist_flex':('腕屈曲',dict(elbow_flex=90,wrist_flex=70)),
      'wrist_extend':('腕背伸',dict(elbow_flex=90,wrist_flex=-65)),
      'radial':('腕桡偏',dict(elbow_flex=90,wrist_deviation=-20)),
      'ulnar':('腕尺偏',dict(elbow_flex=90,wrist_deviation=30)),
      'shrug':('抬肩',dict(clavicle_elevate=25)),
      'reach':('前伸肩带',dict(clavicle_protract=20,shoulder_flex=65,elbow_flex=20)),
    }

def mesh_data(s):
    m=s.to_mesh64();return np.asarray(m.vert_properties)[:,:3],np.asarray(m.tri_verts)

def export(p,ref,A,c,k):
    (OUT/'stl_layout').mkdir(parents=True,exist_ok=True)
    wanted={v['name']+'.stl' for v in A.parts if v['role'] in ['structure','rotor']}
    for old in (OUT/'stl_layout').glob('*.stl'):
        if old.name not in wanted:old.unlink()  # Only obsolete generated O24 layout exports.
    put(OUT/'reference/target_quinn.json',ref);put(OUT/'profiles/arm_profile.json',p)
    put(OUT/'profiles/poses.json',{name:dict(label=label,angles=q) for name,(label,q) in poses().items()})
    put(OUT/'profiles/pose_frames.json',{name:frames(p,q) for name,(_,q) in poses().items()})
    F=frames(p);data=[];arrays={};world=[];geometry=[]
    for i,part in enumerate(A.parts):
        v,f=mesh_data(part['s']);name=part['name']; token=part['frame'];role=part['role']
        arrays[str(i)+'v']=v;arrays[str(i)+'f']=f
        m=trimesh.Trimesh(v,f,process=False)
        data.append(dict(i=i,name=name,frame=token,role=role,color=COLORS[role],notes=part['notes'],interfaces=part['interfaces'],volume_mm3=float(part['s'].volume()),bounds_mm=m.bounds.tolist()))
        geometry.append(dict(name=name,watertight=bool(m.is_watertight),positive_volume=bool(m.volume>0),components=len(part['s'].decompose())))
        if role in ['structure','rotor']:m.export(OUT/'stl_layout'/f'{name}.stl')
        mw=m.copy();mw.apply_transform(F[token]);world.append(mw)
    np.savez_compressed(OUT/'assembly_meshes.npz',**arrays)
    trimesh.Scene({part['name']:mesh for part,mesh in zip(A.parts,world)}).export(OUT/'O24A_left_arm.glb')
    put(OUT/'assembly.json',dict(revision='O24A',manufacturing_release=False,parts=data,neutral_frames=F))
    put(OUT/'verification/mesh_integrity.json',dict(parts=geometry,all_watertight=all(d['watertight'] for d in geometry)))
    # Reference skin stays separately identifiable and is never classified as hardware.
    verts=c['vertices_mm']*k
    np.savez_compressed(OUT/'reference/ue_neutral_surface.npz',v=verts,f=np.array(c['geometry']['triangles']))
    with (OUT/'BOM_layout.csv').open('w',encoding='utf-8-sig',newline='') as f:
        w=csv.writer(f);w.writerow(['part','qty','category','frame','note'])
        for d in data:w.writerow([d['name'],1,d['role'],d['frame'],d['notes']])
    print(json.dumps(dict(parts=len(data),upperarm_mm=p['upperarm_mm'],forearm_mm=p['forearm_mm'],height_mm=ref['neutral_height_mm']),ensure_ascii=False))

def main():
    ref,c,k=reference();p=profile(ref);A=build(p);export(p,ref,A,c,k)
if __name__=='__main__':main()
