"""Union touching printed primitives into review bodies; do not call them print-ready."""
from connections import *

def physical_components(solid):
    """Decompose material bodies, retaining enclosed negative cavity shells.

    Manifold.decompose separates closed boundary components, not always pieces
    of printable material. A cavity must stay with its smallest containing outer
    shell; exporting it alone produces a negative-volume phantom part.
    """
    shells=solid.decompose();positive=[s for s in shells if s.volume()>1e-8];negative=[s for s in shells if s.volume()<-1e-8]
    buckets=[[s] for s in positive]
    for void in negative:
        vb=np.array(void.bounding_box()).reshape(2,3);vv,vf=a.mesh_data(void)
        filled=md.Manifold(md.Mesh64(np.array(vv,dtype=np.float64,copy=True,order='C'),np.array(vf[:,::-1],dtype=np.uint64,copy=True,order='C')))
        candidates=[]
        for i,outer in enumerate(positive):
            b=np.array(outer.bounding_box()).reshape(2,3)
            if np.all(b[0]<=vb[0]+1e-5) and np.all(b[1]>=vb[1]-1e-5):
                overlap=(outer^filled).volume()
                if abs(overlap-filled.volume())<max(1e-6,filled.volume()*1e-5):candidates.append(i)
        if not candidates:raise ValueError('Unassigned enclosed cavity '+str((void.volume(),vb.tolist(),[s.volume() for s in positive])))
        buckets[min(candidates,key=lambda i:positive[i].volume())].append(void)
    result=[md.Manifold.compose(bucket) for bucket in buckets]
    assert all(s.volume()>0 for s in result)
    assert abs(sum(s.volume() for s in result)-solid.volume())<1e-5
    return sorted(result,key=lambda s:-s.volume())
def main():
    parts,z,ss=read_assembly();folder=OUT/'stl_review_bodies';folder.mkdir(exist_ok=True);rows=[]
    for fr in dict.fromkeys(family(p['frame']) for p in parts):
        members=[(p,moved(s,np.linalg.inv(F0[fr])@F0[p['frame']])) for p,s in zip(parts,ss) if family(p['frame'])==fr and p['role'] in ['structure','rotor','shell']]
        if not members:continue
        solid=union(s for p,s in members);comp=physical_components(solid)
        for i,s in enumerate(comp):
            name=fr+'__'+str(i+1).zfill(2);vv,ff=a.mesh_data(s);mesh=trimesh.Trimesh(vv,ff,process=False);mesh.export(folder/(name+'.stl'))
            bounds=np.array(s.bounding_box()).reshape(2,3);ids=[]
            for p,t in members:
                b=np.array(t.bounding_box()).reshape(2,3)
                if np.all(bounds[1]>=b[0]) and np.all(b[1]>=bounds[0]) and (s^t).volume()>.01:ids.append(p['name'])
            screen=None;passed=True
            if s.volume()>2:
                centre=vv.mean(0);_,basis=np.linalg.eigh(np.cov(vv.T));basis[:,0]*=np.linalg.det(basis);local=moved(s,T(-basis.T@centre,basis.T));screen=core(local,.3)
                if len(screen[0]['substantial_core_volumes_mm3'])!=1:screen=core(local,.2)
                passed=len(screen[0]['substantial_core_volumes_mm3'])==1
            specs=sorted({p.get('material','FDM process qualification required') for p,t in members if p['name'] in ids})
            rows.append(dict(body=name,frame=fr,source_primitives=ids,materials=specs,stl='stl_review_bodies/'+name+'.stl',volume_mm3=float(s.volume()),core_screen=screen,status='PASS_SCREEN' if passed else 'REVIEW_REQUIRED'))
        print(fr,len(comp),'bodies',flush=True)
    wanted={r['body']+'.stl' for r in rows}
    for old in folder.glob('*.stl'):
        if old.name not in wanted:
            assert old.resolve().parent==folder.resolve();old.unlink()
    put(OUT/'verification/printed_body_connections.json',dict(status='PASS_SCREEN' if all(x['status']=='PASS_SCREEN' for x in rows) else 'REVIEW_REQUIRED',geometry_sha256=sha(OUT/'assembly_meshes.npz'),bodies=len(rows),rows=rows,cavity_handling='Negative enclosed shells retained inside the containing positive material body; total signed volume conserved.',note='Union overlapping/touching same-rigid-frame printed primitives. Separate bodies require explicit metal interfaces. Review solids, no print orientation, shrink allowance or slicer approval.'))
    print('REVIEW',[(r['body'],r['source_primitives']) for r in rows if r['status']!='PASS_SCREEN'],flush=True)
if __name__=='__main__':main()
