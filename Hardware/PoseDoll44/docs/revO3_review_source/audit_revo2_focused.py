#!/usr/bin/env python3
"""Independent, scoped checks for PoseDoll O2 commit 239d443... .
Reconstructs only named CAD primitives from reviewed source, not the complete
repository model. Does not validate strength, manufacture, or any physical test.
Run: python audit_revo2_focused.py --output focused_results.json
CadQuery and scipy are optional: missing packages produce NOT_RUN, never PASS.
"""
from __future__ import annotations
import argparse, json, math, sys, platform
from pathlib import Path
COMMIT = '239d4430cec49eecaf12c37f1ec4717055d3fbfe'


def calculations() -> dict:
    ro, ri, force, radius, diameter = 12.0, 4.2, 326.0, 10.7, 0.6
    reff = (2/3)*(ro**3-ri**3)/(ro**2-ri**2)
    loads=[]
    for mu in (0.08, 0.22):
        torque_one_Nmm=mu*force*reff
        pin_force=torque_one_Nmm/(2*radius)
        loads.append({'mu_assumed':mu,'torque_per_face_Nm':torque_one_Nmm/1000,
                      'per_pin_force_N_if_pins_carry_all_torque':pin_force,
                      'pin_direct_shear_MPa_equal_sharing':pin_force/(math.pi*diameter**2/4)})
    target=1200.; total=1635.589739452759
    allowances={'frames_links':150,'harness':90,'unresolved_fasteners_springs':100,
                'covers':130,'eight_pcba':127,'power_distribution':35,'new_links':12}
    return {'status':'CONDITIONAL_ARITHMETIC_NOT_A_RATING',
            'effective_radius_mm':reff,'pin_loading':loads,
            'front_wear_to_first_pin_contact_mm':0.6-0.5,
            'rear_wear_to_first_pin_contact_mm':0.6-0.4,
            'declared_total_wear_mm':0.6,
            'symmetric_wear_per_face_mm':0.3,
            'front_pin_penetration_at_symmetric_wear_mm':0.2,
            'rear_pin_penetration_at_symmetric_wear_mm':0.1,
            'mass_budget_g':total,'mass_target_g':target,'over_target_g':total-target,
            'unmodeled_allocations_g':allowances,
            'joint_reference_total_g':total-sum(allowances.values()),
            'mean_joint_budget_g_if_allowances_unchanged':(target-sum(allowances.values()))/41,
            'nominal_diametral_tilt_deg':math.degrees(math.atan(0.02/14)),
            'key_clearance_angle_scale_deg':math.degrees(0.008/3.05),
            'bundle_diameter_mm_at_assumed_065_packing':0.8*math.sqrt(14/0.65),
            'unvalidated_bend_radius_mm':4.0,
            'limitations':['Pin calculation assumes equal load sharing and no unqualified back-face friction or bonding credit.',
                           'Wear example holds spring working height/force by moving pressure plate and adjuster; this is an allowed candidate state, not measured wear.',
                           'Mass allocations may overlap detailed hardware, but cannot be removed without item-level reconciliation.']}


def geometry() -> dict:
    try:
        import cadquery as cq
    except ImportError as exc:
        return {'status':'NOT_RUN','reason':str(exc)}
    def cyl(r,z0,z1):return cq.Solid.makeCylinder(r,z1-z0,cq.Vector(0,0,z0))
    def ring(ro,ri,z0,z1):return cyl(ro,z0,z1).cut(cyl(ri,z0-.01,z1+.01))
    def box(x,y,z,c):return cq.Workplane('XY').box(x,y,z).translate(c).val()
    # compact_joint.py exact floating disc and lining locating pin geometry.
    rotor=ring(12,3.025,-2.1,-.6).fuse(ring(4.05,3.025,-3.3,1.0))
    for sign in (-1,1):rotor=rotor.cut(box(1.8,2.008,5,(sign*3.05,0,-1)))
    front=[cyl(.30,-.5,.05).translate((x,0,0)) for x in (-10.7,10.7)]
    rear=[cyl(.30,-2.95,-2.3).translate((x,0,0)) for x in (-10.7,10.7)]
    wear=[]
    for wf,wr in ((0.,0.),(.10,0.),(.15,0.),(.30,.30)):
        disc=rotor.translate((0,0,wf))
        vf=sum(disc.intersect(pin).Volume() for pin in front)
        vr=sum(disc.intersect(pin.translate((0,0,wf+wr))).Volume() for pin in rear)
        wear.append({'front_wear_mm':wf,'rear_wear_mm':wr,
                     'front_pin_disc_intersection_mm3':vf,'rear_pin_disc_intersection_mm3':vr,
                     'status':'COUNTEREXAMPLE_COLLISION' if max(vf,vr)>1e-4 else 'NO_VOLUME_COLLISION_THIS_STATE_ONLY'})
    assert wear[0]['front_pin_disc_intersection_mm3']<1e-5
    assert wear[-1]['front_pin_disc_intersection_mm3']>0.11
    assert wear[-1]['rear_pin_disc_intersection_mm3']>0.05
    # Reconstruct one post-to-housing-tab interface, deliberately not whole CAD.
    datum=25.1+1.5+1.995;x=7.7
    tab=box(3.4,3,1.2,(x,0,19.4))
    post=ring(1.5,.65,20,datum-.91).translate((x,0,0))
    shelf=box(3.4,2.5,.5,(6.5,0,datum-1.16))
    post=post.fuse(shelf).cut(cyl(.65,19.99,datum-.90).translate((x,0,0)))
    interface=[]
    for dz in (0.,.1,1.,5.):
        moved=post.translate((0,0,dz))
        interface.append({'post_lift_mm':dz,'intersection_mm3':tab.intersect(moved).Volume(),
                          'distance_mm':tab.distance(moved)})
    assert interface[1]['distance_mm']>.099
    return {'status':'SCOPED_CAD_COUNTEREXAMPLES_REPRODUCED','cadquery_version':cq.__version__,
            'wear_states':wear,'post_tab_interface':interface,
            'pcb_clamp_screw_bottom_z_mm':datum-2.3,'housing_tab_top_z_mm':20.,
            'pcb_clamp_screw_stops_above_base_mm':datum-2.3-20.,
            'scope':'Only source-defined rotor, pins, post and tab primitives; original full assembly and its original tests were NOT executed.'}


