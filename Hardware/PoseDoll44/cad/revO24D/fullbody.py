"""O24D full body, mm / RH X forward Y left Z up; new outputs only.

The C/S1 files are inputs, never export targets. Imported modules' main functions
are not run. Manufacturing release and physical qualification remain false.
"""
from pathlib import Path
import sys, json, math, hashlib, csv, copy
import numpy as np
import manifold3d as md
import trimesh
HERE=Path(__file__).resolve().parent
H=HERE.parents[1]; REPO=H.parents[1]; OUT=H/'bench/revO24D'
sys.path[:0]=[str(H/'cad/revO24C'),str(H/'cad/revO24C_T1'),str(H/'cad/revO24')]
import compact_input as c
import s1_geometry_input as k
sys.path.insert(0,str(HERE))  # D validation helpers must not resolve to old C.
a=c.a
T=a.T; rot=a.rot; moved=a.moved; box=a.box; cyl=a.cylinder; tube=a.tube; beam=a.beam; ring=a.ring; union=a.union
load=lambda p:json.loads(Path(p).read_text('utf-8-sig'))
put=a.put; sha=a.sha
REF=load(H/'bench/revO24C/reference/target_quinn.json')
P={n:np.array(v,float) for n,v in REF['points_mm'].items()}
M=np.diag([1.,-1,1,1])
COLORS={**a.COLORS,'shell':[.72,.79,.76],'harness':[.12,.17,.22],'fixture':[.33,.38,.44]}
NEUTRAL_ANGLES={'l_shoulder_abduct':45.,'r_shoulder_abduct':45.}
INTEGRATION=load(HERE/'integration_layout.json')
HIP_BACK=float(INTEGRATION['hip_back_mm']); HIP_BRIDGE=float(INTEGRATION['hip_bridge_height_mm'])

def freeze():
    file=OUT/'reference/baselines_sha256.json'
    if file.exists():
        saved=load(file)
        failures=[n for n,h in saved.items() if not (H/n).exists() or sha(H/n)!=h]
        if failures:
            # Another live workflow may update its own S1. Preserve the original
            # observation and use the D-local frozen geometry inputs. Never roll back.
            put(OUT/'reference/external_baseline_changes.json',dict(status='OBSERVED_EXTERNAL_CHANGES',changed=[dict(path=n,at_start=saved[n],now=sha(H/n)) for n in failures],note='O24D writes only its new directories. Original start manifest retained. D uses compact_input.py and s1_geometry_input.py snapshots.'))
        return saved
    files=[]
    for sub in ['cad/revO24','cad/revO24B','cad/revO24C','cad/revO24C_T1','bench/revO24','bench/revO24B','bench/revO24C','bench/revO24C_T1','reference/ue58']:
        files += [p for p in (H/sub).rglob('*') if p.is_file() and '__pycache__' not in p.parts and p.suffix not in ['.pyc','.blend1']]
    saved={p.relative_to(H).as_posix():sha(p) for p in files}
    put(file,saved);return saved

def graph():
    nodes=[]; axes=[]
    def node(id,parent,offset=(0,0,0),axis=None,limits=None,label='',zero=0,target=None):
        nodes.append(dict(id=id,parent=parent,offset_mm=np.asarray(offset).tolist(),axis=axis,zero_deg=zero,target_bone=target))
        if axis is not None:axes.append(dict(id=id,label=label,limits_deg=limits,axis=axis,target_bone=target))
    node('pelvis',None,P['pelvis'],target='pelvis')
    for id,par,off,ax,lim,lab,bone in [
      ('lumbar_flex','pelvis',P['spine_02']-P['pelvis'],[0,1,0],[-20,50],'腰前屈 / 后伸','spine_02'),
      ('lumbar_side','lumbar_flex',[0,0,0],[-1,0,0],[-25,25],'腰侧屈','spine_02'),
      ('lumbar_yaw','lumbar_side',[0,0,0],[0,0,1],[-35,35],'腰旋转','spine_02'),
      ('thorax_side','lumbar_yaw',P['spine_04']-P['spine_02'],[-1,0,0],[-15,15],'胸侧屈','spine_04'),
      ('thorax_flex','thorax_side',[0,0,0],[0,1,0],[-15,25],'胸前屈 / 后伸','spine_04'),
      ('neck_side','thorax_flex',P['neck_01']-P['spine_04'],[-1,0,0],[-35,35],'颈侧倾','neck_01'),
      ('neck_flex','neck_side',[0,0,0],[0,1,0],[-45,50],'颈点头 / 仰头','neck_01'),
      ('neck_yaw','neck_flex',[0,0,0],[0,0,1],[-70,70],'颈转头','neck_01')]:node(id,par,off,ax,lim,lab,target=bone)
    node('head','neck_yaw',P['head']-P['neck_01'],target='head')
    for side,sgn in [('l',1),('r',-1)]:
        pref=side+'_';cv=P['upperarm_'+side]-P['clavicle_'+side]
        node(pref+'chest','thorax_flex',P['clavicle_'+side]-P['spine_04'],target='clavicle_'+side)
        armdefs=[('clavicle_protract','chest',[0,0,0],[0,0,-1],[-20,20],'锁骨前伸 / 后收','clavicle_'+side),
          ('clavicle_elevate','clavicle_protract',[0,0,0],[1,0,0],[-10,25],'锁骨抬高 / 下压','clavicle_'+side),
          ('shoulder_flex','clavicle_elevate',cv,[0,-1,0],[-45,165],'肩前举 / 后伸','upperarm_'+side),
          ('shoulder_abduct','shoulder_flex',[0,0,0],[1,0,0],[-20,165],'肩外展','upperarm_'+side),
          ('upperarm_roll','shoulder_abduct',[0,0,0],[0,0,-1],[-75,85],'上臂内外旋','upperarm_'+side),
          ('elbow_flex','upperarm_roll',P['lowerarm_'+side]-P['upperarm_'+side],[0,-1,0],[0,145],'肘屈曲','lowerarm_'+side),
          ('forearm_roll','elbow_flex',[0,0,0],[0,0,-1],[-85,80],'前臂旋转','lowerarm_'+side),
          ('wrist_deviation','forearm_roll',P['hand_'+side]-P['lowerarm_'+side],[1,0,0],[-20,30],'腕偏转','hand_'+side),
          ('wrist_flex','wrist_deviation',[0,0,0],[0,1,0],[-65,70],'腕屈伸','hand_'+side)]
        for id,par,off,ax,lim,lab,bone in armdefs:
            if side=='r':ax=(-M[:3,:3]@np.array(ax)).tolist()
            node(pref+id,pref+par,off,ax,lim,('左' if sgn==1 else '右')+lab,zero=-90 if id=='forearm_roll' else 0,target=bone)
        legdefs=[
          ('hip_abduct','pelvis',P['thigh_'+side]-P['pelvis'],[sgn,0,0],[-20,45],'髋外展 / 内收','thigh_'+side),
          ('hip_flex',pref+'hip_abduct',[0,0,0],[0,-1,0],[-20,120],'髋屈伸','thigh_'+side),
          ('hip_roll',pref+'hip_flex',[0,0,0],[0,0,-sgn],[-35,45],'髋内外旋','thigh_'+side),
          ('knee_flex',pref+'hip_roll',P['calf_'+side]-P['thigh_'+side],[0,1,0],[0,140],'膝屈曲','calf_'+side),
          ('ankle_roll',pref+'knee_flex',P['foot_'+side]-P['calf_'+side],[sgn,0,0],[-20,25],'足内外翻','foot_'+side),
          ('ankle_flex',pref+'ankle_roll',[0,0,0],[0,-1,0],[-40,25],'踝背屈 / 跖屈','foot_'+side),
          ('toe_flex',pref+'ankle_flex',P['ball_'+side]-P['foot_'+side],[0,-1,0],[-10,50],'跖趾伸屈','ball_'+side)]
        for id,par,off,ax,lim,lab,bone in legdefs:node(pref+id,par,off,ax,lim,('左' if sgn==1 else '右')+lab,target=bone)
    return dict(schema='POSEDOLL-O24D/1',revision='O24D',coordinates=REF['coordinates'],nodes=nodes,axes=axes,
        physical_dof=len(axes),single_axis_sensors=36,field_sensors=2,raw_scalar_values=42,
        wrist_order='Rx(deviation) @ Ry(flexion); right side is conjugated by diag(1,-1,1)',
        forearm_zero_clocking_deg=-90,reference_height_mm=560,strict_height_limit_mm=600,
        neutral_pose=dict(name='A',angles_deg=NEUTRAL_ANGLES,shoulder_abduction_deg=45,reference='Anatomical angles remain measured from frozen UE N reference; sensor zero is now calibrated at A.'),
        collision_acceptance='All different moving frames within the same or adjacent anatomical segments; non-adjacent contacts are advisory per user instruction 2026-10-23',
        root_pose='No external support fixture. A neutral uses the two foot soles; stability and ground-reaction loads are checked separately. Root registration is unmeasured, not six extra sensors.',
        S1_physical_pass='ASSUMPTION_FOR_DESIGN_ONLY_EXCLUDING_H04_CONNECTION',
        user_feedback='H04 approx 0.20 x 18 mm weak connecting face reported 2026-10-22. Do not inherit that junction. No S1 physical result invented.',
        manufacturing_release=False,runtime_UE_tested=False)

