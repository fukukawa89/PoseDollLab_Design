"""Extract the unchanged O24E left shoulder-to-palm mechanical trial kit.

Reads frozen O24E production geometry. Writes only bench/revO24E_LArm_Mech.
No remeshing, scaling, electronic procurement, or physical pass is inferred.
"""
from pathlib import Path
import sys,json,copy,hashlib,shutil,csv,base64,html,zipfile,math
from collections import Counter,defaultdict
sys.dont_write_bytecode=True
HERE=Path(__file__).resolve().parent
H=HERE.parents[1]
SRC=H/'bench/revO24E'
OUT=H/'bench/revO24E_LArm_Mech'
sys.path.insert(0,str(H/'cad/revO24E'))
import build as e
import numpy as np
import trimesh
load=lambda p:json.loads(p.read_text('utf8'))
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def put(p,v):
    p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(json.dumps(v,ensure_ascii=False,indent=2),encoding='utf8')
def cp(rel):
    d=OUT/rel;d.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(SRC/rel,d)
ROOT='l_clavicle_elevate'
AXES=['l_shoulder_flex','l_shoulder_abduct','l_upperarm_roll','l_elbow_flex','l_forearm_roll','l_wrist_flex','l_wrist_deviation']
MODULES=['l_shoulder_pitch','l_shoulder_swing','l_humeral','l_elbow','l_forearm','l_wrist']
LABELS={'l_shoulder_pitch':'01 肩前举 / 后伸','l_shoulder_swing':'02 肩外展 / 内收','l_humeral':'03 上臂内外旋','l_elbow':'04 肘屈伸','l_forearm':'05 前臂旋前 / 旋后','l_wrist':'06 双轴腕与手掌'}
PART_LABELS={'E-P003':'肩部输入座（固定端）','E-P014':'肩俯仰输出 / 外展叉架','E-P013':'肩外展输出 / 上臂旋转输入','E-P016':'上臂骨杆 / 肘叉架','E-P005':'肘输出 / 前臂旋转输入','E-P006':'前臂骨杆 / 腕部外叉','E-P019':'腕部中心交叉件','E-P018':'腕部输出叉 / 手掌连接座','E-P017':'手掌'}
EXPECTED_SOURCE='cdfd44464ad9654d6611291ad2f90e52235b3a38ae33f902985cc1598d6c4e04'
def electronic(r):
    return r.get('role') in ['pcb','connector','magnet'] or any(k in r.get('feature','') for k in ['_pcb_','_pcb','_magnet_keeper_'])
def fk(profile,q):
    f={}
    for n in profile['nodes']:
        m=(f[n['parent']] if n['parent'] else np.eye(4))@e.T(n['offset_mm'])
        if n['axis'] is not None:m=m@e.rot(n['axis'],q.get(n['id'],0)+n['zero_deg'])
        f[n['id']]=m
    return f
def csvfile(name,fields,rows):
    with (OUT/name).open('w',encoding='utf-8-sig',newline='') as f:
        w=csv.DictWriter(f,fieldnames=fields,extrasaction='ignore');w.writeheader();w.writerows(rows)

