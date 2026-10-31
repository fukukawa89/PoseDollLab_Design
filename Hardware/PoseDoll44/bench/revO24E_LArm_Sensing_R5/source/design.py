"""R5: six coaxial O22 encoders plus independent one-axis TMAG wrist encoder.

Sensor boards follow the actual printed fork/output. Magnets reference the locked
shoulder screw via a hex drive plug, with positive axial capture by the pod.
Changing preload requires removal of the encoder and a fresh zero calibration.
"""
from common import *
GAP_SHIFT=.8 # 2.0 mm nominal magnet-to-package surface; modeled high-grade magnet margin.

def mag_body():
    # z=0 is outer face of the existing AX4 head; positive z points outwards.
    s=cyl([0,0,0],[0,0,3.0],7.0)
    s-=cyl([0,0,.5],[0,0,3.1],3.12)
    s+=k.hexagon([0,0,-1.25],[0,0,1],2.90,1.26)
    for x in [-4.9,4.9]:
        s-=cyl([x,0,-.1],[x,0,3.1],.9)
        s-=k.hexagon([x,0,-.1],[0,0,1],3.30,1.60)
        s-=md.Manifold.cylinder(.85,.8,1.65,32).translate([x,0,2.80])
    return s

def mag_lid():
    s=tube([0,0,3.0],[0,0,3.8],7.0,2.6)
    for x in [-4.9,4.9]:
        s-=cyl([x,0,2.9],[x,0,3.9],.9)
        s-=md.Manifold.cylinder(.85,.8,1.65,32).translate([x,0,2.80])
        s-=cyl([x,0,3.6],[x,0,3.9],1.65)
    return s

def pcb_solid(compact=False):
    # O22 PCB: local x=12, y=10, 1 mm FR4, component side towards magnet.
    # Chip package surface z=4.2; magnet surface z=3.0 => 1.2 mm air gap.
    s=box([-6,-5,5.95],[6,5,6.95])
    s+=box([-3.0,-2.45,4.2],[3.0,2.45,5.95])
    s+=box([-1.05,-4.8,4.95],[1.05,-3.4,5.95])
    s+=box([3.8,-1.0,4.95],[5.2,1.0,5.95])
    s+=box([-5.2,-1.0,4.95],[-3.8,1.0,5.95])
    if compact:
        s+=box([-4.6,3.45,5.0],[4.6,5.2,5.95])
        # Five individual leads turn around the board edge into a back-side channel.
        for x in [-4.2,-2.1,0,2.1,4.2]:
            pts=[[x,4.05,5.35],[x,5.3,5.35],[x,6.3,6.35],[x,6.3,9.0]]
            for p,q in zip(pts,pts[1:]):s+=beam(p,q,.35)
    else:s+=box([-4.8,3.5,5.0],[4.8,9.5,6.0])
    return s.translate([0,0,GAP_SHIFT])

def named_poses():
    ans=[('zero',{})]+[(n,p['angles']) for n,p in POSES.items()]
    for ax in PROFILE['axes']:
        for q in np.linspace(*ax['limits_deg'],math.ceil(np.ptp(ax['limits_deg'])/5)+1):
            ans.append((ax['id']+'/'+str(q),{ax['id']:float(q)}))
    # Explicit independent wrist rectangle: no coupling restriction.
    wf=next(x for x in PROFILE['axes'] if x['id']=='l_wrist_flex')
    wd=next(x for x in PROFILE['axes'] if x['id']=='l_wrist_deviation')
    for x in np.linspace(*wf['limits_deg'],9):
        for y in np.linspace(*wd['limits_deg'],9):
            ans.append((f'wrist/{x}/{y}',{'l_wrist_flex':float(x),'l_wrist_deviation':float(y)}))
    return ans

