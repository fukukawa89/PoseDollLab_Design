from build_stock import *
import base64,html,shutil,re,zipfile
from collections import Counter
from export_stock import LABELS
sys.path.insert(0,str(H/'cad/revO24E_LArm_Mech'));import extract_arm as old
old.OUT=OUT
esc=html.escape;table=old.table;page=old.page
def csvfile(name,fields,rows):
 with (OUT/name).open('w',encoding='utf-8-sig',newline='') as f:
  w=csv.DictWriter(f,fieldnames=fields,extrasaction='ignore');w.writeheader();w.writerows(rows)

def inventory():
 kit=load(OUT/'kit.json');p=load(OUT/'production_assembly.json');parts={r['name']:r for r in p['parts']}
 for r in kit['hardware']:
  r['spec']=SPECS[r['sku']];r['custom_or_secondary_operation']=False
  if r['feature'] in ['KEEP_E-H1172','KEEP_E-H1173']:r['notes']='两片平垫均放在掌部螺钉头下，按 S 版教程；不是左右各一片。'
  parts[r['feature']]['note']=r['notes']
 put(OUT/'kit.json',kit);put(OUT/'production_assembly.json',p)
 source={'AX4':'O22 原清单 / T6','A8':'O22 原清单 / T6；弹力曲线未测','FW4':'O22 原清单 / T6','W4':'O22 原清单 / T6','M2x20':'O22 原清单 / T6','W3':'T6 专用薄反力垫规格','NL3':'T6 锁固规格；O22 普通 N3 不可替代','W2':'T6 / 既有0.5 mm平垫','W6L':'交接记录中的既有1.5 mm大平垫；另核外/内径','M3x16':'常见成品长度；没有库存时补齐','NL2':'常见 M2 尼龙锁母；普通 N2 不可替代'}
 t6={r['编号']:int(r['三样件共用一套数量']) for r in csv.DictReader((T6/'BOM.csv').read_text('utf-8-sig').splitlines())};counts=Counter(r['sku'] for r in kit['hardware']);rows=[]
 for sku,n in counts.items():rows.append(dict(sku=sku,required=n,spec=SPECS[sku],reuse_source=source[sku],one_T6_set_quantity=t6.get(sku,0),difference_vs_one_T6_set=max(0,n-t6.get(sku,0)),verified_on_hand='',buy_quantity='',part_numbers='; '.join(r['part_number'] for r in kit['hardware'] if r['sku']==sku)))
 csvfile('HARDWARE_REUSE_BUY.csv',list(rows[0]),rows);csvfile('HARDWARE_DETAIL.csv',['part_number','feature','sku','quantity','spec','notes'],kit['hardware'])
 csvfile('PRINT_PARTS.csv',['part_number','kit_label','quantity','stl','sha256','reuse_unchanged_stl','process'],kit['structural_parts'])
 previous=[r for r in load(SRC/'kit.json')['hardware'] if r['custom_or_secondary_operation']];assert len(previous)==55
 csvfile('OLD_CUSTOM_55.csv',['part_number','feature','sku','quantity','spec'],previous)
 put(OUT/'BOM_totals.json',dict(printed_bodies=12,hardware_pieces=sum(counts.values()),sku_count=len(counts),custom_metal_count=0,cut_hardware_count=0,rows=rows,inventory_on_hand='UNKNOWN; historical design quantities are not stock quantities'))
 put(OUT/'previous_custom_items.json',previous)

