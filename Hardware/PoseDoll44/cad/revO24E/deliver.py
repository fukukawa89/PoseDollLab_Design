"""Reviewable HTML, actual part index, assembly steps, machining sheets and manifest."""
from build import *
import html,base64,re,zipfile
esc=lambda x:html.escape(str(x))
STYLE='body{font:16px/1.65 system-ui,"Microsoft YaHei",sans-serif;color:#24383d;background:#f3f5f3;margin:0}main{max-width:1160px;margin:auto;padding:38px}h1{font-size:34px;line-height:1.2}h2{margin-top:38px}a{color:#086c73}table{border-collapse:collapse;width:100%;font-size:13px;background:white}td,th{border:1px solid #d5dfdc;padding:8px;text-align:left;vertical-align:top}code{overflow-wrap:anywhere;font-size:12px}.box{padding:18px;background:#e1efeb;border-left:4px solid #168574;margin:18px 0}.warn{background:#fff0db;border-color:#b67c24}.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(230px,1fr));gap:14px}.card{background:white;padding:20px;border-radius:8px}img{max-width:100%;background:white}small{color:#607276}button,select{padding:8px;font:inherit}details{background:white;padding:12px;margin:10px 0}nav a{margin-right:16px}'
def page(file,title,body):
    (OUT/file).parent.mkdir(parents=True,exist_ok=True)
    (OUT/file).write_text(f'<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{esc(title)}</title><style>{STYLE}</style><main><nav><a href="START_HERE.html">交付入口</a><a href="preview/index.html">三维与逐件动画</a><a href="ASSEMBLY.html">装配</a><a href="HARDWARE.html">五金</a><a href="TEST_PLAN.html">验收</a></nav><h1>{esc(title)}</h1>{body}</main></html>',encoding='utf8')
