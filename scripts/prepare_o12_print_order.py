"""Package the sealed O12 plastic geometry with a supplier-facing FDM request.
No purchase, G-code generation, slicing or hardware qualification is performed.
"""
from pathlib import Path
import json, hashlib, zipfile, shutil, html, subprocess, sys

R=Path(__file__).resolve().parents[1]
H=R/'Hardware/PoseDoll44'
SOURCE=H/'bench/revO12/print_beds'
OUT=H/'bench/service_requests/o12_20260926'
ZIP=OUT.parent/'PoseDoll_O12_FDM_Print_Order.zip'
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def write_json(p,d): p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def upstream():
    p=subprocess.run([sys.executable,'-X','utf8',str(R/'scripts/seal_revo12.py'),'--verify'],cwd=R,text=True,capture_output=True,encoding='utf-8')
    assert p.returncode==0,p.stdout+p.stderr
    return json.loads(p.stdout)
before=upstream()
OUT.mkdir(parents=True,exist_ok=True)
(OUT/'models').mkdir(exist_ok=True)
names=['O12_taobao_bench.3mf','printed_base_minus_on_bed.stl','printed_base_plus_on_bed.stl','printed_lever_on_bed.stl']
for name in names:
    shutil.copyfile(SOURCE/name,OUT/'models'/name)
    assert sha(SOURCE/name)==sha(OUT/'models'/name)
