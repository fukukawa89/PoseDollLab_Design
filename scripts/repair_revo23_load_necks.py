"""Locally widen measured necks using exact solids, without convex sweep cuts."""
from build_revo23_wire_seats import *
from audit_revo23_load_paths import screen,raster
from scipy.ndimage import label,distance_transform_edt


def inset_free_material(raw,pitch=.4,inset=.8):
    bb=np.array(raw.bounding_box());origin=np.floor((bb[:3]-2)/pitch)*pitch
    shape=tuple((np.ceil((bb[3:]+2-origin)/pitch).astype(int)+1).tolist())
    mask=raster(raw,origin,shape,pitch)
    field=(distance_transform_edt(mask)-distance_transform_edt(~mask))*pitch
    nx,ny,nz=shape
    def sdf(x,y,z):
        u=(x-origin[0])/pitch;v=(y-origin[1])/pitch;w=(z-origin[2])/pitch
        i=int(math.floor(u));j=int(math.floor(v));k=int(math.floor(w))
        if i<0 or j<0 or k<0 or i>=nx-1 or j>=ny-1 or k>=nz-1:return -2.
        a=u-i;b=v-j;c=w-k
        return float(
            (1-a)*((1-b)*((1-c)*field[i,j,k]+c*field[i,j,k+1])+b*((1-c)*field[i,j+1,k]+c*field[i,j+1,k+1]))+
            a*((1-b)*((1-c)*field[i+1,j,k]+c*field[i+1,j,k+1])+b*((1-c)*field[i+1,j+1,k]+c*field[i+1,j+1,k+1])))
    return md.Manifold.level_set(sdf,np.r_[origin,origin+(np.array(shape)-1)*pitch],.7,inset).simplify(.06)


def disconnected_neck(s):
    bb=np.array(s.bounding_box());origin=np.floor(bb[:3]-2)
    shape=tuple((np.ceil(bb[3:]+2-origin).astype(int)+1).tolist())
    mask=raster(s,origin,shape,1.);labels,count=label(mask)
    counts=np.bincount(labels.ravel());counts[0]=0;order=np.argsort(counts)[::-1]
    sets=[np.argwhere(labels==i)+origin for i in order[:8] if counts[i]>100]
    best=None
    for i,a in enumerate(sets):
        for b in sets[i+1:]:
            tree=cKDTree(a);d,idx=tree.query(b);k=int(np.argmin(d))
            # Connect the substantial fragments, not isolated one-cell tips.
            score=d[k]+50/min(len(a),len(b))**.5
            if best is None or score<best[0]:best=(score,(a[idx[k]]+b[k])/2)
    if best is None:raise RuntimeError('No disconnected voxel regions found.')
    return best[1]


def repair(key,parts,p,cfg,FF):
    item=parts[key];current=item['s'];kz=np.load(DHISTORY/'source/retained_interfaces.npz')
    keep=solid(kz[key+'|v'],kz[key+'|f']);skin=local_skin(key,p,cfg)
    audit=screen(key,current,keep,skin,1.);steps=[]
    for attempt in range(5):
        important=[r for r in audit['rows'] if r['land_volume_mm3']>1000]
        worst=min(important,key=lambda r:r['conservative_cut_area_mm2'])
        if worst['conservative_cut_area_mm2']>=100:break
        center=np.array(worst['cut_center_mm']) if worst['connected_voxel_path'] else disconnected_neck(current)
        radius=(9.,13.,18.,23.,28.)[attempt]
        seed=ball(center,radius);raw=seed;bb=np.array(seed.bounding_box());contacts=0
        print('EXACT NECK',key,attempt,center.tolist(),'radius',radius,flush=True)
        for other,pose,ob,_ in obstacle_transforms(key,parts,p,FF,bb):
            hit=raw^ob
            if hit.volume()<.0005:continue
            raw=raw-ob;contacts+=1
            if contacts%8==0:raw=raw.simplify(.025)
            if contacts%50==0:print('EXACT CONTACTS',key,contacts,flush=True)
        print('INSET FREE REGION',key,'contacts',contacts,flush=True)
        raw=inset_free_material(raw)
        candidate=current+raw
        main=[c for c in candidate.decompose() if c.volume()>current.volume()*.8]
        if len(main)!=1:continue
        candidate=main[0]
        result=screen(key,candidate,keep,skin,1.)
        before=min(r['conservative_cut_area_mm2'] for r in important)
        after=min(r['conservative_cut_area_mm2'] for r in result['rows'] if r['land_volume_mm3']>1000)
        accepted=after>before+2
        steps.append(dict(center_body_mm=center,radius_mm=radius,contacts=contacts,
            before_area_mm2=before,after_area_mm2=after,accepted=accepted))
        if accepted:current=candidate;audit=result;item['s']=current
    path=EROOT/(key.replace('/','__')+'.npz')
    backup=EROOT/'checkpoints/before_exact_necks';backup.mkdir(parents=True,exist_ok=True)
    if not (backup/path.name).exists():shutil.copy2(path,backup/path.name)
    v,f=vf(current);assert trimesh.Trimesh(v,f,process=False).is_watertight
    np.savez_compressed(path,v=v,f=f)
    report=read(path.with_suffix('.json'));report['exact_neck_repairs']=steps
    put(path.with_suffix('.json'),report)
    put(EROOT/'load_paths_candidate'/(key.replace('/','__')+'.json'),audit)
    print('NECK FINISHED',key,[(r['land'],round(r['conservative_cut_area_mm2'],2)) for r in audit['rows']],flush=True)


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--keys',nargs='+',required=True);args=ap.parse_args()
    parts,p,cfg=load_e();poses=read(DHISTORY/'profiles/daily_poses.json')['poses']
    poses.update(read(DHISTORY/'profiles/edge_path_poses.json')['poses'])
    FF={k:frames(p,q) for k,q in poses.items()}
    for key in args.keys:repair(key,parts,p,cfg,FF)
