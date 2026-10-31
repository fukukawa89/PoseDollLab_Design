"""O24C-T1 mechanical bench kit. Millimetres; printable parts, real metal fasteners.

The C arm is a read-only reference. T1 is deliberately an enlarged test fixture,
not a manufacturing release of the 560 mm doll. No printer is contacted.
Run with design/.venv/Scripts/python.exe.
"""
from pathlib import Path
import sys, json, math, hashlib, csv
import numpy as np
import manifold3d as md
import trimesh

HERE=Path(__file__).resolve().parent
H=HERE.parents[1]; ROOT=H.parents[1]; OUT=H/'bench/revO24C_T1'
sys.path.insert(0,str(H/'cad/revO24'))
import arm as a
put=a.put; sha=a.sha; box=a.box; cyl=a.cylinder; tube=a.tube; beam=a.beam
rot=a.rot; moved=a.moved; union=a.union
Y=np.array([0.,1,0]); X=np.array([1.,0,0]); Z=np.array([0.,0,1])
REVISION='O24C-T1-S3'

# Procurement alternatives verified against the unchanged printed geometry.
# Assembly labels/meshes retain their original nominal .3 / 1.6 mm dimensions.
PURCHASE_OPTIONS={
    'W2':dict(spec='M2 平垫圈 5×2.2×0.5',notes='S1共8片：导向座2片必须0.5mm；衬片/加载杆另6片可用0.5或原0.3mm。基准模型后6片仍为0.3；见HARDWARE_ALTERNATIVES.html。'),
    'FR6':dict(spec='M6 大平垫圈 18×6.4，厚1.5或1.6',notes='优先采购1.5mm；基准装配模型为1.6mm。两片同厚使用；1.5mm时浮动压板多压入约0.2mm，无需重印；见HARDWARE_ALTERNATIVES.html。'),
}

def sph(r):return md.Manifold.sphere(r,96)
def hexagon(p,axis,af,length):
    p=np.array(p,float);z=a.unit(axis)
    x=a.unit(np.cross(np.eye(3)[np.argmin(abs(z))],z));y=np.cross(z,x)
    return md.Manifold.cylinder(length,af/math.sqrt(3),circular_segments=6).transform(np.c_[x,y,z,p])
def nut(p,axis,d,af,height):
    p=np.array(p,float);axis=np.array(axis,float)
    return hexagon(p,axis,af,height)-cyl(p-axis*.01,p+axis*(height+.01),d/2+.02)
def screw(p,axis,d,length,hd=None,hh=None):
    p=np.array(p,float);axis=np.array(axis,float);hd=hd or {2:3.8,3:5.5,4:7}[d];hh=hh or d
    # ISO 4762 outer envelope. Thread major diameter is retained, helical form omitted.
    s=cyl(p,p+axis*length,d/2)+cyl(p-axis*hh,p,hd/2)
    return s-hexagon(p-axis*(hh+.01),axis,{2:1.5,3:2.5,4:3}[d],hh*.55)
def washer(p,axis,od,id,t):
    p=np.array(p,float);axis=np.array(axis,float)
    return tube(p,p+axis*t,od/2,id/2)

class Kit:
    def __init__(self):self.parts=[];self.prints={};self.bom={};self.stacks=[]
    def add(self,id,label,s,station,frame='fixed',printable=False,orientation=None,qty=1,role='structure',note=''):
        assert not s.is_empty() and str(s.status())=='Error.NoError',id
        row=dict(id=id,label=label,s=s,station=station,frame=frame,printable=printable,role=role,note=note)
        self.parts.append(row)
        if printable:
            self.prints[id]=dict(row,orientation=np.eye(4) if orientation is None else orientation,qty=qty)
        return row
    def metal(self,id,label,s,station,frame='fixed',sku=None,role='metal',note=''):
        self.add(id,label,s,station,frame,role=role,note=note)
        if sku:
            if sku not in self.bom:self.bom[sku]=dict(spec=label,qty=0,stations=set(),notes=note)|PURCHASE_OPTIONS.get(sku,{})
            self.bom[sku]['qty']+=1;self.bom[sku]['stations'].add(station)
    def stack(self,id,length,nut_far,pitch,note):
        self.stacks.append(dict(id=id,underhead_to_tip_mm=length,underhead_to_nut_exit_mm=nut_far,
            protrusion_mm=length-nut_far,minimum_two_threads_mm=2*pitch,note=note))