def extract():
    assert sha(SRC/'production_meshes.npz')==EXPECTED_SOURCE,'Frozen production mesh changed'
    OUT.mkdir(exist_ok=True)
    for name in ['printing','verification','images','profiles','tutorial','preview','source']: (OUT/name).mkdir(exist_ok=True)
    originals=['production_parts.json','production_assembly.json','production_meshes.npz','profiles/device_profile.json','tutorial/steps.json','O24E_delivery.zip']
    put(OUT/'source_fingerprints.json',{n:sha(SRC/n) for n in originals})
    inv=load(SRC/'production_parts.json');allrows={r['part_number']:r for r in inv['structural_parts']+inv['hardware']}
    mods=[copy.deepcopy(next(m for m in load(SRC/'tutorial/steps.json')['modules'] if m['id']==id)) for id in MODULES]
    candidates=set(p for m in mods for p in m['context'])
    excluded=[allrows[p] for p in sorted(candidates) if electronic(allrows[p])]
    chosen=candidates-{r['part_number'] for r in excluded}
    structural=[copy.deepcopy(r) for r in inv['structural_parts'] if r['part_number'] in chosen]
    hardware=[copy.deepcopy(r) for r in inv['hardware'] if r['part_number'] in chosen]
    # O24D fullbody.py:181-183 uses the ISO4762 screw helper (M2 x 18,
    # D3.8 x 2 head) and two D5 x d2.2 x .5 washers. Correct only the
    # procurement labels; their exact source production meshes stay unchanged.
    for r in hardware:
        if r['feature'] in ['l_palm_screw','l_palm_w0','l_palm_w1']:
            r['source_sku']=r['sku'];r['custom_or_secondary_operation']=False
            if r['feature']=='l_palm_screw':
                r['sku']='M2x18_ISO4762';r['spec']='M2×18 内六角圆柱头螺钉；头径3.8、头高2、内六角1.5 mm。沿用原D标准螺钉包络；与M2锁母核完整尼龙啮合。'
            else:r['sku']='M2_WASHER_5x2.2x0.5';r['spec']='M2薄平垫：外径5、内径2.2、厚0.5 mm；手掌两侧各一片。'
    assert set(r['part_number'] for r in structural)==set(PART_LABELS)
    assert len(structural)==9 and all(r['printable'] for r in structural)
    assert all(not electronic(r) and r['procurement_item'] for r in hardware)
    for r in structural:
        r['kit_label']=PART_LABELS[r['part_number']]
        cp(r['stl']);cp(r['assembly_stl'])
    for r in hardware:
        if r.get('stl'):cp(r['stl'])
        for suffix in ['.json','.svg','.stl']:
            rel='machining/'+r['part_number']+suffix
            if r['custom_or_secondary_operation'] and (SRC/rel).exists():cp(rel)
            elif (OUT/rel).exists():
                target=(OUT/rel).resolve();assert target.parent==(OUT/'machining').resolve();target.unlink()
    kit=dict(revision='O24E_LArm_Mech',side='left',physical_dof=7,root_fixed_frame=ROOT,
        source_geometry_sha256=sha(SRC/'assembly_meshes.npz'),source_production_sha256=EXPECTED_SOURCE,
        structural_parts=structural,hardware=hardware,excluded_electronic_parts=excluded,
        source_dimensions_unchanged=True,manufacturing_release=False,physical_tested=False,
        boundary='Fixed E-P003 shoulder input body through palm. Clavicle DOFs, chest, circuits, magnets, sensor fasteners and wiring excluded. Integral sensor seats remain in unchanged printed bodies.')
    put(OUT/'kit.json',kit)
    data=load(SRC/'production_assembly.json');z=np.load(SRC/'production_meshes.npz');zz={};parts=[]
    for p in data['parts']:
        if p['name'] not in chosen:continue
        p=copy.deepcopy(p);old=str(p['i']);p['i']=len(parts);new=str(p['i'])
        zz[new+'v']=z[old+'v'];zz[new+'f']=z[old+'f'];p['source_i']=int(old);parts.append(p)
    assert len(parts)==len(chosen)
    np.savez_compressed(OUT/'production_meshes.npz',**zz)
    put(OUT/'production_assembly.json',dict(units='mm',parts=parts,source_production_sha256=EXPECTED_SOURCE))
    src_profile=load(SRC/'profiles/device_profile.json')
    nodes=[copy.deepcopy(n) for n in src_profile['nodes'] if n['id'] in [ROOT]+AXES]
    nodes[0].update(parent=None,offset_mm=[0,0,0],axis=None,zero_deg=0)
    prof=dict(schema='O24E_LEFT_ARM_MECHANICAL_TRIAL/1',nodes=nodes,axes=[a for a in src_profile['axes'] if a['id'] in AXES],physical_dof=7,
        root_fixed_frame=ROOT,wrist_order=src_profile['wrist_order'],forearm_zero_clocking_deg=-90,manufacturing_release=False,
        source_geometry_sha256=kit['source_geometry_sha256'])
    put(OUT/'profiles/arm_profile.json',prof)
    poses={};motion=load(SRC/'verification/motion_named_endpoints.json');rom=load(SRC/'verification/rom_examination_dense.json')
    srposes=load(SRC/'profiles/poses.json');named={r['pose']:r for r in motion['cases']}
    keep=['neutral','arms_forward','arms_side','arms_overhead_front','arms_overhead_side','arms_elbow_max','arms_carry','arms_drink','arms_head','arms_pronate','arms_supinate','arms_wrist_flex','arms_wrist_extend','arms_radial','arms_ulnar','cross']
    for name in keep:
        # Upstream clavicle/torso pose is a common rigid transform for this
        # complete subtree; removing that transform preserves internal motion.
        p=srposes[name]
        assert named[name]['count']==0
        poses[name]=dict(label=p['label'].replace('双臂','左臂').replace('双肩','左肩').replace('完整','单臂'),angles={a:p['angles'].get(a,0) for a in AXES},source_case=name)
    for r in rom['cases']:
        if r['axis'] not in AXES or '/step/' in r['case']:continue
        assert r['count']==0
        label=next(a['label'] for a in prof['axes'] if a['id']==r['axis'])
        poses[r['case']]=dict(label=f'{label} {r["value_deg"]}°',angles={a:r['angles'].get(a,0) for a in AXES},source_case=r['case'])
    poses['neutral']['label']='A 字参考 · 左肩外展45°'
    poses['arms_head']['label']='左臂 · 近头参考姿态'
    poses['cross']['label']='左臂 · 胸前内收参考姿态'
    put(OUT/'profiles/poses.json',poses)
    seen=set();rotation=np.linalg.inv(e.FA[ROOT])[:3,:3]
    for m in mods:
        m['label']=LABELS[m['id']];steps=[]
        for s in m['steps']:
            s['part_numbers']=[pn for pn in s['part_numbers'] if pn in chosen]
            if not s['part_numbers']:continue
            s['entry_world_A']=(rotation@np.array(s['entry_world_A'])).tolist()
            if s['feature']=='l_E_W6-01':s['note']='先把中心件放在台面准备；将四个闭合六角窝中的 NL3 与 W3 预放完毕，再合拢两层叉架。此步还不拧紧任何肩钉。'
            steps.append(s)
        # All four captive nut/reaction-washer pairs are prepared before the
        # forks are closed. These are the same accepted T6 W physical parts.
        if m['id']=='l_wrist':
            prep=[s for s in steps if s['feature']=='l_E_W6-01']
            prep += [s for s in steps if s['feature'].startswith('l_E_W') and s['feature'].endswith(('_N','_RW'))]
            steps=prep+[s for s in steps if s not in prep]
        for i,s in enumerate(steps,1):
            s['number']=i;s['new_part_numbers']=[p for p in s['part_numbers'] if p not in seen];seen.update(s['part_numbers'])
            if not s['new_part_numbers']:s['note']='沿用已出现的同一件，不重复取料。'+s['note']
        m['steps']=steps;m['context']=list(dict.fromkeys(p for s in steps for p in s['part_numbers']))
    assert seen==chosen
    put(OUT/'tutorial/steps.json',dict(modules=mods,covered_part_numbers=sorted(seen),source_production_sha256=EXPECTED_SOURCE,steps=sum(len(m['steps']) for m in mods)))
    rows=[]
    for r in hardware:
        row=copy.deepcopy(r);row['category']='定制 / 二次加工' if r['custom_or_secondary_operation'] else '标准件 / 现有规格'
        row['available_verified']='';row['buy_or_make']='';rows.append(row)
    csvfile('HARDWARE_DETAIL.csv',['part_number','feature','sku','quantity','category','disposition','spec','available_verified','buy_or_make'],rows)
    groups=defaultdict(list)
    for r in rows:groups[(r['sku'],r['category'])].append(r)
    totals=[dict(sku=sku,category=cat,quantity=len(rs),part_numbers='; '.join(r['part_number'] for r in rs),specifications=' | '.join(dict.fromkeys(r['spec'] for r in rs)),available_verified='',buy_or_make='') for (sku,cat),rs in sorted(groups.items())]
    csvfile('HARDWARE_SUMMARY.csv',['sku','category','quantity','part_numbers','specifications','available_verified','buy_or_make'],totals)
    csvfile('PRINT_PARTS.csv',['part_number','kit_label','quantity','stl','sha256','material','process'],structural)
    put(OUT/'BOM_totals.json',dict(hardware=totals,printed_bodies=9,hardware_pieces=len(hardware),inventory_on_hand='UNKNOWN'))
    # Rigidly rebase every selected production body to the retained input frame.
    F=fk(prof,poses['neutral']['angles']);scene=trimesh.Scene();bounds=[];mass=0
    for p in parts:
        i=str(p['i']);m=trimesh.Trimesh(zz[i+'v'],zz[i+'f'],process=False)
        density=.00124 if p['role']=='structure' else .00785
        mass+=m.volume*density
        world=m.copy();world.apply_transform(F[p['frame']]);bounds.append(world.bounds)
        m.apply_scale(.001);m.visual.vertex_colors=np.array([*e.COLORS.get(p['role'],[.6,.6,.6]),1])*255
        mat=F[p['frame']].copy();mat[:3,3]*=.001;scene.add_geometry(m,node_name=p['name'],transform=mat)
    scene.export(OUT/'O24E_left_arm_mechanical.glb')
    b=np.array(bounds);bb=[b[:,0].min(0).tolist(),b[:,1].max(0).tolist()]
    put(OUT/'envelope.json',dict(bounds_mm=bb,dimensions_mm=(np.array(bb[1])-bb[0]).tolist(),height_mm=bb[1][2]-bb[0][2],nominal_solid_mass_g=mass,scope='A-pose bounding box; nominal solid density estimate, excludes electronics and external tools.'))
    evidence(kit,prof,poses,parts,zz)
    print('EXTRACT',len(structural),'print',len(hardware),'hardware',len(excluded),'omitted',len(poses),'poses',flush=True)