PROFILE=graph(); NODES={n['id']:n for n in PROFILE['nodes']}
def frames(q=None,profile=None):
    q=q or {}; f={}
    for n in (profile or PROFILE)['nodes']:
        m=(f[n['parent']] if n['parent'] else np.eye(4))@T(n['offset_mm'])
        if n['axis'] is not None:m=m@rot(n['axis'],q.get(n['id'],0)+n['zero_deg'])
        f[n['id']]=m
    return f
F0=frames()
FA=frames(NEUTRAL_ANGLES)

class Design:
    def __init__(self):self.parts=[];self.stacks=[];self.joints=[];self.issues=[];self.hands=[]
    def add(self,name,frame,s,role='structure',note='',sku=None,group=None):
        if s.is_empty() or str(s.status())!='Error.NoError':raise ValueError(name+' invalid')
        self.parts.append(dict(name=name,frame=frame,s=s,role=role,notes=note,sku=sku,group=group or frame))
        return self.parts[-1]
    def local(self,name,frame,s,world_from_local,**kw):return self.add(name,frame,moved(s,np.linalg.inv(F0[frame])@world_from_local),**kw)
    def link(self,name,frame,p0,p1,r=3.0,ri=0):
        s=tube(p0,p1,r,ri) if ri else beam(p0,p1,r)
        return self.local(name,frame,s,np.eye(4),note='Structural link or local joint-clearance fork; only separately measured bone-link sections claim UE centreline alignment.')

def copy_c_arm(D,side):
    """The audited C proximal solids, re-rooted on actual left/right UE points."""
    p=copy.deepcopy(load(H/'bench/revO24C/profiles/arm_profile.json'))
    p['upperarm_mm']=float(np.linalg.norm(P['lowerarm_'+side]-P['upperarm_'+side]))
    p['forearm_mm']=float(np.linalg.norm(P['hand_'+side]-P['lowerarm_'+side]))
    p['clavicle_vector']=((P['upperarm_'+side]-P['clavicle_'+side])*(np.array([1,-1,1]) if side=='r' else 1)).tolist()
    A=c.proximal(p)
    amap={'chest':'chest','collar_z':'clavicle_protract','collar':'clavicle_elevate','shoulder_base':'clavicle_elevate','shoulder_pitch':'shoulder_flex','shoulder_swing':'shoulder_abduct','upper':'upperarm_roll','elbow_base':'upperarm_roll','elbow':'elbow_flex','fore':'forearm_roll'}
    Cf=c.frames(p)
    for v in A.parts:
        if v['name'] in ['chest_mount','clavicle_z_support','clavicle_z_rotor']:continue
        fr=side+'_'+amap[v['frame']]
        src=Cf[v['frame']].copy();src[:3,3]-=np.array(p['root'])
        s=v['s']
        if side=='l' and v['name'].startswith('clavicle_z_') and v['name']!='clavicle_z_rotor':
            s=s.translate([0,0,-87])
            if v['name']=='clavicle_z_shaft':s=cyl([0,0,-79],[0,0,-60],2)
            if any(t in v['name'] for t in ['pcb','connector','sensor_holder']):s=moved(s,rot([0,0,1],90))
        if side=='r':
            if v['name'].startswith('shoulder_pitch_') and any(t in v['name'] for t in ['pcb','connector','sensor_holder']):s=moved(s,rot([0,1,0],270))
            if v['name'].startswith('clavicle_z_'):s=moved(s,np.diag([1.,1,-1,1])).translate([0,0,-10])
            if v['name'].startswith(('clavicle_x_','clavicle_elevation_')) or v['name']=='clavicle_z_rotor':s=moved(s,np.diag([-1.,1,1,1]))
            src=M@src@M;s=moved(s,M)
        global_t=T(P['clavicle_'+side])@src
        D.local(side+'_'+v['name'],fr,s,global_t,role=v['role'],note='O24C geometry inheritance. '+v['notes'],group=side+'_arm')
    if side=='l':
        # Stagger the left vertical journal below the right one along its unchanged
        # Z axis. A rigid rear C-frame transfers rotation without a shaft crossing
        # the neighbouring bearing or the neck; the effective C centre is unchanged.
        layout=load(HERE/'clavicle_route.json');route=layout['points']
        s=union(beam(x,y,layout['radius_mm']) for x,y in zip(route[:-1],route[1:]))
        s-=cyl([6,0,0],[23,0,0],4.6)
        D.local('l_clavicle_vertical_transfer','l_clavicle_protract',s,T(P['clavicle_l']),note='D8.5 continuous steel rear transfer. Coaxial journal moved along Z, UE centre and X/Z axis lines preserved.')
    else:
        s=beam([-8,0,-18],[-16,0,-12],3.5)+beam([-16,0,-12],[-16,0,-6.5],3.5)
        D.local('r_clavicle_vertical_transfer','r_clavicle_protract',s,T(P['clavicle_r']),note='D7 continuous stepped transfer from coaxial Z output socket into X stator socket.')
    # Use the six matched S1 wrist prints and the actual stock metal interfaces.
    kit=k.Kit();k.wrist(kit)
    W=T(P['hand_'+side],F0[side+'_forearm_roll'][:3,:3])
    keep=lambda n:n not in ['W08','W09'] and not n.startswith(('Wlever_'))
    for v in kit.parts:
        if not keep(v['id']):continue
        fr=side+('_wrist_flex' if v['frame']=='ball' else '_forearm_roll')
        ss=v['s'] if side=='l' else moved(v['s'],M)
        if v['id'] in ['W06','W07']:
            sign=-1 if v['id']=='W06' else 1
            rib=union(beam([xx,sign*16,5.5],[np.sign(xx)*8,sign*13,19],2.2) for xx in [-8.5,8.5])
            for xx in [-8,8]:rib-=cyl([xx,-22,19],[xx,22,19],1.8)
            ss+=rib if side=='l' else moved(rib,M)
        if side=='r':base=T(P['hand_'+side])@M@T(R=F0['l_forearm_roll'][:3,:3])@M
        else:base=W
        D.local(side+'_'+v['id'],fr,ss,base,role=v['role'],note='S1 stock interface retained; '+v['note'],group=side+'_wrist')
    # Compact replacement of the external bench base, keyed palm instead of load lever.
    bridge=box([-12,-8,16],[12,8,26])+cyl([0,0,24],[0,0,29],6)
    for x in [-8,8]:bridge-=cyl([x,-9,19],[x,9,19],1.8)
    bridge-=box([-6.2,-5.2,14],[6.2,5.2,18.3])
    from hand_model import hand
    palm,handinfo=hand(side);D.hands.append(handinfo)
    D.add(side+'_palm',side+'_wrist_flex',palm,role='structure',group=side+'_wrist',note='Compact one-piece palm direction indicator, independent of UE fingers. Recessed palm groove, raised dorsal ridge and thumb silhouette. Continuous 7 mm palm into retained square-key/M2 fixing.')
    extras=[('wrist_bridge',bridge,'structure','forearm_roll'),
      ('wrist_PCB',box([-6,-5,16],[6,5,17]),'pcb','forearm_roll'),
      ('wrist_IC',box([-2.45,-1.5,14.5],[2.45,1.5,16]),'metal','forearm_roll'),
      ('wrist_plug',box([-2,6,16],[2,10,18]),'connector','forearm_roll'),
      ('palm_screw',k.screw([6.5,0,-27],[-1,0,0],2,18),'metal','wrist_flex'),
      ('palm_w0',k.washer([6,0,-27],[1,0,0],5,2.2,.5),'metal','wrist_flex'),
      ('palm_w1',k.washer([-6,0,-27],[-1,0,0],5,2.2,.5),'metal','wrist_flex'),
      ('palm_nut',k.nut([-9.5,0,-27],[1,0,0],2,4,3),'metal','wrist_flex')]
    for name,s,role,fr in extras:D.local(side+'_'+name,side+'_'+fr,s if side=='l' else moved(s,M),W,role=role,note='D compact integration; not a print release',group=side+'_wrist')
    D.stacks.extend(dict(x,instance=side+'_wrist') for x in kit.stacks if not x['id'].startswith('W_lever'))
    D.stacks.append(dict(id=side+'_palm_M2x20_trim18',underhead_to_tip_mm=18,underhead_to_nut_exit_mm=16,protrusion_mm=2,minimum_two_threads_mm=.8))