def tutorial():
 kit=load(OUT/'kit.json');by={r['feature']:r for r in kit['structural_parts']+kit['hardware']};modules=[];seen=set();rollmods={};ints=load(OUT/'interfaces.json');reports=load(OUT/'verification/capture_assembly.json')['rows']
 def module(id,label):
  m=dict(id=id,label=label,steps=[],context=[]);modules.append(m);return m
 def step(m,names,title,note,vec=(0,0,0),travel=0,waypoints=None):
  names=names if isinstance(names,list) else [names];ids=[by[n]['part_number'] for n in names];fresh=[n for n in ids if n not in seen];seen.update(ids)
  m['steps'].append(dict(number=len(m['steps'])+1,title=title,feature=' / '.join(names),part_numbers=ids,new_part_numbers=fresh,note=note,entry_world_A=list(vec),animation_travel_mm=travel,animation_waypoints_world_A=waypoints,animation_scope='Nominal assembly at zero adjustable angles; movement is an illustration of the reported module path.'))
  m['context']=list(dict.fromkeys(m['context']+ids))
 for idx,(r,report,fn,on,label) in enumerate(zip(ints['rolls'],reports,['ROOT','SHOULDER_ABDUCT','ELBOW_OUTPUT'],['SHOULDER_PITCH','UPPER_ARM','FOREARM'],['肩俯仰模块','上臂旋转模块','前臂旋转模块']),1):
  pre=r['id'];W=np.array(r['W']);m=module(pre,f'0{idx} 先组装 {label}');step(m,fn,'准备连续固定座',LABELS[fn]+'；清理入口和完整六角窝。此模块先在台面单独组装。')
  for path in report['assembly_paths']:
   n=path['part'];vec=(-W[:3,2]).tolist();travel=24;wp=None
   if n==r['keeper']:
    names=[n]+[pre+f'_lid_nut_{x}' for x in [-r['lug_x_mm'],r['lug_x_mm']]]
    step(m,names,'准备压盖、两颗锁母并装到固定座','在压盖尚未装上时，将两颗 NL3 从前侧放入完整六角窝，尼龙朝螺钉将露出的前侧。托住锁母，再将压盖罩住已放好的 18 mm 大平垫；不得把大平垫遗漏。',vec,24)
    for x in [-r['lug_x_mm'],r['lug_x_mm']]:
     step(m,pre+f'_lid_washer_{x}','压盖螺钉头下 W3','每边一片 7×3.2×0.5；从固定座后侧轴向放入。',W[:3,2],24)
     step(m,pre+f'_lid_bolt_{x}','锁住防脱压盖：M3×16','整根螺钉从后侧装入，用 2.5 mm 内六角拧入已捕获 NL3。两边交替贴合，检查尖端完全穿过尼龙；这里只锁压盖，不调关节摩擦。',W[:3,2],24)
    continue
   notes={'_N':'NL3 尼龙端先进入座深处，金属端朝入口；完整六角窝止转。','_RW':'7×3.2×0.5 薄反力垫贴锁母金属端。不可换成 O22 的 9×3.2×0.8。','_BACK_W4':'9×4.3×0.8 支承垫，给大垫内孔提供金属跨接。','_ANCHOR':'18×6.4×1.5 大平垫放进圆形浅座；这片金属大垫是轴向挡止件，不是普通可省略垫片。','_F1':'内侧 12×4.3×1 摩擦垫，光滑面朝打印转子。','_F2':'外侧 12×4.3×1 摩擦垫，光滑面朝打印转子。','_HW':'头下 9×4.3×0.8 平垫。','_AX':'Φ4×8／M3×6 肩钉整根从中心装入通道穿入；3 mm 内六角。先正常旋入金属牙，再通过尼龙锁固段；不要用肩部顶住小孔垫片代替弹簧预紧。先低预紧检查转动，后调保持力。'}
   note=next((v for suffix,v in notes.items() if n.endswith(suffix)),LABELS.get(n,'安装对应实物件。'))
   if '_A8_' in n:note=('本关节 4 片：每 2 片同向套叠为一组，两组的内孔凸缘相对，构成并联×2、串联×2。' if r['parallel']==2 else '本关节 2 片：内孔凸缘相对；不能同向套叠。')+' 由靠转子的一组开始，依本步件号顺序放入。'
   if n==on:note='将完整输出骨杆沿轴线套入。先前已经锁住的压盖留在固定座上；转子细颈进入盖孔，转子不得压住盖的环唇。'
   if 'side entry angle' in path['direction']:
    nums=re.findall(r'\d+',path['direction']);angle,depth=map(int,nums[:2]);d=np.array([math.cos(math.radians(angle)),math.sin(math.radians(angle)),0.]);wp=[(W[:3,:3]@(d*40+[0,0,-depth])).tolist(),(W[:3,:3]@np.array([0,0,-depth])).tolist(),[0,0,0]]
    note+=' 从骨杆两肋间的侧窗送入，再向关节推到位，见分段动画；不要从远端硬顶过叉桥。'
   if n.endswith('_AX'):travel=50
   step(m,n,by[n].get('sku') or LABELS.get(n,n),note,vec,travel,wp)
  rollmods[pre]=[r['feature'] for r in kit['structural_parts']+kit['hardware'] if by[r['feature']]['part_number'] in m['context']]
  step(m,[pre+'_AX',r['keeper']],'检查预紧、锁固与防脱','压盖的两颗螺钉均已锁紧后，托住骨杆轻推/拉，确认大平垫被前环唇与后座两面捕获。'+('四片碟簧总高先取1.8 mm，工作区间1.7～2.0 mm。' if r['parallel']==2 else '两片碟簧总高先取1.0 mm，工作区间0.9～1.2 mm。')+' 不压平碟簧；尖端露出完整牙，记录见证线。')
 for idx,(r,fn,on,fixedgroup,movinggroup,label) in enumerate(zip(ints['hinges'],['SHOULDER_PITCH','UPPER_ARM'],['SHOULDER_ABDUCT','ELBOW_OUTPUT'],['RP','RU'],['RU','RF'],['连接肩外展','连接肘']),4):
  m=module(r['id'],f'0{idx} {label}');pre=r['id'];M=np.array(r['M']);step(m,rollmods[fixedgroup],'取已完成的旋转模块','同一件号继续使用，不重复取料；此阶段可调轴置0°，最后再回 A 字。')
  for side,tag in [(-1,'HL_'),(1,'HR_')]:
   direction=M[:3,:3]@np.array([0,side,0])
   for suf,txt in [('N','尼龙朝深处，金属面朝外，先对齐完整六角窝。'),('RW','薄 W3 贴锁母金属端。'),('K1','第一片内置 W4。'),('K2','第二片内置 W4，合计1.6 mm。'),('F1','内摩擦大垫，光滑面朝转动耳。')]:step(m,pre+'_'+tag+suf,'准备固定叉 '+tag+suf,txt,direction,25)
  step(m,rollmods[movinggroup],'合上已装好的下游旋转模块','两侧摩擦耳与固定叉同轴，先不装肩钉；R 模块已经在台面完成，所以不用在封闭后再穿入 R 肩钉。',-M[:3,2],45)
  for side,tag in [(-1,'HL_'),(1,'HR_')]:
   direction=M[:3,:3]@np.array([0,side,0]);springs=sorted(['S1','S2'],key=lambda s:float(np.mean(e.bounds(moved(ts(tag+s),M)),axis=0)@direction))
   for suf in ['F2']+springs+['HW','AX']:
    n=pre+'_'+tag+suf;step(m,n,'外侧 '+by[n]['sku'],by[n]['notes']+' 两侧逐步、交替调节；两片 A8 相对串联。',direction,25)
  step(m,fn,'检查本关节','沿用已接受的 T6 H 摩擦耳和金属堆叠。低预紧走完整范围，确认肩钉穿过尼龙、完整六角窝止转，再按整臂保持目标调整；不把重新验收 H 当成开工条件。')
 # Use the measured module insertion order: all inner washers precede fork closure.
 m=module('W','06 双轴腕和手掌');step(m,rollmods['RF'],'准备前臂固定叉','从已完成的前臂模块开始。')
 W=F0['l_wrist_flex'];wp={r['feature']:'KEEP_'+r['part_number'] for r in load(SRC/'kit.json')['hardware'] if r['feature'].startswith('l_E_W')};prepared=['KEEP_E-P019']
 step(m,'KEEP_E-P019','在台面准备腕中心件','四个方向的内层五金全部准备完毕后再合叉；此时不要先把前臂叉封住入口。')
 for prefix,axis in [('WYM_',-W[:3,1]),('WYP_',W[:3,1]),('WXM_',-W[:3,0]),('WXP_',W[:3,0])]:
  for suffix,txt in [('N','NL3 尼龙向深处，金属面朝入口；完整六角窝止转。'),('RW','W3薄反力垫贴锁母金属面。'),('K1','第一片内置W4。'),('K2','第二片内置W4，合计1.6 mm。'),('F1','内FW4，光滑面朝随后装入的3 mm叉耳。')]:
   n=wp['l_E_'+prefix+suffix];prepared.append(n);step(m,n,'腕中心 '+prefix+suffix,txt,axis,25)
 step(m,prepared,'将已备好内层五金的中心件放入前臂叉','托住垫片，中心件从前臂叉的远端开放口装入。此时不再往叉耳背面补塞大垫片。',-W[:3,2],50)
 step(m,'KEEP_E-P018','合上第二轴输出叉','从掌部一端装入，两个叉耳与X轴摩擦面同轴。',-W[:3,2],50)
 for prefix,axis in [('WYM_',-W[:3,1]),('WYP_',W[:3,1]),('WXM_',-W[:3,0]),('WXP_',W[:3,0])]:
  def spring_depth(suf):
   pn=wp['l_E_'+prefix+suf].removeprefix('KEEP_');solid=moved(es(pn),F0[EP[pn]['frame']]);return float(np.mean(e.bounds(solid),axis=0)@axis)
  springs=sorted(['S1','S2'],key=spring_depth)
  for suffix in ['F2']+springs+['HW','AX']:
   n=wp['l_E_'+prefix+suffix];note=by[n]['notes']+' A8两片内孔凸缘相对，先放深处那片；每个肩钉独立、逐步调节，不压平碟簧。'
   step(m,n,'腕外侧 '+prefix+suffix,note,axis,25)
 step(m,'KEEP_E-P017','套入掌部方键','掌部外观保持；锁母入口和头下垫片孔道已修正，此件须重打。',-W[:3,2],35)
 for pn,note,sign in [('KEEP_E-H1174','M2 NL2 从负X端进完整六角窝；金属面朝掌部承压台阶，尼龙向外。',-1),('KEEP_E-H1172','第一片5×2.2×0.5放螺钉头侧。',1),('KEEP_E-H1173','第二片也在螺钉头侧，与上一片叠放；不能再装在锁母侧。',1),('KEEP_E-H1171','O22/T6 的 M2×20 整根使用；1.5 mm 内六角。穿过方键并拧入捕获 NL2，尖端名义露出3.5 mm。不用剪螺钉。',1)]:step(m,pn,'掌部 '+by[pn]['sku'],note,W[:3,0]*sign,30)
 allids={r['part_number'] for r in kit['structural_parts']+kit['hardware']};assert seen==allids,(allids-seen)
 put(OUT/'tutorial/steps.json',dict(modules=modules,steps=sum(len(m['steps']) for m in modules),covered_part_numbers=sorted(seen),assembly_angles={a['id']:0 for a in PROFILE['axes']},scope='Prepare RP/RU/RF separately first, then join H, then W. Repeated IDs are already assembled subassemblies. Forearm -90 degree zero clocking remains in FK.'))