def hinge(k,st='H',bore=4,od=9,wd=1,friction_od=12,hub_r=7,clock=0,bearing_allowance=.20):
    """Axis Y. Rotor bearing seats are relieved 0.4 mm behind braking faces.
    Two off-axis M3 screws compress the brake without using the shaft as tie bolt.
    """
    A=rot(Y,clock)
    def fixed(s):return moved(s,A)
    def add(id,label,s,pr=True,orient=None,frame='fixed',role='structure',note=''):
        if frame=='fixed':s=fixed(s)
        return k.add(st+id,label,s,st,frame,pr,orient,role=role,note=note)
    def met(id,label,s,sku,frame='fixed',role='metal'):
        k.metal(st+id,label,fixed(s) if frame=='fixed' else s,st,frame,sku,role)
    end=5+wd; outer=end+5
    hub=cyl([0,-5,0],[0,5,0],hub_r)
    lever=box([-5,-4,-105],[5,4,-4])+cyl([0,-4,-100],[0,4,-100],5)
    rotor=hub+lever
    rotor=rotor-cyl([0,-6,0],[0,6,0],bore/2+.3)
    for sign in [-1,1]:
        rotor=rotor-cyl([0,sign*.6,0],[0,sign*5.2,0],(od+bearing_allowance)/2)
    for z in [-20,-50,-80]:
        rotor=rotor-cyl([0,-6,z],[0,6,z],1.7)-hexagon([0,-4.1,z],Y,5.8,2.7)
    rotor=rotor-cyl([0,-5,-100],[0,5,-100],1.8)
    for sign,id in [(-1,'01'),(1,'02')]:
        s=rotor^box([-120,0 if sign>0 else -6,-120],[120,6 if sign>0 else 0,30])
        add(id,('单轴' if st=='H' else '扭转')+'转子半体 '+str(sign),s,True,rot(X,90*sign),'rotor','rotor','合模平面朝下；轴承从外端面装入。')
    plate=cyl([0,5+wd,0],[0,outer,0],hub_r)+box([-22,5+wd,-9],[0,outer,9])
    plate=plate-cyl([0,4,0],[0,outer+1,0],bore/2+.4)
    for z in [-5,5]:plate=plate-cyl([-16,4,z],[-16,outer+1,z],1.8)
    add('03','浮动压板',plate,True,rot(X,90),note='交替拧两颗螺母，压板沿轴向移动。')
    for sign,id in [(-1,'04'),(1,'05')]:
        cheek=cyl([0,sign*13,0],[0,sign*25,0],8 if bore==4 else 9)
        cheek=cheek+box([-35,min(sign*13,sign*25),-18],[-26,max(sign*13,sign*25),18])
        for z in [-14,14]:
            cheek=cheek+beam([-29,sign*19,z],[-5,sign*19,z/2],3)
        cheek=cheek-cyl([0,sign*12.9,0],[0,sign*22.8,0],bore/2+.10)
        for z in [-12,12]:cheek=cheek-cyl([-30,sign*12,z],[-30,sign*26,z],2.3)
        # M3 radial shaft clamp; nut is inserted laterally, never threaded in PLA.
        screw_top=11 if bore==4 else 12
        # S2: preserve the screw/nut positions and the lateral insertion slot,
        # but widen the boss. The old 4 mm axial width left only 0.30 mm beside
        # the D3.4 screw clearance hole in the roof. A 10 mm width provides a
        # continuous roof and side walls around the hex pocket without growing
        # the bracket's overall bounds or entering the brake stack.
        cheek=cheek+box([-5,min(sign*13,sign*23),3],[5,max(sign*13,sign*23),screw_top])
        cheek=cheek-cyl([0,sign*18,0],[0,sign*18,15],1.7)
        # The nut's corners span 5.5/cos(30 deg) = 6.35 mm along Y in
        # this orientation. The lateral passage must clear corners, not just
        # the 5.5 mm across-flats dimension; retain 1.65 mm side walls.
        cheek=cheek-hexagon([0,sign*18,4.5],Z,5.8,4.2)-box([0,sign*18-3.35,4.5],[9,sign*18+3.35,8.7])
        if sign<0:
            # S2: a continuous 12 mm wide web from the rear bearing-bracket
            # face to the fixed brake face. The old stepped block touched the
            # rear rail over only 0.20 x 18 mm. Here the rail junction is
            # 12 x 12 mm; the web overlaps the rail by 2 mm and the plate by
            # 2 mm in X, through the plate's full 5 mm thickness. Keep Z within
            # +/-6 to clear the rear spacer tubes; stop at X=-20 to retain
            # access around the M3 preload heads and their 7 mm washers.
            cheek=cheek+moved(plate,rot(X,180))+box([-28,-25,-6],[-20,-end,6])
        add(id,'固定端支架' if sign<0 else '可拆端支架',cheek,True,rot(X,-90*sign),note='外端面朝下，盲轴孔开口朝上，减少孔内支撑。')
        met('shaft_clamp_'+str(sign),'M3×10 内六角螺钉',screw([0,sign*18,screw_top+1],-Z,3,10),'M3x10')
        met('shaft_clamp_nut_'+str(sign),'M3 尼龙锁紧螺母 AF5.5，高≤4',nut([0,sign*18,4.5],Z,3,5.5,4),'NL3')
        # Clamp screw tip nominal interference with smooth rod is intentional contact.
    for z,id in [(-12,'06'),(12,'07')]:
        add(id,'后桥隔柱 26 mm',tube([-30,-13,z],[-30,13,z],5,2.3),True,rot(X,90))
        met('tie_'+str(z),'M4×60 内六角螺钉',screw([-30,-27.4,z],Y,4,60),'M4x60')
        met('tie_w0_'+str(z),'M4 平垫圈 9×4.3×0.8',washer([-30,-27.4,z],Y,9,4.3,.8),'W4')
        met('tie_w1_'+str(z),'M4 平垫圈 9×4.3×0.8',washer([-30,25,z],Y,9,4.3,.8),'W4')
        met('tie_n_'+str(z),'M4 尼龙锁紧螺母 AF7，高≤5',nut([-30,25.8,z],Y,4,7,5),'NL4')
    # Scale ring itself is not rotated: zero always points toward -Z.
    scale=tube([0,-26.6,0],[0,-25,0],40,27)
    for z in [-12,12]:
        p=(A@np.array([-30,0,z,1]))[:3]
        scale=scale-cyl([p[0],-27,p[2]],[p[0],-24,p[2]],2.3)
    for deg in range(-180,180,5):
        tick=box([-.24,-26.7,-40.1],[.24,-26.05,-(35 if deg%15==0 else 37)])
        scale=scale-moved(tick,rot(Y,deg))
    k.add(st+'08','5°刻度环；纸质数字贴片另附',scale,st,'fixed',True,rot(X,-90))
    met('shaft',f'精磨光轴 D{bore}×45 mm',cyl([0,-22.5,0],[0,22.5,0],bore/2),f'SHAFT{bore}')
    for sign in [-1,1]:
        met('bearing_'+str(sign),f'{"684ZZ" if bore==4 else "MR126ZZ"} {bore}×{od}×4',tube([0,sign*.6,0],[0,sign*4.6,0],od/2,bore/2+.02),f'B{bore}',frame='rotor',role='bearing')
        met('friction_'+str(sign),f'M{bore} 大平垫圈 {friction_od}×{bore+.3 if bore==4 else 6.4}×{wd}',washer([0,sign*5,0],sign*Y,friction_od,bore+.3 if bore==4 else 6.4,wd),f'FR{bore}',role='friction')
    for z in [-5,5]:
        met('preload_'+str(z),'M3×30 内六角螺钉',screw([-16,-outer-.5,z],Y,3,30),'M3x30')
        for sign in [-1,1]:met('preload_w'+str(sign)+'_'+str(z),'M3 平垫圈 7×3.2×0.5',washer([-16,sign*outer,z],sign*Y,7,3.2,.5),'W3')
        met('preload_n'+str(z),'M3 尼龙锁紧螺母 AF5.5，高≤4',nut([-16,outer+.5,z],Y,3,5.5,4),'NL3')
    k.stack(st+'_preload_M3x30',30,2*outer+1+4,.5,'两侧各 0.5 mm 平垫；螺母高 4 mm。')
    k.stack(st+'_ties_M4x60',60,27.4+25.8+5,.7,'含 1.6 mm 刻度环。')
    for z in [-20,-50,-80]:
        met('rotor_bolt_'+str(z),'M3×12 内六角螺钉',screw([0,4.5,z],-Y,3,12),'M3x12',frame='rotor')
        met('rotor_w_'+str(z),'M3 平垫圈 7×3.2×0.5',washer([0,4,z],Y,7,3.2,.5),'W3',frame='rotor')
        for i,y in enumerate([-3.8,-6.2]):met('rotor_n'+str(i)+'_'+str(z),'M3 六角螺母 AF5.5×2.4',nut([0,y,z],Y,3,5.5,2.4),'N3',frame='rotor')
    k.stack(st+'_rotor_M3x12',12,4.5+6.2,.5,'第一螺母嵌槽，外侧第二螺母并紧。')

