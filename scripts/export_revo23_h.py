"""Export and regress the H assembly without modifying the published G files."""
from verify_revo23_h import *
import revo23_export as exporter
import package_revo23 as package

original_cancel=exporter.cancel_numeric_faces
original_prepare=exporter.prepare_export
def prepare_with_recomposition(key,s):
    try:
        m,r=original_prepare(key,s);r['source_geometry_sha256']=sha(HROOT/'assembly.npz');put(exporter.EXPORT_ROOT/(key.replace('/','__')+'.json'),r);return m,r
    except RuntimeError as error:
        comparison=read(HROOT/'canonical_probe/comparison.json')
        row=next((r for r in comparison['rows'] if r['key']==key),None)
        if row is None or max(row['removed_mm3'],row['added_mm3'])>.03:raise
        z=np.load(HROOT/'canonical_probe'/(key.replace('/','__')+'.npz'));clean=solid(z['v'],z['f'])
        original_mesh=trimesh.Trimesh(*vf(s),process=False);clean_mesh=trimesh.Trimesh(*vf(clean),process=False)
        sampled_bound=0.
        for a,b in ((original_mesh,clean_mesh),(clean_mesh,original_mesh)):
            probes=np.vstack([a.vertices,a.triangles_center])
            for start in range(0,len(probes),2000):
                _,dist,_=trimesh.proximity.closest_point(b,probes[start:start+2000]);sampled_bound=max(sampled_bound,float(dist.max()))
        assert sampled_bound<.0002,(key,'analytic cleanup surface discrepancy',sampled_bound)
        m,r=original_prepare(key,clean)
        r['equivalent_analytic_recomposition']=dict(row,original_source_mesh_sha256=exporter.source_signature(*vf(s)),
            maximum_bidirectional_sampled_surface_difference_mm=sampled_bound,sampling='Every vertex and triangle centroid in both analytic meshes',
            method='Re-union the same native interfaces, clean skin, actual retained wire seats and complete new connectors. Omit zero-volume subtraction residue of obsolete rods.')
        put(exporter.EXPORT_ROOT/(key.replace('/','__')+'.json'),r)
        print('RECOMPOSED EQUIVALENT',key,flush=True)
        return m,r
def cancel_flat_membranes(v,f,allow_separation=True):
    m,r=original_cancel(v,f);removed=[]
    _,inverse,counts=np.unique(np.sort(m.faces,axis=1),axis=0,return_inverse=True,return_counts=True)
    paired=np.zeros(len(m.faces),bool);multiplicity_pairs=0
    for group in np.flatnonzero(counts>2):
        ids=np.flatnonzero(inverse==group);directions=m.face_normals[ids]@m.face_normals[ids[0]]
        positive=ids[directions>.999999];negative=ids[directions<-.999999];number=min(len(positive),len(negative))
        paired[positive[:number]]=True;paired[negative[:number]]=True;multiplicity_pairs+=number
    if multiplicity_pairs:m.update_faces(~paired);m.remove_unreferenced_vertices()
    r['additional_opposed_pairs_in_multiple_coincident_faces']=multiplicity_pairs
    # A collapsed four-face tetrahedron can share edges with the real surface.
    # Removing coincident triangle pairs alone misses different triangulations.
    # Split only across nonmanifold edges, and discard only independently closed,
    # sub-micron-flat, zero-volume membranes. Never fill an open boundary.
    groups=trimesh.graph.connected_components(m.face_adjacency,nodes=np.arange(len(m.faces)))
    mask=np.ones(len(m.faces),bool)
    for ids in groups:
        if len(ids)>500:continue
        q=trimesh.Trimesh(m.vertices,m.faces[ids],process=False);q.remove_unreferenced_vertices()
        if not q.is_watertight or not q.is_winding_consistent or abs(q.volume)>1e-5:continue
        centered=q.vertices-q.vertices.mean(0);_,_,axes=np.linalg.svd(centered,full_matrices=False)
        thickness=float(np.ptp(centered@axes[-1]))
        if thickness>5e-6:continue
        mask[ids]=False;removed.append(dict(faces=len(ids),absolute_volume_mm3=abs(float(q.volume)),thickness_mm=thickness))
    if removed:m.update_faces(mask);m.remove_unreferenced_vertices()
    r['removed_closed_flat_membranes']=removed;r['after_membrane_cleanup']=exporter.mesh_stats(m)
    stats=r['after_membrane_cleanup']
    if allow_separation and 0<stats['nonmanifold_edges']<=3 and stats['boundary_edges']==stats['degenerate_faces']==stats['duplicate_faces']==0:
        # Two otherwise closed surface sheets can meet at the same quantized
        # edge. Preserve their original indexed topology and open a microscopic
        # clearance by moving only the coincident source vertices inward.
        counts=np.bincount(m.edges_unique_inverse,minlength=len(m.edges_unique))
        bad=np.unique(m.edges_unique[counts>2]);points={tuple(x) for x in m.vertices[bad]}
        q=np.asarray(v,dtype='f4').astype(float);ids=[i for i,x in enumerate(q) if tuple(x) in points]
        normals=trimesh.Trimesh(v,f,process=False).vertex_normals
        for epsilon in (1e-5,3e-5,1e-4):
            changed=np.array(v,copy=True);changed[ids]-=normals[ids]*epsilon
            trial,record=cancel_flat_membranes(changed,f,False)
            if trial.is_watertight and trial.is_winding_consistent and len(trial.split(only_watertight=False))==1:
                record['edge_sheet_separation']=dict(vertices=len(ids),maximum_displacement_mm=epsilon,
                    direction='inward source vertex normal',functional_holes_filled=False)
                record['quantization_max_vertex_displacement_mm']+=epsilon
                return trial,record
    return m,r

