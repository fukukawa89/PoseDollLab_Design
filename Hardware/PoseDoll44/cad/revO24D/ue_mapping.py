"""Reconstruct all UE N-pose rotations; no missing orientation defaults.
Offline component transforms in original-asset UE centimetres. No UE runtime claim.
"""
from fullbody import *
from scipy.spatial.transform import Rotation

def main():
    ref,ch,scale=a.reference(); swap=a.ue.SWAP
    pts={n:np.array(v) for n,v in ref['points_mm'].items()}
    rn={n:swap@ch['neutral'][i][:3,:3]@swap.T for i,n in enumerate(ch['names'])}
    primary={'pelvis':'pelvis','spine_01':'pelvis','spine_02':'lumbar_yaw','spine_03':'lumbar_yaw','spine_04':'thorax_flex','spine_05':'thorax_flex','neck_01':'neck_yaw','neck_02':'neck_yaw','head':'head'}
    endpoints={'pelvis':'pelvis','spine_02':'lumbar_yaw','spine_04':'thorax_flex','neck_01':'neck_yaw','head':'head'}
    for s in ['l','r']:
        primary.update({b+'_'+s:s+'_'+fr for b,fr in [('clavicle','clavicle_elevate'),('upperarm','upperarm_roll'),('lowerarm','forearm_roll'),('hand','wrist_flex'),('thigh','hip_roll'),('calf','knee_flex'),('foot','ankle_flex'),('ball','toe_flex')]})
        endpoints.update({b+'_'+s:s+'_'+fr for b,fr in [('clavicle','clavicle_elevate'),('upperarm','upperarm_roll'),('lowerarm','elbow_flex'),('hand','wrist_flex'),('thigh','hip_roll'),('calf','knee_flex'),('foot','ankle_flex'),('ball','toe_flex')]})
    maps=[];sources={}
    for i,n in enumerate(ch['names']):
        parent=ch['names'][ch['parents'][i]] if ch['parents'][i]>=0 else None
        sources[n]=primary.get(n,sources.get(parent,'pelvis'))
        maps.append(dict(bone=n,parent=parent,frame=sources[n],mode='physical_group' if n in primary else 'rigid_derived_from_parent',neutral_rotation_RH=rn[n],neutral_position_mm=pts[n],neutral_parent_translation_mm=rn[parent].T@(pts[n]-pts[parent]) if parent else pts[n],note='Rigid fingers and helper bones; no additional sensor' if n not in primary else 'Neutral mount clock removed by F(q) R * F(0) R transpose'))
    frames_out={};max_center=0;max_round=0;max_ref=0;worst='';checks=[]
    for label,pose in {**poses(),'reference_N':dict(angles={})}.items():
        F=frames(pose['angles']);g={};records={}
        for row in maps:
            n=row['bone'];par=row['parent'];fr=row['frame']
            r=F[fr][:3,:3]@F0[fr][:3,:3].T@rn[n]
            p=g[par][:3,3]+g[par][:3,:3]@row['neutral_parent_translation_mm'] if par else pts[n]
            g[n]=T(p,r)
            ueR=swap@r@swap.T;uep=swap@(p-ref['floor_shift_mm'])/(10*ref['uniform_scale'])
            quat=Rotation.from_matrix(ueR).as_quat();rr=swap@Rotation.from_quat(quat).as_matrix()@swap.T
            max_round=max(max_round,np.max(abs(rr-r)))
            records[n]=dict(translation_cm=uep,rotation_xyzw=quat,scale=[1,1,1])
            if label=='reference_N':max_ref=max(max_ref,np.linalg.norm(uep-ch['neutral'][ch['index'][n]][:3,3]))
        for n,fr in endpoints.items():
            e=float(np.linalg.norm(g[n][:3,3]-F[fr][:3,3]))
            if e>max_center:max_center=e;worst=label+'/'+n
        frames_out[label]=dict(angles_deg=pose['angles'],bones_component_space=records)
        checks.append(dict(pose=label,max_joint_center_error_mm=max(float(np.linalg.norm(g[n][:3,3]-F[fr][:3,3])) for n,fr in endpoints.items())))
    # The swap is a reflection: positions transform once; rotations require conjugation.
    put(OUT/'reference/full_UE_N_pose.json',dict(asset=ref['asset'],source_files=ref['source_files'],bones=maps,uniform_scale=ref['uniform_scale'],floor_shift_mm=ref['floor_shift_mm']))
    put(OUT/'profiles/UE_component_pose_examples.json',dict(format='UE component space, original asset cm, quaternion xyzw, left-handed basis',neutral_pose='neutral = A, bilateral shoulder abduction 45 degrees',reference_N_is_not_neutral=True,runtime_tested=False,poses=frames_out))
    channels=[];idx=0
    for ax in PROFILE['axes']:
        if '_wrist_' in ax['id']:continue
        channels.append(dict(raw_channel=idx,id=ax['id'],kind='single_axis_angle',physical_axis=ax['axis'],limits_deg=ax['limits_deg'],A_zero_offset_deg=NEUTRAL_ANGLES.get(ax['id'],0),calibration='angle = A_zero_offset_deg + sign * unwrap(raw - raw_at_A); radians/degrees explicit; fixed -90 forearm mounting clock is applied only in FK'));idx+=1
    for s in ['l','r']:
        channels.append(dict(raw_channels=list(range(idx,idx+3)),id=s+'_wrist_field',kind='Bx_By_Bz',solved_axes=[s+'_wrist_deviation',s+'_wrist_flex'],model='two-DOF bounded calibrated field lookup; not three independent joint angles'));idx+=3
    put(OUT/'profiles/channel_map.json',dict(physical_dof=40,scalar_channels=idx,single_axis_devices=36,field_devices=2,channels=channels,firmware_compatible_with_O22_46ch=False,calibration_pose='A neutral',neutral_angles_deg=NEUTRAL_ANGLES,packet_candidate=dict(schema='POSEDOLL_O24D_40_A_2',units='deg',angles={a['id']:NEUTRAL_ANGLES.get(a['id'],0) for a in PROFILE['axes']},sequence=0,calibrated=False),note='Sensor zero is A; packet angles retain anatomical N-reference coordinates. Offline interface only; real magnetic calibration and UE runtime pending.'))
    put(OUT/'verification/ue_mapping.json',dict(status='PASS' if max_center<1e-6 and max_ref<1e-6 and max_round<1e-10 else 'FAIL',all_bones=len(maps),missing_rotations=0,physical_centres=len(endpoints),neutral_pose='A',neutral_angles_deg=NEUTRAL_ANGLES,max_physical_center_error_mm=max_center,worst=worst,reference_N_original_asset_error_cm=max_ref,quaternion_roundtrip_error=max_round,checks=checks,runtime_UE_tested=False,assumptions='A default and sensor calibration; frozen N reference remains a coordinate basis only. Rigid fingers and auxiliary descendants; explicit spine groups. Parent bone lengths preserved; no centre translation correction.'))
    print(json.dumps(dict(ue_bones=len(maps),center_error_mm=max_center,reference_error_cm=max_ref)),flush=True)
if __name__=='__main__':main()
