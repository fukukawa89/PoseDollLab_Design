"""Separate the back housing from the human carrier using four existing M3x8s."""
from refine_revo23 import *

def nut_clearance_world():
    cut=[]
    for y,z in itertools.product((-53,53),(497,509)):
        A=np.eye(4);A[:3,:3]=np.array([[0,0,1],[1,0,0],[0,1,0.]])
        A[:3,3]=[-99.5,y,z]
        cut.append(move(kin.b.b.cyl(3.6,-8.4,-3.75),A))
    return union(cut)

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--hardware-clearance-only',action='store_true');args=ap.parse_args()
    parts=load_current();base,_,_=load_baseline();p=read(B/'profiles/device_profile.json');cfg=read(CFG)
    if cfg.get('backpack_mount_revision')=='detachable_rear_access_v2':
        raise RuntimeError('B2 uses deepen_revo23_backpack.py; the old fixed-coordinate fitter is not compatible.')
    O=frames(kin.profile,p['neutral_raw_deg']);F=frames(p,p['neutral_raw_deg']);M=F['f:chest'];I=np.linalg.inv(M)
    if args.hardware_clearance_only:
        parts['o22/controller_housing']['s']-=move(nut_clearance_world(),I)
        save_parts(parts);print('BACKPACK nut edge clearance added',flush=True);return
    chest,rep,added,keep=make_carrier('frame/chest',base['frame/chest'],O,F,p,cfg,base)
    C=np.array(read(H/'bench/revO22/mechanical/assembly_metadata.json')['controller_frame']);C[:3,3]=controller_corner(cfg)
    house=move(controller_shell(),C)
    flange=box([-101.5,-60,490],[-99.5,60,515]);tabs=union([box([-103.5,47,490],[-101.5,60,515]),box([-103.5,-60,490],[-101.5,-47,515])])
    holes=[];newparts=[];screwR=np.array([[0,0,1],[1,0,0],[0,1,0.]])
    for n,(y,z) in enumerate(itertools.product((-53,53),(497,509)),1):
        A=np.eye(4);A[:3,:3]=screwR;A[:3,3]=[-99.5,y,z]
        holes.append(move(kin.b.b.cyl(1.7,-12,5),A))
        for kind,shape,sku in [('screw',kin.b.b.screw(3,8,5.5,3,0),'SCREW_M3_L8'),('nut',kin.b.b.nut(3,5.5,2.4,-6.4),'NUT_M3')]:
            newparts.append(('o22/backpack_'+kind+'_'+str(n),dict(s=move(shape,I@A),token='f:chest',body='chest',role='metal',sku=sku,old_id=None)))
    cut=union(holes);flange=flange-cut;house=(house+tabs)-cut-nut_clearance_world()
    world=move(chest,M);verts,_=vf(world);ribs=[]
    for side in (-1,1):
        select=verts[(verts[:,0]>-55)&(verts[:,0]<-15)&(verts[:,2]>480)&(verts[:,2]<515)&(verts[:,1]*side>25)&(verts[:,1]*side<50)]
        b=select[np.argmin(np.linalg.norm(select-[-34,side*35,500],axis=1))]
        ribs.append(capsule([-100,side*45,500],b,3.5))
    parts['frame/chest']['s']=chest+move(flange+union(ribs),I)
    newparts.append(('o22/controller_housing',dict(s=move(house,I),token='f:chest',body='chest',role='print',sku=None,old_id='O23B-C01')))
    ix=max(x['index']for x in parts.values())+1
    for key,part in newparts:
        part['index']=parts[key]['index']if key in parts else ix;ix+=1;part['key']=key;parts[key]=part
    save_parts(parts);put(B/'assembly.json',dict(revision=REV,items=[{k:v for k,v in x.items()if k!='s'}for x in parts.values()]))
    z=np.load(B/'retained_interfaces.npz');keeps={k:z[k]for k in z.files};keeps['frame/chest|v'],keeps['frame/chest|f']=keep
    np.savez_compressed(B/'retained_interfaces.npz',**keeps);addition={}
    for key,part in parts.items():
        if part['role']!='structure':continue
        s=part['s']-solid(keeps[key+'|v'],keeps[key+'|f']);addition[key+'|v'],addition[key+'|f']=vf(s)
    np.savez_compressed(B/'added_structure.npz',**addition)
    put(B/'verification/backpack_mount.json',dict(source_geometry_sha256=sha(B/'assembly.npz'),new_print='O23B-C01',
        added_hardware={'SCREW_M3_L8':4,'NUT_M3':4},mount_holes_diameter_mm=3.4,
        mounting_faces_world_x_mm=-101.5,fastener_head_access='From the body side before fitting torso electronics; insertion path not yet verified',
        physically_tested=False,motion_clearance_proven=False))
    print('BACKPACK split, 4 M3x8 + 4 M3 nuts',flush=True)

if __name__=='__main__':main()