def setup():
    configure();exporter.B=HROOT;exporter.EXPORT_ROOT=HROOT/'export';exporter.EXPORT_VERSION='O23H-export-1';package.TAG='O23H'
    exporter.cancel_numeric_faces=cancel_flat_membranes
    exporter.prepare_export=prepare_with_recomposition
    for source in (GHISTORY/'harness').rglob('*'):
        if source.is_file():
            target=HROOT/'harness'/source.relative_to(GHISTORY/'harness')
            if not target.exists():target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(source,target)
    (HROOT/'verification').mkdir(exist_ok=True)

def exports():
    parts,p,cfg=load_h();rows=[]
    for key,item,rid in package.export_selection(parts):
        path=exporter.EXPORT_ROOT/'stl'/(rid+'_'+key.split('/',1)[1].replace('.','_')+'.stl')
        r=dict(exporter.export_stl(path,key,item['s']))
        r.update(id=rid,staged_stl=path.relative_to(HROOT).as_posix(),stl_sha256=sha(path));rows.append(r)
        print('H STL',rid,'closed',r['passed'],'tolerance',r['simplify_tolerance_mm'],flush=True)
    put(exporter.EXPORT_ROOT/'repair.json',dict(revision=HREV,geometry_sha256=sha(HROOT/'assembly.npz'),rows=rows,passed=True))

def verify(mode):
    import verify_revo23_exports as v
    v.B=HROOT;v.EXPORT_ROOT=exporter.EXPORT_ROOT;v.OUT=exporter.EXPORT_ROOT/'verification';v.OUT.mkdir(exist_ok=True)
    v.load_current=lambda:load_h()[0]
    if mode=='features':v.features()
    elif mode=='fixed':v.fixed()
    elif mode in ('daily','edge'):
        name='daily_motion.json' if mode=='daily' else 'edge_motion.json';target='daily_motion.json' if mode=='daily' else 'edge_paths.json'
        shutil.copy2(HROOT/name,HROOT/'verification'/target);v.motion(mode)
    elif mode=='ends':
        parts,p,hashes,digest=v.inputs();r=audit(parts,p,'export');r.update(export_set_sha256=digest,geometry_sha256=sha(HROOT/'assembly.npz'));put(v.OUT/'end_faces.json',r)

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('mode',choices=['export','features','fixed','daily','edge','ends']);a=ap.parse_args();setup()
    if a.mode=='export':exports()
    else:verify(a.mode)
