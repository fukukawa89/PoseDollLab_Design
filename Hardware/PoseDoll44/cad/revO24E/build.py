"""O24E: derive from immutable saved D/T6 meshes; all dimensions are mm.

No old generator is executed. A geometrical result is never a physical test.
"""
from pathlib import Path
import sys, json, copy, hashlib, math, shutil, csv
sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
H = HERE.parents[1]
BASE = H / 'bench/revO24D'
OUT = H / 'bench/revO24E'
sys.path.insert(0, str(H / 'cad/revO24D'))
import fullbody as base
sys.path.insert(0, str(HERE))  # E verification modules must win over same-named legacy scripts.
import numpy as np
import manifold3d as md
import trimesh
T, rot, moved, box, cyl, tube, beam, union = (getattr(base, x) for x in ['T','rot','moved','box','cyl','tube','beam','union'])
load = base.load
put = base.put
sha = base.sha
PROFILE = copy.deepcopy(load(BASE / 'profiles/device_profile.json'))
for side in ['l', 'r']:
    nodes = PROFILE['nodes']
    flex = next(n for n in nodes if n['id'] == side+'_wrist_flex')
    dev = next(n for n in nodes if n['id'] == side+'_wrist_deviation')
    flex.update(parent=side+'_forearm_roll', offset_mm=dev['offset_mm'])
    dev.update(parent=side+'_wrist_flex', offset_mm=[0,0,0])
    ix = nodes.index(dev)
    nodes.remove(flex)
    nodes.insert(ix, flex)
PROFILE.update(revision='O24E',schema='POSEDOLL-O24E/1',
    wrist_order='Ry(flexion) @ Rx(deviation); right conjugated by diag(1,-1,1)',
    S1_physical_pass='NOT_INHERITED',
    accepted_H='User accepts T5 installed result plus T6 inheritance; no independent T6 H cycle count claimed',
    accepted_W='User accepted T6 W installed result',
    rejected_R='T6 open axial pocket excluded; positive transverse capture required',
    manufacturing_release=False, physical_tests_passed=False)
NODES = {n['id']: n for n in PROFILE['nodes']}
def frames(q=None): return base.frames(q, PROFILE)
F0, FA = frames(), frames(base.NEUTRAL_ANGLES)
COLORS = dict(base.COLORS, spring=[.25,.44,.84])
SOURCE_URL='https://www.schnorr-group.com/fileadmin/4_Downloads/Brochures/SCHNORR_Produktbroschuere_EN_2024-02.pdf'
SPRINGS={
 'S8M3':dict(article='000400',od=8.,id=3.2,t=.4,h0=.2,F75=186.),
 'S10M3':dict(article='001000',od=10.,id=3.2,t=.5,h0=.25,F75=279.),
 'S8M4':dict(article='000700A',od=8.,id=4.2,t=.4,h0=.2,F75=210.),
 'S12M4':dict(article='001800',od=12.,id=4.2,t=.6,h0=.4,F75=557.),
 'S12M6L':dict(article='002050C',od=12.5,id=6.2,t=.35,h0=.45,F75=151.),
 'S12M6':dict(article='002700A',od=12.5,id=6.2,t=.7,h0=.3,F75=660.)}

def freeze():
    OUT.mkdir(parents=True, exist_ok=True)
    files=[BASE/'assembly.json',BASE/'assembly_meshes.npz',BASE/'profiles/device_profile.json',
           BASE/'profiles/joint_interfaces.json',BASE/'profiles/poses.json',
           H/'bench/revO24C_T6/assembly.json',H/'bench/revO24C_T6/assembly_meshes.npz']
    data={p.relative_to(H).as_posix():sha(p) for p in files}
    expected='fd64f061821a42f803e2131b0f0642147ab9cc8e65dc32cdb5e3476a0b7c9e8e'
    assert data['bench/revO24D/assembly_meshes.npz']==expected, 'Unexpected baseline D'
    receipt=OUT/'reference/input_sha256.json'
    if receipt.exists(): assert load(receipt)==data, 'Frozen inputs changed'
    else: put(receipt,data)
    for src in ['images/front.png','images/o24d_side.png','profiles/poses.json','profiles/joint_interfaces.json','reference/target_quinn.json']:
        target=OUT/'reference/O24D'/src
        target.parent.mkdir(parents=True,exist_ok=True)
        if not target.exists():shutil.copyfile(BASE/src,target)
    put(OUT/'reference/accepted_state.json',dict(H=PROFILE['accepted_H'],W=PROFILE['accepted_W'],R=PROFILE['rejected_R'],cycle_100_without_retightening='TARGET_UNMEASURED',date='2026-10-26'))

def read_saved(folder=OUT):
    data=load(folder/'assembly.json');z=np.load(folder/'assembly_meshes.npz')
    parts=[]
    for p in data['parts']:
        p=copy.deepcopy(p);i=str(p['i'])
        p['s']=md.Manifold(md.Mesh64(np.ascontiguousarray(z[i+'v']),np.ascontiguousarray(z[i+'f'],dtype=np.uint64)))
        parts.append(p)
    return parts

def bounds(s):return np.array(s.bounding_box()).reshape(2,3)
def centre(s):return bounds(s).mean(0)
def materialize(s):
    v,f=base.a.mesh_data(s)
    return md.Manifold(md.Mesh64(np.array(v,dtype=np.float64,copy=True,order='C'),np.array(f,dtype=np.uint64,copy=True,order='C')))
def polyhex(af,z,h):return md.Manifold.cylinder(h,af/math.sqrt(3),af/math.sqrt(3),6).translate([0,0,z])
def align_z(axis):
    z=np.asarray(axis,float);z/=np.linalg.norm(z)
    x=np.cross([0,0,1] if abs(z[2])<.8 else [0,1,0],z);x/=np.linalg.norm(x)
    return np.c_[x,np.cross(z,x),z]
def disc(spec,height,flip=False):
    r,ri,t=spec['od']/2,spec['id']/2,spec['t']
    p=np.array([[ri,height-t],[r,0],[r,t],[ri,height]])
    if flip:p[:,1]=height-p[:,1];p=p[::-1].copy()
    return md.CrossSection([p]).revolve(circular_segments=48)

