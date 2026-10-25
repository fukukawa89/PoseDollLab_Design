"""O24C compact arm candidate. Read-only A/B baselines, millimetres, RH coordinates.

No bearing, pin, magnet or PCB is geometrically scaled. Not a manufacturing release.
"""
from pathlib import Path
import sys, json, math, hashlib, csv
import numpy as np
import manifold3d as md
import trimesh

HERE=Path(__file__).resolve().parent
H=HERE.parents[1]; OLD=H/'bench/revO24'; BASE_B=H/'bench/revO24B'; OUT=H/'bench/revO24C'
sys.path.insert(0,str(H/'cad/revO24'))
import arm as a
load=lambda p:json.loads(Path(p).read_text('utf-8-sig'))
put=a.put; sha=a.sha
CONFIG=dict(revision='O24C',stage='COMPACT_DIGITAL_CANDIDATE',manufacturing_release=False,
    shoulder_yoke_radius_mm=14.5,shoulder_pitch_shift_mm=1.5,elbow_ear_center_mm=10.5,
    forearm_stem_half_spacing_mm=7.2,ball_radius_mm=11,liner_inner_radius_mm=11.05,
    liner_outer_radius_mm=11.75,socket_outer_radius_mm=14,cap_y_cut_mm=9.6,socket_lower_lip_z_mm=-9.3,
    pin_radius_mm=1.5,slot_radius_mm=1.64,pin_radial_limits_mm=[5.5,15],
    guide_angles_deg=[-23,33],stem_radius_mm=3,neck_end_mm=-18,
    wrist_mount_height_mm=24,magnet_diameter_mm=8,magnet_height_mm=3,
    magnet_model_Br_T=1.2,sensor_position_mm=[0,0,15],sensor_range_mT=25,sensor_ADC_bits=12,
    wrist_flex_limits_deg=[-65,70],wrist_deviation_limits_deg=[-20,30],
    angle_order='Rx(deviation) @ Ry(flexion)',reference_height_mm=560,
    sensor_candidate='TI TMAG5170A1, custom carrier PCB unresolved',
    full_doll_height_verified=False)

def frames(p,q=None):
    q=q or {};f=a.frames(p,q)
    f['wrist_guide']=f['wrist_base']@a.rot([1,0,0],q.get('wrist_deviation',0))
    f['hand_ball']=f['wrist_guide']@a.rot([0,1,0],q.get('wrist_flex',0))
    return f

def poses():
    result=a.poses()
    solved=HERE/'reach_poses.json'
    if solved.exists():
        for n,q in load(solved).items():result[n]=(result[n][0],q)
    return result

def sphere(r):return md.Manifold.sphere(r,96)