volumes=json.loads((SOURCE/'export_check.json').read_text())['parts']
solid_volume_cm3=sum(p['volume_mm3'] for p in volumes)/1000
nominal_mass=solid_volume_cm3*1.22
sources={
 'nozzle_compatibility':'https://us.store.bambulab.com/bundles/all-in-one-hotends-kit-p1-series',
 'material_comparison':'https://cdn1.bambulab.com/filament/filament-guide/wksdyyzd8n9/filament-guide-en.pdf',
 'PLA_CF_A1':'https://raw.githubusercontent.com/bambulab/BambuStudio/master/resources/profiles/BBL/filament/Bambu%20PLA-CF%20%40BBL%20A1.json',
 'PLA_CF_P1S_compatible_X1C':'https://raw.githubusercontent.com/bambulab/BambuStudio/master/resources/profiles/BBL/filament/Bambu%20PLA-CF%20%40BBL%20X1C.json',
 'PLA_CF_base':'https://raw.githubusercontent.com/bambulab/BambuStudio/master/resources/profiles/BBL/filament/Bambu%20PLA-CF%20%40base.json',
 'PLA_base':'https://raw.githubusercontent.com/bambulab/BambuStudio/master/resources/profiles/BBL/filament/fdm_filament_pla.json'
}
requirements={
 'schema':'o12-outsourced-print-request-v1','date':'2026-09-26',
 'purpose':'One independent mechanical test coupon; not a full doll.',
 'not_an_importable_slicer_profile':True,
 'quantity_sets':1,'plastic_parts_per_set':3,
 'geometry_source':'O12 sealed o12_20260926_r1; copied unchanged.',
 'materials':{
  'first_choice':'Bambu Lab PLA-CF, black preferred, same spool/batch for all three parts',
  'fallback_order':['ordinary unfilled PLA with named brand and product','ordinary PETG with named brand and product'],
  'fallback_condition':'Supplier cannot provide the prior choice. Label the entire set and use the actual material profile. Do not mix materials within one set.',
  'unknown_brand_CF':'Not equivalent by name alone. Do not automatically use the Bambu 0.4 mm recipe for another filled filament.',
  'creep_friction_strength_qualified':False},
 'machine':{'allowed':['Bambu Lab A1','Bambu Lab P1S'],'same_machine_for_set':True,
            'for_CF':'Verify hardened steel 0.4 mm nozzle and an extrusion path/gears suitable for abrasive filament. Model name alone does not establish installed hardware.'},
 'process':{'nozzle_mm':.4,'layer_height_mm':.2,'first_layer_mm':.2,'wall_loops':6,
            'top_shell_layers':5,'bottom_shell_layers':5,'infill_percent':100,'infill_pattern':'rectilinear solid fill',
            'scale_percent':[100,100,100],'units':'mm','ironing':False,
            'brim':'5 mm outer brim starting point if needed; avoid internal-hole brims',
            'speed_caps_mm_s':{'first_layer':25,'outer_wall':50,'inner_wall':70,'infill':80,'top_surface':40,'bridge':20},
            'speed_note':'Project trial caps, not a validated optimum. Preserve lower cooling/volumetric limits and supplier calibration.',
            'flow_line_width_retraction':'Use material/machine preset and documented calibration.',
            'support':'Slice and inspect first. Keep the provided bed-facing faces. Add local removable support only where needed; no inaccessible fused support in nut or washer pockets.',
            'postprocess':'Remove support and burrs only; no geometry rescaling, through-drilling stepped bores, polishing friction faces, coating or annealing.'},
 'official_profile_reference_observed_20260926':{
   'applies_only_to':'Bambu PLA-CF with 0.4 mm nozzle and Smooth/High Temperature PEI or Textured PEI plate',
   'A1':{'nozzle_initial_and_other_C':230,'PEI_bed_initial_and_other_C':65},
   'P1S':{'nozzle_initial_and_other_C':230,'PEI_bed_initial_and_other_C':55},
   'cooling':'Use selected machine PLA-CF preset; do not give A1 and P1S one universal fan setting.',
   'different_material_or_plate':'Use the matching current official/supplier-tested preset and record the change.',
   'drying':'Use current material instructions appropriate to the dryer; record conditions.'},
 'orientation':{'base_halves':'Split mating face toward bed, as supplied in 3MF.',
                'lever':'Flat as supplied; do not stand on its long edge.',
                'allowed_rearrangement':'XY translation and rotation about printer Z only; preserve bed-facing faces.'},
 'nominal_dimensions_mm':{
   'assembled_base':[50,30,8],'each_base_half_bounding_dimensions':[50,15,8],
   'lever_overall_bounds':[111,12,6],'lever_friction_hub_axial_thickness':3,
   'lever_center_bore':4.25,'base_front_shoulder_guide':4.25,'base_thread_channel':3.4,
   'M3_hex_pocket_AF':5.8,'reaction_washer_seat_diameter':9.3,
   'two_half_base_connection_through_holes':3.4,'mounting_holes':4.5,'printed_load_web':2.8},
 'acceptance':'Supplier reports actual dimensions/visible defects; these are CAD nominal values, not unverified printer tolerance promises. Owner performs actual metal fit and load tests.',
 'nominal_solid_volume_cm3':round(solid_volume_cm3,3),
 'PLA_CF_nominal_net_mass_g_at_density_1p22':round(nominal_mass,2),
 'mass_scope':'Solid CAD estimate; excludes supports, brim, purge and process variation.',
 'source_urls':sources,
 'slicer_tested':False,'printed':False,'hardware_tested':False,'sent_to_supplier':False,'order_placed':False
}
write_json(OUT/'PROCESS_REQUIREMENTS.json',requirements)
text=f"""PoseDoll O12 独立小样｜委托 FDM 打印要求
日期：2026-09-26
用途：室内机械小样实验。首批 1 套，共 3 个塑料零件，各打印 1 件。

【1. 文件与数量】
优先使用 models/O12_taobao_bench.3mf，其中已经包含三件和摆放方向。
也提供三个独立 STL 作为替代输入。3MF 与 STL 二选一，不是要求打印两套。
- printed_base_minus_on_bed.stl：底座半件 A，1件。
- printed_base_plus_on_bed.stl：底座半件 B，1件。
- printed_lever_on_bed.stl：长臂，1件。
全部单位 mm，XYZ 缩放均为100%。本包不包含 G-code 或机器配置。

【2. 材料与机器】
首选：拓竹 Bambu PLA-CF，优先黑色；同套三件使用同品牌、型号、颜色及批次。
若不能提供：依次改用具名品牌/型号的普通 PLA、普通 PETG；整套替换并在包装上注明。
“PLA-CF”名称相同不保证材料和喷嘴要求相同，不把未知品牌CF自动按拓竹参数打印。
本轮不使用丝绸、发泡、装饰填料或未注明配方的改性料，以固定试验材料。

拓竹 A1 或 P1S 均可，同套尽量使用同一台已校准机器。
喷嘴统一选0.4 mm；PLA-CF需硬化钢喷嘴，并确认挤出机齿轮/送料路径适合磨蚀性耗材。
不能仅凭“P1S”或“A1”型号就默认已经完成耐磨配置。
首轮不换成0.2、0.6或0.8 mm喷嘴；若设备限制，请在报价中说明。

【3. 切片参数】
层高：0.20 mm；首层：0.20 mm。
墙层数：6道；顶面实体层：5层；底面实体层：5层。
填充：100%，采用软件支持的直线/Rectilinear实心填充。
熨烫：关闭。外侧Brim可从5 mm开始；不要把孔内填满裙边。
建议速度上限：首层25、外壁50、内壁70、内部填充80、顶面40、桥接20 mm/s。
这些是本项目首轮控制条件，不是打印机最快速度；保留更低的体积流量/冷却限速。
线宽、流量、回抽和风扇采用对应机型/材料的已校准预设，记录任何调整。
100%填充用于固定试验变量，不表示打印件强度已通过验收。

仅限“拓竹PLA-CF + 0.4喷嘴 + 光面/高温PEI或纹理PEI板”：
- A1：首层及其后喷嘴230°C，热床65°C。
- P1S：首层及其后喷嘴230°C，热床55°C。
以上来自2026-09-26核对的Bambu Studio官方预设；应以实际安装版本匹配预设复核。
不要将该温度表用于其他品牌、普通PLA/PETG、冷板或SuperTack板。
替换材料时用该材料自己的预设，不能只改耗材名称。
按所购耗材与烘干设备的当前说明预干燥并记录；P1S按PLA类要求管理散热。

【4. 摆放、支撑与后处理】
底座两半：分合面朝打印平台，沿用提供的方向。
长臂：平放，沿用提供的方向。
可在平台平面移动和绕竖直轴旋转，不翻转底面、不竖起长臂。
先查看切片：长臂从无支撑检查；底座关注螺母槽和垫圈槽顶部桥接。
确有需要时增加局部支撑，必须能从分合面清除；不得留下粘死或无法取出的支撑。
去除支撑、裙边、毛刺；不要抛光摩擦面、喷漆、退火或擅自磨薄零件。
如使用已校准的象脚/孔径补偿，请记录。不要用整件缩放代替局部工艺校准。
底座中心是阶梯孔：不得将4.25 mm钻头贯穿整块底座来“通孔”。

【5. 检查与记录】
以下是CAD名义尺寸，请按实际能力测量并报告；并非承诺打印机能达到未指定的公差。
- 合拢底座外形：50×30×8 mm；每半件外形：50×15×8 mm。
- 长臂整体包络：111×12×6 mm；中心摩擦凸台轴向厚度：3.00 mm。
- 长臂中心孔：4.25 mm；底座正面光杆导向段：4.25 mm。
- 底座较细螺纹通道与两半连接孔：3.40 mm；内部M3螺母槽对边：5.80 mm。
- 内部反力垫圈座直径：9.30 mm；承压台阶名义厚度：2.80 mm。

检查两半能合拢，接合面和摩擦面无明显翘曲、凸瘤、裂纹、缺料或支撑残留。
如有4 mm光杆/相应M3螺母，可辅助试装；没有实物时注明“未做金属件试装”。
装配需顺畅，不靠强压。不得为试装自行扩大整个阶梯孔或磨薄承压台阶。
最终零件配合、保持力、长期受压变形由委托方小样实验确认，不以打印完成代替测试。

【6. 随货提供】
请注明：机型、喷嘴直径/材质、耗材品牌型号/颜色、干燥条件、使用板型及实际切片参数。
提供切片设置和关键孔槽预览截图；能够提供时附实际使用的切片项目文件。
包装标签标出O12、材料和三个零件名称，不在摩擦面或承压面加刻字。
首批1套即可。按几何实心体积估算，PLA-CF三件净料约{nominal_mass:.1f} g；
这不是报价依据或承诺重量，不包含支撑、裙边、排料及实际流量差异。

【选择依据】
选PLA-CF是本轮室温刚性小样的工程选择，不是全市场材料最优结论。
厂家同系列数据中PLA-CF的XY弯曲模量高于普通PLA及PETG HF；
该指标不能证明层间强度、摩擦性能、长期压缩蠕变或本结构寿命。
普通PLA可先做装配/低载基线；PETG作为另一个材料样品记录，不把耐热等同于长期不变形。

官方来源（资料核对日期2026-09-26）：
喷嘴兼容性：{sources['nozzle_compatibility']}
材料比较：{sources['material_comparison']}
A1的PLA-CF预设：{sources['PLA_CF_A1']}
P1S兼容的PLA-CF预设：{sources['PLA_CF_P1S_compatible_X1C']}
PLA-CF继承项：{sources['PLA_CF_base']}
PEI热床继承项：{sources['PLA_base']}

本包几何与已封存O12一致。尚未用服务商机器切片、打印或加载测试。
"""
(OUT/'PRINT_ORDER.zh-CN.txt').write_text(text,encoding='utf-8-sig')
# Simple self-contained reading/printing view; no scripts or remote assets.
body=html.escape(text)
page='''<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>PoseDoll O12 委托打印要求</title><style>body{font:16px/1.75 "Microsoft YaHei",sans-serif;color:#203b31;background:#f6f5ef;margin:0}main{max-width:920px;margin:32px auto;padding:28px;background:white}pre{white-space:pre-wrap;overflow-wrap:anywhere;font:inherit}a{color:#245c46}nav{padding-bottom:18px;border-bottom:1px solid #d2d8cc}@media print{body{background:white;font-size:11pt}main{margin:0;padding:0}nav{display:none}pre{line-height:1.5}}</style><main><nav><a href="PRINT_ORDER.zh-CN.txt" download>下载文本要求</a> · <a href="models/O12_taobao_bench.3mf" download>下载三件排版 3MF</a></nav><pre>'''+body+'</pre></main></html>'
(OUT/'PRINT_ORDER.zh-CN.html').write_text(page,encoding='utf-8')
content=[p for p in OUT.rglob('*') if p.is_file() and p.name not in ('FILES.sha256.json','package_check.json')]
manifest={
 'schema':'o12-print-request-package-v1','date':'2026-09-26','files_sha256':{p.relative_to(OUT).as_posix():sha(p) for p in sorted(content)},
 'source_models_sha256':{p.relative_to(H).as_posix():sha(p) for p in (SOURCE/n for n in names)},
 'generator_sha256':sha(Path(__file__)),'O12_evidence_manifest_sha256':sha(H/'generated/revO12/runs/o12_20260926_r1/evidence_manifest.json'),
 'scope':'Supplier request only. Geometry unchanged. Temperatures are material/machine/plate-specific reference presets.',
 'physical_tested':False,'slicer_tested':False,'sent_to_supplier':False,'order_placed':False}