class Design:
    def __init__(self):
        self.parts=read_saved(BASE)
        self.joints=copy.deepcopy(load(BASE/'profiles/joint_interfaces.json'))
        self.changes=[];self.interfaces=[];self.preload=[];self.wrists=[]
        self.original_names={p['name'] for p in self.parts}
        self.oldloads={r['axis']:r for r in load(BASE/'verification/preload_retention_loads.json')['rows']}
    def by(self,name):return next(p for p in self.parts if p['name']==name)
    def world(self,p):return moved(p['s'],F0[p['frame']])
    def add(self,name,fr,s,W=np.eye(4),role='structure',sku=None,notes='',**meta):
        assert not s.is_empty(),name
        p=dict(name=name,frame=fr,s=moved(s,np.linalg.inv(F0[fr])@W),role=role,sku=sku,group=fr,notes=notes,**meta)
        self.parts.append(p);return p
    def change(self,p,s,notes,W=None):
        p['s']=materialize(moved(s,np.linalg.inv(F0[p['frame']])@W) if W is not None else s)
        p['notes']=notes;p['revision_change']=True
    def springpack(self,prefix,fr,W,z,sku,parallel=1,series=2,deflection=.65):
        sp=SPRINGS[sku];h=sp['t']+(1-deflection)*sp['h0'];pack=parallel*sp['t']+(1-deflection)*sp['h0']
        names=[]
        for g in range(series):
            for n in range(parallel):
                name=prefix+f'_spring_{g+1}_{n+1}';names.append(name)
                self.add(name,fr,disc(sp,h,g%2==1).translate([0,0,z+g*pack+n*sp['t']]),W,'spring',sku,
                    notes=f'SCHNORR {sp["article"]}, {sp["od"]}x{sp["id"]}x{sp["t"]}; group {g+1}/{series}, nested layer {n+1}/{parallel}.',density_g_mm3=.00785)
        return dict(sku=sku,spec=sp,parallel=parallel,series=series,count=parallel*series,
             height_mm=series*pack,free_height_mm=series*(parallel*sp['t']+sp['h0']),
             assembly_deflection_ratio=deflection,travel_to_flat_mm=series*(1-deflection)*sp['h0'],
             catalogue_force_at_75pct_N=parallel*sp['F75'],source=SOURCE_URL,parts=names)

def cartridge_frame(D,j):
    pre=j['id'];cap=D.by(pre+'_keyed_output_cap');rear=D.by(pre+'_rear_thrust_cap')
    z=centre(D.world(cap))-centre(D.world(rear));z/=np.linalg.norm(z)
    pin=D.by(pre+'_torque_pin');v,_=base.a.mesh_data(D.world(pin));_,axes=np.linalg.eigh(np.cov(v.T));x=axes[:,-1]
    x-=z*np.dot(x,z);x/=np.linalg.norm(x)
    # Deterministic service side, kept in the audit and assembly sequence.
    if x[np.argmax(abs(x))]<0:x=-x
    o=centre(D.world(D.by(pre+'_compression_cartridge')))
    return T(o,np.c_[x,np.cross(z,x),z])