def evidence(kit,prof,poses,parts,zz):
    original=load(SRC/'production_assembly.json');oz=np.load(SRC/'production_meshes.npz');by={p['name']:p for p in original['parts']};identity=[]
    for p in parts:
        a=str(p['i']);b=str(by[p['name']]['i']);identity.append(dict(part_number=p['name'],vertices_equal=bool(np.array_equal(zz[a+'v'],oz[b+'v'])),faces_equal=bool(np.array_equal(zz[a+'f'],oz[b+'f']))))
    assert all(r['vertices_equal'] and r['faces_equal'] for r in identity)
    errors=[]
    source_angles={r['pose']:r['angles'] for r in load(SRC/'verification/motion_named_endpoints.json')['cases']}
    source_angles.update({r['case']:r['angles'] for r in load(SRC/'verification/rom_examination_dense.json')['cases']})
    for pose in poses.values():
        f=fk(prof,pose['angles']);full=e.frames(source_angles[pose['source_case']]);root=np.linalg.inv(full[ROOT])
        errors.extend(float(np.abs(f[n['id']]-root@full[n['id']]).max()) for n in prof['nodes'])
    assert max(errors)<1e-9
    put(OUT/'verification/extraction.json',dict(status='PASS_EXACT_SUBSET',source_production_sha256=EXPECTED_SOURCE,kit_production_sha256=sha(OUT/'production_meshes.npz'),rows=identity,printed_bodies=9,axes=7,max_rebased_FK_error=max(errors),electronics_excluded=True,geometry_edited=False,scope='Exact source arrays and byte-identical print files. Only rigid origin rebasing and electronic-component omission. No physical test.'))
    ids={r['part_number'] for r in kit['structural_parts']};r=load(SRC/'verification/production_parts.json');r['rows']=[x for x in r['rows'] if x['part_number'] in ids]
    assert len(r['rows'])==9 and all(x['status']=='PASS_SCREEN' for x in r['rows'])
    r['scope']='Inherited unchanged-body watertight, connected and morphological-core screens; see extraction.json for exact source identity.';put(OUT/'verification/print_solids.json',r)
    caps=load(SRC/'verification/production_capture.json');caps['rows']=[r for r in caps['rows'] if r['interface'] in MODULES]
    assert len(caps['rows'])==3 and all(r['status']=='PASS_GEOMETRY' for r in caps['rows'])
    caps['scope']='Unchanged shoulder pitch, humeral and forearm production assemblies: output-before-crossbolt paths and mechanical capture inherited by exact identity. This is not a repeated physical pull test.';put(OUT/'verification/capture_inherited.json',caps)
    r=load(SRC/'verification/production_retention.json')
    selected_features={x['feature'] for x in kit['hardware']}
    r['chains']=[x for x in r['chains'] if x['interface'] in MODULES]
    for k,key in [('pin_insertion','pin'),('nut_capture','nut')]:r[k]=[x for x in r[k] if x[key] in selected_features]
    r['wrists']=[x for x in r['wrists'] if x['side']=='l']
    assert len(r['chains'])==5 and len(r['wrists'])==2
    assert len([x for x in r['nut_capture'] if x['nut'].startswith('l_E_W')])==4
    r['scope']='Unchanged selected mechanical capture chain, fixed/drive pins, captive nuts and two wrist axes. Original geometric evidence, no new physical qualification.';put(OUT/'verification/retention_inherited.json',r)
    r=load(SRC/'verification/preload_retention_loads.json');r['rows']=[x for x in r['rows'] if x['axis'] in AXES]
    assert len(r['rows'])==7
    put(OUT/'verification/holding_targets.json',dict(status='INHERITED_TARGETS_NOT_MEASURED',source_geometry_sha256=kit['source_geometry_sha256'],rows=r['rows'],scope='Keep original full O24E holding targets, including its electronics weight allowance. Removing electronics does not qualify extra payload. Values are holding torque, never bolt-tightening torque.'))
    r=load(SRC/'verification/elastic_preload.json');r['rows']=[x for x in r['rows'] if x['axis'] in AXES];r['scope']='Original selected disc-spring capacity screens; actual A8 force curve remains unmeasured.';put(OUT/'verification/springs_inherited.json',r)
    put(OUT/'verification/motion_inherited.json',dict(status='PASS_UNCHANGED_SUBSET',source_production_sha256=EXPECTED_SOURCE,poses=poses,endpoint_count=14,scope='Named poses and individual axis endpoints from O24E reports. Removing bodies cannot introduce a collision; rebase preserves relative transforms. All manual combinations are unverified; whole-space collision proof is not claimed.'))

