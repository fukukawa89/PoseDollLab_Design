"""Independent inspections of saved E meshes. Reports failures, never re-labels them."""
from build import *
from collections import defaultdict
import argparse,time
from scipy.spatial.transform import Rotation
from scipy.spatial import cKDTree

def context():
    import validate as v
    for key,val in dict(OUT=OUT,PROFILE=PROFILE,F0=F0,FA=FA,NODES=NODES,frames=frames).items():setattr(v,key,val)
    v.poses=lambda:load(OUT/'profiles/poses.json')
    return v

def production_groups():
    data=load(OUT/'production_assembly.json');assert data['geometry_sha256']==sha(OUT/'assembly_meshes.npz')
    z=np.load(OUT/'production_meshes.npz');groups={}
    for p in data['parts']:
        if not p['name'].startswith(('E-P','E-M')):continue
        i=str(p['i']);s=md.Manifold(md.Mesh64(np.array(z[i+'v'],dtype=np.float64,copy=True,order='C'),np.array(z[i+'f'],dtype=np.uint64,copy=True,order='C')))
        groups.setdefault(p['frame'],[]).append(moved(s,F0[p['frame']]))
    rigid={fr:union(ss) for fr,ss in groups.items()};result=dict(rigid)
    for fr in NODES:
        family=fr
        while NODES[family]['axis'] is None and NODES[family]['parent']:family=NODES[family]['parent']
        if family in rigid:result[fr]=rigid[family]
    return result

def main_geometry(quick=False):
    v=context();parts,z,ss=v.read_assembly();digest=sha(OUT/'assembly_meshes.npz')
    w=[moved(s,FA[p['frame']]) for p,s in zip(parts,ss)]
    b=np.array([bounds(s) for s in w]);lo=b[:,0].min(0);hi=b[:,1].max(0)
    put(OUT/'verification/envelope.json',dict(geometry_sha256=digest,status='PASS' if hi[2]-lo[2]<600 else 'FAIL',bounds_mm=[lo,hi],height_mm=hi[2]-lo[2],limit_exclusive_mm=600))
    poses=load(OUT/'profiles/poses.json');engine=v.Collision(parts,ss)
    cases={'neutral':poses['neutral']['angles']}
    if not quick:
        cases.update({k:p['angles'] for k,p in poses.items()})
        for ax in PROFILE['axes']:
            for q in ax['limits_deg']:cases[f'ROM/{ax["id"]}/{q}']={**base.NEUTRAL_ANGLES,ax['id']:q}
    rows=[];pairs={}
    for name,q in cases.items():
        hits=engine.check(q)
        rows.append(dict(pose=name,angles=q,count=len(hits),collisions=hits))
        for hit in hits:
            key=hit['a']+' / '+hit['b'];p=pairs.setdefault(key,dict(poses=[],max_mm3=0));p['poses'].append(name);p['max_mm3']=max(p['max_mm3'],hit['volume_mm3'])
        print('MOTION',name,len(hits),flush=True)
    put(OUT/('verification/motion_quick.json' if quick else 'verification/motion_named_endpoints.json'),dict(status='PASS' if not pairs else 'FAIL',geometry_sha256=digest,samples=len(rows),required_scope='same or adjacent anatomy, different moving frame; exact saved meshes',cases=rows,pairs=pairs,finite_samples=True))
    print('PAIRS',json.dumps(pairs,ensure_ascii=False),flush=True)