def channels():
    ints=load(BASE/'interfaces.json');ch=[]
    for r,axis,name in zip(ints['rolls'],['l_shoulder_flex','l_upperarm_roll','l_forearm_roll'],['SHOULDER_PITCH','UPPER_ARM','FOREARM']):
        # Component side faces the locked AX head, facing down local +z.
        A=np.array(r['W'])@T([0,0,-9.1],np.diag([1,-1,-1]))
        ch.append(dict(id=r['id'],axis=axis,kind='roll',A=A@rot([0,0,1],{'RP':90,'RU':255,'RF':180}[r['id']]),mag_A=A,stand_off_mm=0,pcb_frame=r['output_frame'],magnet_frame=r['fixed_frame'],host=name,sign=-1))
    for r,axis,name in zip(ints['hinges'],['l_shoulder_abduct','l_elbow_flex'],['SHOULDER_ABDUCT','ELBOW_OUTPUT']):
        A=np.array(r['M'])@T([0,19.8,0],basis([0,1,0]))
        ch.append(dict(id=r['id'],axis=axis,kind='hinge',A=A,mag_A=A,stand_off_mm=0,pcb_frame=r['output_frame'],magnet_frame=r['fixed_frame'],host=name,sign=-1))
    W=F0['l_wrist_flex']
    for cid,axis,normal,pcbfr,magfr,host,sgn in [
        ('WF','l_wrist_flex',[0,1,0],'l_forearm_roll','l_wrist_flex','FOREARM',1)]:
        A=W@T(np.array(normal)*19.8,basis(normal))
        ch.append(dict(id=cid,axis=axis,kind='hinge',A=A,mag_A=A,stand_off_mm=0,pcb_frame=pcbfr,magnet_frame=magfr,host=host,sign=sgn))
    ch.append(dict(id='WD',axis='l_wrist_deviation',kind='vector',A=W@T([-18,0,-16],basis([-1,0,0])),mag_A=W@T([-12.5,0,-16],basis([0,1,0])),pcb_frame='l_wrist_flex',magnet_frame='l_wrist_deviation',host='KEEP_E-P019',sign=1))
    return ch

def cover_positions(compact=False,variant=None):
    if variant=='RU':return [(-4.0,-9),(4.0,-9)]
    return [(-10.3,0),(10.3,0)] if compact else [(-5.5,-8),(5.5,-8)]

def pcb_tray(compact=False,variant=None):
    s=box([-7.8,-7.0,5.35],[7.8,7.0,7.15])
    s-=box([-6.15,-5.15,5.95],[6.15,5.15,7.3])
    for lo,hi in [([-3.25,-2.7,4],[3.25,2.7,6.0]),([-1.3,-5.1,4.7],[1.3,-3.15,6.0]),([3.5,-1.3,4.7],[5.5,1.3,6.0]),([-5.5,-1.3,4.7],[-3.5,1.3,6.0]),([-5.1,3.3,4.7],[5.1,16,7.5])]:s-=box(lo,hi)
    s=s.translate([0,0,GAP_SHIFT])
    s+=tube([0,0,4.05],[0,0,4.65],7.8,6.4)
    for x in [-7,7]:
        for y in [-5.8,5.8]:s+=box([x-.8,y-.8,4.05],[x+.8,y+.8,5.96+GAP_SHIFT])
    if compact:s=s^box([-8,-6.2,0],[8,6.2,9])
    for x,y in cover_positions(compact,variant):
        if compact:s+=box([min(x-2.5,-6.5) if x<0 else 6.5,-2.5,2.4],[max(x+2.5,6.5) if x>0 else -6.5,2.5,7.15])
        else:s+=box([x-2.5,y-2.5,3.25],[x+2.5,-5.2,7.15+GAP_SHIFT])
        s-=cyl([x,y,2.3],[x,y,7.3+GAP_SHIFT],1.1)
        s-=k.hexagon([x,y,2.3],[0,0,1],4.15,1.75)
    s-=cyl([0,0,-.1],[0,0,3.95],7.2)
    return s

def pcb_back(compact=False,variant=None):
    s=box([-7.8,-11.5 if variant=='RU' else -10.5,7.15],[7.8,8.0,8.35])
    s-=box([-5.1,3.3,7.0],[5.1,8.2,7.65])
    for x in [-6,6]:s-=cyl([x,6.3,7.05],[x,6.3,8.45],.65)
    if compact:
        s=box([-7.8,-6.2,7.15],[7.8,5.5,8.35])+box([-12.8,-2.5,7.15],[12.8,2.5,8.35])
        s-=box([-5.1,3.3,7],[5.1,5.6,7.65])
    for x,y in cover_positions(compact,variant):
        s-=cyl([x,y,7],[x,y,8.5],1.1)
        s-=md.Manifold.cylinder(.95,1.1,2.05,32).translate([x,y,7.15])
        s-=cyl([x,y,8.05],[x,y,8.5],2.05)
    # Shallow socket holds a 0.2 mm soft insulating shim above the FR4 back.
    return s.translate([0,0,GAP_SHIFT])

