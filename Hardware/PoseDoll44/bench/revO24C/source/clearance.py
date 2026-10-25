"""Distance audit of selected moving structures, separate from intended sliding contacts."""
from validate import *

def main():
    p=load(OUT/'profiles/arm_profile.json');A=exported();parts={r['name']:r for r in A.parts};rows=[]
    # Only the external neck can approach the socket more closely than the
    # invariant sphere-to-socket radial separation (11.75 - 11 mm).
    # This exact cylinder is a constituent of the exported ball/neck boolean.
    parts['C_neck_constituent']=dict(frame='hand_ball',s=a.cylinder([0,0,-CONFIG['ball_radius_mm']+2],[0,0,CONFIG['neck_end_mm']],3))
    groups=[('shoulder_yoke_sensor',[('shoulder_open_yoke','humeral_sensor_holder')],[dict(shoulder_abduct=float(q)) for q in np.arange(-20,166,5)],.5),
            ('shoulder_washer_stem',[(f'shoulder_swing_washer_{s*16}',f'humeral_stem_{s}') for s in [-1,1]],[dict(shoulder_abduct=float(q)) for q in np.arange(-20,166,5)],.5),
            ('elbow_forearm',[(f'elbow_{kind}_{s if kind=="ear" else s*14}',f'forearm_{tail}') for s in [-1,1] for kind in ['ear','fork'] for tail in ['housing','stem_-1','stem_1']],[dict(elbow_flex=float(q)) for q in np.arange(0,146,5)],.5),
            ('wrist_neck_socket',[('C_neck_constituent',f'C_socket_half_{s}') for s in [-1,1]],[dict(wrist_flex=float(f),wrist_deviation=float(d)) for f in np.arange(-65,71,5) for d in np.arange(-20,31,5)],.5)]
    for group,pairs,qs,required in groups:
        best=dict(gap_mm=5.)
        for q in qs:
            ff=frames(p,q);world={name:a.moved(parts[name]['s'],ff[parts[name]['frame']]) for pair in pairs for name in pair}
            for x,y in pairs:
                gap=world[x].min_gap(world[y],5)
                if gap<best['gap_mm']:best=dict(gap_mm=gap,a=x,b=y,angles=q)
        rows.append(dict(group=group,samples=len(qs),pairs=len(pairs),required_nominal_gap_mm=required,status='PASS' if best['gap_mm']>=required else 'FAIL',minimum=best));print(group,best,flush=True)
    put(OUT/'verification/selected_clearances.json',dict(status='PASS' if all(r['status']=='PASS' for r in rows) else 'FAIL',geometry_sha256=sha(OUT/'assembly_meshes.npz'),search_cap_mm=5,
        sphere_to_socket_nominal_radial_gap_mm=CONFIG['liner_outer_radius_mm']-CONFIG['ball_radius_mm'],
        scope='Minimum triangle-mesh distances through Manifold min_gap, selected moving structures at 5 degree steps. Wrist uses the exact neck cylinder constituent, not the full ball: the spherical region has invariant nominal 0.75 mm separation from the socket. 0.5 mm is an internal nominal gate, not a manufactured clearance guarantee. Bearings, friction contacts, pin slots and rigid joins are absent from this gap gate, but present in all-pair intersection audit.',rows=rows))

if __name__=='__main__':main()
