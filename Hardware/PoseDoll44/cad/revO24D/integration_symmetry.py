"""Mirror limb hardware about the fixed UE sagittal plane, without moving bones."""
from fullbody import *
PREFIXES=('shoulder_','humeral_','upperarm_','elbow_','forearm_','wrist_','palm','W','hip_','pelvic_','thigh_','knee_','shin_','ankle_','heel_','toe_')
def selected(n):
    # Keep the proven three-part shoulder sensor placement at each narrow clavicle end.
    if n.endswith(('centered_tube','thigh_tube','shin_tube')):return False
    if n[2:] in ['shoulder_pitch_pcb','shoulder_pitch_connector','shoulder_pitch_sensor_holder']:return False
    return n[0:2] in ('l_','r_') and n[2:].startswith(PREFIXES)
def pivot(name):
    short=name[2:]
    if short.startswith(('hip_','pelvic_','thigh_')):return 'thigh'
    if short.startswith(('knee_','shin_')):return 'calf'
    if short.startswith(('ankle_','heel_')):return 'foot'
    if short.startswith('toe_'):return 'ball'
    if short.startswith(('elbow_','forearm_')):return 'lowerarm'
    if short.startswith(('wrist_','palm','W')):return 'hand'
    return 'upperarm'
def mirror_at(name):
    bone=pivot(name);return T(P[bone+'_r'])@M@T(-P[bone+'_l'])
def apply(D):
    left=[p for p in D.parts if p['name'].startswith('l_') and selected(p['name'])]
    D.parts[:]=[p for p in D.parts if not(p['name'].startswith('r_') and selected(p['name']))]
    for p in left:
        r={k:copy.deepcopy(v) for k,v in p.items() if k!='s'}
        r['name']='r_'+p['name'][2:];r['frame']='r_'+p['frame'][2:] if p['frame'].startswith('l_') else p['frame']
        r['group']=r['group'].replace('l_','r_',1) if r['group'].startswith('l_') else r['group']
        r['s']=moved(p['s'],np.linalg.inv(F0[r['frame']])@mirror_at(p['name'])@F0[p['frame']])
        r['notes']+=' Right-side sagittal mirror of the left limb hardware; UE frames and physical axis lines unchanged.'
        if 'bone_link' in r:
            r['bone_link']['bones']=[n[:-2]+'_r' for n in r['bone_link']['bones']]
            r['bone_link']['gauge_world_mm']=[(M[:3,:3]@np.array(v)).tolist() for v in r['bone_link']['gauge_world_mm']]
        D.parts.append(r)
    leftj=[j for j in D.joints if j['id'].startswith('l_') and selected(j['id'])]
    D.joints[:]=[j for j in D.joints if not(j['id'].startswith('r_') and selected(j['id']))]
    for j in leftj:
        r=copy.deepcopy(j);r['id']='r_'+j['id'][2:];r['axis_id']='r_'+j['axis_id'][2:]
        r['center_mm']=(mirror_at(j['id'])@np.r_[j['center_mm'],1])[:3];r['axis_world']=M[:3,:3]@j['axis_world'];D.joints.append(r)
    D.symmetry=dict(mirrored_feature_pairs=len(left),exceptions=['Central staggered clavicle journals and their carriers','Central spine/neck preload access and fixed support paths'],rule='Mirror finished solids and interface dimensions, never alter UE joint coordinates')