def roll_carrier(variant=None):
    s=pcb_tray(variant=variant)
    for side in [-1,1]:
        s+=beam([side*7.0,0,6.65],[side*7.0,14,6.65],1.1)
    flange=box([-13,13,3.5],[13,15,8.35])
    flange-=box([-5.1,12.9,4.7],[5.1,15.1,7.5])
    for x in [-10.5,10.5]:flange-=cyl([x,12.9,6.5],[x,15.1,6.5],1.1)
    s+=flange
    s-=expanded(pcb_back(variant=variant),.1)
    s-=expanded(pcb_solid(),.1)
    return s

def expanded(s,gap=.12):
    v,f=e.base.a.mesh_data(s)
    source=md.Manifold(md.Mesh64(np.array(v,copy=True),np.array(f,dtype=np.uint64,copy=True)))
    return union([source]+[source.translate(np.eye(3)[i]*gap*side) for i in range(3) for side in [-1,1]])

def hinge_carrier(ch,host,obstacles):
    A=ch['A'];local=moved(host,np.linalg.inv(A));direction=1 if ch['id'] in ['HS','HE'] else -1;off=ch['stand_off_mm'];compact=ch['id']=='WD';Q=rot([0,0,1],90) if compact else np.eye(4)
    ring=tube([0,0,-8.7],[0,0,-5.4],10.5,8.35)
    ring+=tube([0,0,-5.8],[0,0,-5.35],10.5,6.7)
    ylo,yhi=sorted([direction*6,direction*14])
    saddle=box([-5.2,ylo,-10.4],[5.2,yhi,-4.7])-expanded(local)
    for side in [-1,1]:
        ring+=beam([side*9.5,0,-7],[side*9.5,0,1.5+off],1.65)
        for y in [-13.5,13.5]:
            ring+=beam([side*9.5,0,1.5+off],[side*6,y,1.5+off],1.65)
    for y in [-13.5,13.5]:
        ring+=box([-8,y-2.4,-.9+off],[7,y+2.4,3.9+off])
        ring-=cyl([-16,y,1.5+off],[16,y,1.5+off],1.1)
        ring-=cyl([-16,y,1.5+off],[-8,y,1.5+off],2.65)
        ring-=cyl([7,y,1.5+off],[16,y,1.5+off],2.65)
    ring=moved(ring,Q)+saddle
    ring-=expanded(local)
    if obstacles is not None:ring-=obstacles
    # Clearance for the two axial PCB-cover fastener assemblies, including the outer jam nut.
    for x,y in cover_positions(compact):ring-=cyl([x,y,-.5+off],[x,y,7.4+off],2.55)
    left=ring^moved(box([-50,-50,-50],[-.08,50,50]),Q)
    right=ring^moved(box([.08,-50,-50],[50,50,50]),Q)
    tray=pcb_tray(compact).translate([0,0,off])
    for y in [-6,6]:left+=moved(beam([-9.5,0,1.5+off],[-5.8,y,5.7+off],1.5),Q)
    left+=tray
    # Main carrier enters axially. The opposite clamp retains the rear stem hook;
    # release only the main half's rear hook for a real, collision-free approach.
    rear=box([-25,-25,-30],[25,25,-5.8])
    left-=union([expanded(local.translate([0,0,-q]),.14)^rear for q in np.linspace(0,24,25)])
    left-=expanded(right,.1)
    left-=expanded(pcb_back(compact).translate([0,0,off]),.1)
    left-=expanded(pcb_solid(compact).translate([0,0,off]),.12)
    left-=cyl([0,0,-30+off],[0,0,3.96+off],7.2)
    for x,y in cover_positions(compact):
        left-=cyl([x,y,-20+off],[x,y,3.25+off],3.35)
        left-=k.hexagon([x,y,3.24+off],[0,0,1],4.15,.81)
        left-=cyl([x,y,4.05+off],[x,y,7.15+GAP_SHIFT+off],1.12)
    # Opposite half enters radially after the axial main carrier is seated.
    right-=union([expanded(local.translate([-q,0,0]),.14) for q in np.linspace(0,8,17)])
    # Detached corner chips left by component and bolt clearance have no function.
    fragments=left.as_original().simplify(.01).decompose();assert sum(s.volume() for s in fragments if s.volume()<10)<30
    left=max(fragments,key=lambda s:s.volume())
    # Soft 0.1 mm liner strips at the keyed saddle remove printed fit play.
    return left,right

