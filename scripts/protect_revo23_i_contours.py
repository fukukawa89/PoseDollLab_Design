"""Confine new internal fairings behind the approved anatomical wall surface."""
from revo23_unified import *

def exterior_guard(key,parts,p,cfg,N):
    item=parts[key];skin=clean_skin(key)
    if skin.is_empty()or key.startswith('frame/hand_'):return md.Manifold()
    definition=next(r for r in read(FROOT/'skins.json')['skins']if r['key']==key)
    if definition['canonical_frame_mm']is None:return md.Manifold()
    A=np.array(definition['canonical_frame_mm']);M=N[item['token']]
    g=canonical(item['body'],M,cfg)
    if g is None:return md.Manifold()
    rows=g[2];s=move(skin,np.linalg.inv(A)@M);v,f=vf(s);mesh=trimesh.Trimesh(v,f,process=False)
    z=np.clip(mesh.triangles_center[:,2],rows[0,0],rows[-1,0]);centers=PchipInterpolator(rows[:,0],rows[:,1:3],axis=0)(z)
    radial=mesh.triangles_center.copy();radial[:,:2]-=centers;radial[:,2]=0
    select=np.einsum('ij,ij->i',mesh.face_normals,radial)>.6*np.linalg.norm(radial,axis=1)
    if not select.any():return md.Manifold()
    m=trimesh.Trimesh(v,f[select],process=False);m.remove_unreferenced_vertices();v=m.vertices;f=m.faces
    z=np.clip(v[:,2],rows[0,0],rows[-1,0]);center=PchipInterpolator(rows[:,0],rows[:,1:3],axis=0)(z)
    d=v.copy();d[:,:2]-=center;d[:,2]=0;d/=np.maximum(np.linalg.norm(d,axis=1)[:,None],1e-9)
    lo=v-d*.08;hi=v+d*25;n=len(v);faces=[f[:,::-1],f+n]
    counts=Counter(tuple(sorted(e))for face in f for e in zip(face,np.roll(face,-1)))
    sides=[]
    for face in f:
        for a,b in zip(face,np.roll(face,-1)):
            if counts[tuple(sorted((a,b)))]==1:sides.extend([[a,b,b+n],[a,b+n,a+n]])
    faces.append(np.asarray(sides));guard=solid(np.vstack([lo,hi]),np.vstack(faces))
    return move(guard,np.linalg.inv(M)@A)

def main():
    parts,p,cfg=load_i();N=frames(p,p['neutral_raw_deg']);out=[];dest=IROOT/'contour_guards';dest.mkdir(exist_ok=True)
    for key,item in parts.items():
        if item['role']!='structure':continue
        guard=exterior_guard(key,parts,p,cfg,N);old=h_part(key);before=item['s'];addition=before-old
        intruded=max(0.,(addition^guard).volume())
        if intruded>.0001:
            # Cut only guard material outside H, without re-unioning its many
            # coincident faces. This preserves the original core exactly.
            after=before-(guard-old);reliefs=[]
            components=[s for s in after.decompose()if abs(s.volume())>.001]
            if any(s.volume()<0 for s in components):
                after,reliefs=open_added_cavities(key,before-guard)
            else:after=max(components,key=lambda s:s.volume())
            assert max(0.,(old-after).volume())<.01,(key,'old core lost')
            record=i_records(key);path=IROOT/(key.replace('/','__')+'.npz');save_s(path,after)
            record.update(candidate_sha256=sha(path),exterior_surface_guard=dict(removed_added_material_mm3=intruded,clearance_inside_original_surface_mm=.08),surface_access_reliefs=reliefs)
            put(path.with_suffix('.json'),record);item['s']=after
        save_s(dest/(key.replace('/','__')+'.npz'),guard)
        remaining=max(0.,((item['s']-old)^guard).volume())
        row=dict(part=key,removed_added_mm3=intruded,remaining_beyond_approved_wall_mm3=remaining,passed=remaining<.03)
        if key.startswith('frame/hand_'):
            A=np.array(next(r for r in read(FROOT/'skins.json')['skins']if r['key']==key)['canonical_frame_mm']);region=move(box([-150,-150,-150],[150,150,-21.501]),np.linalg.inv(N[item['token']])@A)
            row['added_material_in_finger_region_mm3']=max(0.,((item['s']-old)^region).volume());row['passed']&=row['added_material_in_finger_region_mm3']<.03
        out.append(row);print('CONTOUR',key,round(intruded,3),row['passed'],flush=True)
    stage_i();put(IROOT/'external_contours.json',dict(geometry_sha256=sha(IROOT/'assembly.npz'),rows=out,passed=all(r['passed']for r in out),method='Radial guard extending 25 mm outside every approved outer wall face; original H material retained, new material kept inside. Distal finger region separately unchanged.'))

if __name__=='__main__':main()
