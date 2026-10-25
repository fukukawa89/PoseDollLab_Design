"""Ground support and reaction loads; no fixed pelvis reaction is introduced."""
from strength import *
from scipy.spatial import ConvexHull
from scipy.optimize import minimize

def main():
    parts,z,ss=read_assembly();digest=sha(OUT/'assembly_meshes.npz')
    masses=[];centres=[]
    for p in parts:
        masses.append(p['volume_mm3']*p.get('density_g_mm3',DENSITY[p['role']]));centres.append((p['frame'],np.array(p['mass_centroid_mm'])))
    lumps=OUT/'harness/mass_lumps.json'
    if lumps.exists() and load(lumps).get('geometry_sha256')==digest:
        for p in load(lumps)['lumps']:masses.append(p['mass_g']);centres.append((p['frame'],np.array(p['local_mm'])))
    masses=np.array(masses);Mtot=float(masses.sum());contact=[]
    for p in parts:
        if not p['name'].endswith(('heel_sole','toe_pad')):continue
        v=z[str(p['i'])+'v'];F=FA[p['frame']];w=v@F[:3,:3].T+F[:3,3];low=w[:,2].min();pick=w[abs(w[:,2]-low)<1e-5]
        pick=np.unique(pick.round(6),axis=0);hull=ConvexHull(pick[:,:2]);contact.extend(dict(frame=p['frame'],point=pt.tolist(),part=p['name']) for pt in pick[hull.vertices])
    ground=np.array([r['point'] for r in contact]);hull=ConvexHull(ground[:,:2]);equ=hull.equations
    descendants={n:{n} for n in NODES}
    for n in reversed(PROFILE['nodes']):
        if n['parent']:descendants[n['parent']]|=descendants[n['id']]
    sets={a['id']:np.array([fr in descendants[a['id']] for fr,c in centres]) for a in PROFILE['axes']}
    rsets={a['id']:np.array([r['frame'] in descendants[a['id']] for r in contact]) for a in PROFILE['axes']}
    ji={j['axis_id']:j for j in load(OUT/'profiles/joint_interfaces.json')};bc={}
    for p in parts:
        if p['role']=='bearing':bc.setdefault(bearing_axis(p['name']),[]).append((p['frame'],np.mean(np.array(p['bounds_mm']),axis=0)))
    results={a['id']:dict(axis=a['id'],gravity_Nm=0.,bending_Nm=0.,bearing_reaction_N=0.,joint_force_N=0.,worst_hold_pose=None,worst_bearing_pose=None) for a in PROFILE['axes']}
    legaxes=[a['id'] for a in PROFILE['axes'] if any(w in a['id'] for w in ['hip_','knee_','ankle_','toe_'])]
    samples=[(n,q) for n,q in cases() if not any(abs(q.get(k,0))>1e-8 for k in legaxes)]
    if '--quick' in sys.argv:samples=[('neutral',NEUTRAL_ANGLES)]
    rows=[];Aeq=np.vstack([np.ones(len(ground)),ground[:,0],ground[:,1]])
    for name,q in samples:
        F=frames(q);cm=np.array([F[fr][:3,:3]@p+F[fr][:3,3] for fr,p in centres]);com=np.average(cm,axis=0,weights=masses);margin=float(np.min(-(equ[:,:2]@com[:2]+equ[:,2])))
        row=dict(pose=name,COM_mm=com,support_margin_mm=margin,stable_nominal=margin>0,accepted_unassisted_standing=margin>=8)
        if margin<8:rows.append(row);continue
        # Equal-compliance minimum-norm nonnegative reactions on measured sole vertices.
        beq=np.r_[1,com[:2]];sol=minimize(lambda x:float(x@x),np.full(len(ground),1/len(ground)),jac=lambda x:2*x,constraints=[dict(type='eq',fun=lambda x:Aeq@x-beq,jac=lambda x:Aeq)],bounds=[(0,1)]*len(ground),method='SLSQP',options=dict(ftol=1e-12,maxiter=150))
        if not sol.success:raise RuntimeError(sol.message)
        forces=sol.x*Mtot/1000*9.80665;row.update(reactions_N=forces,force_equilibrium_error_N=abs(forces.sum()-Mtot/1000*9.80665),moment_equilibrium_error_Nmm=float(np.linalg.norm(np.sum(ground[:,:2]*forces[:,None],axis=0)-com[:2]*forces.sum())))
        for a in PROFILE['axes']:
            key=a['id'];o=F[key][:3,3];axis=F[key][:3,:3]@np.array(a['axis']);mask=sets[key];rm=rsets[key]
            fg=np.array([0.,0.,-masses[mask].sum()*9.80665/1000]);torque=np.sum(np.cross((cm[mask]-o)/1000,np.c_[np.zeros(mask.sum()),np.zeros(mask.sum()),-masses[mask]*9.80665/1000]),axis=0)
            for point,force in zip(ground[rm],forces[rm]):fg[2]+=force;torque+=np.cross((point-o)/1000,[0,0,force])
            r=results[key];t=abs(float(torque@axis));r['joint_force_N']=max(r['joint_force_N'],float(np.linalg.norm(fg)))
            if t>r['gravity_Nm']:r.update(gravity_Nm=t,worst_hold_pose=name)
            if key in ji:
                c=np.mean([F[fr][:3,:3]@point+F[fr][:3,3] for fr,point in bc[key]],axis=0);m=torque+np.cross((o-c)/1000,fg);bend=float(np.linalg.norm(m-axis*(m@axis)));rad=float(np.linalg.norm(fg-axis*(fg@axis)));reaction=rad/2+bend*1000/ji[key]['bearing_span_mm'];r['bending_Nm']=max(r['bending_Nm'],bend)
                if reaction>r['bearing_reaction_N']:r.update(bearing_reaction_N=reaction,worst_bearing_pose=name)
        rows.append(row)
    neutral=next(r for r in rows if r['pose']=='neutral');passed=neutral['accepted_unassisted_standing'] and max(r.get('moment_equilibrium_error_Nmm',0) for r in rows)<1e-5
    report=dict(status='PASS_QUASI_STATIC_CONDITIONAL' if passed else 'FAIL',geometry_sha256=digest,solid_and_harness_mass_g=Mtot,foot_contacts=contact,support_polygon_mm=ground[hull.vertices,:2],standing_margin_requirement_mm=8,neutral=neutral,samples=len(rows),accepted_standing_samples=sum(r['accepted_unassisted_standing'] for r in rows),rows=rows,joint_loads=list(results.values()),scope='Equal-compliance minimum-norm nonnegative vertex reactions are one admissible equilibrium model, not a measured contact-stiffness distribution. Flat rigid horizontal floor, A legs and stable upper-body configurations, no payload or external cable pull. Gravity and nonnegative ground reactions balance; pelvis carries no external fixture force. Unstable poses require posture adjustment or manual handling; this is not balance control or impact/foot-slip qualification.')
    put(OUT/('history/integration_search/standing_quick.json' if '--quick' in sys.argv else 'verification/standing_ground_loads.json'),report)
    print('STANDING',report['status'],'mass',Mtot,'COM',neutral['COM_mm'],'margin',neutral['support_margin_mm'],'cases',len(rows),flush=True)
    print('ANKLES',[(r['axis'],r['gravity_Nm'],r['bending_Nm']) for r in results.values() if 'ankle' in r['axis']],flush=True)
if __name__=='__main__':main()