def printing():
    sys.path.insert(0,str(H/'cad/revO24C_T1'));import printing as printer
    printer.OUT=OUT;printer.REVISION='O24E_LArm_Mech';printer.WORK=OUT/'verification/slicer_work'
    kit=load(OUT/'kit.json');plates=[];plate=dict(id='ARM_PRINT_01',items=[],optional=False,replacement=False);x=y=8.;rowh=0
    for r in sorted(kit['structural_parts'],key=lambda r:-np.ptp(np.array(r['print_bounds_mm']),axis=0)[1]):
        size=np.ptp(np.array(r['print_bounds_mm']),axis=0);w,h,z=size
        assert max(size[:2])<164 and z<180
        if x+w>172:x=8.;y+=rowh+8;rowh=0
        if y+h>172:
            printer.project(plate);plates.append(plate);plate=dict(id=f'ARM_PRINT_{len(plates)+1:02d}',items=[],optional=False,replacement=False);x=y=8.;rowh=0
        plate['items'].append(dict(id=r['part_number'],stl=r['stl'],offset_mm=[x,y,0],stl_sha256=sha(OUT/r['stl'])));x+=w+8;rowh=max(rowh,h)
    if plate['items']:printer.project(plate);plates.append(plate)
    put(OUT/'printing/plates.json',dict(plates=plates,profile='A1 mini / 180 mm / 0.4 nozzle / PLA / 0.12 layer / 5 walls / solid / auto support / 3 mm brim'))
    for p in plates:
        r=printer.run(p);put(OUT/'verification'/f'slice_{p["id"]}.json',r);assert r['passed']

STYLE='body{margin:0;background:#f3f5f2;color:#243b35;font:16px/1.7 system-ui,"Microsoft YaHei",sans-serif}main{max-width:1120px;margin:auto;padding:30px}h1{font-size:32px}a{color:#116b61}nav a{margin-right:16px}.box{padding:18px;background:#deede5;border-left:4px solid #38866a;margin:20px 0}.warn{background:#fff0d9;border-color:#b87b29}.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:12px}.card,details{background:white;padding:16px;border-radius:6px}table{width:100%;border-collapse:collapse;background:white;font-size:13px}th,td{border:1px solid #cddbd3;padding:9px;text-align:left;vertical-align:top}code{overflow-wrap:anywhere}img{max-width:100%;max-height:640px;object-fit:contain}summary{cursor:pointer;font-weight:600}details{margin:12px 0}small{color:#63756c}'
esc=lambda x:html.escape(str(x))
def table(headers,rows):return '<table><tr>'+''.join('<th>'+esc(x)+'</th>' for x in headers)+'</tr>'+''.join('<tr>'+''.join('<td>'+str(x)+'</td>' for x in r)+'</tr>' for r in rows)+'</table>'
def page(name,title,body):
    (OUT/name).write_text('<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><link rel="icon" href="data:,"><title>'+esc(title)+'</title><style>'+STYLE+'</style><main><nav><a href="START_HERE.html">入口</a><a href="preview/index.html">单臂三维</a><a href="PRINTING.html">打印</a><a href="HARDWARE.html">五金</a><a href="ASSEMBLY.html">装配</a><a href="TEST_PLAN.html">试装记录</a></nav><h1>'+esc(title)+'</h1>'+body+'</main></html>',encoding='utf8')

