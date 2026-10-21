"""Audit actual hip pivots and cross-joint packing after removing O22 offsets."""
from build_revo23_continuous import *
import itertools


def main():
    p=read(DROOT/'source/device_profile.json');parts=load_c()
    old=read(C_HISTORY/'profiles/device_profile.json');neutral=p['neutral_raw_deg']
    F=frames(p,neutral);O=frames(old,neutral)
    refpath=H/'generated/revE/quinn/neutral_landmarks.json'
    reference=read(refpath)['bone_landmarks_mm']
    reference_scale=float(np.linalg.norm(F['f:elbow_l'][:3,3]-F['f:upperarm_l'][:3,3])/
        np.linalg.norm(np.array(reference['lowerarm_l'])-reference['upperarm_l']))
    records=[]
    for side in ('l','r'):
        jid='thigh_'+side;j=next(j for j in p['joints'] if j['id']==jid)
        jo=next(j for j in old['joints'] if j['id']==jid)
        actual=(F['f:'+j['parent']]@np.array(j['parent_to_mount_mm']))[:3,3]
        before=(O['f:'+jo['parent']]@np.array(jo['parent_to_mount_mm']))[:3,3]
        target=np.array(reference[jid])*reference_scale
        records.append(dict(joint=jid,actual_center_mm=actual,target_femur_origin_mm=target,
                            old_physical_center_mm=before,error_mm=float(np.linalg.norm(actual-target))))
    # Different complete hip/waist modules must be assemblable even when their
    # bases share a rigid pelvis frame. Do not hide these as rigid attachments.
    selected={k:v for k,v in parts.items()
              if k.split('/')[0] in ('thigh_l','thigh_r','waist') and v['role']!='structure'}
    keys=list(selected);bounds={}
    for k,v in selected.items():
        bb=v['s'].bounding_box();bounds[k]=np.array(list(itertools.product(*zip(bb[:3],bb[3:]))))
    spec=read(B/'profiles/daily_poses.json')
    poses={n:q for n,q in spec['poses'].items()
           if n in ('A_STAND_35','N_NEUTRAL') or n.startswith(('thigh_','daily_'))}
    cache={};hits=[];maximum=0.
    for name,q in poses.items():
        ff=frames(p,q);world_bounds={}
        for k,v in selected.items():
            M=ff[v['token']];vv=bounds[k]@M[:3,:3].T+M[:3,3]
            world_bounds[k]=np.r_[vv.min(0),vv.max(0)]
        for a,b in itertools.combinations(keys,2):
            if a.split('/')[0]==b.split('/')[0]:continue
            aa,bb=world_bounds[a],world_bounds[b]
            if np.any(np.minimum(aa[3:],bb[3:])-np.maximum(aa[:3],bb[:3])<=0):continue
            T=np.linalg.inv(ff[selected[a]['token']])@ff[selected[b]['token']]
            sig=(a,b,tuple(np.round(T,7).ravel()))
            if sig not in cache:cache[sig]=max(0.,float((selected[a]['s']^move(selected[b]['s'],T)).volume()))
            volume=cache[sig];maximum=max(maximum,volume)
            if volume>.05:hits.append(dict(pose=name,pair=[a,b],overlap_mm3=volume))
    # Hip relocation cannot invalidate shoulder coordination: check every
    # upper-body rigid transform in the existing coordinated pose set.
    previous=read(B/'profiles/daily_poses.json')
    torso_only=copy.deepcopy(p)
    for j in torso_only['joints']:
        if j['id'].startswith('thigh_'):
            donor=next(jj for jj in old['joints'] if jj['id']==j['id'])
            j['parent_to_mount_mm']=donor['parent_to_mount_mm']
            j['rotor_to_child_mm']=donor['rotor_to_child_mm']
    upper=set(p['o23_design']['upper_torso_bodies'])
    error=0.
    for q in previous['poses'].values():
        a=frames(torso_only,q);b=frames(p,q)
        error=max(error,max(np.max(abs(a['f:'+body]-b['f:'+body])) for body in upper))
    assert error<1e-9
    previous['profile_sha256']=sha(DROOT/'source/device_profile.json')
    put(B/'profiles/daily_poses.json',previous)
    report=dict(profile_sha256=profile_signature(p),hip_centers=records,
                reference_file=refpath.relative_to(H).as_posix(),reference_file_sha256=sha(refpath),
                quinn_reference_scale=reference_scale,
                physical_center_spacing_mm=float(np.linalg.norm(records[0]['actual_center_mm']-records[1]['actual_center_mm'])),
                old_center_spacing_mm=float(np.linalg.norm(records[0]['old_physical_center_mm']-records[1]['old_physical_center_mm'])),
                pose_count=len(poses),cross_module_overlap_tolerance_mm3=.05,
                cross_module_contacts=hits,maximum_cross_module_overlap_mm3=maximum,
                shoulder_coordination_transform_error=error,
                scope='Actual two hip modules and waist module, including their rigid bases; structural walls checked separately.',
                source_hardware_overrides_sha256=sha(DROOT/'source/part_overrides.npz'),
                passed=not hits and all(r['error_mm']<1e-8 for r in records),
                continuous_motion_proven=False,manufacturing_release=False)
    put(B/'verification/hip_centers.json',report)
    print('HIP AUDIT',report['passed'],'spacing',report['physical_center_spacing_mm'],
          'poses',len(poses),'cross-module contacts',len(hits),flush=True)
    for h in sorted(hits,key=lambda r:-r['overlap_mm3'])[:15]:print(h,flush=True)


if __name__=='__main__':main()