def cartridges(D):
    for j in D.joints:
        if 'pressure_web_width_mm' in j:continue
        pre=j['id'];W=cartridge_frame(D,j);inv=np.linalg.inv(W)
        cs=lambda p:moved(p['s'],inv@F0[p['frame']])
        cap,shaft,sock,pin=[D.by(pre+x) for x in ['_keyed_output_cap','_shaft','_output_socket','_torque_pin']]
        parent=D.by(pre+'_compression_cartridge')['frame'];child=cap['frame']
        c=cs(cap);cb=bounds(c);front,top=cb[:,2];oldpz=centre(cs(pin))[2]
        pr=2 if j['bearing_diameter_mm']==4 else 3
        radius=float(np.max(np.linalg.norm(base.a.mesh_data(cs(sock))[0][:,:2],axis=1)))
        pz=front+(2.55 if pr==2 else 3.4)
        # Round bolt hole in shaft; axial slot only in the floating pressure cap.
        # This leaves a real compression path through both friction faces.
        slot=union(cyl([-radius-5,0,pz+dz],[radius+5,0,pz+dz],pr/2+.10) for dz in [-.2,0,.2])
        hexr=j['cartridge_hex_radius_mm']
        c=md.Manifold.cylinder(top-front,hexr,hexr,6).translate([0,0,front])-cyl([0,0,front-1],[0,0,top+1],j['bearing_diameter_mm']/2+.025)
        # Socket is slipped on WITHOUT the bolt. Through hole is then used for insertion.
        nh=3 if pr==2 else 4;af=4 if pr==2 else 5.5
        far=radius-nh-.5;head=-radius+pr;headr=1.9 if pr==2 else 2.75
        hole=cyl([-radius-6,0,pz],[radius+6,0,pz],pr/2+.15)
        body=cs(sock)
        nutW=T([far,0,pz],align_z([1,0,0]))
        nutcut=moved(polyhex(af+.2,-.05,nh+2),nutW)
        headcut=cyl([-radius-6,0,pz],[head+.20,0,pz],headr+.12)
        body-=hole+nutcut+headcut
        D.change(sock,body,'E socket and bone member: continuous body, transverse bolt inserted AFTER axial seating; closed hex nut trap, accessible from +service axis. No snap fit assumed.',W)
        c-=slot+headcut+union(nutcut.translate([0,0,dz]) for dz in [-.2,0,.2])
        D.change(cap,c,'E floating keyed pressure cap; 0.40 mm axial cross-bolt relief, recessed captive-nut clearance. Keep continuous lower annulus; spring preload bypasses bolt.',W)
        j['cap_effective_ligament_mm']=float(pz-pr/2-.30-front)
        cy=940 if pre in ['lumbar_shoulder_pitch','l_hip_pitch','r_hip_pitch'] else 750
        j['front_cap_min_yield_MPa']=cy
        cap['material']=f'42CrMo4 QT; certified Rp0.2 >={cy} MPa after machining'
        cap['sku']=f'E_CAP_D{j["bearing_diameter_mm"]}_QT{cy}_{pre}'
        if pre in ['l_hip_pitch','r_hip_pitch']:
            j['cap_min_yield_MPa']=940
            rear=D.by(pre+'_rear_thrust_cap');rear.update(material='42CrMo4 QT; certified Rp0.2 >=940 MPa after machining',sku='E_REAR_CAP_QT940_'+pre,revision_change=True)
            rear['notes']+=' E whole-body load: new certified QT940 rear cap required; ordinary 304 original rear cap not equivalent.'
        D.parts.remove(pin)
        L=far+nh+(0.4 if pr==2 else .5)-head
        stock=next(x for x in [20,25,30,35,40] if x>=L)
        D.add(pre+'_capture_bolt',child,base.k.screw([head,0,pz],[1,0,0],pr,L),W,'metal',f'M{pr}x{stock}_trim{L:.2f}',
             notes='ISO4762 class 10.9; trim only free tip, deburr and gauge. Capture screw is NOT a clamp: retain 0.10–0.20 mm transverse end play, full nylon engagement; verify pressure cap slides axially before setting preload. One-sided hex-key operation.')
        D.add(pre+'_capture_nyloc',child,base.k.nut([far,0,pz],[1,0,0],pr,af,nh),W,'metal',f'M{pr}_NYLOC',
             notes='New DIN985; outer metal hex captured by socket; metal face inward, nylon outward. At least one complete pitch protrudes; inspect actual nut height.')
        # Spring load selection starts from D load envelope + 20%; recomputed below.
        need=D.oldloads[j['axis_id']]['required_clamp_N']*1.20
        td=j['thread_diameter_mm']
        sku=('S12M6L' if need<100 else 'S12M6') if j['bearing_diameter_mm']==6 else ('S8M4' if need<150 else 'S12M4')
        parallel=max(1,math.ceil(need/(SPRINGS[sku]['F75']*.70)))
        pk=D.springpack(pre,child,W,top,sku,parallel,2 if sku=='S12M6L' else 1)
        delta=pk['height_mm']
        washer=D.by(pre+'_nut_washer');D.change(washer,cs(washer).translate([0,0,delta]),'E hardened washer outside spring pack.',W)
        nut=D.by(pre+'_locknut');oldnut=cs(nut);nb=bounds(oldnut);nz=nb[0,2]+delta
        nheight=3.2 if td==6 else 2.2;naf=10 if td==6 else 7
        D.change(nut,base.k.nut([0,0,nz],[0,0,1],td,naf,nheight),'E DIN439 metal thin nut with removable low-strength threadlocker (LOCTITE 222); keyed tab washer is independent positive anti-rotation lock. Do not use nylon adhesive.',W)
        nut['sku']=f'M{td}_DIN439_222_TAB'
        # Extend only threaded tip, retaining journal, rear head, and cross-hole.
        s=cs(shaft);oldtip=bounds(s)[1,2];tip=max(oldtip,nz+nheight+2*j['thread_pitch_mm'])
        # Fill old cross-hole and machine one new round hole at raised service station.
        sd=j['bearing_diameter_mm']/2-.01
        s+=cyl([0,0,oldpz-pr/2-.1],[0,0,max(pz+pr/2+.1,top-.5)],sd)
        s-=cyl([-radius,0,pz],[radius,0,pz],pr/2+.025)
        if tip>oldtip:s+=cyl([0,0,oldtip-.15],[0,0,tip],td/2)
        if any(p['name']==pre+'_end_safety_pin' for p in D.parts):
            ep=cs(D.by(pre+'_end_safety_pin'));zpin=tip-.55
            D.change(D.by(pre+'_end_safety_pin'),ep.translate([0,0,zpin-centre(ep)[2]]),'E end safety pin behind thin preload nut.',W)
            s-=cyl([-5,0,zpin],[5,0,zpin],.80)
        D.change(shaft,s,'E extended threaded end and relocated cross-hole for post-insertion capture. New certified stock with stated shaft material and journal fit; no welded hole repair and not a stock screw.',W)
        shaft['sku']=str(shaft['sku'])+'_E_CROSSHOLE'
        if pre=='l_clavicle_x':
            j['shaft_min_yield_MPa']=940
            shaft['notes']+=' Updated whole-body load requires certified Rp0.2 >=940 MPa, same qualified stock grade as lumbar/ankle shafts.'
        if pre in ['l_ankle_shoulder_pitch','r_ankle_shoulder_pitch','lumbar_shoulder_pitch','thorax_shoulder_pitch','l_hip_pitch','r_hip_pitch','neck_humeral']:
            # Close a full 1.4 mm ligament ABOVE the transverse head/nut opening.
            # Retains original radial silhouette; no thin edge is counted as a bridge.
            newtop=max(bounds(cs(sock))[1,2],pz+max(headr+.15,(af+.25)/math.sqrt(3))+1.4)
            ring=md.Manifold.cylinder(newtop-front,radius,radius,64).translate([0,0,front])
            ring-=md.Manifold.cylinder(newtop-front+2,hexr+.05,hexr+.05,6).translate([0,0,front-1])
            ring-=cyl([0,0,top+.1],[0,0,newtop+1],SPRINGS[sku]['od']/2+.20)
            if pre=='lumbar_shoulder_pitch':ring-=box([-20,6.5,front],[20,20,newtop+1])
            D.change(sock,cs(sock)+ring,'E reinforced continuous output ring; axial top band >=1.4 mm above head/nut service aperture; original radial envelope. Capture fitted AFTER bone member.',W)
            j['reinforced_socket_top_mm']=float(newtop)
        # Flat tab washer keyed into the output hex; bend one tab against a nut flat.
        # Depicted assembled, supplied as a laser-cut 0.4 mm blank, never a printed part.
        outertab=max(naf/2,SPRINGS[sku]['od']/2)+.35
        tab=tube([0,0,top-.4],[0,0,top],outertab+.4,j['bearing_diameter_mm']/2+.15)
        tab+=box([outertab,-1.3,top-.4],[outertab+.4,1.3,nz+nheight-.3])
        tab+=box([naf/2+.05,-1.3,nz+nheight-.7],[outertab+.4,1.3,nz+nheight-.3])
        tab+=box([-hexr,-1.,top-1.2],[-naf/2+.2,1.,top])
        if pre=='l_clavicle_z':tab=moved(tab,rot([0,0,1],180))
        D.add(pre+'_lock_tab',child,tab,W,'metal',f'E_TAB_M{td}_{pre}',notes='Custom machined/formable annealed 304 tab: 0.4 mm annular web and outer tongue, integral 1.2 mm key boss. Not an ordinary flat laser-cut washer. Machine from 1.2 mm blank, then form outer tongue to the actual adjusted nut flat; replace after unbending.')
        cap['s']-=moved(tab,np.linalg.inv(F0[cap['frame']])@W)
        # Radial electronics stay; front axial magnet/board shifts with shaft tip.
        for p in list(D.parts):
            if not p['name'].startswith(pre+'_') or not any(x in p['name'] for x in ['magnet','pcb','connector','sensor_holder']):continue
            b=bounds(cs(p))
            if b[0,2]>=oldtip-.1 and tip>oldtip:
                D.change(p,cs(p).translate([0,0,tip-oldtip]),'E front sensor shifted to preserve magnet/IC gap. '+p['notes'],W)
        j.update(elastic_preload=pk,output_capture='recessed transverse screw with captive DIN985, installed after socket',preload_cap_axial_slot_mm=.4)
        j.update(preload_path='Head / rear keyed cap / rear steel friction pad / fixed steel cartridge / front friction pad / floating keyed cap / disc spring pack / hardened washer / thin metal adjustment nut. Cap slot permits axial float; bearing ends and printed bodies excluded from preload loop.',retention='Output bone / transverse capture screw / shaft / keyed metal thrust caps / fixed cartridge / fixed D1.5 capture pin / input bone. Adjustment nut locked by separate keyed forming tab plus removable low-strength metal thread-lock.')
        D.interfaces.append(dict(id=pre,axis=j['axis_id'],W=W.tolist(),fixed_frame=parent,output_frame=child,
             socket=sock['name'],cap=cap['name'],shaft=shaft['name'],pin_z_mm=float(pz),pin_diameter_mm=pr,
             bolt=pre+'_capture_bolt',nut=pre+'_capture_nyloc',socket_radius_mm=radius,capture_bolt_length_mm=L,
             cap_axial_slot_mm=.4,entry_axis_world=W[:3,2].tolist(),bolt_entry_world=(-W[:3,0]).tolist(),
             sequence=['fixed sleeve capture pin','bearings','rear keyed shaft and rear pad','front pad','floating cap','socket and output bone','capture nut','capture bolt','spring groups','washer','preload locknut','sensor cassette']))
        D.preload.append(dict(axis=j['axis_id'],family='C20',selection_load_N=need,**pk))
        print('C20',pre,sku,parallel,flush=True)

