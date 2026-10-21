"""Independent numeric gates on delivered O23 geometry. No physical PASS implied."""
from present_revo23 import *
import itertools,time

def kinematics(p):
    rng=np.random.default_rng(230020);samples=[kin.profile['neutral_raw_deg'],read(B/'profiles/default_pose.json')['raw_deg']]
    samples += [{k:float(rng.uniform(*lim))for k,lim in p['raw_limits_deg'].items()}for _ in range(32)]
    position=rotation=0
    clocked={r['joint'] for r in p['o23_design'].get('reclocked_single_axis_joints',[])}
    clocked_owners={k for k in frames(p,p['neutral_raw_deg']) if any(k.startswith('j:'+j+':') for j in clocked)}
    shifted={r['joint'] for r in p['o23_design'].get('axially_shifted_single_axis_joints',[])}
    shifted_owners={k for k in frames(p,p['neutral_raw_deg']) if any(k.startswith('j:'+j+':') for j in shifted)}
    redesigned={'f:hand_l','f:hand_r','f:hand_tip_l','f:hand_tip_r'}
    if p['o23_design'].get('compact_clavicles'):
        branches={'clavicle_l.protract_frame','clavicle_r.protract_frame'}
        for _ in p['joints']:
            branches.update(j['child'] for j in p['joints'] if j['parent'] in branches)
        branches.update(m['id'] for m in p['fixed_markers'] if m['parent'] in branches)
        redesigned.update('f:'+name for name in branches)
        redesigned.update(k for k in frames(p,p['neutral_raw_deg']) if k.startswith('j:clavicle_') or any(k.startswith('j:'+j['id']+':') for j in p['joints'] if j['parent'] in branches))
    centered=p['o23_design'].get('centered_torso_joints',[])+p['o23_design'].get('centered_hip_joints',[])
    if centered:
        moved={x['joint'] for x in centered}
        branches={j['child'] for j in p['joints'] if j['id'] in moved}
        for _ in p['joints']:
            branches.update(j['child'] for j in p['joints'] if j['parent'] in branches)
        branches.update(m['id'] for m in p['fixed_markers'] if m['parent'] in branches)
        redesigned.update('f:'+name for name in branches)
        redesigned.update(k for k in frames(p,p['neutral_raw_deg']) if any(k.startswith('j:'+j['id']+':') for j in p['joints'] if j['id'] in moved or j['parent'] in branches))
    neutral_old=frames(kin.profile,p['neutral_raw_deg']);neutral_new=frames(p,p['neutral_raw_deg'])
    redesigned.update(clocked_owners)
    redesigned.update(shifted_owners)
    neutral_error=max(float(np.max(abs(neutral_old[k][:3,3]*p['o23_design']['scale']-neutral_new[k][:3,3]))) for k in set(neutral_old)&set(neutral_new) if k.startswith('f:') and k not in ('f:hand_l','f:hand_r','f:hand_tip_l','f:hand_tip_r'))
    prior_error=None
    if centered:
        from revo23_daily import C_HISTORY
        prior=read(C_HISTORY/'profiles/device_profile.json')
        C=frames(prior,p['neutral_raw_deg'])
        for body in p['o23_design'].get('upper_torso_bodies',[]):
            C['f:'+body][2,3]+=p['o23_design'].get('upper_torso_raise_mm',0)
        prior_error=max(float(np.max(abs(C[k]-neutral_new[k]))) for k in C if k.startswith('f:'))
    for q in samples:
        a=frames(kin.profile,q);b=frames(p,q)
        for k in set(a)&set(b):
            if k not in redesigned:
                position=max(position,float(np.max(np.abs(a[k][:3,3]*p['o23_design']['scale']-b[k][:3,3]))))
            if k not in clocked_owners:
                rotation=max(rotation,float(np.max(np.abs(a[k][:3,:3]-b[k][:3,:3]))))
    return dict(samples=len(samples),maximum_scaled_center_error_mm=position,maximum_rotation_matrix_error=rotation,
        neutral_body_center_error_mm_excluding_redesigned_wrists=neutral_error,
        shoulder_motion_translation_redesigned=bool(p['o23_design'].get('compact_clavicles')),
        torso_motion_translation_redesigned=bool(centered),
        physical_hip_centers_redesigned=bool(p['o23_design'].get('centered_hip_joints')),
        maximum_neutral_body_frame_error_vs_O23C=prior_error,
        neutral_reference_note='O23C plus the explicitly declared upper_torso_raise_mm',
        upper_torso_raise_mm=p['o23_design'].get('upper_torso_raise_mm',0),
        raw_order_unchanged=p['raw_order']==kin.profile['raw_order'],raw_limits_unchanged=p['raw_limits_deg']==kin.profile['raw_limits_deg'],
        reclocked_joint_owner_frames=sorted(clocked_owners),
        neutral_values_unchanged=p['neutral_raw_deg']==kin.profile['neutral_raw_deg'],
        redesigned_center_exclusions=sorted(redesigned),rotation_scope='Every retained body including both hands; 34 multi-axis samples',
        passed=position<1e-8 and rotation<1e-10 and (prior_error is None or prior_error<1e-8)
            and p['raw_order']==kin.profile['raw_order'] and p['raw_limits_deg']==kin.profile['raw_limits_deg']
            and p['neutral_raw_deg']==kin.profile['neutral_raw_deg'])