def modify_roll(original,A,protected,obstacles=None):
    s=moved(original,np.linalg.inv(A))
    # In cap coordinates: z increases away from the inherited preload screw.
    reinforcement=r4.oval_loft([(-3,12.5,12.5),(0,12.3,12.3),(11.5,12.3,12.3),(14,8.0,8.0),(15.5,7,7)])
    reinforcement-=moved(protected,np.linalg.inv(A))
    s+=reinforcement
    s-=cyl([0,0,-.9],[0,0,9.9],7.4)
    # Entire new cassette passes through this radiused side window.
    cut=box([-7.3,-35,-2.8],[7.3,35,11.5])+box([-8.3,-35,-1.8],[8.3,35,10.5])
    for x in [-7.3,7.3]:
        for z in [-1.8,10.5]:cut+=cyl([x,-35,z],[x,35,z],1)
    s-=cut
    for x in [-10.5,10.5]:
        pad=box([x-2.3,4,3.5],[x+2.3,13,9.5])
        s+=pad
    for x in [-10.5,10.5]:
        s-=cyl([x,3.0,6.5],[x,13.1,6.5],1.1)
        s-=k.hexagon([x,8.8,6.5],[0,1,0],4.15,3.4)
        # Nut enters from the exposed outside edge, never through the PCB gap.
        s-=box([x if x>0 else -15,8.8,4.1],[15 if x>0 else x,12.2,8.9])
    if obstacles is not None:
        # Trim only added material; the inherited load path is never collision-carved.
        inherited=moved(original,np.linalg.inv(A))
        s-=moved(obstacles,np.linalg.inv(A))-inherited
    return moved(s,A)

def wd_core(original):
    return original

def wd_hand(original):
    # R2 strengthened fork filled the earlier keeper-hole volume. Restore its
    # actual accessible screw and nut entry without changing the friction ears.
    Q=F0['l_wrist_flex'];s=moved(original,np.linalg.inv(Q));mc=np.array([-12.5,0,-10.8])
    s-=cyl(mc+[0,-8,0],mc+[0,5,0],1.1)
    s-=moved(k.hexagon([0,0,6.5],[0,0,1],4.2,5),T(mc+[0,3,0],basis([0,-1,0])))
    s-=cyl(mc+[0,2,0],mc+[0,7,0],3.6)
    return moved(s,Q)

