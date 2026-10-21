"""Finish O22-F2 delivery UI, assembly cross-references and honest validation notes.
Read-only with respect to CAD meshes and native print projects.
"""
from pathlib import Path
from html import escape
from html.parser import HTMLParser
import json,csv,re,hashlib,shutil
import numpy as np
from build_revo22_fins_v2 import R,B,O
from o22_f2_gcode import extract_paths

CSS='''*{box-sizing:border-box}body{font-family:system-ui,"Microsoft YaHei",sans-serif;background:#f3f5ef;color:#24372f;margin:0;line-height:1.7}main{max-width:1120px;margin:0 auto;padding:40px 24px}a{color:#215a84}h1{font-size:34px;line-height:1.3}h2{margin-top:34px}table{width:100%;border-collapse:collapse;background:white;font-size:14px}td,th{border:1px solid #d5ddd1;padding:9px;text-align:left}.notice{background:#fff0d7;border-left:5px solid #c87b24;padding:18px;margin:20px 0}.ok{background:#dfedde;padding:18px}.muted{color:#59685e;font-size:14px}img{max-width:100%;height:auto;border-radius:8px}code{background:#e1e7dc;padding:2px 5px}.stats{display:flex;flex-wrap:wrap;gap:12px}.stats>div{background:white;padding:18px;flex:1;min-width:180px}.stats b{font-size:26px;display:block}details{margin:12px 0}li{margin:6px 0}'''
def page(title,body):
 return '<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><link rel="icon" href="data:,"><title>'+title+'</title><style>'+CSS+'</style><main>'+body+'</main></html>'
def write(path,s):
 path.parent.mkdir(parents=True,exist_ok=True);path.write_text(s,encoding='utf8')
def read(p):return p.read_text(encoding='utf-8-sig')

def risk_figures(manifest,risk):
 for plate in manifest['plates']:
  rr=next(p['regions'] for p in risk['plates'] if p['plate']==plate['id'])
  if not rr:continue
  _,paths=extract_paths(O/'projects'/f"{plate['id']}_O22F2_PLA_fins.3mf",arc_tolerance_mm=.015,max_arc_segment_mm=.6)
  ar=np.asarray(paths).reshape(-1,9);ar=ar[ar[:,7]==0]
  layers={z:ar[np.abs(ar[:,5]-z)<.001] for z in set(round(x['z_mm'],3) for x in rr)|set(round(x['z_mm']-.2,3) for x in rr)}
  for i,r in enumerate(rr):
   bb=r['bounds_mm'];cx=(bb[0]+bb[2])/2;cy=(bb[1]+bb[3])/2;span=max(bb[2]-bb[0],bb[3]-bb[1])+6;scale=600/span;lo=[cx-span/2,cy-span/2];z=round(r['z_mm'],3)
   svg=[f'<svg xmlns="http://www.w3.org/2000/svg" width="820" height="850" viewBox="0 0 820 850"><rect width="820" height="850" fill="#f6f7f0"/><style>text{{font-family:Arial,"Microsoft YaHei",sans-serif;fill:#28382d}}</style><text x="42" y="38" font-size="21">{escape(plate["id"])} · {i+1:02d} · {escape(r["object_name"])}</text><text x="42" y="72" font-size="17">G-code Z = {z:.2f} mm · flagged area = {r["area_mm2"]:.3f} mm²</text><text x="42" y="98" font-size="15">Grey: previous layer · Blue: current layer · Red: candidate bounds</text><defs><clipPath id="crop"><rect x="80" y="122" width="660" height="660"/></clipPath></defs><g clip-path="url(#crop)"><rect x="80" y="122" width="660" height="660" fill="white"/>']
   for zz,color in [(round(z-.2,3),'#adb3ac'),(z,'#36799b')]:
    aa=layers[zz];mask=(np.maximum(aa[:,0],aa[:,3])>=lo[0]-.8)&(np.minimum(aa[:,0],aa[:,3])<=lo[0]+span+.8)&(np.maximum(aa[:,1],aa[:,4])>=lo[1]-.8)&(np.minimum(aa[:,1],aa[:,4])<=lo[1]+span+.8)
    for v in aa[mask]:
     x1=110+(v[0]-lo[0])*scale;y1=752-(v[1]-lo[1])*scale;x2=110+(v[3]-lo[0])*scale;y2=752-(v[4]-lo[1])*scale
     svg.append(f'<path d="M{x1:.2f},{y1:.2f} L{x2:.2f},{y2:.2f}" stroke="{color}" stroke-width="{v[8]*scale:.3f}" stroke-linecap="round" fill="none"/>')
   x=110+(bb[0]-lo[0])*scale;y=752-(bb[3]-lo[1])*scale
   svg.extend([f'<rect x="{x:.2f}" y="{y:.2f}" width="{(bb[2]-bb[0])*scale:.2f}" height="{(bb[3]-bb[1])*scale:.2f}" fill="none" stroke="#bd3640" stroke-width="2" stroke-dasharray="5 3"/></g>',f'<text x="42" y="810" font-size="15">XY window: {span:.2f} × {span:.2f} mm. Widths from LINE_WIDTH; not a melt-flow simulation.</text></svg>'])
   r['slice_figure']=f'verification/regions/{plate["id"]}_{i+1:02d}.svg';write(O/r['slice_figure'],''.join(svg))
  print('REGION FIGURES',plate['id'],len(rr),flush=True)
 write(O/'risk-data.js','window.O22_REMAINING='+json.dumps(risk,ensure_ascii=False,separators=(',',':'))+';')
 with (O/'待复核出丝位置.csv').open('w',encoding='utf-8-sig',newline='') as f:
  w=csv.writer(f);w.writerow(['打印盘','本盘位置号','对象','Gcode Z mm','检测面积 mm2','Xmin','Ymin','Xmax','Ymax','定位角色','相邻层出丝图'])
  for p in risk['plates']:
   for i,r in enumerate(p['regions']):w.writerow([p['plate'],i+1,r['object_name'],round(r['z_mm'],3),r['area_mm2'],*r['bounds_mm'],'原零件本体',r['slice_figure']])

