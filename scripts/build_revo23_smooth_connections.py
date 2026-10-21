"""Search complete, unclipped round struts and broad, buried wall feet."""
from revo23_smooth import *
from scipy.optimize import linear_sum_assignment


def build_pair(key,other=None,radius=4.0,seated_start=False,actual_neighbours=False,append_mount=None,minimum_cut=0.):
    parts,p,cfg=load_g();N=frames(p,p['neutral_raw_deg']);reflection=np.diag([1.,-1.,1.,1.])
    keys=list(dict.fromkeys([key]+([other] if other else [])));local={};keeps={};skins={};spaces={};landsets={}
    for k in keys:
        M=N[parts[k]['token']];local[k]=M
        keeps[k]=move(raw_keep(k,parts,p,N),M);skins[k]=move(skin_of(k),M)
        landsets[k]=sorted([s for s in keeps[k].decompose() if s.volume()>.05],key=lambda s:-s.volume())
        spaces[k]=Space(k,parts,p,N,replace_neighbour_structures=not actual_neighbours)
    matching={}
    if other:
        cost=np.array([[np.linalg.norm(np.mean(np.array(a.bounding_box()).reshape(2,3),axis=0)-np.mean(np.array(move(b,reflection).bounding_box()).reshape(2,3),axis=0)) for b in landsets[other]]for a in landsets[key]])
        ii,jj=linear_sum_assignment(cost);matching=dict(zip(map(int,ii),map(int,jj)))
    landings=skin_landings(key,parts,p,cfg,N,skin_of(key),radius)
    skinless=skins[key].is_empty()
    if skinless:
        root=landsets[key][0]
        commonroot=root^move(landsets[other][matching[0]],reflection) if other else root
        center=np.mean(np.array(landsets[key][-1].bounding_box()).reshape(2,3),axis=0)
        for point in source_points(commonroot,limit=100):
            normal=point-center;normal/=np.linalg.norm(normal)
            landings.append(dict(point=point,normal=normal,pad=md.Manifold(),foot_body=root,
                bond_fraction=1.,outer_point=point,target_mount=0))
    usable=[];rejected={}
    for target in landings:
        ok,why=spaces[key].clear(target['pad'])
        if ok and other:ok,why=spaces[other].clear(move(target['pad'],reflection))
        if ok:usable.append(target)
        else:rejected[why['part']]=rejected.get(why['part'],0)+1
    landings=usable;print('CLEAR LANDINGS',key,len(landings),rejected,flush=True)
    material={k:[keeps[k],skins[k]] for k in keys};records={k:[] for k in keys};fails={}
    own_wire={}
    if append_mount is not None:
        from seat_revo23_round_roots import wire_spaces
        for k in keys:
            material[k]=[move(parts[k]['s'],local[k])]
            records[k]=read(GROOT/(k.replace('/','__')+'.json'))['rods']
            own_wire[k]=move(wire_spaces(k),local[k])
    processed=set();free=None
    for li,land in enumerate(landsets[key]):
        if li in processed:continue
        if append_mount is not None and li!=append_mount:continue
        if skinless and li==0:continue
        paired=bool(other)
        if other==key:
            paired=matching.get(li)!=li
            if paired:processed.add(matching[li])
        direct=(land^skins[key]).volume()>80
        if paired:direct=direct and (landsets[other][matching[li]]^skins[other]).volume()>80
        if direct and append_mount is None:
            print('DIRECT LAND',key,li,flush=True);continue
        common=land
        if paired and li in matching:
            common=land^move(landsets[other][matching[li]],reflection)
            if common.volume()<5:
                print('NO SHARED ANCHOR',key,li,'common',common.volume(),flush=True)
                raise RuntimeError(('No shared anchor',key,li))
        sources=source_points(common,limit=100)
        if append_mount is not None:
            old=[np.array(r['centerline_world_mm'])[0] for r in records[key] if r['mount']==li]
            sources=np.array([a for a in sources if all(np.linalg.norm(a-b)>4 for b in old)])
        options=[]
        for a in sources:
            for j,target in enumerate(landings):
                b=target['point'];length=np.linalg.norm(b-a)
                if length<4 or length>150:continue
                direction=(b-a)/length;alignment=np.dot(direction,target['normal'])
                if alignment<.05:continue
                options.append((length+12*(1-alignment),a,j))
        options.sort(key=lambda x:x[0]);found=False
        def variants():
            nonlocal free
            for _,a,j in options[:300]:
                b=landings[j]['point'];yield a,j,np.array([a,b]),'straight'
            from route_revo23_smooth_space import FreeRoutes
            if free is None:free=FreeRoutes(spaces[key],spaces[other] if paired else None)
            yield from free.paths(common,landings,radius)
            for _,a,j in options[300:]:
                b=landings[j]['point'];yield a,j,np.array([a,b]),'straight'
            # A single smooth turn can bypass a sensor carrier without
            # carving its shape into the side of a rod.
            used=set()
            for _,a,j in options:
                sig=(j,tuple(np.round(a/5)))
                if sig in used:continue
                used.add(sig);b=landings[j]['point'];normal=landings[j]['normal']
                directions=np.r_[np.eye(3),-np.eye(3)]
                for length in (12.,22.,34.):
                    for direction in directions:
                        # The initial straight exit stays aligned with a native
                        # mounting ear before the smooth turn starts.
                        start=a+direction*min(10.,length*.5)
                        controls=np.array([start,start+direction*length*.5,b-normal*min(9,np.linalg.norm(b-start)*.3),b])
                        t=np.linspace(0,1,25)[:,None]
                        points=(1-t)**3*controls[0]+3*(1-t)**2*t*controls[1]+3*(1-t)*t*t*controls[2]+t**3*controls[3]
                        points=np.vstack([a,(a+start)*.5,points])
                        u=np.diff(points,axis=0);du=np.linalg.norm(u,axis=1)
                        turns=np.arccos(np.clip(np.sum(u[:-1]*u[1:],axis=1)/du[:-1]/du[1:],-1,1))
                        curvature=(du[:-1]+du[1:])*.5/np.maximum(turns,1e-8)
                        if min(curvature)<radius*2:continue
                        yield a,j,points,'smooth bend'
                if len(used)>=100:break
        for attempt,(a,j,points,form) in enumerate(variants()):
            target=landings[j];b=target['point'];direction=(b-a)/np.linalg.norm(b-a)
            body=cyl(a,b,radius) if form=='straight' else positive_round_sweep(points,radius)
            pad=target['pad'];end_direction=points[-1]-points[-2];end_direction/=np.linalg.norm(end_direction)
            probe=cyl(b-end_direction*.8,b,radius)
            buried=(probe^target.get('foot_body',pad)).volume()/probe.volume()
            if buried<(.4 if skinless else .98):fails['foot_burial']=fails.get('foot_burial',0)+1;continue
            if skinless and (body^target['foot_body']).volume()<np.pi*radius**2*1.8:continue
            bond=(body^land).volume()
            initial=points[1]-points[0];initial/=np.linalg.norm(initial)
            startprobe=cyl(points[0],points[0]+initial*.6,radius)
            start_fraction=(startprobe^land).volume()/startprobe.volume()
            if bond<np.pi*radius**2*(2 if seated_start else 1) or seated_start and start_fraction<.85:
                fails['source_bond']=fails.get('source_bond',0)+1;continue
            if paired and (move(body,reflection)^landsets[other][matching[li]]).volume()<np.pi*radius**2:
                fails['mirror_source_bond']=fails.get('mirror_source_bond',0)+1;continue
            if paired and seated_start and (move(startprobe,reflection)^landsets[other][matching[li]]).volume()/startprobe.volume()<.85:continue
            candidate=body+pad
            if append_mount is not None and (candidate^own_wire[key]).volume()>.01:continue
            if append_mount is not None and paired and (move(candidate,reflection)^own_wire[other]).volume()>.01:continue
            ok,reason=spaces[key].clear(candidate)
            if ok and paired:ok,reason=spaces[other].clear(move(candidate,reflection))
            if not ok:
                name=reason['part'];fails[name]=fails.get(name,0)+1
                continue
            if append_mount is not None and minimum_cut:
                from audit_revo23_load_paths import screen
                extra=candidate+(move(candidate,reflection) if other==key else md.Manifold())
                result=move(union(material[key])+extra,np.linalg.inv(local[key]))
                audit=screen(key,result,move(keeps[key],np.linalg.inv(local[key])),skin_of(key),1.)
                score=min(r['conservative_cut_area_mm2'] for r in audit['rows'])
                if score<minimum_cut:continue
                if paired and other!=key:
                    result=move(union(material[other])+move(candidate,reflection),np.linalg.inv(local[other]))
                    audit=screen(other,result,move(keeps[other],np.linalg.inv(local[other])),skin_of(other),1.)
                    if min(r['conservative_cut_area_mm2'] for r in audit['rows'])<minimum_cut:continue
            material[key].append(candidate)
            record=dict(mount=li,rod_count=1,radius_mm=radius,centerline_world_mm=points,
                        positive_cells=True,foot_depth_mm=7. if parts[key]['body'].startswith(('forearm_','elbow_','ball_')) else 13.,
                        foot_tip_mm=1.3 if parts[key]['body'].startswith('ball_') else 1.8,
                        foot_fully_embedded_fraction=buried,wall_bond_disk_fraction=target['bond_fraction'],
                        land_overlap_mm3=bond,wall_landing_world_mm=target['outer_point'],
                        source_cap_embedded_fraction=start_fraction,
                        method='Unclipped circular-section '+form+' with a smooth tapered internal backing pad.')
            records[key].append(record)
            if skinless:record['target_mount']=0
            if paired:
                material[other].append(move(candidate,reflection));r=dict(record,mount=matching[li],mirrored_from=key)
                r['centerline_world_mm']=np.array(record['centerline_world_mm'])*[1,-1,1]
                r['wall_landing_world_mm']=np.array(record['wall_landing_world_mm'])*[1,-1,1]
                r['land_overlap_mm3']=(move(body,reflection)^landsets[other][matching[li]]).volume()
                records[other].append(r)
            found=True;print('SMOOTH STRUT',key,li,'tries',attempt+1,'length',np.linalg.norm(b-a),'bond',bond,flush=True);break
        if not found:
            put(GROOT/(key.replace('/','__')+'_search.json'),dict(land=li,sources=len(sources),landings=len(landings),options=len(options),failures=fails))
            raise RuntimeError(('No complete cylindrical route',key,li,len(options),fails))
    for k in keys:
        result=union(material[k]);cc=[c for c in result.decompose() if c.volume()>.05]
        assert len(cc)==1,(k,'disconnected',[(c.volume(),c.bounding_box()) for c in cc])
        path=GROOT/(k.replace('/','__')+'.npz');s=save_s(path,move(result,np.linalg.inv(local[k])))
        put(path.with_suffix('.json'),dict(key=k,revision=GREV,source_geometry_sha256=FHASH,
            rods=records[k],candidate_sha256=sha(path),volume_mm3=s.volume(),
            mirrored_connections=bool(other),components=1,unclipped_round_struts=True,
            inherited_functional_interfaces=True,wire_fixtures_pending=True))
        print('SAVED',k,s.volume(),'rods',len(records[k]),flush=True)

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('key');ap.add_argument('--mirror');ap.add_argument('--radius',type=float,default=4.)
    ap.add_argument('--seated-start',action='store_true');ap.add_argument('--actual-neighbours',action='store_true')
    ap.add_argument('--append-mount',type=int);ap.add_argument('--minimum-cut',type=float,default=0.)
    a=ap.parse_args();build_pair(a.key,a.mirror,a.radius,a.seated_start,a.actual_neighbours,a.append_mount,a.minimum_cut)