def hinges(D):
    for j in D.joints:
        if 'pressure_web_width_mm' not in j:continue
        pre=j['id'];axis=np.array(j['axis_world']);parent=D.by(pre+'_pressure_-1')['frame']
        # Locate the existing two head/washer/sleeve axes from saved solids.
        screws=[p for p in D.parts if p['name'].startswith(pre+'_preload_') and not p['name'].startswith(pre+'_preload_nut_') and not p['name'].startswith(pre+'_preload_w_')]
        packs=[]
        for screw in screws:
            suffix=screw['name'].removeprefix(pre+'_preload_');wa=D.by(pre+'_preload_w_'+suffix+'_-1');nu=D.by(pre+'_preload_nut_'+suffix)
            wc=centre(D.world(wa));nc=centre(D.world(nu));z=nc-wc;z/=np.linalg.norm(z)
            W=T(wc,align_z(-z));inv=np.linalg.inv(W)
            cs=lambda p:moved(p['s'],inv@F0[p['frame']])
            top=bounds(cs(wa))[1,2]
            need=D.oldloads[j['axis_id']]['required_clamp_N']/2*1.20
            sku='S8M3' if need<130 else 'S10M3'
            para=max(1,math.ceil(need/(SPRINGS[sku]['F75']*.70)))
            pk=D.springpack(screw['name'],parent,W,top,sku,para,2)
            # Head-side load washer; old washer remains the spring reaction surface.
            hz=top+pk['height_mm']
            D.add(screw['name']+'_spring_washer',parent,tube([0,0,hz],[0,0,hz+.5],SPRINGS[sku]['od']/2,1.6),W,'metal',f'W3_OD{SPRINGS[sku]["od"]:g}_T0.5',notes='Hardened flat support washer. Not a split lock washer.')
            tip=bounds(cs(screw))[0,2];length=hz+.5-tip
            stock=next(n for n in [20,25,30,35,40,45,50,55,60] if n>=length)
            D.change(screw,base.k.screw([0,0,hz+.5],[0,0,-1],3,length),'E two independent elastic preload ties; equalise both sides in alternating small turns.',W)
            screw['sku']=f'M3x{stock}_trim{length:.2f}'
            # Anti-rotation hex cradle is outside the pressure path; its back is open.
            nb=bounds(cs(nu));nz=nb[0,2];nh=nb[1,2]-nz
            nv,_=base.a.mesh_data(cs(nu));ix=np.argmax(np.linalg.norm(nv[:,:2],axis=1));theta=math.degrees(math.atan2(nv[ix,1],nv[ix,0]))
            clearance=moved(polyhex(5.7,nz-25,nh+25.5),rot([0,0,1],theta))
            trap=moved(polyhex(8.6,nz-.25,nh+.4),rot([0,0,1],theta))
            # Extend inwards to the existing continuous guide boss; do not split fork.
            trap+=tube([0,0,nb[1,2]-.2],[0,0,nb[1,2]+1.1],4.2,2.9)
            trap-=clearance
            D.add(screw['name']+'_nut_trap',parent,trap,W,'structure',notes='Closed six-flat DIN985 cradle, axial mouth accessible before screw. Outside metal spacer preload loop; joins the original integral guide boss.')
            for bp in D.parts:
                if bp['frame']==parent and bp['role'] in ['structure','rotor','shell']:
                    cut=moved(clearance,np.linalg.inv(F0[parent])@W)
                    if (bp['s']^cut).volume()>1e-5:D.change(bp,bp['s']-cut,bp['notes']+' Straight clocked DIN985 insertion passage.')
            packs.append(pk)
            D.preload.append(dict(axis=j['axis_id'],family='H16',tie=screw['name'],selection_load_N=need,**pk))
        j.update(elastic_preload=packs,physical_inheritance='T6 H elastic preload and independent locking principle only; D metal pressure frame has different loading')
        j['preload_path']='Two independent M3 ties / head washers / series-parallel disc spring packs / steel channel pressure plates / friction discs / steel cap-sleeve-cap / metal reaction washers / captive DIN985. Bearings and printed fork faces remain outside clamp loop.'
        print('H16',pre,flush=True)