def hinge(D,name,parent,child,origin,axis,orient=None,bore=4,od=9,friction_od=12,half=5,ear=10.5,back=-1,include_sensor=True):
    """Compact H2 fork: rotating shaft, fixed bearings, two independent brake plates.
    The off-axis M3 tie screws close the force loop around the rotor; the bearings
    stand outboard of the pressure plates and have 0.4 mm axial end play.
    """
    axis=np.asarray(axis,float);axis/=np.linalg.norm(axis)
    x=np.asarray(orient if orient is not None else [1,0,0],float);x-=axis*np.dot(axis,x);x/=np.linalg.norm(x)
    z=np.cross(x,axis); R=np.c_[x,axis,z]; W=T(origin,R)
    ro=friction_od/2;wd=1 if bore==4 else 1.5;outer=half+wd+2
    tie=2 if name=='neck_shoulder_swing' else 3; spacer_ro=2 if tie==2 else 2.75; spacer_ri=1.1 if tie==2 else 1.6
    bolt_arm=ro+(3 if name=='l_elbow' else (6 if name=='lumbar_shoulder_swing' else 5))
    def add(n,s,frame,role='structure',sku=None,note=''):
        return D.local(name+'_'+n,frame,s,W,role=role,sku=sku,note=note,group=name)
    # Plates are actual independent parts. No shaft nut compresses the bearing stack.
    for sign in [-1,1]:
        add('bearing_'+str(sign),tube([0,sign*(ear-2),0],[0,sign*(ear+2),0],od/2,bore/2),parent,'bearing',('684ZZ' if bore==4 else 'MR126ZZ'))
        ringear=tube([0,sign*(ear-2.6),0],[0,sign*(ear+2.6),0],od/2+2.1,od/2+.1)
        add('ear_'+str(sign),ringear,parent)
        add('friction_'+str(sign),k.washer([0,sign*half,0],[0,sign,0],friction_od,bore+.3 if bore==4 else 6.4,wd),parent,'friction',f'FR{bore}_{friction_od}_{wd}')
        webhalf=11.75 if name=='lumbar_shoulder_swing' else (10.2 if tie==2 else 12.5)
        bolt_z=5 if name=='l_elbow' else (5.5 if name=='lumbar_shoulder_swing' else (5.3 if tie==2 else 6))
        return_depth=9 if name=='lumbar_shoulder_swing' else (7 if bore==4 else 11)
        reach=ro+(8 if name=='l_elbow' else 10)
        plate=cyl([0,sign*(half+wd),0],[0,sign*outer,0],ro)+box([back*reach if back<0 else 0,min(sign*(half+wd),sign*outer),-webhalf],[0 if back<0 else reach,max(sign*(half+wd),sign*outer),webhalf])
        for zz in [-webhalf,webhalf-2]:
            if name=='l_elbow' and sign==-1 and zz==webhalf-2:continue
            plate+=box([back*reach if back<0 else 0,min(sign*(outer-2),sign*(outer+return_depth)),zz],[0 if back<0 else reach,max(sign*(outer-2),sign*(outer+return_depth)),zz+2])
        plate-=cyl([0,-outer-1,0],[0,outer+1,0],bore/2+.35)
        bx=back*bolt_arm
        for zz in [-bolt_z,bolt_z]:plate-=cyl([bx,-outer-1,zz],[bx,outer+1,zz],spacer_ri)
        add('pressure_'+str(sign),plate,parent,'metal',sku='CUSTOM_304_CHANNEL_2mm',note='2 mm formed stainless channel, 7 mm returns stiffen the loaded web. Custom bent/drilled sheet, not a catalogue part. Independent preload bypasses bearings.')
        # A fixed fork joins the bearing ears and the pressure frame behind the motion sector.
        add('fork_'+str(sign),beam([back*(ro+9),sign*ear,0],[0,sign*ear,0],2.8)-cyl([0,-ear-4,0],[0,ear+4,0],od/2+.1),parent)
        for zz in [-bolt_z,bolt_z]:
            bx=back*bolt_arm
            boss=tube([bx,sign*(ear-2.5),zz],[bx,sign*(ear+2.5),zz],4,spacer_ro+.05)
            boss+=beam([bx,sign*ear,0],[bx,sign*ear,zz],3)-cyl([bx,sign*(ear-3),zz],[bx,sign*(ear+3),zz],spacer_ro+.05)
            add(f'guide_boss_{sign}_{zz}',boss,parent,note='D8 boss / D5.6 bore captures the steel preload spacer against tangential motion; 1.2 mm radial wall, fused to the full fork.')
            add(f'compression_spacer_{sign}_{zz}',tube([bx,sign*outer,zz],[bx,sign*(ear+3),zz],spacer_ro,spacer_ri),parent,'metal',f'STEEL_TUBE_{2*spacer_ro:g}x{2*spacer_ri:g}_CUT',note='Steel compression path through the printed guide boss; plastic is not in the axial preload stack.')
    insert_ro=4.6 if bore==4 else 5.8
    capth=2. if bore==4 else 3.
    hub_ro=7.5 if 'ankle_shoulder_swing' in name else (7.2 if name in ['lumbar_shoulder_swing','thorax_shoulder_swing'] else ro+.4)
    hexbody=lambda radius,z0,z1:moved(md.Manifold.cylinder(z1-z0,radius,radius,6),T([0,z0,0])@rot([1,0,0],-90))
    hub=cyl([0,-half+capth+.35,0],[0,half-capth-.35,0],hub_ro)-hexbody(insert_ro+.05,-half-1,half+1)
    # Positive torque key: common small steel dowel through the machined shaft.
    pinr=1 if bore==4 else 1.5
    hub-=union(cyl([-ro-1,0,dz],[ro+1,0,dz],pinr+.05) for dz in [-.15,.15])
    add('hub',hub,child,'rotor',note='Continuous hex socket. Captive pin keys the shaft to the metal core; distributed hex faces transfer torque into FDM, without pin holes through the thin outer wall.')
    capkey=3.3 if bore==4 else 4.4
    sleeve=hexbody(insert_ro,-half+capth,half-capth)+hexbody(capkey,-half+.1,half-.1)
    sleeve-=cyl([0,-half,0],[0,half,0],bore/2+.025)+cyl([-ro-1,0,0],[ro+1,0,0],pinr+.025)
    add('compression_sleeve',sleeve,child,'metal',f'CUSTOM_STEEL_SLEEVE_{bore}',note='Axial compression bypasses FDM creep; radial clearance 0.05 mm to printed hub.')
    for sign in [-1,1]:add('rotor_cap_'+str(sign),cyl([0,sign*(half-capth),0],[0,sign*half,0],ro+.4)-hexbody(capkey+.05,-half-1,half+1),child,'metal','CUSTOM_HEX_KEYED_THRUST_CAP',note='Stepped hex key prevents cap slip; axial thrust bears on the larger metal core shoulder, with clearance to FDM.')
    shaft=cyl([0,-ear-4.4,0],[0,ear+4.4,0],bore/2-.01)-cyl([-5,0,0],[5,0,0],pinr+.025)
    for sign in [-1,1]:shaft-=cyl([-5,sign*(ear+3.4),0],[5,sign*(ear+3.4),0],.75)
    add('shaft',shaft,child,'metal',f'D{bore}_cut_drill_{2*ear+8:g}')
    pin_tip=math.sqrt(hub_ro**2-pinr**2)-.05
    add('drive_pin',tube([-pin_tip,0,0],[pin_tip,0,0],pinr,pinr*.55),child,'metal',f'ROLL_PIN_{2*pinr:g}_CUT',note='Cross pin extends into both printed hub walls, with 0.1 mm axial play and tangential slot clearance. The hex takes torque; the pin positively captures the FDM hub without clamping it between the thrust caps.')
    for sign in [-1,1]:
        collar=tube([0,sign*(ear+2.4),0],[0,sign*(ear+4.4),0],bore/2+1.9,bore/2+.05)
        collar-=cyl([-6,sign*(ear+3.4),0],[6,sign*(ear+3.4),0],.75)
        add('retainer_'+str(sign),collar,child,'metal',note='Cross-drilled steel collar, positively retained by D1.5 spring pin; 0.4 mm bearing-end clearance.')
        add('retention_pin_'+str(sign),tube([-bore/2-1.7,sign*(ear+3.4),0],[bore/2+1.7,sign*(ear+3.4),0],.75,.4),child,'metal','ROLL_PIN_1.5_CUT',note='Commercial spring pin cut to collar width, pressed in reamed cross-hole; not a friction-only shaft collar.')
    for zz in [-bolt_z,bolt_z]:
        end=ear+3
        bx=back*bolt_arm;head=-end-.5; nut_start=end+.5;nutheight=3 if tie==2 else 4
        length=math.ceil(2*end+1+nutheight+1)
        stock=next(n for n in [20,25,30,35,40,45,50] if n>=length)
        add('preload_'+str(zz),k.screw([bx,head,zz],[0,1,0],tie,length),parent,'metal',f'M{tie}x{stock}_trim_to_{length}',note='Common stock screw cut and deburred to the stack length; not a claimed catalogue special length')
        add('preload_nut_'+str(zz),k.nut([bx,nut_start,zz],[0,1,0],tie,4 if tie==2 else 5.5,nutheight),parent,'metal',f'M{tie}_NYLOC')
        for sign in [-1,1]:add(f'preload_w_{zz}_{sign}',k.washer([bx,sign*end,zz],[0,sign,0],5 if tie==2 else 7,tie+.2,.5),parent,'metal',f'W{tie}_steel_0.5')
        D.stacks.append(dict(id=name+'_preload_'+str(zz),underhead_to_tip_mm=length,underhead_to_nut_exit_mm=2*end+1+nutheight,protrusion_mm=length-(2*end+1+nutheight),minimum_two_threads_mm=1.0))
    if include_sensor:
        S=a.Assembly();S.sensor(name,parent,child,[0,-1,0],ear+4.6)
        for v in S.parts:add(v['name'].removeprefix(name+'_'),v['s'],v['frame'],v['role'],note='12x10 populated PCB and 6x4x3 connector reservation; board routing pending')
    D.joints.append(dict(id=name,axis_id=child,axis_world=axis,center_mm=np.asarray(origin),bearing_diameter_mm=bore,bearing_outer_mm=od,bearing_span_mm=2*ear,friction_od_mm=friction_od,friction_inner_loaded_radius_mm=bore/2+.15 if bore==4 else 3.2,friction_faces=2,preload_path='Two M3 off-axis screws / formed channel plates / friction discs / steel cap-sleeve-cap; bearings outside closure',bearing_axial_relief_mm=ear-2-outer,cap_thickness_mm=capth,cap_supported_radius_mm=insert_ro,pressure_web_width_mm=2*webhalf,pressure_web_thickness_mm=2,pressure_return_depth_mm=return_depth,pressure_bolt_arm_mm=ro+5,retention='Two cross-drilled collars and D1.5 spring pins; positive rotor spring pin',thread_diameter_mm=3,thread_pitch_mm=.5))
    D.joints[-1].update(thread_diameter_mm=tie,thread_pitch_mm=.4 if tie==2 else .5,cap_supported_radius_mm=insert_ro*math.sqrt(3)/2,output_hex_engagement_mm=2*(half-capth-.35),output_hex_radius_mm=insert_ro,spacer_od_mm=spacer_ro*2,spacer_id_mm=spacer_ri*2,shaft_min_yield_MPa=750,pressure_bolt_arm_mm=bolt_arm,printed_preload_face_recess_mm=.35)
    D.joints[-1].update(hub_capture_pin_diameter_mm=2*pinr,hub_capture_engagement_per_end_mm=pin_tip-insert_ro-.05)
    return W