def table(headers,rows):return '<table><tr>'+''.join('<th>'+esc(x)+'</th>' for x in headers)+'</tr>'+''.join('<tr>'+''.join('<td>'+str(x)+'</td>' for x in r)+'</tr>' for r in rows)+'</table>'
def assembly():
    inv=load(OUT/'production_parts.json');a=load(OUT/'assembly.json')['parts'];zz=np.load(OUT/'assembly_meshes.npz');by={p['name']:p for p in a};mp=inv['feature_to_production'];modules=[];allseen=set()
    entries={n:r for r in load(OUT/'profiles/sensor_entries.json')['rows'] for n in [r['board'],r.get('tail')] if n}
    pin_report=load(OUT/'verification/production_retention.json') if (OUT/'verification/production_retention.json').exists() else {}
    pin_entries={r['pin']:r for r in pin_report.get('pin_insertion',[]) if r['status']=='PASS_GEOMETRY'} if pin_report.get('geometry_sha256')==sha(OUT/'assembly_meshes.npz') else {}
    def ids(names):return list(dict.fromkeys(k for n in names if n in mp for k in mp[n]))
    def module(id,label):
        r=dict(id=id,label=label,steps=[],context=[]);modules.append(r);return r
    def add(m,title,names,note,axis=None,travel=25):
        for name in names:
            if name not in mp:continue
            direction=axis;stepnote=note
            if name in pin_entries:
                r=pin_entries[name];sg=next(x['sign'] for x in r['paths'] if x['first_block_mm'] is None);p=by[name];Q=FA[p['frame']]@np.linalg.inv(F0[p['frame']]);direction=(Q[:3,:3]@np.array(r['axis_world'])*sg).tolist();stepnote+=' 从完整生产体已验证的通孔入口插入；动画采用该入口方向。'
            if name in entries:
                r=entries[name];direction=(FA[r['frame']][:3,:3]@np.array(r['entry_local'])).tolist();stepnote+=' 板与灌封尾线作为一件从已验证入口共同放入，动画方向以sensor_entries为准。单轴板保留非承力封装胶定位；腕板先放两条0.12 mm PET支承片。'
                if name==r.get('tail') and all(k in allseen for k in ids([name])):continue
            paired=[name]
            if name in entries and name==entries[name]['board'] and entries[name].get('tail'):paired.append(entries[name]['tail'])
            pn=ids(paired);fresh=[x for x in pn if x not in allseen];allseen.update(pn)
            if axis is None and 'pin' in name:
                p=by[name];vv=zz[str(p['i'])+'v'];_,axes=np.linalg.eigh(np.cov(vv.T));axis=(FA[p['frame']][:3,:3]@axes[:,-1]).tolist()
            if direction is None:direction=axis
            s=dict(number=len(m['steps'])+1,title=title+' · '+name,part_numbers=pn,new_part_numbers=fresh,feature=name,note=stepnote,entry_world_A=direction or [0,0,1],animation_travel_mm=travel,animation_scope='Explains declared insertion direction; finite solid path evidence is linked separately, not a physical process simulation.')
            m['steps'].append(s)
    jx={j['id']:j for j in load(OUT/'profiles/joint_interfaces.json')};ix={j['id']:j for j in load(OUT/'profiles/capture_interfaces.json')};order={n['id']:i for i,n in enumerate(PROFILE['nodes'])}
    for pre,j in sorted(jx.items(),key=lambda kv:order[kv[1]['axis_id']]):
        h='pressure_web_width_mm' in j;m=module(pre,('H16 单轴弹性压板 / ' if h else 'C20 金属筒防脱 / ')+pre)
        ax=np.array(j['axis_world']);fr=j['axis_id'];ax=(FA[fr][:3,:3]@F0[fr][:3,:3].T@ax).tolist()
        if not h:
            it=ix[pre];Wx=np.array(it['W']);Q=FA[fr][:3,:3]@F0[fr][:3,:3].T;ax=(Q@Wx[:3,2]).tolist();tx=(Q@Wx[:3,0]).tolist()
            fixednames=[r['source_features'][0] for r in inv['structural_parts'] if r['frame']==it['fixed_frame']]
            stages=[('准备输入连续骨架',fixednames+[pre+'_compression_cartridge'],'先清理通孔、六角配合面和支撑。按金属筒六角键定位；不靠压紧打印件产生预紧。',ax),
             ('先插固定筒捕获销',[pre+'_fixed_capture_pin'],'固定筒先进入输入座，再从有入口的一端插D1.5弹性销；两端进入输入座，之后才放轴承。销长与孔坐标见加工页。',tx),
             ('安装轴承',[n for n in by if n.startswith(pre+'_bearing_')],'轴承由两端入金属筒，按原金属座配合和固持胶工艺；保持端面退让。不要把轴承作为轴向摩擦压紧垫。',ax),
             ('后侧闭合',[pre+'_rear_thrust_cap',pre+'_shaft',pre+'_face_pad_-1'],'后盖六角套在有头轴根部；从后侧穿轴。后盖及后摩擦片进入金属筒端面；后侧带轴预装，与正面零件闭合。',(-np.array(ax)).tolist()),
             ('正面摩擦与浮动压盖',[pre+'_face_pad_1',pre+'_keyed_output_cap'],'先放摩擦片和浮动六角压盖，压盖轴向长孔朝横向穿栓方向。不要预装横向捕获螺钉。',ax),
             ('套入完整输出骨杆',[pre+'_output_socket'],'整个连续生产件沿轴滑入。不是逐个建模特征拼成骨杆。此时横向捕获螺钉必须尚未安装。',ax),
             ('捕获螺母',[pre+'_capture_nyloc'],'从+X六角入口放新DIN985，尼龙端向外，六角进入闭合止转壁。',tx),
             ('横向捕获螺钉',[pre+'_capture_bolt'],'从-X入口穿过输出骨杆、浮动压盖长孔和轴横孔。旋入锁母，留0.10–0.20 mm横向端隙；禁止夹死浮动压盖。至少一完整螺距露出尼龙。',(-np.array(tx)).tolist()),
             ('放防松键片',[pre+'_lock_tab'],'内键入压盖对应槽，外舌暂时不折。键片是定制成形金属件，不能用普通薄平垫冒充。',ax),
             ('弹性预紧',[n for n in by if n.startswith(pre+'_spring_')],'严格按下面的组号装：同组同向套叠增加力，相邻组反向串联增加行程。不要按渲染堆高直接决定夹紧力。',ax),
             ('调节并锁固',[pre+'_nut_washer',pre+'_locknut'],'金属支承平垫→薄螺母。按当前载荷表测保持力矩调整；确认压盖仍有轴向浮动余量，金属回路不压轴承或塑料。薄螺母使用适用于金属的小规格低强度螺纹锁固剂，按厂家固化要求；完成调节后把键片外舌贴住螺母平面。',ax),
             ('末端防脱',[pre+'_end_safety_pin'],'存在本件时必须装入；不得因已有螺纹锁固而省略。',tx),
             ('测角件',[pre+'_magnet',pre+'_pcb',pre+'_connector'],'磁铁按规定径向磁化和极性标记；原板与灌封六芯尾线复用。按原定位座安装；先核极性、间隙和引线，再封装非承力固定胶。',ax)]
        else:
            stages=[('准备固定叉架',[pre+'_fork_-1',pre+'_fork_1'],'该零件号表示整个连续打印体。不要沿承力根开缝装内件。先清支撑、检查轴承孔和螺母入口。',ax),
             ('固定侧轴承与压板',[pre+'_bearing_-1',pre+'_bearing_1',pre+'_pressure_-1',pre+'_pressure_1'],'钢压板、轴承、隔套按模型所在侧安装；轴承端面必须与预紧压板回路分开。',ax),
             ('内金属与输出件',[pre+'_compression_sleeve',pre+'_hub',pre+'_friction_-1',pre+'_rotor_cap_-1',pre+'_friction_1',pre+'_rotor_cap_1',pre+'_shaft'],'将内六角芯、两侧金属盖和摩擦片装入完整输出轮毂。六角驱动传扭；摩擦发生在金属面。',ax),
             ('输出轮毂穿销',[pre+'_drive_pin'],'驱动销贯穿金属芯并进入输出轮毂两壁，承担轴向捕获。由入口插入，确认双端咬合；不得只装金属芯而漏过输出轮毂。',None),
             ('两侧轴向挡圈',[pre+'_retainer_-1',pre+'_retention_pin_-1',pre+'_retainer_1',pre+'_retention_pin_1'],'先挡圈后D1.5横销，两侧都安装；锁母不能代替这些挡止。',ax),
             ('钢隔套',[n for n in by if n.startswith(pre+'_compression_spacer_')],'隔套进入导向座，钢端面形成封闭预紧回路。打印导向座负责定位，不作为被压实的间隔片。',ax),
             ('先放闭合锁母',[n for n in by if n.startswith(pre+'_preload_nut_')],'从外侧直线入口放入新M3 DIN985，旋转至六角完全坐入；不能让尼龙圈抵住入口充当止转。',ax),
             ('支承垫片',[n for n in by if n.startswith(pre+'_preload_w_')],'分别安装正反两面支承垫片，保留规定厚度。',ax),
             ('碟簧组',[n for n in by if n.startswith(pre+'_preload_') and '_spring_' in n],'每根拉紧螺钉独立一套碟簧。相同组号同向叠加，两组相对串联；最外放硬平垫。',ax),
             ('装预紧螺钉',[n for n in by if n.startswith(pre+'_preload_') and not any(k in n for k in ['_nut_','_w_','_spring_','_nut_trap'])],'交替小角度拧两根螺钉，测两侧金属间隙和保持力矩，避免一侧压死另一侧悬空。锁母止转须有效，肩部或隔套不得提前顶死弹性行程。',ax),
             ('测角尾线',[pre+'_magnet',pre+'_pcb',pre+'_connector'],'保持原传感器板、径向磁化磁铁与六芯灌封尾线；更新后的线长见下料表。',ax)]
        for title,names,note,direction in stages:add(m,title,names,note,direction)
        m['context']=list(dict.fromkeys(pn for s in m['steps'] for pn in s['part_numbers']))
    for side in ['l','r']:
        m=module(side+'_wrist','T6 双轴腕 / '+side);ax=[0,0,1]
        mirror=np.diag([1.,-1,1.]) if side=='r' else np.eye(3);wr=FA[side+'_wrist_flex'][:3,:3]@mirror;wy=(wr@np.array([0,1,0])).tolist()
        add(m,'前臂一体近端叉',[side+'_E_W4-01'],'W4-01已与真实前臂骨管合并为同一生产件，根部不是T6台架方口。腕中心与肘腕骨长保持。')
        add(m,'中心交叉件',[side+'_E_W6-01'],'使用T6闭合六角螺母窝；先预放四颗NL3和内侧反力垫W3，再安两层叉架。')
        for pre in ['WYM','WYP','WXM','WXP']:
            d=np.array([1,0,0]) if pre[1]=='X' else np.array([0,1,0]);d=(wr@d*(-1 if pre[-1]=='M' else 1)).tolist()
            for suf,note in [('N','NL3：先入闭合六角窝，尼龙向螺纹尖端。'),('RW','W3：7×3.2×0.5 mm反力垫；不得换成0.8 mm旧垫。'),('K1','W4：9×4.3×0.8 mm隔套第一片。'),('K2','W4：隔套第二片；两片共同保证肩部不顶反力垫。'),('F1','FW4：12×4.3×1 mm内摩擦片。'),('F2','FW4：外摩擦片，叉耳在二者之间。'),('S1','A8：8×4.2×0.4 mm第一片。实际自由高与力曲线需来料核对。'),('S2','A8：第二片与第一片相对串联，沿用已接受T6 W堆叠。'),('HW','W4：头侧硬支承垫。'),('AX','O22肩钉：Φ4×8肩、M3×6牙、Φ7×3头。3 mm内六角继续越过尼龙阻力；验证完整啮合、肩部余隙。')]:
                if pre=='WXM' and suf=='N':add(m,'装第二层输出叉',[side+'_E_W4-04'],'先让输出叉与中心件交错到位，再穿X轴肩钉。')
                add(m,pre+' '+suf,[side+'_E_'+pre+'_'+suf],note,d)
        add(m,'原掌片',[side+'_palm',side+'_palm_w0',side+'_palm_w1',side+'_palm_nut',side+'_palm_screw'],'原掌形和方榫定位；新M2 DIN985在掌柄窝内止转，穿螺钉后双向拉掌验证。')
        add(m,'磁铁安装',[side+'_E_magnet_keeper_nut',side+'_E_wrist_magnet',side+'_E_magnet_keeper_washer',side+'_E_magnet_keeper_screw'],'先从背面预放锁母；磁铁从盲杯开口直入，随后装D7压边平垫和M2×10螺钉。压片覆住开口，不依赖封闭唇强压磁铁。',wy)
        add(m,'固定侧测角板',[side+'_E_pcb_nut_-1',side+'_E_pcb_nut_1',side+'_E_pcb_shim_-1',side+'_E_pcb_shim_1',side+'_E_wrist_pcb',side+'_E_wrist_connector',side+'_E_pcb_keeper_-1',side+'_E_pcb_keeper_1',side+'_E_pcb_screw_-1',side+'_E_pcb_screw_1'],'先放螺母和两条0.12 mm PET支承片，板从镜像后的+Y方向放上台阶，后装两片D10宽平垫和M2×6。平垫压板边约1.6 mm，轻拧不弯板。板和尾线固定在前臂，不跨腕轴。',wy)
        m['context']=list(dict.fromkeys(pn for s in m['steps'] for pn in s['part_numbers']))
    m=module('final','骨架剩余件、电子背板与整机收尾')
    for r in inv['structural_parts']:
        if r['part_number'] in allseen:continue
        add(m,'核对连续实体',[r['source_features'][0]],'按生产件的同体特征定位到整机。相邻模块教程出现相同零件号时是同一件，不得重复打印。')
    for p in a:
        if p['name'].startswith('electronics_'):continue
        if not any(x not in allseen for x in ids([p['name']])):continue
        add(m,'安装剩余独立件',[p['name']],p.get('notes','')+'；按三维位置与原生BOM确认规格，先保持检修口可达。')
    m['context']=list(dict.fromkeys(pn for s in m['steps'] for pn in s['part_numbers']))
    put(OUT/'tutorial/steps.json',dict(geometry_sha256=sha(OUT/'assembly_meshes.npz'),modules=modules,covered_part_numbers=sorted(allseen),pcb_assemblies=inv['purchased_assemblies'],note='One visible step per named physical component or continuous production body. Repeated body IDs refer to the same already introduced part. PCBA components are supplied assembled; no individual pad procurement.'))
    rows=[]
    for m in modules:
        inner=table(['步','实际件号 / 特征','操作与检查'],[(s['number'],'<b>'+', '.join(s['part_numbers'])+'</b><br><code>'+esc(s['feature'])+'</code>',esc(s['note'])) for s in m['steps']])
        rows.append('<details id="'+m['id']+'"><summary>'+esc(m['label'])+f' · {len(m["steps"])} 步</summary>'+inner+'</details>')
    body='<div class="box">先读装配规则，再按实际件号操作。<a href="preview/index.html#assembly">打开三维逐件动画</a>。动画表达装入方向；几何路径通过范围见对应验证表，不能代替手感、公差或实体拉拔验收。</div>'
    body+='<p>总顺序：清理全部打印件与加工件 → 从骨盆向腰胸颈和四肢装金属关节 → 完成前臂后安装双轴腕 → 布线与背板 → A字零位与测角标定 → 整机验收。同一连续件可能同时构成上一关节输出和下一关节输入，教程中相同件号只取一件。</p>'
    body+='<p>每个接口装好后、加入下一级骨杆之前，先检查可调摩擦、零摩擦实体防脱、销双端捕获、锁母六角止转、完整尼龙啮合和工具可达。高载荷轴按新保持力矩表调整。拆卸顺序反向；先支撑下游骨杆并卸载，再展开并更换锁片。不要用增加拧紧力掩盖未到位或孔口干涉。</p>'
    body+=''.join(rows)+'<h2>电子与线束最后闭合</h2><p>E-B001为已装配载板，E-B002为XIAO模块。38块测角板和42个原始标量保持；背板组件按原生PCB资料供装。按 <a href="harness/CABLE_CUTLIST.csv">下料表</a>布每段六芯线，在活动轴两侧固定并留服务弯；未进行柔性线束动态仿真。完成0/10/20/50/100次不补紧记录后才可判性能通过。</p>'
    page('ASSEMBLY.html','O24E · 逐件装配教程',body)

