"""Prepare O23D with actual hip pivots at UE-proportioned femur origins.

Waist is centered laterally with an 8 mm axial offset for the hip modules.
Chest and descendants rise 22 mm. Other neutral body frames and all raw-driven
orientations stay unchanged. The public assembly is not overwritten here.
"""
from revo23_daily import *
from build_revo23_continuous import load_c,DROOT

COLLAR_CLOCK_DEG=90.

def main():
    archive_c();dst=DROOT/'source';dst.mkdir(parents=True,exist_ok=True)
    p=read(C_HISTORY/'profiles/device_profile.json');p2=copy.deepcopy(p);F=frames(p,p['neutral_raw_deg'])
    deltas={};records=[]
    torso_raise=22.;waist_center_raise=8.
    for j in p2['joints']:
        if j['id'] not in ('waist','chest','thigh_l','thigh_r'):continue
        M=F['f:'+j['parent']]@np.array(j['parent_to_mount_mm']);target=F['f:'+j['child']][:3,3].copy()
        if j['id']=='chest':target[2]+=torso_raise
        if j['id']=='waist':target[2]+=waist_center_raise
        delta=target-M[:3,3];deltas[j['id']]=delta
        A=np.array(j['parent_to_mount_mm']);G=np.array(j['rotor_to_child_mm'])
        A[:3,3]=(np.linalg.inv(F['f:'+j['parent']])@np.r_[target,1])[:3];G[:3,3]=0
        if j['id']=='waist':
            rotor_rotation=F['f:'+j['child']][:3,:3]@G[:3,:3].T
            G[:3,3]-=rotor_rotation.T@np.array([0,0,waist_center_raise])
        j['parent_to_mount_mm']=A.tolist();j['rotor_to_child_mm']=G.tolist()
        records.append(dict(joint=j['id'],old_world_center_mm=M[:3,3],new_world_center_mm=target,rigid_interface_shift_mm=delta))
    j=next(j for j in p2['joints'] if j['id']=='forearm_r.twist')
    R=np.eye(4);R[:3,:3]=kin.b.b.rot(2,180)
    j['parent_to_mount_mm']=(np.array(j['parent_to_mount_mm'])@R).tolist()
    j['rotor_to_child_mm']=(np.linalg.inv(R)@np.array(j['rotor_to_child_mm'])).tolist()
    deltas[j['id']]=np.zeros(3)
    for j in p2['joints']:
        if j['id'] not in ('clavicle_l.protract','clavicle_r.protract'):continue
        C=np.eye(4);C[:3,:3]=kin.b.b.rot(2,COLLAR_CLOCK_DEG)
        j['parent_to_mount_mm']=(np.array(j['parent_to_mount_mm'])@C).tolist()
        j['rotor_to_child_mm']=(np.linalg.inv(C)@np.array(j['rotor_to_child_mm'])).tolist()
        deltas[j['id']]=np.zeros(3)
    for j in p2['joints']:
        if j['id'] not in ('forearm_l.twist','forearm_r.twist'):continue
        Z=np.eye(4);Z[2,3]=-8.
        j['parent_to_mount_mm']=(np.array(j['parent_to_mount_mm'])@Z).tolist()
        j['rotor_to_child_mm']=(np.linalg.inv(Z)@np.array(j['rotor_to_child_mm'])).tolist()
        deltas[j['id']]=np.zeros(3)
    N=frames(p2,p2['neutral_raw_deg'])
    for j in p2['joints']:
        j['neutral_origin_mm']=(N['f:'+j['parent']]@np.array(j['parent_to_mount_mm']))[:3,3].tolist()
    upper={'chest'}
    for _ in p2['joints']:upper.update(j['child'] for j in p2['joints'] if j['parent'] in upper)
    upper.update(m['id'] for m in p2['fixed_markers'] if m['parent'] in upper)
    expected={k:v.copy() for k,v in F.items() if k.startswith('f:')}
    for k,v in expected.items():
        if k[2:] in upper or k.startswith('f:hand_tip_'):v[2,3]+=torso_raise
    err=max(np.max(abs(N[k]-v)) for k,v in expected.items())
    assert err<1e-8,err
    p2['profile_id']='o23d_continuous_walls_centered_torso_1p4'
    p2['o23_design']['centered_torso_joints']=[r for r in records if r['joint'] in ('waist','chest')]
    p2['o23_design']['centered_hip_joints']=[r for r in records if r['joint'].startswith('thigh_')]
    p2['o23_design']['hip_placement_note']='Physical hip pivots coincide with the UE-proportioned femur origins. The inherited +/-22.4 mm outward hip offset is removed; neutral leg landmarks and raw orientations stay unchanged.'
    p2['o23_design']['neutral_body_frames_preserved']=False
    p2['o23_design']['upper_torso_raise_mm']=torso_raise
    p2['o23_design']['waist_center_axial_offset_mm']=waist_center_raise
    p2['o23_design']['reclocked_single_axis_joints']=[dict(joint='forearm_r.twist',clocking_deg=180.,
        reason='Move existing sensor carrier clear of wrist flexion; coaxial mount and inverse child frame preserve all body transforms.')]
    p2['o23_design']['reclocked_single_axis_joints'].extend(
        dict(joint='clavicle_'+side+'.protract',clocking_deg=COLLAR_CLOCK_DEG,
             reason='Place collar PCB and clip hardware away from the shoulder sweep; inverse child frame preserves body motion.')
        for side in ('l','r'))
    p2['o23_design']['axially_shifted_single_axis_joints']=[
        dict(joint='forearm_'+side+'.twist',shift_along_local_z_mm=-8.,
             reason='8 mm toward elbow creates wrist clearance; conjugate axial translations preserve all body transforms.')
        for side in ('l','r')]
    p2['o23_design']['upper_torso_bodies']=sorted(upper)
    p2['o23_design']['positional_motion_note']='Hip pivots at femur origins; waist centered laterally and 8 mm above its body reference; chest and descendants raised 22 mm for physical separation. Original neck pivot and all raw-driven orientations retained.'
    parts=load_c();kz=np.load(C_HISTORY/'retained_interfaces.npz');out={};losses=[];separate={}
    base,_,_=load_baseline();O=frames(kin.profile,kin.profile['neutral_raw_deg'])
    for key,part in parts.items():
        if part['role']!='structure':continue
        keep=solid(kz[key+'|v'],kz[key+'|f']);world=move(keep,F[part['token']])
        anchors=interface_anchors(part['body'],p,F)
        if not any(a['joint'] in deltas for a in anchors):
            out[key+'|v'],out[key+'|f']=vf(keep);continue
        # Re-extract each unscaled F7 attachment before translating it.
        # Cutting the already-unioned O23 lands by a second Voronoi partition
        # can split a functional flange and move its halves differently.
        original=move(base[key]['s'],O[base[key]['token']])
        if part['body']=='chest':
            controller=np.array(read(H/'bench/revO22/mechanical/assembly_metadata.json')['controller_frame'])
            original=original-move(controller_shell(),controller)
        old_anchors=interface_anchors(part['body'],kin.profile,O)
        new_anchors={a['joint']:a for a in interface_anchors(part['body'],p2,N)}
        cells=[];input_volume=0
        for a in old_anchors:
            if a['joint'] not in new_anchors:continue
            if part['body']=='chest' and a['joint'].startswith('clavicle_'):
                # Compact O23C already replaced the old extended collar root.
                # Preserve its explicitly cropped bearing/screw land, rather
                # than accidentally restoring the discarded F7 connecting arm.
                cj=next(j for j in p['joints'] if j['id']==a['joint'])
                nj=next(j for j in p2['joints'] if j['id']==a['joint'])
                CM=F['f:'+cj['parent']]@np.array(cj['parent_to_mount_mm'])
                NM=N['f:'+nj['parent']]@np.array(nj['parent_to_mount_mm'])
                cell=move(world,np.linalg.inv(CM))^box([-19.5,-19.5,-11.5],[15.,10.,14.5])
                input_volume+=cell.volume();cells.append(move(cell,NM));continue
            pt=a['point'];cell=original^ball(pt,a['guard_radius']+10.)
            for other in old_anchors:
                d=other['point']-pt
                if np.linalg.norm(d)<1e-8:continue
                normal=d/np.linalg.norm(d)
                cell=cell.split_by_plane(normal,float(normal@((pt+other['point'])/2)))[1]
            old_j=next(j for j in kin.profile['joints'] if j['id']==a['joint'])
            new_j=next(j for j in p2['joints'] if j['id']==a['joint'])
            old_M=O['f:'+old_j['parent']]@np.array(old_j['parent_to_mount_mm'])
            new_M=N['f:'+new_j['parent']]@np.array(new_j['parent_to_mount_mm'])
            moved_cell=move(cell,new_M@np.linalg.inv(old_M))
            input_volume+=cell.volume();cells.append(moved_cell)
            if part['body'].startswith('forearm_') and a['joint'].startswith('forearm_'):
                tag=key+'|'+a['joint'];local=move(moved_cell,np.linalg.inv(N[part['token']]))
                separate[tag+'|v'],separate[tag+'|f']=vf(local)
        if part['body'].startswith('forearm_'):
            # Keep the complete wrist interface separately; a midpoint split
            # of the union would mix its tall attachment tail into the twist
            # land on this compact forearm.
            side=part['body'][-1];donor=base['frame/calf_l']
            dj=next(j for j in kin.profile['joints'] if j['id']=='foot_l')
            DM=O['f:'+dj['parent']]@np.array(dj['parent_to_mount_mm'])
            patch=move(donor['s'],np.linalg.inv(DM)@O[donor['token']])^ball([0,0,0],35)
            wj=next(j for j in p2['joints'] if j['id']=='wrist_'+side)
            WM=N['f:'+wj['parent']]@np.array(wj['parent_to_mount_mm'])
            moved_cell=move(patch,WM);cells.append(moved_cell);input_volume+=patch.volume()
            tag=key+'|wrist_'+side;local=move(moved_cell,np.linalg.inv(N[part['token']]))
            separate[tag+'|v'],separate[tag+'|f']=vf(local)
        moved=move(union(cells),np.linalg.inv(N[part['token']]))
        out[key+'|v'],out[key+'|f']=vf(moved)
        losses.append(dict(key=key,independent_F7_interface_volume_mm3=input_volume,moved_union_volume_mm3=moved.volume(),
            source='Individual original F7 lands; compact chest/collar lands retain the O23C joint-local precision boxes. No discarded F7 collar connecting arm is restored.'))
    np.savez_compressed(dst/'retained_interfaces.npz',**out)
    np.savez_compressed(dst/'separate_forearm_lands.npz',**separate)
    put(dst/'device_profile.json',p2)
    cfg=read(dst/'parameters.json') if (dst/'parameters.json').exists() else read(C_HISTORY/'parameters.json')
    cfg['revision']='O23D-continuous-walls-20261020'
    cfg['contour_adjustments']={
        'chest':{'ap_scale':1.08,'lateral_scale':.90},
        'waist':{'ap_scale':1.,'lateral_scale':.96},
        'pelvis':{'ap_scale':1.08},
        'forearm_l':{'ap_add_mm':2.,'lateral_add_mm':1.},
        'forearm_r':{'ap_add_mm':2.,'lateral_add_mm':1.},
        'head':{'ap_add_mm':3.,'lateral_add_mm':2.}}
    cfg['contour_adjustments']['waist']['longitudinal_extension_mm']=torso_raise
    cfg['upper_torso_raise_mm']=torso_raise
    cfg['motion_acceptance_policy']='ordinary_adjacent'
    put(dst/'parameters.json',cfg)
    put(dst/'relocation.json',dict(source_geometry_sha256=C_HASH,joints=records,
        maximum_neutral_body_frame_error_after_declared_raise=err,upper_torso_raise_mm=torso_raise,
        waist_center_axial_offset_mm=waist_center_raise,interfaces=losses,hardware_scale=1.,
        positional_trajectories_changed=True,manufacturing_release=False))
    put(dst/'active_source.json',dict(torso_centers='Waist and chest centered; neck retains O23C pivot',
        hip_centers='Both physical pivots moved inward by 22.4 mm to the UE-proportioned femur origins',
        interface_source='Individual F7 lands extracted before translation',
        right_wrist='Mirrored printed donor; original raw orientation profile',
        opening_assignment='Fixed to corresponding joint, independent of contact height'))
    print('PREPARED',records,'neutral error',err,flush=True)


if __name__=='__main__':main()
