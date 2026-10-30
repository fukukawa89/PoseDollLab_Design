"""A supported assembly sequence. Every loose stack has an explicit support state."""
from build_stock import *
from tooling import tray,pin

def tools_for_guide():
    data=[];tk=load(OUT/'tooling/kit.json');native={}
    for p in tk['parts']:
        mesh=trimesh.load(OUT/p['stl'],process=True);mesh.apply_transform(np.linalg.inv(p['print_matrix']));native[p['part_number']]=md.Manifold(md.Mesh64(np.array(mesh.vertices,copy=True),np.array(mesh.faces,dtype=np.uint64,copy=True)))
    for r in load(OUT/'interfaces.json')['rolls']:
        W=np.array(r['W']);R=rot([0,0,1],180 if r['id']!='RF' else 90)
        for code,s,M,label in [('J001',native['R4-J001'],W@R@T([0,0,-7.3]),'托叉：握持端始终留在侧窗外'),('J002',native['R4-J002'],W,'导向针：大头始终留在裸转子正面')]:
            data.append(dict(name=r['id']+'_'+code,part_number=r['id']+'_'+code,frame=r['fixed_frame'],s=moved(s,np.linalg.inv(F0[r['fixed_frame']])@M),role='tool',sku=None,label=label,manufacturing_part_number='R4-'+code))
    return data