def machining():
    inv=load(OUT/'production_parts.json');parts={p['name']:p for p in read_saved()};ints=load(OUT/'profiles/capture_interfaces.json');jx=load(OUT/'profiles/joint_interfaces.json');dest=OUT/'machining';dest.mkdir(exist_ok=True);rows=[]
    for r in inv['hardware']+[dict(part_number=x['part_number'],feature=x['source_features'][0],custom_or_secondary_operation=True,stl=x['assembly_stl'],spec=x['process']) for x in inv['structural_parts'] if not x['printable']]:
        if not r.get('custom_or_secondary_operation') or not r.get('stl'):continue
        p=parts[r['feature']];it=next((it for it in ints if p['name'].startswith(it['id']+'_')),None);j=next((j for j in jx if p['name'].startswith(j['id']+'_')),None)
        S=moved(p['s'],np.linalg.inv(np.array(it['W']))@F0[p['frame']]) if it else p['s']
        v,f=base.a.mesh_data(S);bb=bounds(S);cen=bb.mean(0);v=np.array(v,copy=True)-cen
        if r['part_number'].startswith('E-M'):
            mm=trimesh.load(OUT/r['stl'],process=False);v=np.array(mm.vertices);f=np.array(mm.faces);cen=mm.bounds.mean(0);v-=cen;bb=mm.bounds
        stl=dest/(r['part_number']+'.stl');trimesh.Trimesh(v,f,process=False).export(stl)
        # Orthographic triangle edges with explicit overall dimensions. Functional
        # dimensions/tolerances below remain authoritative, not pixel measuring.
        panels=[];drawing_mesh=trimesh.Trimesh(v,f,process=False);adj=drawing_mesh.face_adjacency;edges=drawing_mesh.face_adjacency_edges;normals=drawing_mesh.face_normals;angles=drawing_mesh.face_adjacency_angles
        for q,(aa,ab) in enumerate([(0,1),(0,2),(1,2)]):
            pts=v[:,[aa,ab]];size=np.ptp(pts,axis=0);scale=min(270/max(size[0],1),210/max(size[1],1));pp=pts*scale+[q*320+160,140]
            depth=next(x for x in range(3) if x not in [aa,ab]);silhouette=(normals[adj[:,0],depth]>=0)!=(normals[adj[:,1],depth]>=0)
            unique=edges[silhouette | (angles>math.radians(20))]
            paths=' '.join(f'M{pp[a,0]:.2f},{pp[a,1]:.2f}L{pp[b,0]:.2f},{pp[b,1]:.2f}' for a,b in unique)
            panels.append(f'<path d="{paths}" fill="none" stroke="#245361" stroke-width=".28"/><text x="{q*320+20}" y="285" font-size="13">{["XY","XZ","YZ"][q]} · {size[0]:.3f} × {size[1]:.3f} mm</text>')
        svg=f'<svg xmlns="http://www.w3.org/2000/svg" width="960" height="310" viewBox="0 0 960 310"><rect width="960" height="310" fill="white"/>{"".join(panels)}</svg>'
        (dest/(r['part_number']+'.svg')).write_text(svg,encoding='utf8')
        data=dict(part_number=r['part_number'],feature=p['name'],sku=p.get('sku'),material_requirement=p.get('material','See interface certified material requirement'),notes=p.get('notes',''),local_origin_in_datum_mm=cen.tolist(),bounds_before_centering_mm=bb.tolist(),mesh=stl.name,geometry_sha256=sha(OUT/'assembly_meshes.npz'),interface=j,
            tolerances=dict(unless_specified_mm=.10,journal_diametral_clearance_mm=[.01,.03],bearing_seat='actual bearing/retaining-compound supplier fit; inspect, no printed substitute',metal_pin_hole_mm='+0.00/+0.03 before press fit qualification',metal_friction_face_flatness_mm=.03,metal_friction_face_finish_Ra_um=1.6,printed_nut_flat_clearance_mm=.20,printed_journal_entry_diametral_clearance_mm=.32),
            threaded_geometry='Threads represented by major-diameter envelope; cut actual ISO metric thread and check GO/NO-GO. Crossholes referenced to shaft axis and rear seating datum. Final manufacturing release remains false pending tolerance/physical qualification.')
        put(dest/(r['part_number']+'.json'),data)
        rows.append([r['part_number'],esc(p['name']),f'<a href="machining/{r["part_number"]}.svg">三视图</a> · <a href="machining/{r["part_number"]}.stl">局部实体</a> · <a href="machining/{r["part_number"]}.json">基准/尺寸/材料</a>',esc(p.get('notes',''))])
    page('MACHINING.html','O24E · 定制件与二次加工', '<div class="box warn">这些是逐件名义制造几何与参数页，螺纹使用外径包络显示。功能尺寸、配合、材质证书和实配验收优先；未经实物公差验证，不将网格导出称为生产放行。供应商报价和库存尚未知。</div><p>轴与前压盖优先共用42CrMo类调质钢料；轴材质最低屈服按每轴接口表，750或940 MPa不可用普通退火圆棒代替。已有304压板的强化材质要求继续有效。捕获螺钉优先标准ISO4762，只有自由端切短并修复导入牙；弹簧、轴承和锁母不得整体缩放。</p><p>前压盖的轴向长孔总余隙0.40 mm；整件输出骨杆先到位，再安装横向捕获螺钉。薄预紧螺母的键片有0.4 mm薄环和外舌、1.2 mm局部键，不能按单厚激光平片交货。键片需铣薄后成形，折弯量按实际弹簧调整位置配作；每接口独立件号。旧轴横孔不能靠焊填后冒充认证新轴，改孔轴应新制。</p>'+table(['件号','特征','文件','制造说明'],rows))

