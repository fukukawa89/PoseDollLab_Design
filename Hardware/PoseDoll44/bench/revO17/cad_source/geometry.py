"""O17: serviceable, subtractive integration of the frozen O16 mechanisms.
All legacy generators are read-only. No old source or artifact is overwritten.
"""
from pathlib import Path
import json, sys, hashlib, math
import numpy as np
HERE=Path(__file__).resolve().parent
H=HERE.parents[1]
sys.path.insert(0,str(H/'cad/revO15'))
from common import pose,tri,from_tri_exact,box,cyl,rot,solid_count,mesh_record,md
from fitted import build_fitted
from connected import carrier_inputs
from carriers_swept import ASSEMBLY_POSE
from layout_fullbody import fk
OUT=H/'generated/revO17'
BENCH=H/'bench/revO17'

def write(path,obj):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(obj,ensure_ascii=False,indent=2,allow_nan=False)+'\n',encoding='utf-8')

def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def move(s,A):return pose(s,A[:3,:3],A[:3,3])
def homogeneous(Q,p):
    A=np.eye(4);A[:3,:3]=Q;A[:3,3]=p;return A

def cassette_frame(key,meta,kinds):
    # The holder frame differs from its ring owner. PCB tail rotations do NOT
    # redefine this mechanical reference. All original signs here are +1.
    module,part=key.split('/',1);A=np.asarray(meta[key]['transform'])
    if part=='sensor_cradle':return A.copy()
    i=0 if part.startswith('C01_') else 1
    Z=np.eye(3)[i];X=np.array([0.,0.,-1 if i==0 else 1]);Y=np.cross(Z,X)
    phase=0 if i==0 or kinds[module]=='ankle_core' else 180
    return A@homogeneous(np.c_[X,Y,Z]@rot(2,phase),Z*16)

def integrated_cassette(cradle,clip):
    s=cradle+clip
    # Retain the shared M3 attachment and whole removable mast. Open the +Y
    # board-entry end. An integral rail spring at +X retains the PCB edge.
    s-=box([-7.2,5.05,14.4],[5.5,6.25,20])
    # 0.8 mm thick, 0.8 mm wide, 9.0 mm long leaf on the existing right rail.
    s-=box([6.3,-4.1,14.4],[7.2,6.25,20])
    s-=box([5.49,-4.1,15.8],[6.31,4.9,17.495])
    # Free the last portion from the upper clip; otherwise it cannot bend.
    s-=box([5.49,4.55,17.0],[6.31,6.25,20])
    # Entry chamfer, cut from the inherited front stop. No material is added
    # outside the union of the two O16 parts.
    # Ramp z=17.0 at y=4.9, z=16.25 at y=6.1.
    polygon=np.array([[4.9,17.0],[6.25,16.15625],[6.25,22],[4.9,22]])
    cutter=md.CrossSection([polygon]).extrude(1.2)
    # cross section XY represents YZ; extrusion Z represents X.
    s-=pose(cutter,np.array([[0,0,1],[1,0,0],[0,1,0]]),[5.4,0,0])
    return s

def magnet_basis(key,meta):
    # Analytic module datum. Never infer an encoder axis from tessellation/PCA.
    part=key.split('/',1)[1];A=np.asarray(meta[key]['transform']).copy()
    if part.startswith(('C01_','C02_')):
        i=0 if part.startswith('C01_') else 1;Z=np.eye(3)[i];X=np.array([0.,0.,-1 if i==0 else 1]);Y=np.cross(Z,X)
        A=A@homogeneous(np.c_[X,Y,Z],Z*16);radius,spacing=8.5,6.1
    else:radius,spacing=11.5,8.0
    if np.linalg.det(A[:3,:3])<0:A[:3,1]*=-1
    return A,radius,spacing

def parametric_cartridge(radius,spacing):
    # Reconstruct nominal dimensions before fusing. The O16 tessellated seat
    # and cap meet on a coplanar seam that can become non-manifold when welded.
    seat=cyl(6.2,8.4,10.6)+cyl(radius,9.8,10.6)
    seat-=cyl(3.1,10.4,10.7)+cyl(1.9,8.3,10.7)
    cap=cyl(radius,10.6,13.1)-cyl(3.075,10.5,12.95)-cyl(2.9,12.8,13.2)
    for x in (-spacing,spacing):
        seat-=cyl(1.15,8.3,10.7).translate([x,0,0])
        cap-=(cyl(1.15,10.5,13.2)+cyl(2.05,11.1,13.2)).translate([x,0,0])
    theta=math.degrees(math.asin(4.0/spacing))
    return ((seat+cap)-pose(box([0,-3.12,10.35],[20,3.12,12.96]),rot(2,theta))),theta

