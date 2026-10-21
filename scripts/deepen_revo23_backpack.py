"""O23B2 retained back pack with detachable support and rear-access screws.

The input is the archived checked O23B geometry, not the O22 print release.
This revision changes only the chest mount and controller assembly. It is an
engineering candidate: sampled clearance and tool paths are checked separately.
"""
from refine_revo23 import *
import shutil

HISTORY=B/'history/O23B_before_deeper_backpack_20261020'
INPUT_HASH='c1f9fd6cad0772d146a2d4fcc18b2b1fae81befd085700f59e72d59c73908861'
REVISION='O23B2-retained-backpack-20261020'

def archive():
    if not (HISTORY/'assembly.npz').exists():
        assert sha(B/'assembly.npz')==INPUT_HASH,'Expected the checked O23B input.'
        for rel in ['assembly.npz','assembly.json','retained_interfaces.npz','profiles/device_profile.json',
                    'verification/geometry.json','verification/motion_full.json','verification/motion_quick.json',
                    'verification/backpack_mount.json','verification/review_summary.json','verification/export_formats.json',
                    'DELIVERY.json','DESIGN.zh-CN.md','images/side.png','images/three_quarter.png']:
            target=HISTORY/rel;target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(B/rel,target)
        shutil.copy2(CFG,HISTORY/'parameters.json')
    assert sha(HISTORY/'assembly.npz')==INPUT_HASH

def source_parts():
    n=np.load(HISTORY/'assembly.npz');parts={}
    for item in read(HISTORY/'assembly.json')['items']:
        i=str(item['index']);parts[item['key']]=dict(item,s=solid(n[i+'v'],n[i+'f']))
    return parts

def save_precise_update(parts):
    # Preserve untouched bodies bit for bit; merely reading a Manifold and
    # serializing it again can retriangulate microscopic coincident seams.
    old=np.load(HISTORY/'assembly.npz');old_items={r['key']:r for r in read(HISTORY/'assembly.json')['items']};out={}
    for k,part in parts.items():
        i=str(part['index'])
        if k in old_items and k!='frame/chest'and not k.startswith('o22/'):
            oi=str(old_items[k]['index']);out[i+'v']=old[oi+'v'];out[i+'f']=old[oi+'f']
        else:out[i+'v'],out[i+'f']=vf(part['s'])
    np.savez_compressed(B/'assembly.npz',**out)

SCREW_R=np.array([[0,0,-1],[1,0,0],[0,-1,0.]])

def screw_frame(head):
    A=np.eye(4);A[:3,:3]=SCREW_R;A[:3,3]=head;return A

def fastener_pair(head, nut_start=-7.2):
    A=screw_frame(head)
    return move(kin.b.b.screw(3,8,5.5,3,0),A),move(kin.b.b.nut(3,5.5,2.4,nut_start),A)

def nut_pocket(head, start=-7.4, finish=-4.6):
    # 5.8 mm across flats, 0.2 mm axial allowance per side.
    hole=md.Manifold.cylinder(finish-start,5.8/np.sqrt(3),circular_segments=6).translate([0,0,start])
    return move(hole,screw_frame(head))