def docs():
    kit=load(OUT/'kit.json');bom=load(OUT/'BOM_totals.json');plates=load(OUT/'printing/plates.json')['plates'];tutorial=load(OUT/'tutorial/steps.json');prof=load(OUT/'profiles/arm_profile.json');env=load(OUT/'envelope.json')
    body=f'<div class="box"><b>左肩关节 → 上臂 → 肘 → 前臂 → 双轴腕 → 手掌</b><br>7 个自由度，9 个连续打印件，{len(kit["hardware"])} 件机械五金，{len(plates)} 个打印盘。保留 O24E 原件号与原尺寸；肩部输入座 E-P003 为本套件固定端。</div>'
    body+='<p>本轮只测试机械效果。PCB、磁铁、线束及其专用压片、螺钉、螺母和 PET 支承片均已剔除。打印件上一体成形的传感器座和磁铁空腔保留，不用切掉；以后可直接补装电路。锁骨两个自由度、胸部和整机钢件 E-M004 不需要制作。</p>'
    body+='<div class="grid">'+''.join(f'<div class="card"><a href="{u}"><b>{t}</b></a><br><small>{note}</small></div>' for u,t,note in [('PRINTING.html','先打印这 9 件','独立 STL 与原生 A1 mini 工程'),('HARDWARE.html','机械五金清单','标准件、复用件与定制加工逐项列出'),('ASSEMBLY.html','按件号组装','6 个模块，保留防脱与预紧顺序'),('preview/index.html','只看这只手臂','7 轴摆姿、逐件动画、原件号搜索'),('O24E_left_arm_mechanical.blend','可编辑 Blender 装配','独立实物对象与 7 轴节点'),('TEST_PLAN.html','记录实际效果','孔配合、保持力、间隙与循环')])+'</div>'
    body+='<p><a href="O24E_left_arm_mechanical.glb">机械装配 GLB</a> · <a href="PRINT_PARTS.csv">打印件 CSV</a> · <a href="HARDWARE_SUMMARY.csv">五金汇总 CSV</a> · <a href="HARDWARE_DETAIL.csv">逐位置明细 CSV</a></p><img src="images/arm.png" alt="O24E 单只左臂机械装配">'
    body+='<div class="box warn">这里是 O24E 的机械试装子集。9 个打印 STL 与原版逐字节相同，未把金属承力件改成塑料。轴、金属筒、压板与键片中仍有定制或二次加工项，请先看五金页再备料。</div>'
    body+='<p>建议先手持 E-P003 固定端检查各轴，再用有软垫的台虎钳固定输入座做空载悬臂保持测试；不要夹活动叉耳、薄连接条、轴承座或传感器座。本套件没有自立底座，外部夹具不算人偶零件。夹具移动与关节下垂要分别记录。</p>'
    reports=[p for p in sorted((OUT/'verification').glob('*.json')) if p.name!='delivery_audit.json']
    body+='<h2>核对记录</h2>'+table(['报告','结果'],[(f'<a href="verification/{p.name}">{esc(p.stem)}</a>',esc(load(p).get('status','PASS_SLICE' if load(p).get('passed') else '见报告'))) for p in reports])
    body+='<p><small>H/W 的已接受结论继续有效。本轮新增的是单臂试装记录，不要求先重测 H/W 才能开始。所有实际效果仍以你打印、装配后的记录为准。</small></p>'
    page('START_HERE.html','O24E · 左臂机械试装包',body)
    body='<div class="box">每个件号打印 1 件。工程已保留 O24E 方向、0.4 喷嘴、PLA、0.12 mm 层高、5 壁、100% 填充、自动支撑及 3 mm 防翘边。不要整体缩放配合件。</div>'
    body+=table(['打印盘','工程','离线切片核对'],[(p['id'],f'<a href="{p["file"]}">下载原生 3MF</a>',f'<a href="verification/slice_{p["id"]}.json">边界、件号、零网格修复</a>') for p in plates])
    body+='<h2>独立打印件</h2>'+table(['件号','位置','数量','STL','打印方向尺寸 mm'],[(r['part_number'],r['kit_label'],1,f'<a href="{r["stl"]}">打印 STL</a>',' × '.join(f'{v:.2f}' for v in np.ptp(np.array(r['print_bounds_mm']),axis=0))) for r in kit['structural_parts']])
    body+='<p>先清理通孔、闭合螺母窝和叉内支撑。保留承力根部与传感器一体座；逐一量孔、试装轴承和锁母，不靠用力压入补偿尺寸错误。parts_assembly 内是装配局部坐标版本，打印时使用上表 stl_print 或 3MF。</p>'
    page('PRINTING.html','左臂 · 打印工程与分件',body)
    by={r['part_number']:r for r in kit['hardware']};rows=[]
    for g in bom['hardware']:
        rows.append([esc(g['sku']),g['quantity'],g['category'],esc(g['part_numbers']),esc(g['specifications'])])
    body='<p>按一只左臂计算，不包含备用量。库存列留空：实际补购量＝需求量－核验合格的现有数量。相同名义 SKU 的定制件仍须逐件号核对轴长、孔位和材料，不能只按总数量下单。</p>'
    body+='<p><a href="HARDWARE_SUMMARY.csv">按规格汇总 CSV</a> · <a href="HARDWARE_DETAIL.csv">逐位置、复用与新制明细 CSV</a></p>'+table(['规格 / SKU','件数','类型','实际件号','尺寸 / 要求'],rows)
    custom=[r for r in kit['hardware'] if r['custom_or_secondary_operation'] and (OUT/'machining'/f'{r["part_number"]}.json').exists()]
    body+='<h2>定制与二次加工件</h2><p>以下实体仍为金属件。加工文件的螺纹使用外径包络，必须按参数切实际螺纹；不能直接把这些 STL 加进 PLA 打印盘。钢材强度和表面要求沿用原接口表。三组捕获横栓按自由端切短并恢复导入牙，不磨掉头部或有效锁固段。</p>'
    body+=table(['件号 / 部位','文件','说明'],[(r['part_number']+'<br>'+esc(r['feature']),f'<a href="machining/{r["part_number"]}.svg">三视图</a> · <a href="machining/{r["part_number"]}.stl">金属实体</a> · <a href="machining/{r["part_number"]}.json">尺寸、基准与材料</a>',esc(r['spec'])) for r in custom])
    body+='<p>消耗材料另备：金属小螺纹用低强度可拆锁固剂（沿用 O24E 的 222 工艺）、按轴承座原工艺核验的固持胶、软夹垫和见证线记号笔。它们不作为按颗计数的五金件。锁母尼龙锁固段受损、锁片折弯开裂时更换。</p>'
    page('HARDWARE.html','左臂 · 五金、复用与加工清单',body)
    body='<div class="box">先备齐金属件，再合拢完整骨杆。<a href="preview/index.html#assembly">打开逐件三维</a>。每个件号是一个实际材料体；重复出现的件号表示同一件在相邻关节中继续使用。</div>'
    body+='<p>总顺序：清理 9 个打印件 → 肩俯仰 → 肩外展 → 上臂旋转 → 肘 → 前臂旋转 → 双轴腕 → 手掌。E-P003 中未使用的锁骨连接口留空；它只作为本轮固定输入端，不另装锁骨轴承、金属筒或钢支架。</p>'
    body+='<p>三个 C20 接口必须先套入完整输出骨杆，再装横向捕获螺钉；固定筒捕获销先于轴承。H16 保留完整金属压板回路与弹簧堆叠。腕部先在中心件预装四组 NL3/W3，再合拢两层叉架。所有保持力调好后完成独立锁固，不以加大拧紧力掩盖装配干涉。</p>'
    for m in tutorial['modules']:
        body+='<details id="'+m['id']+'"><summary>'+m['label']+f' · {len(m["steps"])} 步</summary>'+table(['步','实际件号 / 特征','操作'],[(s['number'],'<b>'+', '.join(s['part_numbers'])+'</b><br><code>'+esc(s['feature'])+'</code>',esc(s['note'])) for s in m['steps']])+'</details>'
    body+='<p>拆卸时先托住下游骨杆、卸载并松开预紧，再解除对应捕获件。此教程不包含电路步骤；与传感器相关的空腔保持为空。</p>'
    page('ASSEMBLY.html','左臂 · 逐件机械装配',body)
    targets={r['axis']:r for r in load(OUT/'verification/holding_targets.json')['rows']}
    body='<div class="box">先确认能顺序装好，再测活动顺滑、保持、间隙与防脱。已接受 H/W 状态不重置；下表用于这只新打印左臂的整合效果记录。</div>'
    body+='<ol><li>来料与打印：记录打印批次、实际孔径、插入力、是否需要修孔和支撑是否可清除；不要修改原文件后仍记作同一版本。</li><li>逐关节组装：拍下横栓后装、锁母止转、销双端进入和独立锁固的照片。先低预紧正反轻拉，检查几何挡止；用手支撑下游，不作冲击拉拔。</li><li>活动：肩前举/外展/内外旋、肘、前臂、腕两轴分别走完下面范围，记录卡点、擦碰、掉粉及相邻轴串动。</li><li>保持：先空载手持，再固定输入座。以实测力臂和力计量起动力矩、两向保持力矩；水平悬臂、屈肘和腕端姿态各观察 60 秒，记录角漂与夹具滑移。保持力目标不是螺钉拧紧扭矩，不增加未核定的手持负载。</li><li>循环：一次完整往返为 1 次，在 0/10/20/50/100 次记录；不补紧。发生补紧时保留原记录并另开一轮。检查轴向/径向间隙、见证线、锁片与尼龙段。</li></ol>'
    body+=table(['轴','活动范围 °','沿用 O24E 保持目标 N·m'],[(a['label'],f'{a["limits_deg"][0]} ～ {a["limits_deg"][1]}',f'{targets[a["id"]]["hold_target_Nm"]:.5f}') for a in prof['axes']])
    body+='<p>目标来自原完整 O24E 的有限载荷计算，保留原电路质量余量；不是此次单臂的实测额定值。当前没有电路，不评测角精度、磁场或线束寿命。</p><p><a href="TRIAL_LOG.csv">空白逐轴记录 CSV</a> · <a href="verification/holding_targets.json">原目标与假设</a></p>'
    page('TEST_PLAN.html','左臂 · 试装与效果记录',body)
    if not (OUT/'TRIAL_LOG.csv').exists():
        fields=['axis','label','round_trip_cycles','date','operator','print_batch','fit_notes','hold_Nm_plus','hold_Nm_minus','drift_deg_60s','fixture_slip','axial_play_mm','radial_play_mm','witness_line','dust','retightened','pass','photo']
        csvfile('TRIAL_LOG.csv',fields,[dict(axis=a['id'],label=a['label'],round_trip_cycles=n) for a in prof['axes'] for n in [0,10,20,50,100]])

