"""One-component assembly lessons, using the exported production meshes.

Offsets are in assembly millimetres. Every addition has one real component ID;
subassembly moves retain that identity. No duplicate display-only hardware.
"""
from kit import *
import shutil, collections
from tutorial_orientation import annotate, EDITION

class CatalogKit(Kit):
    def metal(self,id,label,s,station,frame='fixed',sku=None,role='metal',note=''):
        super().metal(id,label,s,station,frame,sku,role,note)
        self.parts[-1]['sku']=sku

def plus(a,b):return (np.array(a)+np.array(b)).round(8).tolist()
ZERO=[0,0,0]
def pose_matrix(p):
    return a.T(p['after'])@a.T(p['pivot'])@rot(p['axis'],p['angle'])@a.T(-np.array(p['pivot']))@a.T(p['before'])

def replay_steps(L):
    """Rebuild deterministic snapshots after assembly-order edits."""
    state={};matrices={}
    for n,s in enumerate(L.steps,1):
        s['n']=n;s['before']={id:p[:] for id,p in state.items()};s['beforeM']=dict(matrices)
        for id,path in s['paths'].items():state[id]=path[-1];matrices[id]=a.T(path[-1]).tolist()
        for id,path in s.get('posePaths',{}).items():
            M=pose_matrix(path[-1]);state[id]=M[:3,3].round(8).tolist();matrices[id]=M.tolist()
        s['after']={id:p[:] for id,p in state.items()};s['afterM']=dict(matrices)
    L.state=state
NAMES={'01':'转子后半体','02':'转子前半体','03':'浮动压板','04':'一体固定支架（S2）','05':'可拆支架（S2）','06':'后桥隔柱 A','07':'后桥隔柱 B','08':'刻度环'}
WNAMES={'W01':'球后半体（负 X）','W02':'球前半体（正 X）','W03':'磁铁占位块','W04':'后侧球面衬片','W05':'前侧球面衬片','W06':'后侧球窝（S3 开口座）','W07':'前侧球窝（S3 开口座）','W08':'固定桥与夹持底座','W09':'100 mm 加载杆'}

class Lesson:
    def __init__(self,station):self.station=station;self.steps=[];self.state={};self.chapter='准备';self.added=[]
    def step(self,title,text,kind='check',ids=None,paths=None,tool='手动检查',detail='',camera=None):
        ids=ids or [];paths=paths or {}
        before={k:v[:] for k,v in self.state.items()}
        for id,path in paths.items():self.state[id]=path[-1][:]
        self.steps.append(dict(n=len(self.steps)+1,chapter=self.chapter,title=title,text=text,kind=kind,ids=ids,paths=paths,before=before,after={k:v[:] for k,v in self.state.items()},tool=tool,detail=detail,camera=camera))
    def add(self,id,text,direction=ZERO,end=ZERO,title=None,tool=None,detail='',path=None):
        assert id not in self.added,id
        self.added.append(id)
        self.step(title or ('装入 '+id),text,'add',[id],{id:path or [plus(end,direction),end]},tool or CATALOG[id]['tool'],detail)
    def move(self,ids,offsets,title,text,detail=''):
        paths={id:[self.state[id]]+[plus(self.state[id],p) for p in offsets] for id in ids}
        self.step(title,text,'move',ids,paths,detail=detail)
    def check(self,title,text,ids=None,detail=''):self.step(title,text,ids=ids,detail=detail)

