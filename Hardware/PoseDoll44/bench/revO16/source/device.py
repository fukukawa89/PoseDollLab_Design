"""O16 physical FK and static capture reference; no CAD or Unreal dependency.
RH X-forward/Y-left/Z-up, mm, column vectors. Mirrored mount matrices occur
in pairs; final physical body rotations are always proper rotations.
"""
import hashlib
import json
import math
import numpy as np


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'),
        ensure_ascii=False, allow_nan=False).encode()).hexdigest()


def rotation(axis, degrees):
    a = np.asarray(axis, float); a /= np.linalg.norm(a)
    x, y, z = a; K = np.array([[0, -z, y], [z, 0, -x], [-y, x, 0]])
    q = math.radians(degrees)
    return np.eye(3) + math.sin(q)*K + (1-math.cos(q))*(K@K)


def compound(kind, q):
    if kind in ('tut', 'wide_tut'):
        steps = [(2,q[0]), (0,q[1]), (1,q[2]), (2,q[3])]
    elif kind == 'three_axis': steps = [(2,q[0]), (0,q[1]), (1,q[2])]
    elif kind == 'ankle_core': steps = [(1,-q[1]), (0,q[0])]
    elif kind == 'hinge': steps = [(2,q[0])]
    else: raise ValueError('unknown physical joint kind')
    T = np.eye(4)
    for axis, a in steps: T[:3,:3] = T[:3,:3] @ rotation(np.eye(3)[axis], a)
    return T


def forward(profile, angles):
    if set(angles) != set(profile['raw_order']): raise ValueError('raw channel set')
    if any(not number(v) for v in angles.values()): raise ValueError('invalid angle')
    frames = {'pelvis':np.asarray(profile['root_transform_mm'],float)}
    for j in profile['joints']:
        frames[j['child']] = (frames[j['parent']] @ np.asarray(j['parent_to_mount_mm'])
            @ compound(j['kind'], [angles[k] for k in j['raw_ids']])
            @ np.asarray(j['rotor_to_child_mm']))
    for leaf in profile['fixed_markers']:
        frames[leaf['id']] = frames[leaf['parent']] @ np.asarray(leaf['transform_mm'])
    return frames


def quaternion(M):
    R = np.asarray(M)[:3,:3]
    v = [1+R[0,0]-R[1,1]-R[2,2], 1-R[0,0]+R[1,1]-R[2,2],
         1-R[0,0]-R[1,1]+R[2,2], 1+np.trace(R)]
    k = int(np.argmax(v)); q = np.zeros(4); q[k] = math.sqrt(max(0.,v[k]))/2; d=4*q[k]
    if k==3: q[:3] = np.array([R[2,1]-R[1,2],R[0,2]-R[2,0],R[1,0]-R[0,1]])/d
    else:
        i,j=(k+1)%3,(k+2)%3
        q[i]=(R[i,k]+R[k,i])/d; q[j]=(R[j,k]+R[k,j])/d; q[3]=(R[j,i]-R[i,j])/d
    q/=np.linalg.norm(q)
    return (q if q[3]>=0 else -q).tolist()


def number(v):
    return not isinstance(v,bool) and isinstance(v,(float,int)) and math.isfinite(v)


