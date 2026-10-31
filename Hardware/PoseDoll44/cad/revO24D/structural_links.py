"""Conservative static screen of the new transfer and its actual cut saddle."""
from strength import *

def descendants(n,root):
    while n:
        if n==root:return True
        n=NODES[n]['parent']
    return False

def section_properties(s,origin,axis,t):
    u=np.array(axis);x=np.cross(u,[1,0,0] if abs(u[0])<.8 else [0,1,0]);x/=np.linalg.norm(x);y=np.cross(u,x);R=np.array([x,y,u]);m=moved(s,T(-R@origin,R));polys=m.slice(t).to_polygons()
    area=cx=cy=ix=iy=ixy=0.;points=[]
    for p in polys:
        p=np.array(p);q=np.roll(p,-1,axis=0);cross=p[:,0]*q[:,1]-q[:,0]*p[:,1]
        area+=cross.sum()/2;cx+=np.sum((p[:,0]+q[:,0])*cross)/6;cy+=np.sum((p[:,1]+q[:,1])*cross)/6
        ix+=np.sum((p[:,1]**2+p[:,1]*q[:,1]+q[:,1]**2)*cross)/12;iy+=np.sum((p[:,0]**2+p[:,0]*q[:,0]+q[:,0]**2)*cross)/12
        ixy+=np.sum((2*p[:,0]*p[:,1]+p[:,0]*q[:,1]+q[:,0]*p[:,1]+2*q[:,0]*q[:,1])*cross)/24;points.extend(p)
    if area<0:area,cx,cy,ix,iy,ixy=[-a for a in [area,cx,cy,ix,iy,ixy]]
    if area<=1e-6:raise ValueError('Missing saddle cross section')
    center=np.array([cx,cy])/area;ix-=area*center[1]**2;iy-=area*center[0]**2;ixy-=area*center[0]*center[1];imin=np.linalg.eigvalsh([[ix,-ixy],[-ixy,iy]])[0];radius=np.linalg.norm(np.array(points)-center,axis=1).max()
    return dict(origin_N_mm=origin+u*t+x*center[0]+y*center[1],axis_N=u,area_mm2=area,I_min_mm4=imin,Z_min_mm3=imin/radius,J_lower_mm4=2*imin,r_max_mm=radius)

