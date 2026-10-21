"""Retain broad paths inside the checked shoulder volume, remove unused bulk."""
from audit_revo23_load_paths import *
from scipy.sparse.csgraph import dijkstra


def trim(key,p,cfg):
    path=EROOT/(key.replace('/','__')+'.npz');z=np.load(path);full=solid(z['v'],z['f'])
    oldparts,_,_=load_d();old=oldparts[key]['s']
    kz=np.load(DHISTORY/'source/retained_interfaces.npz');keep=solid(kz[key+'|v'],kz[key+'|f'])
    lands=sorted([c for c in keep.decompose() if c.volume()>50],key=lambda c:-c.volume())
    bb=np.array(full.bounding_box());pitch=1.
    origin=np.floor(bb[:3]-2);shape=tuple((np.ceil(bb[3:]+2-origin).astype(int)+1).tolist())
    mask=raster(full,origin,shape,pitch);coords,ids,a,b=grid_graph(mask);n=len(coords)
    depth=distance_transform_edt(mask)
    strength=np.minimum(depth[tuple(coords[a].T)],depth[tuple(coords[b].T)])
    cost=1+30/np.maximum(.4,strength)**3
    src=raster(lands[0],origin,shape,pitch)&mask;dst=raster(lands[1],origin,shape,pitch)&mask
    paths=[];penalty=np.ones(n)
    for route_number in range(8):
        weights=cost*np.maximum(penalty[a],penalty[b])
        graph=coo_matrix((np.r_[weights,weights],(np.r_[a,b],np.r_[b,a])),shape=(n,n)).tocsr()
        dist,previous,_=dijkstra(graph,directed=True,indices=ids[src],min_only=True,return_predecessors=True)
        targets=ids[dst];end=int(targets[np.argmin(dist[targets])]);assert np.isfinite(dist[end])
        order=[];cursor=end
        while cursor>=0:
            order.append(cursor);cursor=int(previous[cursor])
        points=coords[order]+origin
        points=points[::3] if len(points)>4 else points
        if np.linalg.norm(points[-1]-(coords[order[-1]]+origin))>.01:points=np.vstack([points,coords[order[-1]]+origin])
        paths.append(points)
        used=np.zeros(shape,bool);used[tuple(coords[order].T)]=True
        distance=distance_transform_edt(~used)
        penalty*=1+15*np.exp(-distance[tuple(coords.T)]**2/18)
        penalty=np.minimum(penalty,1e6)
    baseline=read(EROOT/'load_paths_candidate'/(key.replace('/','__')+'.json'))
    target_area=min(100.,min(r['conservative_cut_area_mm2'] for r in baseline['rows'])*.9)
    target_z=min(80.,min(r['conservative_section_modulus_mm3'] for r in baseline['rows'])*.85)
    selected=full;result=baseline;radius_used=None
    for radius in (5.,7.,9.,12.):
        corridor=union([capsule(a,b,radius) for points in paths for a,b in zip(points,points[1:])])
        corridor=corridor+union([ball(pt,12) for points in paths for pt in (points[0],points[-1])])
        candidate=old+(full^corridor)
        if len([s for s in candidate.decompose() if s.volume()>.001])!=1:continue
        report=screen(key,candidate,keep,local_skin(key,p,cfg),1.)
        if all(r['conservative_cut_area_mm2']>=target_area and
               r['conservative_section_modulus_mm3']>=target_z for r in report['rows']):
            selected=candidate;result=report;radius_used=radius;break
    backup=EROOT/'checkpoints/before_collar_mass_trim';backup.mkdir(parents=True,exist_ok=True)
    if not (backup/path.name).exists():shutil.copy2(path,backup/path.name)
    v,f=vf(selected);np.savez_compressed(path,v=v,f=f)
    report=read(path.with_suffix('.json'));report['mass_trim']=dict(
        method='A wide interior path clipped to the previously checked material volume',
        source_volume_mm3=full.volume(),final_volume_mm3=selected.volume(),path_radius_mm=radius_used,
        paths_body_mm=paths,removed_volume_mm3=max(0,full.volume()-selected.volume()),
        did_not_add_material_outside_checked_volume=True)
    put(path.with_suffix('.json'),report)
    put(EROOT/'load_paths_candidate'/(key.replace('/','__')+'.json'),result)
    print('MASS TRIM',key,'volume',round(full.volume()),'->',round(selected.volume()),'radius',radius_used,flush=True)


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--keys',nargs='*');args=ap.parse_args()
    parts,p,cfg=load_d()
    for key in (args.keys or ('frame/clavicle_r.protract_frame','frame/clavicle_l.protract_frame',
                'frame/clavicle_r','frame/clavicle_l')):trim(key,p,cfg)
