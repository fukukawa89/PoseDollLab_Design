"""Export I with the bounded numerical cleanup used for H; no broad mesh repair."""
from verify_revo23_i import *
import export_revo23_h as common

def sew_collapsed_slits(mesh,record):
    """Retriangulate only zero-width three-edge slits caused by float welding."""
    changes=[];maximum=0.
    for _ in range(16):
        counts=np.bincount(mesh.edges_unique_inverse,minlength=len(mesh.edges_unique))
        boundary=mesh.edges_unique[counts==1]
        if not len(boundary):break
        changed=False
        for group in trimesh.graph.connected_components(boundary,nodes=np.unique(boundary)):
            if len(group)!=3:continue
            ids=list(group);v=mesh.vertices.copy();f=mesh.faces.copy()
            pairs=list(itertools.combinations(ids,2));a,c=max(pairs,key=lambda e:np.linalg.norm(v[e[0]]-v[e[1]]));b=next(i for i in ids if i not in (a,c))
            short=min(pairs,key=lambda e:np.linalg.norm(v[e[0]]-v[e[1]]))
            if np.linalg.norm(v[short[0]]-v[short[1]])<5e-6:
                distance=float(np.linalg.norm(v[short[0]]-v[short[1]]));f[f==short[1]]=short[0]
                q=trimesh.Trimesh(v,f,process=True);q.update_faces(q.nondegenerate_faces());q.remove_unreferenced_vertices()
                changes.append(dict(kind='collapse_quantized_edge',displacement_mm=distance));maximum=max(maximum,distance);mesh=q;changed=True;break
            d=v[c]-v[a];t=float((v[b]-v[a])@d/(d@d));projection=v[a]+t*d;width=float(np.linalg.norm(v[b]-projection))
            if not 0<t<1 or width>5e-6:continue
            face_ids=np.flatnonzero(np.any(f==a,axis=1)&np.any(f==c,axis=1))
            if len(face_ids)!=1:continue
            index=int(face_ids[0]);face=f[index];other=next(i for i in face if i not in (a,c))
            if other==b:continue
            j=next(j for j in range(3)if {int(face[j]),int(face[(j+1)%3])}=={a,c})
            u,w=int(face[j]),int(face[(j+1)%3]);v[b]=projection
            f=np.vstack([np.delete(f,index,axis=0),[u,b,other],[b,w,other]])
            mesh=trimesh.Trimesh(v,f,process=True);changes.append(dict(kind='split_existing_face_at_collinear_vertex',slit_width_mm=width));maximum=max(maximum,width);changed=True;break
        if not changed:break
    if changes:
        record['collapsed_slit_retriangulation']=changes
        record['quantization_max_vertex_displacement_mm']+=maximum
    return mesh,record

def quantized_cleanup(v,f):
    if len(f)>150000:
        # Let the bounded analytic simplification pass run first on dense
        # coplanar arrangements instead of enumerating every collapsed sheet.
        q=v.astype('f4').astype(float)
        return trimesh.Trimesh(q,f,process=True),dict(
            deferred_to_analytic_simplification=True,
            quantization_max_vertex_displacement_mm=float(np.linalg.norm(q-v,axis=1).max()))
    mesh,record=sew_collapsed_slits(*common.cancel_flat_membranes(v,f))
    def valid(m):
        stats=common.exporter.mesh_stats(m)
        return stats['watertight'] and stats['winding_consistent'] and stats['degenerate_faces']==stats['duplicate_faces']==0 and len(m.split(only_watertight=False))==1
    if valid(mesh):return mesh,record
    # Weld sub-micron sliver boundaries consistently before STL float32
    # conversion. No face is added and no opening is filled. Independent
    # exported-solid differences and all functional checks still apply.
    for digits in (6,5,4):
        snapped=np.round(v,digits);candidate,r=sew_collapsed_slits(*common.cancel_flat_membranes(snapped,f))
        stats=common.exporter.mesh_stats(candidate)
        if not valid(candidate) and 0<stats['nonmanifold_edges']<=32 and stats['boundary_edges']==stats['degenerate_faces']==stats['duplicate_faces']==0:
            counts=np.bincount(candidate.edges_unique_inverse,minlength=len(candidate.edges_unique))
            bad=np.unique(candidate.edges_unique[counts>2]);points={tuple(x)for x in candidate.vertices[bad]}
            quantized=snapped.astype('f4').astype(float);ids=[i for i,x in enumerate(quantized)if tuple(x)in points]
            normals=trimesh.Trimesh(snapped,f,process=False).vertex_normals
            for epsilon in (1e-5,3e-5,1e-4):
                separated=snapped.copy();separated[ids]-=normals[ids]*epsilon
                trial,report=sew_collapsed_slits(*common.cancel_flat_membranes(separated,f))
                if valid(trial):
                    candidate,r=trial,report;r['local_coincident_sheet_separation']=dict(vertices=len(ids),maximum_displacement_mm=epsilon)
                    r['quantization_max_vertex_displacement_mm']+=epsilon
                    break
        if not valid(candidate):continue
        displacement=float(np.linalg.norm(snapped-v,axis=1).max())
        r['decimal_grid_cleanup']=dict(grid_mm=10.**-digits,maximum_vertex_shift_mm=displacement)
        r['quantization_max_vertex_displacement_mm']+=displacement
        return candidate,r
    return mesh,record

