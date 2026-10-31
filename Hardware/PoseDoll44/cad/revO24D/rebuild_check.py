"""Rebuild in memory; do not overwrite the deliverables being tested."""
from validate import *

if __name__=='__main__':
    parts,z,solids=read_assembly();digest=sha(OUT/'assembly_meshes.npz');D=build();lookup={p['name']:p for p in parts};rows=[];missing=set(lookup)
    for p in D.parts:
        old=lookup.get(p['name'])
        if old is None:raise ValueError('Unexpected rebuilt feature '+p['name'])
        missing.discard(p['name']);v,f=a.mesh_data(p['s']);want=z[str(old['i'])+'v'];faces=z[str(old['i'])+'f'];same=v.shape==want.shape and f.shape==faces.shape
        delta=float(np.max(abs(v-want))) if same else None
        rows.append(dict(part=p['name'],same_topology=bool(same and np.array_equal(f,faces)),max_vertex_error_mm=delta,volume_error_mm3=abs(p['s'].volume()-old['volume_mm3'])))
    ok=not missing and all(r['same_topology'] and r['max_vertex_error_mm']<1e-8 and r['volume_error_mm3']<1e-5 for r in rows)
    if sha(OUT/'assembly_meshes.npz')!=digest:raise RuntimeError('Delivered assembly changed during independent rebuild')
    put(OUT/'verification/rebuild_reproducibility.json',dict(status='PASS' if ok else 'FAIL',geometry_sha256=digest,features=len(rows),missing=sorted(missing),rows=rows,scope='Second complete CSG build in memory compared against saved NPZ. All topology and local coordinates checked; no output model overwritten.'))
    print('REBUILD MATCH',ok,len(rows),flush=True)
