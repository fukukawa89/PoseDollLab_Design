"""Actual mesh cross-sections, rather than named/averaged support centre lines."""
from validate import *

def fit_sections(p,vertices,faces,shift=None):
    g=p['bone_link'];b0,b1=[P[n] for n in g['bones']];u=b1-b0;u/=np.linalg.norm(u)
    ex=np.cross(u,[1,0,0] if abs(u[0])<.8 else [0,1,0]);ex/=np.linalg.norm(ex);ey=np.cross(u,ex)
    matrix=F0[p['frame']];v=vertices@matrix[:3,:3].T+matrix[:3,3]
    if shift is not None:v+=shift
    mesh=trimesh.Trimesh(v,faces,process=False);rows=[]
    for origin in g['gauge_world_mm']:
        origin=np.array(origin);section=mesh.section(plane_origin=origin,plane_normal=u);candidates=[]
        for path in section.discrete if section is not None else []:
            if len(path)<16 or np.linalg.norm(path[0]-path[-1])>.001:continue
            points=np.c_[(path-origin)@ex,(path-origin)@ey]
            x=np.linalg.lstsq(np.c_[2*points,np.ones(len(points))],np.sum(points**2,axis=1),rcond=None)[0]
            radius=math.sqrt(max(0,x[2]+np.dot(x[:2],x[:2])));radial=np.linalg.norm(points-x[:2],axis=1)
            residual=float(np.max(abs(radial-radius)))
            if min(abs(radius-g[k]) for k in ['inner_radius_mm','outer_radius_mm'])>.1 or residual>.08:continue
            center=origin+ex*x[0]+ey*x[1];error=float(np.linalg.norm(np.cross(center-b0,u)))
            candidates.append(dict(center_world_N_mm=center,point_line_error_mm=error,fitted_radius_mm=radius,max_radial_residual_mm=residual,section_points=len(path)))
        rows.append(min(candidates,key=lambda r:r['max_radial_residual_mm']) if candidates else dict(point_line_error_mm=1e9,missing_circular_section=True))
    return rows

def main():
    parts,z,solids=read_assembly();rows=[];mutation=[];max_pose_error=0.
    for p in parts:
        if 'bone_link' not in p:continue
        v=z[str(p['i'])+'v'];f=z[str(p['i'])+'f'];sections=fit_sections(p,v,f)
        b0,b1=[P[n] for n in p['bone_link']['bones']];u=b1-b0;u/=np.linalg.norm(u);shift=np.cross(u,[0,1,0]);shift/=np.linalg.norm(shift)
        bad=fit_sections(p,v,f,shift);mutation.append(dict(part=p['name'],one_mm_shift_detected=all(x['point_line_error_mm']>.9 for x in bad)))
        for q in poses().values():
            delta=frames(q['angles'])[p['frame']]@np.linalg.inv(F0[p['frame']]);a0=(delta@np.r_[b0,1])[:3];direction=delta[:3,:3]@u
            for row in sections:
                if 'center_world_N_mm' not in row:continue
                center=(delta@np.r_[row['center_world_N_mm'],1])[:3]
                max_pose_error=max(max_pose_error,float(np.linalg.norm(np.cross(center-a0,direction))))
        rows.append(dict(part=p['name'],bones=p['bone_link']['bones'],sections=sections,status='PASS' if all(s['point_line_error_mm']<.02 for s in sections) else 'FAIL'))
    passed=len(rows)==9 and all(r['status']=='PASS' for r in rows) and all(r['one_mm_shift_detected'] for r in mutation)
    put(OUT/'verification/bone_link_alignment.json',dict(status='PASS' if passed else 'FAIL',geometry_sha256=sha(OUT/'assembly_meshes.npz'),actual_tubes=len(rows),cross_sections=sum(len(r['sections']) for r in rows),max_pose_line_error_mm=max_pose_error,rows=rows,mutation_controls=mutation,
        scope='Eight limb main tubes and one thoracic tube: circles fitted from actual exported mesh sections in three gauge planes, then transformed through all named poses. Short fork roots and metal-preload bridges remain local clearance structures, not claimed to be coaxial rods. Lumbar/neck/clavicle short spans are occupied by joint modules; bearing-axis audit separately checks them.'))
    print('BONE LINKS',passed,[(r['part'],r['status']) for r in rows],flush=True)

if __name__=='__main__':main()