def setup():
    common.HROOT=IROOT;common.HREV=IREV;common.GHISTORY=IHISTORY;common.load_h=load_i;common.configure=configure
    common.setup();common.package.TAG='O23I';common.exporter.EXPORT_VERSION='O23I-export-2'
    common.exporter.cancel_numeric_faces=quantized_cleanup
    def prepare(key,s):
        if key in ('frame/waist','frame/pelvis','frame/forearm_r','frame/clavicle_r.protract_frame'):
            return prepare_sensitive_voids(key,s)
        m,r=common.original_prepare(key,s);r['source_geometry_sha256']=sha(IROOT/'assembly.npz')
        put(common.exporter.EXPORT_ROOT/(key.replace('/','__')+'.json'),r);return m,r
    common.exporter.prepare_export=prepare

def prepare_sensitive_voids(key,s):
    e=common.exporter;root=e.EXPORT_ROOT;stem=key.replace('/','__');path=root/(stem+'.npz');meta=path.with_suffix('.json')
    sv,sf=vf(s);signature=e.source_signature(sv,sf);version='O23I-verified-void-retention-1'
    if meta.exists()and path.exists():
        r=read(meta)
        if r.get('export_version')==version and r['source_mesh_sha256']==signature and r['mesh_cache_sha256']==sha(path):
            z=np.load(path);r['source_geometry_sha256']=sha(IROOT/'assembly.npz');put(meta,r);return trimesh.Trimesh(z['v'],z['f'],process=False),r
    base=s;prior_bound=0.;void=md.Manifold()
    if key in ('frame/waist','frame/pelvis'):
        z=np.load(root/'void_recut'/(stem+'.npz'));base=solid(z['v'],z['f'])
        prior_bound=read(root/'before_slit_cleanup'/(stem+'.json'))['surface_displacement_bound_mm']
        for seat in read(IROOT/'harness/wire_seats.json')['seats']:
            if seat['part']!=key:continue
            w=seat['reserved_channel_width_mm'];void+=move(box([-w/2-3.1,.6,-1.7],[w/2+3.1,2.4,1.7]),np.array(seat['transform_body_mm']))
    elif key=='frame/clavicle_r.protract_frame':
        z=np.load(root/'S20_union_H.npz');base=solid(z['v'],z['f'])
        prior_bound=read(root/(stem+'.json'))['surface_displacement_bound_mm']
    attempts=[]
    for tol in (0,1e-6,1e-5,2e-5,5e-5,1e-4,2e-4,3e-4,5e-4,1e-3):
        c=base.simplify(tol)if tol else base
        if not void.is_empty():c-=void
        cv,cf=vf(c);m,rr=quantized_cleanup(cv,cf);stats=e.mesh_stats(m);bound=prior_bound+tol+rr['quantization_max_vertex_displacement_mm']
        row=dict(simplify_tolerance_mm=tol,stats=stats,surface_bound_mm=bound,cleanup=rr);attempts.append(row)
        if not stats['watertight']or not stats['winding_consistent']or stats['degenerate_faces']or stats['duplicate_faces']or bound>=.0011:continue
        components=sorted(m.split(only_watertight=False),key=lambda x:-x.volume);islands=[]
        if len(components)>1:
            if len(components)>3:continue
            valid_islands=True
            for island in components[1:]:
                if not 0<island.volume<1e-4 or len(island.faces)>12 or max(island.extents)>.5:
                    valid_islands=False;break
                _,distance,_=trimesh.proximity.closest_point(components[0],np.vstack([island.vertices,island.triangles_center]));gap=float(distance.max())
                if gap>.03:valid_islands=False;break
                islands.append(dict(vertices=island.vertices,faces=island.faces,volume_mm3=float(island.volume),maximum_surface_distance_mm=gap))
            if not valid_islands:continue
            m=components[0];stats=e.mesh_stats(m)
        clean=solid(m.vertices,m.faces);difference=abs(clean.volume()-s.volume())/s.volume();row['volume_relative_difference']=difference
        if difference>=1e-5:continue
        if key=='frame/clavicle_r.protract_frame':
            row['retained_native_missing_mm3']=max(0.,(native_keep(key)-clean).volume())
            if row['retained_native_missing_mm3']>=.05:continue
        r=dict(key=key,export_version=version,source_geometry_sha256=sha(IROOT/'assembly.npz'),source_mesh_sha256=signature,
            source=e.mesh_stats(trimesh.Trimesh(sv,sf,process=False)),attempts=attempts,simplify_tolerance_mm=tol,
            surface_displacement_bound_mm=bound+max([x['maximum_surface_distance_mm']for x in islands]or[0]),main_surface_displacement_bound_mm=bound,numeric_island_removal=islands,
            exported=stats,components=1,passed=True,no_hole_filling=True,no_voxel_remeshing=True,nominal_geometry_edited=False,
            functional_void_retention='Existing CAD tie-slot planes recut after simplification; right forearm uses finer intermediate simplification only.')
        np.savez_compressed(path,v=m.vertices,f=m.faces);r['mesh_cache_sha256']=sha(path);put(meta,r);return m,r
    put(root/(stem+'_failed_retention.json'),dict(attempts=attempts));raise RuntimeError(('No faithful void-preserving export',key))

def verify(mode):
    if mode!='ends':return common.verify(mode)
    import verify_revo23_exports as v
    v.B=IROOT;v.EXPORT_ROOT=IROOT/'export';v.OUT=IROOT/'export/verification';v.OUT.mkdir(exist_ok=True);v.load_current=lambda:load_i()[0]
    parts,p,hashes,digest=v.inputs();r=end_faces(parts,p,'export');r.update(export_set_sha256=digest)
    put(v.OUT/'end_faces.json',r)

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('mode',choices=['export','features','fixed','daily','edge','ends']);a=ap.parse_args();setup()
    if a.mode=='export':common.exports()
    else:verify(a.mode)