def hinge_lesson(st):
    L=Lesson(st);L.chapter='01 · 支架与锁轴座'
    A=rot(Y,90 if st=='R' else 0)[:3,:3]
    def v(x,y,z):return (A@np.array([x,y,z])).round(8).tolist()
    def add(s,*args,**kwargs):return L.add(st+s,*args,**kwargs)
    b='684ZZ · 内径 4 / 外径 9 / 宽 4 mm' if st=='H' else 'MR126ZZ · 内径 6 / 外径 12 / 宽 4 mm'
    L.check('先认清样件与观察方向',f'{st} 站独立组装。每一步只新增一件，橙色为本步零件，虚线箭头表示装入方向。准备 S2 的 {st}04/{st}05，轴承采用 {b}。前侧是可拆支架一端，后侧是刻度环一端。',detail='螺钉长度均指头下长度；垫圈尺寸按外径 × 内径 × 厚度。先清除支撑，检查裂纹、分层与孔内毛刺。')
    add('04','将一体固定支架放稳；带摩擦压板的一侧朝向关节中间。',v(0,-30,0),title='放置 '+st+'04 · 一体固定支架')
    add('shaft_clamp_nut_-1','从锁轴座的开放侧槽送入 M3 尼龙锁紧螺母，使孔对准径向螺钉孔。尼龙端朝光轴方向。',v(12,0,0),title='固定支架：放入锁轴螺母',detail='S2 侧槽宽 6.7 mm。用镊子轻推，不能用螺钉把卡住的螺母强拉进槽。')
    add('shaft_clamp_-1','从锁轴座外侧旋入 M3×10，暂时回退，端部不能伸进光轴孔。',v(0,0,18),end=v(0,0,2),title='固定支架：预装压轴螺钉',detail='动画停在比最终接触位置退后 2 mm 的示意位置；实物以轴孔畅通为准。螺钉头不要求贴住塑料。')
    L.chapter='02 · 在旁边组装转子'
    park=[-85,0,0]
    add('01','转子后半体放在支架旁边，合模平面朝前。三个六角槽朝外。',[-20,0,0],park)
    add('bearing_-1','从外端面把轴承装入后半体。只压外圈，平行压入，不敲内圈。',[0,-14,0],park,title='转子后侧：装入轴承')
    for z in [-20,-50,-80]:
        add('rotor_n0_'+str(z),f'在加载杆第 {[-20,-50,-80].index(z)+1} 个六角槽内放入一颗 M3 普通螺母。外侧稍后再加第二颗并紧。',[0,-14,0],park,title='转子后半体：埋入普通螺母')
    front=plus(park,[0,22,0])
    add('02','把前半体放在对应前方，先不要合拢。合模平面朝后。',[20,0,0],front)
    add('bearing_1','从前半体外端面压入第二只同型号轴承。',[0,14,0],front,title='转子前侧：装入轴承')
    L.check('测量两个轴承的凹入量','两侧都测量摩擦平面到轴承端面的距离：名义 0.40 mm，实物均须 ≥0.20 mm。轴承内圈应顺畅转动。',[st+'bearing_-1',st+'bearing_1'],detail='不满足时先处理座孔或配合档位；不能靠后面的预紧螺钉强压轴承。')
    L.move([st+'02',st+'bearing_1'],[[0,-22,0]],'合拢两个转子半体','对齐三个螺钉孔，两个合模平面完全贴合。不要夹住毛刺或杂物。')
    for i,z in enumerate([-20,-50,-80],1):
        add('rotor_w_'+str(z),f'第 {i} 个连接孔：从前半体外侧放上 M3 平垫圈。',[0,14,0],park,title=f'转子连接 {i}/3 · 平垫圈')
        add('rotor_bolt_'+str(z),f'第 {i} 个连接孔：M3×12 从前侧穿入并旋入已埋入的普通螺母。先轻合紧。',[0,20,0],park,title=f'转子连接 {i}/3 · M3×12')
        add('rotor_n1_'+str(z),f'第 {i} 个连接孔：在后侧露出的螺纹上加第二颗 M3 普通螺母，与槽内第一颗并紧。',[0,-14,0],park,title=f'转子连接 {i}/3 · 外侧并紧螺母',detail='固定螺钉头后并紧；不要继续挤压塑料来代替双螺母锁固。')
    rotor=[id for id in L.state if CATALOG[id]['frame']=='rotor']
    L.check('确认转子合缝与轴承','三个连接点已轻合紧并锁固；两个半体不张口，两个轴承内圈都能转动。',rotor)
    L.chapter='03 · 套上光轴与摩擦组件'
    add('shaft','从前方把光轴送入固定支架的盲孔，确认轴端无毛刺。径向压轴螺钉仍保持回退。',[0,65,0],title='插入光轴')
    friction='12 × 4.3 × 1 mm' if st=='H' else '18 × 6.4 × 1.5 mm（也允许 1.6 mm）'
    add('friction_-1',f'从光轴开放端套入第一片摩擦垫圈（{friction}），靠到固定压板。平滑面朝转子。',[0,42,0],title='后侧摩擦垫圈',detail='R 的三维基准显示 1.6 mm；若用 1.5 mm，两片必须同厚，最终靠预紧消除新增间隙。' if st=='R' else '去除冲压毛刺，保持接触面干燥、平整。')
    L.move(rotor,[[0,65,0],[85,65,0]],'把转子组件移到轴端前方','先整体绕到开放轴端外，再对准轴承内孔。此步移动的是已装好的转子组件。')
    L.move(rotor,[[0,-65,0]],'沿光轴滑入转子组件','让光轴依次穿过两只轴承内圈。轻推组件到后侧垫圈旁，不通过加载杆硬扳。')
    add('friction_1',f'套入第二片相同规格的摩擦垫圈（{friction}），平滑面朝转子。',[0,40,0],title='前侧摩擦垫圈')
    add('03','对准光轴和两个预紧孔，套入浮动压板。它沿轴向可移动，用于调整摩擦力。',[0,38,0])
    for i,z in enumerate([-5,5],1):
        add('preload_w-1_'+str(z),'从固定支架一侧放上螺钉头下的 M3 平垫圈。',[0,-20,0],title=f'预紧连接 {i}/2 · 后侧垫圈')
        add('preload_'+str(z),'M3×30 从固定压板侧穿入，穿过浮动压板的对应孔。',[0,-38,0],title=f'预紧连接 {i}/2 · M3×30')
        add('preload_w1_'+str(z),'在浮动压板外侧套上 M3 平垫圈。',[0,18,0],title=f'预紧连接 {i}/2 · 前侧垫圈')
        add('preload_n'+str(z),'旋上 M3 尼龙锁紧螺母，尼龙端朝外。这里只消除明显空隙，暂不调整目标持姿力。',[0,18,0],title=f'预紧连接 {i}/2 · 锁紧螺母',detail='螺钉要穿过尼龙圈；用另一把扳手固定螺钉头。')
    L.chapter='04 · 合拢后桥与支架'
    for n in ['06','07']:add(n,'对准固定支架后桥的连接孔，放入隔柱。两根隔柱尺寸相同，可互换。',[0,40,0],detail='H06 / H07 / R06 / R07 都是外径 10、内径 4.6、长 26 mm 的隔柱。')
    add('05','可拆支架先放在光轴前方，留出操作空间。',[25,0,0],[0,45,0])
    add('shaft_clamp_nut_1','从可拆支架侧槽放入 M3 尼龙锁紧螺母，孔朝径向螺钉；尼龙端朝轴孔。',v(12,0,0),[0,45,0],title='可拆支架：放入锁轴螺母')
    add('shaft_clamp_1','旋入 M3×10，暂不让端部进入光轴孔。',v(0,0,18),plus([0,45,0],v(0,0,2)),title='可拆支架：预装压轴螺钉')
    L.move([st+'05',st+'shaft_clamp_nut_1',st+'shaft_clamp_1'],[[0,-45,0]],'合上可拆支架','同时对准光轴盲孔和两根隔柱；轻推就位。不能靠两颗长螺钉硬拉错位的支架。')
    add('08','刻度环贴在固定支架后侧，对齐后桥的两个连接孔。',[0,-20,0])
    for i,z in enumerate([-12,12],1):
        add('tie_w0_'+str(z),'刻度环外侧的螺钉头下，放一片 M4 平垫圈。',[0,-18,0],title=f'后桥连接 {i}/2 · 头下垫圈')
        add('tie_'+str(z),'M4×60 从刻度环一侧穿过固定支架、隔柱和可拆支架。',[0,-65,0],title=f'后桥连接 {i}/2 · M4×60')
        add('tie_w1_'+str(z),'在可拆支架外侧放上 M4 平垫圈。',[0,18,0],title=f'后桥连接 {i}/2 · 外侧垫圈')
        add('tie_n_'+str(z),'旋上 M4 尼龙锁紧螺母，尼龙端朝外。两个连接点交替合紧，框架不晃动即可。',[0,18,0],title=f'后桥连接 {i}/2 · M4 锁紧螺母')
    L.chapter='05 · 锁轴、预紧与检查'
    for sign in [-1,1]:
        id=st+'shaft_clamp_'+str(sign)
        L.move([id],[v(0,0,-2)],'让压轴螺钉接触光轴','框架紧固后，将这一颗 M3×10 缓慢拧到光轴不转动、不松摆。另一侧下一步单独调整。',detail='动画只表示从退让位置到名义接触位置。实际以端部接触光轴为准，不把螺钉头拧到贴住塑料。')
    L.check('先做极小预紧的顺畅检查','确认轴固定、支架不晃，再轻转加载杆。两只轴承不能被大垫圈压住；若卡顿，先回查凹入量和轴承配合。',[st+'03',st+'friction_-1',st+'friction_1'])
    L.check('交替微调两颗预紧螺母','固定螺钉头，每次只转一颗螺母，最多 1/12 圈；再以相同小幅度调整另一颗。随时检查压板平行。',[st+'preload_n-5',st+'preload_n5'],detail='1/12 圈即 30°，不是指定的最终紧固扭矩。持姿力需要按测试手册实测，不能凭动画的到位位置确定。')
    L.check('作记号并记录力矩','在螺母、螺钉头和打印件旁作对齐记号。记录起动力矩、静置持姿及磨损；完成后检查裂纹和螺纹是否松动。',detail=('H 肩工况目标 0.13 N·m，H 肘工况目标 0.04 N·m。' if st=='H' else 'R 扭转工况目标 0.02 N·m。')+'这些是待验证目标，不是实测性能。刻度贴纸按 100% 打印并核对 50 mm 校验线。')
    L.step('名义活动范围演示','这段只演示设计目标角度。实物先在极小预紧下逐步测试；遇到卡点立即停止并记录。','rom',[st+'01',st+'02'],tool='手动慢摆 + 角度记录',detail='H 肩 −45°～165°，H 肘 0°～145°；本动画演示肩工况。' if st=='H' else 'R 目标 −85°～80°；轴线穿过转子中心。')
    # Preload bolts need a small tilt past the S2 diagonal brace. Keep the
    # floating plate off until both bolts are straight; the washer is held near
    # the fixed plate so its larger OD need not pass axially through the brace.
    altered=[];skip={st+'preload_'+str(z) for z in [-5,5]}|{st+'preload_w-1_'+str(z) for z in [-5,5]}
    for s in L.steps:
        if s['kind']=='add' and s['ids'][0] in skip:continue
        if s['kind']=='add' and s['ids']==[st+'03']:
            for i,z in enumerate([-5,5],1):
                wid=st+'preload_w-1_'+str(z);bid=st+'preload_'+str(z);pivot=v(-16,-8.5-(.6 if st=='R' else 0),z)
                def pose(d,angle,side=ZERO):return dict(pivot=pivot,axis=v(1,0,0),before=[0,-d,0],after=side,angle=angle)
                angle=float(np.sign(z)*6)
                def special(title,text,kind,ids,paths,tool,detail=''):
                    return dict(chapter='03 · 套轴与预装预紧螺钉',title=title,text=text,kind=kind,ids=ids,paths={},posePaths=paths,tool=tool,detail=detail,camera=None)
                altered.append(special(f'预紧连接 {i}/2 · 从侧边放入垫圈','先不要装浮动压板。从斜撑与固定压板之间的侧边放入 M3 平垫圈，稍向中心倾斜，暂时用镊子扶住。','add',[wid],{wid:[pose(.9,angle,v(0,0,np.sign(z)*22)),pose(.9,angle)]},CATALOG[wid]['tool'],'垫圈先留在压板后面，不能从斜撑后方直推。此处约 6° 的倾斜只用于让螺钉绕过斜撑，不是预紧角度。'))
                altered.append(special(f'预紧连接 {i}/2 · 倾斜穿入 M3×30','M3×30 略向中心倾斜，穿过手扶的垫圈与固定压板孔；螺钉头绕过斜撑后，暂不完全贴合。','add',[bid],{bid:[pose(38,angle),pose(2,angle)]},CATALOG[bid]['tool'],'浮动压板尚未安装，孔位保留了摆正空间。手动轻送，不能用扳手顶着孔壁硬拧。'))
                altered.append(special('摆正螺钉和垫圈','螺钉头越过斜撑后，把螺钉与垫圈一起摆正，使螺钉平行于光轴。','move',[bid,wid],{bid:[pose(2,angle),pose(2,0)],wid:[pose(.9,angle),pose(.9,0)]},'手动调整 / 镊子'))
                altered.append(special('垫圈贴到固定压板','沿螺钉将垫圈轻推到固定压板背面，保持平贴。','move',[wid],{wid:[pose(.9,0),pose(0,0)]},'镊子'))
                altered.append(special('螺钉头靠到垫圈','把螺钉继续送入，让螺钉头轻靠垫圈。前侧此时还没有螺母。','move',[bid],{bid:[pose(2,0),pose(0,0)]},'手动送入'))
            s['text']='同时对准光轴和两颗已摆正的 M3×30 螺钉，套入浮动压板。它沿轴向可移动，用于调整摩擦力。'
        altered.append(s)
    L.steps=altered;replay_steps(L)
    return L