def capture_window(profile, calibration, scans, *, expected_capture_id, evaluation_time_ms):
    """Validate a synchronized stable window; preserve raw data and calibration.
    A valid measurement does not imply physical qualification or UE acceptance.
    Transport integrity must be verified by the actual driver, not user supplied.
    """
    def reject(reason): return {'status':'REJECTED','reason':reason,'hardware_capture_eligible':False}
    p=profile['capture_policy']; ids=profile['raw_order']
    if len(scans)<p['minimum_scans']: return reject('insufficient scans')
    if calibration.get('profile_sha256')!=digest(profile): return reject('profile mismatch')
    if calibration.get('status') not in ('MEASURED','SYNTHETIC'): return reject('uncalibrated')
    axes=calibration.get('axes',{})
    if set(axes)!=set(ids): return reject('calibration channel set')
    for a in axes.values():
        if not number(a.get('sign')) or a['sign'] not in (-1,1): return reject('uncalibrated sign')
        if not all(number(a.get(k)) for k in ('sensor_zero_deg','reference_joint_deg')):
            return reject('uncalibrated zero')
    if not number(evaluation_time_ms) or not isinstance(expected_capture_id,int) or isinstance(expected_capture_id,bool):
        return reject('invalid caller clock or request')
    first=scans[0]; identity=(first.get('boot_id'),first.get('capture_id'),first.get('device_id'))
    if (not isinstance(identity[0],str) or not identity[0] or not isinstance(identity[1],int)
        or isinstance(identity[1],bool) or identity[1]<0 or not identity[2]
        or identity[2]!=calibration.get('device_id') or identity[1]!=expected_capture_id): return reject('capture identity')
    rows=[]; last_time=None; last_seq=None
    for scan in scans:
        if (scan.get('boot_id'),scan.get('capture_id'),scan.get('device_id'))!=identity:
            return reject('mixed capture, boot or device')
        if scan.get('integrity')!='valid' or set(scan.get('channels',{}))!=set(ids):
            return reject('integrity or channel set')
        seq=scan.get('sequence'); now=scan.get('time_ms')
        if not isinstance(seq,int) or isinstance(seq,bool) or seq<0 or (last_seq is not None and seq<=last_seq):
            return reject('replayed scan')
        if not number(now) or now<0 or (last_time is not None and (now<=last_time or now-last_time>p['maximum_scan_gap_ms'])):
            return reject('scan time or gap')
        row=[]; times=[]
        for k in ids:
            s=scan['channels'][k]; angle=s.get('sensor_deg'); stamp=s.get('time_ms')
            if s.get('status')!='valid' or not number(angle) or not number(stamp): return reject('invalid sample')
            if not 0<=angle<360 or not 0<=now-stamp<=p['maximum_age_ms']: return reject('stale or invalid sample')
            a=axes[k]; value=a['reference_joint_deg']+a['sign']*((angle-a['sensor_zero_deg']+180)%360-180)
            # Select the unique encoder turn inside the mechanical interval.
            lo,hi=profile['raw_limits_deg'][k]
            candidates=[value+360*n for n in (-1,0,1) if lo-1e-7<=value+360*n<=hi+1e-7]
            if len(candidates)!=1: return reject('outside raw diagnostic range or ambiguous turn')
            row.append(candidates[0]); times.append(stamp)
        if max(times)-min(times)>p['maximum_scan_skew_ms']: return reject('scan skew')
        rows.append(row);last_seq=seq;last_time=now
    if not 0<=evaluation_time_ms-scans[-1]['time_ms']<=p['maximum_age_ms']: return reject('stale entire window')
    if scans[-1]['time_ms']-first['time_ms']<p['stable_window_ms']: return reject('short stable window')
    # Compare every sample pair in actual joint coordinates. A limited joint
    # crossing its mechanical stop must not be made continuous by unwrapping.
    span=float(np.ptp(np.asarray(rows),axis=0).max())
    if span>p['maximum_peak_to_peak_deg']: return reject('moving in capture window')
    measured=dict(zip(ids,rows[-1])); frames=forward(profile,measured)
    checks=calibration.get('physical_tests',{})
    eligible=calibration['status']=='MEASURED' and all(checks.get(k) is True for k in profile['required_physical_measurement_tests'])
    return {'schema':'POSEDOLL-O16-MEASUREMENT/1','status':'VALID_MEASUREMENT',
        'hardware_capture_eligible':eligible,'device_profile_id':profile['profile_id'],
        'device_profile_sha256':digest(profile),'calibration_sha256':digest(calibration),
        'calibration':calibration,'raw_scans':scans,'joint_angles_deg':measured,
        'maximum_peak_to_peak_deg':span,'frames':{k:{'matrix_mm':M.tolist(),
        'orientation_xyzw':quaternion(M)} for k,M in frames.items()},
        'root_provenance':'FIXED_REFERENCE_NOT_MEASURED','target_adapter_status':'NOT_APPLIED',
        'contact_correction':False}