def hip_pitch_cartridge_seed(D,side,origin):
    """Compact paired journal on the exact hip Y axis, seed for metal closure."""
    sg=1 if side=='l' else -1;pre=side+'_hip_pitch';parent=side+'_hip_abduct';child=side+'_hip_flex'
    W=T(origin,np.c_[[1,0,0],[0,0,-sg],[0,sg,0]])
    D.local(pre+'_housing',parent,ring([0,0,1],-26.8,-16,8.8,6.1),W,group=pre)
    for zz in [-24.4,-18.4]:D.local(pre+'_bearing_'+str(zz),parent,ring([0,0,1],zz-2,zz+2,6,3.03),W,role='bearing',sku='MR126ZZ',group=pre)
    D.local(pre+'_rotor_flange',child,ring([0,0,1],-15.5,-13.5,9,3.05),W,role='rotor',group=pre)
    ss=a.Assembly();ss.sensor(pre,parent,child,[0,0,1],-4)
    for p in ss.parts:D.local(p['name'],p['frame'],p['s'],W,role=p['role'],group=pre)

def gimbal(D,name,parent,first,second,third,origin,flip=1,clock=0,axial_shift=0,short_roll=False):
    """C concentric shoulder modules, also used for hip and aligned trunk hubs.
    Keep dimensions and bearing standards, never scale the mesh.
    """
    p=load(H/'bench/revO24C/profiles/arm_profile.json');A=c.proximal(p)
    mapf={'shoulder_base':parent,'shoulder_pitch':first,'shoulder_swing':second,'upper':third or second}
    names=('shoulder_','humeral_') if third else ('shoulder_',)
    # Canonical C axes: first -Y, second X, roll -Z. Flip Z for upwards trunk.
    B=rot([0,0,1],clock)@np.diag([1,flip,flip,1.]);W=T(origin)@(M if name.startswith('r_') else np.eye(4))@B
    iship=name.endswith('hip');isneck=name=='neck'
    for v in A.parts:
        if not v['name'].startswith(names):continue
        s=v['s']
        if iship:
            n=v['name']
            # Medial paired journal for the hip pitch axis. No bearing protrudes
            # into the neutral wrist corridor. The X line still passes H exactly.
            if n in ['shoulder_swing_ear_16','shoulder_swing_stub_16','shoulder_swing_washer_16']:continue
            if n=='shoulder_swing_ear_-16':s=tube([-25.6,0,0],[-14.4,0,0],6.4,4.6)
            elif n=='shoulder_swing_bearing_-16':s=ring([1,0,0],-25,-21,4.5,2.03)
            elif n=='shoulder_swing_bearing_16':s=ring([1,0,0],-19,-15,4.5,2.03)
            elif n=='shoulder_swing_stub_-16':s=cyl([-26,0,0],[3,0,0],2)
            elif n=='shoulder_swing_washer_-16':s=ring([1,0,0],-14,-13,6,2.15)
            elif n=='shoulder_cross_head':s=ring([1,0,0],-12.8,3,4,2.08)
            elif n.startswith('shoulder_swing_') and any(t in n for t in ['magnet','pcb','connector','sensor_holder']):s=s.translate([-6.5,0,0])
        if name in ['lumbar','thorax'] and v['name']=='shoulder_open_yoke':
            pp=[np.array([14.5*math.cos(t),21.5*math.sin(t),0]) for t in np.linspace(math.pi,2*math.pi,33)]
            s=union(beam(x,y,3.5) for x,y in zip(pp[:-1],pp[1:]))-cyl([-30,0,0],[30,0,0],6.1)
        if name.endswith('ankle') and v['name']=='shoulder_open_yoke':
            s+=s.translate([0,-3,0])  # Broaden the complete U-shaped root into the retreated coaxial socket.
        if v['name'].startswith('humeral_') and axial_shift:
            if v['name'].startswith('humeral_stem_'):
                sign=-1 if v['name'].endswith('-1') else 1
                s=beam([0,sign*7.8,-2],[0,sign*7.8,-14-axial_shift],2.6) if iship else beam([sign*7.8,0,-2],[sign*7.8,0,-14-axial_shift],2.6)
            else:s=s.translate([0,0,-axial_shift])
        if short_roll:
            n=v['name']
            if n=='humeral_housing':s=ring([0,0,-1],12,26,8.8,6.1)
            elif n=='humeral_bearing_31':s=s.translate([0,0,8])
            elif n in ['humeral_rotor_flange','humeral_brake']:s=s.translate([0,0,8])
            elif n=='humeral_shaft':s=tube([0,0,-10],[0,0,-28],3,1.5)
        if isneck:
            n=v['name']
            if n=='shoulder_open_yoke':
                pp=[np.array([10.5*math.cos(t),14.5*math.sin(t),0]) for t in np.linspace(math.pi,2*math.pi,25)]
                s=(union(beam(x,y,3) for x,y in zip(pp[:-1],pp[1:]))-cyl([-28,0,0],[28,0,0],4.58))^box([-30,-16.95,-10],[30,10,10])
            if n=='shoulder_cross_head':
                s=tube([-7,0,0],[7,0,0],4,2.08)
            if n.startswith('shoulder_swing_') and any(t in n for t in ['ear_','bearing_','washer_']):s=s.translate([(-1 if n.endswith('-16') else 1)*-4,0,0])
            if n.startswith('shoulder_swing_stub_'):
                sign=-1 if n.endswith('-16') else 1
                s=cyl([sign*4,0,0],[sign*15,0,0],2)
            if n.startswith('shoulder_swing_') and any(t in n for t in ['magnet','pcb','connector','sensor_holder']):s=moved(s.translate([4,0,0]),rot([1,0,0],270))
            if n.startswith('shoulder_pitch_') and any(t in n for t in ['magnet','pcb','connector','sensor_holder']):s=s.translate([0,3,0])
            if n.startswith('shoulder_pitch_') and any(t in n for t in ['pcb','connector','sensor_holder']):
                # Full PCB outline shifted 3 mm posteriorly; sensing IC stays on
                # the magnet axis at an off-centre board position. No PCB scaling.
                s=s.translate([-3,0,0])
                if n.endswith('sensor_holder'):
                    for zz in [-7,7]:s+=beam([-3,-23,zz],[-3,-32,zz],1.6)
            if n=='shoulder_pitch_shaft':s=cyl([0,-27.5,0],[0,-14.5,0],2)
            if n.startswith('humeral_'):
                if n.startswith('humeral_stem_'):
                    sign=-1 if n.endswith('-1') else 1
                    s=beam([sign*2.5,0,-2],[sign*4.5,0,-10],2.6)+beam([sign*4.5,0,-10],[sign*9.2,0,-20],2.6)+beam([sign*9.2,0,-20],[sign*9.2,0,-28],2.6)
                else:s=s.translate([0,0,-14])
                if any(t in n for t in ['magnet','pcb','connector','sensor_holder']):s=moved(s,np.diag([1.,1,-1,1])).translate([0,0,-66])
                if n=='humeral_shaft':s=tube([0,0,-24],[0,0,-44],3,1.5)
                if n=='humeral_sensor_holder':
                    s=box([-6.8,-7.8,-51.5],[6.8,7.8,-47.5])-box([-5.25,-6.25,-52],[5.25,6.25,-47.4])
                    for sg in [-1,1]:
                        s+=beam([sg*8.1,0,-38],[sg*14.5,0,-38],1.6)+beam([sg*14.5,0,-38],[sg*14.5,0,-48.5],1.6)+beam([sg*14.5,0,-48.5],[sg*6.3,0,-48.5],1.6)
        if name=='lumbar' and v['name'].startswith('shoulder_swing_') and any(t in v['name'] for t in ['magnet','pcb','connector','sensor_holder']):s=moved(s,rot([0,0,1],180))
        if name=='thorax' and (v['name'].startswith('shoulder_pitch_') or v['name']=='shoulder_open_yoke'):s=moved(s,np.diag([1.,-1,1,1]))
        D.local(name+'_'+v['name'],mapf[v['frame']],s,W,role=v['role'],note='C concentric gimbal geometry; D retention/preload integration is tracked separately',group=name)
    return W