def proximal(p):
    A=a.build(p)
    A.parts=A.parts[:94]
    lookup={v['name']:v for v in A.parts}
    def replace(name,s,note):
        old=lookup[name];old['s']=s;old['notes']=note;old['changed']=True
    def translate(name,v,note):replace(name,lookup[name]['s'].translate(v),note)
    shift=CONFIG['shoulder_pitch_shift_mm'];r=CONFIG['shoulder_yoke_radius_mm']
    for v in list(A.parts):
        if v['name'].startswith('shoulder_pitch_'):
            translate(v['name'],[0,shift,0],f'O24C: complete pitch bearing/sensor stack shifted {shift} mm toward S along its original axis; bearing size and centre spacing retained.')
    cv=np.array(p['clavicle_vector'])
    for s in [-1,1]:
        aa=cv*.13;bb=cv*.24+np.array([s*11,0,0]);cc=cv+np.array([s*7,-24+shift,0])
        replace('clavicle_link_'+str(s),a.beam(aa,bb,2.2)+a.beam(bb,cc,2.2),'Rerouted to compact shoulder stack; original 4.4 mm strut diameter retained.')
    replace('shoulder_open_yoke',(a.arc([1,0,0],[0,1,0],r,180,360,3)-a.cylinder([-23,0,0],[23,0,0],4.58))^a.box([-30,-r-2.45,-10],[30,10,10]),f'Yoke centre radius {r} mm instead of 16; 6 mm strut diameter retained.')
    for x in [-16,16]:
        for kind in ['ear','bearing','stub','washer']:
            name=f'shoulder_swing_{kind}_{x}'
            translate(name,[np.sign(x)*(r-16),0,0],'Swing stack translated along original axis; two 684ZZ and OD12 friction faces retained.')
    replace('shoulder_cross_head',a.tube([-r+3.5,0,0],[r-3.5,0,0],4,2.08),'Shorter cross-head, original OD8 and bore retained.')
    for s in [-1,1]:
        replace('humeral_stem_'+str(s),a.beam([s*(r-6.7),0,-2],[s*(r-6.7),0,-14],2.6),'Humeral support moved inward; original D5.2 strut retained, avoiding the preserved OD12 friction face.')
    for v in list(A.parts):
        if v['name'].startswith('shoulder_swing_') and not any(k in v['name'] for k in ['ear_','bearing_','stub_','washer_']):
            translate(v['name'],[16-r,0,0],f'Complete swing sensor cassette shifted toward S by {16-r} mm; PCB and magnet unchanged.')
    ear=CONFIG['elbow_ear_center_mm'];delta=14-ear
    for s in [-1,1]:
        for kind in ['ear','bearing']:
            translate(f'elbow_{kind}_{s}',[0,-s*delta,0],'Elbow bearing stack moved inward; 684ZZ and original ear wall thickness retained.')
        replace(f'elbow_fork_{s*14}',(a.beam([0,0,22],[0,s*ear,22],2.6)+a.beam([0,s*ear,22],[0,s*ear,0],2.6))-a.cylinder([0,-20,0],[0,20,0],4.58),'Shorter lateral cantilever, original 5.2 mm fork strut diameter retained.')
    span=ear+3
    replace('elbow_shaft',a.cylinder([0,-span,0],[0,span,0],2),'Shorter D4 shaft; thread/locking design still pending.')
    translate('elbow_head',[0,-delta,0],'Head follows shortened shaft; head thickness retained.')
    translate('elbow_nut',[0,delta,0],'Nut follows shortened shaft; nut thickness retained.')
    for v in list(A.parts):
        if v['name'].startswith('elbow_') and any(k in v['name'] for k in ['magnet','pcb','connector','sensor_holder']):
            translate(v['name'],[0,delta,0],'Full elbow sensor cassette moved inward; magnet/PCB/gap unchanged.')
    for s in [-1,1]:
        y=CONFIG['forearm_stem_half_spacing_mm']
        replace('forearm_stem_'+str(s),a.beam([0,s*2.5,-5.5],[0,s*y,-15],1.5)+a.beam([0,s*y,-15],[0,s*y,-30],1.5),'Forearm support moved closer to bone line, original D3 strut retained; housing/bearings unchanged.')
    # A shorter wrist bridge leaves room for a longer, original-section bone tube.
    F=p['forearm_mm'];mount=CONFIG['wrist_mount_height_mm']
    replace('forearm_centered_tube',a.tube([0,0,-49],[0,0,-F+mount],6,3),'OD12/ID6 centred tube extended to new W +24 mm interface.')
    return A

