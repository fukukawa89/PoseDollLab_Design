"""O23C compact back case and redesigned load-bearing collar/chest candidate.

The rejected long-support B2 experiment is archived before any replacement.
New hinge centres preserve every neutral body frame and all body orientations.
Moved bearing/magnet/sensor interfaces are taken from retained F7 geometry.
This script constructs geometry; independent checks determine its limitations.
"""
from study_revo23_compact import *
from deepen_revo23_backpack import screw_frame,fastener_pair,nut_pocket
import shutil

HISTORY=B/'history/O23B2_long_support_experiment_20261020'
INPUT_HASH='084fff8e58e5cb430031a00630f5097a23b96c580704bdcccdb3becfbcb9ac94'
REVISION='O23C-compact-backpack-20261020'
CHANGED={'frame/chest','frame/clavicle_l','frame/clavicle_r',
         'frame/clavicle_l.protract_frame','frame/clavicle_r.protract_frame'}


def archive():
    if not (HISTORY/'assembly.npz').exists():
        assert sha(B/'assembly.npz')==INPUT_HASH
        for rel in ['assembly.npz','assembly.json','retained_interfaces.npz','profiles','verification','images','design','DELIVERY.json','DESIGN.zh-CN.md']:
            src=B/rel;dst=HISTORY/rel
            if not src.exists():continue
            dst.parent.mkdir(parents=True,exist_ok=True)
            if src.is_dir():shutil.copytree(src,dst)
            else:shutil.copy2(src,dst)
        shutil.copy2(CFG,HISTORY/'parameters.json')
    assert sha(HISTORY/'assembly.npz')==INPUT_HASH
    (HISTORY/'EXPERIMENT.zh-CN.md').write_text('# O23B2 长支架避让试验\n\n该模型保留用于复查。侧视中背盒悬臂过长，且整体背盒系统仍有运动干涉，因此不作为最终外形方案，也未制造放行。\n用户已确认控制板尚未制作，后续 O23C 重新排布电路板和胸肩安装位置。\n',encoding='utf8')


def source():
    n=np.load(HISTORY/'assembly.npz');parts={}
    for item in read(HISTORY/'assembly.json')['items']:
        i=str(item['index']);parts[item['key']]=dict(item,s=solid(n[i+'v'],n[i+'f']))
    return parts


def joint_frame(p,ff,jid,child=False):
    j=next(j for j in p['joints'] if j['id']==jid)
    A=ff['f:'+j['parent']]@np.array(j['parent_to_mount_mm'])
    if child:
        Q=np.eye(4);Q[:3,:3]=kin.b.b.rot(2,p['neutral_raw_deg'][j['raw_ids'][0]]);A=A@Q
    return A


def patches(parts,p,p2):
    old=frames(p,p['neutral_raw_deg']);new=frames(p2,p2['neutral_raw_deg'])
    keepz=np.load(HISTORY/'retained_interfaces.npz');keeps={k:move(solid(keepz[k+'|v'],keepz[k+'|f']),old[parts[k]['token']]) for k in CHANGED}
    # F7 C7 split the left root into W005A. Its lever cup is a separate print,
    # absent from the W005B carrier's retained mesh. Include that actual root.
    root=parts['revision/clavicle_l.root']
    keeps['frame/clavicle_l.protract_frame']+=move(root['s'],old[root['token']])
    out={k:[] for k in CHANGED};records=[]
    for side in ('l','r'):
        for name,pa,ch in [('protract','frame/chest','frame/clavicle_'+side+'.protract_frame'),
                           ('elevate','frame/clavicle_'+side+'.protract_frame','frame/clavicle_'+side)]:
            jid='clavicle_'+side+'.'+name
            for child,key in [(False,pa),(True,ch)]:
                A=joint_frame(p,old,jid,child);N=joint_frame(p2,new,jid,child)
                lo,hi=([-12.5,-12.5,-2.0],[15.,12.5,10.]) if child else ([-19.5,-19.5,-11.5],[15.,10.,14.5])
                local=move(keeps[key],np.linalg.inv(A))^box(lo,hi)
                assert local.volume()>100,(key,jid,child,local.volume())
                q=move(local,N);out[key].append(q)
                records.append(dict(body=key,joint=jid,side='child' if child else 'parent',
                    old_center_mm=A[:3,3],new_center_mm=N[:3,3],volume_mm3=q.volume(),
                    retained_interface_crop_in_joint_coordinates_mm=[lo,hi]))
    for key,jid,radius in [('frame/chest','chest',36),('frame/chest','head',37),
        ('frame/clavicle_l','upperarm_l',40),('frame/clavicle_r','upperarm_r',40)]:
        A=joint_frame(p,old,jid);q=keeps[key]^ball(A[:3,3],radius)
        # Original nearest-anchor partition prevents distant end fragments.
        centers=[np.array(r['center_mm']) for c in read(HISTORY/'design/carriers.json') if c['key']==key for r in c['interfaces']]
        for c in centers:
            delta=c-A[:3,3]
            if np.linalg.norm(delta)<1:continue
            unit=delta/np.linalg.norm(delta);q=q.split_by_plane(unit,float(unit@((A[:3,3]+c)/2)))[1]
        out[key].append(q)
    return out,records