def wd_parts(add,ch):
    Q=F0['l_wrist_flex'];A=ch['A'];pf=ch['pcb_frame'];mf=ch['magnet_frame']
    def w(s):return moved(s,A)
    pcb=box([-6,-5,1.2],[6,5,2.0])+box([-2.5,-1.5,0],[2.5,1.5,1.2])+box([-2.2,3.5,.3],[2.2,8,1.2])
    case=box([-7.6,-6.5,.6],[7.6,6.5,2.2])
    case-=box([-6.2,-5.2,1.2],[6.2,5.2,2.4])
    case-=expanded(pcb,.15)
    case-=box([-2.5,3.3,-.1],[2.5,12,3.0])
    back=box([-7.6,-10.5,2.2],[7.6,6.5,6.6])-box([-5.5,-4.5,2.1],[5.5,4.5,5.0])
    back-=box([-2.5,3.3,1],[2.5,7,3.6])
    for x in [-5.5,5.5]:
        case+=box([x-2.6,-10.6,.1],[x+2.6,-5.5,2.3])
        case-=cyl([x,-8,-1],[x,-8,3],1.1)
        case-=k.hexagon([x,-8,.1],[0,0,1],4.15,3.05)
        back-=cyl([x,-8,2.1],[x,-8,6.7],1.1)
        back-=k.hexagon([x,-8,.0],[0,0,1],4.2,3.2)
    pts=[[0,0,-6],[0,0,-10.5],[0,-17,-10.5],[-22,-17,-16],[-22,-5,-16]]
    bracket=union([beam(p,q,2.2) for p,q in zip(pts,pts[1:])])
    bracket+=beam([-5,-17,-10.5],[-22,-10,-16],2.2)
    back+=moved(moved(bracket,Q),np.linalg.inv(A))
    back-=expanded(case,.08)+expanded(pcb,.12)+expanded(box([-5.8,-4.8,2],[5.8,3.2,2.2]),.05)
    add('WD_CARRIER',pf,w(case),label='WD 三轴传感板托')
    add('WD_BACK',pf,w(back),label='WD 固定支架与后盖')
    add('WD_PCB',pf,w(pcb),'electronics','S1_TMAG5170A1_12x10x0P8')
    add('WD_PCB_SHIM',pf,w(box([-5.8,-4.8,2],[5.8,3.2,2.2])),'insulator','FOAM_INSULATOR_0P2')
    for x in [-5.5,5.5]:
        add(f'WD_BACK_BOLT_{x}',pf,w(k.screw([x,-8,7.1],[0,0,-1],2,8)),'metal','M2x8_BRASS')
        add(f'WD_BACK_W_{x}',pf,w(k.washer([x,-8,6.6],[0,0,1],5,2.2,.5)),'metal','W2_BRASS')
        add(f'WD_BACK_N_{x}',pf,w(k.nut([x,-8,.1],[0,0,1],2,4,3)),'metal','NL2_BRASS')
    mp=np.array([-12.5,0,-16]);mc=mp+[0,0,5.2]
    add('WD_MAGNET',mf,moved(cyl(mp+[0,-1.0,0],mp+[0,1.5,0],3),Q),'magnet','MAGNET_D6_T2P5_DIAMETRIC')
    add('WD_MAG_SPACER',mf,moved(cyl(mp+[0,-1.5,0],mp+[0,-1,0],3.0),Q),label='WD 旧磁铁盲座 0.5 mm 补高片')
    S=Q@T(mc+[0,3,0],basis([0,-1,0]))
    add('WD_MAG_KEEP_SCREW',mf,moved(k.screw([0,0,.5],[0,0,1],2,10),S),'metal','M2x10_BRASS')
    add('WD_MAG_KEEP_W',mf,moved(k.washer([0,0,.5],[0,0,1],7,2.2,.5),S),'metal','W2_OD7_BRASS')
    add('WD_MAG_KEEP_N',mf,moved(k.nut([0,0,6.5],[0,0,1],2,4,3),S),'metal','NL2_BRASS')

