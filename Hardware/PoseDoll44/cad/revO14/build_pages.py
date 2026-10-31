"""O14 viewer and UTF-8 core guide; keep sealed O13 files unchanged."""
from pathlib import Path
import json,sys,shutil,html,math,re,zipfile
import numpy as np
from audit_reference_and_collisions import H,G13,OUT,read,sha
sys.path.insert(0,str(H/'cad/revO13'))
from fullbody_stage import geometry_model
from solid_ops import from_tri
sys.path.insert(0,str(H/'cad'))
from model import fk
PAGE=H/'tutorials/full-doll-o14';GUIDE=H/'tutorials/core-print'
def write(p,s):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(s,encoding='utf-8')
def dump(p,s):write(p,json.dumps(s,ensure_ascii=False,indent=2)+'\n')
def plots():
 raw=np.load(OUT/'oriented_parts.npz');bed=read(OUT/'bed_geometry.json');report=read(OUT/'slicing/report.json');cards=[]
 for row,r in zip(bed['parts'],report['rows']):
  key=row['part'];paths=read(OUT/f'slicing/{key}_paths.json');t=raw[key];contact=row['new']['flat_contact_area_mm2'];isfork=key in ('C01','C02');bbox=row['new']['bounds_mm'];axis=0 if bbox[3]-bbox[0]>=bbox[4]-bbox[1] else 1
  # Two orthographic illustrations from actual mesh triangles and actual G-code.
  body=['<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 640 280" role="img" aria-labelledby="title"><title id="title">'+key+' 实际切片：侧面支撑与首层路径</title><rect width="640" height="280" fill="#f6f4ec"/>']
  for panel in ('side','top'):
   if panel=='side':
    lo=np.array([bbox[axis]-5,0]);hi=np.array([bbox[axis+3]+5,bbox[5]+4]);off=15
    project=lambda a:np.array([a[axis],a[2]])
   else:
    h=np.array(r['combined_first_layer_hull_mm']);lo=h.min(0)-6;hi=h.max(0)+6;off=335
    project=lambda a:np.array(a[:2])
   scale=min(285/(hi[0]-lo[0]),200/(hi[1]-lo[1]))
   def xy(a):
    v=(project(a)-lo)*scale;return (off+v[0],235-v[1])
   def line(a,b,c,w=.7):
    x,y=xy(a);xx,yy=xy(b);return f'<path d="M{x:.2f},{y:.2f}L{xx:.2f},{yy:.2f}" stroke="{c}" stroke-width="{w}" fill="none"/>'
   if panel=='side':
    body.append('<text x="15" y="24" font-size="14" fill="#253e36">侧面：绿色零件 / 橙色支撑</text>')
    # Actual support paths projected to the side. Each layer represented; no invented support volume.
    for s in paths['support_segments'][::3]:body.append(line(s['a'],s['b'],'#cc7b32',.45))
    # Filled mesh triangles produce an exact orthographic silhouette at this projection.
    for face in t:
     pts=[xy(a) for a in face];u=np.subtract(pts[1],pts[0]);v=np.subtract(pts[2],pts[0]);area=abs(u[0]*v[1]-u[1]*v[0])
     if area>.03:body.append('<polygon points="'+' '.join(f'{x:.2f},{y:.2f}' for x,y in pts)+'" fill="#537c6b"/>')
    body.append(f'<path d="M{off},236H{off+285}" stroke="#536258" stroke-width="3"/>')
   else:
    body.append('<text x="335" y="24" font-size="14" fill="#253e36">首层：含支撑底座与Brim 附着边</text>')
    for s in paths['first_layer_segments']:
     c='#a9b3a5' if 'Brim' in s['type'] else '#cc7b32' if 'Support' in s['type'] else '#3e7261';body.append(line(s['a'],s['b'],c,.8))
    c=r['model_COM_mm'];x,y=xy(c);body.append(f'<circle cx="{x:.2f}" cy="{y:.2f}" r="4" fill="#162d48"/><text x="335" y="266" font-size="12" fill="#536258">蓝点：零件实体重心的投影</text>')
  body.append('</svg>');write(GUIDE/f'{key}_support.svg',''.join(body))
  subtitle='叉架 · 耳部平面贴床，偏置柄下必须加支撑' if isfork else '承力环半件 · 分割平面贴床，检查孔槽支撑能否取出'
  cards.append(f'<article class="part"><h3>{key} <span>× 1</span></h3><p>{subtitle}</p><img src="{key}_support.svg" alt="{key} 的切片支撑和首层接触路径"><p class="small">平面贴床面积 {contact:.1f} mm²。'+('叉架单独的重心投影超出耳面接触区；不能关闭支撑。' if isfork else '零件实体重心投影位于自身接触区内。')+'</p></article>')
 return ''.join(cards)