def wrist(k,liner_inner=11.05):
    def add(id,label,s,pr=True,orient=None,frame='fixed',role='structure',note=''):
        return k.add('W'+id,label,s,'W',frame,pr,orient,role=role,note=note)
    def met(id,label,s,sku,frame='fixed',role='metal',note=''):
        k.metal('W'+id,label,s,'W',frame,sku,role,note)
    ball=sph(11)+cyl([0,0,-9],[0,0,-23],3)+box([-3,-3,-31],[3,3,-22])
    ball=ball-cyl([0,0,-1.6],[0,0,1.6],4.1)
    for sign in [-1,1]:
        ball=ball-cyl([0,sign*5.3,0],[0,sign*9.5,0],1.15)
        # S1: captured METAL stack. Shoulder -> .5 washer -> plain M2 nut.
        # Nut and washer touch directly: no thin PLA annulus is in the clamp.
        # Split X=0 permits insertion; outer roof retains the washer after closure.
        ball=ball-hexagon([0,sign*7.3,0],sign*Y,4.35,1.8)
        ball=ball-cyl([0,sign*8.9,0],[0,sign*9.6,0],2.65)
        ball=ball-cyl([0,sign*9.5,0],[0,sign*12,0],1.4)
    for z in [-5.5,5.5]:
        ball=ball-cyl([-12,0,z],[12,0,z],1.15)-cyl([6.5,0,z],[12,0,z],2.1)-hexagon([-12,0,z],X,4.35,8.5)
    ball=ball-cyl([-4,0,-27],[4,0,-27],1.15)
    for sign,id in [(-1,'01'),(1,'02')]:
        half=ball^box([0 if sign>0 else -12,-12,-32],[12 if sign>0 else 0,12,12])
        add(id,'S1 D22 球体合模半件 '+str(sign),half,True,rot(Y,-90*sign),'ball','rotor','S1：X=0合模面朝下；捕获M2普通螺母及5×2.2×0.5钢垫圈；仅配D2.5导向件。')
    for z in [-5.5,5.5]:
        met('ball_bolt_'+str(z),'M2×14 内六角螺钉',screw([6.5,0,z],-X,2,14),'M2x14','ball')
        met('ball_nut_'+str(z),'M2 尼龙锁紧螺母 AF4，高≤3',nut([-6.5,0,z],X,2,4,3),'NL2','ball')
    k.stack('W_ball_M2x14',14,13,.4,'螺母最大高 3 mm；须完全通过尼龙圈。')
    # A printed dummy occupies the same chamber; replace it with the D8x3 magnet later.
    add('03','D8×3 磁铁占位块（机械测试先用此件）',cyl([0,0,-1.5],[0,0,1.5],4),True,None,'ball','magnet')
    for sign in [-1,1]:
        pin=cyl([0,sign*9.5,0],[0,sign*15.5,0],1.25)+cyl([0,sign*5.5,0],[0,sign*9.5,0],1)
        pin=pin+cyl([0,sign*15.5,0],[0,sign*17.9,0],2.4)-hexagon([0,sign*17.91,0],-sign*Y,2,1.4)
        met('guide_'+str(sign),'M2 / D2.5×6 肩螺钉，螺纹长4，头D4.8×2.4',pin,'GUIDE_M2_D2P5_L6','ball',note='S1按用户天卓五金图片标称尺寸适配：304，M2×0.4，内六角2；须到货试配。不是原D3特殊规格。')
        met('guide_w_'+str(sign),'M2 平垫圈 5×2.2×0.5',washer([0,sign*9,0],sign*Y,5,2.2,.5),'W2','ball')
        met('guide_nut_'+str(sign),'M2 普通六角螺母 AF4×1.6',nut([0,sign*7.4,0],sign*Y,2,4,1.6),'N2','ball',note='S1金属垫圈直接靠普通螺母；低强度可拆金属螺纹锁固仍必需。禁止换成3mm高尼龙螺母。')
    k.stack('W_guides_M2_thread4',4,.5+1.6,.4,'S1仅夹金属：0.5钢垫圈+1.6普通螺母，露出1.9；塑料捕获该组件，不作为肩部小环承压座。')
    slot=union(moved(cyl([0,sign*9.8,0],[0,sign*18,0],1.47),rot(X,d)) for sign in [-1,1] for d in np.linspace(-23,33,57))
    for sign,ids in [(-1,('04','06')),(1,('05','07'))]:
        side=box([-22,9.6 if sign>0 else -22,-9.3],[22,22 if sign>0 else -9.6,28])
        liner=((sph(11.75)-sph(liner_inner))^side)-slot
        cup=((sph(14)-sph(11.75))^side)-slot
        pockets=[]
        for xx in [-8.5,8.5]:
            sx=1 if xx>0 else -1
            root=beam([sx*5.2,sign*10.1,4],[xx,sign*12.8,4],.75)
            pad=box([xx-2,min(sign*12.2,sign*13.4),-4.2],[xx+2,max(sign*12.2,sign*13.4),4.2])
            tab=root+pad
            tab=tab-cyl([xx,sign*10,0],[xx,sign*18,0],1.15)-cyl([xx,sign*9,0],[xx,sign*12.2,0],2.6)
            liner=liner+tab
            boss=box([xx-2.8,min(sign*11.6,sign*18.3),-5.2],[xx+2.8,max(sign*11.6,sign*18.3),5.2])
            # S3: open the retaining-pad pocket toward the ball, so the rigid
            # liner can actually be inserted before closing the two cups.
            # S2's round tool recess left a lip trapping the 8.4 mm-tall pad.
            # Sweep the root clearance inward as well; retain the outer floor
            # and captive-nut seat, which carry the M2 retaining screw load.
            root_clear=beam([sx*5.2,sign*10.1,4],[xx,sign*12.8,4],.95)
            pocket=md.Manifold.batch_hull([root_clear,root_clear.translate([0,-sign*4,0])])+box([xx-2.2,min(sign*8,sign*13.55),-4.4],[xx+2.2,max(sign*8,sign*13.55),4.4])
            boss=boss-pocket
            boss=boss-cyl([xx,sign*10,0],[xx,sign*20,0],1.15)-hexagon([xx,sign*14.8,0],sign*Y,4.35,4)
            # Open inward head/tool recess, exposing the retaining tab and washer.
            boss=boss-cyl([xx,sign*9,0],[xx,sign*12.25,0],2.6)
            cup=cup+boss
            pockets.extend([pocket,cyl([xx,sign*9,0],[xx,sign*12.25,0],2.6),cyl([xx,sign*10,0],[xx,sign*19,0],1.15)])
            met('liner_screw_'+str(sign)+'_'+str(xx),'M2×8 内六角螺钉',screw([xx,sign*11.9,0],sign*Y,2,8),'M2x8')
            met('liner_w_'+str(sign)+'_'+str(xx),'M2 平垫圈 5×2.2×0.3',washer([xx,sign*11.9,0],sign*Y,5,2.2,.3),'W2')
            met('liner_n_'+str(sign)+'_'+str(xx),'M2 尼龙锁紧螺母 AF4，高≤3',nut([xx,sign*14.8,0],sign*Y,2,4,3),'NL2')
        for xx in [-8,8]:
            cup=cup+beam([xx*.65,sign*11.8,3],[xx,sign*12.5,19],2.1)
            cup=cup+box([xx-3.6,min(sign*10.5,sign*14.5),15.4],[xx+3.6,max(sign*10.5,sign*14.5),22.6])
            cup=cup-cyl([xx,sign*9,19],[xx,sign*16,19],1.8)
        cup=cup-slot-sph(11.75)-union(pockets)
        add(ids[0],'S1 球面衬片 '+str(sign),liner^side,True,rot(X,90*sign),role='friction',note='S1槽宽2.94，仅配D2.5导向件；内R11.05 / 外R11.75；先试配。')
        add(ids[1],'S3 开口式衬片座球窝及预紧耳 '+str(sign),cup,True,rot(X,90*sign),note='S3衬片固定耳入口朝球心开放；先装衬片及M2固定件，再包住球；保留S1槽宽2.94和D2.5导向件。')
    k.stack('W_liner_M2x8',8,17.8-11.9,.4,'0.3 mm 垫片；球窝承压底厚1.25 mm。')
    bridge=box([-12,-8,16],[12,8,26])+cyl([0,0,25],[0,0,36],7)+box([-30,-18,35],[30,18,41])
    for xx in [-8,8]:bridge=bridge-cyl([xx,-9,19],[xx,9,19],1.8)
    for xx in [-20,20]:bridge=bridge-cyl([xx,0,34],[xx,0,42],2.3)
    add('08','腕部固定桥与夹持底座',bridge,True,rot(X,180))
    for xx in [-8,8]:
        met('preload_'+str(xx),'M3×35 内六角螺钉',screw([xx,-15,19],Y,3,35),'M3x35')
        for sign in [-1,1]:met('preload_w'+str(sign)+'_'+str(xx),'M3 平垫圈 7×3.2×0.5',washer([xx,sign*14.5,19],sign*Y,7,3.2,.5),'W3')
        met('preload_n'+str(xx),'M3 尼龙锁紧螺母 AF5.5，高≤4',nut([xx,15,19],Y,3,5.5,4),'NL3')
    k.stack('W_preload_M3x35',35,34,.5,'左右预紧耳内侧与固定桥各有2.5 mm调节空间。')
    lever=box([-6,-6,-35],[6,6,-21.8])+box([-5,-4,-105],[5,4,-30])
    lever=lever-box([-3.2,-3.2,-31.2],[3.2,3.2,-21.7])-cyl([-8,0,-27],[8,0,-27],1.15)-cyl([0,-5,-100],[0,5,-100],1.8)
    add('09','腕部100 mm加载杆',lever,True,rot(X,90),'ball','rotor')
    met('lever_screw','M2×20 内六角螺钉',screw([6.3,0,-27],-X,2,20),'M2x20','ball')
    for sign in [-1,1]:met('lever_w'+str(sign),'M2 平垫圈 5×2.2×0.3',washer([sign*6,0,-27],sign*X,5,2.2,.3),'W2','ball')
    met('lever_n','M2 尼龙锁紧螺母 AF4，高≤3',nut([-9.3,0,-27],X,2,4,3),'NL2','ball')
    k.stack('W_lever_M2x20',20,15.6,.4,'方键承扭，M2防脱；外置螺母避免挖薄方键。')

