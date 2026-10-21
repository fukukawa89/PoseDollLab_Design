"""Repair each end of a native-to-native link, retaining a tangent-continuous middle.

An internal waypoint's analytic continuation is a routing condition, not an
attachment or an acceptance host. The finished native ends are checked again.
"""
from repair_revo23_endfaces import *

def main(key,other,paired=True):
    parts,p,cfg=load_h();N=frames(p,p['neutral_raw_deg']);R=np.diag([1.,-1.,1.,1.]);M=N[parts[key]['token']];OM=N[parts[other]['token']]
    record=copy.deepcopy(connection_records(key));orecord=copy.deepcopy(connection_records(other));r=record['rods'][0]
    hosts=native_hosts(key,parts,p,N);ohosts=native_hosts(other,parts,p,N)
    cost=np.array([[np.linalg.norm(np.mean(np.array(a.bounding_box()).reshape(2,3),0)-np.mean(np.array(move(b,R).bounding_box()).reshape(2,3),0))for b in ohosts]for a in hosts])
    ii,jj=linear_sum_assignment(cost);matching=dict(zip(map(int,ii),map(int,jj)))
    spaces=Space(key,parts,p,N,False);ospace=Space(other,parts,p,N,False) if paired else None;wires=move(wire_spaces(key),M);owires=move(wire_spaces(other),OM) if paired else None
    full=np.array(r['centerline_world_mm']);sockets={};done=[]
    for end in ('source','target'):
        path=full if end=='source' else full[::-1]
        mount=r['mount'] if end=='source' else r['target_mount'];host=hosts[mount];common=host^move(ohosts[matching[mount]],R) if paired else host
        cache=HROOT/'native_link_ends'/(key.replace('/','__')+'_'+end+'.json')
        if cache.exists():
            saved=read(cache);full=np.array(saved['full_centerline_world_mm']);sockets.update(saved['sockets']);done.append(end);continue
        distance=np.r_[0,np.cumsum(np.linalg.norm(np.diff(path,axis=0),axis=1))];found=None
        for span in (52.,42.,30.):
            j=int(np.argmin(abs(distance-span)))
            if j>=len(path)-8:continue
            # Last 2 mm straight follows the untouched middle's tangent.
            b=path[j];d=path[j+1]-path[j];d/=np.linalg.norm(d)
            prefix=np.vstack([path[:j],b-d*1.6,b-d*.8,b])
            temp=dict(r,centerline_world_mm=prefix,internal_waypoint=True,target_mount=0,mount=mount)
            for k in ('source_socket','target_socket','source_feet','mirrored_from'):temp.pop(k,None)
            continuation=cyl(b-d*2.,b+d*3.,r['radius_mm']+.001)
            result,fail=search(temp,host,continuation,spaces,wires,other if paired else None,ospace,owires,common)
            if result is None:continue
            pts=np.array(result['centerline_world_mm'])
            if np.linalg.norm(pts[-1]-b)>.01:continue
            combined=np.vstack([pts,path[j+1:]])
            # Ignore only the still-unrepaired opposite end during this local step.
            # Assess the new end and its join. The untouched middle retains the
            # previously verified complete sweep; it is not redesigned here.
            if not sensible(np.vstack([pts,path[j+1:j+4]]),r['radius_mm']):
                print('JOIN NEEDS MORE ROOM',key,end,span,flush=True);continue
            full=combined if end=='source' else combined[::-1]
            if 'source_socket' in result:sockets[end+'_socket']=result['source_socket']
            put(cache,dict(full_centerline_world_mm=full,sockets=sockets,source_geometry_sha256=GHASH,span_mm=span))
            found=result;done.append(end);print('NATIVE END REPAIRED',key,end,flush=True);break
        if found is None:raise RuntimeError(('No seated native end',key,end))
    result=copy.deepcopy(r);result.update(centerline_world_mm=full,positive_cells=True,method='Both native ends seated on full flat bases; tangent-continuous circular stem.')
    result.pop('mirrored_from',None);result.update(sockets)
    total=structural_connectors([result]);ok,why=spaces.clear(total)
    assert ok,(key,why)
    if paired:
        ok,why=ospace.clear(move(total,R));assert ok,(other,why)
    assert (total^wires).volume()<.01 and (not paired or (move(total,R)^owires).volume()<.01)
    for end in ('source','target'):
        pts=full if end=='source' else full[::-1];mount=r['mount'] if end=='source' else r['target_mount'];host=hosts[mount]
        if end+'_socket' in sockets:
            assert socket_base_witness(host,sockets[end+'_socket'])['passed'];host=socket_solid(sockets[end+'_socket'])
        assert face_witness(host,pts[0],pts[1]-pts[0],r['radius_mm'])['passed']
    record['rods']=[result];mirror=copy.deepcopy(result);mirror.update(mount=matching[r['mount']],target_mount=matching[r['target_mount']],mirrored_from=key)
    for name in ('centerline_world_mm','wall_landing_world_mm'):
        if name in mirror:mirror[name]=np.array(mirror[name])*[1,-1,1]
    for socket in ('source_socket','target_socket'):
        if socket not in mirror:continue
        f=mirror[socket]
        for name in ('base_world_mm','normal_world','u_world','top_normal_world','top_offset_world_mm'):
            if name in f:f[name]=np.array(f[name])*[1,-1,1]
    orecord['rods']=[mirror]
    for k,rr in [(key,record)]+([(other,orecord)] if paired else []):
        s=move(preserved_material(k,parts,p,N)+structural_connectors(rr['rods']),np.linalg.inv(N[parts[k]['token']]))
        main=[c for c in s.decompose() if c.volume()>.001];assert len(main)==1
        path=HROOT/(k.replace('/','__')+'.npz');save_s(path,main[0]);rr.update(revision=HREV,candidate_sha256=sha(path),source_geometry_sha256=GHASH,components=1);put(path.with_suffix('.json'),rr)
    print('NATIVE LINK REPAIRED',key,other if paired else 'independent native mounting',flush=True)

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('key');ap.add_argument('other');ap.add_argument('--independent',action='store_true');a=ap.parse_args();main(a.key,a.other,not a.independent)