def capture(production=False):
    parts=read_saved();by={p['name']:p for p in parts};digest=sha(OUT/'assembly_meshes.npz');rows=[]
    actual=production_groups() if production else None
    for it in load(OUT/'profiles/capture_interfaces.json'):
        W=np.array(it['W']);inv=np.linalg.inv(W);pre=it['id']
        cs=lambda name:moved(by[name]['s'],inv@F0[by[name]['frame']])
        # Entire connected structural output plus the actual bone link, not cap only.
        family=context().family
        body=union(moved(p['s'],inv@F0[p['frame']]) for p in parts if family(p['frame'])==family(it['output_frame']) and p['role'] in ['structure','rotor','shell'])
        if actual is not None:body=moved(actual[it['output_frame']],inv)
        hardware=[p['name'] for p in parts if p['name'].startswith(pre+'_') and p['role'] not in ['structure','rotor','shell','pcb','connector','magnet'] and not any(t in p['name'] for t in ['capture_','spring_','locknut','nut_washer','end_safety','lock_tab'])]
        fixtures=union(cs(n) for n in hardware)
        local=cs(it['socket']);bolt=cs(it['bolt']);cap=cs(it['cap']);shaft=cs(it['shaft'])
        # Full structural body and local socket are both recorded.
        paths=[]
        for name,solid in [('socket',local),('whole_output_structure',body)]:
            hits=[]
            for d in np.arange(0,40.001,.25):
                overlap=(solid.translate([0,0,d])^fixtures).volume()
                if overlap>.02:hits.append(dict(travel_mm=float(d),intersection_mm3=float(overlap)))
            paths.append(dict(part_set=name,samples=161,travel_mm=40,max_overlap_mm3=max([x['intersection_mm3'] for x in hits] or [0]),first_blocked=hits[0] if hits else None,status='PASS' if not hits else 'FAIL'))
        # Body cannot leave bolt in either axial direction, even at zero friction.
        stops=[];negative=[]
        for sg in [-1,1]:
            hit=None
            for d in np.arange(.1,8.001,.1):
                vol=(body.translate([0,0,d*sg])^bolt).volume()
                if vol>.02:hit=dict(direction=sg,travel_mm=float(d),intersection_mm3=float(vol));break
            stops.append(hit)
        # One-dimensional positive control: retaining bolt deleted -> socket free in outward direction.
        for d in np.arange(0,8.001,.1):negative.append(float((local.translate([0,0,d])^fixtures).volume()))
        # Bolt itself enters along the transverse through-hole after socket is seated.
        obstacle=body+cap+shaft
        bolt_path=[]
        for d in np.arange(0,35.01,.25):
            vol=(bolt.translate([-d,0,0])^obstacle).volume()
            if vol>.02:bolt_path.append(dict(travel_mm=float(d),intersection_mm3=float(vol)))
        row=dict(interface=pre,paths=paths,positive_stops=stops,remove_capture_bolt_negative_control=max(negative)<.02,
            transverse_bolt_path=dict(samples=141,first_blocked=bolt_path[0] if bolt_path else None,max_overlap_mm3=max([x['intersection_mm3'] for x in bolt_path] or [0])),
            status='PASS_GEOMETRY' if all(p['status']=='PASS' for p in paths) and all(stops) and not bolt_path and max(negative)<.02 else 'FAIL')
        rows.append(row);print('CAPTURE',pre,row['status'],[(p['part_set'],p['max_overlap_mm3']) for p in paths],row['transverse_bolt_path']['max_overlap_mm3'],flush=True)
    put(OUT/('verification/production_capture.json' if production else 'verification/capture_and_paths.json'),dict(status='PASS_GEOMETRY' if all(r['status']=='PASS_GEOMETRY' for r in rows) else 'FAIL',geometry_sha256=digest,production_mesh_sha256=sha(OUT/'production_meshes.npz') if production else None,rows=rows,scope='Rigid straight paths; screw thread rotation and spring compliance not simulated. Full connected output and local socket tested separately; no stop is inferred from frame labels. Production mode uses actual manufactured bodies for whole-output checks.'))

def field(q,mp,sp,moment):
    R=Rotation.from_rotvec([0,np.radians(q[0]),0]).as_matrix()@Rotation.from_rotvec([np.radians(q[1]),0,0]).as_matrix()
    r=sp-R@mp;m=R@moment;rnorm=np.linalg.norm(r);u=r/rnorm
    return (3*u*np.dot(u,m)-m)/rnorm**3

