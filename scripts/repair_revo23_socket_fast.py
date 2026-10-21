"""Compact seated adapters: reject obstructed feet before routing round stems."""
import repair_revo23_endfaces as base
from repair_revo23_endfaces import *

def fast_search(r,source,target,space,wires,other=None,ospace=None,owires=None,source_common=None):
    common=source if source_common is None else source_common
    radius=r['radius_mm'];old=np.array(r['centerline_world_mm']);R=np.diag([1.,-1.,1.,1.]);goals=[]
    for b in endpoints(r,target):
        e=(np.array(r['wall_landing_world_mm'])-b) if 'target_mount' not in r else old[-1]-old[-2]
        e/=np.linalg.norm(e)
        if quick_face(target,b,-e,radius):goals.append((b,e,None))
    if not r.get('internal_waypoint') and len(old)>8:
        distance=np.r_[0,np.cumsum(np.linalg.norm(np.diff(old,axis=0),axis=1))]
        tail=old
        for cut in (0,1,2,3):
            tt=old if cut==0 else old[:-cut]
            e=tt[-2]-tt[-1];e/=np.linalg.norm(e)
            if quick_face(target,tt[-1],e,radius):tail=tt;break
        for length in (10.,22.,36.):
            j=int(np.argmin(abs(distance-length)))
            if j<3 or j>=len(tail)-4:continue
            e=tail[j+1]-tail[j];e/=np.linalg.norm(e)
            goals.append((tail[j],e,tail[j:]))
    assert goals,(space.key,'no complete target end face')
    feet=rectangular_bases(common,radius,old[0]);fail={};trials=0;tested=0
    print('COMPACT FOOT SEARCH',space.key,'bases',len(feet),'goals',len(goals),flush=True)
    # Prefer small offsets and compact transitions. Full base area is unchanged.
    for shift in (0.,4.,-4.,8.,-8.):
      for depth in (4.,7.,10.,14.):
       for f0 in feet:
        b=np.array(f0['base_world_mm']);n=np.array(f0['normal_world']);u=np.array(f0['u_world']);v=np.cross(n,u)
        for offset in ([v*shift] if shift==0 else [v*shift,u*shift]):
         top=b+n*depth+offset
         for goal,e,tail in goals:
          d=goal-top;distance=np.linalg.norm(d)
          if distance<5:continue
          d/=distance
          if depth-(radius+.6)*np.sqrt(max(0.,1-(n@d)**2))<.1:continue
          f=dict(f0,depth_mm=depth,top_radius_mm=radius+.6,top_normal_world=d,top_offset_world_mm=offset,socket_length_mm=3.)
          a=top-d*1.4;pad=socket_solid(f)
          trials+=1
          if trials%1000==0:print('COMPACT FEET',space.key,trials,'routes',tested,fail,flush=True)
          if (pad^wires).volume()>.01:fail['aperture']=fail.get('aperture',0)+1;continue
          ok,why=space.clear(pad)
          if ok and ospace:ok,why=ospace.clear(move(pad,R))
          if ok and owires is not None and (move(pad,R)^owires).volume()>.01:ok=False;why={'part':'mirror aperture'}
          if not ok:fail[why['part']]=fail.get(why['part'],0)+1;continue
          if not quick_face(pad,a,d,radius) or not socket_base_witness(common,f)['passed']:continue
          routes=[]
          if tail is None:routes.append(np.array([a,goal]))
          for sc in (4.,8.,14.,22.):
              pts=curve(a,d,goal,e,sc)
              if tail is not None:pts=np.vstack([pts,tail[1:]])
              routes.append(pts)
          for pts in routes:
            tested+=1
            if not sensible(pts,radius):continue
            sd=pts[1]-pts[0];ed=pts[-2]-pts[-1]
            if not quick_face(pad,pts[0],sd/np.linalg.norm(sd),radius) or not quick_face(target,pts[-1],ed/np.linalg.norm(ed),radius):continue
            body=cyl(*pts,radius) if len(pts)==2 else positive_round_sweep(pts,radius)
            if len(body.decompose())!=1 or body.genus()!=0:continue
            candidate=body+pad
            if (candidate^wires).volume()>.01:continue
            ok,why=space.clear(candidate)
            if ok and ospace:ok,why=ospace.clear(move(candidate,R))
            if ok and owires is not None and (move(candidate,R)^owires).volume()>.01:ok=False
            if not ok:continue
            rr=copy.deepcopy(r)
            for k in ('source_socket','source_feet','foot_only','mirrored_from'):rr.pop(k,None)
            rr.update(centerline_world_mm=pts,source_socket=f,positive_cells=True,
                source_end_face=face_witness(pad,pts[0],sd,radius),target_end_face=face_witness(target,pts[-1],ed,radius),
                land_overlap_mm3=(candidate^source).volume(),source_cap_host='source_socket',source_cap_embedded_fraction=1.,
                method='Compact complete circular socket on a fully seated flat mounting base; entire round stem preserved.')
            if 'target_mount' not in rr:rr['wall_foot_reference_endpoint_world_mm']=r.get('wall_foot_reference_endpoint_world_mm',old[-1])
            print('COMPACT FOUND',space.key,trials,'routes',tested,flush=True)
            return rr,fail
    return None,dict(fail,foot_candidates=trials,routes=tested)

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('key');ap.add_argument('--mirror');ap.add_argument('--indices',type=int,nargs='*');ap.add_argument('--native-other');a=ap.parse_args()
    if a.native_other:
        import repair_revo23_native_links as native
        native.search=fast_search;native.main(a.key,a.native_other,False)
    else:
        base.search=fast_search;base.main(a.key,a.mirror,a.indices)