def preview():
    from preview import ASSEMBLY_JS
    parts=load(OUT/'production_assembly.json')['parts'];kit=load(OUT/'kit.json');by={r['part_number']:r for r in kit['structural_parts']+kit['hardware']};z=np.load(OUT/'production_meshes.npz');packed=[];cursor=0
    for p in parts:
        i=str(p['i']);v=z[i+'v'];f=z[i+'f'];m=trimesh.Trimesh(v,f,process=False);ar=np.concatenate([v[f],np.repeat(m.face_normals[:,None,:],3,axis=1)],axis=2).reshape(-1,6).astype('<f4')
        p.update(first=cursor,count=len(ar),color=e.COLORS.get(p['role'],[.6,.6,.6]),source_features=by[p['name']].get('source_features',[by[p['name']].get('feature','')]))
        cursor+=len(ar);packed.append(ar)
    prof=load(OUT/'profiles/arm_profile.json');poses=load(OUT/'profiles/poses.json');env=load(OUT/'envelope.json')
    payload=dict(profile=prof,parts=parts,poses=poses,geometry=base64.b64encode(np.vstack(packed).tobytes()).decode(),height=env,geometry_sha256=sha(OUT/'production_meshes.npz'),production_mesh_sha256=sha(OUT/'production_meshes.npz'),ueBones=[],harness=[],paths={},audit={n:dict(count=0,pairs=[],affected=[]) for n in poses},contexts={},expectedFrames={n:{fr:M.tolist() for fr,M in fk(prof,p['angles']).items()} for n,p in poses.items()},assembly=load(OUT/'tutorial/steps.json')['modules'])
    dest=OUT/'preview';(dest/'data.js').write_text('window.O24D='+json.dumps(payload,ensure_ascii=False,separators=(',',':'))+';',encoding='utf8')
    view=(SRC/'preview/viewer.js').read_text('utf8');view=view.replace("state.center=[0,0,280],span:650","state.center=[0,0,0],span:240")
    view=view.replace('个装配显示实体（PCBA子特征归整件采购）','个机械实物件').replace('相邻关节：0 对干涉。非相邻接触：','原 O24E 相同姿态的相邻干涉记录：0 对。非相邻接触：')
    view=view.replace("revision:'O24E'","revision:'O24E_LArm_Mech'").replace("'O24E_pose.json'","'O24E_left_arm_pose.json'")
    # Changing a slider exits illustrative assembly mode before moving the arm.
    view=view.replace("state.angles[a.id]=+e.target.value;","state.assemblyVisible=null;state.offsets={};state.highlight=[];state.angles[a.id]=+e.target.value;")
    (dest/'viewer.js').write_text(view,encoding='utf8');shutil.copyfile(SRC/'preview/style.css',dest/'style.css')
    js=ASSEMBLY_JS.replace("$('#harness').checked=true;$('#bones').checked=true;","$('#harness').checked=false;$('#bones').checked=true;")
    js+="\nwindow.ARM_SELF_CHECK=window.O24E_SELF_CHECK;window.ARM_ASSEMBLY_CHECK=window.O24E_ASSEMBLY_CHECK;\n"
    (dest/'assembly.js').write_text(js,encoding='utf8')
    (dest/'index.html').write_text('''<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><link rel="icon" href="data:,"><title>O24E · 左臂机械试装</title><link rel="stylesheet" href="style.css"><body><aside><div class="eyebrow">O24E / LEFT ARM MECHANICAL TRIAL</div><h1>单只左臂<span>肩关节到手掌</span></h1><p class="intro">原 O24E 生产分件与尺寸。PCB、磁铁、线束和专用固定件已剔除。</p><div class="stats"><div><strong>7</strong><span>自由度</span></div><div><strong>9</strong><span>打印件</span></div><div><strong id="parts">—</strong><span>机械实物件</span></div></div><span id="height" hidden></span><div class="assumption"><b>固定端 E-P003</b> 肩部输入座保留，锁骨两轴不在本轮范围。<br>A 字参考：肩外展45°；前臂固定钟向仍只计一次。<br>姿态几何依据来自原 O24E；实际打印、组装与保持效果待测。</div><label class="field">姿态 / 单轴端点<select id="pose"></select></label><p id="context" class="intro"></p><label class="field">检查区域<select id="focus"><option value="all">整只左臂</option><option value="wrist">双轴腕与手掌</option></select></label><label class="field">查找零件<input id="search" placeholder="例如 E-P006、forearm 或 wrist"></label><div class="checks"><label><input type="checkbox" id="bones" checked> 机械转轴</label><label><input type="checkbox" id="hardware" checked> 机械五金</label><input type="checkbox" id="shell" checked hidden><input type="checkbox" id="helpers" hidden><input type="checkbox" id="harness" hidden></div><div class="buttons"><button id="zero">回 A 字</button><button id="fit">适配视图</button><button id="save">导出角度</button></div><button id="play" hidden></button><button id="stop" hidden></button><details id="assembly-panel"><summary>逐件装配 / 装入方向</summary><label class="field">模块<select id="assembly-module"></select></label><div class="buttons"><button id="assembly-prev">上一步</button><button id="assembly-next">下一步</button><button id="assembly-move">重播装入</button><button id="assembly-exit">回单臂</button></div><b id="assembly-title"></b><p id="assembly-parts"></p><p id="assembly-note"></p><small>方向示意；相同件号只取一件，装配路径依据见原几何报告。</small></details><div id="sliders"></div><div class="links"><a href="../START_HERE.html">试装入口</a><a href="../PRINTING.html">打印工程</a><a href="../HARDWARE.html">五金清单</a><a href="../ASSEMBLY.html">逐件教程</a><a href="../O24E_left_arm_mechanical.blend">Blender</a><a href="../O24E_left_arm_mechanical.glb">GLB</a></div></aside><main><header><span id="current"></span><div><button data-view="three">立体</button><button data-view="front">正面</button><button data-view="side">侧面</button><button data-view="back">背面</button></div></header><canvas id="view" aria-label="可旋转的单只左臂机械装配"></canvas><div id="overlay"><span>拖动旋转 · 滚轮缩放</span><span id="scope"></span></div><div id="status"></div><div id="singular"></div><details id="issues"><summary>姿态提示</summary><div id="pairs"></div></details><pre id="error" hidden></pre></main><script src="data.js"></script><script src="viewer.js"></script><script src="assembly.js"></script></body></html>''',encoding='utf8')
    print('PREVIEW',len(parts),len(poses),flush=True)