def connect_components(shape,precision,obstacles,radius=3.2):
    """Connect real exposed component boundaries; record failure, never fill bores."""
    for attempt in range(12):
        cc=sorted([s for s in shape.decompose() if s.volume()>.01],key=lambda s:-s.volume())
        if len(cc)<2:break
        vv,_=vf(cc[0]);tree=cKDTree(vv);targets=[]
        for c in cc[1:]:
            v,_=vf(c);dist,idx=tree.query(v);targets.append((float(dist.min()),c,v,dist,idx))
        success=False
        for _,c,v,dist,idx in sorted(targets,key=lambda q:q[0]):
            candidates=[]
            for n in np.argsort(dist):
                if any(np.linalg.norm(v[n]-v[q])<4 for q in candidates):continue
                candidates.append(n)
                if len(candidates)>=6:break
            for n in candidates:
                a=v[n];b=vv[idx[n]];axis=b-a;length=np.linalg.norm(axis)
                if length<1e-5:continue
                axis/=length;u=np.cross(np.eye(3)[np.argmin(abs(axis))],axis);u/=np.linalg.norm(u);w=np.cross(axis,u)
                crop=box(np.minimum(a,b)-14,np.maximum(a,b)+14)
                local_obstacles=obstacles^crop
                for delta in [np.zeros(3),u*7,-u*7,w*7,-w*7,u*12,-u*12,w*12,-w*12]:
                    mid=(a+b)/2+delta
                    beam=(capsule(a,mid,radius)+capsule(mid,b,radius))-local_obstacles
                    connected=[piece for piece in beam.decompose() if piece.volume()>.01 and (piece^c).volume()>.05 and (piece^cc[0]).volume()>.05]
                    if not connected:continue
                    shape=shape+union(connected);success=True;break
                if success:break
            if success:break
        if not success:break
    # Only discard free cut-off skin with no retained interface, and log the
    # remaining functional components in the caller's report.
    cc=sorted([s for s in shape.decompose() if s.volume()>.0001],key=lambda s:-s.volume())
    if len(cc)>1:shape=union(cc[:1]+[s for s in cc[1:] if (s^precision).volume()>.02])
    return solid(*vf(shape))