def kinematics():
    digest=sha(OUT/'assembly_meshes.npz');rows=[]
    for side in ['l','r']:
        maxerr=0.;maxold=0.;S=np.diag([1.,-1,1.])
        for f in [-65,-30,0,35,70]:
            for d in [-20,0,30]:
                q={**base.NEUTRAL_ANGLES,side+'_wrist_flex':f,side+'_wrist_deviation':d};F=frames(q)
                R=Rotation.from_rotvec([0,math.radians(f),0]).as_matrix()@Rotation.from_rotvec([math.radians(d),0,0]).as_matrix()
                if side=='r':R=S@R@S
                actual=F[side+'_forearm_roll'][:3,:3].T@F[side+'_wrist_deviation'][:3,:3]
                maxerr=max(maxerr,float(np.max(abs(actual-R))))
                old=base.frames(q)[side+'_wrist_flex'][:3,:3]
                maxold=max(maxold,float(Rotation.from_matrix(old.T@F[side+'_wrist_deviation'][:3,:3]).magnitude()*180/math.pi))
        rows.append(dict(side=side,independent_RyRx_error=maxerr,old_chain_max_difference_deg=maxold,status='PASS' if maxerr<1e-10 and maxold>1 else 'FAIL'))
    old=load(BASE/'profiles/device_profile.json');new={a['id']:a['limits_deg'] for a in PROFILE['axes']}
    ranges=all(new[a['id']]==a['limits_deg'] for a in old['axes'])
    bones={n:float(np.linalg.norm(np.array(base.P['hand_'+n])-base.P['lowerarm_'+n])) for n in ['l','r']}
    put(OUT/'verification/kinematics.json',dict(status='PASS' if ranges and all(r['status']=='PASS' for r in rows) else 'FAIL',geometry_sha256=digest,physical_dof=len(new),original_endpoints_retained=ranges,endpoint_count=80,rows=rows,forearm_lengths_mm=bones,forearm_clock_applied_once=True))
    sensors=[]
    for w in load(OUT/'profiles/wrists.json'):
        mp=np.array(w['magnet_local_mm']);sp=np.array(w['sensor_local_mm']);mom=np.array(w['magnet_moment_axis']);minsv=1e9;cond=0;values=[];angles=[]
        for f in np.arange(-65,70.01,1):
            for d in np.arange(-20,30.01,1):
                q=np.array([f,d]);B=field(q,mp,sp,mom);eps=.01
                J=np.column_stack([(field(q+np.eye(2)[k]*eps,mp,sp,mom)-field(q-np.eye(2)[k]*eps,mp,sp,mom))/(2*eps) for k in range(2)])
                sv=np.linalg.svd(J,compute_uv=False);minsv=min(minsv,float(sv[-1]));cond=max(cond,float(sv[0]/sv[-1]));values.append(B);angles.append(q)
        values=np.array(values);angles=np.array(angles);tree=cKDTree(values);dist,idx=tree.query(values,k=6)
        aliases=[]
        for i in range(len(values)):
            for j,d in zip(idx[i,1:],dist[i,1:]):
                sep=np.linalg.norm(angles[i]-angles[j])
                if sep>3 and d<minsv:aliases.append([int(i),int(j),float(sep),float(d)])
        sensors.append(dict(side=w['side'],samples=len(values),min_J_singular_value_per_degree=minsv,max_condition_number=cond,local_rank_2=minsv>1e-9,near_aliases=aliases[:20],global_uniqueness_test='nearest field neighbours, 1 degree finite grid; not continuous proof',status='PASS_IDEAL_MODEL' if minsv>1e-9 and not aliases else 'FAIL',physical_accuracy='UNMEASURED',steel_interference='UNMEASURED'))
        np.savez_compressed(OUT/f'profiles/{w["side"]}_wrist_ideal_LUT.npz',angles_deg=angles,normalized_field=values)
    put(OUT/'verification/wrist_observability.json',dict(status='PASS_IDEAL_MODEL' if all(s['status']=='PASS_IDEAL_MODEL' for s in sensors) else 'FAIL',geometry_sha256=digest,rows=sensors,calibrated=False,scope='Ideal dipole in air only; actual steel, magnet tolerance, IC noise, field range and accuracy require physical calibration. Firmware must reject use of uncalibrated LUT.'))

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('mode',choices=['quick','motion','capture','kinematics']);ap.add_argument('--production',action='store_true',help='For capture: check the final production bodies');a=ap.parse_args()
    if a.mode in ['quick','motion']:main_geometry(a.mode=='quick')
    elif a.mode=='capture':capture(a.production)
    else:kinematics()
