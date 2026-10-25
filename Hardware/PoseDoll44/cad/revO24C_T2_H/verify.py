"""Geometry, force-path, assembly-path and tool-clearance checks for the new H.
Neither elastic deformation nor physical torque/wear is inferred from these.
"""
from spring_hinge import *
import itertools, time

EPS=.001
def overlap(s,t):
    u=np.array(s.bounding_box()).reshape(2,3);v=np.array(t.bounding_box()).reshape(2,3)
    if np.any(np.minimum(u[1],v[1])-np.maximum(u[0],v[0])<=1e-7):return 0.
    return max(0.,float((s^t).volume()))

def main():
    begin=time.time();static=[];motion=[];stacks=[];paths=[];tools=[]
    for h in [1.2,1.1,1.,.9]:
        parts=build(h);d={p['id']:p['s'] for p in parts}
        for p,q in itertools.combinations(parts,2):
            v=overlap(p['s'],q['s'])
            if v>EPS:static.append(dict(height_mm=h,pair=[p['id'],q['id']],volume_mm3=v))
        for ang in range(-45,166):
            s=moved(d['H2-02'],rot(Y,-ang))
            for p in parts:
                if p['id']=='H2-02':continue
                v=overlap(s,p['s'])
                if v>EPS:motion.append(dict(height_mm=h,angle_deg=ang,part=p['id'],volume_mm3=v))
        head=3.3+h;neck=head-8;tip=head-14
        stacks.append(dict(spring_pair_height_mm=h,compression_fraction=(1.2-h)/.4,
            head_face_y=head,shoulder_start_y=neck,thread_tip_y=tip,
            shoulder_floor_clearance_mm=neck+4.4,shoulder_to_reaction_washer_gap_mm=neck+5.3,
            protrusion_past_main_nut_mm=-8.5-tip,
            full_thread_engagement_mm=min(-6.1,neck-.3)-max(-8.5,tip+.5),
            cap_screw_protrusion_mm=1.1,cap_screw_tip_to_lever_clearance_mm=.7))
        # A 3 mm straight hex key shaft and a D7 x 35 tool-body envelope are
        # clear in front. Wrench handle sweep is deliberately not asserted.
        for label,t,except_id in [('axis_AF3',hexagon([0,head+1.5,0],Y,2.98,40),'AX01'),
            ('axis_driver_D7',cyl([0,head+3.1,0],[0,head+38.1,0],3.5),'AX01')]:
            hits=[dict(part=p['id'],volume_mm3=v) for p in parts if p['id']!=except_id and (v:=overlap(t,p['s']))>EPS]
            tools.append(dict(height_mm=h,tool=label,findings=hits))
    p=build();d={r['id']:r['s'] for r in p}
    def path(label,movers,obstacles,axis,distance):
        worst=0.;pair=None
        for s in np.arange(0,distance+.01,.25):
            for m in movers:
                for b in obstacles:
                    v=overlap(d[m].translate(np.array(axis)*s),d[b])
                    if v>worst:worst=v;pair=[m,b]
        paths.append(dict(label=label,movers=movers,distance_mm=distance,step_mm=.25,max_overlap_mm3=worst,pair=pair,passed=worst<=EPS))
    # Paths are reversed insertion trajectories; only already-installed parts
    # are obstacles. The main nut is inserted in the separate cap first.
    path('反力垫从后方装入',['M03'],['H2-01'],[0,-1,0],25)
    path('调节螺母先放进独立后盖',['M02'],['H2-03'],[0,1,0],20)
    path('带螺母后盖直线合拢',['H2-03','M02'],['H2-01','M03'],[0,-1,0],25)
    for i in [1,2]:path('固定普通螺母从正面入槽',[f'C_N{i}'],['H2-01'],[0,1,0],20)
    path('内侧大垫圈',['F01'],['H2-01','H2-03','M02','M03','C_N1','C_N2'],[0,1,0],25)
    path('转动杆',['H2-02'],['H2-01','H2-03','M02','M03','C_N1','C_N2','C_S1','C_S2','F01'],[0,1,0],25)
    installed=['H2-01','H2-02','H2-03','M02','M03','C_N1','C_N2','C_S1','C_S2','F01']
    for id in ['F02','SP01','SP02','M04','AX01']:
        path('正面逐件装入 '+id,[id],installed,[0,1,0],25);installed.append(id)
    for i in [1,2]:
        path('后盖垫圈与螺钉装入',[f'C_S{i}',f'C_W{i}'],['H2-01','H2-03','M02','M03',f'C_N{i}'],[0,-1,0],25)
        t=hexagon([(-14 if i==1 else 14),-15.7,0],-Y,2.48,35)
        hits=[dict(part=r['id'],volume_mm3=v) for r in p if r['id']!=f'C_S{i}' and (v:=overlap(t,r['s']))>EPS]
        tools.append(dict(tool='cap_AF2.5_'+str(i),findings=hits))

    # Tiny axial virtual displacement must close each intended force contact.
    contacts=[]
    for moving,target,sign in [('M02','M03',1),('M03','H2-01',1),('F01','H2-01',-1),
        ('F01','H2-02',1),('F02','H2-02',-1),('SP01','F02',-1),('SP02','SP01',-1),
        ('M04','SP02',-1),('AX01','M04',-1)]:
        v=overlap(d[moving].translate([0,.02*sign,0]),d[target])
        contacts.append(dict(pair=[moving,target],virtual_displacement_mm=.02,contact_probe_mm3=v,passed=v>1e-4))
    # Direct numeric regression: the nut cannot spin in its cap; the cap has
    # ample material around the corner of its hex pocket and two fixing bolts.
    captured=overlap(moved(d['M02'],rot(Y,30)),d['H2-03'])
    cap_gap=float(d['M03'].bounding_box()[1]-d['H2-03'].bounding_box()[4])
    sensitivity=[]
    for h,ls,lt,stackerr,nuterr in itertools.product([.9,1.0,1.1,1.2],[7.9,8.1],[5.8,6.2],[-.1,.1],[-.1,.1]):
        head=3.3+h+stackerr;neck=head-ls;tip=neck-lt;n0=-8.5+nuterr;n1=-6.1+nuterr
        sensitivity.append(dict(pair_mm=h,shoulder_mm=ls,thread_mm=lt,stack_error_mm=stackerr,nut_position_error_mm=nuterr,
            bottom_clearance_mm=neck+4.4,full_engagement_mm=max(0,min(neck-.3,n1)-max(tip+.5,n0)),
            tip_past_nut_mm=n0-tip))
    min_full=min(v['full_engagement_mm'] for v in sensitivity)
    # Contact area is not itself torque gain. Two washers are unkeyed: report
    # both one- and two-effective-face estimates and never promise either.
    r0=2.15;r1=6;re=(2/3)*(r1**3-r0**3)/(r1**2-r0**2)
    torque=[dict(mu_assumed=mu,effective_faces=n,required_axial_force_N=.13/(n*mu*re/1000)) for mu,n in itertools.product([.1,.2,.3],[1,2])]
    result=dict(revision=REVISION,passed=not static and not motion and all(r['passed'] for r in paths+contacts) and not any(r['findings'] for r in tools)
        and captured>.1 and cap_gap>.14 and min_full>=2.39 and min(r['bottom_clearance_mm'] for r in sensitivity)>.39,
        geometry_sha256=sha(OUT/'assembly_meshes.npz'),static_collisions=static,motion_collisions=motion,
        motion_poses=844,motion_step_deg=1,spring_height_cases_mm=[1.2,1.1,1.,.9],threshold_mm3=EPS,
        stacks=stacks,assembly_paths=paths,contacts=contacts,tools=tools,captive_nut_30deg_overlap_mm3=captured,
        cap_nose_gap_to_reaction_washer_mm=cap_gap,cap_min_wall_outside_hex_corner_mm=5.9-5.8/math.sqrt(3),
        continuous_reaction_web_mm=2.8,fit_diametral_allowance_mm=.25,
        tolerance_sensitivity=dict(assumed_not_supplier_tolerances=True,cases=len(sensitivity),min_full_thread_engagement_mm=min_full,
                                 min_shoulder_floor_clearance_mm=min(r['bottom_clearance_mm'] for r in sensitivity),
                                 min_tip_past_nut_mm=min(r['tip_past_nut_mm'] for r in sensitivity),rows=sensitivity),
        force_estimates=dict(assumed_mu_not_measured=True,target_Nm=.13,effective_radius_mm=re,area_each_mm2=math.pi*(r1*r1-r0*r0),
                             old_T1_nominal_rotor_face_area_mm2=math.pi*(6**2-4.6**2),cases=torque),
        physical_torque_verified=False,physical_wear_verified=False,physical_strength_verified=False,
        scope='Rigid nominal geometry, 1-degree angular sampling, specified assembly trajectories, straight tool shanks, geometric force contacts. No elastic/contact-pressure/material/bolt-strength simulation; no supplier force curve assumed.',elapsed_s=time.time()-begin)
    put(OUT/'verification/mechanics.json',result)
    print(json.dumps({k:result[k] for k in ['passed','motion_poses','static_collisions','motion_collisions','cap_nose_gap_to_reaction_washer_mm','elapsed_s']},ensure_ascii=False))
    if not result['passed']:
        print(json.dumps(dict(paths=[r for r in paths if not r['passed']],contacts=contacts,tools=tools,min_full=min_full,cap_gap=cap_gap,captured=captured),ensure_ascii=False))
        raise SystemExit(1)

if __name__=='__main__':main()