def make():
    OUT.mkdir(parents=True,exist_ok=True)
    p,m,states,fail,pr,prov=build_fitted('quinn',ASSEMBLY_POSE)
    if fail:raise ValueError(fail)
    kinds={s['id']:s['kind'] for s in states};old=p.copy();new={};replacements=[];services=[]
    for key in list(old):
        if not key.endswith('sensor_cradle'):continue
        pre=key[:-len('sensor_cradle')];clip=pre+'pcb_clip';A=cassette_frame(key,m,kinds);I=np.linalg.inv(A)
        c0,c1=move(old[key],I),move(old[clip],I);s=integrated_cassette(c0,c1)
        nk=pre+'sensor_cassette';new[nk]=(move(s,A),m[key].copy())
        replacements.append({'part':nk,'replaces':[key,clip],'anchor':key,'kind':'sensor_cassette','local_service_frame':A.tolist(),
            'old_count':2,'new_count':1,'added_outside_old_mm3':max(0.,float((s-(c0+c1)).volume()))})
        # Board is installed into the detached cassette before connecting FFC.
        # Leaf deflection is only a service clearance envelope, not elastic FEA.
        pcba={k:move(v,I) for k,v in old.items() if k.startswith(pre) and m[k]['sku'] in ('AS5048A_MINI_PCBA','PCBA_INCLUDED')}
        released=s-box([5.49,-4.11,14.4],[6.32,6.26,17.495])
        worst=0.;end=0.
        for t in np.linspace(0,24,49):
            for b in pcba.values():worst=max(worst,float((released^b.translate([0,t,0])).volume()))
        for b in pcba.values():end=max(end,float((s^b).volume()))
        services.append({'part':nk,'kind':'sensor_cassette','detached_pcba_slide_samples':49,'slide_mm':[0,24],
            'maximum_overlap_with_latch_released_mm3':worst,'installed_pcba_overlap_mm3':end,
            'leaf_length_mm':9.0,'leaf_thickness_mm':0.8,'leaf_width_mm':0.8,'release_travel_mm':1.2,
            'linear_cantilever_surface_strain_estimate':1.5*.8*1.2/9.0**2,
            'elastic_or_fatigue_validation':False,'material':'PETG prototype; qualify actual process',
            'note':'Clearance model removes the deflected leaf; real release/creep/fatigue needs a coupon.'})
    for key in list(old):
        if not key.endswith('magnet_seat'):continue
        pre=key[:-len('magnet_seat')];cap=pre+'magnet_cap';mag=pre+'magnet'
        screws=[k for k in old if k.startswith(pre) and ('magnet_screw_' in k or 'magnet_cap_screw_' in k)]
        if len(screws)!=2:raise ValueError((key,screws))
        bk=next(k for k in screws if not k.rsplit('_',1)[-1].startswith('-'))
        A,radius,d=magnet_basis(key,m);I=np.linalg.inv(A)
        seat,cover=move(old[key],I),move(old[cap],I)
        # Oblique side loading leaves most of the existing screw bearing land.
        # The screw HEAD blocks the 6 mm magnet after the assembly is closed.
        theta=math.asin(4.0/d);u=np.array([math.cos(theta),math.sin(theta),0.]);Q=rot(2,math.degrees(theta))
        slot=pose(box([0,-3.12,10.35],[20,3.12,12.96]),Q)
        s,angle=parametric_cartridge(radius,d);nk=pre+'magnet_cartridge';new[nk]=(move(s,A),m[key].copy())
        added=max(0.,float((s-(seat+cover)).volume()))
        replacements.append({'part':nk,'replaces':[key,cap],'anchor':key,'kind':'magnet_cartridge','local_service_frame':A.tolist(),
            'old_count':2,'new_count':1,'added_outside_old_mm3':added})
        magnet=move(old[mag],I);bolt=move(old[bk],I)
        overlaps=[float((s^magnet.translate(u*t)).volume()) for t in np.linspace(0,20,81)]
        block=[float((bolt^magnet.translate(u*t)).volume()) for t in np.linspace(0,20,81)]
        # Evaluate clamp bearing land at the original underside of the head.
        bearing=pose(cyl(1.88,11.09,11.10)-cyl(1.18,11.08,11.11),np.eye(3),[d,0,0])
        original_land=float(((seat+cover)^bearing).volume())
        new_land=float((s^bearing).volume())
        services.append({'part':nk,'kind':'magnet_cartridge','side_load_angle_deg':math.degrees(theta),
            'retaining_screw':bk,'insertion_samples':81,'insertion_mm':[0,20],
            'maximum_open_path_overlap_mm3':max(overlaps),'maximum_blocking_overlap_with_bolt_mm3':max(block),
            'screw_bearing_land_retained_fraction':new_land/original_land if original_land else 0,
            'magnet_slide_direction_local':u.tolist(),'magnet_antirotation_physical_test':False,'angular_retention':'Nonconductive adhesive in magnet side-wall clearance; replace magnet+cartridge as one service unit',
            'note':'Insert magnet from side and bond side wall before installing; keep both M2 fasteners. Screw blocks escape but does not constrain a round magnet against spin. Cured cartridge is the replacement unit.'})
    # Remove the battery, retaining the pre-equipment pelvic carrier geometry.
    # Intersection also retains any later cable reliefs; material only removed.
    _,frames,_=carrier_inputs('quinn','carriers_refined');T,_=fk(pr,ASSEMBLY_POSE)
    k='frame/pelvis';base=move(frames['pelvis'],T['pelvis']);s=p[k]^base;new[k]=(s,m[k].copy())
    replacements.append({'part':k,'replaces':[k],'anchor':k,'kind':'battery_mount_removal','old_count':1,'new_count':1,'added_outside_old_mm3':max(0.,float((s-p[k]).volume()))})
    # USB port at the top edge of the mounted XIAO, plus two tie slots. The
    # input connector and data cable have different power nets (D1 omitted).
    entry=next(x for x in read(H/'generated/revO15/runs/o15_20260929_r1/equipment/quinn_search.json')['entries'] if x['kind']=='controller')
    F=np.c_[[0,1,0],[0,0,-1],[-1,0,0]];o=np.array(entry['front_center_world_mm'])-F@np.array([35,30,0]);A=homogeneous(F,o)
    cut=box([28,-6,9.8],[42,4,19])
    for u in (23,45):cut+=box([u,-6,3],[u+3,-1,4.6])
    k='frame/chest';s=p[k]-move(cut,A);new[k]=(s,m[k].copy())
    replacements.append({'part':k,'replaces':[k],'anchor':k,'kind':'usb_port_and_tie_slots','old_count':1,'new_count':1,'added_outside_old_mm3':0.,'usb_plug_max_cross_section_mm':[12,8],'soft_tether_sweep_qualified':False})
    removed=[k for k in old if k=='accessory/chest/controller_pcba_D1' or k.startswith('accessory/pelvis/battery_') or (k.startswith('accessory/') and m[k]['sku']=='SEEED_FPC_A02_65MM')]
    for k in removed:p.pop(k);m.pop(k)
    for r in replacements:
        mats=[np.array(m[k]['transform']) for k in r['replaces']]
        if any(np.max(abs(M-mats[0]))>1e-9 for M in mats):raise ValueError(('different motion owners',r['part']))
        for k in r['replaces']:p.pop(k);m.pop(k)
        nk=r['part'];p[nk],m[nk]=new[nk]
    bad=[];stats=[]
    for k,(s,meta) in new.items():
        rec=mesh_record(s);stats.append({'part':k,**rec})
        if rec['components']!=1 or rec['status']!='Error.NoError':bad.append({'part':k,**rec})
    # Save each new solid in its actual owner frame, not in the printing frame.
    np.savez_compressed(OUT/'changed_parts.npz',**{k:tri(move(s,np.linalg.inv(mm['transform']))) for k,(s,mm) in new.items()})
    write(OUT/'changes.json',{'schema':'POSEDOLL-O17-CHANGES/1','replacements':replacements,'removed_parts':removed,
        'changed_parts':stats,'parts_after':len(p),'bad_solids':bad,'service_checks':services,
        'unchanged_kinematics':True,'raw_channels':46,'semantic_dof':41,
        'physical_tested':False,'continuous_collision_proof':False,
        'source_snapshot':'posedoll-o16-saved-20260930','source_commit':'26255df','envelope_scope':'Sensor cassettes/frame cuts are subtractive; magnet cartridges rebuilt from nominal O16 dimensions. Tessellation differences explicitly recorded; no blanket continuous collision proof.',
        'source_o16_zip_sha256':sha(H/'bench/revO16/PoseDoll_O16_Universal_Design.zip'),
        'generator_sha256':sha(__file__)})
    brief={'changed_solids':len(new),'merged_pairs':sum(r['old_count']==2 for r in replacements),'removed_assembly_parts':len(removed),'bad_solids':[v['part'] for v in bad],
        'max_new_occupied_volume_mm3':max(r['added_outside_old_mm3'] for r in replacements),
        'slide_issues':[r for r in services if r.get('maximum_overlap_with_latch_released_mm3',0)>1e-4 or r.get('installed_pcba_overlap_mm3',0)>1e-4 or r.get('maximum_open_path_overlap_mm3',0)>1e-4],
        'min_retained_screw_bearing_fraction':min(r['screw_bearing_land_retained_fraction'] for r in services if r['kind']=='magnet_cartridge'),
        'min_magnet_block_overlap_mm3':min(r['maximum_blocking_overlap_with_bolt_mm3'] for r in services if r['kind']=='magnet_cartridge')}
    print(json.dumps(brief,ensure_ascii=False,indent=2),flush=True)
    return p,m,pr,brief
if __name__=='__main__':make()