def viewer():
 old=H/'tutorials/full-doll';PAGE.mkdir(exist_ok=True)
 shutil.copyfile(old/'style.css',PAGE/'style.css')
 models={k+'#0':geometry_model(from_tri(t)) for n,t in np.load(OUT/'selected_layout/carriers.npz').items() if n.endswith('_bridge') for k in [n[:-7]+'/bridge_o14']}
 write(PAGE/'carriers.js','Object.assign(window.O13_MODELS,'+json.dumps(models,separators=(',',':'))+');')
 states=read(OUT/'selected_layout/integrated_arm_states.json')['states'];checks={(r['character'],r['pose']):r['findings'] for r in read(OUT/'selected_layout/integrated_arms.json')['cases']}
 oldscenes=read(G13/'fullbody/scenes.json')['states'];old_by={(r['character'],r['pose']):r for r in oldscenes};scenes=[];profiles={}
 for char in ('manny','quinn'):
  p=read(OUT/f'selected_layout/fullbody/{char}_profile.json');profiles[char]=p;T0,A0=fk(p,{})
  rows=[s for s in states if s['character']==char];neutral=next(s for s in rows if s['pose']=='neutral')
  for s in [s for s in oldscenes if s['character']==char and s['reference_only_pose']]:
   T,_=fk(p,s['q']);D=T['chest']@np.linalg.inv(T0['chest']);rows.append({'character':char,'pose':s['pose'],'requested_angles_deg':s['q'],'reference_only_pose':True,'objects':[{**o,'frame':(D@np.array(o['frame'])).tolist()} for o in neutral['objects']]})
  for s in rows:
   old_s=old_by[char,s['pose']];T,A=fk(p,s['requested_angles_deg']);objects=[]
   for o in s['objects']:
    orig=[v for v in old_s['objects'] if v['label']==o['id']]
    if o['id'].endswith('integrated_bridge'):objects.append({'key':o['library']+'#0','frame':o['frame'],'label':o['id'],'role':'actual_geometry'})
    else:
     assert orig,o['id'];objects += [{**v,'frame':o['frame']} for v in orig]
   bones=[]
   for n in p['nodes']:
    if not n['parent'] or n['parent']=='device_base':continue
    a,b=T[n['parent']][:3,3],T[n['id']][:3,3]
    if np.linalg.norm(b-a)>1:bones.append({'id':n['id'],'a':a.tolist(),'b':b.tolist(),'radius':4 if n['id'].startswith(('hand','ball','toe')) else 6})
   scenes.append({'character':char,'pose':s['pose'],'q':s['requested_angles_deg'],'reference_only_pose':s.get('reference_only_pose',False),'objects':objects,'whole_arm_findings':checks.get((char,s['pose']),[]),'bones':bones,'support_points':[T[n][:3,3].tolist() for n in ('pelvis','forearm_l','forearm_r')]})
 write(PAGE/'scenes.js','window.O13_SCENES='+json.dumps(scenes,separators=(',',':'))+';')
 cr=read(OUT/'collision_classification.json');facts={'cases':len(cr['cases']),'adjacentFailures':cr['structural_failure_endpoints'],'nonadjacentContacts':cr['pose_contact_endpoints'],'shoulderOffsetPerSideMm':0}
 write(PAGE/'results.js','window.O13_RESULTS='+json.dumps(facts)+';');dump(OUT/'viewer_data.json',{'scenes':len(scenes),'facts':facts,'references_only':sum(s['reference_only_pose'] for s in scenes)})
 js=(old/'app.js').read_text(encoding='utf-8')
 js=js.replace("const bad=new Set((scene.whole_arm_findings||[]).flatMap(f=>f.pair));", "const findings=scene.whole_arm_findings||[],bad=new Set(findings.filter(f=>f.classification==='STRUCTURAL_ADJACENT_OR_SAME_JOINT').flatMap(f=>f.pair)),contact=new Set(findings.filter(f=>f.classification==='POSE_AVOIDABLE_NONADJACENT_CONTACT').flatMap(f=>f.pair));")
 js=js.replace("bad.has(o.label)?[.80,.28,.20]:o.role", "bad.has(o.label)?[.80,.28,.20]:contact.has(o.label)?[.85,.54,.15]:o.role")
 js=js.replace("(bad.size?'红色零件：此端点存在穿插':'实际手臂模型 + 全身参考骨架')", "(bad.size?'红色：同一或相邻关节干涉，需改设计':contact.size?'橙色：非相邻部位接触，需调整姿势':'该端点未检出所检零件穿插；非整机验收')")
 start=js.index("const r=window.O13_RESULTS;");end=js.index("window.O13_TEST=",start)
 js=js[:start]+"const r=window.O13_RESULTS;$('#facts').innerHTML=[['原小样实物反馈','装配通过','继续使用；保持力数值待补测'],['肩部额外外移','0 mm','已恢复 UE 缩放参考肩宽'],['同一 / 相邻关节',r.adjacentFailures+' / '+r.cases+' 端点干涉','仅当前实际手臂模型与连接架'],['非相邻部位',r.nonadjacentContacts+' / '+r.cases+' 端点接触','保留橙色提示，通过调整姿势避开']].map(x=>'<div class=fact>'+x[0]+'<strong>'+x[1]+'</strong><span>'+x[2]+'</span></div>').join('');\n"+js[end:]
 write(PAGE/'app.js',js)
 oldhtml=(old/'index.html').read_text(encoding='utf-8');top=oldhtml[:oldhtml.index('<section class="grid">')]
 top=top.replace('O13','O14').replace('检查中检出的穿插','同一 / 相邻关节干涉').replace('<span><i class="gold"></i>可用手支撑的位置</span>','<span><i style="background:#d98a26"></i>非相邻接触，调整姿势</span><span><i class="gold"></i>可用手支撑的位置</span>')
 top=top.replace('左右肩各外移 8 mm，肩间距增加 16 mm。骨长和原动作角度保留；这组安装偏移尚未写入 UE 设备校准。','已取消左右各 8 mm 的额外外移。肩宽恢复参考值；锁骨机构位置与腕部两轴间距仍有偏差，详见下方。')
 ref=read(OUT/'reference_deviations.json')['profiles'];oldref=read(OUT/'reference_deviations_o13.json')['profiles'];table=''
 for p,b in zip(ref,oldref):
  table+=f'<tr><td>{p["character"].title()}</td><td>{p["shoulder_width_reference_mm"]:.2f} mm</td><td>{b["shoulder_width_current_mm"]:.2f} mm</td><td>{p["shoulder_width_current_mm"]:.2f} mm</td><td>{max(p["worst_hand_tip_case"]["hand_tip_distance_mm"].values()):.2f} mm</td></tr>'
 tail=f"""<section class="next" style="margin-top:28px"><h2>肩宽已恢复，其他关节偏差仍需处理</h2><p>之前的 8 mm 外移用来避开左右肩模块之间的接触。按本轮规则，左右肩属于非相邻身体部位，因此取消外移，并重新生成连接架、检查全部 102 个原端点。上臂、前臂和手部参考段长保持不变。</p><div style="overflow-x:auto"><table><thead><tr><th>角色</th><th>参考肩宽</th><th>O13 肩宽</th><th>O14 肩宽</th><th>检查姿势中的最大手端偏差</th></tr></thead><tbody>{table}</tbody></table></div><p>比较对象是由 UE Manny / Quinn 得到的 480 mm 缩放参考，使用相同语义关节角度。手端偏差是模型位置差，不是传感器误差。</p><p><b>锁骨机构中心仍向后约 48–49 mm、向外约 34–36 mm、向上 10 mm；腕部屈伸轴与侧偏轴仍错开 8 mm。</b>因此不能宣称所有骨骼和关节中心都与 UE 一致，手掌接触位置也尚无经过验证的补偿。允许有限偏差作为设计空间；具体可接受范围尚未定案，这些差异保持为待优化项。</p></section>
<section class="grid"><article><div class="eyebrow">01 / 结构问题</div><h2>同一与相邻关节必须互不干涉</h2><p>锁骨—肩—肘—前臂—腕屈伸—腕侧偏按机械链相邻关系检查；同一个关节内的运动零件也属于必须解决的结构问题。未知零件分组会报错，不能自动放行。</p></article><article><div class="eyebrow">02 / 姿势问题</div><h2>非相邻接触保留提示</h2><p>本次 102 个端点中，结构干涉端点为 0，非相邻接触端点为 12。左右肩或左右手臂碰在一起时标橙色，需要换姿势；不会删掉这些记录，也不会说该姿势已通过。</p></article><article><div class="eyebrow">03 / 检查边界</div><h2>不是整机制造验收</h2><p>新连接架的中间运动、装拆路径、强度、线束与完整电路仍待验证。颈、躯干和下肢是参考骨架。旧版 3894 个路径样本不能直接作为恢复肩宽后的通过证据。</p></article></section>
<section class="next"><h2>现在是否要做新测试件？</h2><p>当前长臂小样继续使用。下一阶段新增的是四件打印主体组成的双轴核心，用来观察两轴同时动作、对侧预紧和环接缝的表现。无需重打原长臂。</p><p>原叉架摆放只有最低点接触，检查不充分，已纠正为平面贴床，并执行带支撑的离线切片。两个叉架必须开支撑；服务商按实际设备和材料复核后再下单，不直接使用旧的 O13 打印盘。</p><p><a href="../core-print/index.html">打开中文核心试装说明、数量和支撑示意 →</a></p></section>
<footer>O14 · 2026-09-29 · 102 个离散端点检查 · 完整人偶与实际打印工艺尚未验收</footer></main><style>table{{width:100%;border-collapse:collapse;margin:20px 0;font-size:14px}}th,td{{padding:12px;text-align:left;border-bottom:1px solid #c9d2c3}}th{{white-space:nowrap}}</style><script src="../full-doll/models.js"></script><script src="carriers.js"></script><script src="scenes.js"></script><script src="results.js"></script><script src="../full-doll/core.js"></script><script src="app.js"></script></html>"""
 write(PAGE/'index.html',top+tail)
