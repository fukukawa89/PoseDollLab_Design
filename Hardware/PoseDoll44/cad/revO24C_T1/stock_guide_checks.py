"""S1: stock D2.5 shoulder interface, split insertion and captive steel stack.

Nominal geometry checks, not proof of material strength or supplier tolerances.
"""
from kit import *
from validate import overlaps


def main():
    k=build();P={p['id']:p for p in k.parts};checks=[]
    for sign in [-1,1]:
        ids=['Wguide_'+str(sign),'Wguide_w_'+str(sign),'Wguide_nut_'+str(sign)]
        p,w,n=(P[id]['s'] for id in ids)
        pinv=mesh(p).vertices@(sign*Y);wv=mesh(w).vertices@(sign*Y);nv=mesh(n).vertices@(sign*Y)
        checks.append(dict(name='Metal stack '+str(sign),washer_to_nut_gap_mm=float(wv.min()-nv.max()),
            thread_protrusion_mm=float(nv.min()-pinv.min()),passed=bool(abs(wv.min()-nv.max())<1e-5 and nv.min()-pinv.min()>=.8)))
        # Insert captured hardware from the open X=0 split, before closing ball.
        for half,direction in [('W01',X),('W02',-X)]:
            worst=0
            for d in np.linspace(0,8,41):
                for solid in [w,n]:
                    s=solid.translate(d*direction)
                    if overlaps(s,P[half]['s']):worst=max(worst,float((s^P[half]['s']).volume()))
            checks.append(dict(name='Split insertion '+half+' '+str(sign),max_intersection_mm3=worst,passed=worst<.02))
        # Screw is installed only AFTER the cups surround the ball.
        worst=0
        for d in np.linspace(0,12,61):
            s=p.translate(d*sign*Y)
            for id in ['W01','W02','W04','W05','W06','W07',ids[1],ids[2]]:
                if overlaps(s,P[id]['s']):worst=max(worst,float((s^P[id]['s']).volume()))
        checks.append(dict(name='Screw insertion '+str(sign),max_intersection_mm3=worst,passed=worst<.02))
        # Tool at neutral: 2 mm hex shaft, 4 mm outer tool envelope outside head.
        tool=hexagon([0,sign*16.6,0],sign*Y,2,10)+cyl([0,sign*18,0],[0,sign*35,0],2)
        worst=max(float((tool^P[id]['s']).volume()) for id in ['W01','W02','W04','W05','W06','W07','W08'])
        checks.append(dict(name='Neutral tool access '+str(sign),max_intersection_mm3=worst,passed=worst<.02))
        # Captured washer roof and nut floor prevent escape (positive block),
        # while +/- .09 mm motion fits within the .20 mm nominal end float.
        for shift in [-.09,.09,-.4,.4]:
            v=sum(float(((w+n).translate(shift*sign*Y)^P[id]['s']).volume()) for id in ['W01','W02'])
            blocked=abs(shift)>.1
            checks.append(dict(name='Captured stack axial shift '+str(sign)+' '+str(shift),
                intersection_mm3=v,expected_blocked=blocked,passed=(v>.02 if blocked else v<.02)))
    # Worst nominal axial capture positions plus the permitted .20 cup closing.
    worst=0;poses=0
    for sign in [-1,1]:
        for drift in [-.1,.1]:
            for q in [-65,-45,0,45,70]:
                for d in [-20,0,30]:
                    poses+=1
                    s=moved(P['Wguide_'+str(sign)]['s'].translate(drift*sign*Y),frames('W',q,d)['ball'])
                    for id in ['W04','W05','W06','W07','W08']:
                        t=P[id]['s']
                        if id in ['W06','W07']:t=t.translate([0,(-1 if id=='W07' else 1)*.2,0])
                        if overlaps(s,t):worst=max(worst,float((s^t).volume()))
    checks.append(dict(name='Guide capture end float plus cup closing',guide_cases=poses,
        drift_mm=[-.1,.1],cup_closing_mm=.2,max_intersection_mm3=worst,passed=worst<.02))
    # Historical input is stored outside release, so reproducibility does not
    # silently depend on overwriting an original file with the new generation.
    before=ROOT/'output/o24ct1-stock-adaptation/before/assembly.json'
    delta=[]
    if before.exists():
        old={p['id']:p for p in json.loads(before.read_text('utf8'))['parts'] if p['printable']}
        current=json.loads((OUT/'assembly.json').read_text('utf8'))['parts']
        delta=[p['id'] for p in current if p['printable'] and p['stl_sha256']!=old[p['id']]['stl_sha256']]
        wrist_delta=[id for id in delta if id.startswith('W')]
        checks.append(dict(name='S1 wrist interface retained in six revised wrist prints',parts=wrist_delta,passed=set(wrist_delta)=={'W01','W02','W04','W05','W06','W07'}))
    result=dict(revision=REVISION,guide_interface_revision='O24C-T1-S1',geometry_sha256=sha(OUT/'assembly_meshes.npz'),
        verification_source_sha256=sha(Path(__file__)),passed=all(c['passed'] for c in checks),checks=checks,
        guide=dict(shoulder_d=2.5,shoulder_l=6,thread='M2x0.4',thread_l=4,head_d=4.8,head_h=2.4,key=2,
                   slot_width=2.94,nominal_diametral_clearance=.44,washer=[5,2.2,.5],nut_af=4,nut_h=1.6,
                   nominal_axial_end_float=.2,minimum_ball_roof_over_washer_pocket_mm=math.sqrt(11**2-2.65**2)-9.6),
        scope='Nominal rigid assembly and retention; supplier fillet, washer bore, print error, adhesive compatibility/curing, play and wear require physical acceptance. No material strength or fatigue qualification.')
    put(OUT/'verification/stock_guide_checks.json',result)
    print(json.dumps(result,ensure_ascii=False),flush=True)
    if not result['passed']:raise SystemExit(1)

if __name__=='__main__':main()
