"""Read-only diagnosis and isolated export-conditioning trials for O23G."""
from package_revo23 import *
import shutil, time

WORK=B/'design/export_repair_G'
SNAP=B/'history/O23G_before_export_repair_20261021'

def snapshot():
    if (SNAP/'snapshot.json').exists():
        assert sha(B/'assembly.npz')==read(SNAP/'snapshot.json')['geometry_sha256']
        return
    names=['assembly.npz','assembly.json','DELIVERY.json','DESIGN.zh-CN.md','SMOOTH_CONNECTIONS.zh-CN.md','结构件清单.csv','附件清单.csv']
    for d in ('review_stl','review_3mf','profiles','harness','verification'):
        names += [p.relative_to(B).as_posix() for p in (B/d).rglob('*') if p.is_file() and (d in ('review_stl','review_3mf','profiles','harness') or p.suffix=='.json')]
    for rel in names:
        dst=SNAP/rel;dst.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(B/rel,dst)
    shutil.copy2(CFG,SNAP/'parameters.json')
    put(SNAP/'snapshot.json',dict(geometry_sha256=sha(B/'assembly.npz'),profile_sha256=sha(B/'profiles/device_profile.json'),files={rel:sha(SNAP/rel) for rel in names}))

def stats(m):
    counts=np.bincount(m.edges_unique_inverse,minlength=len(m.edges_unique))
    return dict(vertices=len(m.vertices),faces=len(m.faces),watertight=bool(m.is_watertight),winding=bool(m.is_winding_consistent),boundary_edges=int((counts==1).sum()),nonmanifold_edges=int((counts>2).sum()),degenerate_faces=int((~m.nondegenerate_faces()).sum()),duplicate_faces=int((~m.unique_faces()).sum()),volume_mm3=float(m.volume))

def trial(s,tol):
    c=s.simplify(tol) if tol else s
    v,f=vf(c);q=v.astype('f4').astype(float)
    mesh=trimesh.Trimesh(q,f,process=True)
    before=stats(mesh)
    # Only remove zero-area and repeated triangles after the actual float32 weld.
    mesh.update_faces(mesh.nondegenerate_faces());mesh.update_faces(mesh.unique_faces());mesh.remove_unreferenced_vertices()
    after=stats(mesh)
    return mesh,dict(tolerance=tol,unwelded_vertices=len(v),quantization_collapsed_vertices=len(v)-len(np.unique(q,axis=0)),before=before,after=after)

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--ids',nargs='*');a=ap.parse_args();snapshot();WORK.mkdir(parents=True,exist_ok=True)
    parts=load_current();rows=[]
    for key,part,rid in export_selection(parts):
        if a.ids and rid not in a.ids:continue
        s=part['s'];v,f=vf(s);stem=key.split('/',1)[1].replace('.','_');old=trimesh.load(B/'review_stl'/f'{rid}_{stem}.stl',process=True)
        row=dict(id=rid,key=key,source=stats(trimesh.Trimesh(v,f,process=False)),original_stl=stats(old),trials=[])
        for tolerance in (0,1e-6,1e-5,1e-4,.001,.005,.01):
            mesh,r=trial(s,tolerance);row['trials'].append(r)
            print(rid,tolerance,r['before']['watertight'],r['after']['watertight'],'bad edges',r['before']['nonmanifold_edges'],'degenerate',r['before']['degenerate_faces'],flush=True)
            if r['after']['watertight'] and r['after']['winding']:
                np.savez_compressed(WORK/f'{rid}_trial.npz',v=mesh.vertices,f=mesh.faces)
                break
        rows.append(row);put(WORK/'diagnosis.json',dict(geometry_sha256=sha(B/'assembly.npz'),rows=rows))

if __name__=='__main__':main()