def guide(cards):
 css=(H/'tutorials/full-doll/style.css').read_text();write(GUIDE/'style.css',css+"\nmain{max-width:1120px}h1{font-size:clamp(34px,5vw,52px)}.callout{background:#e8eddd;border-left:4px solid #608064;padding:20px 24px;margin:28px 0}.parts{display:grid;grid-template-columns:1fr 1fr;gap:22px}.part{border:1px solid #d2dbce;border-radius:14px;overflow:hidden;background:#fff;padding:20px}.part h3{margin:0;font-size:25px}.part h3 span{font-size:15px;color:#637269}.part p{font-size:14px}.part img{width:100%;display:block}.section{margin:40px 0}table{width:100%;border-collapse:collapse;font-size:14px}th,td{text-align:left;border-bottom:1px solid #d2dbce;padding:12px 10px}th{white-space:nowrap}.table-wrap{overflow-x:auto}li{margin-bottom:10px}pre{font-family:inherit;white-space:pre-wrap;background:#edf0e8;padding:18px;font-size:14px}.downloads{display:flex;flex-wrap:wrap;gap:12px}.downloads a{padding:12px 16px;border:1px solid #a8b9aa;border-radius:8px}@media(max-width:800px){.parts{grid-template-columns:1fr}}")
 source=(H/'bench/revO13/README.zh-CN.md').read_text(encoding='utf-8');rows=[]
 for line in source.splitlines():
  if line.startswith('|') and not line.startswith('|---') and not line.startswith('| 零件') and '观察' not in line:
   cells=[v.strip() for v in line.strip('|').split('|')]
   if len(cells)==3:rows.append('<tr>'+''.join('<td>'+html.escape(v)+'</td>' for v in cells)+'</tr>')
 # Stop at the eight hardware rows; subsequent observation tables are separate.
 bom=''.join(rows[:8])
 s="""<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><link rel="icon" href="data:,"><title>双轴核心：打印、零件数量与试装 | PoseDoll O14</title><link rel="stylesheet" href="style.css"></head><body><header><a href="../full-doll-o14/index.html">← 返回人偶查看器</a><span>POSEDOLL / O14</span></header><main><div class="eyebrow">核心试装说明与零件数量 · 2026 / 09 / 29</div><h1>下一件小样：<br>两个轴一起工作。</h1><p>这是四件打印主体与标准件组成的双轴核心，用来验证两个轴一起转动时的配合。你已经装好的长臂小样继续用；本包不包含外侧扭转座、传感器、连接架或完整人偶。</p><div class="callout"><b>现在先把下方的复核包发给打印服务商核对。</b><p style="margin:8px 0 0">新版已纠正叉架摆放，并完成实际带支撑切片。仍需服务商按真实打印机和耗材复核支撑、孔槽清理与附着情况，再确定打印。M1.6 合拢紧固件的商品尺寸也还要核对。</p></div>
<section class="section"><div class="eyebrow">01 / 四件打印主体，各一件</div><h2>平面贴床，悬空处由支撑承托</h2><p>原摆放仅以最低点到达 Z=0 判断贴床，没有验证接触面积，这是之前检查的遗漏。修正后，两个叉架以耳部平面贴床；偏置的柄和上方悬空部分仍要支撑。加宽底部Brim 附着边可以帮助附着，但不能替代悬空处的支撑。</p><div class="parts">CARDS</div><p class="small">示意来自本轮真实 STL 与 PrusaSlicer 2.9.6 生成的路径。橙色是支撑，灰色是首层Brim 附着边，蓝点是零件实体重心投影。为了可读，侧图每三段支撑路径显示一段，首层图保留全部路径。底部凸包与重心检查通过，只表示几何承托范围合理，不代表热床附着、层间强度或支撑可拆性已经实测。</p></section>
<section class="section"><div class="eyebrow">02 / 给服务商的要求</div><h2>不用照搬诊断切片的机器参数</h2><p>先沿用这次成功小样的材料与工艺，并记录耗材品牌、材质、喷嘴和层高。目前不知道实物实际使用了什么材料，不能把某个材料名字写成已验证结论。</p><pre>模型单位：mm，100% 比例，不要整体缩放。
四件各一件；按新版 3MF 摆放，保持平面贴床。
C01 / C02：必须启用支撑，承托偏置柄和上方悬空面。
C14 / C15：分割平面贴床，检查内部孔槽；支撑必须能够取出。
切片起点：0.4 mm 喷嘴、0.2 mm 层高、6 圈墙、5 层顶底、100% 填充、5 mm Brim 附着边。
本轮诊断使用普通自动支撑、45° 阈值（从水平面算）、3 层接触面、0.2 mm 顶部间隙。
以上仅是本轮切片起点；服务商按 A1 / P1S 与实际材料调整，不直接套用其他切片软件的角度定义。
逐层确认：首层连续、柄下有支撑、后续层没有未承托的孤岛；孔槽支撑可拆除。
支撑不要留下凸起影响垫圈平贴；孔径若需修整，先确认金属件能顺滑装入，不能靠强拧强压。
先看服务商带支撑的切片预览，再打印试件。</pre><p>本轮四件全部完成离线诊断切片，两个叉架都有实际支撑路径；完整零件和逐层挤出质心的投影均在“零件＋支撑”首层接触凸包内。这不是打印机实测，也未验证所有层的连接、冷却变形及支撑拆除过程。没有提供可直接上机的 G-code。</p><div class="downloads" id="download"><a href="../../bench/revO14/O14_core_supplier_review.zip">下载服务商复核包（中文说明＋四件模型）</a><a href="../../bench/revO14/print_beds/O14_core_flat_faces_supports_required.3mf">下载新版四件几何 3MF</a><a href="../../bench/revO14/print_beds/C01_flat_face.stl">C01 STL</a><a href="../../bench/revO14/print_beds/C02_flat_face.stl">C02 STL</a><a href="../../bench/revO14/print_beds/C14_flat_face.stl">C14 STL</a><a href="../../bench/revO14/print_beds/C15_flat_face.stl">C15 STL</a></div><p class="small" style="margin-top:12px">3MF 仅含几何与摆放，不含支撑设置或设备配置。导入 Bambu Studio 后仍须手动启用支撑并核对预览。</p></section>
<section class="section"><div class="eyebrow">03 / 一套核心的数量</div><h2>现成金属小件</h2><div class="table-wrap"><table><thead><tr><th>零件</th><th>数量</th><th>尺寸与说明</th></tr></thead><tbody>BOM</tbody></table></div><p style="margin-top:15px">除最后两种 M1.6 紧固件，其余沿用你已装好的那批规格。垫圈图里的 M3 / M4 是商品标称，已有成功装配支持复用该批零件；不把标称孔径当成精密实测值。此核心不需要旧长臂的 M3×35 壳体连接螺钉，也不需要定制金属件。</p></section>
<section class="section"><div class="eyebrow">04 / 装配顺序</div><h2>先合拢环，再装两片叉架</h2><ol><li>在承力环半件里放入四处 M3 螺母、M3 大垫圈和环合拢用的 M1.6 螺母。检查它们完整坐入各自凹槽。</li><li>合拢 C14、C15，用四颗 M1.6 螺钉固定。接缝应贴合，内部垫圈不能翘起。</li><li>放入两片叉架。每侧从环到螺钉头依次是：M4 大垫圈 → 打印叉架耳 → M4 大垫圈 → 两片反向碟簧 → M4 普通垫圈 → 轴肩螺钉头。螺纹进入环内的 M3 螺母。碟簧叠法和垫圈朝向沿用已成功的小样。</li><li>先给小预紧，再逐侧小幅调整。目标是顺滑且有适当阻力，不是拧到最紧。用查看器的“双轴核心”按钮和两个滑块对照结构。</li></ol><a href="../full-doll-o14/index.html">打开双轴核心三维查看器 →</a></section>
<section class="section"><div class="eyebrow">05 / 这次要测什么</div><h2>检查双轴工作，不是重新测打印机孔径</h2><ol><li><b>两轴是否卡滞：</b>先固定一轴、动另一轴，再交换，最后同时小幅转动；记录突变、刮碰和跳动。</li><li><b>对侧预紧是否互相影响：</b>一次只调一颗螺钉，观察对应轴和另一轴的手感。</li><li><b>环与叉架是否松动：</b>两方向轻推，观察接缝、轴孔、端部，记录可见位移或异响。</li><li><b>停留漂移：</b>同一角度、同一负载先看 1 分钟，再看 10 分钟。需要手托可以如实记录；卡滞、裂纹和松脱仍需解决。</li></ol><p>现有长臂的小样成功说明该批尺寸和装配可行，尚不能代替双轴测试。两轴核心还没有实物结果，整个人偶也未完成制造验证。</p></section><footer>依据本地 CAD 与实际诊断切片生成。打印方式参考 <a href="https://help.prusa3d.com/article/place-on-face-tool_1781">Prusa 的贴面放置说明</a>和<a href="https://help.prusa3d.com/article/easyprint_898029">支撑说明</a>。这是试件说明，不是整机打印清单。</footer></main></body></html>"""
 write(GUIDE/'index.html',s.replace('CARDS',cards).replace('BOM',bom))