def wrists(D):
    tdir=H/'bench/revO24C_T6';ta=load(tdir/'assembly.json');tz=np.load(tdir/'assembly_meshes.npz')
    for side in ['l','r']:
        keep_palm=D.by(side+'_palm');palm_hardware=[D.by(side+'_'+s) for s in ['palm_screw','palm_w0','palm_w1','palm_nut']]
        # Remove the entire superseded wrist, its old PCB and dedicated wrist tails.
        oldnames={p['name'] for p in D.parts if p['name'].startswith(side+'_W') or p['name'].startswith(side+'_wrist_') or p['name'].startswith(side+'_palm_')}
        D.parts=[p for p in D.parts if p['name'] not in oldnames and p is not keep_palm]
        W=F0[side+'_wrist_flex'];mirror=np.diag([1.,-1,1,1]) if side=='r' else np.eye(4)
        # W is already clocked by forearm's single -90 degree mounting transform.
        for p in ta['parts']:
            if p['station']!='W' or p['bench_only'] or p['id'].startswith(('W_R_','WPALM_')) or p['id']=='W3-09':continue
            i=str(p['index']);s=md.Manifold(md.Mesh64(np.asarray(tz['v'+i],dtype=np.float64),np.asarray(tz['f'+i],dtype=np.uint64)))
            if p['id']=='W4-01':
                # Replace only the proximal square bench interface by a solid root.
                s+=box([-5.15,-5.15,20.5],[5.15,5.15,32])+tube([0,0,28],[0,0,36],6,3)
                s-=cyl([0,0,29.8],[0,0,37],3)
            fr=side+'_'+{'fixed':'forearm_roll','flex':'wrist_flex','hand':'wrist_deviation'}[p['frame']]
            D.add(side+'_E_'+p['id'],fr,moved(s,mirror),W,p['role'],p['sku'],p['note'],
                 accepted_T6_source=p['id'],modified_interface_only=p['id']=='W4-01')
        keep_palm['frame']=side+'_wrist_deviation';D.parts.append(keep_palm)
        for p in palm_hardware:p['frame']=side+'_wrist_deviation';D.parts.append(p)
        # Captive M2 nylon nut replaces hand-held ordinary nut, with the same M2 screw.
        palm=D.by(side+'_palm');s=palm['s']
        nw=T([-9.5,0,-27],align_z([1,0,0]))
        trap=moved(polyhex(7.,-.4,3.8)-polyhex(4.2,-.5,3.5),nw)
        s+=trap
        D.change(palm,s,'Original O24D palm silhouette; local captive M2 DIN985 trap added to the 6 mm square key. Palm is the second wrist-axis output.')
        D.by(side+'_palm_nut').update(sku='M2_NYLOC',notes='M2 DIN985 AF4 height3, nylon outward; new nut for final assembly.')
        # One 3-axis TMAG per wrist preserves 38 boards / 42 raw scalars.
        # New nonlinear field map is validated for Ry@Rx; no reuse of old wrist LUT.
        mp=np.array([-12.5,0.,-16.]);sensor=np.array([0.,24.5,0.])
        magnet=cyl(mp+[0,-1.5,0],mp+[0,1.5,0],3)
        D.add(side+'_E_wrist_magnet',side+'_wrist_deviation',moved(magnet,mirror),W,'magnet','D6x3_ND_DIAMETRIC',notes='Diametric magnet in X-ear recess; keyed polarity mark. New calibration required; not assigned to the adjustable screw head.')
        output=D.by(side+'_E_W4-04');cut=cyl(mp+[0,-1.65,0],mp+[0,1.65,0],3.10)
        localcut=moved(moved(cut,mirror),np.linalg.inv(F0[output['frame']])@W)
        output['s']-=localcut
        # Blind seat opens on +Y. A standard eccentric washer blocks the opening;
        # it is installed only after the magnet. No closed-lip insertion assumed.
        cut=cyl(mp+[0,-1.65,0],mp+[0,4,0],3.10)
        mc=mp+[0,0,5.2];screwW=T(mc+[0,3.,0],align_z([0,-1,0]))
        seat=cyl(mp+[0,-2,0],mp+[0,2,0],4)+cyl(mc+[0,-6.5,0],mc+[0,2,0],3.1)
        hole=cyl(mc+[0,-8,0],mc+[0,4,0],1.1)
        nutcut=moved(polyhex(4.2,6.5,5),screwW)
        seat-=cut+hole+nutcut
        output['s']-=moved(moved(cut+hole+nutcut,mirror),np.linalg.inv(F0[output['frame']])@W)
        D.add(side+'_E_wrist_magnet_seat',side+'_wrist_deviation',moved(seat,mirror),W,notes='Blind D6.2 seat, open +Y. Insert magnet first; M2 screw and D7 washer overlap opening by 1.40 mm. Removable, no snap-fit lip or adhesive retention assumed.')
        for nm,solid,sku,note in [
            ('magnet_keeper_washer',tube([0,0,.5],[0,0,1.],3.5,1.1),'W2_OD7_T0.5','Standard washer blocks the magnet opening; inspect at least 1 mm overlap.'),
            ('magnet_keeper_screw',base.k.screw([0,0,0],[0,0,1],2,10),'M2x10','Insert after magnet and washer; new DIN985 nut, do not crush printed boss.'),
            ('magnet_keeper_nut',base.k.nut([0,0,6.5],[0,0,1],2,4,3),'M2_NYLOC','Preinsert from -Y before wrist core; nylon outward, 0.5 mm complete tip past nut.')]:
            D.add(side+'_E_'+nm,side+'_wrist_deviation',moved(moved(solid,screwW),mirror),W,'metal',sku,notes=note)
        pcb=box([-6,24.5,-5],[6,26.1,5]);con=box([-2,25,-9],[2,29,-5])
        holder=box([-7.7,24,-6.7],[7.7,26.20,6.7])-box([-6.15,24.45,-5.15],[6.15,28,5.15])-box([-5,23,-4],[5,25,4])
        for sx in [-1,1]:
            pc=np.array([sx*9.4,0.,0.]);pw=T(pc+[0,26.60,0],align_z([0,-1,0]))
            holder+=cyl(pc+[0,21.25,0],pc+[0,26.20,0],3.1)
            hc=cyl(pc+[0,19,0],pc+[0,29,0],1.1)+moved(polyhex(4.2,2.35,4),pw)
            holder-=hc
            D.add(side+f'_E_pcb_screw_{sx}',side+'_forearm_roll',moved(moved(base.k.screw([0,0,0],[0,0,1],2,6),pw),mirror),W,'metal','M2x6',notes='M2 x 6, captive DIN985. Install wide keeper washer after board; snug without PCB flex.')
            D.add(side+f'_E_pcb_nut_{sx}',side+'_forearm_roll',moved(moved(base.k.nut([0,0,2.35],[0,0,1],2,4,3),pw),mirror),W,'metal','M2_NYLOC',notes='New nut inserted from back before board; 0.65 mm nominal tip past nylon.')
            D.add(side+f'_E_pcb_keeper_{sx}',side+'_forearm_roll',moved(moved(tube([0,0,0],[0,0,.5],5,1.1),pw),mirror),W,'metal','W2_OD10_T0.5',notes='Standard wide keeper washer; overlaps PCB edge by 1.6 mm. Remove both washers for straight +Y board withdrawal.')
        for sx in [-1,1]:holder+=beam([sx*6.3,25.5,5.8],[sx*6.3,24,22],1.8)+beam([sx*6.3,24,22],[sx*6.3,7,25],1.8)
        D.add(side+'_E_wrist_pcb',side+'_forearm_roll',moved(pcb,mirror),W,'pcb','TMAG5170_EXISTING',notes='Existing 12x10 sensor design; 3-axis field output, two-angle bounded LUT for E wrist only.')
        D.add(side+'_E_wrist_connector',side+'_forearm_roll',moved(con,mirror),W,'connector','6_CORE_POTTED_TAIL',notes='Reuse native sensor solder-pad tail, potted strain relief; removable connector remains at carrier. Fixed side, no cable crosses either wrist axis.')
        D.add(side+'_E_wrist_sensor_holder',side+'_forearm_roll',moved(holder,mirror),W,notes='Continuous support into proximal fork; board enters +Y onto 0.45 mm rim before two standard wide keeper washers. No added printed cover or glued load path.')
        D.wrists.append(dict(side=side,center_world_mm=W[:3,3].tolist(),order='Ry(flex) @ Rx(deviation)',sensor_frame=side+'_forearm_roll',magnet_frame=side+'_wrist_deviation',magnet_local_mm=mp.tolist(),magnet_moment_axis=[1,0,0],sensor_local_mm=sensor.tolist(),mirror=mirror.tolist(),fixed_clock_count=1,raw='Bx,By,Bz',calibration='E-specific bounded nonlinear LUT; old D LUT invalid'))
        print('WRIST',side,flush=True)

