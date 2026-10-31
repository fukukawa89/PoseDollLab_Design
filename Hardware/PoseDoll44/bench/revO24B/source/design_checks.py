"""Checks of guide restraint and conservative magnetic interference budgets."""
from spherical_wrist import *

def main():
    A=build();pin=[p for p in A.parts if p['name'].startswith('B_guide_pin')];caps=[p for p in A.parts if p['name'].startswith('B_socket_half')]
    rows=[]
    for flex,dev in [(0,0),(55,20),(-60,-15)]:
        for roll in [0,4,-4]:
            R=a.rot([1,0,0],dev)@a.rot([0,1,0],flex)@a.rot([0,0,1],roll)
            volume=sum((a.moved(p['s'],R)^c['s']).volume() for p in pin for c in caps)
            rows.append(dict(flex_deg=flex,deviation_deg=dev,unauthorized_axial_roll_deg=roll,pin_socket_overlap_mm3=volume))
    assert all(r['pin_socket_overlap_mm3']<.02 if r['unauthorized_axial_roll_deg']==0 else r['pin_socket_overlap_mm3']>.02 for r in rows)
    put(OUT/'verification/antiroll_negative_control.json',dict(status='PASS',geometry_sha256=sha(OUT/'assembly_meshes.npz'),
        scope='Actual pin and slot solids; extra axial roll keeps stem direction fixed but creates interference. This does not certify load capacity, wear or eliminate finite-clearance backlash.',cases=rows))
    # Contact-normal feasibility: four patches on each opposed cup remain outside the guide slot.
    normals=[]
    for sy in [-1,1]:
        for sx in [-1,1]:
            for sz in [-1,1]:normals.append(np.array([sx*3,sy*11,sz*math.sqrt(12.05**2-3**2-11**2)])/12.05)
    n=np.array(normals);assert np.linalg.matrix_rank(n)==3 and np.linalg.norm(n.sum(0))<1e-10
    put(OUT/'verification/capture_feasibility.json',dict(status='PASS',normals=n,rank=3,positive_equal_weight_sum_norm=np.linalg.norm(n.sum(0)),
        nominal_radial_gap_mm=.05,scope='Ideal opposing spherical contact normals positively span 3D translation. Proves local constraint feasibility after contact/preload, not physical retention strength or a pull-out test. Nominal gap allows real center motion before preload.'))
    p=load(OLD/'profiles/arm_profile.json');meta=load(OUT/'assembly.json')['parts'];magnets=[x for x in meta if x['role']=='magnet' and not x['new']];cases=load(OUT/'verification/motion_grid.json')['cases'];results=[]
    for case in cases:
        ff=frames(p,case['angles']);sensor=(ff['wrist_base']@np.r_[CONFIG['sensor_position_mm'],1])[:3];parts=[]
        for mag in magnets:
            m=(ff[mag['frame']]@np.r_[np.mean(mag['bounds_mm'],axis=0),1])[:3];r=np.linalg.norm(sensor-m)/1000;v=mag['volume_mm3']*1e-9
            bound=2*1.2*v/(4*np.pi*r**3)*1000
            parts.append(dict(name=mag['name'],distance_mm=r*1000,unknown_orientation_upper_bound_mT=bound,fixed_relative_to_wrist_sensor=mag['frame']=='fore'))
        results.append(dict(pose=case['name'],sum_bound_mT=sum(m['unknown_orientation_upper_bound_mT'] for m in parts),variable_bound_mT=sum(m['unknown_orientation_upper_bound_mT'] for m in parts if not m['fixed_relative_to_wrist_sensor']),parts=parts))
    worst=max(results,key=lambda x:x['variable_bound_mT']);fixed=max(m['unknown_orientation_upper_bound_mT'] for r in results for m in r['parts'] if m['fixed_relative_to_wrist_sensor'])
    put(OUT/'verification/magnetic_interference_budget.json',dict(status='ANALYTIC_BUDGET_ONLY',samples=len(results),worst_variable_case=worst,
        max_fixed_proximal_forearm_magnet_bound_mT=fixed,scope='Conservative sum of dipole magnitude bounds, using actual O24A magnet positions/volumes and assumed Br=1.2T. Unknown dipole clockings prevent a field prediction. Same-forearm magnet bias is nominally constant; others vary with pose. Ambient fields and ferromagnetism excluded.',
        conclusion='Interference must be measured and compensated with the whole arm. The ideal isolated-sensor angular RMS is not a system accuracy claim.'))
    # Holding budget intentionally uses a conservative effective radius around the cup poles.
    put(OUT/'verification/holding_estimate.json',dict(status='BUDGET_ONLY',wrist_target_Nm=.006,assumed_mu=.2,assumed_worst_effective_radius_mm=4,
        required_sum_normal_load_N=.006/(.2*.004),scope='N summed over both friction patches; not bolt preload or tightening torque. Friction material, compliance, actual pressure distribution and creep remain untested.'))
    print(json.dumps(dict(antiroll='PASS',capture_normals='PASS',variable_magnetic_bound_mT=worst['variable_bound_mT'],fixed_magnetic_bound_mT=fixed,worst_pose=worst['pose']),ensure_ascii=False))

if __name__=='__main__':main()
