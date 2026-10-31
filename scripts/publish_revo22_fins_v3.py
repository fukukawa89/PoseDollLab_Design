import re,json,shutil,csv,base64,gzip,collections
from pathlib import Path
import numpy as np
from build_revo22_fins_v3 import R,B,O
from pack_revo22_a1mini import read_mesh

def encoded(a,t):return base64.b64encode(gzip.compress(np.asarray(a,dtype=t).tobytes(),mtime=0)).decode()
def run():
 manifest=json.loads((O/'manifest.json').read_text());plates=manifest['plates'];meshes={};reports={}
 for p in plates:
  for it in p['items']:
   pid=it['id']
   if pid in meshes:continue
   n=dict(np.load(O/'parts'/f'{pid}.npz'));sv,sf=read_mesh(B/it['source_3mf']);assert np.array_equal(sv,n['source_v'])
   r=json.loads((O/'design'/f'{pid}.json').read_text())
   if 'added_body_v' in n:
    assert np.array_equal(sf,n['source_f']) and r['body_change']['geometric_fit_pass']
    n['v']=sv@np.array(r['orientation']['matrix']).T+r['orientation']['source_translation_mm'];n['f']=sf
   else:
    assert np.array_equal(sf,n['f']) and np.allclose(n['v'],sv@np.array(r['orientation']['matrix']).T+r['orientation']['source_translation_mm'],atol=1e-10)
   reports[pid]=r;meshes[pid]={}
   for role,vk,fk in [('part','v','f'),('fin','fin_v','fin_f'),('teeth','teeth_v','teeth_f'),('retained','added_body_v','added_body_f')]:
    if fk in n and len(n[fk]):meshes[pid][role]={'v':encoded(n[vk],'<f4'),'f':encoded(n[fk],'<u4')}
 scene={'plates':plates,'meshes':meshes,'reports':reports};(O/'scene.js').write_text('window.O22_FINS='+json.dumps(scene,ensure_ascii=False,separators=(',',':'))+';',encoding='utf-8')
 with (O/'新旧盘号与安装编号对照.csv').open('w',encoding='utf-8-sig',newline='') as f:
  w=csv.writer(f);w.writerow(['新版打印盘','新版对象','原安装编号','零件号','安装部位','鳍板数','连接齿数','原高度mm','新高度mm'])
  for p in plates:
   for it in p['items']:
    r=reports[it['id']];w.writerow([p['id'],it['object_name'],it['original_object_name'],it['id'],it['part'],r['support_count'],len(r['teeth']),r['source_height_mm'],r['new_height_mm']])
 src=B/'a1mini_fins';js=(src/'viewer.js').read_text(encoding='utf-8');js=js.replace("plate:'S00'","plate:'S01'").replace('O22F1','O22F3')
 info="""function info(){let p=S.plates.find(p=>p.id===state.plate),it=p.items.find(i=>i.object_name===state.item);$('#plateinfo').textContent=p.title+' · '+p.items.length+' 件';$('#contact').replaceChildren(new Option('选择连接齿近看',''));if(!it){$('#info').textContent='选择零件后，可逐个放大检查黄色连接齿。';$('#directions').textContent='取件冷却后，先剪连接齿，再向原热盘方向取下鳍板。';return}let r=S.reports[it.id];$('#info').textContent=it.object_name+'。原安装编号：'+it.original_object_name+'。高度 '+r.source_height_mm.toFixed(1)+' → '+r.new_height_mm.toFixed(1)+' mm；'+r.support_count+' 块设计鳍板，'+r.teeth.length+' 个连接齿。'+(r.support_count?'支撑主体与本体无体积交叠。':'无需额外支撑。');$('#directions').textContent='先剪黄色连接齿，必要时剪开橙色底脚间连片，再朝打印时的热盘方向分段退出。较高鳍板连同加强肋一起取下。不要从细轨或配合孔处用力。';for(let j=0;j<r.teeth.length;j++){let t=r.teeth[j];$('#contact').add(new Option('齿 '+(j+1)+' · 高 '+t.contact_point_mm[2].toFixed(2)+' mm · 嵌入 '+t.part_bite_mm3.toFixed(3)+' mm³',j))}}
"""
 js=re.sub(r'function info\(\).*?\nasync function loadPlate',info+'async function loadPlate',js,flags=re.S)
 js=js.replace("state.item='';state.iso=false", "state.item='';state.focus=null;state.iso=false")
 js=js.replace("let center=lo.map", "if(state.focus){lo=state.focus[0];hi=state.focus[1]}let center=lo.map")
 js=js.replace('Math.max(20,','Math.max(5,')
 js=js.replace("gl.uniform1f(L.clip,+$('#clip').value);", "gl.uniform1f(L.clip,+$('#clip').value);gl.uniform3fv(L.cutlo,new Float32Array(state.focus?state.focus[0]:[-1000,-1000,-1000]));gl.uniform3fv(L.cuthi,new Float32Array(state.focus?state.focus[1]:[1000,1000,1000]));")
 js=js.replace('varying float height;void main(){vec4 v=', 'varying float height;varying vec3 worldpos;void main(){worldpos=(world*vec4(p,1.)).xyz;vec4 v=')
 js=js.replace('varying float height;void main(){if(height>clip)discard;', 'varying float height;varying vec3 worldpos;uniform vec3 cutlo;uniform vec3 cuthi;void main(){if(height>clip||any(lessThan(worldpos,cutlo))||any(greaterThan(worldpos,cuthi)))discard;')
 js=js.replace("clip:gl.getUniformLocation(program,'clip')", "clip:gl.getUniformLocation(program,'clip'),cutlo:gl.getUniformLocation(program,'cutlo'),cuthi:gl.getUniformLocation(program,'cuthi')")
 js=js.replace("state.item=e.target.value;info();draw()", "state.item=e.target.value;state.focus=null;info();draw()")
 js=js.replace("$('#reset').onclick=()=>{state.zoom=1;", "$('#reset').onclick=()=>{state.focus=null;state.zoom=1;")
 injection="""$('#contact').onchange=e=>{if(e.target.value===''){state.focus=null;draw();return}let p=S.plates.find(p=>p.id===state.plate),it=p.items.find(i=>i.object_name===state.item);if(!it)return;let t=S.reports[it.id].teeth[+e.target.value],point=t.contact_point_mm.map((_,i)=>it.rotation_matrix[i].reduce((s,k,j)=>s+k*t.contact_point_mm[j],it.translation_mm[i]));let bb=t.bounds_mm,cc=[];for(let x of [bb[0],bb[3]])for(let y of [bb[1],bb[4]])for(let z of [bb[2],bb[5]]){let v=[x,y,z];cc.push(it.rotation_matrix.map((row,i)=>row.reduce((s,k,j)=>s+k*v[j],it.translation_mm[i])))}state.focus=[point.map((_,i)=>Math.min(...cc.map(v=>v[i]))-(i===2?1.5:2.5)),point.map((_,i)=>Math.max(...cc.map(v=>v[i]))+(i===2?1.5:2.5))];state.iso=true;state.zoom=1;$('#isolate').checked=true;state.pitch=-1.15;state.yaw=-.5;draw()};"""
 js=js.replace("let drag;c.onpointerdown",injection+"let drag;c.onpointerdown")
 js=js.replace("['part','fin','teeth']", "['part','fin','teeth','retained']")
 js=js.replace("teeth:$('#showteeth').checked", "teeth:$('#showteeth').checked,retained:$('#showretained').checked")
 js=js.replace("['showpart','showfin','showteeth','ghost']", "['showpart','showfin','showteeth','showretained','ghost']")
 js=js.replace("o.role==='part'?[.48,.68,.76]", "o.role==='retained'?[.65,.31,.78]:o.role==='part'?[.48,.68,.76]")
 js=js.replace("此处显示实际输出几何", "此处显示实际输出几何")
 (O/'viewer.js').write_text(js,encoding='utf-8')
 css=re.search(r'<style>(.*?)</style>',(src/'index.html').read_text(encoding='utf-8'),re.S).group(1)
 html='''<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>O22-F3 支撑鳍与安装</title><style>'''+css+'''</style>
<header><div><p>POSEDOLL / O22-F3</p><h1>垂直落盘宽鳍 · 接触点可检查</h1><p>重新定向与分布支撑 · 186 个主套实例 · A1 mini / PLA / 0.4 mm / 0.20 mm</p></div><div class="actions"><a id="download" download>本盘打印 3MF</a><a href="assembly/tutorials/assembly-o22/index.html">安装教程 ↗</a></div></header>
<main><aside class="side"><label>打印盘<select id="plate"></select></label><label>零件<select id="item"></select></label><label><input type="checkbox" id="isolate">只看所选零件</label><label>连接齿近景<select id="contact"></select></label><div id="plateinfo"></div><div class="info" id="info"></div><details open><summary>拆除方法</summary><div id="directions"></div></details><p class="muted">Fxx 为新版盘号。安装教程仍按原编号查询，见 <a href="新旧盘号与安装编号对照.csv">完整对照表</a>。Sxx 为额外试件。</p></aside>
<section class="viewer"><div class="legend"><label><input id="showpart" type="checkbox" checked><span class="dot blue"></span>保留：零件</label><label><input id="showfin" type="checkbox" checked><span class="dot orange"></span>移除：鳍板、底脚和加强肋</label><label><input id="showteeth" type="checkbox" checked><span class="dot yellow"></span>剪断：实际连接齿</label></div><label style="display:none"><input id="showretained" type="checkbox" checked><span class="dot" style="background:#a64fc7"></span>保留：新增内部加强筋</label><canvas id="model" tabindex="0" aria-label="实际三维网格"></canvas><div class="tools"><button id="iso">立体</button><button id="top">俯视</button><button id="front">正视</button><button id="reset">退出近景 / 重置</button><label><input type="checkbox" id="ghost">零件半透明</label><label>剖切 <input id="clip" type="range" min="0" max="180" step=".2" value="180"><span id="cliplabel">全部</span></label></div><p class="muted" id="status">正在加载实际几何…</p></section>
<section class="notes"><h2>打印与拆除</h2><p>本页蓝色是保留的原零件，橙色是支撑，黄色是与两侧实体均有实际交叠的连接齿。颜色仅用于识别；打印用同一种 PLA，无需 AMS。选择一个零件，再选择连接齿，可以检查局部实际网格。近景裁切仅改变显示。</p><ol><li>用 OrcaSlicer 打开本盘 3MF 为项目。保持 0.4 mm 喷嘴、0.20 mm 首层与层高，按层打印，自动支撑关闭。</li><li>保留文件中的朝向、位置和部件分组。鳍板已经是实体，切片器的支撑间隙参数不会改变它们。</li><li>冷却取件后，扶住厚实本体，先剪黄色连接齿，再剪底脚间连片，逐片朝原热盘方向退出。避免扯动配合孔、PCB 滑轨和薄弹片。</li><li>清除齿痕，按原安装编号分袋；使用实际五金试配，再按 26 步安装教程装配。</li></ol><div class="warning">数字几何、切片检查与实物验收分开记录。未进行实物打印或材料力学试验。当前验证详情见 <a href="验证说明.html">验证说明</a>；先使用 S 盘验证拆除与配合。</div><h2>新版与原版的差异</h2><p>逐件比较打印角度与实际出丝结果；保留功能轴线和弹片方向。最终 150 种零件本体均保留原形状，详情见验证说明。所有鳍板沿自身垂直路径落到热盘；较高的宽板有横向加强肋。鳍主体不与零件交叠，连接齿才进入本体。每个支撑实体都检查热盘连接及与零件之间的连接。</p><p>本次为独立设计的实体支撑，没有采用拓竹自动支撑生成结果。支撑布局与候选朝向通过脚本构造、几何检查和 Blender 可视化反复修正。它们不是受力仿真的结果。</p><h2>打印盘与装配对照</h2><div id="inventory"></div><p><a href="新旧盘号与安装编号对照.csv">下载编号对照表</a> · <a href="blender/final_chest.blend">最终胸架 Blender 文件</a> · <a href="blender/contact_closeup.blend">实际接触点 Blender 文件</a></p></section></main><script src="scene.js"></script><script src="viewer.js"></script></html>'''
 (O/'index.html').write_text(html,encoding='utf-8')
 if not (O/'assembly').exists():shutil.copytree(src/'assembly',O/'assembly')
 for p in (O/'assembly').rglob('*.html'):
  text=p.read_text(encoding='utf-8-sig').replace('O22-F1','O22-F3')
  if p.name=='index.html' and 'assembly-o22' in p.as_posix():
   text=re.sub(r'<p style="padding:14px;background:#fff4dc">.*?</p>','<p style="padding:14px;background:#fff4dc">本教程配套 O22-F3。原安装编号继续有效，打印盘已调整为 Fxx。请先查 <a href="../../../新旧盘号与安装编号对照.csv">新旧编号对照表</a>，移除橙色支撑与黄色连接齿后再安装。<a href="../../../index.html">支撑识别入口</a></p>',text,flags=re.S)
  if p.name=='external-files.html':text='<!doctype html><meta charset="utf-8"><title>O22-F3 打印入口</title><p><a href="../../../index.html">打开新版彩色支撑视图与打印文件</a></p><p>旧安装编号继续有效，但打印盘已重新排布。<a href="../../../新旧盘号与安装编号对照.csv">查看编号对照表</a></p><p>PCB 制造资料继续使用原 O22 工程包。</p>'
  p.write_text(text,encoding='utf-8')
 print('PUBLISHED',len(plates),len(meshes),flush=True)
if __name__=='__main__':run()