def main():
    archive();parts=source_parts();p=read(B/'profiles/device_profile.json');cfg=read(CFG)
    N=frames(p,p['neutral_raw_deg'])['f:chest'];I=np.linalg.inv(N)
    corner=np.array([-203.,47.,625.]);old_corner=np.array([-103.,47.,572.])
    delta=corner-old_corner
    for k,part in parts.items():
        if k.startswith('o22/') and not k.startswith('o22/backpack_'):
            part['s']=part['s'].translate(N[:3,:3].T@delta)
    # Remove the previous cantilever outside the human wall, while preserving
    # every explicitly retained precision interface from the checked model.
    keep_data=np.load(HISTORY/'retained_interfaces.npz')
    keep=move(solid(keep_data['frame/chest|v'],keep_data['frame/chest|f']),N)
    _,outer,_=anatomy('chest',N,cfg['scale'],cfg)
    old_mount_region=box([-150,-66,485],[-50,66,520])
    chest=move(parts['frame/chest']['s'],N)-(old_mount_region-outer-keep)
    # The independent bracket fits the printer envelope and leaves the chest
    # body compact. Four M3x8s fix it to four side-loaded captive nuts.
    body_heads=[[-52.2,y,z]for y,z in itertools.product((-30.,30.),(497.,513.))]
    case_heads=[[corner[0]-1.7,y,z]for y,z in itertools.product((-55.,55.),(corner[2]-75.,corner[2]-63.))]
    body_pads=union([box([-50,y-8,490],[-35,y+8,520]) for y in (-30,30)])
    front_ears=union([box([-52.2,y-8,490],[-50.2,y+8,520]) for y in (-30,30)])
    case_x=case_heads[0][0];case_z=corner[2]-75
    case_tabs=union([box([case_x,y-8,case_z-7],[case_x+2,y+8,case_z+19])for y in(-55,55)])
    rear_ears=union([box([case_x+2.2,y-8,case_z-7],[case_x+7.2,y+8,case_z+19])for y in(-55,55)])
    braces=[]
    for side in(-1,1):
        a=[-51.2,side*20,505]
        lo=[case_x+6.2,side*20,case_z-2]
        hi=[case_x+6.2,side*20,case_z+14]
        braces.extend([capsule(a,lo,3.5),capsule(a,hi,3.5),capsule(lo,hi,3.5)])
    crossbars=union([capsule([case_x+6.2,-55,z],[case_x+6.2,55,z],3)for z in(case_z-2,case_z+14)])
    bracket=(front_ears+rear_ears+union(braces)+crossbars)^box([-400,-100,400],[-50.2,100,700])
    C=np.array(read(H/'bench/revO22/mechanical/assembly_metadata.json')['controller_frame']);C[:3,3]=corner
    house=move(controller_shell(),C)+case_tabs
    holes=[];tools=[];newparts=[];ix=max(v['index']for v in parts.values())+1
    for k in list(parts):
        if k.startswith('o22/backpack_'):del parts[k]
    for n,head in enumerate(body_heads+case_heads,1):
        A=screw_frame(head);holes.append(move(kin.b.b.cyl(1.7,-10,4),A))
        # A 6 mm diameter straight driver shaft enters from the rear.
        tools.append(dict(id=n,head_neutral_mm=head,approach_direction=[-1,0,0],diameter_mm=6,length_mm=80))
        screw,nut=fastener_pair(head)
        for kind,s,sku in [('screw',screw,'SCREW_M3_L8'),('nut',nut,'NUT_M3')]:
            key=f'o22/backpack_{kind}_{n}';newparts.append((key,dict(s=move(s,I),token='f:chest',body='chest',role='metal',sku=sku,old_id=None)))
    body_cuts=[]
    for head in body_heads:
        body_cuts.append(nut_pocket(head))
        # A lateral loading slot admits a nut without reaching inside the torso.
        y=head[1];lo,hi=(y,44.)if y>0 else(-44.,y)
        body_cuts.append(box([head[0]+4.6,lo,head[2]-3.4],[head[0]+7.4,hi,head[2]+3.4]))
    for head in case_heads:bracket-=nut_pocket(head)
    all_holes=union(holes)
    chest=solid(*vf((chest+body_pads)-all_holes-union(body_cuts)));bracket=solid(*vf(bracket-all_holes));house=solid(*vf(house-all_holes))
    components=sorted(chest.decompose(),key=lambda s:-s.volume());debris=[]
    for fragment in components[1:]:
        if abs(fragment.volume())<1e-8:continue
        overlap=float((fragment^keep).volume())
        assert fragment.volume()<150 and overlap<.01,'Unexpected detached functional chest material.'
        if fragment.volume()>1e-8:debris.append(dict(volume_mm3=fragment.volume(),bounds_neutral_mm=fragment.bounding_box(),retained_numerical_sliver_mm3=overlap))
    chest=components[0]
    parts['frame/chest']['s']=move(chest,I)
    parts['o22/controller_housing']['s']=move(house,I)
    newparts.append(('o22/backpack_support',dict(s=move(bracket,I),token='f:chest',body='chest',role='print',sku=None,old_id='O23B-C02')))
    for key,part in newparts:
        part.update(index=ix,key=key);ix+=1;parts[key]=part
    save_precise_update(parts);put(B/'assembly.json',dict(revision=REVISION,items=[{k:v for k,v in x.items()if k!='s'}for x in parts.values()]))
    cfg.update(revision=REVISION,controller_front_corner_neutral_mm=corner.tolist(),backpack_mount_revision='detachable_rear_access_v2')
    put(CFG,cfg)
    put(B/'verification/backpack_mount.json',dict(revision=REVISION,source_geometry_sha256=sha(B/'assembly.npz'),input_geometry_sha256=INPUT_HASH,
        input_snapshot=str(HISTORY.relative_to(B)),previous_corner_mm=old_corner,new_corner_mm=corner,translation_neutral_mm=delta,
        total_added_hardware_over_O22={'SCREW_M3_L8':8,'NUT_M3':8},added_hardware_over_O23B={'SCREW_M3_L8':4,'NUT_M3':4},
        rear_access_screws=tools,nut_installation='Chest nuts slide in laterally; bracket nuts insert from its front before fitting the box.',
        independent_support_key='o22/backpack_support',new_print='O23B-C02',physically_tested=False,motion_clearance_proven=False,
        removed_old_mount_debris=debris,retained_interface_difference_mm3=float((keep-chest).volume()),
        tool_access_verified=False,unvalidated=['continuous motion','wire service loop','nut retention tolerance','strength','hold-pose load']))
    print('DEEPER BACKPACK',corner,'ITEMS',len(parts),'CHEST/SUPPORT/CASE COMPONENTS',*[len(s.decompose())for s in(chest,bracket,house)],flush=True)

if __name__=='__main__':main()
