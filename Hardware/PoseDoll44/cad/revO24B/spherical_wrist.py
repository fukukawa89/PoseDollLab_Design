"""O24B: constrained spherical wrist feasibility candidate; O24A is read-only.

Exact A meshes proximal to W are reused. B is not a manufacturing release.
All lengths mm; column-vector, RH X-forward / Y-left / Z-up convention.
"""
from pathlib import Path
import sys, json, hashlib, math, csv, base64
import numpy as np
import manifold3d as md
import trimesh
from scipy.spatial.transform import Rotation

HERE=Path(__file__).resolve().parent
H=HERE.parents[1]; OLD=H/'bench/revO24'; OUT=H/'bench/revO24B'
sys.path.insert(0,str(H/'cad/revO24'))
import arm as a

CONFIG=dict(revision='O24B',stage='SPHERICAL_WRIST_FEASIBILITY',manufacturing_release=False,
    ball_radius_mm=12,liner_inner_radius_mm=12.05,liner_outer_radius_mm=12.75,
    socket_outer_radius_mm=15,cap_y_cut_mm=10.6,pin_radius_mm=1.5,slot_radius_mm=1.65,
    pin_length_mm=10.5,pin_radial_limits_mm=[5.5,16],guide_angles_deg=[-23,33],
    wrist_flex_limits_deg=[-65,70],wrist_deviation_limits_deg=[-20,30],
    stem_radius_mm=3,magnet_diameter_mm=8,magnet_height_mm=3,magnet_model_Br_T=1.2,
    sensor_position_mm=[0,0,16],sensor_candidate='TI TMAG5170A1; custom carrier PCB required',
    sensor_range_mT=25,sensor_ADC_bits=12,angle_order='Rx(deviation) @ Ry(flexion)',
    reference_height_mm=560,full_doll_height_verified=False,
    intent='One spherical output body has both wrist rotations; guide pins remove the third rotation. No claim that an indivisible rigid part creates motion.')

def load(path):return json.loads(Path(path).read_text('utf-8-sig'))
def put(path,value):a.put(path,value)
def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def sphere(r):return md.Manifold.sphere(r,96)

def frames(p,q=None):
    q=q or {};f=a.frames(p,q)
    f['wrist_guide']=f['wrist_base']@a.rot([1,0,0],q.get('wrist_deviation',0))
    f['hand_ball']=f['wrist_guide']@a.rot([0,1,0],q.get('wrist_flex',0))
    return f

def reused():
    meta=load(OLD/'assembly.json')['parts'];z=np.load(OLD/'assembly_meshes.npz');A=a.Assembly()
    for p in meta[:94]:
        i=str(p['i']);solid=md.Manifold(md.Mesh64(np.ascontiguousarray(z[i+'v']),np.ascontiguousarray(z[i+'f'],dtype=np.uint64)))
        A.add(p['name'],p['frame'],solid,p['role'],p['notes'],p['interfaces'])
    return A,meta,z

