"""Move an internal wall landing to permit a properly seated direct connection."""
from repair_revo23_endfaces import *

def main(key,index,other=None):
    parts,p,cfg=load_h();N=frames(p,p['neutral_raw_deg']);M=N[parts[key]['token']];R=np.diag([1.,-1.,1.,1.])
    report=copy.deepcopy(connection_records(key));old=report['rods'][index];radius=old['radius_mm'];assert 'target_mount' not in old
    hosts=native_hosts(key,parts,p,N);source=hosts[old['mount']];common=source
    space=Space(key,parts,p,N,False);wires=move(wire_spaces(key),M);ospace=None;owires=None
    if other:
        OM=N[parts[other]['token']];oh=native_hosts(other,parts,p,N);ospace=space if other==key else Space(other,parts,p,N,False);owires=move(wire_spaces(other),OM)
        costs=np.array([[np.linalg.norm(np.mean(np.array(a.bounding_box()).reshape(2,3),0)-np.mean(np.array(move(b,R).bounding_box()).reshape(2,3),0))for b in oh]for a in hosts])
        ii,jj=linear_sum_assignment(costs);matching=dict(zip(map(int,ii),map(int,jj)));common=source^move(oh[matching[old['mount']]],R)
        oreport=report if other==key else copy.deepcopy(connection_records(other))
    targets=[];fail={};tries=0
    for t in skin_landings(key,parts,p,cfg,N,clean_skin(key),radius):
        if (t['pad']^wires).volume()>.01:continue
        ok,why=space.clear(t['pad'])
        if ok and other:ok,why=ospace.clear(move(t['pad'],R))
        if ok and other and (move(t['pad'],R)^owires).volume()>.01:continue
        if ok:targets.append(t)
    print('CLEAR WALL LANDINGS',key,len(targets),flush=True)
    def accept(a,t,socket=None):
        nonlocal tries
        tries+=1
        if tries%3000==0:print('REANCHOR SEARCH',key,index,tries,fail,flush=True)
        b=t['point'];d=b-a;d/=np.linalg.norm(d)
        host=common if socket is None else socket_solid(socket)
        if not quick_face(host,a,d,radius):return None
        if not quick_face(t['pad'],b,-d,radius):return None
        if socket is not None:
            if not socket_base_witness(common,socket)['passed']:return None
            if (host^wires).volume()>.01:return None
            ok,why=space.clear(host)
            if ok and other:ok,why=ospace.clear(move(host,R))
            if not ok:fail['socket '+why['part']]=fail.get('socket '+why['part'],0)+1;return None
        body=cyl(a,b,radius);s=body+t['pad']+(host if socket is not None else md.Manifold())
        if (s^wires).volume()>.01:fail['wire']=fail.get('wire',0)+1;return None
        ok,why=space.clear(s)
        if ok and other:ok,why=ospace.clear(move(s,R))
        if ok and other and (move(s,R)^owires).volume()>.01:ok=False;why={'part':'mirror wire'}
        if not ok:fail[why['part']]=fail.get(why['part'],0)+1;return None
        r=copy.deepcopy(old)
        for k in ('source_socket','source_feet','mirrored_from','foot_only'):r.pop(k,None)
        r.update(centerline_world_mm=np.array([a,b]),positive_cells=True,
            wall_landing_world_mm=t['outer_point'],wall_foot_reference_endpoint_world_mm=b,
            foot_depth_mm=7. if parts[key]['body'].startswith(('forearm_','elbow_','ball_')) else 13.,foot_tip_mm=1.3 if parts[key]['body'].startswith('ball_') else 1.8,
            source_end_face=face_witness(host,a,d,radius),target_end_face=face_witness(t['pad'],b,-d,radius),
            wall_bond_disk_fraction=t['bond_fraction'],land_overlap_mm3=(s^source).volume(),
            method='Fully seated direct circular stem; internal wall landing relocated without changing the anatomical skin.')
        r['source_cap_embedded_fraction']=r['source_end_face']['first_stem_coverage'];r['source_cap_host']='native_land' if socket is None else 'source_socket'
        if socket is not None:r['source_socket']=socket
        return r
    points=source_points(common,pitch=.75,limit=600);oldstart=np.array(old['centerline_world_mm'])[0]
    options=sorted([(np.linalg.norm(t['point']-a)+.2*np.linalg.norm(a-oldstart),a,t) for a in points for t in targets],key=lambda x:x[0])
    result=None
    for _,a,t in options:
        result=accept(a,t)
        if result:break
    if not result:
        bases=rectangular_bases(common,radius,oldstart)
        # Prefer bases that point toward a reachable shell, with generous end purchase.
        options=[]
        for f in bases:
            base=np.array(f['base_world_mm']);normal=np.array(f['normal_world'])
            for t in targets:
                delta=t['point']-base;length=np.linalg.norm(delta)
                if length<8 or np.dot(delta/length,normal)<.15:continue
                options.append((length+5*(1-np.dot(delta/length,normal)),f,t))
        options.sort(key=lambda x:x[0]);print('FOOT LANDING OPTIONS',key,len(options),flush=True)
        for _,f0,t in options:
            base=np.array(f0['base_world_mm']);normal=np.array(f0['normal_world'])
            for neck,depth in ((0.,6.),(0.,9.),(4.,10.),(8.,14.)):
                top=base+normal*depth;e=t['point']-top;length=np.linalg.norm(e)
                if length<2:continue
                e/=length;u=np.array(f0['u_world']);v=np.cross(normal,u)
                corners=np.array([base+x*u+y*v for x,y in itertools.product((-f0['width_mm']/2,f0['width_mm']/2),(-f0['height_mm']/2,f0['height_mm']/2))])
                if depth-3*(normal@e)-(radius+1.4)*np.sqrt(max(0.,1-(normal@e)**2))<.1:continue
                f=dict(f0,neck_mm=neck,depth_mm=depth,top_radius_mm=radius+1.4,top_normal_world=e,socket_length_mm=3.5)
                result=accept(top-e*1.5,t,f)
                if result:break
            if result:break
    if not result:
        print('NO NEW WALL LANDING',key,index,tries,fail,flush=True);put(HROOT/(key.replace('/','__')+f'_reanchor_{index}.json'),dict(passed=False,failures=fail));return
    report['rods'][index]=result
    if other:
        j=min(range(len(oreport['rods'])),key=lambda j:np.linalg.norm(np.array(oreport['rods'][j]['centerline_world_mm'])[0]-oldstart*[1,-1,1]))
        q=copy.deepcopy(result);q.update(mount=matching[old['mount']],mirrored_from=key)
        for name in ('centerline_world_mm','wall_landing_world_mm','wall_foot_reference_endpoint_world_mm'):q[name]=np.array(q[name])*[1,-1,1]
        if 'source_socket' in q:
            f=q['source_socket']
            for name in ('base_world_mm','normal_world','u_world','top_normal_world','top_offset_world_mm'):
                if name in f:f[name]=np.array(f[name])*[1,-1,1]
        oreport['rods'][j]=q
    for k,rr in [(key,report)]+([(other,oreport)] if other and other!=key else []):
        s=move(preserved_material(k,parts,p,N)+structural_connectors(rr['rods']),np.linalg.inv(N[parts[k]['token']]))
        cc=[c for c in s.decompose() if c.volume()>.001];assert len(cc)==1,(key,'disconnected material')
        path=HROOT/(k.replace('/','__')+'.npz');save_s(path,cc[0]);rr.update(revision=HREV,candidate_sha256=sha(path),source_geometry_sha256=GHASH,components=1);put(path.with_suffix('.json'),rr)
    print('REANCHORED',key,index,'start',result['centerline_world_mm'][0],'end',result['centerline_world_mm'][-1],flush=True)

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('key');ap.add_argument('index',type=int);ap.add_argument('--mirror');a=ap.parse_args();main(a.key,a.index,a.mirror)
