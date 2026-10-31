"""Traceable harness topology, conservative A-pose routes and finite slack budget.

Rigid routing guides are NOT a simulated flexible cable. Dynamic checks bound
endpoint travel and required reserved length; obstacle/fatigue tests remain physical.
"""
from strength import *
from scipy.ndimage import distance_transform_edt
import heapq

class Router:
    def __init__(self,parts,solids):
        self.parts=parts;self.ss=[moved(s,FA[p['frame']]) for p,s in zip(parts,solids)]
        self.bb=np.array([s.bounding_box() for s in self.ss]).reshape(-1,2,3)
        self.lo=np.array([-150.,-260.,-8.]);self.step=4.;self.shape=(74,131,151);self.cache={};self.tests=0
    def clear(self,a,b,r,ignore=()):
        a=np.array(a);b=np.array(b)
        if np.linalg.norm(a-b)<1e-5:return True
        box0=np.minimum(a,b)-r;box1=np.maximum(a,b)+r
        ids=np.where(np.all(box1>self.bb[:,0],1)&np.all(box0<self.bb[:,1],1))[0]
        if not len(ids):return True
        s=beam(a,b,r)
        for i in ids:
            if self.parts[i]['name'] in ignore:continue
            self.tests+=1
            if (s^self.ss[i]).volume()>.02:return False
        return True
    def mask(self,r):
        key=round(r,2)
        if key in self.cache:return self.cache[key]
        m=np.zeros(self.shape,bool)
        for bb in self.bb:
            a=np.maximum(0,np.floor((bb[0]-r-self.lo)/self.step).astype(int));b=np.minimum(np.array(self.shape)-1,np.ceil((bb[1]+r-self.lo)/self.step).astype(int))
            m[a[0]:b[0]+1,a[1]:b[1]+1,a[2]:b[2]+1]=True
        self.cache[key]=m;return m
    def route(self,start,end,r):
        a=np.array(start['A']);b=np.array(end['A']);ig=[x['ignore'] for x in [start,end] if x.get('ignore')]
        if self.clear(a,b,r,ig):return np.array([a,b])
        m=self.mask(r+1.)
        def escape(row):
            p=np.array(row['A']);d=np.array(row.get('direction_A',[0,0,0]));prefix=[p]
            if row.get('escape_A'):
                for q in row['escape_A']:
                    q=np.array(q);assert self.clear(prefix[-1],q,r,[row.get('ignore','')]),row['id']+' explicit escape blocked';prefix.append(q)
                p=prefix[-1];d=np.zeros(3)
            if np.linalg.norm(d)>.5:
                for length in [8.,4.,2.]:
                    q=p+d*length
                    if self.clear(p,q,r,[row.get('ignore','')]):prefix.append(q);break
            p=prefix[-1];idx=np.round((p-self.lo)/self.step).astype(int)
            for extent in [5,10,18,30]:
                lo=np.maximum(idx-extent,0);hi=np.minimum(idx+extent,np.array(self.shape)-1)
                free=np.argwhere(~m[lo[0]:hi[0]+1,lo[1]:hi[1]+1,lo[2]:hi[2]+1])+lo
                ds=np.linalg.norm(self.lo+free*self.step-p,axis=1);order=np.argsort(ds)
                for ix in order[:160]:
                    q=self.lo+free[ix]*self.step
                    if self.clear(p,q,r,[row.get('ignore','')]):return prefix+[q],tuple(free[ix])
            raise RuntimeError('No clear escape '+row['id'])
        aa,s=escape(start);zz,g=escape(end)
        todo=[(0.,0.,s)];dist={s:0.};prev={};found=False
        while todo:
            _,c,u=heapq.heappop(todo)
            if dist.get(u)!=c:continue
            if u==g:found=True;break
            for ax in range(3):
                for sg in [-1,1]:
                    v=list(u);v[ax]+=sg;v=tuple(v)
                    if any(v[i]<0 or v[i]>=self.shape[i] for i in range(3)) or m[v]:continue
                    nc=c+1
                    if nc<dist.get(v,1e99):dist[v]=nc;prev[v]=u;heapq.heappush(todo,(nc+sum(abs(v[i]-g[i]) for i in range(3)),nc,v))
        if not found:raise RuntimeError('No grid route '+start['id']+' -> '+end['id'])
        chain=[g]
        while chain[-1]!=s:chain.append(prev[chain[-1]])
        chain.reverse();raw=np.array(aa[:-1]+[self.lo+np.array(q)*self.step for q in chain]+zz[-2::-1]);simple=[raw[0]];i=0
        while i<len(raw)-1:
            j=len(raw)-1
            while j>i+1 and not self.clear(raw[i],raw[j],r,ig if i==0 or j==len(raw)-1 else ()):j-=1
            simple.append(raw[j]);i=j
        return np.array(simple)