def build():
    a,ss=baseline();parts=[];W={p['name']:moved(s,F0[p['frame']]) for p,s in zip(a,ss)};chs=channels()
    def add(name,frame,solid,role='structure',sku=None,label=None,source=None):
        assert str(solid.status())=='Error.NoError' and not solid.is_empty(),(name,str(solid.status()),solid.volume())
        p=dict(name=name,frame=frame,s=moved(solid,np.linalg.inv(F0[frame])),role=role,sku=sku,label=label or name,source=source)
        parts.append(p);return p
    modified={ch['host']:ch for ch in chs if ch['kind']=='roll'}
    extra_obstacles={}
    # Elbow end folds back toward the upper-arm sensor window at 145 degrees.
    p7=next(p for p in a if p['name']=='UPPER_ARM');obs=[]
    for angle in np.linspace(0,145,31):
        ff=frames({'l_elbow_flex':float(angle)})
        for name in ['ELBOW_OUTPUT','FOREARM','RF_keeper']:
            pp=next((p for p in a if p['name']==name),None)
            if pp:
                ww=F0[p7['frame']]@np.linalg.inv(ff[p7['frame']])@ff[pp['frame']]@np.linalg.inv(F0[pp['frame']])
                piece=moved(W[name],ww)^moved(box([-25,-25,-5],[25,25,16]),modified['UPPER_ARM']['mag_A'])
                if not piece.is_empty():obs.append(expanded(piece,.35))
    extra_obstacles['UPPER_ARM']=union(obs)
    for host,targets,samples in [
        ('SHOULDER_PITCH',['SHOULDER_ABDUCT','RU_keeper'],[{'l_shoulder_abduct':float(v)} for v in np.linspace(-20,165,48)]),
        ('FOREARM',['KEEP_E-P018','KEEP_E-P019'],[{'l_wrist_flex':float(f),'l_wrist_deviation':float(d)} for f in np.linspace(-65,70,28) for d in [-20,0,30]])]:
        hp=next(p for p in a if p['name']==host);cuts=[];region=moved(box([-25,-25,-5],[25,25,17]),modified[host]['mag_A'])
        for q in samples:
            ff=frames(q)
            for name in targets:
                pp=next(p for p in a if p['name']==name);tr=F0[hp['frame']]@np.linalg.inv(ff[hp['frame']])@ff[pp['frame']]@np.linalg.inv(F0[pp['frame']])
                piece=moved(W[name],tr)^region
                if not piece.is_empty():cuts.append(expanded(piece,.35))
        if cuts:extra_obstacles[host]=union(cuts)
    for p,s in zip(a,ss):
        n=p['name'];w=W[n]
        if n in modified:
            protect=union([expanded(W[o['name']],.02) for o in a if o['role']!='structure'])
            w=modify_roll(w,modified[n]['A'],protect,extra_obstacles.get(n));W[n]=w
        if n=='KEEP_E-P019':w=wd_core(w);W[n]=w
        if n=='KEEP_E-P018':w=wd_hand(w);W[n]=w
        changed=n in modified or n in ['KEEP_E-P019','KEEP_E-P018']
        q=add(n,p['frame'],w,p['role'],p['sku'],p.get('label',n),p['part_number']);q.update(part_number=p['part_number'].replace('S4-','R5-') if changed else p['part_number'],baseline_name=n,reprint=changed)
    for ch in chs:
        if ch['kind']=='vector':wd_parts(add,ch);continue
        n=ch['id'];compact=n=='WD';A=ch['A'];off=ch['stand_off_mm'];M=ch['mag_A']@T([0,0,off]);B=A@T([0,0,off]);pf=ch['pcb_frame'];mf=ch['magnet_frame']
        magnetbody=mag_body().translate([0,0,off])
        if off:
            magnetbody-=cyl([0,0,off-1.3],[0,0,off-.01],2)
            magnetbody+=cyl([0,0,0],[0,0,off+.01],1.8)+k.hexagon([0,0,-1.25],[0,0,1],2.90,1.3)
        if compact:magnetbody=magnetbody^box([-8,-3.75,-3],[8,3.75,30])
        lid=mag_lid()^box([-8,-3.75,-3],[8,3.75,5]) if compact else mag_lid()
        add(n+'_MAG_BODY',mf,moved(magnetbody,ch['mag_A']),label=n+' 六角定位磁铁座')
        add(n+'_MAG_LID',mf,moved(lid,M),label=n+' 磁铁防脱盖')
        add(n+'_MAGNET',mf,moved(cyl([0,0,.5],[0,0,3],3),M),'magnet','MAGNET_D6_T2P5_DIAMETRIC')
        for x in [-4.9,4.9]:
            # M1.6 countersunk brass screw, 4 mm including head.
            bolt=cyl([x,0,-.2],[x,0,2.86],.8)+md.Manifold.cylinder(.8,.8,1.6,32).translate([x,0,2.84])+cyl([x,0,3.62],[x,0,3.8],1.6)
            bolt-=box([x-.18,-1,3.35],[x+.18,1,3.9])+box([x-1,-.18,3.35],[x+1,.18,3.9])
            add(n+f'_MAG_SCREW_{x}',mf,moved(bolt,M),'metal','M1.6x4_CS_BRASS')
            add(n+f'_MAG_NUT_{x}',mf,moved(k.nut([x,0,.1],[0,0,1],1.6,3.2,1.3),M),'metal','N1.6_BRASS')
        if ch['kind']=='roll':
            main=roll_carrier(n)
            if n=='RU':main-=moved(extra_obstacles['UPPER_ARM'],np.linalg.inv(A))
        else:
            obstacle_name={'HS':'SHOULDER_PITCH','HE':'UPPER_ARM','WF':'KEEP_E-P019','WD':'KEEP_E-P019'}[n]
            obstacle_part=next(p for p in a if p['name']==obstacle_name)
            obstacle_local=moved(W[obstacle_name],np.linalg.inv(F0[obstacle_part['frame']]))
            limits=next(x['limits_deg'] for x in PROFILE['axes'] if x['id']==ch['axis'])
            cuts=[]
            for angle in np.linspace(*limits,math.ceil(np.ptp(limits)/4)+1):
                ff=frames({ch['axis']:float(angle)})
                transform=np.linalg.inv(A)@F0[pf]@np.linalg.inv(ff[pf])@ff[obstacle_part['frame']]
                piece=moved(obstacle_local,transform)^box([-15,-17,-12],[15,17,-3.5])
                if not piece.is_empty():cuts.append(expanded(piece,.22))
            main,right=hinge_carrier(ch,W[ch['host']],union(cuts) if cuts else None)
        add(n+'_CARRIER',pf,moved(main,A),label=n+' 传感板托与安装座')
        if ch['kind']=='hinge':
            add(n+'_CLAMP',pf,moved(right,A),label=n+' 叉耳定位夹半盖')
            for y in [-13.5,13.5]:
                CB=B@rot([0,0,1],90) if compact else B
                add(n+f'_CLAMP_BOLT_{y}',pf,moved(k.screw([-8.5,y,1.5],[1,0,0],2,20),CB),'metal','M2x20_BRASS')
                for tag,x,sg in [('HEAD',-8.5,1),('NUT',7,1)]:add(n+f'_CLAMP_W_{tag}_{y}',pf,moved(k.washer([x,y,1.5],[sg,0,0],5,2.2,.5),CB),'metal','W2_BRASS')
                for j,x in enumerate([7.5,9.1]):add(n+f'_CLAMP_N{j}_{y}',pf,moved(k.nut([x,y,1.5],[1,0,0],2,4,1.6),CB),'metal','N2_BRASS')
        else:
            for x in [-10.5,10.5]:
                add(n+f'_MOUNT_BOLT_{x}',pf,moved(k.screw([x,15.5,6.5],[0,-1,0],2,8),A),'metal','M2x8')
                add(n+f'_MOUNT_W_{x}',pf,moved(k.washer([x,15,6.5],[0,1,0],5,2.2,.5),A),'metal','W2')
                add(n+f'_MOUNT_N_{x}',pf,moved(k.nut([x,9,6.5],[0,1,0],2,4,3),A),'metal','NL2')
        add(n+'_PCB',pf,moved(pcb_solid(compact),B),'electronics','O22_MT6701CT_12x10x1')
        add(n+'_PCB_SHIM',pf,moved(box([-5.8,-4.8,6.95+GAP_SHIFT],[5.8,3.2,7.15+GAP_SHIFT]),B),'insulator','FOAM_INSULATOR_0P2')
        back=pcb_back(compact,n)
        if n=='RU':back-=moved(extra_obstacles['UPPER_ARM'],np.linalg.inv(B))
        add(n+'_BACK',pf,moved(back,B),label=n+' 传感板后盖')
        for x,y in cover_positions(compact,n):
            bolt=cyl([x,y,-1.65+GAP_SHIFT],[x,y,7.17+GAP_SHIFT],1)+md.Manifold.cylinder(.9,1,1.9,32).translate([x,y,7.15+GAP_SHIFT])+cyl([x,y,8.03+GAP_SHIFT],[x,y,8.35+GAP_SHIFT],1.9)
            bolt-=box([x-.2,y-1.1,7.7+GAP_SHIFT],[x+.2,y+1.1,8.5+GAP_SHIFT])+box([x-1.1,y-.2,7.7+GAP_SHIFT],[x+1.1,y+.2,8.5+GAP_SHIFT])
            add(n+f'_BACK_BOLT_{x}',pf,moved(bolt,B),'metal','M2x10_CS_BRASS')
            for j,z in enumerate([2.4,.8]):add(n+f'_BACK_N{j}_{x}',pf,moved(k.nut([x,y,z],[0,0,1],2,4,1.6),B),'metal','N2_BRASS')
    core=next(p for p in parts if p['name']=='KEEP_E-P019');arm=next(p for p in parts if p['name']=='WD_BACK')
    core['s']+=arm['s'];parts.remove(arm)
    # Shoulder split clamp corner clears the RP board lid through the whole hinge arc.
    victim=next(p for p in parts if p['name']=='HS_CLAMP');other=next(p for p in parts if p['name']=='RP_BACK');cuts=[]
    for angle in np.linspace(-20,165,48):
        ff=frames({'l_shoulder_abduct':float(angle)})
        cuts.append(expanded(moved(other['s'],np.linalg.inv(ff[victim['frame']])@ff[other['frame']]),.35))
    victim['s']-=union(cuts)
    hs=next(c for c in chs if c['id']=='HS');A=hs['A'];cuts=[]
    offsets=[A[:3,0]*8+A[:3,2]*q for q in np.linspace(0,25,26)]+[A[:3,0]*q for q in np.linspace(0,8,17)]
    for name in ['RP_CARRIER','RP_BACK']:
        other=next(p for p in parts if p['name']==name)
        for off in offsets:
            tr=np.linalg.inv(F0[victim['frame']])@T(-off)@F0[other['frame']];piece=moved(other['s'],tr)^expanded(victim['s'],.5)
            if not piece.is_empty():cuts.append(expanded(piece,.35))
    if cuts:victim['s']-=union(cuts)
    victim=next(p for p in parts if p['name']=='HS_BACK');other=next(p for p in parts if p['name']=='KEEP_E-H1138')
    ff=frames(POSES['arms_elbow_max']['angles']);victim['s']-=expanded(moved(other['s'],np.linalg.inv(ff[victim['frame']])@ff[other['frame']]),.4)
    from service_clearance import trim
    trim(parts,expanded)
    restore_shoulder_seats(parts)
    serial=0
    for p in parts:
        if 'part_number' not in p:
            serial+=1;p['part_number']='R5-E'+str(serial).zfill(3)
    return parts,chs