def build():
    A,meta,z=reused();c=CONFIG
    # The ball and neck are one output body. The central axial magnet is loaded
    # through a proximal bore and a removable polymer cap; final cap retention is open.
    ball=sphere(12)+a.cylinder([0,0,-10],[0,0,-21],3)
    magnet_bore=a.cylinder([0,0,-1.65],[0,0,13],4.10)
    pin_bores=a.union(a.cylinder([0,s*5.4,0],[0,s*17,0],1.55) for s in [-1,1])
    ball=ball-magnet_bore-pin_bores
    A.add('B_ball_and_centered_neck','hand_ball',ball,'rotor','D24 spherical output and D6 neck share W; central bore for D8x3 axial magnet. Pin retention and cap locking need manufacturing detail.')
    plug=(a.cylinder([0,0,1.7],[0,0,12.1],4.04)^sphere(12))
    A.add('B_magnet_access_plug','hand_ball',plug,'structure','Polymer closure envelope, not a finalized threaded or snap retention. 0.05 mm end gap; lock must be designed before printing for use.')
    A.add('B_axial_magnet_D8x3','hand_ball',a.cylinder([0,0,-1.5],[0,0,1.5],4),'magnet','Centered AXIALLY magnetized disc; magnetic moment along output +Z. Distinct from O24A diametric single-axis magnets.')
    for s in [-1,1]:
        A.add(f'B_guide_pin_{s}','hand_ball',a.cylinder([0,s*5.5,0],[0,s*16,0],1.5),'metal','D3 non-ferromagnetic pin stock, 10.5 mm cut length. Pair follows YZ arc and removes roll; final retention and wear unresolved.')
    cuts=[]
    for s in [-1,1]:
        for deg in np.linspace(-23,33,57):
            cuts.append(a.moved(a.cylinder([0,s*11.3,0],[0,s*17.5,0],1.65),a.rot([1,0,0],deg)))
    slot=a.union(cuts)
    for s in [-1,1]:
        side=a.box([-25,10.6 if s>0 else -25,-25],[25,25 if s>0 else -10.6,30])
        shell=(sphere(15)-sphere(12.75))^side
        for x in [-5,5]:shell= shell+a.beam([x,s*13.4,4],[x,s*13.4,19],1.7)
        shell=shell+a.beam([-5,s*13.4,19],[5,s*13.4,19],1.7)
        screw_hole=a.cylinder([0,s*10,19],[0,s*18,19],1.12)
        shell=(shell-sphere(12.75)-slot-screw_hole)
        A.add(f'B_socket_half_{s}','wrist_base',shell,'structure','Concave side cup with guide slot; paired compliant mount arms. Adjustable symmetric preload remains a bench design, not force-validated.')
        liner=((sphere(12.75)-sphere(12.05))^side)-slot
        A.add(f'B_spherical_liner_{s}','wrist_base',liner,'friction','Custom curved 0.70 mm friction liner, nominal radial clearance 0.05 mm; compression, material and coefficient untested.')
        A.add(f'B_preload_screw_{s}','wrist_base',a.cylinder([0,s*10,19],[0,s*15.7,19],1)+a.cylinder([0,s*15.7,19],[0,s*17.2,19],2),'metal','M2 non-ferromagnetic screw envelope. Threads omitted; preload target is not a specified tightening torque.')
        A.add(f'B_preload_washer_{s}','wrist_base',a.ring([0,s,0],15.2,15.7,2.5,1.1).translate([0,0,19]),'metal','OD5/ID2.2 washer envelope. Spring/preload specification must follow force tests.')
    bridge=[]
    for x in [-8,8]:
        bridge.append(a.beam([0,0,28],[x,0,23],2.2))
        for s in [-1,1]:
            bridge.append(a.beam([x,0,23],[x,s*10,19],2.2))
            bridge.append(a.beam([x,s*10,19],[0,s*10,19],2.2))
    bridge.append(a.cylinder([0,0,26],[0,0,29.5],4))
    bridge=a.union(bridge)
    for s in [-1,1]:bridge=bridge-a.cylinder([0,s*7,19],[0,s*12.3,19],.85)
    A.add('B_forearm_mount_bridge','wrist_base',bridge,'structure','Centered input interface at W +28 mm; split cup mounts outside the sensor. Not a qualified bolted interface to O24A tube.')
    A.add('B_three_axis_sensor_PCB','wrist_base',a.box([-6,-5,17],[6,5,18]),'pcb','12x10 custom PCB reservation, not an existing MT6701 module and not a routed board.')
    A.add('B_TMAG5170_package','wrist_base',a.box([-2.45,-1.5,15.5],[2.45,1.5,17]),'metal','Nominal 4.9x3 package envelope; sensing point modeled at [0,0,16] mm. SPI, three field components; hardware calibration required.')
    A.add('B_sensor_connector','wrist_base',a.box([6,-2,17],[10,2,19]),'connector','Connector reservation; vendor selection and harness bend clearance pending.')
    # Separate carrier, keeps mounting details visibly distinct from the electronics.
    holder=a.box([-7,-6,16.8],[7,6,18.5])-a.box([-6.2,-5.2,16.7],[6.2,5.2,19])
    holder=holder-a.box([5.9,-2.3,16.5],[8,2.3,19])
    for x in [-6.7,6.7]:holder=holder+a.beam([x,-5.6,18],[x,-5.6,23],.7)
    A.add('B_sensor_carrier','wrist_base',holder,'structure','Prototype removable PCB carrier; cover/fasteners and wiring not yet detailed.')
    p=meta[123];i=str(p['i']);A.add('B_hand_handle','hand_ball',md.Manifold(md.Mesh64(np.ascontiguousarray(z[i+'v']),np.ascontiguousarray(z[i+'f'],dtype=np.uint64))),'structure','Unmodified O24A rigid palm geometry; centered neck and handle are rigidly joined in this candidate. Interface locking is not finalized.')
    return A