def docs():
    digest=sha(OUT/'assembly_meshes.npz');inv=load(OUT/'production_parts.json');loads=load(OUT/'verification/preload_retention_loads.json');env=load(OUT/'verification/envelope.json');route=load(OUT/'harness/routes.json');reports=[]
    for p in sorted((OUT/'verification').glob('*.json')):
        r=load(p)
        if isinstance(r,dict) and 'status' in r:reports.append([f'<a href="verification/{p.name}">{p.stem}</a>',esc(r['status']), '当前' if r.get('geometry_sha256')==digest else '无当前几何标记 / 请看范围'])
    printed=[r for r in inv['structural_parts'] if r['printable']]
    body=f'<div class="box"><b>O24E 整机设计交付 · 名义几何与制造准备</b><br>完整高度 {env["height_mm"]:.3f} mm；40机械自由度，80原范围端点；{len(printed)}个连续打印体与1个独立钢制承力体。仍需完成实配、保持力、测角标定与百次循环验收，manufacturing_release=false。</div>'
    body+='<div class="grid">'+''.join(f'<div class="card"><h3>{t}</h3><a href="{u}">{l}</a></div>' for t,u,l in [('检查整机','preview/index.html','交互三维、40轴、路径与逐件动画'),('可编辑装配','O24E_production_assembly.blend','Blender真实分件与姿态时间线'),('打印工程','printing/plates.json','A1 mini分盘清单与原生3MF'),('逐件装配','ASSEMBLY.html','按真实件号的装配教程'),('复用与补购','HARDWARE.html','数量、规格及复用条件'),('定制金属件','MACHINING.html','逐件实体、三视图和参数'),('电子与UE','ELECTRONICS.html','新腕角链、38板42标量与走线'),('验证与实测','TEST_PLAN.html','几何报告与不补紧百次记录')])+'</div>'
    body+='<p>H按用户接受的T5实装与T6继承关系通过；W采用用户已认可的T6双轴腕。没有把重新测试H/W设为开工条件，也没有虚构独立T6 H计数。T6 R的敞口拔出连接未移植。</p>'
    body+='<p>20组金属筒改为“骨杆先套入、横向捕获螺钉后装”。输出骨杆、浮动金属盖和轴由穿栓捕获；固定金属筒再由原固定捕获销连接输入座。高负载单轴保留金属预紧回路并加按载荷配置的碟簧。腰、胸、踝、颈等接口新增完整截面的绕孔叉根；满意外观的主体与骨点保持。</p>'
    body+='<img src="images/front.png" alt="O24E A字完整装配正视"><p><a href="reference/O24D/images/front.png">冻结O24D正视</a> · <a href="images/side.png">O24E侧视</a> · <a href="images/left_arm.png">完整手臂</a> · <a href="O24E_production_assembly.glb">整机GLB</a></p>'
    body+='<h2>当前几何验证</h2>'+table(['报告','结果','指纹'],reports)+f'<p><small>制造网格 SHA256：<code>{digest}</code>。输入冻结凭证：<a href="reference/input_sha256.json">input_sha256.json</a>。验证报告说明有限采样与范围，不能合并成实测性能通过。</small></p>'
    page('START_HERE.html','O24E · 完整装配与防脱改版',body)
    bom=load(OUT/'BOM_totals.json')['counts'];hr=[r for r in inv['hardware'] if r.get('procurement_item',True)]
    rows=[]
    for sku,qty in bom.items():
        ex=next((r for r in hr if r['sku']==sku),None);new=any(r['sku']==sku and r['disposition']=='补购/制作新件' for r in hr)
        dispo='新配 / 变更件' if new else '候选复用，核对尺寸与状态'
        if 'NYLOC' in sku or sku=='NL3' or sku.startswith('E_TAB'):dispo='最终装配用新件；拆卸后按失效/复用规定更换'
        rows.append([esc(sku),qty,dispo,esc(ex['spec'] if ex else '作为已装配组件采购；详见电子原生BOM')])
    page('HARDWARE.html','O24E · 补购与复用清单','<div class="box">下表是本版设计数量，不是用户在手库存。最终补购量＝需求量－核验合格的可复用库存。禁止把原型名义规格相近当作已在手或完全兼容。</div><p>优先复用：合格O22肩钉、W3/W4/FW4、A8（用于已认可腕堆叠）、现有合格轴承、摩擦平垫、未改变的金属压板/隔套、38块原生测角板、载板与线材。新制：修改横孔的轴、浮动前压盖、按接口配作键片、变更的完整打印件；按表补新横向螺钉、锁母和分载碟簧。原样件R不作为整组复用模块。</p><p><a href="HARDWARE_REUSE_BUY.csv">每个实物位置与件号CSV</a> · <a href="PRINT_AND_MACHINING_PARTS.csv">打印/钢体清单</a> · <a href="BOM_totals.json">规格汇总</a>。PCBA焊盘、贴片件和USB外壳显示特征归并在E-B001/E-B002内，不重复作为机械散件采购。</p>'+table(['规格 / SKU','数量','处理','说明'],rows))
    axes=table(['轴','目标保持力矩 N·m','计算夹紧力 N','材料/计算状态'],[(r['axis'],f'{r["hold_target_Nm"]:.5f}',f'{r["required_clamp_N"]:.2f}',r['status']) for r in loads['rows']])
    page('TEST_PLAN.html','O24E · 验证与实物记录','<div class="box">已接受H/W状态继续有效。以下是改版接口与新整机工况的验收项目，当前所有实测字段留空。一次完整往返算一循环，同时记录单程次数；0/10/20/50/100次全程不补紧。</div><ol><li>来料：测肩长、牙长、头径、垫片厚度、碟簧自由高、螺母金属六角与尼龙位置。记录钢材证书与打印批次。</li><li>顺序装配：按教程验证整骨杆轴向套入、横栓后装、固定销先于轴承、螺母入闭合窝。分别留照片。</li><li>捕获负对照：保持螺纹关系不变，正反拉整个输出骨杆；确认金属链与打印件均有挡止。单独受控卸下相应捕获件时应恢复预期拆卸路径。不得以胶、摩擦或尼龙阻力代替挡止。</li><li>预紧：用细线/力计在已知力臂测起动及保持力矩，记录两个方向。按下表目标调到位；核弹簧行程、0.40 mm浮动盖槽及轴承退让。锁固后画见证线。</li><li>循环：0/10/20/50/100次记录力矩、角漂、轴向/径向间隙、螺钉尖端位置、见证线及掉粉。任何补紧都结束本次“不补紧”试验，维修后另开记录。</li><li>整机：A字站立、全部日常动作和原范围端点；检查线弯半径、夹线、USB拉扯和足底打滑。静态站立计算不覆盖外部拖线。</li><li>测角：两腕分别覆盖二维网格，拟合E专用LUT，保留留出点误差、回差、温漂、钢件干扰和噪声；未经标定不得发送为已标定姿态。</li></ol>'+axes+'<p><a href="PHYSICAL_TEST_LOG.csv">空白逐轴试验记录</a>。上述保持力矩来自名义质量、摩擦系数≥0.08、25%质量余量及1.5重力系数的有限工况计算，不是拧紧扭矩或实测额定负载。打印材料许用8 MPa尚需批次验证。无外加负载额定值。</p>')
    with (OUT/'PHYSICAL_TEST_LOG.csv').open('w',encoding='utf-8-sig',newline='') as f:
        w=csv.writer(f);w.writerow(['axis','cycles_full_round_trip','single_strokes','date','operator','build_hash','hold_Nm_plus','hold_Nm_minus','drift_deg','axial_play_mm','radial_play_mm','tip_mm','witness_line','dust','retightened','pass','photo'])
        for ax in PROFILE['axes']:
            for count in [0,10,20,50,100]:w.writerow([ax['id'],count,count*2,'','',digest]+['']*11)
    page('ELECTRONICS.html','O24E · 腕角链、传感器与走线','<p>物理腕序为 <b>Ry(屈伸) × Rx(尺桡偏)</b>，右腕通过diag(1,−1,1)共轭镜像。前臂固定安装钟向只在FK中出现一次。A字为标定中立，N参考只作为坐标基底；不通过骨点平移修补机械偏心。</p><p>保留36个单轴板及2个腕三轴磁场板，共38板、42原始标量、40机械自由度。新腕磁铁跟随第二层输出叉，测角板固定于前臂；每腕需要二维有界场图。旧D腕标定、旧RxRy链和旧46通道固件均不兼容。</p><p><a href="profiles/device_profile.json">设备profile</a> · <a href="profiles/channel_map.json">通道表</a> · <a href="profiles/UE_component_pose_examples.json">完整UE骨架离线姿态</a> · <a href="verification/wrist_observability.json">理想磁场可观测性</a> · <a href="electronics/pcb_reuse_manifest.json">原生PCB复用指纹</a>。</p><p>本版保留原生PCB、灌封六芯尾线与载板连接方式，不新增虚构的板上连接器。电路文件位于electronics/inherited_D。原ERC/DRC记录仅证明原板设计，不能代表新整机测角精度或已经通电。</p><p>走线按当前A姿态重算实体避让，并按有限活动样本的端点距离增加余量。<a href="harness/CABLE_CUTLIST.csv">逐段下料</a> · <a href="harness/routes.json">固定点/路径/弯曲预算</a>。实际服务弯如何弯曲、是否夹线和反复弯折寿命仍需实物检查；不得把端点余量称作动态线束仿真。</p>')
    plates=load(OUT/'printing/plates.json') if (OUT/'printing/plates.json').exists() else {'plates':[]}
    page('PRINTING.html','O24E · 打印工程', '<p>A1 mini 180×180×180 mm，0.4喷嘴、PLA、0.12层高、5壁、100%填充、自动支撑及3 mm裙边/防翘边。方向、件号与独立STL见下面索引。材料和接触面公差尚需首件核验；不要把审查整机GLB作为一个打印物体。</p>'+table(['打印盘','原生工程','切片验证'],[(p['id'],f'<a href="printing/{p["id"]}.3mf">{p["id"]}.3mf</a>',f'<a href="verification/slice_{p["id"]}.json">轨迹/边界检查</a>') for p in plates['plates']])+table(['实体件号','部位','STL','范围mm'],[(r['part_number'],esc(r['label']),f'<a href="{r["stl"]}">独立打印实体</a>',esc(np.round(np.ptp(np.array(r['print_bounds_mm']),axis=0),2))) for r in printed]))
    # Keep the direct link reachable from the entry, not just the JSON plate list.
    p=OUT/'START_HERE.html';p.write_text(p.read_text('utf8').replace('href="printing/plates.json"','href="PRINTING.html"'),encoding='utf8')
    p=OUT/'HARDWARE.html';p.write_text(p.read_text('utf8').replace('</main>',f'<p>新增单轴碟簧按 <a href="{SOURCE_URL}">SCHNORR官方产品目录</a>第11页名义数据选型，并在容量检查中使用−7.5%力值公差。串联增加行程、同向套叠增加力。目录参数不代表现有A8的实测曲线，渲染压缩量不能当作拧紧设定。</p></main>'),encoding='utf8')
    p=OUT/'ELECTRONICS.html';p.write_text(p.read_text('utf8').replace('</main>','<p><a href="profiles/sensor_entries.json">38板和尾线的装入方向</a> · <a href="verification/sensor_assembly.json">板件/磁铁入口检查</a> · <a href="electronics/calibration_template.json">待实测标定模板</a> · <a href="verification/protocol_guard.json">旧格式和未标定数据拒收检查</a>。腕板每侧用两条0.12×0.8×8 mm PET支承片，随后装宽垫压片；这些薄片已计入实物清单。</p><p>protocol_reference.py是主机接口参考，配合cad/revO24E源目录运行。当前未烧录固件、未连接UE运行时；原生PCB继承与离线骨链验证不等同于已通电验收。</p></main>'),encoding='utf8')