def make_plan(parts,orientation):
    P={p['part_number']:p for p in parts};N={p['name']:p['part_number'] for p in parts};ints=load(OUT/'interfaces.json');steps=[];chapters=[];seen=set();done={};installed=set();offsets={};chapter=None;target=None;mat=None;mid=None
    def pn(names):return [N[n] for n in (names if isinstance(names,list) else [names])]
    def v(x):return np.asarray(x,float).tolist()
    def add(names,title,note,base=None,path=None,kind='insert',support='hand_external',remove_after=False,partbases=None,primary=None,receiver=None):
        nonlocal installed,offsets
        ids=pn(names);base=np.asarray(base if base is not None else [0,0,0]);path=path or [[0,0,0]];pb={N[k]:v(x) for k,x in (partbases or {}).items()};before=sorted(installed);fresh=[i for i in ids if i not in seen];seen.update(ids);installed.update(ids)
        for i in ids:
            off=pb.get(i,base.tolist())
            if np.linalg.norm(off)>.0001:offsets[i]=off
            else:offsets.pop(i,None)
        tar=N[receiver] if receiver else target;pr=N[primary] if primary else ids[0]
        row=dict(index=len(steps),number=len(steps)+1,chapter=mid,chapter_step=len(chapter['step_indices'])+1,title=title,note=note,parts=ids,new_parts=fresh,before=before,visible=sorted(installed),offsets=copy.deepcopy(offsets),base_offset=base.tolist(),part_base_offsets=pb,path=path,kind=kind,animated=len(path)>1,primary=pr,target=tar,printed_parts=[i for i in ids if P[i]['role'] in ['structure','tool']],metal_parts=[i for i in ids if P[i]['role'] not in ['structure','tool']],frame_matrix=mat.tolist(),printed_direction=orientation[tar]['orientation'],metal_direction=note,support=support,remove_after=remove_after,auto_section=support in ['tray_and_guide','continuous_pin_transfer','axle_and_tray'],camera_direction=(mat[:3,:3]@np.array([2.6,3.2,2.0])/np.linalg.norm([2.6,3.2,2.0])).tolist(),source_step=None)
        steps.append(row);chapter['step_indices'].append(row['index'])
        if remove_after:
            for i in ids:installed.remove(i);offsets.pop(i,None)
        return row
    def start(id,label,M,t,initial=()):
        nonlocal mid,mat,target,chapter,installed,offsets
        mid=id;mat=np.array(M);target=N[t];chapter=dict(id=id,label=label,step_indices=[]);chapters.append(chapter);installed=set(initial);offsets={}
    for r,fn,on,label in zip(ints['rolls'],['ROOT','SHOULDER_ABDUCT','ELBOW_OUTPUT'],['SHOULDER_PITCH','UPPER_ARM','FOREARM'],['肩俯仰','上臂旋转','前臂旋转']):
        pre=r['id'];W=np.array(r['W']);Z=W[:3,2];Y=W[:3,1] if pre!='RF' else W[:3,0];B=-Z*45;start(pre,label+'：裸转子预装后合座',W,on)
        tj=pre+'_J001';pj=pre+'_J002';springs=sorted([n for n in N if n.startswith(pre+'_A8_')],key=lambda n:float(orientation[N[n]]['centre']@Z) if isinstance(orientation[N[n]]['centre'],np.ndarray) else np.dot(orientation[N[n]]['centre'],Z))
        pack=[pre+'_HW']+springs+[pre+'_F2'];loaded=[tj]+pack;T0=B+Y*35-Z*6
        add(on,'固定裸转子，保留正面开放','先不装固定座和压盖。用带软垫的小台钳／桌夹轻夹厚实外圆，使蓝色轴向箭头朝上；避免夹住薄筋。此时正面可取出导向针，背面可穿入肩钉。',B,kind='prepare',support='bench_clamp')
        add(tj,'把托叉放在外部，朝上的浅座承托五金','托叉在模型侧面外35 mm处，手指可直接接触整组。握住20×20 mm手柄，保持浅座水平向上；本步不是把手指伸进窗口。',T0,kind='prepare',support='hand_on_20mm_handle')
        for n in pack:
            note='从上方放入托叉，始终由托叉浅座承托；不在骨杆内部逐片摆放。'
            if '_A8_' in n:note+=' 按右侧剖面核对凸缘方向；RP每两片同向，两组反向；RU/RF为两片反向。自由状态总高可比动画名义工作高度稍大。'
            add(n,'外部预排：'+(P[N[n]]['sku'] or n),note,T0,path=[v(Z*20),[0,0,0]],receiver=tj,support='tray_gravity_up')
        add(loaded,'整组托入侧窗，暂不到摩擦面','夹具已固定裸转子；一手保持托叉水平，从侧窗送入整组，到轴线下方即停。零件由托叉承托，无需在窗口里托住散片。',B-Z*6,path=[v(Y*35),[0,0,0]],support='tray_gravity_up')
        add(pj,'从开放正面插入导向针','用手捏住导向针的大头，从裸转子正面穿过轴孔和各垫片内孔。只轻推定位，若错孔先退回外部重新排齐；大头始终留在外部。',B,path=[v(Z*30),[0,0,0]],support='hand_external_pin')
        add(loaded,'沿导向针上移托叉，保留1 mm间隙','保持导向针不动，将托叉与整组上移5 mm。暂留1 mm装配余量，托叉继续承托，导向针限制侧向错位。',B-Z,path=[v(-Z*5),[0,0,0]],support='tray_and_guide')
        # The first sample is outside the complete bone, not inside its service bore.
        add(pre+'_AX','肩钉从真正的外部入口接近导向针','从尚未连接下游关节的外部开口穿入肩钉。用3 mm内六角托住螺钉头，另一手保持托叉；停止在接触导向针的位置。',B-Z*21.9,path=[v(-Z*158.1),[0,0,0]],support='driver_and_tray')
        add([pre+'_AX',pj],'肩钉顶出导向针，连续接替定位','肩钉与导向针端面对接，一起向上推；垫片内孔始终由针或肩钉占住。导向针从开放正面升出，螺钉头到达头下垫片。',B-Z,path=[v(-Z*20.9),[0,0,0]],partbases={pre+'_AX':B-Z,pj:B+Z*20.9},primary=pre+'_AX',support='continuous_pin_transfer')
        add(pj,'取走导向针','从外部取走导向针。各片现在已经套在肩钉上，托叉继续承托；不要松手倾倒。',B+Z*50,path=[v(-Z*29.1),[0,0,0]],remove_after=True,support='axle_and_tray')
        add(r['keeper'],'先套上防脱压盖','从开放正面把空压盖套到转子细颈上。此时尚不与固定座锁合，六角窝现在用于容纳反向安装的螺钉头。',B,path=[v(Z*25),[0,0,0]],support='rotor_neck')
        for suffix in ['F1','ANCHOR','BACK_W4','RW','N']:
            n=pre+'_'+suffix;txt='正面完全开放，手指可直接托放；保持轴线朝上，依次落在肩钉上。'
            if suffix=='N':txt+=' 此处仍用NL3：金属端朝垫片、尼龙端朝外。用5.5 mm扳手托住外露螺母，3 mm内六角旋入，先捕获整组，保留1 mm间隙。'
            add(n,'开放正面：'+P[N[n]]['sku'],txt,B,path=[v(Z*25),[0,0,0]],support='axle_and_gravity')
        add(tj,'肩钉已捕获整组，抽出托叉','确认反力锁母已旋上、各片穿在肩钉上后，从侧面抽出托叉。7.6 mm开口可绕过7 mm螺钉头；托叉不留在人偶中。',B-Z+Y*35,path=[v(-Y*35),[0,0,0]],remove_after=True,support='axle_thread_captured')
        add(pack+[pre+'_AX'],'轻贴合预紧堆叠','取走托叉后，一手在正面用扳手保持NL3，另一手旋肩钉，收掉1 mm装配余量。只调到名义初始高度；RP四片1.8 mm，RU/RF两片1.0 mm，不压平。',B,path=[v(-Z),[0,0,0]],support='thread_capture')
        add(fn,'取固定座，准备合拢','固定座此时才加入。先观察锁母六角与窝的朝向；若差一个角度，微调轴钉和锁母后重新核对碟簧高度。',kind='prepare',support='hand_external',receiver=fn)
        packet=[on,r['keeper']]+pack+[pre+'_'+q for q in ['AX','F1','ANCHOR','BACK_W4','RW','N']]
        add(packet,'把已捕获五金的转子总成合入固定座','整组保持完整：先让反力锁母进入六角窝，再让大平垫进入浅座。压盖环唇仍捕获大平垫，禁止省略。此过程不再携带未定位的散垫片。',path=[v(B),[0,0,0]],support='axle_thread_captured',receiver=fn)
        for x in [-r['lug_x_mm'],r['lug_x_mm']]:
            add(pre+f'_lid_bolt_{x}','压盖螺钉反向穿入','从压盖六角口穿入原M3×16，头埋入旧锁母窝，螺纹尖端在固定座背面露出。用2.5 mm内六角托住头。',path=[v(-Z*28),[0,0,0]],support='driver')
            for suf,title in [('washer','背面套入薄W3'),('nut','第一颗普通M3'),('jam','第二颗普通M3对顶')]:
                txt='背面无遮挡，手指沿露出的螺纹端放入。'
                if suf=='nut':txt+=' 第一颗先轻贴合W3，让压盖贴座。不要拿压盖螺钉调关节预紧。'
                if suf=='jam':txt+=' 用厚度≤2 mm的5.5 mm开口扳手保持第一颗不转，再用另一把厚度≤2 mm的5.5 mm开口扳手拧紧第二颗，使两颗互相锁住；不能两颗一起向打印件猛拧。前臂压盖后方会挡住长套筒，本教程统一使用两把薄开口扳手。'
                add(pre+f'_lid_{suf}_{x}',title,txt,path=[v(Z*28),[0,0,0]],support='external_thread')
        add(fn,'检查本模块防脱与锁固','两侧压盖螺钉均完成对顶；螺纹应露出第二颗螺母至少一整牙，名义1.1 mm。画见证线，轻推拉确认捕获；检查压盖贴合、转子可转、反力NL3已穿过尼龙段。',kind='check',support='fully_fastened')
        done[pre]=set(installed)
    def external_pack(prefix,axis,B=None):
        B=np.asarray(B if B is not None else [0,0,0]);features=[n for n in N if n.startswith(prefix)];ax=prefix+'AX';springs=sorted([n for n in features if n.endswith(('_S1','_S2'))],key=lambda n:np.dot(orientation[N[n]]['centre'],axis),reverse=True)
        group=[ax,prefix+'HW']+springs+[prefix+'F2'];staging=B+axis*35
        add(ax,'在外部拿好肩钉','把肩钉头放在3 mm内六角上，尖端朝上；在身体外35 mm处操作，手指可接触每一片。',staging,kind='prepare',support='driver_tip_up')
        for n in group[1:]:add(n,'在肩钉上预装 '+P[N[n]]['sku'],'从螺纹尖端套入，依次为头下W4、A8、A8、外FW4。按右侧凸缘箭头核对两片反向；各片由肩钉和螺钉头承托。',staging,path=[v(-axis*20),[0,0,0]],support='axle_gravity')
        add(group,'整根肩钉连同预紧组装入','整组移至关节外侧，直接旋入已固定的NL3；肩钉约束内孔，手在外部托住螺钉头。先低预紧，再与另一侧交替调整；不在关节上逐片悬放。',B,path=[v(axis*35),[0,0,0]],support='driver_and_axle')
    for r,fn,fixedgroup,movinggroup,label in zip(ints['hinges'],['SHOULDER_PITCH','UPPER_ARM'],['RP','RU'],['RU','RF'],['肩外展','肘']):
        M=np.array(r['M']);pre=r['id'];start(pre,label+'：先定位内层，再整组穿钉',M,fn,done['RP'] if pre=='HS' else done['HS'])
        add(fn,'准备已完成的上游模块','保留已经完成的旋转模块；固定本模块，分别使正在操作的内座朝上。',kind='prepare',support='bench_clamp')
        for side,tag in [(-1,'HL_'),(1,'HR_')]:
            axis=M[:3,1]*side
            for suf in ['N','RW','K1','K2','F1']:
                txt='此时叉口仍开放，手指可从外侧直接放入。NL3尼龙朝深处；W3贴金属面，两片W4叠在其外。'
                if suf=='F1':txt='用指腹把FW4压到三处定位筋之间，光滑面朝外。定位筋顶端比摩擦面低0.18 mm；它只临时夹住外圆，不能代替肩钉。'
                add(pre+'_'+tag+suf,'内层 '+P[N[pre+'_'+tag+suf]]['sku'],txt,path=[v(axis*25),[0,0,0]],support='face_up_seat' if suf!='F1' else 'radial_retention_pads')
            add(fn,'轻翻转检查：内层五金不掉落','在软布上轻轻翻转刚完成的一侧，确认FW4和背后各片不滑出。若松脱或需硬砸才能压入，先停在台面处理定位筋配合，不能进入合叉步骤。恢复另一侧朝上再继续。',kind='check',support='retention_fit_gate')
        add([P[i]['name'] for i in sorted(done[movinggroup])],'合入已完成的下游模块','内层已由定位筋留在座内。握持模块的厚实部分，从叉口合入；不用手指伸在两个摩擦面之间托片。',path=[v(-M[:3,2]*60),[0,0,0]],support='radial_retention_pads')
        for side,tag in [(-1,'HL_'),(1,'HR_')]:external_pack(pre+'_'+tag,M[:3,1]*side)
        add(fn,'检查本关节与取走临时工具','肩钉均穿过NL3尼龙段后，内层由正式金属堆叠捕获；定位筋不承受预紧力。两侧交替调节，按已有活动范围慢转。',kind='check',support='fully_fastened');done[pre]=set(installed)
    W=F0['l_wrist_flex'];B=-W[:3,2]*50;start('W','双轴腕：四侧防落片与外部预装',W,'FOREARM',done['HE'])
    add('KEEP_E-P019','在台面准备腕中心件','四面分别朝上装入内层，压入各侧FW4后检查不掉片，再换下一面。暂不装入前臂叉。',B,kind='prepare',support='bench_top')
    old={r['part_number']:r['feature'] for r in load(SRC/'kit.json')['hardware']};wp={old[n.removeprefix('KEEP_')]:n for n in N if n.startswith('KEEP_E-H')}
    groups=[]
    for key,axis in [('WYM',-W[:3,1]),('WYP',W[:3,1]),('WXM',-W[:3,0]),('WXP',W[:3,0])]:
        group=[]
        for suf in ['N','RW','K1','K2','F1']:
            n=wp['l_E_'+key+'_'+suf];group.append(n);add(n,'腕中心 '+key+' / '+P[N[n]]['sku'],'开放面朝上，手指在外侧放入。最后FW4压入三处定位筋，光滑面朝叉耳；轻翻转不掉片后才换面。',B,path=[v(axis*25),[0,0,0]],receiver='KEEP_E-P019',support='radial_retention_pads' if suf=='F1' else 'face_up_seat')
        add('KEEP_E-P019',key+' 定位保持检查','在软布上轻翻转；这一面全部五金保持在座内才继续。夹持筋配合必须在开放台面处理，不允许合叉后再塞散片。',B,kind='check',support='retention_fit_gate',receiver='KEEP_E-P019');groups+=group
    add(['KEEP_E-P019']+groups,'装入已定位好四侧五金的腕中心','握住中心件的实心角区，整件进入前臂叉。四侧FW4都已临时定位，不需同时托住四面散垫片。',path=[v(B),[0,0,0]],support='radial_retention_pads')
    add('KEEP_E-P018','装入一体腕叉与手掌','握住一体手掌从开放叉口合入；角链、磁铁入口和原轴线保持。',path=[v(-W[:3,2]*50),[0,0,0]],support='radial_retention_pads')
    # Map original wrist feature names to the generic prefix routine.
    for key,axis in [('WYM',-W[:3,1]),('WYP',W[:3,1]),('WXM',-W[:3,0]),('WXP',W[:3,0])]:
        alias='TEMP_'+key+'_'
        for suf in ['AX','HW','S1','S2','F2']:N[alias+suf]=N[wp['l_E_'+key+'_'+suf]]
        external_pack(alias,axis)
    row=add('KEEP_E-P018','装配完成：七轴检查与A字姿态','取走托叉、导向针和台钳。确认三只压盖完成双普通螺母对顶，11处关节肩钉仍用NL3。低预紧活动，最后肩外展回45°；本版尚需实物验证定位筋配合、手感和保持力。',kind='pose',support='fully_fastened')
    ids=[p['part_number'] for p in parts if p['role']!='tool'];row.update(parts=ids,printed_parts=[i for i in ids if P[i]['role']=='structure'],metal_parts=[i for i in ids if P[i]['role']!='structure'],before=ids,visible=ids,new_parts=[],base_offset=[0,0,0],part_base_offsets={},offsets={},animated=True,pose_from={a['id']:0 for a in PROFILE['axes']},pose_to=POSES['neutral']['angles'])
    assert set(ids)<=seen
    return steps,chapters
