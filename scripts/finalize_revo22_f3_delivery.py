"""Finish O22-F3 delivery UI, assembly cross-references and honest validation notes.
Read-only with respect to CAD meshes and native print projects.
"""
from pathlib import Path
from html import escape
from html.parser import HTMLParser
import json,csv,re,hashlib,shutil
import numpy as np
from build_revo22_fins_v3 import R,B,O
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
  _,paths=extract_paths(O/'projects'/f"{plate['id']}_O22F3_PLA_fins.3mf",arc_tolerance_mm=.015,max_arc_segment_mm=.6)
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
 write(O/'verification/remaining_regions.json',json.dumps(risk,ensure_ascii=False,indent=2))
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
function focusRisk(i){let r=currentRisks()[i];if(!r)return;state.risk=r;$('#risk').closest('details').open=true;state.item=r.object_name;$('#item').value=state.item;$('#risk').value=i;info();let b=r.bounds_mm;state.focus=[[b[0]-3,b[1]-3,r.z_mm-3],[b[2]+3,b[3]+3,r.z_mm+3]];state.iso=true;state.zoom=1;state.pitch=-1.05;state.yaw=-.6;$('#clip').value=180;$('#cliplabel').textContent='全部';$('#isolate').checked=true;const a=document.createElement('a');a.href=r.slice_figure;a.target='_blank';a.textContent='查看当前层与前一层的实际出丝图 ↗';$('#riskinfo').replaceChildren('红框：局部待复核区域，Z '+r.z_mm.toFixed(2)+' mm，面积 '+r.area_mm2.toFixed(3)+' mm²。该位置尚未通过实物验证。',document.createElement('br'),a);draw()}
function drawRiskBox(view){if(!state.risk)return;let b=state.risk.bounds_mm,z=state.risk.z_mm,lo=[b[0]-.025,b[1]-.025,z-.2],hi=[b[2]+.025,b[3]+.025,z+.02],verts=[];for(let axis=0;axis<3;axis++){let a=(axis+1)%3,d=(axis+2)%3;for(let i=0;i<2;i++)for(let j=0;j<2;j++)for(let k=0;k<2;k++){let p=lo.slice();p[axis]=k?hi[axis]:lo[axis];p[a]=i?hi[a]:lo[a];p[d]=j?hi[d]:lo[d];verts.push(...p,0,0,1)}}if(!riskBuffer)riskBuffer=gl.createBuffer();gl.bindBuffer(gl.ARRAY_BUFFER,riskBuffer);gl.bufferData(gl.ARRAY_BUFFER,new Float32Array(verts),gl.DYNAMIC_DRAW);gl.vertexAttribPointer(L.p,3,gl.FLOAT,false,24,0);gl.vertexAttribPointer(L.n,3,gl.FLOAT,false,24,12);gl.uniformMatrix4fv(L.M,false,column(view));gl.uniformMatrix4fv(L.world,false,column(I()));gl.uniform4f(L.color,.85,.08,.13,1);gl.disable(gl.BLEND);gl.disable(gl.DEPTH_TEST);gl.depthMask(false);gl.drawArrays(gl.LINES,0,verts.length/6);gl.enable(gl.DEPTH_TEST)}
'''
 js=js.replace('async function init(){',helper+'\nasync function init(){')
 js=js.replace("$('#plate').replaceChildren", "const query=new URLSearchParams(location.search);if(S.plates.some(p=>p.id===query.get('plate')))state.plate=query.get('plate');$('#risk').onchange=e=>{if(e.target.value===''){state.risk=null;state.focus=null;$('#riskinfo').textContent='';draw()}else focusRisk(+e.target.value)};$('#plate').replaceChildren",1)
 js=js.replace("await loadPlate();window.O22_FINS_UI", "await loadPlate();if(query.has('risk'))focusRisk(+query.get('risk'));else if(query.has('item')){const it=S.plates.find(p=>p.id===state.plate).items.find(i=>i.object_name.startsWith(query.get('item')+' '));if(it){state.item=it.object_name;state.iso=true;$('#item').value=state.item;$('#isolate').checked=true;info();draw()}}window.O22_FINS_UI")
 html=html.replace('<title>','<link rel="icon" href="data:,"><title>',1)
 html=html.replace('<div id="plateinfo">','<details><summary>待复核的出丝起点</summary><label>来自实际 G-code 的定位<select id="risk"></select></label><p id="riskinfo" class="muted"></p><a href="验证说明.html#remaining">范围与判定方法</a></details><div id="plateinfo">')
 html=html.replace('安装教程仍按原编号查询，见','安装教程同时列出新版位置与原编号，见')
 html=html.replace('打印用同一种 PLA，无需 AMS。','打印用同一种 PLA，无需 AMS。每个零件与其支撑在打印文件中已合并成一个实体网格；彩色分区保留在本识别页面中。')
 html=html.replace('保留文件中的朝向、位置和部件分组。','保留文件中的朝向、位置和完整对象。不要重新自动朝向、单独落盘支撑或拆分后重排。')
 html=html.replace('数字几何、切片检查与实物验收分开记录。未进行实物打印或材料力学试验。当前验证详情见', '这是 O22-F3 工程试打版。支撑主体、接触齿与落盘几何检查通过；实际 G-code 仍有 {RISKCOUNT} 处局部区域被标记为与前层缺少覆盖，已提供定位与相邻层图。尚未判定这些位置可可靠打印，也未做实物打印或受力仿真。详情见')
 html=html.replace('先使用 S 盘验证拆除与配合。','先用 S01 验证拆齿与配合；S01 不能替代胸架等高件的单件验证。')
 html=html.replace('<h2>新版与原版的差异</h2>','<h2>实际几何示例</h2><p>胸架最终实际网格。橙色落盘宽鳍带横向加强；黄色连接齿与本体相接。</p><a href="blender/final_chest.blend"><img style="width:100%;border-radius:8px" src="blender/final_chest.png" alt="最终胸架的实际三维几何：蓝色零件、橙色宽鳍、黄色连接齿"></a><h2>新版与原版的差异</h2>')
 html=html.replace('<a href="blender/final_chest.blend">','<a href="blender/final_chest.blend">最终几何 Blender 文件</a> · <a href="blender/final_chest.blend">')
 html=html.replace('<script src="viewer.js">','<script src="risk-data.js"></script><script src="viewer.js">')
 html=html.replace('{RISKCOUNT}',str(sum(len(p['regions']) for p in risk['plates'])))
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
    s=s.replace('对应 A1 mini 打印盘 A01–A10。','本次打印使用 F 系列主套盘。下方保留原分组便于核对零件身份，取件请使用每行的新版 F 盘位置。').replace('打印盘 A','原编号分组 A').replace('盘内编号 / 打印号','新版位置（原编号） / 打印号')
    s=re.sub(r'本步需打开打印盘：[A0-9、，\s]+。','本步请按下表的新版 F 盘位置取件。',s)
   self.out.append(s)
  def handle_entityref(self,n):self.out.append('&'+n+';')
  def handle_charref(self,n):self.out.append('&#'+n+';')
  def handle_decl(self,d):self.out.append('<!'+d+'>')
  def handle_comment(self,d):self.out.append('<!--'+d+'-->')
 src=B/'a1mini_fins/assembly';dst=O/'assembly';sp=src/'tutorials/assembly-o22';dp=dst/'tutorials/assembly-o22'
 raw=read(sp/'index.html').replace('O22-F1','O22-F3')
 banner='<p style="padding:14px;background:#fff4dc">本教程配套 O22-F3：每件的新版 F 盘位置已标出，括号保留原 A 编号。原 A 盘示意图仅用于历史分组辨认，不能用于本版排盘。<a href="../../../index.html">新版彩色支撑与打印入口</a> · <a href="../../../验证说明.html">试打状态与待复核位置</a>。先拆除橙色支撑及黄色连接齿，再进行以下装配。S01 试件是额外零件，不计入主套数量；本教程 S01–S26 表示安装步骤。</p>'
 raw=re.sub(r'<p style="padding:14px;background:#fff4dc">.*?</p>',banner,raw,flags=re.S)
 parser=Relabel();parser.feed(raw);write(dp/'index.html',''.join(parser.out));print('ASSEMBLY RELABEL',parser.count,flush=True)
 md=translate(read(sp/'ASSEMBLY.zh-CN.md'));md=md.replace('打印盘 A','原编号分组 A')
 write(dp/'ASSEMBLY.zh-CN.md','# O22-F3 装配编号说明\n\n打印使用 F 系列主套盘；以下位置已替换为“新编号（原 A 编号）”。原 A 盘图片仅保留分组参考。先按彩色支撑页拆除橙色与黄色结构。S01 试打盘是额外零件；教程 S01–S26 是装配步骤。\n\n'+md)
 guide=json.loads(read(sp/'guide-data.json'))
 for p in guide['parts'].values():
  addr=p.get('address');p['original_address']=addr
  if addr in mapping:p['address']=mapping[addr]+'（原 '+addr+'）';p['f3_plate']=mapping[addr].split('-')[0]
 guide['f3_plate_manifest_sha256']=hashlib.sha256((O/'manifest.json').read_bytes()).hexdigest();guide['plate_address_note']='F3 display addresses updated; original assembly geometry and original inventory dimensions retained.'
 write(dp/'guide-data.json',json.dumps(guide,ensure_ascii=False,separators=(',',':')))
 sc=json.loads(read(sp/'scene.json'))
 for p in sc['objects']:
  addr=p.get('address')
  if addr in mapping:p['original_address']=addr;p['address']=mapping[addr]+'（原 '+addr+'）'
 write(dp/'scene.json',json.dumps(sc,ensure_ascii=False,separators=(',',':')))
 write(dst/'README_F3.txt','此目录继承 O22 的 26 步安装、电子和校准资料。F3 仅改变打印朝向与可拆支撑，不改变装配零件形状。安装页面已在原编号前加入新版 F 盘位置。原 A 盘示意图为历史参考，打印请使用上级 projects 中的 F 系列主套盘。彩色支撑页面可直接打开；安装页面的旋转 CAD 视图需通过本地预览服务打开，静态图文可直接阅读。\n')
 return mapping


def documentation(manifest,risk):
 geom=json.loads(read(O/'verification/geometry_final.json'));selection=json.loads(read(O/'verification/selection.json'));stats=[]
 for p in manifest['plates']:
  pid=p['id'];engines={}
  for eng,folder,projects in [('orca',O/'verification',O/'projects'),('bambu',O/'verification/bambu',O/'crosscheck_bambu')]:
   v=json.loads(read(folder/f'{pid}_extrusion_contacts.json'));n=json.loads(read(folder/f'{pid}_native_mesh.json'));path=projects/v['project'];sha=hashlib.sha256(path.read_bytes()).hexdigest()
   assert v['project_sha256']==n['project_sha256']==sha
   assert v['teeth_missing_printed_layer']==0 and all(x['first_layer_printed_mm2']>.01 for x in v['fin_bed_roots']),(eng,pid,v['teeth_missing_printed_layer'])
   assert n['native_mesh_preserved'] and n['automatic_supports_disabled']
   engines[eng]={'remaining_regions':len(v['floating_printed_components']),'area_mm2':sum(x['area_mm2'] for x in v['floating_printed_components']),'max_area_mm2':max([x['area_mm2'] for x in v['floating_printed_components']],default=0),'teeth':len(v['teeth']),'roots':len(v['fin_bed_roots']),'embedded_tip_discretization_layers':v.get('embedded_tip_discretization_layer_count',0),'project_sha256':sha}
  stats.append({'plate':pid,'instances':len(p['items']),'optional':p['optional'],**engines})
 totals={eng:{key:sum(p[eng][key] for p in stats) for key in ['remaining_regions','area_mm2','teeth','roots','embedded_tip_discretization_layers']} for eng in ['orca','bambu']}
 for eng in totals:totals[eng]['max_area_mm2']=max(p[eng]['max_area_mm2'] for p in stats)
 old=json.loads(read(B/'a1mini_fins_v2/verification/remaining_regions.json'));oldregions=[x for p in old['plates'] for x in p['regions']];baseline={'bambu_regions':len(oldregions),'bambu_area_mm2':sum(x['area_mm2'] for x in oldregions),'bambu_max_area_mm2':max(x['area_mm2'] for x in oldregions)}
 summary={'version':'O22-F3','status':'engineering_trial','main_instances':186,'sample_instances':7,'source_types':150,'print_plates':len(stats),'native_projects':len(stats)*2,'geometry_checks_pass':True,'source_body_meshes_unchanged':True,'changed_print_orientation_types':selection['selected_rotations_total_types'],'automatic_supports_disabled':True,'all_fin_roots_have_actual_first_layer_extrusion':True,'tooth_print_presence_checks_pass':True,'baseline_F2':baseline,'totals':totals,'plates':stats,'physical_print_tested':False,'fin_force_or_thermal_simulated':False,'complete_print_reliability_certified':False}
 write(O/'verification/delivery_summary.json',json.dumps(summary,ensure_ascii=False,indent=2))
 rows=''.join(f'<tr><td><a href="index.html?plate={p["plate"]}">{p["plate"]}</a></td><td>{p["instances"]}</td><td>{p["orca"]["teeth"]}</td><td>{p["orca"]["roots"]}</td><td>{p["orca"]["remaining_regions"]} / {p["bambu"]["remaining_regions"]}</td><td><a href="projects/{p["plate"]}_O22F3_PLA_fins.3mf">Orca</a> · <a href="crosscheck_bambu/{p["plate"]}_O22F3_PLA_fins.3mf">拓竹</a></td></tr>' for p in stats)
 residual=''
 for p in risk['plates']:
  rr=''.join(f'<tr><td>{i+1}</td><td>{escape(r["object_name"])}</td><td>{r["z_mm"]:.2f}</td><td>{r["area_mm2"]:.3f}</td><td><a href="index.html?plate={p["plate"]}&amp;risk={i}">三维定位</a> · <a href="{r["slice_figure"]}">实际出丝图</a></td></tr>' for i,r in enumerate(p['regions']))
  residual+=f'<details><summary>{p["plate"]}：{len(p["regions"])} 处候选</summary><table><tr><th>序号</th><th>对象</th><th>Z / mm</th><th>面积 / mm²</th><th>检查</th></tr>{rr}</table></details>'
 chest=json.loads(read(O/'design/X046.json'));oldchest=json.loads(read(B/'a1mini_fins_v2/design/X046.json'));height=max(q['height_mm'] for q in chest['segments']);oldheight=max(q['height_mm'] for q in oldchest['segments'])
 tool=json.loads(read(O/'verification/toolchain.json'));pkgs='、'.join(k+' '+v for k,v in tool['packages'].items())
 text=f'''<p><a href="index.html">← 彩色三维与打印文件</a> · <a href="assembly/tutorials/assembly-o22/index.html">安装教程</a></p><p>POSEDOLL / O22-F3</p><h1>验证结果与使用说明</h1><div class="notice"><b>这是工程试打版。</b>支撑落盘、几何接触与实际出丝检查通过；尚未进行实物打印、拆除或力学验收。Orca 切片仍有 {totals['orca']['remaining_regions']} 处局部出丝候选缺少前层覆盖，拓竹有 {totals['bambu']['remaining_regions']} 处。下方保留全部定位，不能据此宣称整套打印成功率已经验证。</div><div class="stats"><div><b>150</b>保留原形状的零件类型</div><div><b>186 + 7</b>主套实例 + 额外试件</div><div><b>{len(stats)} × 2</b>同一几何，两种原生切片工程</div><div><b>{selection['selected_rotations_total_types']}</b>采用新打印朝向的类型</div></div><h2>胸架 X046 的具体变化</h2><p>胸架单独放在 F01，盒子开口转向上方；多个宽鳍分布在盒体下方和骨架悬挑下方，全部从热盘起始。较高面板带横向加强，后补的 6 块局部面板又增加 17 根横向肋。主体不得穿入零件，只有黄色牺牲齿允许嵌入。</p><p>整件打印高度由 {oldchest['new_height_mm']:.1f} 增为 {chest['new_height_mm']:.1f} mm；最高鳍由 {oldheight:.1f} 降为 {height:.1f} mm。支撑几何体积由 {oldchest['support_volume_mm3']/1000:.1f} 增为 {chest['support_volume_mm3']/1000:.1f} cm³。这个取舍增加了支撑用量，换取更分散的支承和较少的大面积跨空；没有把高件说成已经通过抗摆动测试。</p><img src="blender/final_chest.png" alt="最终胸架实际网格，蓝色保留，橙色支撑，黄色连接齿"><h2>选择依据与零件改形检查</h2><p>先筛选朝向和落盘通路，再实际切片。部分几何评分较好的候选在出丝检查中退步，已恢复 F2 朝向；传感器卡匣也保留弹片长度在层面内的方向。最终保留的朝向变化是 {', '.join(['X046']+selection['rotated_non_chest_types'])}。</p><p>尝试过在胸架内部固定柱增加四条永久加强筋，并检查了 1,521 个装配实体和 107 个姿态样本。它们改善了旧角度，但在最终新角度下没有进一步改善切片，因此没有采用。最终 150 种本体网格只作刚性变换，孔径、轴线、限位、PCB 高度和装配轮廓全部保留；姿态范围没有因本体改形而改变。</p><p>连接齿中不参与有效连接的细尖尾已修剪；五处原有短齿加宽到 1.0 × 1.1 mm，修正局部层不出丝的问题。接触示例是实际网格裁切，不是示意图。</p><img src="blender/contact_closeup.png" alt="实际连接齿及两侧实体的近景"><h2>数字检查范围</h2><ol><li>150 种本体与源网格逐顶点、逐三角形核对；旋转矩阵无缩放。鳍与本体的体积交叠为零，功能保护区无支撑侵入。</li><li>每个鳍连通体到达 Z=0，在首层有截面与实际出丝；每个齿连通体都与鳍和本体有实际体积交叠。高面板的加强记录也被检查。</li><li>OrcaSlicer 2.4.2 和 Bambu Studio 2.8.2.61 分别导出原生工程。导出前后的三角网格和位置核对通过，未发生自动修网格，自动支撑关闭。</li><li>使用 G-code 的实际正向挤出路径、圆弧与线宽重建二维覆盖，检查真实齿截面，不只检查包围框。{totals['orca']['teeth']} 个齿实例及 {totals['orca']['roots']} 个支撑连通体完成检查。完全嵌入本体且小于 0.02 mm² 的离散尖端，只有在其它层已能证明两端有出丝连接时才单独注明；悬空齿颈缺层不会被豁免。详细原始记录保留在报告中。</li><li>另外检测当前层中面积大于 0.05 mm²、与前层外扩 0.025 mm 后交叠仍小于 0.001 mm² 的出丝连通区域。它是复核线索，不是熔丝、受力或冷却仿真。</li></ol><table><tr><th>盘</th><th>实例</th><th>连接齿</th><th>落盘支撑连通体</th><th>待复核区域<br>Orca / 拓竹</th><th>原生工程</th></tr>{rows}</table><p><a href="verification/geometry_final.json">逐件几何报告</a> · <a href="verification/delivery_summary.json">汇总与文件哈希</a> · <a href="verification/selection.json">候选取舍</a></p><h2>与 F2 的同类检测对比</h2><p>拓竹出丝覆盖检测：F2 共 {baseline['bambu_regions']} 处、总面积 {baseline['bambu_area_mm2']:.2f} mm²、最大单处 {baseline['bambu_max_area_mm2']:.3f} mm²；F3 共 {totals['bambu']['remaining_regions']} 处、总面积 {totals['bambu']['area_mm2']:.2f} mm²、最大单处 {totals['bambu']['max_area_mm2']:.3f} mm²。数量与面积都保留，避免只报告有利指标。两种切片器的结果也未混为一组。</p><h2 id="remaining">仍需复核的出丝区域</h2><p>下面定位来自交付的 Orca 工程。红框表示候选范围；灰色为前层、蓝色为当前层的实际线宽覆盖。存在疑点时，不能把它自动解释为可安全桥接。<a href="待复核出丝位置.csv">全部位置 CSV</a>。</p>{residual}<h2>打印、拆除与安装</h2><ol><li>先用 S01 验证齿的连接和拆除，再单独试打 F01 胸架。F01 是主套胸架；S01 的 7 件是额外试件，不计入主套 186 件。F02–F12 为其余主套。</li><li>在对应切片器中以“项目”打开原生 3MF。配置为 A1 mini、Generic PLA、0.4 mm 喷嘴、0.20 mm 层高与首层、3 壁、20% 填充、按层打印、自动支撑关闭。改变材料、喷嘴、层高或朝向后需要重新检查。</li><li>每个零件与其支撑已合并成完整打印对象。保留朝向与内部相对位置；彩色页面只用于区分保留和移除部位，打印无需 AMS。</li><li>冷却后扶住厚壁，先剪黄色连接齿，再分段剪开橙色底脚连接并向原热盘方向退出。不要硬拉细轨、孔口或弹片。颜色显示的是实际网格；近景裁切不会修改打印文件。</li><li>按新版 Fxx-nn 和括号内的原 Axx-nn 编号分袋，试配实际五金与 PCB，再按 26 步教程装配。教程中的旧 A 盘示意图仅用于历史分组，新排盘以本页面为准。</li></ol><h2>已经准备好的工具</h2><p>当前项目 Python 虚拟环境已具备 {pkgs}。Orca、拓竹和 Blender 已实际运行；FreeCAD / Gmsh / CalculiX 的工具基准也已验证。本次未将工具基准称为人偶受力仿真，未报告未经计算的应力、安全系数或热变形。</p><p><a href="verification/toolchain.json">Python 与 Orca 工具检查</a> · <a href="verification/freecad_toolchain.json">FreeCAD 求解器基准</a></p>'''
 write(O/'验证说明.html',page('O22-F3 验证与使用说明',text))
 write(O/'先读我.txt',f'''O22-F3 支撑鳍工程试打版