def main():
    parts,z,ss=read_assembly();fr='l_clavicle_protract';member=[p for p in parts if descendants(p['frame'],fr) or p['name'].startswith('l_clavicle_z_')]
    masses={n:0. for n in NODES};moments={n:np.zeros(3) for n in NODES}
    for p in member:
        m=p['volume_mm3']*p.get('density_g_mm3',DENSITY[p['role']]);masses[p['frame']]+=m;moments[p['frame']]+=m*np.array(p['mass_centroid_mm'])
    harness=load(OUT/'harness/mass_lumps.json');assert harness['geometry_sha256']==sha(OUT/'assembly_meshes.npz')
    for p in harness['lumps']:
        if descendants(p['frame'],fr):m=p['mass_g'];masses[p['frame']]+=m;moments[p['frame']]+=m*np.array(p['local_mm'])
    mass=sum(masses.values());force=np.array([0,0,-mass/1000*9.80665*1.875]);allcases=cases()
    layout=load(HERE/'clavicle_route.json');route=np.array(layout['points'])+P['clavicle_l'];r=layout['radius_mm'];area=math.pi*r*r;I=math.pi*r**4/4;J=2*I;Z=I/r;length=float(np.linalg.norm(np.diff(route,axis=0),axis=1).sum())
    sections=[]
    for a0,b0 in zip(route[:-1],route[1:]):
        u=(b0-a0)/np.linalg.norm(b0-a0)
        for t in [.15,.5,.85]:sections.append(dict(origin_N_mm=a0+(b0-a0)*t,axis_N=u,area_mm2=area,I_min_mm4=I,Z_min_mm3=Z,J_lower_mm4=J,r_max_mm=r))
    p=next(p for p in parts if p['name']=='left_clavicle_seat');s=moved(ss[p['i']],F0[p['frame']]);u=P['spine_05']-P['spine_04'];u/=np.linalg.norm(u)
    root=P['clavicle_l']+[9,0,-61.5];tip=P['spine_04']+u*25+[0,14,0];axis=(tip-root)/np.linalg.norm(tip-root);seatlength=float(np.linalg.norm(tip-root));seat=[section_properties(s,root,axis,seatlength*f) for f in [.1,.25,.4,.55,.7,.85,.95]]
    specs=[dict(name='left_steel_transfer',frame=fr,sections=sections,allowable=115,E=200000,G=77000,Kt=2,length=length),dict(name='left_printed_saddle',frame=p['frame'],sections=seat,allowable=8,E=1500,G=550,Kt=1.5,length=seatlength)]
    for spec in specs:spec.update(worst_stress_MPa=0.,worst_pose=None,max_moment_Nmm=0.)
    for name,q in allcases:
        F=frames(q);center=sum(F[n][:3,:3]@moments[n]+masses[n]*F[n][:3,3] for n in NODES)/mass
        for spec in specs:
            d=F[spec['frame']]@np.linalg.inv(F0[spec['frame']])
            for section in spec['sections']:
                origin=(d@np.r_[section['origin_N_mm'],1])[:3];axis=d[:3,:3]@section['axis_N'];moment=np.cross(center-origin,force)
                torsion=abs(np.dot(moment,axis));bending=np.linalg.norm(moment-axis*np.dot(moment,axis));normal=abs(np.dot(force,axis))/section['area_mm2']+bending/section['Z_min_mm3'];shear=torsion*section['r_max_mm']/section['J_lower_mm4']
                vm=spec['Kt']*math.sqrt(normal**2+3*shear**2)
                if vm>spec['worst_stress_MPa']:spec['worst_stress_MPa']=vm;spec['worst_pose']=name
                spec['max_moment_Nmm']=max(spec['max_moment_Nmm'],float(np.linalg.norm(moment)))
    for spec in specs:
        imin=min(s['I_min_mm4'] for s in spec['sections']);jmin=min(s['J_lower_mm4'] for s in spec['sections']);amin=min(s['area_mm2'] for s in spec['sections']);L=spec['length'];M=spec['max_moment_Nmm'];F=np.linalg.norm(force)
        # Integrate an upper bound using the worst moment, minimum stiffness
        # and total path length; include torsional rotation conservatively.
        angle=M*L/(spec['E']*imin)+M*L/(spec['G']*jmin);bound=angle*L+F*L/(spec['E']*amin)
        spec.update(rotation_upper_bound_deg=math.degrees(angle),translation_upper_bound_mm=bound,stress_margin=spec['allowable']/spec['worst_stress_MPa'],status='PASS_CONDITIONAL' if spec['worst_stress_MPa']<=spec['allowable'] and bound<=1 else 'FAIL')
    put(OUT/'verification/structural_links.json',dict(status='PASS_CONDITIONAL' if all(s['status']=='PASS_CONDITIONAL' for s in specs) else 'FAIL',geometry_sha256=sha(OUT/'assembly_meshes.npz'),supported_solid_mass_g=mass,gravity_factor=1.875,case_count=len(allcases),rows=specs,scope='Static self-weight screen. Steel transfer nominal D8.5 beam sections use Kt=2 at bends; joined socket roots additionally require the actual material-core check. Saddle uses seven sections of the actual relieved mesh, minimum principal inertia and Kt=1.5. Worst-moment/path-length bounds overestimate elastic movement. Not whole-body FEA, fatigue or process qualification. Steel E=200 GPa, yield>=230 MPa; printed E=1.5 GPa and allowable 8 MPa are explicit design assumptions.'))
    print('STRUCTURAL LINKS',[(s['name'],s['status'],s['worst_stress_MPa'],s['translation_upper_bound_mm']) for s in specs],flush=True)

if __name__=='__main__':main()
