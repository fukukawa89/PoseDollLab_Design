"""Local multi-axis grids, with explicit adjacent-segment acceptance."""
from validate import *
from itertools import product

def main():
    parts,z,s=read_assembly();e=Collision(parts,s);axes={a['id']:a for a in PROFILE['axes']};rows=[]
    groups=[['lumbar_flex','lumbar_side','lumbar_yaw'],['thorax_side','thorax_flex'],['neck_side','neck_flex','neck_yaw']]
    for side in ['l','r']:
        groups.extend([[side+'_'+a for a in seq] for seq in [('clavicle_protract','clavicle_elevate'),('shoulder_flex','shoulder_abduct','upperarm_roll'),('elbow_flex','forearm_roll'),('wrist_deviation','wrist_flex'),('hip_abduct','hip_flex','hip_roll'),('ankle_roll','ankle_flex')]])
    for group in groups:
        values=[np.linspace(*axes[n]['limits_deg'],5).tolist() for n in group];cases=[]
        for index,vals in enumerate(product(*values)):
            q={**NEUTRAL_ANGLES,**dict(zip(group,vals))};hits=e.check(q)
            cases.append(dict(index=index,angles=q,count=len(hits),collisions=hits))
        fail=sum(c['count']>0 for c in cases);rows.append(dict(axes=group,samples=len(cases),failed_cases=fail,cases=cases));print('GRID',group,len(cases),'FAIL',fail,flush=True)
    # Synthetic positive/negative controls exercise actual overlap classification.
    fake=[dict(name=n,frame=fr) for n,fr in [('upper','l_upperarm_roll'),('fore','l_forearm_roll'),('waist','lumbar_yaw')]]
    # Different local solids are placed at the same world cube for all controls.
    cube=box([0,0,0],[2,2,2]);fs=[moved(cube,np.linalg.inv(FA[p['frame']])) for p in fake];control=Collision(fake,fs)
    required_hits=control.check(NEUTRAL_ANGLES);all_hits=control.check(NEUTRAL_ANGLES,scope='all')
    tests=dict(adjacent_overlap_detected=any({h['a'],h['b']}=={'upper','fore'} for h in required_hits),nonadjacent_is_advisory=any({h['a'],h['b']}=={'fore','waist'} and not h['required_adjacent'] for h in all_hits),gimbal_stages_included=required('l_shoulder_flex','l_upperarm_roll'))
    put(OUT/'verification/adjacency_policy.json',dict(status='PASS' if all(tests.values()) else 'FAIL',geometry_sha256=sha(OUT/'assembly_meshes.npz'),authority='Explicit user request 2026-10-23',segments={n:segment(n) for n in NODES},required_segment_edges=EDGES,same_segment_different_moving_frames_required=True,same_rigid_body_contacts_exempt=True,nonadjacent_contacts='ADVISORY_NOT_ACCEPTANCE_FAILURE',controls=tests))
    put(OUT/'verification/joint_local_grids.json',dict(status='PASS_SAMPLED_GRIDS' if all(r['failed_cases']==0 for r in rows) and all(tests.values()) else 'FAIL',geometry_sha256=sha(OUT/'assembly_meshes.npz'),samples=sum(r['samples'] for r in rows),failed_cases=sum(r['failed_cases'] for r in rows),points_per_axis=5,groups=rows,scope='Each listed local axis group sampled at a 5-point Cartesian grid including all endpoints; required collision scope same/adjacent anatomical segments. Not exhaustive continuous range certification or whole-body Cartesian-product proof.'))

if __name__=='__main__':main()