def add_wrist(A):
    c=CONFIG;r=c['ball_radius_mm'];ri=c['liner_inner_radius_mm'];rl=c['liner_outer_radius_mm'];ro=c['socket_outer_radius_mm'];cut=c['cap_y_cut_mm']
    end=c['neck_end_mm'];pinend=c['pin_radial_limits_mm'][1];mount=c['wrist_mount_height_mm']
    ball=sphere(r)+a.cylinder([0,0,-r+2],[0,0,end],3)
    ball=ball-a.cylinder([0,0,-1.65],[0,0,r+1],4.10)-a.union(a.cylinder([0,s*5.4,0],[0,s*(pinend+1),0],1.55) for s in [-1,1])
    A.add('C_ball_and_centered_neck','hand_ball',ball,'rotor','D22 ball, unchanged D6 output neck and D8x3 magnet. Metal pin engagement and cap retention require manufacture detail.')
    A.add('C_magnet_access_plug','hand_ball',a.cylinder([0,0,1.7],[0,0,r+.1],4.04)^sphere(r),'structure','Original magnet bore diameter and cap wall allocation retained; cap locking unresolved.')
    A.add('C_axial_magnet_D8x3','hand_ball',a.cylinder([0,0,-1.5],[0,0,1.5],4),'magnet','Same standard D8x3 axial magnet as B; no magnetic component scaling.')
    for s in [-1,1]:A.add(f'C_guide_pin_{s}','hand_ball',a.cylinder([0,s*5.5,0],[0,s*pinend,0],1.5),'metal','D3 non-ferromagnetic pin stock, 9.5 mm cut length; final retention and wear pending.')
    slot=a.union(a.moved(a.cylinder([0,s*(r-.7),0],[0,s*(ro+2.5),0],c['slot_radius_mm']),a.rot([1,0,0],deg)) for s in [-1,1] for deg in np.linspace(-23,33,57))
    y=12.4;z=16
    for s in [-1,1]:
        side=a.box([-25,cut if s>0 else -25,-25],[25,25 if s>0 else -cut,30])
        shell=(sphere(ro)-sphere(rl))^side
        for x in [-5,5]:shell=shell+a.beam([x,s*y,3],[x,s*y,z],1.7)
        shell=shell+a.beam([-5,s*y,z],[5,s*y,z],1.7)
        shell=shell-sphere(rl)-slot-a.cylinder([0,s*9,z],[0,s*17,z],1.12)
        shell=shell^a.box([-30,-30,c['socket_lower_lip_z_mm']],[30,30,35])
        A.add(f'C_socket_half_{s}','wrist_base',shell,'structure','Outer shell thickness 2.25 mm and D3.4 support arms retained. Lower free lip trimmed at Z=-9.3, outside the liner contact patch, to clear neck at 30 degree deviation. Preload unqualified.')
        A.add(f'C_spherical_liner_{s}','wrist_base',((sphere(rl)-sphere(ri))^side)-slot,'friction','0.70 mm curved liner, 0.05 mm nominal radial gap, same thickness as B; contact and creep require bench measurement.')
        A.add(f'C_preload_screw_{s}','wrist_base',a.cylinder([0,s*9,z],[0,s*14.7,z],1)+a.cylinder([0,s*14.7,z],[0,s*16.2,z],2),'metal','M2 non-ferromagnetic screw envelope; full head and diameter retained, threads schematic.')
        A.add(f'C_preload_washer_{s}','wrist_base',a.ring([0,s,0],14.2,14.7,2.5,1.1).translate([0,0,z]),'metal','OD5/ID2.2 unchanged washer envelope.')
    beams=[]
    for x in [-8,8]:
        beams.append(a.beam([0,0,mount],[x,0,mount-3],2.2))
        for s in [-1,1]:
            beams.append(a.beam([x,0,mount-3],[x,s*9,z],2.2))
            beams.append(a.beam([x,s*9,z],[0,s*9,z],2.2))
    bridge=a.union(beams)+a.cylinder([0,0,mount-2],[0,0,mount+1.5],4)
    for s in [-1,1]:bridge=bridge-a.cylinder([0,s*6,z],[0,s*11.3,z],.85)
    components=bridge.decompose()
    assert all(s.volume()<1e-8 for s in sorted(components,key=lambda s:s.volume())[:-1]),'Disconnected load-bearing bridge'
    bridge=max(components,key=lambda s:s.volume())
    A.add('C_forearm_mount_bridge','wrist_base',bridge,'structure','W +24 mm input, unchanged D4.4 bridge struts and D8 spigot. Interface locking remains open.')
    A.add('C_three_axis_sensor_PCB','wrist_base',a.box([-6,-5,16],[6,5,17]),'pcb','Same 12x10 carrier footprint as B; custom PCB not routed.')
    A.add('C_TMAG5170_package','wrist_base',a.box([-2.45,-1.5,14.5],[2.45,1.5,16]),'metal','TI VSSOP body 3x3, lead span envelope 4.9x3; sensing point [0,0,15].')
    A.add('C_sensor_connector','wrist_base',a.box([6,-2,16],[10,2,18]),'connector','Same 4x4x2 connector reservation as B; harness clearance not verified.')
    holder=a.box([-7,-6,15.8],[7,6,17.5])-a.box([-6.2,-5.2,15.7],[6.2,5.2,18])-a.box([5.9,-2.3,15.5],[8,2.3,18])
    for x in [-6.7,6.7]:holder=holder+a.beam([x,-5.6,17],[x,-5.6,21],.7)
    A.add('C_sensor_carrier','wrist_base',holder,'structure','Carrier translated 1 mm, original wall retained and shorter supports; final fixings pending.')
    A.add('C_hand_handle','hand_ball',a.box([-3.5,-11,-45],[3.5,11,-18])+a.beam([0,0,-16],[0,0,-21],3.5),'structure','Original palm geometry unchanged. Positive neck overlap is a nominal rigid interface, not a designed fastener.')
    return A

