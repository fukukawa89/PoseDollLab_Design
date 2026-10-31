from deliver_stock import *

def finish():
 inventory();tutorial();preview();docs()
 replacements={
 '无电路。':'机械试装不装电子元件；电子空间预留见专页。',
 '本包无电路、磁铁或线束。':'本次试装物料不含电路、磁铁或线束；另附电子空间预留与绑定审查，电子附件尚未发布生产文件。',
 '尖端名义露出3.5 mm':'尖端名义露出2.5 mm',
 '两件腕打印件 S2-P011/S2-P012 的 STL 与旧 E-P018/E-P019 逐字节相同，可直接复用；其余10件采用新STL，包括掌部。':'只有腕中心件 S2-P012 与旧 E-P019 的 STL 逐字节相同。其余11件使用 R2 文件；S2-P011 输出叉已经补强，不能复用旧叉冒充 R2。',
 '若已有旧腕件，可从工程中取消 S2-P011 和 S2-P012，其余件不要混用旧金属筒版。':'若已有合格旧 E-P019 腕中心件，可从工程中取消 S2-P012；其余11件按 R2 重打。',
 '局部压盖和双肋':'局部压盖和连续骨杆',
 'O24E · 常见五金左臂试装':'O24E R2 · 单臂结构复查版',
 'O24E · 常见五金单臂试装版':'O24E R2 · 单臂结构复查版',
 '双轴腕输出叉（原 E-P018）':'双轴腕输出叉（R2 补强）',
 '优先复用 O22 / T6 常见五金；零金属定制、零切短。':'P007 近端横桥、连续骨杆与圆滑工具入口；保留 O22 / T6 常见五金。',
 }
 for path in [*OUT.glob('*.html'),OUT/'preview/index.html',OUT/'tutorial/steps.json']:
  text=path.read_text('utf8')
  for x,y in replacements.items():text=text.replace(x,y)
  path.write_text(text,encoding='utf8')
 r=load(OUT/'verification/structure_comparison.json');en=load(OUT/'electronics/interface_reservations.json')
 rows=[
 ('S2-P001～003','R 防脱压盖','锁母窝后承压层从约0.4加厚到1.6 mm；M3×16仍穿过尼龙。','环唇是大平垫的轴向挡止；圆形避空让旋转件通过；六角窝负责止转，均必须保留。'),
 ('S2-P004','固定握持座','R座背部方键过渡改为连续圆截面渐变；输入握持块与双杆保留。','握持块用于夹持；双杆短而分开布置，为肩转动体及装入工具让位，无孤立薄台阶。'),
 ('S2-P005','肩俯仰转子／肩外展固定端','补上关节中心横向连接，接近关节的连续椭圆骨杆替代长双杆。','侧窗是12 mm摩擦垫装入入口；中心孔是肩钉／内六角入口。'),
 ('S2-P006','肩外展转动叉／上臂旋转座','重建转动叉，删除旧方键槽、裂槽和横孔；叉杆直径由5.6加到7 mm。','开放U叉必须让固定中心件进入并容许转动，不能把运动间隙填成实心；耳内孔和3 mm摩擦耳保留。'),
 ('S2-P007','上臂转子／肘固定端','补近端横向承力芯；用半封闭椭圆骨杆取代两根长杆；大工具孔以12 mm长平滑过渡连接小孔。','原突变台阶不是挡止或轴承面，已删除；中孔仍穿过横桥供先装R肩钉使用，按教程先R后H。'),
 ('S2-P008','肘转动叉／前臂旋转座','同P006重建叉杆，删除无用旧接口；保留原旋转盖±20 mm装钉间距。','开放叉用于组装／旋转；与盖的装钉通道是有用途的间隙。'),
 ('S2-P009','前臂转子／腕固定叉','删除旧方键环、旧裂槽／横孔；连续椭圆根部；腕叉杆增至7 mm。','腕根的R21圆弧避让极限姿态的螺钉头，不是拼接残留；侧窗与中心孔仍是工具入口。'),
 ('S2-P010','掌部','锁母背面承压层由约0.5加到1.5 mm；M2×20整根，尖端名义露出2.5 mm。','方键传递掌部扭矩；六角口止转；头下两片平垫及工具孔必须保留。'),
 ('S2-P011','双轴腕输出叉','叉杆由5.6加到7 mm，近耳保持原摩擦面；磁铁座位置与入口保留。','叉根方键用于安装手掌；负X侧D6.2磁铁口袋及小锁固座用于后续腕感测，不应磨平。'),
 ('S2-P012','双轴腕中心件','复用已接受的E-P019／T6 W几何；保留四侧金属堆叠的内支承。','四个六角窝、沉孔和正交轴孔有明确承力或装配功能，保留。'),
 ]
 put(OUT/'verification/feature_purpose_review.json',dict(status='REVIEWED_12_PARTS',geometry_sha256=sha(OUT/'production_meshes.npz'),rows=[dict(part_numbers=x,name=y,change=z,preserved_purpose=w) for x,y,z,w in rows],scope='Functional feature and load-path review plus individual core screening. It is not a minimum-thickness or full-arm FEA certificate.'))
 body='<div class="box"><b>你的两点担心都指出了实际设计问题。</b> P007 的肘固定端并非完全没有预紧反力：肩钉、垫片与锁母构成金属回路；问题在于旧版取消了近端横桥，额外侧载及配合误差主要由两根长杆承接。旧内侧台阶来自装入孔直径突然结束，并无独立功能。</div>'
 body+='<div class="grid"><div><h2>上一版 R1</h2><img src="images/P007_R1.png" alt="旧P007两根长杆和孔端台阶"></div><div><h2>本版 R2</h2><img src="images/P007_R2.png" alt="新P007连续骨杆和关节近端横桥"></div></div>'
 body+='<p>新增横桥传递两耳之间的横向作用，骨杆与关节以连续截面连接。装入孔从直径12.7 mm渐变至7.5 mm，保留圆角侧窗。没有把摩擦耳、锁母座、挡止唇、传感器座等功能台阶简单磨掉。</p>'
 body+=table(['件号','部位','处理','保留凹凸的明确用途'],rows)
 body+='<h2>验证能说明什么</h2><p>全部12个最终STL均为连续封闭实体，0.5 mm侵蚀后的主体仍连通；新结构已重新通过三组R的双向轴向挡止、拆盖负对照、逐件装入、107项H／W／掌部／盖螺钉路径、模块连接、30个名义姿态和850个密集运动采样。所有检查均引用本版最终STL的几何哈希。</p>'
 body+='<p>P007另外做了相同边界条件下的H8体素弹性比较：固定近端R转子，两个打印叉耳各施加向内1 N，假设均质材料E=1500 MPa、ν=0.35。该载荷是支架侧载比较，不是把A8预紧力错误地施加到打印两臂。</p>'
 body+=table(['版本','1.2 mm网格闭合量/mm','0.9 mm网格','0.6 mm网格'],[(x['revision'],*[f'{v["closure_mm"]:.6f}' for v in x['solutions']]) for x in r['rows']])
 body+='<p>三个网格均显示新增近端连接显著减少叉耳相对位移。数值仍依赖体素边界，尤其R2小位移尚未网格收敛；这里不报告“刚度提高多少倍”或材料强度额定值。没有模拟钢件接触、打印各向异性、蠕变或疲劳。其他零件做的是截面／用途／装配／连通性审查，没有冒充完成整臂有限元。</p>'
 body+='<p><a href="verification/structure_comparison.json">比较模型与结果</a> · <a href="verification/feature_purpose_review.json">逐件功能审查</a> · <a href="verification/connected_core.json">全部打印件薄连接筛查</a></p><div class="box warn">这是可开始打印试装的结构修正版，实装保持力、轴向拉拔、PLA蠕变、100次免补紧仍待你的实物记录。已接受的T6 H/W状态保留，不要求重新验收H/W才开始。</div>'
 page('STRUCTURE_REVIEW.html','R2 · 整臂受力与表面特征复查',body)
 body='<div class="box"><b>机械试装不用购买或安装电子元件。</b> 本版同时检查未来电子元件的尺寸与活动空间；电子支架、磁铁锁盖、PCB与活动线束尚未发布生产版本。绿色PCB和红色磁铁均为预留包络，不能拿它们当可打印零件。</div>'
 body+='<p>保留5个单轴传感器加1个双轴腕传感器的映射。沿用原生S1／S2／S3板尺寸与芯片偏心量：S1/S2为12×10×0.8 mm、S3为10×12×0.8 mm；包络另计入朝内2.5 mm元件高度和4 mm灌封尾线。S2不能按PCB几何中心对准磁铁。</p>'
 body+=table(['传感器','对应轴','板型','安装基准与状态'],[(b['id'],' / '.join(b['axes']),b['variant'],('原腕输出叉磁铁口袋保留；固定PCB位于前臂。' if b['id']=='W' else '通过外部可拆鞍座／现有盖螺钉接口安装；不在新横桥开孔。')+' 支架制造图未释放。') for b in en['bindings']])
 body+='<p>12个刚体包络在850个有限姿态下与所有机械实物检查无实体重叠。PCB位置与磁铁位置可在三维视图中单独显示；完整局部变换矩阵、板型偏心及装入检查见下列JSON。该结果只证明预留空间，不证明支架装配、磁场强度或角度精度。</p><p><a href="preview/index.html">三维视图：勾选“电子空间预留”</a> · <a href="electronics/interface_reservations.json">六组接口与坐标</a> · <a href="electronics/reserved_layout.glb">带预留的GLB</a> · <a href="electronics/inherited_pinmap_reference.json">保留的接线映射</a></p>'
 body+='<h2>走线与腕角链</h2><p>线束按6根AWG30细绞线、单根绝缘外径≤0.7 mm预留，束径包络3.5 mm，动态弯曲半径至少10 mm。线沿骨杆外侧，先在板端卸力，再经过外置可拆线夹。RP、HS、RU、HE、RF各自留活动环；不穿摩擦垫、碟簧、旋转捕获唇、叉内夹点或中央调节孔。这里的弧长预算不是下料长度，实际线束碰撞、弯曲寿命与下料表仍须在电子附件定型后完成。</p>'
 body+='<p>腕角链仍为Ry(屈伸)·Rx(偏摆)，前臂固定−90°钟向只计一次。腕板固定在前臂，磁铁随输出叉运动，因此不需要线跨越两个腕轴。保留旧针脚与节点名称；新单轴磁铁／板位置、标准钢件布局均已改变，旧角度标定表不能直接复用。可调预紧螺钉不充当磁铁的转动基准。</p><p><a href="https://www.ti.com/product/TMAG5170">TI TMAG5170官方资料</a>仅用于核对器件能力；本次未验证磁场量程、钢件偏置、双轴反解条件或实际角度精度。</p>'
 page('ELECTRONICS_RESERVATION.html','电子接口与走线空间预留',body)
 # Add explicit revision entry and direct review links to the existing deliverable pages.
 start=OUT/'START_HERE.html';text=start.read_text('utf8');text=text.replace('<body>','<body><div class="box"><b>R2 结构修正版 · 2026-10-27</b><br><a href="STRUCTURE_REVIEW.html">先看P007及全臂修改对照</a> · <a href="ELECTRONICS_RESERVATION.html">电子预留范围与限制</a><br>本版仍是12个打印件、134件现有规格五金；仅P012可直接复用旧打印件。</div>');start.write_text(text,encoding='utf8')
 # Optional non-production overlays, excluded from trial inventory and tutorial.
 path=OUT/'preview/data.js';d=json.loads(path.read_text('utf8').removeprefix('window.O24D=').removesuffix(';'));data=bytearray(base64.b64decode(d['geometry']));cursor=len(data)//24;z=np.load(OUT/'electronics/reserved_meshes.npz')
 for p in load(OUT/'electronics/reserved_parts.json'):
  i=str(p['i']);v=z[i+'v'];f=z[i+'f'];m=trimesh.Trimesh(v,f,process=False);arr=np.concatenate([v[f],np.repeat(m.face_normals[:,None,:],3,axis=1)],axis=2).reshape(-1,6).astype('<f4');d['parts'].append(dict(name=p['name'],frame=p['frame'],role=p['role'],source_features=['electronics','reserved'],reservation=True,bounds_mm=m.bounds.tolist(),color=[.15,.65,.4] if p['role']=='pcb' else [.85,.2,.15],first=cursor,count=len(arr)));data.extend(arr.tobytes());cursor+=len(arr)
 d['geometry']=base64.b64encode(data).decode();d['mechanical_count']=146;d['reservation_count']=12;path.write_text('window.O24D='+json.dumps(d,ensure_ascii=False,separators=(',',':'))+';',encoding='utf8')
 p=OUT/'preview/viewer.js';s=p.read_text('utf8').replace('function selected(p){','function selected(p){if(p.reservation&&!$(\'#electronics-reserved\').checked)return false;').replace("if(!$('#hardware').checked&&!['structure','rotor','shell'].includes(p.role))continue;","if(!p.reservation&&!$('#hardware').checked&&!['structure','rotor','shell'].includes(p.role))continue;").replace("$('#parts').textContent=D.parts.length;","$('#parts').textContent=D.mechanical_count;").replace("['bones','helpers','hardware','shell','harness']","['bones','helpers','hardware','shell','harness','electronics-reserved']").replace('显示 ${visible} / ${D.parts.length} 个机械实物件 · mm','显示 ${visible} 件 · 机械146件，另有12个可选电子包络 · mm');p.write_text(s,encoding='utf8')
 p=OUT/'preview/index.html';s=p.read_text('utf8').replace('<div class="checks">','<div class="checks"><label><input type="checkbox" id="electronics-reserved"> 电子空间预留（附件未发布）</label>').replace('<a href="../START_HERE.html">','<a href="../STRUCTURE_REVIEW.html">P007与全臂复查</a><a href="../ELECTRONICS_RESERVATION.html">电子预留说明</a><a href="../START_HERE.html">');p.write_text(s,encoding='utf8')
 print('R2 DOCUMENTED: 12 mechanical prints, 6 electronic reservations, explicit future accessory scope',flush=True)
if __name__=='__main__':finish()
