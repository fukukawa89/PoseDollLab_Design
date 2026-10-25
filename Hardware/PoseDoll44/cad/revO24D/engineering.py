"""Independent export-axis, gravity and interface budgets. No measured ratings."""
from validate import *

def bearing_axis(name):
    side=name[:2] if name.startswith(('l_','r_')) else ''
    short=name[len(side):]
    for pre,key in [('clavicle_z','clavicle_protract'),('clavicle_x','clavicle_elevate'),('shoulder_pitch','shoulder_flex'),('shoulder_swing','shoulder_abduct'),('humeral','upperarm_roll'),('elbow','elbow_flex'),('forearm','forearm_roll'),('hip_abduction','hip_abduct'),('hip_pitch','hip_flex'),('hip_twist','hip_roll'),('knee','knee_flex'),('ankle_shoulder_pitch','ankle_roll'),('ankle_shoulder_swing','ankle_flex'),('toe','toe_flex')]:
        if side and short.startswith(pre+'_'):return side+key
    for pre,kind in [('lumbar','lumbar'),('thorax','thorax'),('neck','neck')]:
        if name.startswith(pre+'_shoulder_pitch_'):return kind+('_side' if kind in ['thorax','neck'] else '_flex')
        if name.startswith(pre+'_shoulder_swing_'):return kind+('_flex' if kind in ['thorax','neck'] else '_side')
        if name.startswith(pre+'_humeral_'):return kind+'_yaw'
    raise ValueError(name)

def axes(parts,z):
    fitted=[]
    for p in parts:
        if p['role']!='bearing':continue
        key=bearing_axis(p['name']);v=z[str(p['i'])+'v'];o=v.mean(0);ev,U=np.linalg.eigh(np.cov(v.T));_,i,j=min((abs(ev[i]-ev[j]),i,j) for i,j in [(0,1),(0,2),(1,2)]);ax=U[:,({0,1,2}-{i,j}).pop()]
        fitted.append(dict(part=p['name'],frame=p['frame'],axis_id=key,local_point=o,local_axis=ax))
    maxdist=maxdir=0;rows=[]
    for pn,q in [(n,p['angles']) for n,p in poses().items()]:
        F=frames(q)
        for p in fitted:
            mf=F[p['frame']];pf=F[p['axis_id']];o=mf[:3,:3]@p['local_point']+mf[:3,3];d=mf[:3,:3]@p['local_axis'];want=pf[:3,:3]@NODES[p['axis_id']]['axis']
            dis=float(np.linalg.norm(np.cross(pf[:3,3]-o,d)));ang=float(np.linalg.norm(np.cross(d,want)))
            maxdist=max(maxdist,dis);maxdir=max(maxdir,ang)
            rows.append(dict(pose=pn,part=p['part'],axis=p['axis_id'],line_offset_mm=dis,sin_direction_error=ang))
    wrists=[]
    for side in ['l','r']:
        points=[]
        for name in [side+'_W01',side+'_W02']:
            # CSG cut-edge vertices lie inside spherical facets; fit the original
            # R11 outer vertices, not the nearby bore/neck intersection edges.
            p=next(x for x in parts if x['name']==name);v=z[str(p['i'])+'v'];rr=np.linalg.norm(v,axis=1);points.append(v[abs(rr-11)<.0001])
        v=np.unique(np.vstack(points).round(9),axis=0)
        if len(v)<100 or np.min(np.ptp(v,axis=0))<15:raise RuntimeError('Insufficient spherical surface coverage')
        def fit(v):
            x=np.linalg.lstsq(np.c_[2*v,np.ones(len(v))],np.sum(v*v,1),rcond=None)[0];return x[:3],math.sqrt(x[3]+np.dot(x[:3],x[:3]))
        center,radius=fit(v);bad,_=fit(v+[1,0,0]);maxoff=0
        for pp in poses().values():
            F=frames(pp['angles']);w=F[side+'_wrist_flex'];global_c=w[:3,:3]@center+w[:3,3]
            maxoff=max(maxoff,*[np.linalg.norm(global_c-F[side+'_'+ax][:3,3]) for ax in ['wrist_deviation','wrist_flex']])
        wrists.append(dict(side=side,sphere_vertices=len(v),outer_vertex_selection_tolerance_mm=.0001,fit_center_local_mm=center,fit_radius_mm=radius,max_axis_origin_error_mm=maxoff,one_mm_mesh_shift_detected=bool(np.linalg.norm(bad)>0.999)))
    covered=sorted({p['axis_id'] for p in fitted});put(OUT/'verification/physical_axes.json',dict(status='PASS' if len(covered)==36 and maxdist<1e-6 and maxdir<1e-6 and all(w['max_axis_origin_error_mm']<1e-6 and w['one_mm_mesh_shift_detected'] for w in wrists) else 'FAIL',geometry_sha256=sha(OUT/'assembly_meshes.npz'),bearing_axes_covered=covered,wrist_dof_covered=4,max_line_error_mm=maxdist,max_sin_direction_error=maxdir,samples=len(rows),fits=fitted,wrists=wrists,rows=rows,scope='PCA fit to actual exported annular bearing vertices, transformed through every named pose. Wrist sphere fitted from actual outer facets; its two constrained axes intersect the fitted centre. No encoder accuracy claim. 1 mm mesh translation negative control.'))
    print('PHYSICAL AXES',len(covered),maxdist,maxdir,flush=True)


if __name__=='__main__':
    parts,z,solids=read_assembly();axes(parts,z)
    from strength import main as current_loads
    current_loads()
