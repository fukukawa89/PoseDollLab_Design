"""Emit the existing arm-chain transforms from calibrated R5 joint angles.
This is a file bridge in the profile's CAD frame, not an installed UE LiveLink plugin.
"""
import argparse,json,math
from pathlib import Path
import numpy as np
from arm_reader import angles
AXES=dict(RP='l_shoulder_flex',HS='l_shoulder_abduct',RU='l_upperarm_roll',HE='l_elbow_flex',RF='l_forearm_roll',WF='l_wrist_flex',WD='l_wrist_deviation')

def transforms(q,profile):
    world={};rows=[]
    for node in profile['nodes']:
        m=np.eye(4);m[:3,3]=node['offset_mm']
        if node['axis'] is not None:
            a=np.asarray(node['axis'],float);a/=np.linalg.norm(a);theta=math.radians(q[node['id']]+node['zero_deg']);x,y,z=a
            k=np.array([[0,-z,y],[z,0,-x],[-y,x,0]])
            m[:3,:3]=np.eye(3)+math.sin(theta)*k+(1-math.cos(theta))*(k@k)
        w=(world[node['parent']] if node['parent'] else np.eye(4))@m;world[node['id']]=w
        rows.append(dict(frame=node['id'],target_bone=node['target_bone'],local_matrix_mm=m.tolist(),world_matrix_mm=w.tolist()))
    return rows

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--capture',required=True);p.add_argument('--calibration',required=True);p.add_argument('--profile',default=str(Path(__file__).parent.parent/'profiles/arm_profile.json'));p.add_argument('--output',required=True);a=p.parse_args()
    data=json.loads(Path(a.capture).read_text('utf8'));cal=json.loads(Path(a.calibration).read_text('utf8'));profile=json.loads(Path(a.profile).read_text('utf8'))
    if data.get('error') or not data.get('frames') or cal['status']!='MEASURED_ACCEPTANCE_PASSED':raise ValueError('Accepted capture and measured calibration required')
    frames=[]
    for f in data['frames']:
        if f['device']!=cal['device']:raise ValueError('Calibration device mismatch')
        q={AXES[k]:v for k,v in angles(f,cal).items()};frames.append(dict(scan=f['scan'],time_us=f['end_us'],joint_angles_deg=q,nodes=transforms(q,profile)))
    Path(a.output).write_text(json.dumps(dict(schema='R5_ARM_POSE_CHAIN/1',coordinates='R4 CAD frame, mm, row-major; apply existing UE reference-pose basis conversion downstream',wrist='Ry(WF) @ Rx(WD); RF -90 degree clock counted once',frames=frames),ensure_ascii=False),encoding='utf8')