def coupons(k):
    # Single flat plate with graduated bearing seats, rod holes and nut pockets.
    s=box([0,0,0],[100,46,5])
    for row,(d,ys) in enumerate([(9,12),(12,32)]):
        for i,extra in enumerate([.1,.2,.3]):s=s-cyl([12+18*i,ys,1],[12+18*i,ys,6],(d+extra)/2)
    for i,d in enumerate([4.1,4.2,4.3,6.1,6.2,6.3]):s=s-cyl([69+(i%3)*11,9+(i//3)*12,-1],[69+(i%3)*11,9+(i//3)*12,6],d/2)
    for x,af in [(70,4.25),(82,4.35),(94,4.45)]:s=s-hexagon([x,36,1],Z,af,5)
    k.add('C01','孔与M2螺母配合阶梯试片',s,'C','fixed',True)

def build():
    k=Kit();hinge(k);hinge(k,'R',6,12,1.6,18,10,90);wrist(k);coupons(k);return k

def mesh(s):
    m=s.to_mesh();return trimesh.Trimesh(np.array(m.vert_properties)[:,:3],np.array(m.tri_verts),process=False)
def frames(st,q=0,dev=0):
    if st in ['H','R']:return {'fixed':np.eye(4),'rotor':rot(Y,-q if st=='H' else q)}
    return {'fixed':np.eye(4),'ball':rot(X,dev)@rot(Y,q)}

def export(k):
    OUT.mkdir(parents=True,exist_ok=True);(OUT/'stl_print').mkdir(exist_ok=True);(OUT/'verification').mkdir(exist_ok=True)
    rows=[];arrays={};scene=trimesh.Scene();locations={'H':[-85,0,0],'R':[15,0,0],'W':[115,0,0],'C':[-130,70,0]}
    colors={'structure':[134,185,176,255],'rotor':[231,159,60,255],'metal':[154,166,181,255],'bearing':[62,78,90,255],'friction':[141,86,55,255],'magnet':[201,68,76,255]}
    for i,p in enumerate(k.parts):
        m=mesh(p['s']);arrays[f'v{i}']=m.vertices;arrays[f'f{i}']=m.faces
        row={key:value for key,value in p.items() if key!='s'}
        row.update(index=i,volume_mm3=float(m.volume),bounds_mm=m.bounds.tolist(),watertight=bool(m.is_watertight),components=len(p['s'].decompose()))
        if p['printable']:
            M=k.prints[p['id']]['orientation'].copy();pm=m.copy();pm.apply_transform(M)
            shift=-pm.bounds[0];M[:3,3]+=shift;pm.apply_translation(shift)
            file=OUT/'stl_print'/(p['id']+'.stl');pm.export(file)
            reread=trimesh.load(file,process=True)
            row.update(print_matrix=M.tolist(),print_bounds_mm=pm.bounds.tolist(),stl_sha256=sha(file),stl=file.relative_to(OUT).as_posix(),print_qty=k.prints[p['id']]['qty'],stl_roundtrip_watertight=bool(reread.is_watertight))
        display=m.copy();display.apply_scale(.001);display.units='m';display.visual.vertex_colors=colors[p['role']]
        scene.add_geometry(display,node_name=p['id'],geom_name=p['id'],transform=a.T(np.array(locations[p['station']])*.001))
        rows.append(row)
    np.savez_compressed(OUT/'assembly_meshes.npz',**arrays);scene.export(OUT/'O24C_T1_kit.glb')
    put(OUT/'assembly.json',dict(revision=REVISION,units='mm',parts=rows,station_locations=locations))
    put(OUT/'verification/fastener_stacks.json',dict(passed=all(r['protrusion_mm']>=r['minimum_two_threads_mm']-1e-8 for r in k.stacks),rows=k.stacks,
        note='Nominal maximum nut heights; inspect actual bolts fully traverse nylon insert. Radial set screws are contact adjustments, not through-stacks.'))
    bom=[dict(sku=sku,**{key:(sorted(val) if isinstance(val,set) else val) for key,val in r.items()}) for sku,r in k.bom.items()]
    put(OUT/'BOM.json',bom)
    with (OUT/'BOM.csv').open('w',encoding='utf-8-sig',newline='') as f:
        w=csv.writer(f);w.writerow(['编号','规格','整套数量','站位','备注'])
        for r in bom:w.writerow([r['sku'],r['spec'],r['qty'],','.join(r['stations']),r['notes']])
    put(OUT/'verification/geometry.json',dict(passed=all(r['watertight'] and r['components']==1 and r.get('stl_roundtrip_watertight',True) for r in rows),parts=len(rows),printed_parts=sum(p['printable'] for p in rows),geometry_sha256=sha(OUT/'assembly_meshes.npz'),rows=[{key:r[key] for key in ['id','volume_mm3','components','watertight']} for r in rows]))
    refs=[H/'cad/revO24C/compact_arm.py',H/'bench/revO24C/assembly_meshes.npz',H/'bench/revO24C/config.json']
    put(OUT/'reference_baseline.json',{str(p.relative_to(ROOT)):sha(p) for p in refs})
    print(json.dumps(dict(parts=len(rows),printed=sum(p['printable'] for p in rows),disconnected=[r['id'] for r in rows if r['components']!=1],stacks_pass=all(r['protrusion_mm']>=r['minimum_two_threads_mm']-1e-8 for r in k.stacks)),ensure_ascii=False),flush=True)

def export_fit_options():
    rows=[];folder=OUT/'stl_fit_options';folder.mkdir(exist_ok=True)
    for allowance in [.10,.30]:
        k=Kit();hinge(k,bearing_allowance=allowance);hinge(k,'R',6,12,1.6,18,10,90,bearing_allowance=allowance)
        for id in ['H01','H02','R01','R02']:
            p=k.prints[id];m=mesh(p['s']);m.apply_transform(p['orientation']);m.apply_translation(-m.bounds[0]);file=folder/f'{id}_bearing_plus_{allowance:.2f}.stl';m.export(file)
            rows.append(dict(id=file.stem,replaces=id,stl=file.relative_to(OUT).as_posix(),stl_sha256=sha(file),watertight=bool(trimesh.load(file,process=True).is_watertight),components=len(p['s'].decompose()),bounds_mm=m.bounds.tolist(),purpose='孔径比轴承外径大 '+str(allowance)+' mm；一对半体采用同一档。'))
    # Cup OD stays unchanged. Thin alternatives are labelled separately and are not
    # used for the main reported wear baseline unless chosen and recorded.
    for radius in [11.15,11.25]:
        k=Kit();wrist(k,liner_inner=radius)
        for id in ['W04','W05']:
            p=k.prints[id];m=mesh(p['s']);m.apply_transform(p['orientation']);m.apply_translation(-m.bounds[0]);file=folder/f'{id}_inner_R{radius:.2f}.stl';m.export(file)
            rows.append(dict(id=file.stem,replaces=id,stl=file.relative_to(OUT).as_posix(),stl_sha256=sha(file),watertight=bool(trimesh.load(file,process=True).is_watertight),components=len(p['s'].decompose()),bounds_mm=m.bounds.tolist(),purpose=f'外R11.75不变；内R{radius}，壁厚{11.75-radius:.2f} mm；配对换件并记录。'))
    put(OUT/'fit_options.json',dict(passed=all(r['watertight'] and r['components']==1 for r in rows),parts=rows))

if __name__=='__main__':export(build());export_fit_options()
