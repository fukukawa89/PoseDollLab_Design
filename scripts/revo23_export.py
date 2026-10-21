"""Topology-safe STL export; the checked assembly and nominal dimensions stay fixed.

No hole filling or volumetric remeshing. Remove only zero-area facets and pairs
of exactly coincident, oppositely oriented facets after STL's float32 weld.
Where short edges still collapse, simplify within at most 0.001 mm first.
"""
from build_revo23 import *

EXPORT_ROOT=B/'design/export_repair_G'
EXPORT_VERSION='O23G-export-repair-1'

def mesh_stats(m):
    counts=np.bincount(m.edges_unique_inverse,minlength=len(m.edges_unique))
    return dict(vertices=len(m.vertices),triangles=len(m.faces),watertight=bool(m.is_watertight),
        winding_consistent=bool(m.is_winding_consistent),boundary_edges=int((counts==1).sum()),
        nonmanifold_edges=int((counts>2).sum()),degenerate_faces=int((~m.nondegenerate_faces()).sum()),
        duplicate_faces=int((~m.unique_faces()).sum()),volume_mm3=float(m.volume))

def source_signature(v,f):
    return hashlib.sha256(np.asarray(v,dtype='<f8').tobytes()+np.asarray(f,dtype='<u8').tobytes()).hexdigest()

def cancel_numeric_faces(v,f):
    q=v.astype('f4').astype(float);m=trimesh.Trimesh(q,f,process=True)
    before=mesh_stats(m)
    m.update_faces(m.nondegenerate_faces())
    _,inv,cnt=np.unique(np.sort(m.faces,axis=1),axis=0,return_inverse=True,return_counts=True)
    remove=np.zeros(len(m.faces),bool);pairs=0
    for i in np.flatnonzero(cnt>1):
        ix=np.flatnonzero(inv==i)
        # Do not delete arbitrary overlapping or same-facing triangles.
        if len(ix)==2 and np.linalg.norm(m.face_normals[ix].sum(0))<1e-8:
            remove[ix]=True;pairs+=1
    m.update_faces(~remove);m.remove_unreferenced_vertices()
    return m,dict(before_cleanup=before,removed_opposed_face_pairs=pairs,
        quantization_max_vertex_displacement_mm=float(np.linalg.norm(q-v,axis=1).max()))

def prepare_export(key,s):
    EXPORT_ROOT.mkdir(parents=True,exist_ok=True)
    name=key.replace('/','__');cache=EXPORT_ROOT/(name+'.npz');record=cache.with_suffix('.json')
    v,f=vf(s);signature=source_signature(v,f)
    if cache.exists() and record.exists():
        r=read(record)
        if r.get('export_version')==EXPORT_VERSION and r['source_mesh_sha256']==signature and r['mesh_cache_sha256']==sha(cache):
            n=np.load(cache);return trimesh.Trimesh(n['v'],n['f'],process=False),r
    base=s;rebuild=None
    if key=='o22/controller_housing':
        # Existing case construction dimensions, ports, posts, mount ears and
        # wire seats are re-evaluated directly, without the obsolete boss cut.
        from rebuild_revo23_export_case import clean_case
        base=clean_case()
        removed=max(0.,(s-base).volume());added=max(0.,(base-s).volume())
        assert removed<1e-6 and added<1e-6,(removed,added)
        rebuild=dict(method='Re-evaluate identical analytic case features; discard legacy zero-thickness Boolean membranes.',
            removed_mm3=removed,added_mm3=added,source_components=len(s.decompose()),clean_components=len(base.decompose()))
    attempts=[]
    for tol in (0,1e-6,1e-5,1e-4,1e-3):
        c=base.simplify(tol) if tol else base
        cv,cf=vf(c);m,rr=cancel_numeric_faces(cv,cf);after=mesh_stats(m)
        rr.update(simplify_tolerance_mm=tol,after_cleanup=after);attempts.append(rr)
        if not (after['watertight'] and after['winding_consistent'] and after['degenerate_faces']==0 and after['duplicate_faces']==0):continue
        components=m.split(only_watertight=False)
        if len(components)!=1 or m.volume<=0:continue
        clean=solid(m.vertices,m.faces)
        if clean.status()!=md.Error.NoError:continue
        r=dict(key=key,export_version=EXPORT_VERSION,source_geometry_sha256=sha(B/'assembly.npz'),
            source_mesh_sha256=signature,source=mesh_stats(trimesh.Trimesh(v,f,process=False)),
            attempts=attempts,case_rebuild=rebuild,simplify_tolerance_mm=tol,
            surface_displacement_bound_mm=tol+rr['quantization_max_vertex_displacement_mm'],
            exported=after,components=1,passed=True,
            no_hole_filling=True,no_voxel_remeshing=True,nominal_geometry_edited=False)
        np.savez_compressed(cache,v=m.vertices,f=m.faces);r['mesh_cache_sha256']=sha(cache);put(record,r)
        return m,r
    raise RuntimeError(('No safe STL repair',key,attempts))

def export_stl(path,key,s):
    m,r=prepare_export(key,s);path=Path(path);path.parent.mkdir(exist_ok=True,parents=True)
    path.write_bytes(trimesh.exchange.stl.export_stl(m))
    reread=trimesh.load(path,process=True);check=mesh_stats(reread)
    assert check['watertight'] and check['winding_consistent'] and check['degenerate_faces']==check['duplicate_faces']==0,(key,check)
    assert source_signature(reread.triangles,np.zeros((0,3),int))==source_signature(m.triangles,np.zeros((0,3),int))
    return r

def stage_exports():
    from present_revo23 import load_current
    from package_revo23 import export_selection
    from probe_revo23_stl import snapshot
    snapshot();rows=[]
    for key,part,rid in export_selection(load_current()):
        stem=key.split('/',1)[1].replace('.','_');path=EXPORT_ROOT/'stl'/f'{rid}_{stem}.stl'
        r=dict(export_stl(path,key,part['s']));r.update(id=rid,staged_stl=path.relative_to(B).as_posix(),stl_sha256=sha(path));rows.append(r)
        print('STAGED STL',rid,flush=True)
    put(EXPORT_ROOT/'repair.json',dict(geometry_sha256=sha(B/'assembly.npz'),rows=rows,passed=True))

if __name__=='__main__':stage_exports()
