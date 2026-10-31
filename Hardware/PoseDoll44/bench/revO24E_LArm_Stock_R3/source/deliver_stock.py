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
 put(OUT/'BOM_totals.json',dict(printed_bodies=11,hardware_pieces=sum(counts.values()),sku_count=len(counts),custom_metal_count=0,cut_hardware_count=0,rows=rows,inventory_on_hand='UNKNOWN; historical design quantities are not stock quantities'))
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
 step(m,'KEEP_E-P018','装入一体腕叉与手掌','整件从掌部一端装入，两个叉耳与X轴摩擦面同轴；手掌已连为一体，不再单独装掌部螺钉。',-W[:3,2],50)
 for prefix,axis in [('WYM_',-W[:3,1]),('WYP_',W[:3,1]),('WXM_',-W[:3,0]),('WXP_',W[:3,0])]:
  def spring_depth(suf):
   pn=wp['l_E_'+prefix+suf].removeprefix('KEEP_');solid=moved(es(pn),F0[EP[pn]['frame']]);return float(np.mean(e.bounds(solid),axis=0)@axis)
  springs=sorted(['S1','S2'],key=spring_depth)
  for suffix in ['F2']+springs+['HW','AX']:
   n=wp['l_E_'+prefix+suffix];note=by[n]['notes']+' A8两片内孔凸缘相对，先放深处那片；每个肩钉独立、逐步调节，不压平碟簧。'
   step(m,n,'腕外侧 '+prefix+suffix,note,axis,25)
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
 view=(SRC/'preview/viewer.js').read_text('utf8').replace('原 O24E 相同姿态的相邻干涉记录：0 对。','本版生产 STL 相邻干涉：0 对。').replace('O24E_LArm_Mech','O24E_LArm_Stock_R3').replace('l_wrist|l_e_w|l_palm','l_wrist|forearm|keep_e-p01[789]|keep_e-h11');(OUT/'preview/viewer.js').write_text(view,encoding='utf8');shutil.copyfile(SRC/'preview/style.css',OUT/'preview/style.css')
 js=ASSEMBLY_JS.replace('state.angles={...D.poses.neutral.angles};','state.angles={...D.assemblyAngles};').replace("$('#harness').checked=true;$('#bones').checked=true;","$('#harness').checked=false;$('#bones').checked=true;")
 js=js.replace('for(let p of s.part_numbers)state.offsets[p]=s.entry_world_A.map(x=>x*d);',"let pts=s.animation_waypoints_world_A,off=s.entry_world_A.map(x=>x*d);if(pts){let u=t*(pts.length-1),j=Math.min(pts.length-2,Math.floor(u)),f=u-j;off=pts[j].map((x,k)=>x*(1-f)+pts[j+1][k]*f)}for(let p of s.part_numbers)state.offsets[p]=off;")
 js+='\nwindow.ARM_SELF_CHECK=window.O24E_SELF_CHECK;window.ARM_ASSEMBLY_CHECK=window.O24E_ASSEMBLY_CHECK;';(OUT/'preview/assembly.js').write_text(js,encoding='utf8')
 text=(SRC/'preview/index.html').read_text('utf8').replace('O24E · 左臂机械试装','O24E · 常见五金左臂试装').replace('LEFT ARM MECHANICAL TRIAL','LEFT ARM / COMMON HARDWARE').replace('<strong>9</strong>','<strong>12</strong>').replace('E-P003','S3-P004').replace('E-P006','S3-P009').replace('O24E_left_arm_mechanical','O24E_left_arm_stock_R3').replace('原 O24E 生产分件与尺寸。PCB、磁铁、线束和专用固定件已剔除。','优先复用 O22 / T6 常见五金；零金属定制、零切短。无电路。').replace('姿态几何依据来自原 O24E；实际打印、组装与保持效果待测。','本版实际 STL 已检查活动范围；实装保持力与循环待测。').replace('装配路径依据见原几何报告。','装配时可调轴置0°；侧窗步骤分两段移动。')
 (OUT/'preview/index.html').write_text(text,encoding='utf8')