def main():
    archive();parts=source();p=read(HISTORY/'profiles/device_profile.json');cfg=read(HISTORY/'parameters.json')
    p2=compact_profile(p,x=-35,y=20,z=560,ex=24,ey=28,ez=562)
    p2['profile_id']='o23c_compact_shoulders_1p4';p2['o23_design']['compact_clavicles']=True
    p2['o23_design']['landmark_note']='Neutral body frames and bone lengths preserved; shoulder translation during protraction/elevation is redesigned. All raw-driven orientations retained.'
    p2['o23_design']['wrist_physical_travel_verified']=False
    old=frames(p,p['neutral_raw_deg']);F=frames(p2,p2['neutral_raw_deg']);pieces,patch_records=patches(parts,p,p2)
    removed=[k for k in parts if k.startswith(('o22/','revision/clavicle'))]
    for k in removed:parts.pop(k)
    # Actual other hardware/prints at neutral and the four previously used poses.
    # Expanded only along six Cartesian directions; not an isotropic proof.
    bounds={}; obstacles={};sourcecases=cases(p2,'quick')
    for key in CHANGED:
        owner=parts[key]['token'];sh=[];seen=set()
        for q in sourcecases.values():
            ff=frames(p2,q);T=F[owner]@np.linalg.inv(ff[owner])
            for k,item in parts.items():
                if k in CHANGED:continue
                M=T@ff[item['token']];b=np.array(move(item['s'],M).bounding_box())
                if b[5]<(455 if key=='frame/chest' else 495) or b[2]>630 or b[1]>120 or b[4]<-120:continue
                ck=(k,tuple(np.round(M,6).ravel()))
                if ck in seen:continue
                seen.add(ck);s=move(item['s'],M)
                sh.append(s)
        obstacles[key]=union(sh)
        print('OBSTACLES',key,len(sh),flush=True)
    rows=[];newkeeps={}
    for key in sorted(CHANGED):
        kept=union(pieces[key]);owner=parts[key]['token'];body=parts[key]['body'];N=F[owner]
        obstacle=obstacles[key]
        if key=='frame/chest':
            skin,outer,stations=anatomy('chest',N,1.4,cfg)
            addition=skin
        else:
            a,b=pieces[key][0:2]
            av,_=vf(a);bv,_=vf(b);at=av.mean(0);bt=bv.mean(0)
            # Single oval structural bridge, subsequently relieved against the
            # actual mechanism. It is part of this load-bearing print.
            addition=capsule(at,bt,7)-capsule(at,bt,3.8)
        addition=addition-obstacle-kept
        candidate=connect_components(kept+addition,kept,obstacle)
        newkeeps[key]=move(kept,np.linalg.inv(N));parts[key]['s']=move(candidate,np.linalg.inv(N))
        rows.append(dict(key=key,volume_mm3=candidate.volume(),components=len([s for s in candidate.decompose() if s.volume()>.01]),
            retained_volume_removed_mm3=max(0,(kept-candidate).volume())))
        print('NEW',rows[-1],flush=True)
    # Compact double-sided carrier is installed in a real two-piece housing.
    layout=read(B/'electronics/carrier/placement.json');assert layout['identical_pad_nets'] and layout['board_mm']==[64,60,1.6]
    C=np.eye(4);C[:3,:3]=np.array([[0,0,-1],[-1,0,0],[0,1,0.]])
    C[:3,3]=[-55,32,496];N=F['f:chest'];I=np.linalg.inv(N)
    def add(key,s,role='print',sku=None):
        parts[key]=dict(key=key,s=move(move(s,C),I),token='f:chest',body='chest',role=role,sku=sku,old_id=None)
    floor=box([-5,-5,0],[69,65,2])
    wall=box([-5,-5,1],[69,65,32])-box([-3,-3,.9],[67,63,32.1])
    # Wire exits remain open at both sides. PCB removal exposes inward ports.
    for u in (-6,66):wall=wall-box([u,10,4],[u+4,50,29])
    wall=wall-box([2,-6,21],[23,-2,32.1])-box([25,62,16],[40,66,32.1])
    mounts=[(3,3),(61,3),(3,57),(61,57)]
    posts=union([(kin.b.b.cyl(2.8,1.8,14)-kin.b.b.cyl(.85,8,15)).translate([u,v,0])for u,v in mounts])
    coverposts=[(-2,-2),(66,-2),(-2,62),(66,62)]
    capboss=union([(kin.b.b.cyl(2.5,1.5,32)-kin.b.b.cyl(.85,25,33)).translate([u,v,0])for u,v in coverposts])
    # The PCB outline clips the four tall lid bosses, keeping a 0.3 mm board
    # edge gap. M2 self-tapping thread engagement is an intentional fit.
    capboss=capboss-box([-.3,-.3,12],[64.3,60.3,33])
    housing=floor+wall+posts+capboss
    lid=box([-5,-5,32.2],[69,65,34.2])
    for u,v in coverposts:lid=lid-kin.b.b.cyl(1.15,32,35).translate([u,v,0])
    for u in range(7,59,10):
        for v in (5,55):lid=lid-box([u,v,32],[u+5,v+1.5,35])
    # Four rear-facing M3x8 screws mount the case directly to chest bosses.
    body_heads=[[-57.2,y,z] for y,z in itertools.product((-40.,40.),(500.,521.))]
    chassis=move(parts['frame/chest']['s'],N)
    ears=union([box([-57,y-5,z-6],[-55,y+5,z+6])for _,y,z in body_heads])
    pads=union([box([-54.8,y-6,z-7],[-30,y+6,z+7])for _,y,z in body_heads])
    for head in body_heads:
        A=screw_frame(head);hole=move(kin.b.b.cyl(1.7,-9,3.5),A)
        ears=ears-hole;pads=pads-hole-nut_pocket(head)
        _,y,z=head
        # Rear nut slot is fed from the lateral outside of each boss.
        slot=box([-52.6, y if y>0 else y-10,z-2.9],[-49.8,y+10 if y>0 else y,z+2.9])
        pads=pads-slot
    chassis=connect_components(chassis+pads,move(newkeeps['frame/chest'],N),obstacles['frame/chest'])
    parts['frame/chest']['s']=move(chassis,I)
    housing=housing+move(ears,np.linalg.inv(C))
    add('o22/controller_housing',housing);add('o22/controller_lid',lid)
    pcb=box([0,0,14],[64,60,15.6])-union([kin.b.b.cyl(1.1,13.9,15.7).translate([u,v,0]) for u,v in mounts])
    add('o22/carrier_pcb',pcb,'sensor','O23C_4L_CARRIER_64X60')
    for i,(u,v) in enumerate(mounts):add('o22/carrier_screw_'+str(i),kin.b.b.screw(2,6,3.8,1.5,15.6).translate([u,v,0]),'metal','SELF_TAP_M2_L6')
    for i,(u,v) in enumerate(coverposts):add('o22/lid_screw_'+str(i),kin.b.b.screw(2,6,3.8,1.5,34.2).translate([u,v,0]),'metal','SELF_TAP_M2_L6')
    for i,head in enumerate(body_heads):
        screw,nut=fastener_pair(head)
        for word,s,sku in [('screw',screw,'SCREW_M3_L8'),('nut',nut,'NUT_M3')]:
            parts['o22/backpack_'+word+'_'+str(i)]=dict(key='o22/backpack_'+word+'_'+str(i),s=move(s,I),token='f:chest',body='chest',role='metal',sku=sku,old_id=None)
    for r in layout['footprints']:
        ref=r['reference'];u,v=r['x_mm'],r['y_mm'];bb=np.array(r['bbox_mm']);back=r['side']=='B'
        if ref.startswith('H'):continue
        if ref in ('J1','J2'):height=4;sku='XIAO_HEADER_ENVELOPE'
        elif ref.startswith('J'):height=4.4 if ref!='J3' else 6.5;sku='SH5_CONNECTOR_ENVELOPE' if ref!='J3' else 'PH2_CONNECTOR_ENVELOPE'
        elif ref.startswith('U'):height=1.5;sku='IC_ENVELOPE'
        elif ref=='L1':height=3;sku='INDUCTOR_ENVELOPE'
        else:height=1.5;sku='PASSIVE_ENVELOPE'
        loz,hiz=(14-height,14) if back else (15.6,15.6+height)
        # Courtyard rectangles are conservative package volumes, not artwork.
        add('o22/'+ref,box([bb[0],bb[1],loz],[bb[2],bb[3],hiz]),'sensor',sku)
    add('o22/xiao',box([3.73,4.5,19.6],[21.51,25.5,21.2]),'sensor','XIAO_ESP32S3_ENVELOPE')
    add('o22/xiao_usb',box([8.12,4.5,21.2],[17.12,12,24.66]),'sensor','USB_SOCKET_ENVELOPE')
    # Keep every unaffected mesh byte-for-byte from B2.
    oldnp=np.load(HISTORY/'assembly.npz');olditems={r['key']:r for r in read(HISTORY/'assembly.json')['items']};out={};items=[]
    for i,(key,item) in enumerate(parts.items()):
        item['index']=i
        if key not in CHANGED and not key.startswith('o22/'):
            oi=str(olditems[key]['index']);out[str(i)+'v']=oldnp[oi+'v'];out[str(i)+'f']=oldnp[oi+'f']
        else:out[str(i)+'v'],out[str(i)+'f']=vf(item['s'])
        items.append({k:v for k,v in item.items() if k!='s'})
    np.savez_compressed(B/'assembly.npz',**out);put(B/'assembly.json',dict(revision=REVISION,items=items));put(B/'profiles/device_profile.json',p2)
    keepdata={};oldkeep=np.load(HISTORY/'retained_interfaces.npz')
    for key in oldkeep.files:keepdata[key]=oldkeep[key]
    for key,s in newkeeps.items():keepdata[key+'|v'],keepdata[key+'|f']=vf(s)
    np.savez_compressed(B/'retained_interfaces.npz',**keepdata)
    cfg.update(revision=REVISION,backpack_mount_revision='compact_direct_v3',controller_front_corner_neutral_mm=C[:3,3].tolist(),
        controller_board_mm=[64,60,1.6],controller_board_layout_only=True,user_controller_pcb_not_manufactured=True)
    put(CFG,cfg)
    put(B/'design/compact_revision.json',dict(revision=REVISION,source_geometry_sha256=INPUT_HASH,geometry_sha256=sha(B/'assembly.npz'),
        profile_sha256=sha(B/'profiles/device_profile.json'),changed_carriers=sorted(CHANGED),removed_objects=removed,
        moved_interfaces=patch_records,carrier_build=rows,controller_frame_neutral_mm=C,case_body_mm=[74,70,34.2],
        mount_heads_world_mm=body_heads,lid_boss_version=2,pcb_sha256=layout['pcb_sha256'],pcb_unrouted=True,manufacturing_release=False,
        scope='Prototype layout. Body neutral landmarks retained; intermediate shoulder translations changed. Independent collision, access and manufacturing checks are required.'))
    print('SAVED',sha(B/'assembly.npz'),len(parts),flush=True)


if __name__=='__main__':main()