def contact_counterexample() -> dict:
    try:
        import numpy as np
        from scipy.optimize import linprog
    except ImportError as exc:
        return {'status':'NOT_RUN','reason':str(exc)}
    # Same XY projections at two heights. O2 static constraints use XY only.
    pts=np.array([[-.01,-.01,0],[-.01,.01,0],[.01,-.01,0],[.01,.01,0],
                  [-.01,-.01,.02],[-.01,.01,.02],[.01,-.01,.02],[.01,.01,.02]])
    A=np.vstack([np.ones(8),pts[:,0],pts[:,1]]);b=np.array([10.,0.,0.])
    obj=np.r_[np.zeros(4),-np.ones(4)]
    relaxed=linprog(obj,A_eq=A,b_eq=b,bounds=(0,None),method='highs')
    physical=linprog(obj,A_eq=A,b_eq=b,bounds=[(0,None)]*4+[(0,0)]*4,method='highs')
    assert relaxed.success and physical.success
    return {'status':'HEIGHT_OMISSION_COUNTEREXAMPLE_REPRODUCED',
            'total_weight_N':10.,'airborne_height_mm':20.,
            'max_airborne_support_force_without_gap_constraint_N':float(sum(relaxed.x[4:])),
            'max_airborne_support_force_with_gap_constraint_N':float(sum(physical.x[4:])),
            'scope':'Synthetic example of the source constraint form, not recomputation of the character load report.'}


def maintenance_model() -> dict:
    period=16667;last=0;events=[]
    for k in range(60):
        now=1000000+k*period
        maintenance=(last==0 or now-last>=100000)
        if maintenance:last=now
        events.append({'frame':k,'us':now,'maintenance':maintenance})
    m=sum(e['maintenance'] for e in events)
    return {'status':'IDEAL_SCHEDULER_MODEL_NOT_ESP_IDF_EXECUTION','permanently_missing_nodes':1,
            'window_frames':60,'maintenance_cohorts':m,'normal_acquisition_cohorts':60-m,
            'healthy_node_fresh_opportunity_fraction':(60-m)/60,
            'steady_all_healthy_maintenance_cohorts':0,
            'assumptions':'Persistent missing node, maintenance eligibility remains true, 16667us loop, no SDK jitter; each target slot suppresses SYNC for all nodes as in main.c.'}


def timing_semantics_counterexample() -> dict:
    # Direct semantic model of pd_end/pd_finish and capture_metrics_revo2.py.
    # Not an execution of the repository decoder or firmware.
    node_delay_us=200; node_span_us=6200; end_receive_elapsed_us=11000
    usb_timing=(0,end_receive_elapsed_us)
    actual_sample_gate=node_delay_us+node_span_us<=8000
    old_metric_gate=sum(usb_timing)<=8000
    assert actual_sample_gate and end_receive_elapsed_us<14000 and not old_metric_gate
    return {'status':'SEMANTIC_COUNTEREXAMPLE_REPRODUCED',
            'node_local_delay_us':node_delay_us,'node_local_span_us':node_span_us,
            'gateway_end_receive_elapsed_us':end_receive_elapsed_us,
            'PD41_v1_exported_node_timing_us':list(usb_timing),
            'actual_node_8ms_gate':actual_sample_gate,
            'gateway_strict_14ms_gate':end_receive_elapsed_us<14000,
            'current_metric_misclassifies_as_not_in_8ms':not old_metric_gate,
            'correct_PD41_only_8ms_observability':'NOT_OBSERVABLE_NEEDS_RAW_END_OR_NODE_TRACE',
            'scope':'Source-derived field semantics, not an end-to-end timing measurement.'}


def main() -> None:
    ap=argparse.ArgumentParser();ap.add_argument('--output',type=Path,default=Path('focused_results.json'));args=ap.parse_args()
    result={'reviewed_commit':COMMIT,'python_version':sys.version,'platform':platform.platform(),
            'full_repository_clone':'NOT_AVAILABLE_DNS_FAILURE','complete_CAD_rerun':False,
            'KiCad_rerun':False,'ESP_IDF_rerun':False,'hardware_tests':False,
            'calculations':calculations(),'geometry':geometry(),
            'contact_counterexample':contact_counterexample(),'maintenance_model':maintenance_model(),
            'timing_semantics_counterexample':timing_semantics_counterexample()}
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(result,ensure_ascii=False,indent=2,allow_nan=False)+'\n',encoding='utf-8')
    print(json.dumps(result,ensure_ascii=False,indent=2))
if __name__=='__main__':main()