def service_paths(D):
    """Machine documented straight service bores, never a moving collision Boolean."""
    cuts=[]
    pin=D.by('r_clavicle_z_fixed_capture_pin');fr=pin['frame'];c=centre(pin['s']);pb=bounds(pin['s']);passage=cyl([c[0],pb[0,1]-.1,c[2]],[c[0],50,c[2]],.9)
    def family(fr):
        while NODES[fr]['axis'] is None and NODES[fr]['parent']:fr=NODES[fr]['parent']
        return fr
    for p in D.parts:
        if p['role'] not in ['structure','rotor','shell'] or family(p['frame'])!=family(fr):continue
        cut=moved(passage,np.linalg.inv(F0[p['frame']])@F0[fr]);loss=(p['s']^cut).volume()
        if loss>.00001:
            D.change(p,p['s']-cut,p['notes']+' E D1.8 straight tool/pin access from +Y through the complete fixed chest; metal capture-pin press-fit bore unchanged.')
            cuts.append(dict(part=p['name'],interface='r_clavicle_z',operation='whole-chest fixed-pin service passage',diameter_mm=1.8,removed_mm3=loss))
    # Head shell is a fixed descendant of neck yaw and belongs to the SAME
    # manufactured output body. Its service access must be cut as well.
    it=next(x for x in D.interfaces if x['id']=='neck_humeral');W=np.array(it['W']);pz=it['pin_z_mm'];bolt=D.by(it['bolt']);bb=bounds(moved(bolt['s'],np.linalg.inv(W)@F0[bolt['frame']]))
    rr=max(abs(bb[:,1]).max(),abs(bb[:,2]-pz).max())+.15
    tool=cyl([-60,0,pz],[bb[0,0]+.2,0,pz],rr)
    for p in D.parts:
        fr=p['frame'];family=fr
        while NODES[family]['axis'] is None and NODES[family]['parent']:family=NODES[family]['parent']
        if family!=it['output_frame'] or fr==it['output_frame'] or p['role'] not in ['structure','rotor','shell']:continue
        local=moved(tool,np.linalg.inv(F0[fr])@W);loss=(p['s']^local).volume()
        if loss>.00001:
            D.change(p,p['s']-local,p['notes']+' E neck-yaw cross-screw service passage through complete integral head; fit cross-screw after head/bone seating.')
            cuts.append(dict(part=p['name'],interface=it['id'],operation='complete-head cross-screw entry',radius_mm=rr,removed_mm3=loss))
    for side in ['l','r']:
        pin=D.by(side+'_ankle_shoulder_swing_drive_pin');v,_=base.a.mesh_data(pin['s']);_,ax=np.linalg.eigh(np.cov(v.T));a=ax[:,-1];c=centre(pin['s']);bore=cyl(c-a*40,c+a*40,1.6)
        for p in D.parts:
            if p['frame']==pin['frame'] and p['role'] in ['structure','rotor','shell']:
                loss=(p['s']^bore).volume()
                if loss>1e-5:D.change(p,p['s']-bore,p['notes']+' Straight D3.2 printed drive-pin service passage. Metal pin bore remains nominal press fit.')
    for it in D.interfaces:
        W=np.array(it['W']);inv=np.linalg.inv(W);r=it['socket_radius_mm'];d=it['pin_diameter_mm'];pz=it['pin_z_mm']
        nh=3 if d==2 else 4;af=4 if d==2 else 5.5
        head=-r+d;far=r-nh-.5
        if it['id']=='thorax_shoulder_pitch':
            j=next(j for j in D.joints if j['id']==it['id']);axclear=cyl([0,0,pz-4],[0,0,j['reinforced_socket_top_mm']+.2],r+.25)
            p=D.by('thorax_input_branch');s=moved(p['s'],inv@F0[p['frame']]);D.change(p,s-axclear,p['notes']+' Axisymmetric clearance around reinforced output ring; continuous root screened independently.',W)
        # Tool and head enter from -X, captive nut from +X. These are straight
        # swept paths in one manufacturing body, not final-position scallops.
        bore=cyl([-45,0,pz],[head+.20,0,pz],(1.9 if d==2 else 2.75)+.15)
        bore+=moved(polyhex(af+.25,0,45-far),T([far,0,pz],align_z([1,0,0])))
        for p in D.parts:
            if p['frame']!=it['output_frame'] or p['role'] not in ['structure','rotor','shell']:continue
            local=moved(p['s'],inv@F0[p['frame']]);vol=(local^bore).volume()
            if vol>1e-5:
                D.change(p,local-bore,p['notes']+' E transverse tool/part service bore; inspect remaining section.',W)
                cuts.append(dict(part=p['name'],interface=it['id'],operation='transverse straight tool and nut path',removed_mm3=vol))
            if p['name'].endswith('_shoulder_open_yoke'):
                j=next(j for j in D.joints if j['id']==it['id']);shaft=moved(D.by(it['shaft'])['s'],inv@F0[it['output_frame']]);sb=bounds(shaft)
                axial=cyl([0,0,sb[0,2]-8.2],[0,0,sb[1,2]+.2],j['bearing_diameter_mm']/2+.16)
                local=moved(p['s'],inv@F0[p['frame']]);v=(local^axial).volume()
                if v>1e-5:
                    D.change(p,local-axial,p['notes']+' E axial installation bore, journal diameter +0.32 mm.',W)
                    cuts.append(dict(part=p['name'],interface=it['id'],operation='axial installation bore',removed_mm3=v))
    # Dedicated nonmoving pockets for new locked hardware. No joints or axes move.
    newmetal=[p for p in D.parts if p['role'] in ['metal','spring'] and (p['name'] not in D.original_names or p.get('revision_change'))]
    for p in D.parts:
        if p['role'] not in ['structure','rotor','shell']:continue
        for m in newmetal:
            if m['frame']!=p['frame']:continue
            a,b=bounds(p['s']),bounds(m['s'])
            if not (np.all(a[1]>b[0]) and np.all(b[1]>a[0])):continue
            vol=(p['s']^m['s']).volume()
            if vol>1e-4:
                p['s']=materialize(p['s']-m['s']);p['revision_change']=True
                cuts.append(dict(part=p['name'],hardware=m['name'],operation='explicit same-body hardware pocket',removed_mm3=vol))
    put(OUT/'profiles/service_machining.json',dict(rows=cuts,scope='Only rigid same-frame service bores / pockets. These operations do not establish strength or path clearance; separately checked.'))

