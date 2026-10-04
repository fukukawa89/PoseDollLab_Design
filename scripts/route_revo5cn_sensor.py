"""O5CN bounded router derived from the project mini-head router.
Vias stay away from all SMD lands; final KiCad DRC/parity still required."""
import math,heapq,collections,os
import pcbnew as pcb
STEP=.05
XLO,XHI,YLO,YHI=1889,2111,1909,2091
def g(v):return round(pcb.ToMM(v)/STEP)
def pos(x,y):return pcb.VECTOR2I(pcb.FromMM(x*STEP),pcb.FromMM(y*STEP))
def route(b):
    occupancy=[collections.defaultdict(set),collections.defaultdict(set)]
    padgroups=collections.defaultdict(list)
    via_positions=[]
    smd_rects=[]
    def fill(layer,x0,y0,x1,y1,net):
        for x in range(math.floor(x0),math.ceil(x1)+1):
            for y in range(math.floor(y0),math.ceil(y1)+1):occupancy[layer][(x,y)].add(net)
    for f in b.GetFootprints():
        for p in f.Pads():
            pnet=p.GetNetCode();center=p.GetPosition(); x=pcb.ToMM(center.x)/STEP;y=pcb.ToMM(center.y)/STEP
            size=p.GetSize();sx=pcb.ToMM(size.x)/STEP;sy=pcb.ToMM(size.y)/STEP
            if p.GetAttribute()==pcb.PAD_ATTRIB_SMD:
                smd_rects.append((x-sx/2,y-sy/2,x+sx/2,y+sy/2))
            if p.GetAttribute()==pcb.PAD_ATTRIB_NPTH:
                for l in (0,1):fill(l,x-sx/2-4,y-sy/2-4,x+sx/2+4,y+sy/2+4,-1)
            else:
                for l,L in ((0,pcb.F_Cu),(1,pcb.B_Cu)):
                    if p.IsOnLayer(L):fill(l,x-sx/2-5,y-sy/2-5,x+sx/2+5,y+sy/2+5,pnet or -1)
                if pnet:padgroups[pnet].append(p)
    def free(state,net):
        x,y,l=state
        return XLO<=x<=XHI and YLO<=y<=YHI and abs(x-2000)+abs(y-2000)<=187 and not (occupancy[l].get((x,y),set())-{net})
    def viaok(x,y,net):
        # Via copper radius .30 mm + .20 mm separation from the SMD land.
        # This avoids assuming filled/capped via-in-pad assembly.
        for x0,y0,x1,y1 in smd_rects:
            dx=max(x0-x,0,x-x1);dy=max(y0-y,0,y-y1)
            if dx*dx+dy*dy<100:return False
        if any(0<(x-a)**2+(y-z)**2<256 for a,z in via_positions):return False
        return all(free((x+dx,y+dy,l),net) for dx in range(-5,6) for dy in range(-5,6) if dx*dx+dy*dy<=26 for l in (0,1))
    def astar(start,goal,net):
        pq=[(0,0,start)];cost={start:0};prev={};iters=0
        while pq:
            _,c,u=heapq.heappop(pq)
            if c!=cost[u]:continue
            if u==goal:
                path=[u]
                while u!=start:u=prev[u];path.append(u)
                return path[::-1]
            iters+=1
            if iters>500000:raise RuntimeError("router search budget")
            x,y,l=u
            neigh=[((x+dx,y+dy,l),10) for dx,dy in ((1,0),(-1,0),(0,1),(0,-1))]
            if viaok(x,y,net):neigh.append(((x,y,1-l),100))
            for v,w in neigh:
                if not free(v,net):continue
                n=c+w
                if n<cost.get(v,10**20):
                    cost[v]=n;prev[v]=u
                    h=(abs(v[0]-goal[0])+abs(v[1]-goal[1]))*10+(100 if v[2]!=goal[2] else 0)
                    heapq.heappush(pq,(n+h,n,v))
        raise RuntimeError("No route for net "+str((net,start,goal,occupancy[start[2]].get(start[:2]),occupancy[goal[2]].get(goal[:2]))))
    def track(a,z,net,layer):
        if a==z:return
        t=pcb.PCB_TRACK(b);t.SetStart(a);t.SetEnd(z);t.SetLayer(pcb.F_Cu if layer==0 else pcb.B_Cu);t.SetWidth(pcb.FromMM(.15));t.SetNetCode(net);b.Add(t)
    logs=[]
    names={n.GetNetname().lstrip("/"):code for code,n in b.GetNetsByNetcode().items()}
    order=[names[x] for x in os.environ.get("PD44_ROUTE_ORDER","MISO_IC,MISO,MOSI,CS_N,SCK,GND,+3V3").split(",")]
    for net in order:
        pads=list(padgroups[net]);connected=[pads.pop(0)]
        while pads:
            a,z=min(((a,z) for a in connected for z in pads),key=lambda pair:(pair[0].GetPosition()-pair[1].GetPosition()).SquaredEuclideanNorm())
            s=(g(a.GetPosition().x),g(a.GetPosition().y),0 if a.IsOnLayer(pcb.F_Cu) else 1);t=(g(z.GetPosition().x),g(z.GetPosition().y),0 if z.IsOnLayer(pcb.F_Cu) else 1)
            path=astar(s,t,net)
            track(a.GetPosition(),pos(*s[:2]),net,s[2]);track(pos(*t[:2]),z.GetPosition(),net,t[2])
            for (x,y,l),(xx,yy,ll) in zip(path,path[1:]):
                if l!=ll:
                    if (x,y) in via_positions:continue
                    via_positions.append((x,y))
                    v=pcb.PCB_VIA(b);v.SetPosition(pos(x,y));v.SetWidth(pcb.FromMM(.6));v.SetDrill(pcb.FromMM(.3));v.SetViaType(pcb.VIATYPE_THROUGH);v.SetLayerPair(pcb.F_Cu,pcb.B_Cu);v.SetNetCode(net);b.Add(v)
                    for layer in (0,1):fill(layer,x-11,y-11,x+11,y+11,net)
                else:
                    track(pos(x,y),pos(xx,yy),net,l)
                    fill(l,min(x,xx)-6,min(y,yy)-6,max(x,xx)+6,max(y,yy)+6,net)
            connected.append(z);pads.remove(z);logs.append({"net":net,"steps":len(path)})
    return logs