def main():
    parts,z,ss=read_assembly();digest=sha(OUT/'assembly_meshes.npz');router=Router(parts,ss)
    tails=load(OUT/'electronics/sensor_tails.json')['rows'];clips=load(OUT/'harness/anchors.json')['anchors'];nodes={}
    def node(key,frame,local,ignore=None,direction=None):
        w=FA[frame];r=dict(id=key,frame=frame,local_mm=np.array(local),A=w[:3,:3]@local+w[:3,3])
        if ignore:r['ignore']=ignore
        if direction is not None:r['direction_A']=w[:3,:3]@direction
        nodes[key]=r;return r
    for r in clips:node(r['id'],r['frame'],r['local_mm'])
    axisorder={r['id']:i for i,r in enumerate(PROFILE['axes'])}
    banks={b:[] for b in 'ABC'}
    for r in tails:banks['B' if r['sensor'].startswith('l_') else ('C' if r['sensor'].startswith('r_') else 'A')].append(r)
    ports=load(OUT/'electronics/carrier/placement.json')['footprints'];elec=load(OUT/'electronics/mechanical_integration.json');px=elec['board_origin_world_mm'][0];base=elec['board_origin_world_mm'][2]-60
    cables=[];edges={}
    for bank,sensors in banks.items():
        sensors.sort(key=lambda r:axisorder.get(r['axis'][0] if isinstance(r.get('axis'),list) else r.get('axis',''),999))
        for channel,r in enumerate(sensors):
            sensor=r['sensor'];side=sensor[0] if bank!='A' else ('l' if channel%2==0 else 'r');start='sensor_'+sensor
            node(start,r['frame'],r['tail_exit_local_mm'],r['connector_part'],r['tail_direction_local'])
            if sensor=='neck_humeral':
                p=np.array(nodes[start]['A']);v=np.array(nodes[start]['direction_A']);q=p+v*8
                nodes[start]['escape_A']=[q,[q[0],q[1],510.],[q[0]-24,q[1],506.]]
            if bank=='A':route=[side+'_back_wire_tab_1']
            elif any(w in sensor for w in ['clavicle','humeral']) or ('shoulder_' in sensor and 'ankle' not in sensor):route=[side+'_back_wire_tab_1']
            elif 'elbow' in sensor:route=[side+'_upperarm_wire_tab',side+'_back_wire_tab_1']
            elif any(w in sensor for w in ['forearm','wrist']):route=[side+'_forearm_wire_tab',side+'_upperarm_wire_tab',side+'_back_wire_tab_1']
            elif 'hip_abduction' in sensor or 'hip_pitch' in sensor:route=[side+'_pelvis_wire_tab',side+'_back_wire_tab_0']
            elif 'hip_twist' in sensor or 'knee' in sensor:route=[side+'_thigh_wire_tab',side+'_pelvis_wire_tab',side+'_back_wire_tab_0']
            elif 'ankle' in sensor:route=[side+'_shin_wire_tab',side+'_thigh_wire_tab',side+'_pelvis_wire_tab',side+'_back_wire_tab_0']
            elif 'toe' in sensor:route=[side+'_foot_wire_tab',side+'_shin_wire_tab',side+'_thigh_wire_tab',side+'_pelvis_wire_tab',side+'_back_wire_tab_0']
            else:raise ValueError(sensor)
            ref='J'+str({'A':10,'B':26,'C':42}[bank]+channel);p=next(p for p in ports if p['reference']==ref);front=p['side']=='F';x=px-5 if front else px+1.6+5
            world=np.array([x,32-p['x_mm'],base+60-p['y_mm']]);fr='thorax_flex';local=(np.linalg.inv(F0[fr])@np.r_[world,1])[:3];direction=np.array([-1.,0,0]) if front else np.array([1.,0,0]);node(ref,fr,local,'electronics_'+ref,np.linalg.inv(F0[fr])[:3,:3]@direction)
            if ref=='J40':nodes[ref]['escape_A']=[world+[8,0,0],world+[8,0,-8],[world[0]+8,-45,world[2]-8]]
            route=[start]+route+[ref];cable=dict(id=f'{bank}{channel+1:02}',sensor=sensor,port=ref,mux_address=channel,bank=bank,variant=r['variant'],route=route,pins=['GND','SENSOR3V45','SCK_'+bank,'SDO_'+f'{bank}{channel+1:02}','CS_'+bank,'MOSI_'+bank])
            cables.append(cable)
            for a,b in zip(route,route[1:]):edges.setdefault((a,b),[]).append(cable['id'])
    assert [len(banks[x]) for x in 'ABC']==[8,15,15]
    allcases=cases();framecases=[frames(q) for n,q in allcases];routes=[];lumps=[]
    cachefile=OUT/'harness/route_cache.json';cache=load(cachefile) if cachefile.exists() else {}
    cache.setdefault('paths',{});cache['geometry_sha256']=digest
    for (a,b),ids in edges.items():
        one=nodes[a];two=nodes[b];radius=1.05 if len(ids)==1 else 1.05*math.sqrt(len(ids)/.70)
        key=a+'__'+b+'__'+str(round(radius,5))+'__'+str(np.r_[one['A'],two['A']].round(5).tolist())
        path=np.array(cache['paths'][key]) if key in cache['paths'] else None
        if path is None or not all(router.clear(p,q,radius,[one.get('ignore',''),two.get('ignore','')]) for p,q in zip(path,path[1:])):path=router.route(one,two,radius)
        cache['paths'][key]=path;put(cachefile,cache)
        length=float(np.linalg.norm(np.diff(path,axis=0),axis=1).sum());dynamic=one['frame']!=two['frame'];maxdist=0.;worst=None
        for (name,q),F in zip(allcases,framecases):
            pts=[F[n['frame']][:3,:3]@n['local_mm']+F[n['frame']][:3,3] for n in [one,two]];d=float(np.linalg.norm(pts[1]-pts[0]))
            if d>maxdist:maxdist=d;worst=name
        reserve=math.pi*10+20 if dynamic else 15;cut=math.ceil((max(length,maxdist)+reserve)/5)*5
        # Actual CSG check uses the full estimated bundled diameter, not one wire.
        clear=all(router.clear(p,q,radius,[one.get('ignore',''),two.get('ignore','')]) for p,q in zip(path,path[1:]))
        row=dict(id=a+'__'+b,start=a,end=b,cables=ids,diameter_mm=2*radius,guide_A_mm=path,guide_length_mm=length,cut_length_per_cable_mm=cut,free_span=dynamic,max_endpoint_distance_mm=maxdist,worst_extension_pose=worst,reserve_over_max_distance_mm=cut-maxdist,minimum_dynamic_bend_radius_mm=10 if dynamic else None,A_CSG_clear=clear)
        routes.append(row)
        for n in [one,two]:lumps.append(dict(frame=n['frame'],local_mm=n['local_mm'],mass_g=cut*len(ids)*.0055/2,source=row['id']))
        print('ROUTE',a,b,len(ids),len(path),round(length,1),clear,flush=True)
    for c in cables:c['cut_length_mm']=sum(r['cut_length_per_cable_mm'] for r in routes if c['id'] in r['cables'])
    report=dict(status='PASS_ROUTING_AND_SLACK_CONDITIONAL' if all(r['A_CSG_clear'] and (not r['free_span'] or r['reserve_over_max_distance_mm']>=math.pi*10+20) for r in routes) else 'FAIL',geometry_sha256=digest,cable_count=len(cables),clip_count=len(clips),span_count=len(routes),motion_cases=len(allcases),wire='Six AWG30 finely stranded copper conductors, insulation OD <=0.7 mm, loose braid',mass_assumption_g_per_mm_of_6_core=.0055,total_wire_mass_g=sum(r['mass_g'] for r in lumps),total_6core_length_mm=sum(c['cut_length_mm'] for c in cables),minimum_dynamic_bend_radius_mm=10,rigid_obstacle_boolean_tests=router.tests,cables=cables,nodes=list(nodes.values()),spans=routes,scope='A-pose centreline routing guides checked with actual rigid solids and full estimated bundle diameter. Length budget covers finite endpoint travel, plus pi*10 mm bending allowance and 20 mm dressing reserve on every moving span. Guide corners do not define bent wire geometry. Reserved slack must be dressed as smooth service loops outside hinge pinch zones. This is not a flexible-body collision, bend-cycle, fatigue or all-pose cable clearance proof. Clamp each span at both anchors; never pull wire taut.')
    put(OUT/'harness/routes.json',report);put(OUT/'verification/harness_routing.json',report);put(OUT/'harness/mass_lumps.json',dict(geometry_sha256=digest,lumps=lumps))
    with (OUT/'harness/CABLE_CUTLIST.csv').open('w',encoding='utf-8-sig',newline='') as f:
        w=csv.writer(f);w.writerow(['cable','sensor','mainboard_port','mux_address','6core_cut_length_mm','sensor_board_variant','route']);w.writerows([c['id'],c['sensor'],c['port'],c['mux_address'],c['cut_length_mm'],c['variant'],' > '.join(c['route'])] for c in cables)
    print('HARNESS',report['status'],report['total_wire_mass_g'],'g',flush=True)
if __name__=='__main__':main()
