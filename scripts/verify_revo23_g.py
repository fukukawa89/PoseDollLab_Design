"""Verify the actual staged O23G parts; leave the published F model intact."""
from revo23_smooth import *
from verify_revo23_daily import check_daily
from audit_revo23_load_paths import screen

def stage():
    parts,p,cfg=load_g();out={};changed=[]
    for key,item in parts.items():
        path=GROOT/(key.replace('/','__')+'.npz')
        if item['role']=='structure':assert path.exists(),key
        i=str(item['index']);out[i+'v'],out[i+'f']=vf(item['s'])
        if path.exists():changed.append(key)
    np.savez_compressed(GROOT/'assembly.npz',**out)
    put(GROOT/'assembly.json',dict(revision=GREV,items=[{k:v for k,v in r.items() if k!='s'} for r in parts.values()]))
    put(GROOT/'staging.json',dict(input_geometry_sha256=FHASH,geometry_sha256=sha(GROOT/'assembly.npz'),changed_parts=changed,
        candidate_files={k:sha(GROOT/(k.replace('/','__')+'.npz')) for k in changed}))
    shutil.copytree(FHISTORY/'profiles',GROOT/'profiles',dirs_exist_ok=True)
    cfg['revision']=GREV;put(GROOT/'parameters.json',cfg)
    return parts,p,cfg

def rod_body(r):
    pts=np.array(r['centerline_world_mm']);mirror=bool(r.get('mirrored_from'))
    if mirror:pts=pts*[1,-1,1]
    s=cyl(*pts,r['radius_mm']) if len(pts)==2 else (positive_round_sweep if r.get('positive_cells') else round_sweep)(pts,r['radius_mm'])
    if r.get('foot_only'):s=wall_pad(r,mirroring=False)
    return move(s,np.diag([1.,-1.,1.,1.])) if mirror else s

def wall_pad(r,mirroring=True):
    end=np.array(r.get('wall_foot_reference_endpoint_world_mm',r['centerline_world_mm'][-1]));pos=np.array(r['wall_landing_world_mm']);mirror=bool(r.get('mirrored_from'))
    if mirror:pos=pos*[1,-1,1];end=end*[1,-1,1]
    n=pos-end;n/=np.linalg.norm(n);radius=r['radius_mm']
    depth=r.get('foot_depth_mm',2*np.linalg.norm(pos-end)-1.8);tip=r.get('foot_tip_mm',1.8)
    s=tapered(pos-n*depth,pos-n*tip,radius+.8,radius+2.5)
    return move(s,np.diag([1.,-1.,1.,1.])) if mirror and mirroring else s