def export(A):
    OUT.mkdir(parents=True,exist_ok=True);(OUT/'stl_layout').mkdir(exist_ok=True)
    profile=load(OLD/'profiles/arm_profile.json');ref=load(OLD/'reference/target_quinn.json')
    put(OUT/'config.json',CONFIG);put(OUT/'profiles/arm_profile.json',{**profile,'revision':'O24B','wrist_angle_order':CONFIG['angle_order'],'physical_wrist_dof':2,'sensor_change':'Two MT6701 channels replaced by one candidate 3D field sensor plus calibrated 2D estimator; not firmware compatible.'})
    put(OUT/'reference/target_quinn.json',ref)
    data=[];arrays={};integrity=[];neutral=frames(profile);scene=trimesh.Scene();wrist=trimesh.Scene()
    for i,p in enumerate(A.parts):
        v,f=a.mesh_data(p['s']);arrays[str(i)+'v']=v;arrays[str(i)+'f']=f;m=trimesh.Trimesh(v,f,process=False)
        data.append(dict(i=i,name=p['name'],frame=p['frame'],role=p['role'],color=a.COLORS[p['role']],notes=p['notes'],bounds_mm=m.bounds.tolist(),volume_mm3=float(m.volume),new=i>=94))
        integrity.append(dict(name=p['name'],watertight=bool(m.is_watertight),positive_volume=bool(m.volume>0),components=len(p['s'].decompose())))
        colored=m.copy();colored.visual.vertex_colors=np.array([*a.COLORS[p['role']],1])*255
        scene.add_geometry(colored,node_name=p['name'],transform=neutral[p['frame']])
        if i>=94:
            wrist.add_geometry(colored,node_name=p['name'])
            if p['role'] in ['structure','rotor','friction']:m.export(OUT/'stl_layout'/f'{p["name"]}.stl')
    np.savez_compressed(OUT/'assembly_meshes.npz',**arrays)
    scene.export(OUT/'O24B_hybrid_arm.glb');wrist.export(OUT/'O24B_spherical_wrist.glb')
    put(OUT/'assembly.json',dict(revision='O24B',parts=data,neutral_frames=neutral,manufacturing_release=False))
    put(OUT/'verification/mesh_integrity.json',dict(status='PASS' if all(p['watertight'] and p['positive_volume'] and p['components']==1 for p in integrity) else 'FAIL',parts=integrity))
    put(OUT/'reference/O24A_frozen_hashes.json',{name:sha(OLD/name) for name in ['assembly.json','assembly_meshes.npz','profiles/arm_profile.json','reference/target_quinn.json','O24A_left_arm.blend']})
    with (OUT/'BOM_candidate.csv').open('w',encoding='utf-8-sig',newline='') as stream:
        writer=csv.writer(stream);writer.writerow(['part','qty','role','new','note'])
        for p in data:writer.writerow([p['name'],1,p['role'],p['new'],p['notes']])
    print(json.dumps(dict(parts=len(data),new_parts=len(data)-94,mesh_status=load(OUT/'verification/mesh_integrity.json')['status'],geometry_sha256=sha(OUT/'assembly_meshes.npz')),ensure_ascii=False))

if __name__=='__main__':export(build())