def preview():
 from preview import ASSEMBLY_JS
 parts=load(OUT/'production_assembly.json')['parts'];kit=load(OUT/'kit.json');z=np.load(OUT/'production_meshes.npz');packed=[];cursor=0
 for p in parts:
  i=str(p['i']);v=z[i+'v'];f=z[i+'f'];m=trimesh.Trimesh(v,f,process=False);ar=np.concatenate([v[f],np.repeat(m.face_normals[:,None,:],3,axis=1)],axis=2).reshape(-1,6).astype('<f4');p['source_features']=[p['name'],p['label']];p['name']=p['part_number'];p.update(first=cursor,count=len(ar),color=e.COLORS.get(p['role'],[.6,.6,.6]));cursor+=len(ar);packed.append(ar)
 motion=load(OUT/'verification/motion.json');assert motion['geometry_sha256']==sha(OUT/'production_meshes.npz') and motion['status']=='PASS_SAMPLED'
 audit={r['pose']:dict(count=r['count'],pairs=r['collisions'],advisory_count=r['advisory_count'],advisory_pairs=r['advisory_pairs'],affected=[]) for r in motion['cases']};t=load(OUT/'tutorial/steps.json')
 payload=dict(profile=PROFILE,parts=parts,poses=POSES,geometry=base64.b64encode(np.vstack(packed).tobytes()).decode(),height=load(OUT/'envelope.json'),geometry_sha256=sha(OUT/'production_meshes.npz'),production_mesh_sha256=sha(OUT/'production_meshes.npz'),ueBones=[],harness=[],paths={},audit=audit,contexts={},expectedFrames={n:{fr:M.tolist() for fr,M in frames(p['angles']).items()} for n,p in POSES.items()},assembly=t['modules'],assemblyAngles=t['assembly_angles'])
 (OUT/'preview/data.js').write_text('window.O24D='+json.dumps(payload,ensure_ascii=False,separators=(',',':'))+';',encoding='utf8')
 view=(SRC/'preview/viewer.js').read_text('utf8').replace('原 O24E 相同姿态的相邻干涉记录：0 对。','本版生产 STL 相邻干涉：0 对。').replace('O24E_LArm_Mech','O24E_LArm_Stock').replace('l_wrist|l_e_w|l_palm','l_wrist|forearm|keep_e-p01[789]|keep_e-h11');(OUT/'preview/viewer.js').write_text(view,encoding='utf8');shutil.copyfile(SRC/'preview/style.css',OUT/'preview/style.css')
 js=ASSEMBLY_JS.replace('state.angles={...D.poses.neutral.angles};','state.angles={...D.assemblyAngles};').replace("$('#harness').checked=true;$('#bones').checked=true;","$('#harness').checked=false;$('#bones').checked=true;")
 js=js.replace('for(let p of s.part_numbers)state.offsets[p]=s.entry_world_A.map(x=>x*d);',"let pts=s.animation_waypoints_world_A,off=s.entry_world_A.map(x=>x*d);if(pts){let u=t*(pts.length-1),j=Math.min(pts.length-2,Math.floor(u)),f=u-j;off=pts[j].map((x,k)=>x*(1-f)+pts[j+1][k]*f)}for(let p of s.part_numbers)state.offsets[p]=off;")
 js+='\nwindow.ARM_SELF_CHECK=window.O24E_SELF_CHECK;window.ARM_ASSEMBLY_CHECK=window.O24E_ASSEMBLY_CHECK;';(OUT/'preview/assembly.js').write_text(js,encoding='utf8')
 text=(SRC/'preview/index.html').read_text('utf8').replace('O24E · 左臂机械试装','O24E · 常见五金左臂试装').replace('LEFT ARM MECHANICAL TRIAL','LEFT ARM / COMMON HARDWARE').replace('<strong>9</strong>','<strong>12</strong>').replace('E-P003','S-P004').replace('E-P006','S-P009').replace('O24E_left_arm_mechanical','O24E_left_arm_stock').replace('原 O24E 生产分件与尺寸。PCB、磁铁、线束和专用固定件已剔除。','优先复用 O22 / T6 常见五金；零金属定制、零切短。无电路。').replace('姿态几何依据来自原 O24E；实际打印、组装与保持效果待测。','本版实际 STL 已检查活动范围；实装保持力与循环待测。').replace('装配路径依据见原几何报告。','装配时可调轴置0°；侧窗步骤分两段移动。')
 (OUT/'preview/index.html').write_text(text,encoding='utf8')