def supplier_bundle():
 b=H/'bench/revO14';src=GUIDE/'index.html'
 s=src.read_text(encoding='utf-8').replace('<link rel="stylesheet" href="style.css">','<style>'+(GUIDE/'style.css').read_text(encoding='utf-8')+'.part svg{width:100%;height:auto}</style>')
 for k in ('C01','C02','C14','C15'):s=re.sub(r'<img src="'+k+r'_support.svg"[^>]*>',lambda m:(GUIDE/f'{k}_support.svg').read_text(encoding='utf-8'),s)
 s=s.replace('../../bench/revO14/print_beds/','print_beds/')
 s=re.sub(r'<a href="../../bench/revO14/O14_core_supplier_review.zip">.*?</a>','',s)
 s=re.sub(r'<a href="../full-doll-o14/index.html">.*?</a>','<span>PoseDoll 双轴核心试件 · 供应商切片复核</span>',s)
 write(b/'PRINT_ORDER.zh-CN.html',s)
 with zipfile.ZipFile(b/'O14_core_supplier_review.zip','w',zipfile.ZIP_DEFLATED) as z:
  for p in [b/'PRINT_ORDER.zh-CN.html',b/'README.zh-CN.md',*sorted((b/'print_beds').glob('*'))]:z.write(p,p.relative_to(b))
def main():
 viewer();guide(plots());supplier_bundle();print('O14 pages ready',PAGE,GUIDE)
if __name__=='__main__':main()
