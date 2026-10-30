from common import *
from export_r5 import COLORS
from tool_r5 import fork,nut_starter
import base64,re

def readjs(path):
    s=path.read_text('utf8');return json.loads(s[s.index('=')+1:].rstrip(';'))

def build():
    a=load(OUT/'production_assembly.json')['parts'];z=dict(np.load(OUT/'production_meshes.npz'));kit=load(OUT/'kit.json');old=readjs(BASE/'assembly_guide/data.js');oldparts={p['id']:p for p in old['parts']};oldraw=np.frombuffer(base64.b64decode(old['geometry']),dtype='<f4').reshape(-1,6)
    names={p['name']:p['part_number'] for p in a};P={p['part_number']:p for p in a};chs=load(OUT/'channels.json');parts=[];tri=[];cursor=0
    remap={p['source']:p['part_number'] for p in a if p.get('baseline_name')};K={p['part_number']:p for section in ['structural_parts','hardware','electronics','soft_parts'] for p in kit[section]}
    def pack(p,arr,meta):
        nonlocal cursor
        meta=copy.deepcopy(meta);meta.update(id=p['part_number'],part_number=p['part_number'],first=cursor,count=len(arr),bounds=p['bounds_mm'],frame=p['frame'],role=p['role']);parts.append(meta);tri.append(arr);cursor+=len(arr)
    for p in a:
        i=str(p['i']);v=z[i+'v'];f=z[i+'f'];m=trimesh.Trimesh(v,f,process=False);ar=np.concatenate([v[f],np.repeat(m.face_normals[:,None,:],3,axis=1)],axis=2).reshape(-1,6).astype('<f4')
        c=(F0[p['frame']]@np.r_[np.mean(p['bounds_mm'],axis=0),1])[:3];src=oldparts.get(p.get('source'));meta=src or dict(label=p['label'],feature=p['name'],kind='打印件' if p['role']=='structure' else '电子板' if p['role']=='electronics' else '五金 / 附件',sku=p['sku'],spec=K[p['part_number']]['spec'],orientation='按本步朝向安装；电子板元件面朝磁铁。小五金先在台面预装，避免在关节窄缝中抓持。',markers=[dict(label=p['label'],point=c.tolist())],arrows=[],centre=c.tolist(),spring_group=None)
        if p.get('reprint'):meta['label']=p['label']+'（R5测角修订）';meta['orientation']=meta['orientation'].replace('本轮不装电子件','本轮安装真实测角组件')
        meta['spec']=K[p['part_number']]['spec']
        pack(p,ar,meta)
    for p in old['parts']:
        if p['role']=='tool':
            row=dict(part_number=p['id'],frame=p['frame'],role='tool',bounds_mm=p['bounds']);pack(row,oldraw[p['first']:p['first']+p['count']],p)
    for c in chs:
        if c['kind']!='roll':continue
        A=np.array(c['A']);s=moved(fork(),np.linalg.inv(F0[c['pcb_frame']])@A);v,f=e.base.a.mesh_data(s);m=trimesh.Trimesh(v,f,process=False);ar=np.concatenate([v[f],np.repeat(m.face_normals[:,None,:],3,axis=1)],axis=2).reshape(-1,6).astype('<f4');pn='R5-J003-'+c['id'];names['TOOL_'+c['id']]=pn
        p=dict(part_number=pn,frame=c['pcb_frame'],role='tool',bounds_mm=e.bounds(s).tolist());centre=(A@np.array([0,20,1,1]))[:3]
        pack(p,ar,dict(label='J003 磁铁组件侧送托叉（同一件重复使用）',feature=pn,kind='临时工装',sku=None,spec='PLA；只打印1件，三个旋转接口重复使用。',orientation='开口朝侧窗内，长柄留在外部；工作面朝上，底托承重、侧壁定位。退出后不能留在人偶中。',markers=[dict(label='手指握持区',point=centre.tolist())],arrows=[],centre=centre.tolist(),spring_group=None))
    for source in a:
        if '_BACK_N0_' not in source['name'] and '_BACK_N1_' not in source['name']:continue
        ch=next(c for c in chs if source['name'].startswith(c['id']+'_'));A=np.array(ch['A']);point=(np.linalg.inv(A)@F0[source['frame']]@np.r_[source['mass_centroid_mm'],1])[:3];point[2]+=.05;Q=A@T(point)
        s=moved(nut_starter(),np.linalg.inv(F0[source['frame']])@Q);v,f=e.base.a.mesh_data(s);m=trimesh.Trimesh(v,f,process=False);ar=np.concatenate([v[f],np.repeat(m.face_normals[:,None,:],3,axis=1)],axis=2).reshape(-1,6).astype('<f4');pn='J004-'+source['name'];names[pn]=pn;centre=(Q@np.array([0,0,-36,1]))[:3]
        pack(dict(part_number=pn,frame=source['frame'],role='tool',bounds_mm=e.bounds(s).tolist()),ar,dict(label='J004 M2螺母送料柄（同一件重复使用）',feature=pn,kind='临时工装',sku=None,spec='PLA；浅口临时保持，不承担最终锁紧扭矩。',orientation='薄纸衬住螺母，长柄留在外部；6.2 mm杆通过6.7 mm通道，起牙后退出。',markers=[dict(label='手指握持区',point=centre.tolist())],arrows=[],centre=centre.tolist(),spring_group=None))
    B={p['id']:p for p in parts};steps=[];chapters=[];done=set();locations={};labels={c['id']:c['label'] for c in old['chapters']}
    labels.update(WD_PRE='腕部测角组件：台面预装',ENC_RP='肩俯仰测角',ENC_RU='上臂旋转测角',ENC_RF='前臂旋转测角',ENC_HS='肩外展测角',ENC_HE='肘屈伸测角',ENC_WF='腕屈伸测角',FINISH='走线、标定与检查')
    def ids(ns):return [names.get(n,n) for n in ns]
    def step(ch,title,ns,target,note,A=np.eye(4),base=None,path=None,kind='insert',support='外侧手指 / 台面',new=True,remove=False):
        ns=ids(ns);target=names.get(target,target);base=np.zeros(3) if base is None else np.array(base);path=[np.zeros(3)] if path is None else [np.asarray(x) for x in path];visible=sorted(done|set(ns)|{target});off={p:locations.get(p,[0,0,0]) for p in visible if p not in ns};fresh=[p for p in ns if p not in done] if new else []
        s=dict(chapter=ch,title=title,note=note,parts=ns,new_parts=fresh,before=sorted(done),visible=visible,offsets=off,base_offset=base.tolist(),part_base_offsets={},path=[x.tolist() for x in path],kind=kind,animated=len(path)>1,primary=ns[0],target=target,printed_parts=[p for p in ns if B[p]['role'] in ['structure','tool']],metal_parts=[p for p in ns if B[p]['role'] not in ['structure','tool']],frame_matrix=np.asarray(A).tolist(),printed_direction=B[target]['orientation'],metal_direction=note,support=support,remove_after=remove,auto_section=False,camera_direction=(np.asarray(A)[:3,:3]@np.array([.6,.6,1])).tolist(),source_step=None)
        steps.append(s);done.update(ns);done.add(target)
        for p in ns:locations[p]=(base+path[-1]).tolist()
        if remove:done.difference_update(ns)
        return s
    # WD electronics must be fitted before closing the two wrist forks.
    c=chs[-1];A=np.array(c['A']);Q=F0['l_wrist_flex'];bench=np.array([300,150,0]);front=bench.copy()
    step('WD_PRE','在台面准备 R5-P012 与传感板托',['KEEP_E-P019'],'KEEP_E-P019','元件尚未上电。支架已经与腕中心一体打印；先放在台面另一侧，给板托预装留出操作空间。',A,bench+[200,0,0],kind='prepare')
    step('WD_PRE','板托放在手边，暂不与腕中心闭合',['WD_CARRIER'],'WD_CARRIER','保持板托前后两面敞开，所有螺母和PCB都能从外部用指尖按住。',A,front,kind='prepare')
    for n in ['WD_BACK_N_-5.5','WD_BACK_N_5.5']:
        step('WD_PRE','装入板托的 M2 锁母',[n],'WD_CARRIER','在敞开的板托后面装入锁母；金属端朝螺钉入口，尼龙端朝磁铁侧。外侧低粘胶带暂留，螺钉起牙后取掉。',A,front,[A[:3,2]*15,np.zeros(3)])
    for n,title in [('WD_PCB','装入 S1 三轴传感板'),('WD_PCB_SHIM','铺绝缘缓冲片')]:
        step('WD_PRE',title,[n],'WD_CARRIER','芯片朝向磁铁，6线尾部从缺口引出。手指只压板边，绝缘片在无元件背面；胶点仅用于装配保持。',A,front,[A[:3,2]*18,np.zeros(3)])
    wdboard=ids(['WD_CARRIER','WD_PCB','WD_PCB_SHIM','WD_BACK_N_-5.5','WD_BACK_N_5.5'])
    step('WD_PRE','移动腕中心到预装板托旁',['KEEP_E-P019'],'KEEP_E-P019','手持移动腕中心；在板托对面保持5 mm空隙。此步是台面重新摆放，不是穿入动作。',A,bench+A[:3,2]*5,kind='prepare')
    step('WD_PRE','把预装板托装到腕中心支架',wdboard,'KEEP_E-P019','一手持腕中心，一手压住板托边缘；此时手掌叉还没有安装，板托前方完全敞开。',A,bench+A[:3,2]*5,[-A[:3,2]*5,np.zeros(3)])
    bench=bench+A[:3,2]*5
    for x in [-5.5,5.5]:
        step('WD_PRE','从外侧装 M2×8 与平垫',[f'WD_BACK_BOLT_{x}',f'WD_BACK_W_{x}'],'KEEP_E-P019','先在外部把平垫穿到螺钉上，再从支架背面穿入锁母；指尖保持板托贴合。仅压住缓冲片，不弯曲PCB。',A,bench,[A[:3,2]*20,np.zeros(3)])
    wdboard=ids(['WD_CARRIER','WD_PCB','WD_PCB_SHIM','WD_BACK_N_-5.5','WD_BACK_N_5.5','WD_BACK_BOLT_-5.5','WD_BACK_BOLT_5.5','WD_BACK_W_-5.5','WD_BACK_W_5.5'])
    handbench=np.array([550,150,0]);M=np.array(c['mag_A']);normal=M[:3,2]
    step('WD_PRE','在台面准备手掌磁铁盲座',['KEEP_E-P018'],'KEEP_E-P018','使用 R5-P010：已恢复压片螺钉和锁母入口。磁铁口朝上，所有散件都在外露面操作。',M,handbench,kind='prepare')
    for n,title,d in [('WD_MAG_KEEP_N','装入压片锁母',-normal),('WD_MAG_SPACER','放入 0.5 mm 补高片',normal),('WD_MAGNET','放入 O22 径向充磁磁铁',normal),('WD_MAG_KEEP_W','盖住磁铁入口的大平垫',normal),('WD_MAG_KEEP_SCREW','锁住磁铁防脱压片',normal)]:
        step('WD_PRE',title,[n],'KEEP_E-P018','磁铁不是轴向充磁型号。磁铁侧壁用少量中性胶防转，充分固化；防脱由D7平垫承担，入口重叠应≥1 mm。锁母从背面敞开窝装入，用外侧胶带暂留；螺钉起牙后取掉胶带。',M,handbench,[d*20,np.zeros(3)])
    wdmag=ids(['WD_MAG_KEEP_N','WD_MAG_SPACER','WD_MAGNET','WD_MAG_KEEP_W','WD_MAG_KEEP_SCREW'])
    preattached={names['KEEP_E-P019']:wdboard,names['KEEP_E-P018']:wdmag}
    # Inherit every R4 mechanical operation and its support tools, updated to actual R5 bodies.
    oldfinal=None
    for oldstep in old['steps']:
        s=copy.deepcopy(oldstep)
        if s['kind']=='pose':oldfinal=s;continue
        for key in ['parts','new_parts','before','visible','printed_parts','metal_parts']:s[key]=[remap.get(p,p) for p in s[key]]
        for key in ['primary','target']:s[key]=remap.get(s[key],s[key])
        for key in ['offsets','part_base_offsets']:s[key]={remap.get(p,p):v for p,v in s.get(key,{}).items()}
        for host,attached in preattached.items():
            if host in s['visible']:
                s['visible']+=attached
                for p in attached:s['offsets'][p]=s['offsets'].get(host,[0,0,0])
            if host in s['parts']:
                s['parts']+=attached;s['metal_parts']+=attached
                for p in attached:s['part_base_offsets'][p]=s['part_base_offsets'].get(host,s['base_offset'])
            if host in s['new_parts']:s['new_parts'].remove(host)
        s['note']=s['note'].replace('本轮不装电子件','腕测角组件已预装').replace('R4','R5');s['source_step']=oldstep['number'];steps.append(s)
    done=set(p['part_number'] for p in a if p.get('baseline_name'))|set(wdboard)|set(wdmag);locations={}
    for c in chs[:-1]:
        n=c['id'];ch='ENC_'+n;A=np.array(c['A']);M=np.array(c['mag_A']);pf=c['pcb_frame'];bench=np.array([250,150,0]);magbench=bench+A[:3,1]*60
        mg=[p['name'] for p in a if p['name'].startswith(n+'_MAG')];pod=[p['name'] for p in a if p['name'].startswith(n+'_') and (p['name'] in [n+'_CARRIER',n+'_PCB',n+'_PCB_SHIM',n+'_BACK'] or '_BACK_BOLT_' in p['name'] or '_BACK_N' in p['name'])]
        step(ch,'先确认机械预紧，再准备磁铁座',[n+'_MAG_BODY'],n+'_MAG_BODY','先按 R4 方法调好关节摩擦。磁铁座对准锁固肩钉六角孔；此后若再调肩钉，必须拆下测角附件并重新标零。先在台面装磁铁组件。',M,magbench,kind='prepare')
        for x in [-4.9,4.9]:step(ch,'磁铁座装入 M1.6 黄铜螺母',[n+f'_MAG_NUT_{x}'],n+'_MAG_BODY','螺母从背面敞开六角窝进入；外侧低粘胶带暂留。此时尚未装入关节，手指可直接按住。',M,magbench,[-M[:3,2]*12,np.zeros(3)])
        step(ch,'磁铁放入盲座',[n+'_MAGNET'],n+'_MAG_BODY','复用 O22 D6×2.5 径向充磁磁铁。侧壁少量中性胶防转，固化后使用；不能只靠胶防脱。',M,magbench,[M[:3,2]*15,np.zeros(3)])
        step(ch,'盖上磁铁防脱盖',[n+'_MAG_LID'],n+'_MAG_BODY','外缘盖住磁铁，中心孔用于观察间隙；两个螺钉孔对齐。',M,magbench,[M[:3,2]*15,np.zeros(3)])
        for x in [-4.9,4.9]:step(ch,'锁紧 M1.6×4 沉头螺钉',[n+f'_MAG_SCREW_{x}'],n+'_MAG_BODY','一手持磁铁座外缘，一手旋入；螺钉头平齐，背面去掉临时胶带。检查磁铁不能转动、不能从盖孔取出。',M,magbench,[M[:3,2]*15,np.zeros(3)])
        step(ch,'台面准备传感板托',[n+'_CARRIER'],n+'_CARRIER','从敞开背面预装，暂不把板托固定到关节。',A,bench,kind='prepare')
        nutnames=[p for p in pod if '_BACK_N0_' in p]
        for nn in nutnames:
            tool='J004-'+nn
            step(ch,'板托装入内层 M2 黄铜螺母',[nn,tool],n+'_CARRIER','使用J004送料柄：在外部将螺母卡入0.8 mm浅六角口，用薄纸衬紧。长柄保持在外侧，沿已开通的6.7 mm通道送入；六角窝侧壁用微量中性胶暂留，固化后再取出送料柄并装PCB。最终由两颗普通螺母对顶锁固。',A,bench,[-A[:3,2]*15,np.zeros(3)],support='J004 外部送料柄；胶点仅作预装保持')
            step(ch,'暂留胶固化后抽出 J004',[tool],n+'_CARRIER','确认螺母已经保持在窝中，再抽出送料柄；不能让未保持住的螺母留在内部。',A,bench,[np.zeros(3),-A[:3,2]*25],remove=True,new=False)
        for nn,title in [(n+'_PCB','放入 O22 MT6701 传感板'),(n+'_PCB_SHIM','铺背面绝缘缓冲片'),(n+'_BACK','合上传感板后盖')]:
            step(ch,title,[nn],n+'_CARRIER','芯片面朝磁铁，焊线尾部从侧口引出；只捏板边。背面缓冲片先用微小胶点保持。',A,bench,[A[:3,2]*20,np.zeros(3)])
        for nn in [p for p in pod if '_BACK_BOLT_' in p]:step(ch,'装 M2×10 黄铜沉头螺钉',[nn],n+'_CARRIER','在台面压住后盖，旋入已暂留的内层螺母；螺钉头与后盖平齐。',A,bench,[A[:3,2]*18,np.zeros(3)])
        for nn in [p for p in pod if '_BACK_N1_' in p]:
            tool='J004-'+nn
            step(ch,'外层 M2 普通螺母对顶',[nn,tool],n+'_CARRIER','螺杆已穿出；用J004送料柄把螺母送到螺杆端并起牙，之后用外径≤6.5 mm的4 mm套筒轻锁。J004只负责保持，不承担最终锁紧扭矩。内层螺母由六角窝止转。',A,bench,[-A[:3,2]*15,np.zeros(3)],support='J004 / 4 mm薄壁套筒')
            step(ch,'起牙后抽出 J004',[tool],n+'_CARRIER','螺母已由螺杆保持；取走送料柄，再用4 mm套筒轻锁。',A,bench,[np.zeros(3),-A[:3,2]*25],remove=True,new=False)
        if c['kind']=='roll':
            for x in [-10.5,10.5]:step(ch,'从外侧装入支架锁母',[n+f'_MOUNT_N_{x}'],c['host'],'锁母从新增外侧开口送入，不从传感板旁的窄缝装入。指尖停留在外侧，用低粘胶带暂留到螺钉起牙。',A,path=[A[:3,0]*(18 if x>0 else -18),np.zeros(3)])
            tool='TOOL_'+n
            drop=2.0
            step(ch,'板托先送入临时高度',pod,c['host'],f'先将关节朝上夹稳。磁铁尚未放入；板托比终点外移{drop:.1f} mm，手指握住外侧法兰保持临时高度。',A,base=A[:3,2]*drop,path=[A[:3,1]*35,np.zeros(3)],support='外侧手指持板托，台钳固定关节')
            step(ch,'把磁铁组件放在 J003 托叉上',[tool],n+'_MAG_BODY','底托承重、侧壁定位，工作面保持朝上；握持长柄。只需打印一件 J003，依次重复使用。',A,magbench,[A[:3,1]*25,np.zeros(3)])
            step(ch,'从板托下方送入磁铁组件',mg+[tool],c['host'],'握持位置始终留在侧窗外。先从法兰下方侧送，再沿轴向落下1.45 mm，六角插入肩钉。六角配合不得晃动；用极少量可剥离中性胶填隙防转，固化后使用，不粘住关节活动面。',A,path=[A[:3,1]*35+A[:3,2]*1.45,A[:3,2]*1.45,np.zeros(3)],support='J003 外部长柄与重力支承；外侧手指持板托')
            step(ch,'板托轴向落到定位面',pod,c['host'],f'托叉保持磁铁座，板托沿轴向落下{drop:.1f} mm；挡环捕获磁铁座之后才能取走托叉。保持外侧法兰直到两颗螺钉起牙。',A,path=[A[:3,2]*drop,np.zeros(3)],new=False)
            step(ch,'保持板托，退出 J003',[tool],n+'_CARRIER','板托挡环已限制磁铁外移，六角仍有啮合。把托叉完全侧向抽出，不把工装留在关节里。',A,path=[np.zeros(3),A[:3,1]*42],support='外部手指持板托',remove=True,new=False)
            for x in [-10.5,10.5]:step(ch,'穿入 M2×8 与平垫',[n+f'_MOUNT_BOLT_{x}',n+f'_MOUNT_W_{x}'],c['host'],'先在外部把垫片穿到螺钉上，再整组穿入。螺钉起牙后取掉锁母暂留胶带，交替轻锁到法兰贴合。',A,path=[A[:3,1]*22,np.zeros(3)],support='螺钉杆携带平垫；外部手指按法兰')
        else:
            step(ch,'磁铁组件插入外露肩钉六角孔',mg,c['host'],'关节外侧完全敞开；手指按住磁铁座外缘，用一条低粘胶带暂贴外缘。六角填极少量可剥离中性胶消除回差，固化后使用，不粘活动面。后续挡环就位后去掉胶带。任何预紧调整后必须重新标零。',M,path=[M[:3,2]*22,np.zeros(3)])
            step(ch,'从轴向装入预装传感板主体',pod,c['host'],'主体半夹后沿已开出轴向安装路径；手持外侧板托，挡环到位后捕获磁铁座。外露面取掉暂留胶带。',A,path=[A[:3,2]*25,np.zeros(3)])
            step(ch,'合上另一半定位夹',[n+'_CLAMP'],c['host'],'0.10 mm PET衬条先在外露叉耳上暂贴，宽2.5 mm、长约50 mm，避开摩擦垫。先从外侧绕过固定座，再径向合拢8 mm；后托面负责轴向捕获，必须贴合。',A,path=[A[:3,0]*8+A[:3,2]*25,A[:3,0]*8,np.zeros(3)],support='手指握外部夹壳')
            for y in [-13.5,13.5]:
                step(ch,'夹壳穿入 M2×20 与头下垫',[n+f'_CLAMP_BOLT_{y}',n+f'_CLAMP_W_HEAD_{y}'],n+'_CARRIER','平垫先套在螺钉上，整组从外侧穿入；此处不改变关节原来的AX4预紧。',A,path=[-A[:3,0]*25,np.zeros(3)])
                for nn in [n+f'_CLAMP_W_NUT_{y}',n+f'_CLAMP_N0_{y}',n+f'_CLAMP_N1_{y}']:
                    step(ch,'外侧平垫／普通螺母逐件锁固',[nn],n+'_CLAMP','螺杆已经穿出外侧，垫片和螺母由螺杆承托；两颗普通M2对顶。夹壳不能沿轴向或周向晃动。',A,path=[A[:3,0]*18,np.zeros(3)])
        step(ch,'本轴检查：参考件、间隙与线尾',[n+'_PCB',n+'_MAGNET'],c['host'],'轻转该轴，板随指定输出运动，磁铁参考件保持锁固；不能擦碰。磁铁面到芯片封装表面名义2.0 mm，同轴偏心实测≤0.3 mm。用后盖穿线孔绑软线固定线尾，禁止绑住转动件。',A,kind='check',new=False)
    final=copy.deepcopy(oldfinal)
    for key in ['parts','new_parts','before','visible','printed_parts','metal_parts']:final[key]=[remap.get(p,p) for p in final[key]]
    final.update(chapter='FINISH',title='完成走线后检查七轴，再采集标定',parts=sorted(done),new_parts=[],visible=sorted(done),offsets={},part_base_offsets={},base_offset=[0,0,0],primary=names['ROOT'],target=names['ROOT'],note='按 WIRING.html 完成各段服务环和外侧固定。先断电慢转全范围检查拉线，再按 CALIBRATION.html 分轴采集；腕部必须做屈伸×侧摆3×3交叉检查。R5电子实测尚未通过，不能用理论曲线替代标定。');steps.append(final)
    final['printed_parts']=[p for p in final['parts'] if B[p]['role']=='structure'];final['metal_parts']=[p for p in final['parts'] if B[p]['role']!='structure']
    # RP encoder is installed before joining the shoulder-abduction fork, whose
    # final geometry blocks a later lateral service approach. Carry the completed
    # encoder through all subsequent mechanical assembly steps.
    rp=[s for s in steps if s['chapter']=='ENC_RP'];steps=[s for s in steps if s['chapter']!='ENC_RP'];at=next(i for i,s in enumerate(steps) if s['chapter']=='HS')
    prior=set(steps[at-1]['visible']);rpgroup={p['part_number'] for p in a if not p.get('baseline_name') and p['name'].startswith('RP_')}
    allowed=prior|rpgroup|{names['TOOL_RP']}|{p['id'] for p in parts if p['id'].startswith('J004-RP_')}
    for s in rp:
        s['visible']=[p for p in s['visible'] if p in allowed];s['before']=[p for p in s['before'] if p in allowed];s['offsets']={p:v for p,v in s['offsets'].items() if p in allowed}
    for s in steps[at:]:
        if s.get('source_step') is not None:
            s['visible']=sorted(set(s['visible'])|rpgroup);s['before']=sorted(set(s['before'])|rpgroup)
    steps[at:at]=rp
    seen=[]
    for i,s in enumerate(steps):
        s.update(index=i,number=i+1)
        if s['chapter'] not in seen:seen.append(s['chapter'])
    for ch in seen:
        inds=[i for i,s in enumerate(steps) if s['chapter']==ch]
        for j,i in enumerate(inds):steps[i]['chapter_step']=j+1
        chapters.append(dict(id=ch,label=labels[ch],step_indices=inds))
    data=dict(revision='O24E R5',geometry_sha256=sha(OUT/'production_meshes.npz'),parts=parts,profile=PROFILE,steps=steps,chapters=chapters,geometry=base64.b64encode(np.vstack(tri).tobytes()).decode(),initial_angles={ax['id']:0 for ax in PROFILE['axes']},spring_groups=old['spring_groups'],physical_tested=False,mechanical_only=False)
    put(OUT/'assembly_guide/steps.json',{k:v for k,v in data.items() if k!='geometry'});(OUT/'assembly_guide/data.js').write_text('window.ARM_GUIDE='+json.dumps(data,ensure_ascii=False,separators=(',',':'))+';',encoding='utf8')
    for f in ['index.html','style.css','guide.js','enhance.js']:
        text=(BASE/'assembly_guide'/f).read_text('utf8').replace('O24E R4','O24E R5').replace('PoseDoll_R4','PoseDoll_R5').replace('201步','完整测角安装').replace('201 步','完整测角安装').replace('201',''+str(len(steps)))
        text=text.replace('p.role===\'tool\'?',"p.role==='electronics'?[.1,.45,.3,1]:p.role==='magnet'?[.8,.2,.16,1]:p.role==='tool'?")
        text=text.replace('重打3件＋2件工装','重打5个主件＋测角附件').replace('11 个打印件 · 136 件五金','40 个打印件 · 7 路传感器').replace('本教程只装机械件。','本教程安装完整机械和七路测角装置。').replace('标为J001/J002','标为J001～J004').replace('按六个章节依次安装','按左侧章节依次安装').replace('先在台面分别完成 RP / RU / RF，再连接肩、肘、腕。','腕测角先在台面预装；RP测角须在肩外展叉合入前装好。')
        (OUT/'assembly_guide'/f).write_text(text,encoding='utf8')
    # Review viewer uses the very same triangle buffer, excluding temporary tools.
    viewparts=[]
    for p in parts:
        if p['role']=='tool':continue
        viewparts.append(dict(name=p['id'],frame=p['frame'],role=p['role'],sku=p['sku'],label=p['label'],source_features=[p['feature'],p['label']],first=p['first'],count=p['count'],bounds_mm=p['bounds'],color=COLORS.get(p['role'],[.5]*3)))
    report=load(OUT/'verification/motion_prototype.json') if (OUT/'verification/motion_prototype.json').exists() else {}
    valid=report.get('passed',False) and report.get('geometry_sha256')==data['geometry_sha256']
    view=dict(profile=PROFILE,parts=viewparts,poses=POSES,geometry=data['geometry'],height={},geometry_sha256=data['geometry_sha256'],production_mesh_sha256=data['geometry_sha256'],ueBones=[],harness=load(OUT/'harness/viewer_routes.json') if (OUT/'harness/viewer_routes.json').exists() else [],paths={},audit={n:dict(count=0,pairs=[],advisory_count=0,advisory_pairs=[],affected=[]) for n in POSES} if valid else {},contexts={n:'六路 O22 MT6701 + 一路独立 TMAG 腕侧摆；手动组合另作实物走线检查。' for n in POSES},expectedFrames={},assembly=[],assemblyAngles={},mechanical_count=len(viewparts),reservation_count=0)
    (OUT/'preview/data.js').write_text('window.O24D='+json.dumps(view,ensure_ascii=False,separators=(',',':'))+';',encoding='utf8')
    for f in ['index.html','style.css','viewer.js']:
        s=(BASE/'preview'/f).read_text('utf8').replace('O24E_LArm_Stock_R4','O24E_LArm_Sensing_R5').replace('O24E R4','O24E R5').replace('O24E_left_arm_stock_R4','O24E_R5_sensing_arm')
        s=s.replace('机械147件，另有12个可选电子包络','完整测角装配，电子板均为实际安装件').replace('电子预留（附件未发布）','测角装置已安装').replace('id="electronics-reserved"','id="electronics-reserved" checked hidden').replace('201步',str(len(steps))+'步')
        s=s.replace('普通M3压盖锁固；内垫片临时定位；新版托具装配。3个主件重打，其余8件复用。','保留 R4 摩擦与防脱。5个主件重打、6个复用；六路MT6701与独立腕侧摆传感器。').replace('<strong>11</strong><span>打印件','<strong>40</strong><span>打印件').replace('id="harness" hidden','id="harness"').replace('<input type="checkbox" id="harness">','<label><input type="checkbox" id="harness"> 走线参考</label>')
        s=s.replace("s=$('#search').value.toLowerCase()","s=$('#search').value.toLowerCase()")
        s=s.replace('机械实物件','安装实体').replace('例如 S4-P009','例如 R5-P009')
        (OUT/'preview'/f).write_text(s,encoding='utf8')
    print('VIEW / GUIDE',len(viewparts),'installed bodies,',len(steps),'steps',flush=True)

if __name__=='__main__':build()
