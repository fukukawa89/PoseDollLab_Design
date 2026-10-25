from validate import *
def main():
    parts,z,solids=read_assembly();by={p['name']:(p,s) for p,s in zip(parts,solids)};rows=[]
    pairs=[('l_palm_nut','l_hip_twist_sensor_holder',['neutral']),('r_palm_nut','r_hip_twist_sensor_holder',['neutral']),('l_W07','r_Wpreload_8',['cross']),('neck_humeral_sensor_holder','head_spine_branch_1',['neutral','neck_left_turn','neck_right_turn']),('neck_humeral_sensor_holder','head_spine_rail_1',['neutral','neck_left_turn','neck_right_turn']),('left_clavicle_seat','neck_shoulder_open_yoke',['neutral','neck_down','neck_up','neck_left_tilt','neck_right_tilt']),('neck_input_bridge','r_clavicle_z_shaft',['neutral']),('l_W06','l_palm',['arms_radial','arms_ulnar','arms_wrist_flex','arms_wrist_extend'])]
    for an,bn,cases in pairs:
        a0,sa=by[an];b0,sb=by[bn]
        for n in cases:
            F=frames(poses()[n]['angles']);a1=moved(sa,F[a0['frame']]);b1=moved(sb,F[b0['frame']]);gap=float(a1.min_gap(b1,10))
            req=required(a0['frame'],b0['frame'])
            rows.append(dict(a=an,b=bn,pose=n,gap_mm=gap,search_cap_mm=10,nominal_review_margin_mm=.5,required_adjacent=req,status=('PASS_SELECTED' if gap>=.5 else 'TOLERANCE_REVIEW') if req else 'ADVISORY_NONADJACENT'))
    # Both arms against each other: explicit non-contact body families, not fits.
    q=poses()['cross']['angles'];F=frames(q);arm=lambda p:('arm' in p['group'] or 'wrist' in p['group']);left=[(p,moved(s,F[p['frame']])) for p,s in zip(parts,solids) if p['name'].startswith('l_') and arm(p)];right=[(p,moved(s,F[p['frame']])) for p,s in zip(parts,solids) if p['name'].startswith('r_') and arm(p)]
    near=[]
    for pa,sa in left:
        aa=np.array(sa.bounding_box()).reshape(2,3)
        for pb,sb in right:
            if family(pa['frame'])==family(pb['frame']):continue
            bb=np.array(sb.bounding_box()).reshape(2,3)
            if np.all(aa[1]+.5>=bb[0]) and np.all(bb[1]+.5>=aa[0]):
                gap=float(sa.min_gap(sb,.5))
                if gap<.5:near.append(dict(a=pa['name'],b=pb['name'],gap_mm=gap))
    put(OUT/'verification/selected_clearances.json',dict(status='PASS_SELECTED' if all(r['status']=='PASS_SELECTED' for r in rows if r['required_adjacent']) else 'TOLERANCE_REVIEW',geometry_sha256=sha(OUT/'assembly_meshes.npz'),rows=rows,cross_arm_near_pairs=near,cross_arm_contacts_are_advisory=True,scope='Exact minimum gap for selected non-contact pairs. Only same/adjacent anatomy gates acceptance, per user instruction 2026-10-23. Cross-arm contacts remain advisory. Not a global swept minimum or a tolerance guarantee; functional bearing/friction/captured-guide fits are checked separately.'))
    print('SELECTED GAPS',[(r['a'],r['b'],r['pose'],round(r['gap_mm'],3)) for r in rows],flush=True);print('CROSS NEAR',near,flush=True)
if __name__=='__main__':main()