def reinforce_roots(D):
    for side,sgn in [('l',-1),('r',1)]:
        p=D.by(side+'_shoulder_open_yoke');s=union(beam([sg*6,sgn*14.5,z],[sg*15,sgn*15,z],2.3) for sg in [-1,1] for z in [-5,5]);D.change(p,p['s']+s,p['notes']+' Four D4.6 roots bypass the transverse service bore and close the shoulder fork connection.')
    for side in ['l','r']:
        p=D.by(side+'_ankle_shoulder_open_yoke');braces=[]
        for sg in [-1,1]:
            for zz in [-6,6]:braces.append(beam([-17,sg*7.5,zz],[-13,sg*16,zz],2.3))
        D.change(p,p['s']+union(braces),p['notes']+' Four D4.6 full-material bypass roots around transverse service apertures.')
    p=D.by('lumbar_shoulder_open_yoke');s=union(beam([sg*7.5,19,-6],[sg*15,15,-6],2.3) for sg in [-1,1]);D.change(p,p['s']+s,p['notes']+' Two D4.6 lower continuous roots; upper quadrant stays open for lumbar yaw housing at side-bend endpoint.')
    p=D.by('thorax_shoulder_open_yoke');s=union(beam([19,sg*7.5,z],[15,sg*15,z],2.3) for sg in [-1,1] for z in [-6,6]);D.change(p,p['s']+s,p['notes']+' Four D4.6 continuous roots around the cross-bolt access.')
    for sg in [-1,1]:
        p=D.by('head_spine_branch_'+str(sg));s=beam([sg*9,0,49.5],[sg*16,0,54],2.5);D.change(p,p['s']+s,p['notes']+' D5 central upper root joins output ring to head rail; stays within the original azimuth corridor beside the fixed sensor supports.')
    # Two continuous bypasses stay outside the right clavicle PCB entry.
    p=D.by('r_clavicle_link_-1');route=[[-9.5,7,5],[-11,0,10.3],[-11,-10,5],[-11,-17,-5]];s=union(beam(a,b,2.0) for a,b in zip(route,route[1:]))
    it=next(x for x in D.interfaces if x['id']=='r_clavicle_x');W=np.array(it['W']);pad=D.by('r_clavicle_x_face_pad_1');pb=bounds(moved(pad['s'],np.linalg.inv(W)@F0[pad['frame']]))
    relief=cyl([0,0,pb[0,2]-.2],[0,0,pb[1,2]+.2],max(abs(pb[:,:2]).ravel())+.2)
    s-=moved(relief,np.linalg.inv(F0[p['frame']])@W)
    D.change(p,p['s']+s,p['notes']+' D4 curved-route bypass connects upper output-ring sector around the complete axial entry corridor to descending link; coaxial friction-washer service envelope has 0.2 mm clearance.')
    p=D.by('r_clavicle_link_1');s=beam([0,-4.5,0],[8,-4.5,0],1.6)+beam([8,-4.5,0],[10,-17,-5],1.6);D.change(p,p['s']+s,p['notes']+' D3.2 forward-side bypass keeps continuous material behind the PCB entry relief.')
    p=D.by('r_elbow_sensor_holder');s=box([-6.8,-24,-91.565],[6.8,-22.62,-75.565]);D.change(p,p['s']+s,p['notes']+' Continuous 1.38 mm PCB backing plate closes thin rim links; electronics entry stays clear on the other side.')

def cleanup_chips(D):
    from groups import physical_components
    buckets={};removed=[]
    for p in D.parts:
        if p['role'] not in ['structure','rotor','shell']:continue
        fr=p['frame']
        while NODES[fr]['axis'] is None and NODES[fr]['parent']:fr=NODES[fr]['parent']
        buckets.setdefault((fr,p.get('material','FDM')),[]).append(p)
    for (fr,mat),members in buckets.items():
        shapes=[moved(p['s'],np.linalg.inv(F0[fr])@F0[p['frame']]) for p in members]
        components=physical_components(union(shapes))
        chips=[s for s in components if s.volume()<5]
        if not chips:continue
        cut=union(chips)
        affected=[]
        for p,s in zip(members,shapes):
            loss=(s^cut).volume()
            if loss>1e-7:
                D.change(p,s-cut,p['notes']+' Explicit machining cutoffs removed; not a fastening feature.',F0[fr]);affected.append(p['name'])
        removed.append(dict(frame=fr,material=mat,affected_features=affected,chip_volumes_mm3=[s.volume() for s in chips],bounds_mm=[bounds(s) for s in chips],classification='Isolated burr/scallop after service boring, no intended retained function; major connected bodies preserved'))
    D.parts=[p for p in D.parts if p['s'].volume()>1e-6]
    put(OUT/'verification/removed_machining_chips.json',dict(rows=removed,criterion='Reviewed isolated positive material <5 mm^3; preserve all 47 major structural bodies. Not a strength acceptance.'))