def build():
    D=Design();copy_c_arm(D,'l');copy_c_arm(D,'r')
    # Main pelvis and back support: dimensions are independent of the UE joint centres.
    D.link('pelvic_crossbeam','pelvis',P['thigh_r']+[-32,0,17],P['thigh_l']+[-32,0,17],5,2.3)
    for side in ['l','r']:
        hip=P['thigh_'+side];knee=P['calf_'+side];ank=P['foot_'+side];toe=P['ball_'+side];pr=side+'_'
        # Right hardware reflects canonical solids, rotations remain proper in the graph.
        sgn=1 if side=='l' else -1
        # Full H/R preload modules. The hip abduction journal is moved along its
        # own X axis, behind the neutral wrist corridor, never off that axis.
        hinge(D,pr+'hip_abduction','pelvis',pr+'hip_abduct',hip+[-HIP_BACK,0,0],[1,0,0],orient=[0,0,1],bore=6,od=12,friction_od=18,half=6,ear=12,include_sensor=True)
        hip_pitch_cartridge_seed(D,side,hip)
        hinge(D,pr+'hip_twist',pr+'hip_flex',pr+'hip_roll',hip+[0,0,-70],[0,0,-1],orient=[0,sgn,0],bore=6,od=12,friction_od=18,half=6,ear=12)
        for yy in [-sgn*18,-sgn*24]:
            D.link(pr+'pelvic_crossbeam_key_'+str(yy),'pelvis',hip+[-32,yy,17],hip+[-42,yy,17],4)
            D.link(pr+'hip_fixed_bridge_'+str(yy),'pelvis',hip+[-HIP_BACK,yy,HIP_BRIDGE],hip+[-42,yy,HIP_BRIDGE],3.5)
            D.link(pr+'hip_fixed_riser_'+str(yy),'pelvis',hip+[-HIP_BACK,yy,15],hip+[-HIP_BACK,yy,HIP_BRIDGE],3.5)
            D.link(pr+'hip_front_riser_'+str(yy),'pelvis',hip+[-42,yy,17],hip+[-42,yy,HIP_BRIDGE],3.5)
        for sx in [-12,12]:
            pier=beam(hip+[-HIP_BACK+sx,0,6],hip+[-HIP_BACK+sx,0,HIP_BRIDGE],3.5)-cyl(hip+[-HIP_BACK-24,0,0],hip+[-HIP_BACK+26,0,0],6.1)
            D.local(pr+'hip_bearing_pier_'+str(sx),'pelvis',pier,np.eye(4),note='Continuous D7 pier joins the real bearing ear to the pelvis bridge; journal bore relieved.')
        D.link(pr+'hip_pier_top','pelvis',hip+[-HIP_BACK-12,0,HIP_BRIDGE],hip+[-HIP_BACK+12,0,HIP_BRIDGE],3.5)
        D.link(pr+'hip_pier_cross','pelvis',hip+[-HIP_BACK,0,HIP_BRIDGE],hip+[-HIP_BACK,-sgn*24,HIP_BRIDGE],3.5)
        D.link(pr+'hip_L_yoke_a',pr+'hip_abduct',hip+[-HIP_BACK+26,0,0],hip+[-HIP_BACK+26,-sgn*22,0],5)
        D.link(pr+'hip_L_yoke_b',pr+'hip_abduct',hip+[-HIP_BACK+26,-sgn*22,0],hip+[-9,-sgn*22,0],4)
        D.link(pr+'hip_key_root',pr+'hip_flex',hip+[0,-sgn*12,-7],hip+[0,-sgn*12,-21],4)
        for xx in [-14,14]:
            D.link(pr+'hip_key_branch_'+str(xx),pr+'hip_flex',hip+[0,-sgn*12,-21],hip+[xx,-sgn*12,-28],3)
            D.link(pr+'hip_key_dogleg_'+str(xx),pr+'hip_flex',hip+[xx,-sgn*12,-28],hip+[xx,0,-36],3)
            D.link(pr+'hip_twist_rail_'+str(xx),pr+'hip_flex',hip+[xx,0,-36],hip+[xx,0,-58],3)
            D.link(pr+'hip_twist_seat_'+str(xx),pr+'hip_flex',hip+[xx,0,-58],hip+[np.sign(xx)*7,0,-58],3)
        D.link(pr+'hip_twist_outer_fork',pr+'hip_flex',hip+[0,-sgn*18,-58],hip+[0,-sgn*18,-82],3.5)
        D.link(pr+'thigh_tube',pr+'hip_roll',hip+[0,0,-87],knee+[0,0,23],7,3)
        hinge(D,pr+'knee',pr+'hip_roll',pr+'knee_flex',knee,[0,1,0],bore=6,od=12,friction_od=18,half=6,ear=12,orient=[-1,0,0])
        for sign in [-1,1]:
            D.link(pr+'knee_fork_link_'+str(sign),pr+'hip_roll',knee+[0,0,23],knee+[16,sign*12,0],3.2)
        D.link(pr+'shin_tube',pr+'knee_flex',knee+[0,0,-12],ank+[0,0,23],6,3)
        shinkey=beam([0,0,-5],[0,0,-15],4.5)-cyl([0,-20,0],[0,20,0],3.05)
        D.local(pr+'shin_key_neck',pr+'knee_flex',shinkey,T(knee),note='D9 key neck into ID6 tube: radial overlap 1.5 mm, replacing the rejected 0.20 mm annular junction; actual shaft bore retained')
        gimbal(D,pr+'ankle',pr+'knee_flex',pr+'ankle_roll',pr+'ankle_flex',None,ank,clock=-90)
        D.link(pr+'ankle_input_top',pr+'knee_flex',ank+[0,0,23],ank+[-25,0,23],3.5)
        D.local(pr+'ankle_tube_endcap',pr+'knee_flex',tube([0,0,19],[0,0,28],5,1.5),T(ank),note='D10 socket core into ID6 tube: 2 mm radial overlap; D3 central reserve. Continuous top-beam load path')
        for sy in [-7,7]:D.link(pr+'ankle_input_leg_'+str(sy),pr+'knee_flex',ank+[-25,0,23],ank+[-25,sy,0],3.5)
        D.local(pr+'heel_stem',pr+'ankle_flex',beam([0,0,0],[3,0,-10],4.75)+beam([3,0,-10],[3,0,-23],4.75),T(ank),note='D9.5 heel root for the explicit free-standing ground-reaction envelope.')
        sole=box([-14,-12,-29],[34,12,-23])
        for sy in [-1,1]:sole+=beam([-10,sy*9,-25.5],[-20,sy*16,-25.5],3.5)
        sole-=box([-14.1,-7,-25.9],[-10.3,7,-21.8])  # Rear upper-edge relief only; 3.1 mm sole floor and lateral heel roots remain.
        # Feet are real structural soles with a heel and a hinged toe platform.
        D.local(pr+'heel_sole',pr+'ankle_flex',sole,T(ank),role='shell',note='Complete sole included in height and collisions',group=pr+'foot')
        hinge(D,pr+'toe',pr+'ankle_flex',pr+'toe_flex',toe,[0,-1,0],ear=10.5,orient=[1,0,0],include_sensor=True)
        for sign in [-1,1]:D.link(pr+'toe_support_'+str(sign),pr+'ankle_flex',ank+[26,sign*10.5,-23],toe+[-15,sign*10.5,0],2.8)
        foot=box([-4,-11,-29],[19,11,-23])+beam([0,0,-5],[5,0,-25],4)
        D.local(pr+'toe_pad',pr+'toe_flex',foot,T(toe),role='shell',group=pr+'foot')
    # Spine hubs are located exactly at spine_02 and spine_04, not old midpoints.
    gimbal(D,'lumbar','pelvis','lumbar_flex','lumbar_side','lumbar_yaw',P['spine_02'],flip=-1,short_roll=True)
    back_posts=union(beam([9.5,sy,30],[12,sy,37.1],3.5) for sy in [-2,2])
    D.local('lumbar_link','lumbar_yaw',back_posts,T(P['spine_02']),note='Paired D7 posts bypass the locknut with open spanner access and connect to the next stator bridge.')
    gimbal(D,'thorax','lumbar_yaw','thorax_side','thorax_flex',None,P['spine_04'],flip=-1,clock=90)
    branch=union(beam(P['spine_02']+[12,sy,37.1],P['spine_04']+[32,sy,-13.5],3.5) for sy in [-2,2])
    D.local('thorax_input_branch','lumbar_yaw',branch,np.eye(4))
    seat=union(beam([32,sy,-13.5],[32,np.sign(sy)*7,0],3.5) for sy in [-2,2])-cyl([0,0,0],[55,0,0],6.1)
    D.local('thorax_input_seat','lumbar_yaw',seat,T(P['spine_04']))
    spine_direction=(P['spine_05']-P['spine_04'])/np.linalg.norm(P['spine_05']-P['spine_04'])
    D.link('thoracic_root_neck','thorax_flex',P['spine_04']+spine_direction*3,P['spine_04']+spine_direction*18,5)
    D.link('thoracic_centered_tube','thorax_flex',P['spine_04']+spine_direction*14,P['spine_04']+spine_direction*40,4.5,2)
    for sy in [-14,14]:
        D.link('thoracic_bone_fork_'+str(sy),'thorax_flex',P['spine_04']+spine_direction*38,P['spine_05']-spine_direction*7+[0,sy,0],3.5)
    for sy in [-22,22]:
        D.link('thoracic_fork_out_'+str(sy),'thorax_flex',P['spine_05']-spine_direction*7+[0,np.sign(sy)*14,0],P['spine_05']+[0,sy,-7],4)
        D.link('thoracic_fork_root_'+str(sy),'thorax_flex',P['spine_05']+[0,sy,-7],[-40,sy,420],4)
        D.link('thoracic_fork_return_'+str(sy),'thorax_flex',[-40,sy,420],[-40,sy,438],4)
    D.link('thoracic_rear_crossbar','thorax_flex',[-40,-22,438],[-40,22,438],4)
    route=[np.array([-40,-22,438])-P['neck_01'],np.array([-40,-15,414])-P['neck_01'],np.array([P['neck_01'][0]+42,-15,414])-P['neck_01'],np.array([42,-15,0]),np.array([22,-15,0]),np.array([22,0,0])]
    neckbridge=union(beam(x,y,4) for x,y in zip(route[:-1],route[1:]))-cyl([5,0,0],[45,0,0],4.6)
    D.local('neck_input_bridge','thorax_flex',neckbridge,T(P['neck_01']))
    leftseat=beam(P['clavicle_l']+[9,0,-61.5],P['spine_04']+spine_direction*25+[0,14,0],6.75)-cyl(P['clavicle_l']+[0,0,-74],P['clavicle_l']+[0,0,-60],4.6)
    leftseat-=cyl(P['clavicle_l']+[0,0,-56.7],P['clavicle_l']+[0,0,-50.7],9)
    D.local('left_clavicle_seat','thorax_flex',leftseat,np.eye(4),note='D13.5 root saddle carrying the new steel carrier mass; relieved around the actual rotating output envelope and bearing bore. UE C axis unchanged.')
    D.link('right_clavicle_seat','thorax_flex',P['clavicle_r']+[-7,0,-27],[-40,-22,438],3.2)
    # Narrow chest shell leaves the complete arm sweep open.
    chest=box([-10,-14,21],[8,14,38])-box([-8,-12,23],[6,12,39])
    D.local('thorax_shell','thorax_flex',chest,T(P['spine_04']),role='shell',note='1.8–2 mm review shell; counted in complete height / collision model')
    gimbal(D,'neck','thorax_flex','neck_side','neck_flex','neck_yaw',P['neck_01'],flip=-1,clock=-90,short_roll=True)
    # Head contour is a lightweight shell rather than the whole reference mannequin.
    head_x=float(P['neck_01'][0]-P['head'][0])
    cap=box([-40,-40,25],[40,40,60])
    outer=(md.Manifold.sphere(1,48).scale([19,23,27]).translate([head_x,0,25])^cap)+cyl([0,0,8.5],[0,0,25],1).scale([19,23,1]).translate([head_x,0,0])
    inner=(md.Manifold.sphere(1,48).scale([17,21,25]).translate([head_x,0,25])^cap)+cyl([0,0,2],[0,0,25],1).scale([17,21,1]).translate([head_x,0,0])
    head=outer-inner
    D.local('head_shell','head',head,T(P['head']),role='shell',note='Head crown and lower cut are actual mesh, not a budget placeholder')
    for sign in [-1,1]:
        D.link('head_spine_branch_'+str(sign),'neck_yaw',P['neck_01']+[sign*8.5,0,45.5],P['neck_01']+[sign*16,0,45.5],2.3)
        D.link('head_spine_rail_'+str(sign),'neck_yaw',P['neck_01']+[sign*16,0,45.5],P['neck_01']+[sign*16,0,70],2.8)
    D.link('head_spine','neck_yaw',P['neck_01']+[-19,0,70],P['neck_01']+[19,0,70],2.8)
    # External pelvis clamp deleted: body support is through its two feet.
    for yy in [29,33]:
        brace=beam([-31,yy,P['thigh_l'][2]+17],P['spine_02']+[-9,yy,-3],4)-cyl(P['spine_02']+[0,10,0],P['spine_02']+[0,50,0],6.1)
        D.local('pelvis_lumbar_brace_'+str(yy),'pelvis',brace,np.eye(4),note='Continuous D8 root load path, relieved around the two 684ZZ seats')
    from closures import apply
    apply(D)
    from ankle_sensor import apply as compact_ankle_sensor
    compact_ankle_sensor(D)
    if INTEGRATION.get("symmetry_enabled"):
        from integration_symmetry import apply as mirror_limbs
        mirror_limbs(D)
    # Compact, machined QT-steel waist-side pressure channels for new board/wire mass.
    for j in D.joints:
        if j['axis_id']=='lumbar_side' or j['axis_id'].endswith('ankle_flex'):j.update(pressure_plate_min_yield_MPa=750,pressure_plate_Kt=1.5)
        if j['axis_id'].endswith('ankle_flex'):j.update(cap_min_yield_MPa=750,cap_Kt=1.5)
    for p in D.parts:
        if p['name'] in ['lumbar_shoulder_swing_pressure_-1','lumbar_shoulder_swing_pressure_1'] or ('ankle_shoulder_swing' in p['name'] and any(s in p['name'] for s in ['_pressure_','_rotor_cap_'])):
            cap='_rotor_cap_' in p['name']
            p.update(material='42CrMo4 +QT, certified yield >=750 MPa',density_g_mm3=.00785,manufacturing='ONE_PIECE_MACHINED_QT_STEEL',sku='CUSTOM_QT750_KEYED_CAP' if cap else 'CUSTOM_QT750_PRESSURE_CHANNEL')
            p['notes']='Machine the keyed cap or pressure-channel envelope from certified QT steel stock, minimum yield 750 MPa after processing. Kt=1.5 and material certificate are explicit strength conditions.'
    # This long transfer cannot meet the printed-material bending allowance.
    # Its joined carrier, sockets and sensor seat are one custom steel body.
    for p in D.parts:
        if p['frame']=='l_clavicle_protract' and p['role'] in ['structure','rotor','shell']:
            p.update(material='304 steel, certified yield >=230 MPa',density_g_mm3=.00785,manufacturing='ONE_PIECE_CUSTOM_STEEL_CARRIER',sku='CUSTOM_304_L_CLAVICLE_CARRIER')
            p['notes']+=' Part of the one-piece machined steel carrier; not a printed or bonded metal/plastic junction. Keep all internal clearances and positive capture interfaces.'
    for side in ['l','r']:
        for suffix,b0,b1,t0,t1,ro,ri in [('thigh_tube','thigh','calf',87,23,7,3),('shin_tube','calf','foot',12,23,6,3)]:
            p=next(p for p in D.parts if p['name']==side+'_'+suffix);v=P[b1+'_'+side]-P[b0+'_'+side];length=np.linalg.norm(v);v/=length
            p['bone_link']=dict(bones=[b0+'_'+side,b1+'_'+side],gauge_world_mm=[(P[b0+'_'+side]+v*(t0+(length-t0-t1)*f)).tolist() for f in [.3,.5,.7]],outer_radius_mm=ro,inner_radius_mm=ri)
    p=next(p for p in D.parts if p['name']=='thoracic_centered_tube')
    p['bone_link']=dict(bones=['spine_04','spine_05'],gauge_world_mm=[(P['spine_04']+spine_direction*t).tolist() for t in [24,27,30]],outer_radius_mm=4.5,inner_radius_mm=2)
    if INTEGRATION.get("electronics_enabled"):
        from integrated_electronics import apply as add_electronics
        add_electronics(D)
        from integrated_sensors import apply as add_sensor_tails
        add_sensor_tails(D)
        from harness_mounts import apply as add_wire_tabs
        add_wire_tabs(D)
    return D