打开 index.html 查看实际彩色三维和下载各盘。蓝色保留；橙色鳍、底脚、加强肋移除；黄色连接齿剪断。无需 AMS。

projects 是 13 个 Orca 原生切片工程；crosscheck_bambu 是同一几何的 13 个拓竹原生工程。不要把两套都打印一遍。
F01 是胸架单件主套盘；F02–F12 是其它主套，共 186 个实例（185 个安装件 + 1 个量规）。S01 为 7 个额外试件。
A1 mini / Generic PLA / 0.4 mm 喷嘴 / 0.20 mm 首层和层高 / 按层打印 / 自动支撑关闭。每个本体与支撑合并为完整对象，不要拆开后重新落盘。

150 种本体保持原形状，{selection['selected_rotations_total_types']} 种调整了打印朝向。全部鳍落盘，鳍主体不穿模，连接齿有实际实体连接。几何与两种切片器的出丝检查记录见 验证说明.html。

仍需复核：Orca 有 {totals['orca']['remaining_regions']} 处局部出丝候选缺少前层覆盖；拓竹有 {totals['bambu']['remaining_regions']} 处。未进行实物打印、拆除、力学或打印过程热仿真，不能视作整套量产验收通过。
先试 S01，再试 F01；安装教程为 assembly/tutorials/assembly-o22/index.html，已更新 F 位置与原 A 编号对照。

彩色页可直接离线打开；安装教程的旋转三维需要本地 HTTP，可运行 start_preview.py。静态图文也可直接阅读。
''')
 print('DOCUMENTED',json.dumps(totals),flush=True)
 return summary

if __name__=='__main__':
 manifest=json.loads(read(O/'manifest.json'));risk=json.loads(read(O/'verification/remaining_regions.json'))
 risk_figures(manifest,risk);improve_viewer(risk);assembly(manifest);documentation(manifest,risk)