def improve_viewer(risk):
 js=read(O/'viewer.js');html=read(O/'index.html')
 # The publisher is called before this finalizer, so edits remain deterministic.
 assert 'function riskOptions' not in js
 js=js.replace("const $=s=>document.querySelector(s),S=window.O22_FINS,state=", "const $=s=>document.querySelector(s),S=window.O22_FINS,riskData=window.O22_REMAINING,state=")
 js=js.replace('let gl,c,program,L,objects=[]','let gl,c,program,L,riskBuffer,objects=[]')
 js=js.replace("state.item='';state.focus=null;state.iso=false", "state.item='';state.focus=null;state.risk=null;state.iso=false")
 js=js.replace("state.item=e.target.value;state.focus=null;info();draw()", "state.item=e.target.value;state.focus=null;state.risk=null;$('#risk').value='';$('#riskinfo').textContent='';info();draw()")
 js=js.replace("$('#reset').onclick=()=>{state.focus=null;", "$('#reset').onclick=()=>{state.focus=null;state.risk=null;$('#risk').value='';$('#riskinfo').textContent='';$('#contact').value='';$('#cliplabel').textContent='全部';")
 js=js.replace("$('#contact').onchange=e=>{", "$('#contact').onchange=e=>{state.risk=null;$('#risk').value='';$('#riskinfo').textContent='';")
 js=js.replace("state.zoom=1;info();draw();$('#status')", "state.zoom=1;riskOptions();info();draw();$('#status')")
 js=js.replace('gl.depthMask(true);window.O22_FINS_DRAW=', 'drawRiskBox(view);gl.depthMask(true);window.O22_FINS_DRAW=')
 helper=r'''
function currentRisks(){return riskData.plates.find(p=>p.plate===state.plate)?.regions||[]}
function riskOptions(){const rows=currentRisks();$('#risk').replaceChildren(new Option(rows.length?'选择待复核位置（'+rows.length+' 处）':'此盘未检出孤立起点',''),...rows.map((r,i)=>new Option((i+1)+' · '+r.object_name.split(' ')[0]+' · Z '+r.z_mm.toFixed(2)+' mm',i)));$('#riskinfo').textContent=''}
function focusRisk(i){let r=currentRisks()[i];if(!r)return;state.risk=r;$('#risk').closest('details').open=true;state.item=r.object_name;$('#item').value=state.item;$('#risk').value=i;info();let b=r.bounds_mm;state.focus=[[b[0]-3,b[1]-3,r.z_mm-3],[b[2]+3,b[3]+3,r.z_mm+3]];state.iso=true;state.zoom=1;state.pitch=-1.05;state.yaw=-.6;$('#clip').value=180;$('#cliplabel').textContent='全部';$('#isolate').checked=true;const a=document.createElement('a');a.href=r.slice_figure;a.target='_blank';a.textContent='查看当前层与前一层的实际出丝图 ↗';$('#riskinfo').replaceChildren('红框：本体待复核区域，Z '+r.z_mm.toFixed(2)+' mm，面积 '+r.area_mm2.toFixed(3)+' mm²。该位置尚未通过实物验证。',document.createElement('br'),a);draw()}
function drawRiskBox(view){if(!state.risk)return;let b=state.risk.bounds_mm,z=state.risk.z_mm,lo=[b[0]-.025,b[1]-.025,z-.2],hi=[b[2]+.025,b[3]+.025,z+.02],verts=[];for(let axis=0;axis<3;axis++){let a=(axis+1)%3,d=(axis+2)%3;for(let i=0;i<2;i++)for(let j=0;j<2;j++)for(let k=0;k<2;k++){let p=lo.slice();p[axis]=k?hi[axis]:lo[axis];p[a]=i?hi[a]:lo[a];p[d]=j?hi[d]:lo[d];verts.push(...p,0,0,1)}}if(!riskBuffer)riskBuffer=gl.createBuffer();gl.bindBuffer(gl.ARRAY_BUFFER,riskBuffer);gl.bufferData(gl.ARRAY_BUFFER,new Float32Array(verts),gl.DYNAMIC_DRAW);gl.vertexAttribPointer(L.p,3,gl.FLOAT,false,24,0);gl.vertexAttribPointer(L.n,3,gl.FLOAT,false,24,12);gl.uniformMatrix4fv(L.M,false,column(view));gl.uniformMatrix4fv(L.world,false,column(I()));gl.uniform4f(L.color,.85,.08,.13,1);gl.disable(gl.BLEND);gl.disable(gl.DEPTH_TEST);gl.depthMask(false);gl.drawArrays(gl.LINES,0,verts.length/6);gl.enable(gl.DEPTH_TEST)}
'''
 js=js.replace('async function init(){',helper+'\nasync function init(){')
 js=js.replace("$('#plate').replaceChildren", "const query=new URLSearchParams(location.search);if(S.plates.some(p=>p.id===query.get('plate')))state.plate=query.get('plate');$('#risk').onchange=e=>{if(e.target.value===''){state.risk=null;state.focus=null;$('#riskinfo').textContent='';draw()}else focusRisk(+e.target.value)};$('#plate').replaceChildren",1)
 js=js.replace("await loadPlate();window.O22_FINS_UI", "await loadPlate();if(query.has('risk'))focusRisk(+query.get('risk'));else if(query.has('item')){const it=S.plates.find(p=>p.id===state.plate).items.find(i=>i.object_name.startsWith(query.get('item')+' '));if(it){state.item=it.object_name;state.iso=true;$('#item').value=state.item;$('#isolate').checked=true;info();draw()}}window.O22_FINS_UI")
 html=html.replace('<title>','<link rel="icon" href="data:,"><title>',1)
 html=html.replace('<div id="plateinfo">','<details><summary>待复核的本体起点</summary><label>来自实际 G-code 的定位<select id="risk"></select></label><p id="riskinfo" class="muted"></p><a href="验证说明.html#remaining">范围与判定方法</a></details><div id="plateinfo">')
 html=html.replace('安装教程仍按原编号查询，见','安装教程同时列出新版位置与原编号，见')
 html=html.replace('打印用同一种 PLA，无需 AMS。','打印用同一种 PLA，无需 AMS。每个零件与其支撑在打印文件中已合并成一个实体网格；彩色分区保留在本识别页面中。')
 html=html.replace('保留文件中的朝向、位置和部件分组。','保留文件中的朝向、位置和完整对象。不要重新自动朝向、单独落盘支撑或拆分后重排。')
 html=html.replace('数字几何、切片检查与实物验收分开记录。未进行实物打印或材料力学试验。当前验证详情见', '这是 O22-F2 工程试打版。支撑主体、接触齿与落盘几何检查通过；实际 G-code 仍有 148 处本体小区域被标记为与前层缺少覆盖，已提供定位与相邻层图。尚未判定这些位置可可靠打印，也未做实物打印或受力仿真。详情见')
 html=html.replace('先使用 S 盘验证拆除与配合。','先用 S01 验证拆齿与配合；S01 不能替代胸架等高件的单件验证。')
 html=html.replace('<h2>新版与原版的差异</h2>','<h2>实际几何示例</h2><p>左：头部 C01；中：左脚骨架；右：胸架。胸架仍有最高约 90.8 mm 的宽鳍，配有横向加强肋，仍需实物验证。</p><a href="blender/O22_F2_Final_Reference.blend"><img style="width:100%;border-radius:8px" src="blender/final_reference.png" alt="最终头部、左脚和胸架的实际三维几何：蓝色零件、橙色宽鳍、黄色连接齿"></a><h2>新版与原版的差异</h2>')
 html=html.replace('<a href="blender/O22_F2_Orientation_Study.blend">','<a href="blender/O22_F2_Final_Reference.blend">最终几何 Blender 文件</a> · <a href="blender/O22_F2_Orientation_Study.blend">')
 html=html.replace('<script src="viewer.js">','<script src="risk-data.js"></script><script src="viewer.js">')
 write(O/'viewer.js',js);write(O/'index.html',html)