def poses():
    result={'neutral':dict(label='A 字中立站姿 · 双肩外展45°',angles=dict(NEUTRAL_ANGLES))}
    src=c.poses()
    for name in ['forward','side','overhead_front','overhead_side','elbow_max','carry','drink','head','pronate','supinate','wrist_flex','wrist_extend','radial','ulnar','shrug']:
        lab,q=src[name];result['arms_'+name]=dict(label='双臂 · '+lab,angles={s+'_'+k:v for s in ['l','r'] for k,v in q.items()})
    add=lambda n,l,q:result.update({n:dict(label=l,angles=q)})
    add('bend','弯腰取物',dict(lumbar_flex=40,thorax_flex=15,l_hip_flex=15,r_hip_flex=15,l_knee_flex=20,r_knee_flex=20))
    add('turn','转身回望',dict(lumbar_yaw=30,neck_yaw=55))
    add('sit','坐姿',dict(l_hip_flex=90,r_hip_flex=90,l_knee_flex=90,r_knee_flex=90))
    add('squat','下蹲',dict(l_hip_flex=110,r_hip_flex=110,l_hip_abduct=12,r_hip_abduct=12,l_knee_flex=130,r_knee_flex=130,l_ankle_flex=20,r_ankle_flex=20,lumbar_flex=15))
    add('step','迈步',dict(l_hip_flex=40,l_knee_flex=55,l_ankle_flex=10,r_hip_flex=-15,r_knee_flex=15,r_ankle_flex=-20,l_shoulder_flex=-20,r_shoulder_flex=30))
    add('kneel','单膝屈曲',dict(l_hip_flex=85,l_knee_flex=95,r_hip_flex=-15,r_knee_flex=130,r_ankle_flex=-35))
    add('toe','踮脚 / 趾部活动',dict(l_ankle_flex=-30,r_ankle_flex=-30,l_toe_flex=40,r_toe_flex=40))
    add('cross','双臂胸前交叉',dict(l_shoulder_flex=75,r_shoulder_flex=75,l_shoulder_abduct=-12,r_shoulder_abduct=-12,l_upperarm_roll=55,r_upperarm_roll=55,l_elbow_flex=110,r_elbow_flex=95))
    add('neck_down','低头',dict(neck_flex=40))
    add('neck_up','仰头',dict(neck_flex=-30))
    add('neck_left_tilt','颈侧倾左',dict(neck_side=20))
    add('neck_right_tilt','颈侧倾右',dict(neck_side=-20))
    add('neck_left_turn','颈转头左',dict(neck_yaw=70))
    add('neck_right_turn','颈转头右',dict(neck_yaw=-70))
    if (HERE/'daily_poses.json').exists():
        for n,p in load(HERE/'daily_poses.json').items():result[n]=p
    result['neutral']=dict(label='A 字中立站姿 · 双肩外展45°',angles=dict(NEUTRAL_ANGLES))
    for name,p in result.items():
        if name.startswith('neck_') or name in ['toe','turn','bend','sit','squat','kneel','step']:
            p['angles']={**NEUTRAL_ANGLES,**p['angles']}
    return result