def audit():
    kit=load(OUT/'kit.json');checks=[]
    def check(n,ok):checks.append(dict(check=n,passed=bool(ok)))
    check('source O24E untouched',all(sha(SRC/n)==v for n,v in load(OUT/'source_fingerprints.json').items()))
    check('9 unchanged printed bodies',len(kit['structural_parts'])==9 and all(sha(OUT/r['stl'])==r['sha256']==sha(SRC/r['stl']) for r in kit['structural_parts']))
    check('mechanical hardware only',all(not electronic(r) for r in kit['hardware']))
    ids={r['part_number'] for r in kit['structural_parts']+kit['hardware']};steps=load(OUT/'tutorial/steps.json')
    check('all physical parts covered once in inventory',set(steps['covered_part_numbers'])==ids)
    placed=[]
    for p in load(OUT/'printing/plates.json')['plates']:
        r=load(OUT/'verification'/f'slice_{p["id"]}.json');check('slice '+p['id'],r['passed'] and r['input_sha256']==sha(OUT/p['file']) and r['mesh_repairs']==0)
        placed.extend(i['id'] for i in p['items'])
    check('one print copy per body',Counter(placed)==Counter(r['part_number'] for r in kit['structural_parts']))
    from html.parser import HTMLParser
    from urllib.parse import urlsplit,unquote
    class Links(HTMLParser):
        def __init__(self):super().__init__();self.links=[]
        def handle_starttag(self,tag,attrs):self.links.extend(v for k,v in attrs if k in ['src','href'] and v)
    missing=[]
    for p in [*OUT.glob('*.html'),OUT/'preview/index.html']:
        h=Links();h.feed(p.read_text('utf8'))
        for u in h.links:
            a=urlsplit(u)
            if not a.scheme and a.path and not (p.parent/unquote(a.path)).exists():missing.append(str(p)+': '+u)
    check('all local links exist',not missing)
    check('editable and exchange models',all((OUT/n).exists() for n in ['O24E_left_arm_mechanical.blend','O24E_left_arm_mechanical.glb']))
    browser=load(OUT/'verification/browser_review.json') if (OUT/'verification/browser_review.json').exists() else {}
    check('final browser model and controls',browser.get('production_mesh_sha256')==sha(OUT/'production_meshes.npz') and browser.get('ready') and browser.get('sliders')==7 and browser.get('console_errors')==0 and browser.get('restored_visible')==len(ids))
    r=dict(status='PASS_DELIVERY' if all(c['passed'] for c in checks) else 'FAIL',checks=checks,missing_links=missing,physical_tested=False)
    put(OUT/'verification/delivery_audit.json',r);print(r['status'],[x for x in checks if not x['passed']],missing,flush=True)
    assert r['status']=='PASS_DELIVERY'

def package():
    for p in HERE.glob('*'):
        if p.suffix in ['.py','.md']:shutil.copyfile(p,OUT/'source'/p.name)
    files=[]
    for p in sorted(OUT.rglob('*')):
        if p.is_file() and p.name not in ['manifest.json','O24E_left_arm_mechanical.zip'] and 'slicer_work' not in p.parts and p.suffix!='.blend1':files.append(dict(path=p.relative_to(OUT).as_posix(),sha256=sha(p),bytes=p.stat().st_size))
    put(OUT/'manifest.json',dict(revision='O24E_LArm_Mech',files=files,source_production_sha256=EXPECTED_SOURCE,physical_tested=False))
    dest=OUT/'O24E_left_arm_mechanical.zip'
    with zipfile.ZipFile(dest,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
        for r in files:z.write(OUT/r['path'],'O24E_left_arm/'+r['path'])
        z.write(OUT/'manifest.json','O24E_left_arm/manifest.json')
    with zipfile.ZipFile(dest) as z:assert z.testzip() is None
    print('ZIP',dest.stat().st_size,len(files),flush=True)

if __name__=='__main__':
    for command in sys.argv[1:] or ['extract','printing','preview','docs']:globals()[command]()