write_json(OUT/'FILES.sha256.json',manifest)
files=sorted(content+[OUT/'FILES.sha256.json'])
with zipfile.ZipFile(ZIP,'w',zipfile.ZIP_DEFLATED) as z:
    for p in files:z.write(p,'PoseDoll_O12_Print_Order/'+p.relative_to(OUT).as_posix())
with zipfile.ZipFile(ZIP) as z:
    assert z.testzip() is None
    for p in files:assert hashlib.sha256(z.read('PoseDoll_O12_Print_Order/'+p.relative_to(OUT).as_posix())).hexdigest()==sha(p)
    assert len(z.namelist())==8
with zipfile.ZipFile(OUT/'models/O12_taobao_bench.3mf') as z:
    import xml.etree.ElementTree as ET
    root=ET.fromstring(z.read('3D/3dmodel.model'))
    ns={'m':'http://schemas.microsoft.com/3dmanufacturing/core/2015/02'}
    assert root.attrib['unit']=='millimeter' and len(root.findall('.//m:object',ns))==3
    assert not any(n.lower().endswith(('.gcode','.bgcode')) for n in z.namelist())
after=upstream()
assert before==after
check={'zip':ZIP.relative_to(R).as_posix(),'zip_sha256':sha(ZIP),'files':len(files),'source_models_unchanged':True,
       'three_mf_objects':3,'units':'mm','gcode_included':False,'upstream_O12_verified':after['verified'],
       'slicer_tested':False,'physical_tested':False,'net_CAD_mass_PLA_CF_g':round(nominal_mass,2)}
write_json(OUT/'package_check.json',check)
print(json.dumps(check,ensure_ascii=False))