def geometric(parts,p):
    ff=frames(p,read(B/'profiles/default_pose.json')['raw_deg']);boxes=[];rows=[]
    for k,part in parts.items():
        s=part['s'];M=ff[part['token']];boxes.append(move(s,M).bounding_box())
        modified_wrist=k.startswith('wrist_r/') and part['role'] in ('print','frame')
        if part['role']!='structure' and not modified_wrist and k not in ('o22/controller_housing','o22/backpack_support','o22/controller_lid'):continue
        v,f=vf(s);mesh=trimesh.Trimesh(v,f,process=False)
        # Oriented bounding box is a geometric bed-fit screen, not a sliced plate.
        T,ext=trimesh.bounds.oriented_bounds(mesh,angle_digits=1)
        # Also try a diagonal bed placement. An OBB edge >170 mm alone does
        # not mean the part is too large for a 170 mm square.
        candidates=[]
        for vertical in range(3):
            xy=[i for i in range(3) if i!=vertical]
            Q=np.eye(3)[[*xy,vertical]]
            if np.linalg.det(Q)<0:Q[0]*=-1
            for angle in np.linspace(0,90,19):
                Q2=kin.b.b.rot(2,float(angle))@Q
                vm=v@T[:3,:3].T+T[:3,3];vm=vm@Q2.T
                extent=np.ptp(vm,axis=0)
                penalty=max(extent)+.02*extent[2]
                A=np.eye(4);A[:3,:3]=Q2@T[:3,:3];A[:3,3]=Q2@T[:3,3]-vm.min(0)+[5,5,0]
                candidates.append((penalty,extent,A))
        _,bed,bedmatrix=min(candidates,key=lambda x:x[0])
        rows.append(dict(key=k,components=len([x for x in s.decompose() if x.volume()>1e-4]),
            watertight=bool(mesh.is_watertight),winding_consistent=bool(mesh.is_winding_consistent),
            volume_mm3=s.volume(),oriented_box_mm=ext,bed_oriented_extent_mm=bed,print_matrix=bedmatrix,
            within_170mm_box=bool(max(bed)<=170),
            solid_PLA_equivalent_g=s.volume()/1000*1.24))
    boxes=np.array(boxes);lo=boxes[:,:3].min(0);hi=boxes[:,3:].max(0)
    return dict(rows=rows,height_mm=hi[2]-lo[2],bounds_mm=[lo,hi],height_under_800mm=bool(hi[2]-lo[2]<800),
        invalid_parts=[r['key']for r in rows if r['components']!=1 or not r['watertight']],
        oversize_parts=[r['key']for r in rows if not r['within_170mm_box']],
        mass_note='Solid-volume equivalent for the explicitly modeled walls/lands. Not slicer filament or measured mass.')