def wrist_lesson():
    L=Lesson('W')
    def add(s,*args,**kwargs):return L.add('W'+s,*args,**kwargs)
    L.chapter='01 · 球半体与内置五金'
    L.check('腕部先检查版本和肩螺钉','W06/W07 使用 S3 开口式衬片座。其他腕部打印件沿用 S1/S2 的 D2.5 导向接口。取两套肩螺钉、0.5 mm 钢垫圈和普通 M2 螺母，先在球外干装试配。',detail='肩 D2.5×6，M2×0.4 螺纹长 4，头 D4.8×2.4，2 mm 内六角。肩端压在 0.5 mm 钢垫圈上，垫圈直接贴 1.6 mm 普通螺母；金属叠厚 2.1 mm，名义穿出 1.9 mm。这里不能用高 3 mm 的尼龙螺母。')
    add('01','球后半体放稳，开口合模面朝正 X。先在这个开放面装入内部五金。',[-18,0,0])
    for sign,side in [(-1,'后侧'),(1,'前侧')]:
        add('guide_nut_'+str(sign),f'由球半体的开放合模面，把{side}的普通 M2 螺母放入六角捕获槽。',[14,0,0],title=side+'导向座 · 普通 M2 螺母',detail='AF4 × 高 1.6 mm；不是尼龙锁紧螺母。不把它从外侧小导向孔硬塞进去。')
        add('guide_w_'+str(sign),f'同样由开放合模面装入{side}的 0.5 mm 钢平垫圈，使其直接贴着普通螺母。',[14,0,0],title=side+'导向座 · 0.5 mm 钢垫圈',detail='导向座这两片必须厚 0.5 mm。塑料不能夹在螺母与钢垫圈之间。')
    for z in [-5.5,5.5]:
        add('ball_nut_'+str(z),'从球后半体外侧的六角孔放入 M2 尼龙锁紧螺母。尼龙端朝负 X 外侧，另一端朝球内部。',[-14,0,0],title='球合拢连接 · 放入尼龙螺母',detail='这两颗与导向座的普通 M2 螺母用途不同，请勿混用。')
    add('03','把打印的磁铁占位块放进球内圆形腔。只做机械试验时不需要购买磁铁。',[14,0,0],detail='占位块 D8×3 mm；将来可换同尺寸磁铁。应完全入腔，不能把两个半体顶开。')
    add('02','保持所有内部五金留在槽内，合上前半体，对准两个连接孔。',[18,0,0])
    for z in [-5.5,5.5]:
        add('ball_bolt_'+str(z),'M2×14 从前半体的圆形沉孔穿入，旋入对面的尼龙锁紧螺母。两颗交替轻合紧。',[18,0,0],title='合拢球体 · M2×14',detail='这里不用额外平垫圈；不要因过拧使球面接缝变形。')
    L.check('检查球体和捕获式导向座','球合缝应闭合；占位块不顶住半体。内部普通螺母和钢垫圈不能掉出，且不被塑料挤压成承载叠层。',['W01','W02'],detail='钢垫圈与螺母金属接触，捕获槽总轴向游隙名义 0.20 mm。肩螺钉暂不装，等球窝包住球后再装。')
    L.chapter='02 · 单独装好两侧衬片与球窝'
    cupgroups=[]
    for sign,lin,cup,side in [(-1,'04','06','后侧'),(1,'05','07','前侧')]:
        parked=[0,sign*42,0];group=[]
        add(cup,'把 S3 球窝放到球体旁边，开放的衬片固定耳入口朝向球心。',[25,0,0],parked,title=f'{side} · 放置 W{cup} 球窝');group.append('W'+cup)
        add(lin,'从球心一侧将衬片平行送入球窝；两个固定耳同时进入开放槽，曲面自然贴合。',[0,-sign*13,0],parked,title=f'{side} · 装入 W{lin} 衬片',detail='S3 已打开原本挡住固定耳的入口。无需掰弯固定耳或强行卡入；若仍有阻力，停下检查支撑残留。');group.append('W'+lin)
        for i,xx in enumerate([-8.5,8.5],1):
            suffix=str(sign)+'_'+str(xx)
            add('liner_n_'+suffix,'从球窝外侧六角槽放入 M2 尼龙锁紧螺母，尼龙端朝外侧。',[0,sign*14,0],parked,title=f'{side}衬片固定 {i}/2 · 螺母');group.append('Wliner_n_'+suffix)
            add('liner_w_'+suffix,'从球心一侧稍向外绕过衬片边缘，再对准固定耳孔，平推垫圈到螺钉头侧。',end=parked,path=[plus(parked,p) for p in [[0,-sign*14,0],[np.sign(xx)*1.5,-sign*3,0],[0,-sign*1,0],[0,0,0]]],title=f'{side}衬片固定 {i}/2 · 垫圈',detail='可用 5×2.2×0.5 mm；动画保留 0.3 mm 名义模型，采购替代厚度已另行核对。不要让垫圈刮擦球面衬片。');group.append('Wliner_w_'+suffix)
            add('liner_screw_'+suffix,'M2×8 从球心一侧穿过垫圈和固定耳，旋入外侧螺母。仅轻贴合，勿压白或压裂薄耳。',[0,-sign*16,0],parked,title=f'{side}衬片固定 {i}/2 · M2×8');group.append('Wliner_screw_'+suffix)
        cupgroups.append((sign,group))
        L.check(side+'衬片固定检查','确认两个固定耳在槽内坐平、根部无裂纹，螺钉均穿过尼龙圈。当前球窝仍单独放在旁边，方便工具进入。',group)
    L.chapter='03 · 包球与导向锁固'
    for sign,group in cupgroups:L.move(group,[[0,-sign*42,0]],'将'+('后侧' if sign<0 else '前侧')+'球窝组件包到球上','保持球体不动，将已装好衬片的球窝沿导向方向合到球面。肩螺钉此时仍未装入。',detail='不靠导向肩螺钉把卡住的球窝拉合。导向槽应对准球内捕获式螺母。')
    for sign,side in [(-1,'后侧'),(1,'前侧')]:
        add('guide_'+str(sign),f'从{side}球窝外侧将肩螺钉穿过导向槽，旋入球内普通 M2 螺母。肩端应压到钢垫圈上。',[0,sign*16,0],title=side+' · 装入导向肩螺钉',detail='先只干装检查。肩径 2.5 mm，槽名义宽 2.94 mm；不要磨小金属肩径来解决卡滞。2 mm 内六角扳手。')
    L.check('干装检查导向与球面','轻扶两侧球窝，确认球可小幅屈伸和偏转，导向肩在槽内无明显卡点。此时尚未完成导向螺纹锁固。',['Wguide_-1','Wguide_1'],detail='如果金属叠层未贴合、肩长或螺纹长度不符，先停下处理；不能靠继续拧紧塑料补偿。')
    for sign,side in [(-1,'后侧'),(1,'前侧')]:
        id='Wguide_'+str(sign)
        L.move([id],[[0,sign*16,0]],side+'导向螺钉 · 单独退出','扶住球窝，先退出这一侧肩螺钉；另一侧留在原位。')
        L.check(side+'导向螺钉 · 施加锁固剂','按所选低强度、可拆卸金属螺纹锁固剂说明，将少量锁固剂用于金属啮合螺纹；不要涂在光肩、导向槽和球面上。',[id],detail='先确认对不锈钢适用、与附近 PLA 相容，并按产品说明处理和固化；教程不能替代该产品的用量与时间规定。')
        L.move([id],[[0,-sign*16,0]],side+'导向螺钉 · 装回到位','装回并让肩端与钢垫圈直接接触。固定的是金属叠层，不是把塑料夹紧。')
    L.check('锁固完成后再进入载荷测试','两侧均完成金属螺纹锁固。按锁固剂说明等待固化；未完成前只做轻柔装配检查。',['Wguide_-1','Wguide_1'],detail='此检查点不会自动跳过。无固定通用固化时长，请以实际产品说明为准。')
    L.chapter='04 · 固定桥、预紧件与加载杆'
    add('08','从上方把固定桥放到两个球窝的预紧耳之间，对齐两组 M3 通孔。',[0,0,28],detail='名义上固定桥与两侧耳内面各留 2.5 mm 调节空间；不要用其他垫片填死该空间。')
    for i,xx in enumerate([-8,8],1):
        add('preload_w-1_'+str(xx),'在后侧耳外放上 M3 平垫圈。',[0,-18,0],title=f'腕部预紧 {i}/2 · 后侧垫圈')
        add('preload_'+str(xx),'M3×35 从后侧穿过球窝预紧耳、固定桥和前侧预紧耳。',[0,-42,0],title=f'腕部预紧 {i}/2 · M3×35')
        add('preload_w1_'+str(xx),'在前侧耳外套上 M3 平垫圈。',[0,18,0],title=f'腕部预紧 {i}/2 · 前侧垫圈')
        add('preload_n'+str(xx),'旋上 M3 尼龙锁紧螺母，尼龙端朝外。仅消除明显游隙，先不施加目标预紧。',[0,18,0],title=f'腕部预紧 {i}/2 · 螺母')
    add('09','从下方把加载杆方孔套到球颈方键上；方键负责传递扭转。',[0,0,-28])
    add('lever_w1','在加载杆正 X 一侧的连接孔放上 M2 平垫圈。',[16,0,0],title='加载杆连接 · 螺钉头侧垫圈')
    add('lever_screw','M2×20 从垫圈侧横穿加载杆与方键。',[26,0,0],title='加载杆连接 · M2×20')
    add('lever_w-1','在另一侧套上 M2 平垫圈。',[-16,0,0],title='加载杆连接 · 螺母侧垫圈')
    add('lever_n','旋上 M2 尼龙锁紧螺母，尼龙端朝外。轻合紧，螺钉主要防脱，不靠它把方键挤变形。',[-16,0,0],title='加载杆连接 · M2 锁紧螺母')
    L.chapter='05 · 微调与实测'
    L.check('两侧等量微调预紧','固定 M3 螺钉头，两颗预紧螺母交替小幅调整；每次不超过 1/12 圈，随调随检查球面运动。',['Wpreload_n-8','Wpreload_n8'],detail='以松装位置为零点，单侧球窝向内闭合量 ≤0.20 mm；两侧差 ≤0.10 mm。该限值不是要求一定压到 0.20 mm。')
    L.check('记录持姿、间隙与磨损','初始目标力矩为 0.006 N·m，需实测确认。检查固定耳无白化或裂纹、导向螺钉不松、球面无突跳。按测试手册记录磨合和循环后的变化。',detail='教程显示名义几何；不代表实物已经通过 ROM、持姿或寿命试验。')
    L.step('名义腕部活动范围演示','先演示屈伸 −65°～70°，再演示偏转 −20°～30°。实物逐步慢摆，出现卡滞就停下记录。','rom',['W01','W02','W09'],tool='手动慢摆 + 角度记录',detail='两根转轴在球心相交。实际可达范围和非目标滚转仍需实测。')
    replay_steps(L)
    return L

