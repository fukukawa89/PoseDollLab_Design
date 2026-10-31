"""Find a fixed solid support outside the sampled moving-neck/clavicle envelope."""
from connections import *
import heapq,itertools

def main():
    parts,z,solids=read_assembly();pitch=1.;lo=np.array([-55.,-40,420]);hi=np.array([40.,45,495]);shape=((hi-lo)/pitch).astype(int)+1
    occ=np.zeros(shape,bool);obstacles=[];seen=set();cases=[p['angles'] for p in poses().values()]
    for ax,vals in [('neck_side',range(-20,21,5)),('neck_flex',range(-30,41,5))]:cases.extend({ax:v} for v in vals)
    for q in cases:
        F=frames(q);back=F0['thorax_flex']@np.linalg.inv(F['thorax_flex'])
        for i,(p,s) in enumerate(zip(parts,solids)):
            if p['name'].startswith('left_clavicle_seat'):continue
            if family(p['frame'])=='thorax_flex' and p['role'] in ['structure','shell']:continue
            W=back@F[p['frame']];key=(i,np.round(W,6).tobytes())
            if key in seen:continue
            seen.add(key);w=moved(s,W);bb=np.array(w.bounding_box()).reshape(2,3)
            if not (np.all(bb[1]>=lo) and np.all(bb[0]<=hi)):continue
            obstacles.append((p['name'],w,bb))
    print('SUPPORT obstacles',len(obstacles),flush=True)
    for oi,(name,s,bb) in enumerate(obstacles):
        start=np.maximum(0,np.floor((bb[0]-lo)/pitch).astype(int));end=np.minimum(shape-1,np.ceil((bb[1]-lo)/pitch).astype(int))
        ix=np.arange(start[0],end[0]+1);iy=np.arange(start[1],end[1]+1);xx,yy=np.meshgrid(lo[0]+ix*pitch,lo[1]+iy*pitch,indexing='ij');grid=np.c_[xx.ravel(),yy.ravel()]
        for iz in range(start[2],end[2]+1):
            inside=np.zeros(len(grid),bool)
            for poly in s.slice(float(lo[2]+iz*pitch)).to_polygons():inside^=PolygonPath(poly).contains_points(grid)
            occ[start[0]:end[0]+1,start[1]:end[1]+1,iz]|=inside.reshape(len(ix),len(iy))
        if oi%100==0:print('VOX',oi,flush=True)
    distance=ndimage.distance_transform_edt(~occ,sampling=pitch);free=distance>=4.2
    index=lambda p:tuple(np.rint((np.array(p)-lo)/pitch).astype(int))
    point=lambda i:lo+np.array(i)*pitch
    targets=[[-40,22,z] for z in [438,445,455,465]]+[[-40,-22,z] for z in [438,445,455,465]]+[[P['neck_01'][0]+30,17,z] for z in [435,440,450,460,465]]
    goals={index(p) for p in targets if free[index(p)]};starts=[];housing=next(moved(s,F0[p['frame']]) for p,s in zip(parts,solids) if p['name']=='l_clavicle_z_housing')
    for h in np.arange(10,19,1):
        for ang in np.linspace(0,2*math.pi,72,endpoint=False):
            p=P['clavicle_l']+[8.6*math.cos(ang),8.6*math.sin(ang),h];idx=index(p)
            if free[idx] and (housing^a.sphere(point(idx),3.2)).volume()>4:starts.append(idx)
    starts=list(set(starts));print('STARTS',len(starts),'GOALS',len(goals),flush=True)
    if not starts or not goals:raise RuntimeError('No load-bearing support anchor with the specified swept clearance')
    gg=np.array(list(goals));heur=lambda n:float(np.min(np.linalg.norm(gg-n,axis=1)));heap=[];dist={};parent={};closed=set()
    for n in starts:dist[n]=0;parent[n]=None;heapq.heappush(heap,(heur(n),n))
    directions=[(np.array(d),float(np.linalg.norm(d))) for d in itertools.product([-1,0,1],repeat=3) if any(d)]
    target=None
    while heap:
        _,n=heapq.heappop(heap)
        if n in closed:continue
        closed.add(n)
        if n in goals:target=n;break
        for d,cost in directions:
            ni=np.array(n)+d
            if np.any(ni<0) or np.any(ni>=shape):continue
            nt=tuple(ni)
            if not free[nt]:continue
            nd=dist[n]+cost*(1+.3/max(distance[nt]-3.2,.1))
            if nd<dist.get(nt,1e99):dist[nt]=nd;parent[nt]=n;heapq.heappush(heap,(nd+heur(ni),nt))
    if target is None:raise RuntimeError('No route through sampled free space')
    route=[]
    while target is not None:route.append(point(target));target=parent[target]
    route.reverse()
    def clear(a0,b0):
        s=beam(a0,b0,3.2);bb=np.array(s.bounding_box()).reshape(2,3)
        for n,t,b in obstacles:
            if np.all(bb[1]>b[0]) and np.all(b[1]>bb[0]) and (s^t).volume()>.002:return False
        return True
    simplified=[route[0]];i=0
    while i<len(route)-1:
        for j in range(len(route)-1,i,-1):
            if clear(route[i],route[j]):simplified.append(route[j]);i=j;break
        else:raise RuntimeError('Voxel route cannot satisfy exact solid clearance')
    result=dict(radius_mm=3.2,points_mm=simplified,source_geometry_sha256=sha(OUT/'assembly_meshes.npz'),sampled_obstacle_instances=len(obstacles),grid_pitch_mm=1,grid_center_clearance_mm=4.2,exact_segment_overlap_threshold_mm3=.002,method='A* over sampled swept envelopes, then exact solid checks for each capsule segment; starts intersect the actual fixed bearing housing, ends join fixed backbone',states_expanded=len(closed))
    put(HERE/'seat_route.json',result);put(OUT/'verification/seat_route_search.json',result);print('ROUTE',[p.tolist() for p in simplified],flush=True)
if __name__=='__main__':main()