def manifest():
    source=OUT/'source';source.mkdir(exist_ok=True)
    diagnostics={'core_locations.py','diagnose_paths.py','diagnose_stl.py','material_revision.py'}
    for p in [*HERE.glob('*.py'),HERE/'README.md']:
        if p.name not in diagnostics:shutil.copyfile(p,source/p.name)
    files=[]
    for p in sorted(OUT.rglob('*')):
        if not p.is_file() or p.name in ['manifest.json','O24E_delivery.zip'] or 'slicer_work' in p.parts:continue
        files.append(dict(path=p.relative_to(OUT).as_posix(),sha256=sha(p),bytes=p.stat().st_size))
    put(OUT/'manifest.json',dict(revision='O24E',geometry_sha256=sha(OUT/'assembly_meshes.npz'),manufacturing_release=False,files=files,old_baseline_unchanged=sha(BASE/'assembly_meshes.npz')=='fd64f061821a42f803e2131b0f0642147ab9cc8e65dc32cdb5e3476a0b7c9e8e'))
    with zipfile.ZipFile(OUT/'O24E_delivery.zip','w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
        for row in files:z.write(OUT/row['path'],'O24E/'+row['path'])
        z.write(OUT/'manifest.json','O24E/manifest.json')
    with zipfile.ZipFile(OUT/'O24E_delivery.zip') as z:assert z.testzip() is None
    print('DELIVERY',len(files),flush=True)
if __name__=='__main__':
    if len(sys.argv)>1:globals()[sys.argv[1]]()
    else:assembly();machining();docs()