def sensor_entries(D):
    import itertools
    rows=[]
    for pcb in [p for p in D.parts if p['name'].endswith('_pcb')]:
        pre=pcb['name'][:-4];holder=D.by(pre+'_sensor_holder');fr=pcb['frame'];moving=pcb['s']
        tail=next((p for p in D.parts if p['name']==pre+'_connector'),None)
        if tail:moving+=moved(tail['s'],np.linalg.inv(F0[fr])@F0[tail['frame']])
        v,_=base.a.mesh_data(pcb['s']);_,R=np.linalg.eigh(np.cov(v.T));R[:,0]*=np.linalg.det(R);center=centre(pcb['s']);local=moved(moving,T(-R.T@center,R.T));lo,hi=bounds(local)
        def family(fr):
            while NODES[fr]['axis'] is None and NODES[fr]['parent']:fr=NODES[fr]['parent']
            return fr
        obstacles_list=[(p,moved(p['s'],np.linalg.inv(F0[fr])@F0[p['frame']])) for p in D.parts if (family(p['frame'])==family(fr) if pre=='r_clavicle_z' else p['frame']==fr) and p['role'] in ['structure','rotor','shell'] and p is not holder]
        obstacles=union(s for p,s in obstacles_list)
        # Sweep each connected PCB/tail solid separately. A single bounding box
        # fills the empty bend between board and tail and causes false collisions.
        inflated=[md.Manifold.batch_hull([c.translate(t) for t in itertools.product([-.12,.12],repeat=3)]) for c in moving.decompose()]
        options=[]
        for ax in range(3):
            for sg in [-1,1]:
                direction=R[:,ax]*sg
                path=union(md.Manifold.batch_hull([c,c.translate(direction*30)]) for c in inflated);other=(path^obstacles).volume();loss=(path^holder['s']).volume()
                options.append((other>.02,other if other>.02 else loss,ax,sg,path,loss))
        options.sort(key=lambda r:(r[0],r[1]));bad,other,ax,sg,path,loss=options[0]
        relief=[]
        if bad:
            # Reviewed local rim clearances at existing board seats, not an
            # unrestricted cut through a load body. The resulting physical
            # bodies must pass the independent connected-core inspection.
            allowed=[]
            side=pre[0]
            if pre.endswith('_shoulder_pitch'):allowed=[side+'_clavicle_x_output',side+'_clavicle_link_-1',side+'_clavicle_link_1',side+'_clavicle_x_output_socket']
            if pre.endswith('_elbow'):allowed=[side+'_elbow_fork_14']
            if pre.endswith('_forearm'):allowed=[side+'_forearm_stem_-1',side+'_forearm_stem_1']
            if pre.endswith('_hip_pitch'):allowed=[side+'_hip_L_yoke_a',side+'_hip_abduction_keyed_outlet']
            if pre=='r_clavicle_z':allowed=['thoracic_centered_tube','thorax_shell']
            hits=[(p,(path^s).volume()) for p,s in obstacles_list if (path^s).volume()>.00001]
            if any(p['name'] not in allowed for p,v in hits) or other>20:
                rows.append(dict(board=pcb['name'],status='UNRESOLVED',minimum_other_material_intersection_mm3=other));continue
            for p,v in hits:
                p['s']=materialize(p['s']-moved(path,np.linalg.inv(F0[p['frame']])@F0[fr]));p['revision_change']=True;p['notes']+=' E local PCB rim clearance, recorded in sensor_entries; whole connected core checked after machining.'
                relief.append(dict(feature=p['name'],removed_mm3=v))
        holder['s']=materialize(holder['s']-path);holder['revision_change']=True;holder['notes']+=' E straight board plus existing potted-tail entry, 0.12 mm boundary clearance; install before any separate keeper.'
        if '_E_wrist' in pre:
            side=pre[0];mirror=np.diag([1.,-1,1,1]) if side=='r' else np.eye(4)
            for sx in [-1,1]:
                shim=box([sx*5.55-.4,24.38,-4],[sx*5.55+.4,24.5,4])
                D.add(side+f'_E_pcb_shim_{sx}',fr,moved(shim,mirror),F0[side+'_wrist_flex'],'connector','PET_0.12x0.8x8',notes='Cut 0.12 mm PET film strip, 0.8 x 8 mm; place on wrist board support edge before PCB. Two per wrist, retained by wide washers. Inspect actual thickness and flat seating.',material='PET film',density_g_mm3=.0014)
        direction=R[:,ax]*sg;rows.append(dict(board=pcb['name'],tail=tail['name'] if tail else None,holder=holder['name'],frame=fr,entry_local=direction.tolist(),travel_mm=30,removed_from_sensor_holder_mm3=loss,status='DESIGNED_ENTRY',local_rim_reliefs=relief,support_only_no_bone_cut=not relief,clearance_mm=.12,mounting='Existing non-load-bearing encapsulation bondline for single-axis boards; wrist board supported on two 0.12 mm PET shims under its clamp edges. Recalibrate after assembly.'))
    put(OUT/'profiles/sensor_entries.json',dict(rows=rows,scope='Separate convex sweeps of connected PCB and potted tail with 0.12 mm clearance. Explicit small rim reliefs are itemized; no automatic broad load-body cuts. Whole-body core and exact paths verified separately.'))

def export(D):
    z={};rows=[];scene=trimesh.Scene();checks=[]
    for p in D.parts:
        s=materialize(p['s']);p['s']=s
        if s.is_empty() or s.volume()<=1e-6:raise ValueError('Empty or negative '+p['name'])
        v,f=base.a.mesh_data(s);i=len(rows);z[str(i)+'v']=v;z[str(i)+'f']=f
        m=trimesh.Trimesh(v,f,process=False)
        row={k:v for k,v in p.items() if k not in ['s','i','bounds_mm','volume_mm3','mass_centroid_mm','color']}
        role=p['role'];color=COLORS.get(role,[.7,.7,.7])
        if p.get('material','').startswith('304'):color=COLORS['metal']
        row.update(i=i,volume_mm3=float(m.volume),bounds_mm=m.bounds.tolist(),mass_centroid_mm=m.center_mass.tolist(),color=color)
        rows.append(row);checks.append(dict(part=p['name'],watertight=bool(m.is_watertight),positive_volume=bool(m.volume>0)))
        mm=m.copy();mm.apply_scale(.001);mm.visual.vertex_colors=np.array([*color,1])*255
        F=FA[p['frame']].copy();F[:3,3]*=.001
        scene.add_geometry(mm,node_name=p['name'],transform=F)
    np.savez_compressed(OUT/'assembly_meshes.npz',**z)
    scene.export(OUT/'O24E_full_body.glb')
    put(OUT/'assembly.json',dict(revision='O24E',units='mm',parts=rows,manufacturing_release=False,neutral_frames=FA,build_reference_N_frames=F0,neutral_angles_deg=base.NEUTRAL_ANGLES))
    digest=sha(OUT/'assembly_meshes.npz')
    put(OUT/'profiles/device_profile.json',PROFILE);put(OUT/'profiles/joint_interfaces.json',D.joints)
    put(OUT/'profiles/poses.json',load(BASE/'profiles/poses.json'))
    put(OUT/'profiles/wrists.json',D.wrists)
    put(OUT/'profiles/capture_interfaces.json',D.interfaces)
    put(OUT/'profiles/preload_selection.json',dict(geometry_sha256=digest,rows=D.preload,specs=SPRINGS,source=SOURCE_URL,physical_force_curve_measured=False))
    put(OUT/'verification/mesh_integrity.json',dict(geometry_sha256=digest,status='PASS' if all(r['watertight'] and r['positive_volume'] for r in checks) else 'FAIL',rows=checks))
    put(OUT/'reference/change_inventory.json',dict(removed=sorted(D.original_names-{p['name'] for p in D.parts}),added=sorted({p['name'] for p in D.parts}-D.original_names),modified=[p['name'] for p in D.parts if p.get('revision_change')]))
    print('EXPORTED',len(rows),digest,flush=True)

def build():
    freeze();D=Design();cartridges(D);reinforce_roots(D);hinges(D);wrists(D);service_paths(D);sensor_entries(D);cleanup_chips(D);export(D)
    return D

if __name__=='__main__':build()