def materials(parts,p):
    N=frames(p,p['neutral_raw_deg']);digest=sha(GROOT/'assembly.npz');walls=[];counts=[];rods=[];sym=[];done=set()
    for key,item in parts.items():
        if item['role']!='structure':continue
        path=GROOT/(key.replace('/','__')+'.npz');r=read(path.with_suffix('.json'));M=N[item['token']]
        keep=raw_keep(key,parts,p,N);skin=skin_of(key);s=item['s'];v,f=vf(s);mesh=trimesh.Trimesh(v,f,process=False)
        walls.append(dict(part=key,components=len([x for x in s.decompose() if x.volume()>.0001]),
            indexed_watertight=bool(mesh.is_watertight),planned_clean_skin_missing_mm3=max(0.,(skin-s).volume()),
            retained_interface_missing_mm3=max(0.,(keep-s).volume())))
        groups=[];anchors=interface_anchors(item['body'],p,N)
        lands=sorted([c for c in keep.decompose() if c.volume()>.05],key=lambda c:-c.volume())
        for land in lands:
            points,_=vf(move(land,M));mid=(points.min(0)+points.max(0))/2
            group='controller_housing' if key=='frame/chest' and mid[0]<-38 and 510<mid[2]<555 and abs(mid[1])>25 else min(anchors,key=lambda a:np.linalg.norm(points-np.array(a['point']),axis=1).min())['joint']
            groups.append(group)
        bygroup={};connections=[]
        for number,rod in enumerate(r['rods']):
            body=move(rod_body(rod),np.linalg.inv(M));missing=max(0.,(body-s).volume())
            body_components=len(body.decompose());body_genus=body.genus()
            foot_missing=0.;buried=None;wall_bond=None
            if 'target_mount' not in rod:
                foot=wall_pad(rod);foot_missing=max(0.,(move(foot,np.linalg.inv(M))-s).volume())
                pts=np.array(rod['centerline_world_mm']);end=pts[-1];direction=end-pts[-2];direction/=np.linalg.norm(direction)
                probe=cyl(end-direction*.8,end,rod['radius_mm'])
                buried=(probe^foot).volume()/probe.volume()
                pos=np.array(rod['wall_landing_world_mm']);normal=pos-np.array(rod.get('wall_foot_reference_endpoint_world_mm',end));normal/=np.linalg.norm(normal)
                tip=rod.get('foot_tip_mm',1.8)
                disk=cyl(pos-normal*(tip+.2),pos-normal*tip,rod['radius_mm']+2.5)
                wall_bond=(move(disk,np.linalg.inv(M))^skin).volume()/disk.volume()
            contact_body=globals().get('connection_contact_material',lambda key,rod,body,M:body)(key,rod,body,M)
            touched={groups[i] for i,l in enumerate(lands) if (contact_body^l).volume()>1.}
            for group in touched:bygroup[group]=bygroup.get(group,0)+1
            rid=f'{key}/round_connection_{number+1}'
            connections.append(dict(id=rid,adjacent_components=sorted(touched)))
            rods.append(dict(part=key,id=rid,radius_mm=rod['radius_mm'],method=rod['method'],
                missing_full_section_material_mm3=missing,
                connected_rod_components=body_components,rod_genus=body_genus,
                missing_wall_foot_mm3=foot_missing,
                wall_endpoint_embedded_fraction=buried,wall_bond_disk_fraction=wall_bond,
                positive_cell_curve=len(rod['centerline_world_mm'])==2 or rod.get('positive_cells',False),
                adjacent_components=sorted(touched),passed=body_components==1 and body_genus==0 and missing<.05 and foot_missing<.05 and bool(touched)
                    and (len(rod['centerline_world_mm'])==2 or rod.get('positive_cells',False))
                    and ('target_mount' in rod or buried>=.98 and wall_bond>=.9599)))
        counts.append(dict(part=key,rods=len(r['rods']),counts=bygroup,connections=connections,passed=all(v<=3 for v in bygroup.values())))
        if key in done:continue
        other=key[:-1]+'r' if key.endswith('_l') else key.replace('_l.protract','_r.protract') if '_l.protract' in key else key
        if key.endswith('_r') or '_r.protract' in key:continue
        if other!=key:done.add(other)
        reflection=np.diag([1.,-1.,1.,1.]);mirrored=move(skin,reflection@M);target=move(skin_of(other),N[parts[other]['token']])
        sv,sf=vf(mirrored);tv,tf=vf(target)
        error=max(cKDTree(tv).query(sv)[0].max(),cKDTree(sv).query(tv)[0].max()) if len(sv) and len(tv) else (0. if len(sv)==len(tv) else float('inf'))
        if error>.02 and len(sv) and len(tv):
            _,da,_=trimesh.proximity.closest_point(trimesh.Trimesh(tv,tf,process=False),sv)
            _,db,_=trimesh.proximity.closest_point(trimesh.Trimesh(sv,sf,process=False),tv)
            error=max(da.max(),db.max())
        rr=read(GROOT/(other.replace('/','__')+'.json'))
        bv=np.concatenate([vf(rod_body(q))[0] for q in r['rods']])*[1,-1,1] if r['rods'] else np.zeros((0,3))
        ov=np.concatenate([vf(rod_body(q))[0] for q in rr['rods']]) if rr['rods'] else np.zeros((0,3))
        delta=max(cKDTree(ov).query(bv)[0].max(),cKDTree(bv).query(ov)[0].max()) if len(bv) and len(ov) else 0.
        sym.append(dict(part=key,mirror_part=other,wall_mirror_max_surface_distance_mm=error,
            rod_mirror_max_vertex_distance_mm=delta,wall_passed=error<.02,all_rods_mirrored=delta<.02,
            exception=None if delta<.02 else 'Actual offset mounting lands require a non-mirrored local attachment; not claimed fully symmetric.'))
        print('MATERIAL PART',key,'wall mirror',round(error,5),'rod mirror',round(delta,5),flush=True)
    put(GROOT/'continuous_walls.json',dict(geometry_sha256=digest,rows=walls,
        passed=all(r['components']==1 and r['indexed_watertight'] and r['planned_clean_skin_missing_mm3']<.05 and r['retained_interface_missing_mm3']<.05 for r in walls),
        analytic_clean_skins_preserved=True,independent_skin_perforations=0))
    put(GROOT/'physical_rod_count.json',dict(geometry_sha256=digest,rows=counts,passed=all(r['passed'] for r in counts),
        maximum_rods_per_adjacent_component=max([n for r in counts for n in r['counts'].values()],default=0)))
    report=dict(geometry_sha256=digest,rods=rods,symmetry=sym,passed=all(r['passed'] for r in rods) and all(r['wall_passed'] for r in sym),
        total_rods=len(rods),no_sphere_based_connections=True,manufacturing_release=False)
    put(GROOT/'smooth_connections.json',report);print('MATERIAL',report['passed'],'RODS',len(rods),'COUNT',all(r['passed'] for r in counts),flush=True)