def docs():
 kit=load(OUT/'kit.json');bom=load(OUT/'BOM_totals.json');plates=load(OUT/'printing/plates.json')['plates'];t=load(OUT/'tutorial/steps.json');env=load(OUT/'envelope.json');targets=load(OUT/'verification/holding_targets.json')['rows']
 body=f'<div class="box"><b>肩关节到手掌，7 自由度；12 个打印件、134 件标准五金、{len(plates)} 个打印盘。</b><br>优先复用 O22 / T6 的常见规格。金属定制件 0，切短/钻孔五金 0。估算本单臂质量 {env["estimated_mass_g"]:.1f} g，不含外部夹具。</div>'
 body+='<p>这是独立的常见五金试装改版。需要使用这里的新打印件，不能把这份五金清单直接塞入旧 O24E 的金属筒版。原 O24E 和原单臂包均保留；本包无电路、磁铁或线束。</p>'
 body+='<div class="grid">'+''.join(f'<div class="card"><a href="{link}"><b>{label}</b></a><br>{note}</div>' for link,label,note in [('HARDWARE.html','先核对五金','O22/T6复用、需求量和库存空栏'),('PRINTING.html','打印这12件','独立STL、A1 mini原生3MF'),('ASSEMBLY.html','按步骤组装','先三个旋转模块，再肩、肘、双轴腕'),('preview/index.html','检查三维装配','七轴摆姿、逐件显示、侧窗装入动画'),('CHANGES.html','旧55件加工项如何取消','具体件号、规格及替代方式'),('TEST_PLAN.html','记录实际效果','预紧、保持力、间隙、拉拔和循环')])+'</div>'
 body+='<p><a href="O24E_left_arm_stock.blend">可编辑 Blender</a> · <a href="O24E_left_arm_stock.glb">GLB</a> · <a href="HARDWARE_REUSE_BUY.csv">复用与补购表</a></p><img src="images/arm.png" alt="常见五金单臂">'
 body+='<div class="box warn">R 新增 18 mm 金属大垫与双螺钉固定压盖，形成独立的双向轴向挡止。碟簧提供弹性预紧，完整六角窝限制锁母转动，尼龙圈负责螺纹防松。三者分别承担功能。H/W 已接受状态继续有效；本单臂的新载荷、PLA 蠕变与100次免补紧尚未实测。</div>'
 body+='<p>保持 UE 的7条有效轴线、83.5662 mm上臂骨长、80.4963 mm前臂骨长、A字肩外展45°和原日常活动范围。为标准件入口调整了局部压盖和双肋：前臂盖宽47.6 mm，另两盖宽39.6 mm；手掌仅修改紧固孔道和台阶。这里没有重新拼装整机，故不把原整机557.55 mm高度冒充新整机测量值。</p>'
 reports=['stl_export','connected_core','capture_assembly','hinge_wrist_paths','module_joining','motion','motion_dense','holding_targets']
 body+=table(['检查','本版记录'],[(f'<a href="verification/{n}.json">{n}</a>',esc(load(OUT/f'verification/{n}.json')['status'])) for n in reports]);page('START_HERE.html','O24E · 常见五金单臂试装版',body)
 body='<p>按一只左臂，不含备件。历史 O22/T6 清单只能证明规格来源，不能证明你还有多少库存。填写“已核实库存”后再计算补购；不会代你下单。</p>'
 body+=table(['规格','需求','具体尺寸','复用来源','相对一整套 T6 H/R/W 的缺口'],[(r['sku'],r['required'],esc(r['spec']),esc(r['reuse_source']),r['difference_vs_one_T6_set']) for r in bom['rows']])
 body+='<p><a href="HARDWARE_REUSE_BUY.csv">可填写的复用/补购CSV</a> · <a href="HARDWARE_DETAIL.csv">134个实际位置明细</a></p><div class="box warn">不能互换：O22 的普通 N3/N2 ≠ NL3/NL2；9×3.2×0.8 ≠ T6 的7×3.2×0.5；M4孔4.3的垫片 ≠ M3孔3.2。大平垫只按18×6.4×1.5使用，1.6厚不能直接混装。肩钉须同时符合光杆Φ4×8和M3螺纹长6，不是普通M3螺钉。</div>'
 body+='<p>优先挑平整、无毛刺、尺寸合格的旧件；尼龙圈失效或碟簧已永久压平的旧件不算可复用。A8 外形一致不等于弹力相同，实物持姿仍须测量。另备3 mm、2.5 mm、1.5 mm内六角、卡尺、见证线笔、软夹垫和力计；本版不依靠胶水防脱。</p>';page('HARDWARE.html','常见五金 · 需求与复用',body)
 body='<p>旧抽取包中需要定制或二次处理的五金共有55件；不是所有162件都要加工。下面按功能列明，逐件规格见 <a href="OLD_CUSTOM_55.csv">旧55件明细</a>。</p>'
 body+=table(['旧结构','数量','具体加工内容','本版替代'],[('三组筒式旋转接口',15,'3六角金属筒＋3有头横孔轴＋3后承压盖＋3浮动前盖＋3成形锁片','连续打印座/转子＋既有肩钉＋大垫/压盖捕获'),('肩外展、肘双压板接口',16,'4成形304槽形压板＋2六角压缩芯＋4键式转子盖＋4横孔挡圈＋2根截短钻孔Φ4轴（29/37 mm）','沿用T6 H一体叉和肩钉、标准垫片、碟簧、NL3'),('须切短的螺钉',7,'M2×20→14.90×1；M3×20→18×1、→17×1；M3×45→43.67×2；M3×35→34.44×2','整根肩钉、M3×16、M2×20'),('须下料的弹性销',9,'Φ1.5×7件、Φ2×2件，各按旧接口长度截断','不用横销，改用独立锁住的压盖及捕获锁母'),('须下料的钢管',8,'外径5.5/内径3.2，按旧压板堆叠长度下料','标准厚度平垫组合')])
 body+='<p>新方案保留骨长、轴线、七轴顺序和双轴腕。变化是取消上述机加工承力回路，改成适合首轮单臂试装的连续打印件；不能继承原金属筒版的承载额定结论。两件腕打印件 S-P011/S-P012 的 STL 与旧 E-P018/E-P019 逐字节相同，可直接复用；其余10件采用新STL，包括掌部。</p>'
 body+='<p>掌部改用 O22 的 M2×20整根；两片0.5 mm垫片都放头下。锁母侧新建承压台阶、贯通六角入口，正面开通垫片及工具入口。前臂压盖两孔外移至±20 mm，避开肘转动叉，保证整根M3×16能从后侧装入。</p>'
 page('CHANGES.html','原加工项与标准件替代',body)
 body='<div class="box">每件号1件。推荐先完成整只单臂；若已有旧腕件，可从工程中取消 S-P011 和 S-P012，其余件不要混用旧金属筒版。0.4 mm喷嘴、PLA、0.12 mm层高、5壁、100%填充、自动支撑、3 mm裙边。</div>'
 body+=table(['打印盘','工程','离线核对'],[(p['id'],f'<a href="{p["file"]}">原生3MF</a>',f'<a href="verification/slice_{p["id"]}.json">{p["count"]}件 / 零网格修复 / 挤出边界</a>') for p in plates])
 body+=table(['件号','名称','STL','尺寸 mm','可复用旧件'],[(r['part_number'],r['kit_label'],f'<a href="{r["stl"]}">独立生产STL</a>',' × '.join(f'{x:.1f}' for x in np.ptp(r['print_bounds_mm'],axis=0)),r['source'] if r['reuse_unchanged_stl'] else '重打') for r in kit['structural_parts']])
 body+='<p>支撑清理重点：压盖环唇、六角窝、中心穿钉孔、侧窗与叉内。不可把整个零件缩放来修配孔径；先量孔并记录误差。parts_assembly为装配局部坐标STL，打印用stl_print或3MF。离线切片通过不代表打印强度和配合实测通过。</p>';page('PRINTING.html','单臂打印工程与真实分件',body)
 body='<div class="box">顺序：单独装好 RP、RU、RF → 连接肩外展 HS → 连接肘 HE → 双轴腕 → 手掌。需要拿取的物料始终只有12个打印件和134个五金；重复件号指已经完成的同一总成。</div><p>装配阶段可调角度置0°，前臂内置-90°钟向保留。组装后回到肩外展45°的A字参考。<a href="preview/index.html#assembly">打开逐件三维与侧窗分段动画</a>。</p>'
 for m in t['modules']:body+='<details><summary>'+m['label']+f' · {len(m["steps"])}步</summary>'+table(['步','件号 / 动作','操作与方向'],[(s['number'],'<b>'+', '.join(s['part_numbers'])+'</b><br>'+esc(s['title']),esc(s['note'])) for s in m['steps']])+'</details>'
 body+='<p>R预紧回路：肩钉头 → W4 → A8 → 外FW4 → 打印转子耳 → 内FW4 → 18 mm大垫 → W4 → W3 → NL3。标准平垫之间也是串联摩擦界面，不能只用12 mm大垫半径估算保持力。压盖两颗螺钉负责捕获，和中间调预紧的肩钉分开。</p><a href="images/roll_section.png"><img src="images/roll_section.png" alt="RP真实生产截面与防脱预紧路径"></a><p>拆卸先托住下游，卸载并松开预紧；需要拆掉旋转芯时才解除压盖。不要在压盖未锁好时做拉拔判断。</p>';page('ASSEMBLY.html','逐件装配与明确锁固',body)
 body='<div class="box">H/W的用户接受状态保留。以下测试针对这次单臂集成后的实际效果，不要求先重新验收H/W才开始打印。保持力目标是关节输出力矩，不是拧螺钉的扭矩。</div>'
 body+=table(['轴','范围 °','空载保持目标 N·m','按假定摩擦估计的单堆叠轴向力 N'],[(r['label'],str(r['limits_deg']),f'{r["hold_target_Nm"]:.4f}',f'{r["required_axial_force_per_stack_N"]:.1f}') for r in targets])
 body+='<p>目标按本版网格质量、25%质量余量及1.5保持系数计算，未给手持载荷额定值。摩擦系数0.15、串联接触有效半径2.6 mm仅为计算假设，A8弹力曲线未测；肩俯仰采用4片碟簧（两片并联为一组，两组串联），增加所需轴向力的可用余量，不能把它写成已达到目标。</p><ol><li>清理支撑、量孔并检查各标准件尺寸；记录是否能按教程无强压装入。</li><li>低预紧下检查三盖已锁住、大垫已捕获；托住下游缓慢做正反轴向轻拉。可先以5 N为试验目标，记录实际施力、位移和是否开裂；这不是已验证的额定拉力。</li><li>分别走完七轴范围，再做前伸、侧举、屈肘、近头和腕端姿态。记录碰擦、卡点、间隙及邻轴串动。</li><li>用软垫夹持 S-P004 输入握持座，或先手持；不要夹薄叉耳。测起动力矩与两向保持力矩，水平悬臂观察60秒，并区别夹具滑移与关节角漂。</li><li>往返0/10/20/50/100次记录间隙、保持力、见证线与磨屑。目标100次免补紧；若中途补紧，保留失败记录并另开新轮。不要压平碟簧来掩盖保持力不足。</li></ol><p><a href="TRIAL_LOG.csv">空白逐轴记录表</a> · <a href="verification/holding_targets.json">计算参数与适用范围</a></p>';page('TEST_PLAN.html','单臂实际效果记录',body)
 if not (OUT/'TRIAL_LOG.csv').exists():csvfile('TRIAL_LOG.csv',['axis','label','cycles','date','print_batch','fit_notes','spring_pack_height_mm','hold_plus_Nm','hold_minus_Nm','drift_60s_deg','axial_pull_N','axial_play_mm','radial_play_mm','witness_line','dust','retightened','result'],[dict(axis=a['id'],label=a['label'],cycles=n) for a in PROFILE['axes'] for n in [0,10,20,50,100]])

if __name__=='__main__':
 inventory();tutorial();preview();docs();print('DOCUMENTED',load(OUT/'tutorial/steps.json')['steps'],'steps',flush=True)