def assembly(manifest):
 main=[it for p in manifest['plates'] if not p.get('optional') for it in p['items']]
 mapping={it['original_object_name'].split()[0]:it['object_name'].split()[0] for it in main};assert len(mapping)==186
 def translate(s):return re.sub(r'\bA\d\d-\d\d\b',lambda m:mapping.get(m[0],m[0])+'（原 '+m[0]+'）' if m[0] in mapping else m[0],s)
 class Relabel(HTMLParser):
  def __init__(self):super().__init__(convert_charrefs=False);self.out=[];self.skip=0;self.count=0
  def handle_starttag(self,t,a):self.out.append(self.get_starttag_text());self.skip+=int(t in ['script','style'])
  def handle_startendtag(self,t,a):self.out.append(self.get_starttag_text())
  def handle_endtag(self,t):self.out.append('</'+t+'>');self.skip-=int(t in ['script','style'])
  def handle_data(self,s):
   if not self.skip:
    self.count+=len(re.findall(r'\bA\d\d-\d\d\b',s));s=translate(s)
    s=s.replace('另有可选 T01 两件传感器小样','另有 S01 盘 7 个额外试件').replace('按排盘编号图把零件装袋','按彩色支撑页中的新版 F 位置把零件装袋').replace('可点击盘图放大编号，也可以直接打开对应步骤','旧盘图仅供原编号分组参考；新版 F 盘请从彩色支撑页查看，也可以直接打开对应步骤')
    s=s.replace('对应 A1 mini 打印盘 A01–A10。','本次打印使用 F01–F11。下方保留原分组便于核对零件身份，取件请使用每行的新版 F 盘位置。').replace('打印盘 A','原编号分组 A').replace('盘内编号 / 打印号','新版位置（原编号） / 打印号')
    s=re.sub(r'本步需打开打印盘：[A0-9、，\s]+。','本步请按下表的新版 F 盘位置取件。',s)
   self.out.append(s)
  def handle_entityref(self,n):self.out.append('&'+n+';')
  def handle_charref(self,n):self.out.append('&#'+n+';')
  def handle_decl(self,d):self.out.append('<!'+d+'>')
  def handle_comment(self,d):self.out.append('<!--'+d+'-->')
 src=B/'a1mini_fins/assembly';dst=O/'assembly';sp=src/'tutorials/assembly-o22';dp=dst/'tutorials/assembly-o22'
 raw=read(sp/'index.html').replace('O22-F1','O22-F2')
 banner='<p style="padding:14px;background:#fff4dc">本教程配套 O22-F2：每件的新版 F 盘位置已标出，括号保留原 A 编号。原 A 盘示意图仅用于历史分组辨认，不能用于本版排盘。<a href="../../../index.html">新版彩色支撑与打印入口</a> · <a href="../../../验证说明.html">试打状态与待复核位置</a>。先拆除橙色支撑及黄色连接齿，再进行以下装配。S01 试件是额外零件，不计入主套数量；本教程 S01–S26 表示安装步骤。</p>'
 raw=re.sub(r'<p style="padding:14px;background:#fff4dc">.*?</p>',banner,raw,flags=re.S)
 parser=Relabel();parser.feed(raw);write(dp/'index.html',''.join(parser.out));print('ASSEMBLY RELABEL',parser.count,flush=True)
 md=translate(read(sp/'ASSEMBLY.zh-CN.md'));md=md.replace('打印盘 A','原编号分组 A')
 write(dp/'ASSEMBLY.zh-CN.md','# O22-F2 装配编号说明\n\n打印使用 F01–F11；以下位置已替换为“新编号（原 A 编号）”。原 A 盘图片仅保留分组参考。先按彩色支撑页拆除橙色与黄色结构。S01 试打盘是额外零件；教程 S01–S26 是装配步骤。\n\n'+md)
 guide=json.loads(read(sp/'guide-data.json'))
 for p in guide['parts'].values():
  addr=p.get('address');p['original_address']=addr
  if addr in mapping:p['address']=mapping[addr]+'（原 '+addr+'）';p['f2_plate']=mapping[addr].split('-')[0]
 guide['f2_plate_manifest_sha256']=hashlib.sha256((O/'manifest.json').read_bytes()).hexdigest();guide['plate_address_note']='F2 display addresses updated; original assembly geometry and original inventory dimensions retained.'
 write(dp/'guide-data.json',json.dumps(guide,ensure_ascii=False,separators=(',',':')))
 sc=json.loads(read(sp/'scene.json'))
 for p in sc['objects']:
  addr=p.get('address')
  if addr in mapping:p['original_address']=addr;p['address']=mapping[addr]+'（原 '+addr+'）'
 write(dp/'scene.json',json.dumps(sc,ensure_ascii=False,separators=(',',':')))
 write(dst/'README_F2.txt','此目录继承 O22 的 26 步安装、电子和校准资料。F2 仅改变打印朝向与可拆支撑，不改变装配零件形状。安装页面已在原编号前加入新版 F 盘位置。原 A 盘示意图为历史参考，打印请使用上级 projects 中的 F01–F11。彩色支撑页面可直接打开；安装页面的旋转 CAD 视图需通过本地预览服务打开，静态图文可直接阅读。\n')
 return mapping

