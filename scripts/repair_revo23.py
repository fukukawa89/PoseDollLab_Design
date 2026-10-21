"""Join substantial wall regions around sampled obstacles; discard cut debris.

This constructs real solid ribs and records any remaining disconnected body.
It does not certify the strength or continuous motion clearance of a rib.
"""
from refine_revo23 import *

def components(s):return sorted([x for x in s.decompose() if x.volume()>1e-4],key=lambda x:-x.volume())

def all_obstacles(parts,key,p):
    """Actual nearby objects at all five checked poses, for new ribs only."""
    bounds=np.asarray(parts[key]['s'].bounding_box());lo=bounds[:3]-16;hi=bounds[3:]+16
    crop=box(lo,hi);seen=set();obstacles=[]
    for raw in cases(p,'quick').values():
        F=frames(p,raw);I=np.linalg.inv(F[parts[key]['token']])
        for other,part in parts.items():
            if other==key:continue
            M=I@F[part['token']];code=(other,tuple(np.round(M,7).ravel()))
            if code in seen:continue
            seen.add(code);bb=part['s'].bounding_box()
            corners=np.array(list(itertools.product(*zip(bb[:3],bb[3:]))))
            corners=corners@M[:3,:3].T+M[:3,3]
            if np.any(np.minimum(hi,corners.max(0))-np.maximum(lo,corners.min(0))<=0):continue
            obstacle=move(part['s'],M)^crop
            if not obstacle.is_empty():obstacles.append(obstacle)
    return solid(*vf(union(obstacles)))

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--only');ap.add_argument('--keys',nargs='*');ap.add_argument('--trim-only',action='store_true');args=ap.parse_args()
    parts=load_current();zc=np.load(B/'clearance_cutters.npz');zk=np.load(B/'retained_interfaces.npz')
    records=[];before_hash=sha(B/'assembly.npz');p=read(B/'profiles/device_profile.json')
    for key,part in parts.items():
        if part['role']!='structure' or (args.only and args.only not in key) or (args.keys and key not in args.keys):continue
        keep=solid(zk[key+'|v'],zk[key+'|f']);cut=solid(zc[key+'|v'],zc[key+'|f'])
        old=part['s'];comps=components(old);discard=[];retained=[]
        for comp in comps:
            if comp.volume()<25 and (comp^keep).volume()<.02:discard.append(comp.volume())
            else:retained.append(comp)
        current=union(retained);initial=len(retained);ribs=[];failed=[]
        if initial>1 and not args.trim_only:
            # A bridge must avoid all nearby objects, not merely the obstacles
            # which happened to touch the disconnected wall before repair.
            cut=solid(*vf(cut+all_obstacles(parts,key,p)))
        for attempt in range(0 if args.trim_only else 12):
            comps=components(current)
            if len(comps)<2:break
            primary=comps[0];pv,_=vf(primary);tree=cKDTree(pv);best=[]
            for n,c in enumerate(comps[1:]):
                cv,_=vf(c);ds,ix=tree.query(cv);best.append((float(ds.min()),n+1,cv,ds,ix))
            succeeded=False
            for distance,index,cv,ds,ix in sorted(best,key=lambda x:x[0]):
                target=comps[index];chosen=[];pairs=[]
                for n in np.argsort(ds):
                    a=cv[n];b=pv[ix[n]]
                    if any(np.linalg.norm(a-x)<3 for x in chosen):continue
                    chosen.append(a);pairs.append((a,b))
                    if len(pairs)>=8:break
                for a,b in pairs:
                    d=b-a;length=np.linalg.norm(d)
                    if length>55:continue
                    axis=d/max(length,1e-9);u=np.cross(np.eye(3)[np.argmin(abs(axis))],axis);u/=max(np.linalg.norm(u),1e-9);v=np.cross(axis,u)
                    offsets=[np.zeros(3)]+[r*t for r in (4,8,12) for t in (u,-u,v,-v,(u+v)/1.414,(u-v)/1.414,(-u+v)/1.414,(-u-v)/1.414)]
                    for delta in offsets:
                        mid=(a+b)/2+delta
                        bridge=union([capsule(a,mid,2.5),capsule(mid,b,2.5)])-cut
                        connected=[]
                        for piece in components(bridge):
                            if (piece^primary).volume()>.05 and (piece^target).volume()>.05:connected.append(piece)
                        if not connected:continue
                        addition=union(connected);new=current+addition
                        if len(components(new))>=len(comps):continue
                        current=new;ribs.append(dict(length_mm=float(length),detour_mm=float(np.linalg.norm(delta)),volume_mm3=addition.volume()))
                        succeeded=True;break
                    if succeeded:break
                if succeeded:break
            if not succeeded:
                failed=[round(c.volume(),3) for c in comps[1:]];break
        # Any disconnected skin island with no retained interface is removed.
        # Never hide an unattached functional land by deleting it.
        final=components(current);isolated=[];selected=final[:1]
        for comp in final[1:]:
            if (comp^keep).volume()<.02:isolated.append(comp.volume())
            else:selected.append(comp)
        current=union(selected);part['s']=current
        rec=dict(key=key,initial_components=len(components(old)),discarded_debris_mm3=discard,
                 initial_substantial_components=initial,final_components=len(components(current)),ribs=ribs,
                 discarded_isolated_skin_mm3=isolated,disconnected_volumes_mm3=[c.volume()for c in components(current)[1:]],interface_loss_mm3=max(0.,(keep-current).volume()))
        records.append(rec);print('CONNECT',key,rec['initial_components'],'->',rec['final_components'],'ribs',len(ribs),'debris',len(discard),flush=True)
    save_parts(parts)
    put(B/'verification/connections.json',dict(input_sha256=before_hash,output_sha256=sha(B/'assembly.npz'),rows=records,
        structural_strength_validated=False,sampled_obstacles_only=True))

if __name__=='__main__':main()