def cases(p,suite):
    q=read(B/'profiles/default_pose.json')['raw_deg'];out={'A_STAND_35':q,'N_NEUTRAL':p['neutral_raw_deg']}
    for name in ('left_elbow','asymmetric','right_forearm'):
        out[name]=read(H/'bench/revO22/ue'/f'{name}.payload.json')['joint_angles_deg']
    if suite=='full':
        for rid,limits in p['raw_limits_deg'].items():
            for angle in np.linspace(*limits,7):out[rid+'@'+str(round(float(angle),4))]=dict(q,**{rid:float(angle)})
        rng=np.random.default_rng(20261020)
        for n in range(16):out['combined_'+str(n)]={k:float(rng.uniform(*v))for k,v in p['raw_limits_deg'].items()}
    return out

def motion(parts,base,p,suite,focus_override=None):
    focus=focus_override if focus_override is not None else {k for k,v in parts.items() if v['role']=='structure' or k.startswith(('wrist_','o22/'))};keys=list(parts)
    if focus_override is None and p['o23_design'].get('compact_clavicles'):
        # Relocated collar axes move every downstream arm object. Include their
        # hardware-to-hardware pairs, not only the new carrier surfaces.
        branches={'clavicle_l.protract_frame','clavicle_r.protract_frame'}
        for _ in p['joints']:branches.update(j['child'] for j in p['joints'] if j['parent'] in branches)
        moved_joints={j['id'] for j in p['joints'] if j['parent'] in branches or j['id'].startswith('clavicle_')}
        focus.update(k for k,v in parts.items() if (v['token'].startswith('f:') and v['token'][2:] in branches) or (v['token'].startswith('j:') and v['token'].split(':')[1] in moved_joints))
    local_corners={};oldcorners={}
    for k,v in parts.items():
        b=v['s'].bounding_box();local_corners[k]=np.array(list(itertools.product(*zip(b[:3],b[3:]))))
    cache={};oldcache={};rows=[];start=time.time();hits=[]
    for number,(name,q) in enumerate(cases(p,suite).items()):
        F=frames(p,q);O=frames(kin.profile,q);bounds=[]
        donor_frames={}
        for side in ('l','r'):
            dq=dict(q);dq['foot_l/r0']=q['hand_'+side+'.deviate/r0'];dq['foot_l/r1']=q['hand_'+side+'.flex/r0']
            donor_frames[side]=frames(kin.profile,dq)
        def donor(k,side):
            if k.startswith('wrist_'+side+'/'):return parts[k]['source_key']
            if k=='frame/forearm_'+side:return 'frame/calf_l'
            if k=='frame/hand_'+side:return 'frame/foot_l'
            return None
        for k in keys:
            M=F[parts[k]['token']];c=local_corners[k]@M[:3,:3].T+M[:3,3];bounds.append(np.r_[c.min(0),c.max(0)])
        bounds=np.array(bounds);contacts=[]
        for i,k in enumerate(keys):
            if k not in focus:continue
            mask=np.all(np.minimum(bounds[i,3:],bounds[:,3:])-np.maximum(bounds[i,:3],bounds[:,:3])>1e-5,axis=1)
            for j in np.flatnonzero(mask):
                other=keys[j]
                if other==k or (other in focus and j<i):continue
                rel=np.linalg.inv(F[parts[k]['token']])@F[parts[other]['token']]
                ck=(k,other,tuple(np.round(rel,7).ravel()))
                if ck not in cache:cache[ck]=max(0.,float((parts[k]['s']^move(parts[other]['s'],rel)).volume()))
                volume=cache[ck]
                if volume<.03:continue
                old=0.;bk=k;bo=other;comparison=O
                if k=='o22/controller_housing' and other.startswith('o22/') and other in base:bk='frame/chest'
                if other=='o22/controller_housing' and k.startswith('o22/') and k in base:bo='frame/chest'
                for side in ('l','r'):
                    dk,do=donor(k,side),donor(other,side)
                    if dk and do:
                        valid=all(kin.profile['raw_limits_deg'][foot][0]<=q[hand]<=kin.profile['raw_limits_deg'][foot][1]
                            for foot,hand in [('foot_l/r0','hand_'+side+'.deviate/r0'),('foot_l/r1','hand_'+side+'.flex/r0')])
                        if valid:bk,bo,comparison=dk,do,donor_frames[side]
                        else:bk,bo='OUTSIDE_DONOR_RANGE/'+dk,'OUTSIDE_DONOR_RANGE/'+do
                        break
                if bk in base and bo in base:
                    relold=np.linalg.inv(comparison[base[bk]['token']])@comparison[base[bo]['token']]
                    ok=(bk,bo,tuple(np.round(relold,7).ravel()))
                    if ok not in oldcache:oldcache[ok]=max(0.,float((base[bk]['s']^move(base[bo]['s'],relold)).volume()))
                    old=oldcache[ok]
                # Four explicitly modelled M2 self-tapping lid screws engage
                # 1.7 mm pilot bores by 3.8 mm. The nominal 3.31 mm3 radial
                # thread engagement is intentional; cap it so extra contact
                # elsewhere cannot be hidden by this allowance.
                pair={k,other};lid_mate=next((x for x in pair if x.startswith('o22/lid_screw_')),None)
                intended=bool('o22/controller_housing' in pair and lid_mate and volume<=3.5 and parts[k]['token']==parts[other]['token'])
                rec=dict(pair=[k,other],overlap_mm3=volume,baseline_overlap_mm3=old,
                    increased=bool(volume>old+.05 and not intended),same_rigid_owner=parts[k]['token']==parts[other]['token'],baseline_comparison_pair=[bk,bo])
                if intended:rec['intended_fit']='M2 self-tap in 1.7 mm pilot; nominal 3.31 mm3, capped at 3.5 mm3; physical fit untested'
                contacts.append(rec)
                if rec['increased']:hits.append(dict(pose=name,**rec))
        rows.append(dict(pose=name,contacts=contacts))
        print('MOTION',number,name,'contacts',len(contacts),'increased',sum(x['increased']for x in contacts),'sec',round(time.time()-start),flush=True)
        if number%10==0:put(B/'verification'/('motion_'+suite+'.progress.json'),dict(completed=number+1,unique_checks=len(cache),increased=len(hits)))
    return dict(suite=suite,geometry_sha256=sha(B/'assembly.npz'),pose_count=len(rows),unique_solid_checks=len(cache),rows=rows,
        new_or_increased_contacts=hits,passed=not hits,continuous_full_range_proven=False,
        scope='Every new carrier, every new wrist object and every relocated controller object versus all actual objects. Same-pair O22 contacts listed; wrist-family internal contacts compare the exact F7 ankle donor at the same two angles. Baseline contacts never suppress a whole pose.',
        contact_tolerance_mm3=.03,volume_increase_tolerance_mm3=.05,clearance_2mm_proven=False)

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--suite',choices=['quick','full'],default='quick');ap.add_argument('--geometry-only',action='store_true');args=ap.parse_args()
    parts=load_current();base,_,_=load_baseline();p=read(B/'profiles/device_profile.json')
    report=dict(revision=REV,geometry_sha256=sha(B/'assembly.npz'),configuration_sha256=sha(CFG),kinematics=kinematics(p),geometry=geometric(parts,p),
        physical_tested=False,manufacturing_release=False)
    put(B/'verification/geometry.json',report);print('HEIGHT',report['geometry']['height_mm'],'INVALID',report['geometry']['invalid_parts'],'OVERSIZE',report['geometry']['oversize_parts'],flush=True)
    if args.geometry_only:return
    checks=motion(parts,base,p,args.suite);put(B/'verification'/('motion_'+args.suite+'.json'),checks)
    if args.suite=='full':
        # The full run contains the quick suite verbatim; reuse those exact
        # checks instead of asking a later packaging step to trust a stale run.
        quick_names=set(cases(p,'quick'));quick=dict(checks)
        quick.update(suite='quick',derived_from='motion_full.json',
            rows=[r for r in checks['rows']if r['pose']in quick_names],
            new_or_increased_contacts=[r for r in checks['new_or_increased_contacts']if r['pose']in quick_names],
            pose_count=len(quick_names),unique_solid_checks=None)
        quick['passed']=not quick['new_or_increased_contacts']
        put(B/'verification/motion_quick.json',quick)
    print('MOTION RESULT',checks['passed'],len(checks['new_or_increased_contacts']),flush=True)

if __name__=='__main__':main()