def build(p=None):return add_wrist(proximal(p or load(OLD/'profiles/arm_profile.json')))

def freeze_baselines():
    path=OUT/'reference/baselines_sha256.json'
    if path.exists():
        for relative,digest in load(path).items():assert sha(H/relative)==digest,'Baseline changed: '+relative
    else:
        files=[]
        for folder in ['cad/revO24','cad/revO24B','bench/revO24','bench/revO24B']:
            files.extend(p for p in (H/folder).rglob('*') if p.is_file() and p.suffix in ['.py','.json','.npz','.blend','.zip'])
        put(path,{str(f.relative_to(H)).replace('\\','/'):sha(f) for f in files})

def export(A,p):
    freeze_baselines();OUT.mkdir(exist_ok=True);(OUT/'stl_layout').mkdir(exist_ok=True)
    ref=load(OLD/'reference/target_quinn.json')
    p={**p,'revision':'O24C','wrist_angle_order':CONFIG['angle_order'],'sensor_change':'B spherical 2DoF measurement retained; 7 single-axis sensors plus one 3D field sensor. No firmware integration claimed.'}
    put(OUT/'config.json',CONFIG);put(OUT/'profiles/arm_profile.json',p);put(OUT/'reference/target_quinn.json',ref)
    put(OUT/'profiles/poses.json',{n:dict(label=l,angles=q) for n,(l,q) in poses().items()})
    put(OUT/'profiles/pose_frames.json',{n:frames(p,q) for n,(_,q) in poses().items()})
    data=[];arrays={};integrity=[];ff=frames(p);scene=trimesh.Scene()
    for i,v in enumerate(A.parts):
        verts,faces=a.mesh_data(v['s']);arrays[str(i)+'v']=verts;arrays[str(i)+'f']=faces
        m=trimesh.Trimesh(verts,faces,process=False)
        row=dict(i=i,name=v['name'],frame=v['frame'],role=v['role'],color=a.COLORS[v['role']],notes=v['notes'],bounds_mm=m.bounds.tolist(),volume_mm3=float(m.volume),changed=v.get('changed',v['name'].startswith('C_')))
        data.append(row);integrity.append(dict(name=v['name'],watertight=bool(m.is_watertight),positive_volume=bool(m.volume>0),components=len(v['s'].decompose())))
        if v['role'] in ['structure','rotor','friction']:m.export(OUT/'stl_layout'/f'{v["name"]}.stl')
        m.visual.vertex_colors=np.array([*row['color'],1])*255;scene.add_geometry(m,node_name=v['name'],transform=ff[v['frame']])
    np.savez_compressed(OUT/'assembly_meshes.npz',**arrays);scene.export(OUT/'O24C_compact_arm.glb')
    put(OUT/'assembly.json',dict(revision='O24C',manufacturing_release=False,parts=data,neutral_frames=ff))
    put(OUT/'verification/mesh_integrity.json',dict(status='PASS' if all(r['watertight'] and r['positive_volume'] and r['components']==1 for r in integrity) else 'FAIL',geometry_sha256=sha(OUT/'assembly_meshes.npz'),parts=integrity))
    with (OUT/'BOM_candidate.csv').open('w',encoding='utf-8-sig',newline='') as f:
        w=csv.writer(f);w.writerow(['part','qty','role','changed_from_A','note'])
        for r in data:w.writerow([r['name'],1,r['role'],r['changed'],r['notes']])
    print(json.dumps(dict(parts=len(data),geometry_sha256=sha(OUT/'assembly_meshes.npz'),mesh_status=load(OUT/'verification/mesh_integrity.json')['status'])))

if __name__=='__main__':
    p=load(OLD/'profiles/arm_profile.json');export(build(p),p)