def documentation(manifest,risk):
 geom=json.loads(read(O/'verification/geometry_final.json'));stats=[];totalt=totalroot=totalrisk=0
 for p in manifest['plates']:
  v=json.loads(read(O/'verification'/f"{p['id']}_extrusion_contacts.json"));n=json.loads(read(O/'verification'/f"{p['id']}_native_mesh.json"));t=len(v['teeth']);roots=len(v['fin_bed_roots']);rr=next(q['regions'] for q in risk['plates'] if q['plate']==p['id']);totalt+=t;totalroot+=roots;totalrisk+=len(rr)
  assert v['teeth_missing_printed_layer']==0 and all(x['first_layer_printed_mm2']>.01 for x in v['fin_bed_roots']);assert n['native_mesh_preserved'] and n['automatic_supports_disabled'];assert n['project_sha256']==hashlib.sha256((O/'projects'/v['project']).read_bytes()).hexdigest()
  stats.append({'plate':p['id'],'instances':len(p['items']),'teeth':t,'rooted_components':roots,'remaining_regions':len(rr),'project_sha256':n['project_sha256']})
 assert geom['all_geometry_checks_passed'] and sum(p['instances'] for p in stats if p['plate'].startswith('F'))==186
 summary={'version':'O22-F2','status':'engineering_trial','main_instances':186,'trial_instances':7,'source_types':150,'print_projects':12,'geometry_checks_pass':True,'design_tooth_instance_layer_presence_checks':totalt,'fin_components_with_printed_bed_footprint':totalroot,'remaining_candidate_regions':totalrisk,'residual_regions_locate_to_original_part':True,'physical_print_tested':False,'force_or_thermal_simulated':False,'plates':stats}
 write(O/'verification/delivery_summary.json',json.dumps(summary,ensure_ascii=False,indent=2))
 rows=''.join(f'<tr><td><a href="index.html?plate={p["plate"]}">{p["plate"]}</a></td><td>{p["instances"]}</td><td>{p["teeth"]}</td><td>{p["rooted_components"]}</td><td>{p["remaining_regions"]}</td><td><a href="verification/{p["plate"]}_native_mesh.json">网格</a> · <a href="verification/{p["plate"]}_extrusion_contacts.json">出丝</a></td></tr>' for p in stats)
 residual=''
 for p in risk['plates']:
  rs=''.join(f'<tr><td>{i+1}</td><td>{escape(r["object_name"])}</td><td>{r["z_mm"]:.2f}</td><td>{r["area_mm2"]:.3f}</td><td><a href="index.html?plate={p["plate"]}&amp;risk={i}">三维定位</a> · <a href="{r["slice_figure"]}">相邻层出丝图</a></td></tr>' for i,r in enumerate(p['regions']))
  residual+=f'<details><summary>{p["plate"]}：{len(p["regions"])} 处</summary><table><tr><th>序号</th><th>对象</th><th>G-code Z / mm</th><th>面积 / mm²</th><th>位置</th></tr>{rs}</table></details>'
 text=f'''<p><a href="index.html">← 彩色三维与打印文件</a> · <a href="assembly/tutorials/assembly-o22/index.html">安装教程</a></p><p>POSEDOLL / O22-F2 / 2026-10-06</p><h1>验证范围与试打说明</h1><div class="notice"><b>交付状态：工程试打版。</b>本版完成了支撑设计、几何检查和拓竹切片检查，尚未进行实物打印、拆除试验或有限元受力分析。另有 {totalrisk} 处本体出丝小区域缺少前一层覆盖，已全部列出；它们尚未获得可靠打印的结论。请勿把“成功生成切片”理解为“整套可直接批量打印”。</div><div class="stats"><div><b>150</b>原始零件网格类型</div><div><b>186 + 7</b>主套实例 + 额外试件</div><div><b>{totalt:,}</b>连接齿实例的逐层出丝存在检查</div><div><b>{totalroot}</b>支撑连通体有首层出丝</div></div><h2>本次纠正的结构问题</h2><p>在原 O22 零件上进行刚性旋转与排布，构造垂直落盘的宽鳍、底脚及必要的横向加强肋。连接齿与本体和鳍均有实际体积交叠；鳍主体与本体没有体积交叠。打印 3MF 中，零件与其可拆支撑已布尔合并；识别页中的蓝、橙、黄仍分别显示原始本体、鳍和齿。</p><p>150 种零件各做约 118–119 个重力方向的几何初筛，对问题较多的零件又比较了实际支撑构造后的候选结果。评价考虑高度、悬垂、落盘通路和可拆除空间。这是有限候选的几何搜索，不是全局最优证明，也不是材料受力模拟。</p><table><tr><th>示例</th><th>原摆放高度 → 新高度</th><th>设计要点</th></tr><tr><td>P033 头部 C01</td><td>45.2 → 23.0 mm</td><td>放低并增加可逐齿检查的实际连接</td></tr><tr><td>X050 头部骨架</td><td>72.6 → 40.3 mm</td><td>旋转后降低悬垂与支撑高度</td></tr><tr><td>W016 左脚骨架</td><td>84.6 → 37.9 mm</td><td>宽直板落盘，避免细长斜撑</td></tr><tr><td>X046 胸架</td><td>107.8 → 99.0 mm</td><td>最高鳍约 90.8 mm、宽约 23.4 mm、厚 2.4 mm，配横向加强肋；仍需高件试打</td></tr></table><p>多数鳍高不超过 35 mm。胸架与部分锁骨支撑是例外；并未把所有鳍都声称为“低矮”。横向加强属于几何改良，尚无可报告的安全系数或挠度。</p><img src="blender/final_reference.png" alt="最终支撑几何示例"><h2>已完成的数字检查</h2><ol><li>逐类型比较原网格与变换前网格，旋转矩阵行列式为 1；没有缩放或修改原零件轮廓。新添的牺牲连接齿仅位于支撑界面。</li><li>实体布尔检查：鳍主体与零件无体积交叠；每个齿连通分量同时接触零件和鳍；每个鳍连通分量到达 Z=0，并在 Z=0.1 mm 有非零截面。已有功能保护区也参与碰撞检查；它不能替代实物五金试配。</li><li>原生导出的 12 个 Bambu 3MF 与已验证的合并网格逐顶点、逐三角形比较；未出现切片器修网格改动，自动支撑关闭。</li><li>从工程内 G-code 的实际正向挤出路径、圆弧和 LINE_WIDTH 重建二维出丝覆盖。检查每个连接齿包围区域对应层均有出丝、每个支撑连通体的首层区域有出丝。{totalt:,} 个齿实例未发现缺失层，{totalroot} 个连通支撑体未发现首层缺失。这里的数量包括 7 个额外试件；连通体数量不是鳍板数量。</li><li>另外对全盘各层的出丝连通区域检查前层覆盖，结果见下方。上述逐齿区域存在性检查不等于测量实际粘接面积、抗弯强度或拆除力。</li></ol><p><a href="verification/geometry_final.json">逐零件几何证据</a> · <a href="verification/delivery_summary.json">交付汇总 JSON</a></p><table><tr><th>盘</th><th>实例</th><th>设计齿实例</th><th>支撑连通体</th><th>本体待复核区域</th><th>报告</th></tr>{rows}</table><h2 id="remaining">尚未解决的本体出丝区域</h2><p>判定方法：当前层面积大于 0.05 mm² 的出丝连通区域，与前一层向外扩 0.025 mm 后的交叠仍小于 0.001 mm²，就记为候选。圆弧折线弦误差不超过 0.015 mm，布尔坐标网格 0.0001 mm。该简化二维覆盖模型不能预测熔丝下垂、喷嘴拖拽或层间粘接。</p><p>这 {totalrisk} 处的包围矩形与对应高度的角色截面比较，均定位到蓝色原零件本体，未定位到橙色鳍或黄色齿。此结论用于定位，不表示它们是无害的桥接或已通过打印。部分是孔、内壁和局部轮廓附近的小段；最大候选约 2.53 mm²。当前保留原零件功能形状并交付这些未消除的位置，没有把它们隐去。</p><p>点击“三维定位”查看原几何与红框；点击“相邻层出丝图”查看灰色前层、蓝色当前层的实际出丝宽度。红框只是疑点范围。<a href="待复核出丝位置.csv">下载全部位置 CSV</a>。</p>{residual}<h2>试打、拆除和安装</h2><ol><li>先用 S01 小样盘检查首层、齿的连接、拆除手感与配合。它含 7 个额外原件，不替代 F01–F11 主套；S01 自身仍有 6 处已标出的本体疑点。</li><li>文件设置为 A1 mini、Generic PLA、0.4 mm 喷嘴、0.20 mm 首层及层高、按层打印、3 壁、20% 填充、自动支撑关闭。首层底脚已建模。材料、喷嘴或层高改变后，本次出丝证据不再直接适用。</li><li>保留完整对象的朝向、支撑与相对位置；需要单独试打胸架时，可在项目副本中移除其他完整对象，重新切片后重点看 F01 胸架的高鳍和第 83 mm 左右区域。S01 无法证明胸架高鳍在打印加速度下的稳定性。</li><li>冷却后扶住零件厚壁，先剪黄色齿，再视需要剪开橙色底脚连片，分段向原热盘方向退出。不要直接拉扯细轨、轴孔或薄弹片。连接齿嵌入本体，去除后可能留痕；先在样件验证再修整。</li><li>按新版 Fxx-nn 和括号内原 Axx-nn 分袋，试装实际轴、螺钉、轴承及电路板，再进入 26 步安装教程。特别留意对称件及重复 N003/N004 的所属关节。</li></ol><p>试打至少确认：所有鳍底脚粘牢；高鳍无持续摆动、层移或喷嘴碰撞；齿顶承接到本体而非分离；拆齿时本体不崩裂；配合孔、滑轨和薄片可正常装配。这些项目目前尚无实物记录。</p><h2>进一步仿真软件</h2><p>本机已有 Blender 5.2.2，本次用它检查真实几何、朝向和接触近景。定量静力分析可使用 <a href="https://blog.freecad.org/2025/09/16/getting-started-with-fem/">FreeCAD FEM / CalculiX</a>，但需要先定义材料、层间各向异性、载荷与热盘约束。模拟 FFF/FDM 打印过程的热变形，可考察商用 <a href="https://www.cadence.com/en_US/home/tools/msc-software/digimat.html">Digimat-AM</a>。两者用途不同；此包未附任何未经实际计算的应力云图或安全系数。</p><p class="muted">打印项目及报告均以交付清单 SHA-256 固定。朝向研究的 Blender 文件展示候选姿态；最终结果以 O22_F2_Final_Reference.blend、彩色页以及 projects 中 12 个打印项目为准。</p>'''
 write(O/'验证说明.html',page('O22-F2 验证范围与试打说明',text))
 write(O/'先读我.txt',f'''O22-F2 支撑鳍工程试打版 | 2026-10-06

1. 完整解压后，用 Chrome / Edge 打开 index.html。蓝色保留，橙色鳍板/底脚/加强肋移除，黄色为需剪断的连接齿。选择零件及连接齿可看实际接触近景。
2. projects/F01–F11 是主套 186 个实例（185 个零件 + 1 个焊接量规）；S01 是 7 个额外试件。打印用同种 PLA。保持 A1 mini / 0.4 mm / 0.20 mm / 按层打印 / 自动支撑关闭。每个本体与其支撑已合并为一个打印网格，不要拆开后重新落盘。
3. 支撑主体不穿入零件；齿与两侧有实际几何交叠；所有鳍从热盘起始。没有细长斜向主体支撑。胸架仍有约 90.8 mm 高、23.4 mm 宽、2.4 mm 厚的宽鳍和横向加强肋，不能声称已验证受力。
4. 数字检查：150 种原始网格保形，12 个原生打印项目网格检查通过。含样件的 {totalt} 个设计齿实例对应层均检测到出丝，{totalroot} 个支撑连通体有首层出丝。
5. 重要未完成验证：全盘另有 {totalrisk} 处原零件本体的局部出丝候选缺少前层覆盖，位置、相邻层图和判定局限见 验证说明.html 与 待复核出丝位置.csv。尚未证明这些区域可可靠打印。未进行实物打印、拆除试验或受力/热仿真。这不是整套批量打印验收通过的声明。
6. 先用 S01 验证连接与拆除，再验证胸架等高件；查看每盘疑点。冷却后扶住厚壁，剪黄齿，再分段去除橙色支撑。试配五金与 PCB 后按 assembly/tutorials/assembly-o22/index.html 的 26 步装配。教程已经加入新版 F 位置；原 A 盘示意图只用于历史分组。
7. 支撑三维页可直接离线打开；安装教程静态图文也可直接阅读。安装教程的旋转 CAD 视图需要本地 HTTP：有 Python 时运行 start_preview.py，浏览器会打开本包。服务仅绑定本机。关闭终端即停止。
8. blender 内 final_reference 为最终几何；orientation_study 为朝向候选比较；true_contact 为实际接触点近景。没有运行材料力学仿真。
''')
 write(O/'start_preview.py','''from pathlib import Path\nfrom http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler\nfrom functools import partial\nimport webbrowser\nroot=Path(__file__).resolve().parent\nserver=ThreadingHTTPServer(("127.0.0.1",0),partial(SimpleHTTPRequestHandler,directory=str(root)))\nurl=f"http://127.0.0.1:{server.server_port}/index.html"\nprint("Open",url," | Ctrl+C to stop",flush=True)\nwebbrowser.open(url)\ntry: server.serve_forever()\nexcept KeyboardInterrupt: pass\nfinally: server.server_close()\n''')
 print('DOCS',summary,flush=True)

if __name__=='__main__':
 manifest=json.loads(read(O/'manifest.json'));risk=json.loads(read(O/'verification/remaining_regions.json'))
 risk_figures(manifest,risk);improve_viewer(risk);assembly(manifest);documentation(manifest,risk)