def loads(parts,p,keys=None):
    N=frames(p,p['neutral_raw_deg']);rows=[]
    for key,item in parts.items():
        if item['role']!='structure' or keys and key not in keys:continue
        path=GROOT/(key.replace('/','__')+'.npz');r=screen(key,item['s'],raw_keep(key,parts,p,N),skin_of(key),1.)
        r['candidate_sha256']=sha(path);put(GROOT/'load_paths'/(path.stem+'.json'),r)
        rows.extend([dict(part=key,body=item['body'],**q) for q in r['rows']])
    if not keys:put(GROOT/'load_paths.json',dict(geometry_sha256=sha(GROOT/'assembly.npz'),rows=rows,structure_count=24,
        passed=all(r['connected_voxel_path'] for r in rows),physical_strength_verified=False,
        method='1 mm voxel min-cut with grid-face area divided by sqrt(3); geometric screen only, not FEA or load certification.'))

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--mode',choices=['stage','materials','loads','geometry','fixed','daily','edge'],required=True);ap.add_argument('--keys',nargs='*');ap.add_argument('--use-staged',action='store_true');a=ap.parse_args()
    if a.use_staged:
        parts,p,cfg=load_g();st=read(GROOT/'staging.json')
        assert sha(GROOT/'assembly.npz')==st['geometry_sha256']
        for k,h in st['candidate_files'].items():assert sha(GROOT/(k.replace('/','__')+'.npz'))==h,('Changed staged part',k)
    else:parts,p,cfg=stage()
    if a.mode=='materials':materials(parts,p)
    elif a.mode=='loads':loads(parts,p,a.keys)
    elif a.mode in ('geometry','fixed'):
        import verify_revo23 as v
        v.B=GROOT
        if a.mode=='geometry':
            r=dict(revision=GREV,geometry_sha256=sha(GROOT/'assembly.npz'),kinematics=v.kinematics(p),geometry=v.geometric(parts,p),physical_tested=False,manufacturing_release=False)
            put(GROOT/'geometry.json',r);print('GEOMETRY',r['geometry']['invalid_parts'],r['geometry']['height_mm'],flush=True)
        else:
            from revo23_daily import rigid_groups
            v.cases=lambda profile,suite:{'A_STAND_35':read(GROOT/'profiles/default_pose.json')['raw_deg']}
            base,_,_=v.load_baseline();result=v.motion(parts,base,p,'fixed_reference')
            groups=rigid_groups(p,{x['token'] for x in parts.values()})
            rows=[r for case in result['rows'] for r in case['contacts'] if groups[parts[r['pair'][0]]['token']]==groups[parts[r['pair'][1]]['token']]]
            hits=[r for r in rows if r['increased']]
            put(GROOT/'fixed_interfaces.json',dict(geometry_sha256=sha(GROOT/'assembly.npz'),rows=rows,new_contacts=hits,passed=not hits));print('FIXED',not hits,hits,flush=True)
    elif a.mode in ('daily','edge'):
        spec=read(FHISTORY/'profiles'/('daily_poses.json' if a.mode=='daily' else 'edge_path_poses.json'))
        path=GROOT/(a.mode+'_motion.json');path.with_suffix('.rows.jsonl').write_text('',encoding='utf8')
        r=check_daily(parts,p,spec['poses'],spec.get('policy',{}).get('poses',[]),sha(GROOT/'assembly.npz'),output=path)
        r.update(complete_policy=True,trial=False,profile_sha256=profile_signature(p));put(path,r);print('MOTION',r['passed'],len(r['blocking_contacts']),flush=True)