def main():
    global CATALOG
    k=CatalogKit();hinge(k);hinge(k,'R',6,12,1.6,18,10,90);wrist(k)
    rows={p['id']:p for p in json.loads((OUT/'assembly.json').read_text('utf8'))['parts']}
    CATALOG={}
    for p in k.parts:
        id=p['id'];sku=p.get('sku');label=p['label'];spec=label
        if p['printable']:
            label=WNAMES[id] if id.startswith('W') else NAMES[id[1:]]
            spec='PLA 打印件 · '+id+' · 1 件';tool='手动装配'
        elif sku in ['NL2','N2']:tool='4 mm 小扳手 / 镊子'
        elif sku in ['NL3','N3']:tool='5.5 mm 小扳手 / 镊子'
        elif sku=='NL4':tool='7 mm 小扳手'
        elif sku=='GUIDE_M2_D2P5_L6':
            tool='2 mm 内六角扳手';spec='肩 Ø2.5 × 6；M2 × 0.4 螺纹长 4；头 Ø4.8 × 2.4 mm；304 不锈钢'
        elif sku.startswith('M2x'):tool='1.5 mm 内六角扳手'
        elif sku.startswith('M3x'):tool='2.5 mm 内六角扳手'
        elif sku.startswith('M4x'):tool='3 mm 内六角扳手'
        else:tool='手动装入 / 镊子'
        if sku=='W2':spec='M2 钢平垫圈 · 外径 5 / 内径 2.2 / 厚 0.5 mm'+('（必须）' if 'guide_' in id else '；此位置也允许 0.3 mm')
        if sku=='FR6':spec='M6 大平垫圈 · 外径 18 / 内径 6.4 / 厚 1.5 或 1.6 mm；两片同厚'
        CATALOG[id]=dict(id=id,label=label,spec=spec,sku=sku,tool=tool,printable=p['printable'],station=p['station'],frame=p['frame'],bounds=rows[id]['bounds_mm'],stl=rows[id].get('stl'))
    lessons=[hinge_lesson('H'),hinge_lesson('R'),wrist_lesson()]
    orientation_coverage=annotate(CATALOG,lessons)
    for l in lessons:
        expected={id for id,p in CATALOG.items() if p['station']==l.station}
        assert set(l.added)==expected,(l.station,expected-set(l.added),set(l.added)-expected)
        assert len(l.added)==len(expected)
        assert all(np.allclose(offset,0) for offset in l.state.values()),l.station
    folder=OUT/'tutorial';folder.mkdir(exist_ok=True)
    data=dict(revision=REVISION,tutorial_edition=EDITION,geometry_sha256=sha(OUT/'assembly_meshes.npz'),catalog=CATALOG,lessons={l.station:dict(steps=l.steps,total_parts=len(l.added),printed=sum(CATALOG[id]['printable'] for id in l.added)) for l in lessons})
    (folder/'steps.js').write_text('window.LESSONS='+json.dumps(data,ensure_ascii=False,separators=(',',':'))+';',encoding='utf8')
    put(folder/'steps.json',data)
    for source,dest in [('tutorial.html','index.html'),('tutorial.js','tutorial.js'),('tutorial.css','style.css'),('orientation.js','orientation.js')]:shutil.copyfile(HERE/source,folder/dest)
    bom=collections.Counter(p['sku'] for p in CATALOG.values() if p['sku'])
    assert bom=={p['sku']:p['qty'] for p in json.loads((OUT/'BOM.json').read_text('utf8'))}
    put(OUT/'verification/tutorial_coverage.json',dict(passed=True,revision=REVISION,geometry_sha256=data['geometry_sha256'],stations={l.station:dict(steps=len(l.steps),parts=len(l.added),one_part_per_add=True,final_offsets_zero=True) for l in lessons},unique_parts=len(CATALOG),hardware=sum(bom.values()),sku_counts=bom,orientation=orientation_coverage,excluded='C01 is a fit coupon, not an assembly component.'))
    print('TUTORIAL',[(l.station,len(l.steps),len(l.added)) for l in lessons],flush=True)

if __name__=='__main__':main()