def export(D):
    freeze();OUT.mkdir(parents=True,exist_ok=True);(OUT/'stl_layout').mkdir(exist_ok=True)
    wanted={v['name']+'.stl' for v in D.parts if v['role'] in ['structure','rotor','shell','friction']}
    for old in (OUT/'stl_layout').glob('*.stl'):
        if old.name not in wanted:
            assert old.resolve().parent==(OUT/'stl_layout').resolve()
            old.unlink()  # Only obsolete exports created by this new O24D generator.
    z={};rows=[];checks=[];scene=trimesh.Scene()
    for i,v in enumerate(D.parts):
        expected_volume=v['s'].volume()
        verts,faces=a.mesh_data(v['s']);z[f'{i}v']=verts;z[f'{i}f']=faces
        m=trimesh.Trimesh(verts,faces,process=False)
        if abs(m.volume-expected_volume)>max(1e-5,expected_volume*1e-8):raise ValueError('CSG/export volume mismatch: '+v['name'])
        row={key:value for key,value in v.items() if key!='s'}
        row.update(i=i,volume_mm3=float(m.volume),mass_centroid_mm=m.center_mass.tolist(),bounds_mm=m.bounds.tolist(),color=COLORS['metal'] if v.get('manufacturing')=='ONE_PIECE_CUSTOM_STEEL_CARRIER' else COLORS[v['role']])
        rows.append(row);checks.append(dict(name=v['name'],watertight=bool(m.is_watertight),positive_volume=bool(m.volume>0),components=len(v['s'].decompose())))
        if v['role'] in ['structure','rotor','shell','friction']:m.export(OUT/'stl_layout'/(v['name']+'.stl'))
        mm=m.copy();mm.apply_scale(.001);mm.units='m';mm.visual.vertex_colors=np.array([*row['color'],1])*255
        F=FA[v['frame']].copy();F[:3,3]*=.001;scene.add_geometry(mm,node_name=v['name'],transform=F)
    np.savez_compressed(OUT/'assembly_meshes.npz',**z)
    scene.export(OUT/'O24D_full_body.glb')
    put(OUT/'assembly.json',dict(revision='O24D',units='mm',manufacturing_release=False,parts=rows,neutral_frames=FA,build_reference_N_frames=F0,neutral_angles_deg=NEUTRAL_ANGLES))
    put(OUT/'profiles/hand_geometry.json',dict(hands=D.hands,additional_dof=0))
    put(OUT/'profiles/device_profile.json',PROFILE);put(OUT/'profiles/poses.json',poses())
    put(OUT/'profiles/pose_frames.json',{n:frames(p['angles']) for n,p in poses().items()})
    put(OUT/'reference/target_quinn.json',REF)
    put(OUT/'verification/mesh_integrity.json',dict(status='PASS_CSG_FEATURES' if all(r['watertight'] and r['positive_volume'] for r in checks) else 'FAIL',parts=checks,scope='Closed positive-volume CSG features, which are not necessarily individual printed parts. Disconnected features and enclosed cavity shells are retained in these counts. Actual joined material bodies and narrow bridges are checked separately by groups.py.'))
    put(OUT/'verification/fastener_stacks.json',dict(status='PASS' if all(s['protrusion_mm']>=s['minimum_two_threads_mm']-.0001 for s in D.stacks) else 'FAIL',rows=D.stacks))
    put(OUT/'profiles/joint_interfaces.json',D.joints)
    put(OUT/'verification/static_interface_machining.json',dict(geometry_sha256=sha(OUT/'assembly_meshes.npz'),rows=getattr(D,'interface_machining',[]),scope='Actual mating-hardware sockets subtracted only within the same rigid body. No moving-body collision removed by this operation. Core and material-interface checks remain mandatory.'))
    put(OUT/'verification/removed_machining_cutoffs.json',dict(geometry_sha256=sha(OUT/'assembly_meshes.npz'),rows=getattr(D,'cutoffs',[]),scope='Explicitly reviewed isolated chips removed from actual model; these were not functional fastened components.'))
    with (OUT/'BOM_candidate.csv').open('w',newline='',encoding='utf-8-sig') as f:
        w=csv.writer(f);w.writerow(['part','qty','role','frame','sku_or_candidate','notes'])
        for p in rows:w.writerow([p['name'],1,p['role'],p['frame'],p['sku'] or 'LAYOUT_CANDIDATE',p['notes']])
    print(json.dumps(dict(parts=len(rows),dof=PROFILE['physical_dof'],mesh=load(OUT/'verification/mesh_integrity.json')['status']),ensure_ascii=False),flush=True)

if __name__=='__main__':freeze();export(build())
