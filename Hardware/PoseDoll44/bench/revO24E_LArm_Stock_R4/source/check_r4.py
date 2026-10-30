from build_stock import *
from check_stock import saved
from assembly_plan import tools_for_guide

def run():
    a,ss=saved();P={p['name']:p for p in a};S={p['name']:moved(s,F0[p['frame']]) for p,s in zip(a,ss)};ints=load(OUT/'interfaces.json');rows=[];access=[]
    for r,fn,on in zip(ints['rolls'],['ROOT','SHOULDER_ABDUCT','ELBOW_OUTPUT'],['SHOULDER_PITCH','UPPER_ARM','FOREARM']):
        pre=r['id'];W=np.array(r['W']);iw=np.linalg.inv(W);body=moved(S[fn],iw);lid=moved(S[r['keeper']],iw);output=moved(S[on],iw)
        moving=union(moved(S[n],iw) for n in S if n==on or (n.startswith(pre+'_') and '_lid_' not in n and n!=r['keeper']))
        pos=[dict(shift_mm=dz,body_overlap_mm3=(moving.translate([0,0,dz])^body).volume(),cover_overlap_mm3=(moving.translate([0,0,dz])^lid).volume()) for dz in [-.25,.25]]
        neg=max((moving.translate([0,0,float(z)])^body).volume() for z in np.linspace(-12,0,49))
        rows.append(dict(id=pre,positive_stops=pos,cover_removed_negative_control_mm3=neg,passed=all(max(x['body_overlap_mm3'],x['cover_overlap_mm3'])>.02 for x in pos) and neg<.02))
        obstacles=union(moved(S[n],iw) for n in [fn,on,r['keeper']])
        for x in [-r['lug_x_mm'],r['lug_x_mm']]:
            sg=1 if x>0 else -1;A=T([x,0,0])@rot([0,0,1],0 if sg>0 else 180)
            # An open jaw approaches radially from outside, leaving its nose clear of the central body.
            spanner=box([-2.5,-5.25,8.65],[8,5.25,10.45])+box([6,-2.5,8.65],[38,2.5,10.45]);spanner-=box([-3,-2.8,8.5],[2.2,2.8,10.6]);spanner=moved(spanner,A)
            socket=tube([x,0,10.9],[x,0,30.9],4.25,3.25)
            key=cyl([x,0,-4.5],[x,0,-35],1.45)
            sweep=[]
            for deg in np.linspace(-30,30,25):
                Q=T([x,0,0])@rot([0,0,1],float(deg))@T([-x,0,0]);sweep.append((moved(spanner.translate([0,0,2.4]),Q)^obstacles).volume())
            vals={'inner_5p5_spanner':(spanner^obstacles).volume(),'outer_5p5_spanner':(spanner.translate([0,0,2.4])^obstacles).volume(),'outer_spanner_60deg_sweep':max(sweep),'head_2p5_hex':(key^obstacles).volume()}
            access.append(dict(module=pre,x=x,volumes_mm3=vals,rejected_long_socket_overlap_mm3=(socket^obstacles).volume(),passed=max(vals.values())<.02,nut_height_mm=2.4,spanner_thickness_max_mm=2.0,thread_beyond_outer_nut_mm=1.1))
    fingers=[]
    for r,on in zip(ints['rolls'],['SHOULDER_PITCH','UPPER_ARM','FOREARM']):
        W=np.array(r['W']);R=rot([0,0,1],180 if r['id']!='RF' else 90);body=moved(S[on],np.linalg.inv(W));test=union([cyl([0,-40,2.3],[0,-40,14.3],8),cyl([0,-40,-1.3],[0,-40,-13.3],8)]);test=moved(test,R@T([0,0,-7.3]));mx=0.
        for z in [-6,-1]:
            for dy in np.linspace(0,35,71):
                offset=(R[:3,:3]@np.array([0,-dy,z]));mx=max(mx,(test.translate(offset)^body).volume())
        fingers.append(dict(module=r['id'],location='20 x 20 mm external tray handle',assumed_finger_diameter_mm=16,maximum_print_overlap_mm3=mx,passed=mx<.02))
    for r,fn in zip(ints['hinges'],['SHOULDER_PITCH','UPPER_ARM']):
        M=np.array(r['M']);ob=union(S[n] for n in [fn]);
        for side in [-1,1]:
            finger=moved(cyl([0,side*11.25,0],[0,side*27.25,0],8),M);vol=(finger^ob).volume();fingers.append(dict(module=r['id'],side=side,location='open cup mouth; not a fingertip inserted to the deep nut seat',assumed_finger_diameter_mm=16,maximum_print_overlap_mm3=vol,passed=vol<.02))
    for axis in [[1,0,0],[-1,0,0],[0,1,0],[0,-1,0]]:
        q=np.array(axis);vol=(moved(cyl(q*11.25,q*27.25,8),F0['l_wrist_flex'])^S['KEEP_E-P019']).volume();fingers.append(dict(module='W',axis=axis,location='unclosed centre face',assumed_finger_diameter_mm=16,maximum_print_overlap_mm3=vol,passed=vol<.02))
    kit=load(OUT/'kit.json');old={p['part_number']:p for p in load(R2/'kit.json')['structural_parts']};reuse=[];changed=[]
    for p in kit['structural_parts']:
        if p.get('source_r2_print'):reuse.append(dict(part_number=p['part_number'],source=p['source_r2_print'],byte_identical=sha(OUT/p['stl'])==sha(R2/old[p['source_r2_print']]['stl'])))
        else:changed.append(p['part_number'])
    fits=[]
    for p in a:
        if (p['name'].endswith('_F1') and p['name'].startswith(('HS_','HE_'))) or p['name'] in ['KEEP_E-H1133','KEEP_E-H1141','KEEP_E-H1149','KEEP_E-H1157']:
            target='SHOULDER_PITCH' if p['name'].startswith('HS_') else 'UPPER_ARM' if p['name'].startswith('HE_') else 'KEEP_E-P019';vol=(S[p['name']]^S[target]).volume();fits.append(dict(pad_part=P[target]['part_number'],washer=p['part_number'],radial_interference_mm=.06,axial_clearance_to_moving_ear_mm=.18,rigid_overlap_mm3=vol,physical_retention_tested=False))
    checks=[dict(check='positive axial capture with negative control',passed=all(x['passed'] for x in rows)),dict(check='specified spanners, sockets and hex keys clear',passed=all(x['passed'] for x in access)),dict(check='external 16 mm finger proxy clears',passed=all(x['passed'] for x in fingers)),dict(check='only P005 P007 P012 changed; 8 exact STL reuses',passed=changed==['S4-P005','S4-P007','S4-P012'] and len(reuse)==8 and all(x['byte_identical'] for x in reuse)),dict(check='eight declared temporary radial fits, not loaded friction faces',passed=len(fits)==8 and all(.03<x['rigid_overlap_mm3']<.15 for x in fits)),dict(check='seven axes and limits unchanged',passed=load(OUT/'profiles/arm_profile.json')==load(R2/'profiles/arm_profile.json'))]
    d=dict(status='PASS_DESIGN_GEOMETRY' if all(x['passed'] for x in checks) else 'REVIEW_REQUIRED',geometry_sha256=sha(OUT/'production_meshes.npz'),checks=checks,capture=rows,cover_tool_access=access,external_hand_envelopes=fingers,required_reprint=changed,reused_prints=reuse,temporary_retention=fits,physical_assembly_tested=False,scope='Specific geometric checks. 16 mm fingers are an explicit screening assumption, not population coverage or real dexterity validation. Pad press fits require the eight physical inversion gates in the tutorial; no retention-force or fatigue claim.')
    put(OUT/'verification/assembly_usability.json',d);print(d['status'],[x for x in checks if not x['passed']],flush=True)
    for x in access+fingers:
        if not x['passed']:print(x,flush=True)
if __name__=='__main__':run()
