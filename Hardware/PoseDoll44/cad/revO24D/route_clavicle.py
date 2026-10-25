"""Search a continuous D8 load path against the finite full-body pose envelope."""
from validate import *
from rom_cases import examination_cases
import heapq,itertools

def main():
    parts,z,ss=read_assembly();fr='l_clavicle_protract';origin=P['clavicle_l']
    cases=[{}]+[v['angles'] for v in examination_cases().values()]
    lo=np.array([-80.,-40.,-90.]);hi=np.array([55.,45.,-4.]);obs={}
    for q in cases:
        F=frames(q);back=T(-origin)@F0[fr]@np.linalg.inv(F[fr])
        for j,p in enumerate(parts):
            if family(p['frame'])==fr:continue
            W=back@F[p['frame']];key=(j,np.round(W,6).tobytes())
            if key in obs:continue
            t=moved(ss[j],W);b=np.array(t.bounding_box()).reshape(2,3)
            if np.all(b[1]>lo-5) and np.all(b[0]<hi+5):obs[key]=(t,b,p['name'])
    obstacles=list(obs.values());mins=np.array([b[0] for s,b,n in obstacles]);maxs=np.array([b[1] for s,b,n in obstacles]);print('SWEPT OBSTACLES',len(obstacles),flush=True)
    socket=next((p,s) for p,s in zip(parts,ss) if p['name']=='l_clavicle_z_output_socket');s=moved(socket[1],T(-origin)@F0[socket[0]['frame']]);start=np.array(s.bounding_box()).reshape(2,3).mean(0)+[-10,0,0];goal=np.array([20.,0,-7.])
    coords=[sorted(set(np.arange(lo[k],hi[k]+.1,5).tolist()+[float(start[k]),float(goal[k])])) for k in range(3)]
    si=tuple(coords[k].index(start[k]) for k in range(3));gi=tuple(coords[k].index(goal[k]) for k in range(3));point=lambda key:np.array([coords[k][key[k]] for k in range(3)])
    good={};edges={};tests=0
    def check(shape):
        nonlocal tests
        b=np.array(shape.bounding_box()).reshape(2,3);ids=np.where(np.all(maxs>b[0],1)&np.all(mins<b[1],1))[0]
        for i in ids:
            tests+=1
            if (shape^obstacles[i][0]).volume()>.002:return False
        return True
    anchor_center=start+[10,0,-2];candidates=[]
    for deg in range(0,360,15):
        pt=anchor_center+np.array([10.5*math.cos(math.radians(deg)),10.5*math.sin(math.radians(deg)),0])
        if check(md.Manifold.sphere(4.25,16).translate(pt)):candidates.append(pt)
    print('FREE ANCHORS',[p.tolist() for p in candidates],flush=True)
    if candidates:
        start=min(candidates,key=lambda p:np.linalg.norm(p-goal))
        coords=[sorted(set(np.arange(lo[k],hi[k]+.1,5).tolist()+[float(start[k]),float(goal[k])])) for k in range(3)]
        si=tuple(coords[k].index(start[k]) for k in range(3));gi=tuple(coords[k].index(goal[k]) for k in range(3))
    else:
        shape=md.Manifold.sphere(4.25,16).translate(start);b=np.array(shape.bounding_box()).reshape(2,3)
        ids=np.where(np.all(maxs>b[0],1)&np.all(mins<b[1],1))[0]
        print('ANCHOR BLOCKERS',sorted(set(obstacles[i][2] for i in ids if (shape^obstacles[i][0]).volume()>.002)),flush=True)
    def node_ok(key):
        if key not in good:good[key]=check(md.Manifold.sphere(4.25,16).translate(point(key)))
        return good[key]
    def edge_ok(a0,b0):
        key=tuple(sorted([a0,b0]))
        if key not in edges:edges[key]=check(beam(point(a0),point(b0),4.25))
        return edges[key]
    print('ANCHORS',start.tolist(),goal.tolist(),node_ok(si),node_ok(gi),flush=True)
    queue=[(float(np.linalg.norm(start-goal)),0.,si)];dist={si:0.};previous={};count=0
    while queue:
        _,d,u=heapq.heappop(queue)
        if d!=dist[u]:continue
        if u==gi:break
        count+=1
        if count%200==0:print('ROUTE',count,len(queue),'CSG',tests,flush=True)
        for k,delta in itertools.product(range(3),[-1,1]):
            v=list(u);v[k]+=delta;v=tuple(v)
            if not 0<=v[k]<len(coords[k]) or not node_ok(v) or not edge_ok(u,v):continue
            step=float(np.linalg.norm(point(v)-point(u)));nd=d+step
            if nd<dist.get(v,float('inf')):
                dist[v]=nd;previous[v]=u;heapq.heappush(queue,(nd+float(np.linalg.norm(point(v)-goal)),nd,v))
    if gi not in previous:raise RuntimeError('No D8 route found')
    path=[gi]
    while path[-1]!=si:path.append(previous[path[-1]])
    path=list(reversed(path));compact=[path[0]];i=0
    while i<len(path)-1:
        j=len(path)-1
        while j>i+1 and not edge_ok(path[i],path[j]):j-=1
        compact.append(path[j]);i=j
    result=dict(geometry_sha256=sha(OUT/'assembly_meshes.npz'),frame=fr,relative_to='clavicle_l',radius_mm=4,search_radius_mm=4.25,poses=len(cases),points=[point(p) for p in compact],length_mm=sum(np.linalg.norm(point(b)-point(a)) for a,b in zip(compact[:-1],compact[1:])),expanded=count,boolean_tests=tests)
    put(OUT/'verification/clavicle_route_proposal.json',result);print(result,flush=True)

if __name__=='__main__':main()