def restore_shoulder_seats(parts):
    # Preserve the entire original fork end above the RP side-entry ceiling.
    # A broad overlapping region avoids thin crescent fragments at load seats.
    old,W=world_solids();p=next(p for p in parts if p['name']=='SHOULDER_PITCH')
    w=moved(p['s'],F0[p['frame']]);A=next(c['A'] for c in channels() if c['id']=='RP');guard=moved(box([-20,-20,10],[20,20,35]),A)
    restore=W[p['name']]^guard
    p['s']=moved(w+restore,np.linalg.inv(F0[p['frame']]))

def save():
    OUT.mkdir(exist_ok=True)
    for f in ['verification','stl_print','parts_assembly','printing','preview','source','electronics','harness','assembly_guide','images']:(OUT/f).mkdir(exist_ok=True)
    parts,chs=build();z={};a=[]
    for i,p in enumerate(parts):
        v,f=e.base.a.mesh_data(p['s']);z[str(i)+'v']=v;z[str(i)+'f']=f
        q={k:v for k,v in p.items() if k!='s'};q.update(i=i,bounds_mm=e.bounds(p['s']).tolist(),volume_mm3=p['s'].volume(),components=sum(s.volume()>.01 for s in p['s'].decompose()));a.append(q)
    put(OUT/'production_assembly.json',dict(revision='O24E_LArm_Sensing_R5',parts=a))
    np.savez_compressed(OUT/'production_meshes.npz',**z)
    put(OUT/'channels.json',[{k:(v.tolist() if isinstance(v,np.ndarray) else v) for k,v in c.items()} for c in chs])
    print('BUILT',len(parts),'parts; structural',sum(p['role']=='structure' for p in parts),'bad components',[(p['name'],p['components']) for p in a if p['components']!=1],flush=True)
    return parts,chs

def probe():
    a,S=world_solids();world={n:S[n] for n in S};parts={p['name']:p for p in a}
    for ch in channels():
        A=ch['A'];is_=np.linalg.inv(A)
        print(ch['id'], 'magnet',ch['magnet_frame'],'board',ch['pcb_frame'],flush=True)
        for tag,solid,frame in [('cap',mag_body()+mag_lid(),ch['magnet_frame']),('PCB',pcb_solid(),ch['pcb_frame'])]:
            s=moved(solid,A);b=e.bounds(s);hits={}
            for n,o in world.items():
                bb=e.bounds(o)
                if np.any(bb[0]>b[1]) or np.any(bb[1]<b[0]):continue
                v=(s^o).volume()
                if v>.02:hits[n]=round(v,4)
            print(tag,hits,flush=True)
        host=moved(world[ch['host']],is_)
        print('host bounds',np.round(e.bounds(host),2).tolist(),flush=True)
    return

if __name__=='__main__':save()
