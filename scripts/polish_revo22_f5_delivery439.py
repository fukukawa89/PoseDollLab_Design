import json,re
from publish_revo22_f5_compact302 import D,write
m=json.loads((D/'manifest.json').read_text());html=(D/'合盘布局.html').read_text();a=html.index('const PLATES=')+len('const PLATES=');b=html.index(';const $',a);data=json.loads(html[a:b]);byid={p['id']:p for p in m['plates']}
for p in data:
 byaddr={i['object_name'].split()[0]:i for i in byid[p['id']]['items']}
 for i in p['items']:i['optional_sample']=byaddr[i['address']].get('optional_sample',False)
html=html[:a]+json.dumps(data,ensure_ascii=False,separators=(',',':'))+html[b:]
html=html.replace('本包主套使用 D 编号，小样使用 Q 编号。','本包使用 D 编号；带“可选小样”标记的对象为额外样件。')
html=html.replace("esc(it.part)","(esc(it.part)+(it.optional_sample?' · 可选小样':''))")
a=html.index("$('#summary').innerHTML=");b=html.index(";$('#plates').innerHTML",a);html=html[:a]+"$('#summary').innerHTML='<span class=\"metric\">打印文件 15 → '+PLATES.length+' 个</span><span class=\"metric\">7 个可选小样已合盘</span>'"+html[b:];write(D/'合盘布局.html',html)
html=(D/'index.html').read_text();html=html.replace('<canvas id="model"','<div style="position:relative"><svg id="view-axes" width="90" height="90" viewBox="0 0 90 90" aria-label="本零件视图坐标轴" style="position:absolute;right:10px;top:10px;pointer-events:none"></svg><canvas id="model"').replace('aria-label="实际打印零件与支撑三维网格"></canvas>','aria-label="实际打印零件与支撑三维网格"></canvas></div>');html=html.replace('拖动旋转，滚轮缩放。','拖动旋转，滚轮缩放。灰色网格表示热盘平面，网格间隔 10 mm。');html=html.replace('</style>','#removal-info,#stem-info{max-height:6.5em;overflow:auto;margin:8px 0;line-height:1.7}</style>');write(D/'index.html',html)
js=(D/'viewer.js').read_text().replace('[1,0,0,0,0,1,0,0,0,0,1,0,0,0,0,0,1]','[1,0,0,0,0,1,0,0,0,0,1,0,0,0,0,1]');js=js.replace("i.object_name.split(' ')[0]+' '+i.id+'</button>'","i.object_name.split(' ')[0]+' '+i.id+(i.optional_sample?' [小样]':'')+'</button>'")
grid_code="""if(!window.f5BedGrid||window.f5BedGrid.id!==state.id){let bb=meshData.bounds,verts=[],loX=Math.floor((bb[0]-2)/10)*10,hiX=Math.ceil((bb[3]+2)/10)*10,loY=Math.floor((bb[1]-2)/10)*10,hiY=Math.ceil((bb[4]+2)/10)*10;for(let x=loX;x<=hiX;x+=10)verts.push(x,loY,-.02,0,0,1,x,hiY,-.02,0,0,1);for(let y=loY;y<=hiY;y+=10)verts.push(loX,y,-.02,0,0,1,hiX,y,-.02,0,0,1);let buffer=window.f5BedGrid?window.f5BedGrid.buffer:gl.createBuffer();gl.bindBuffer(gl.ARRAY_BUFFER,buffer);gl.bufferData(gl.ARRAY_BUFFER,new Float32Array(verts),gl.STATIC_DRAW);window.f5BedGrid={id:state.id,buffer,count:verts.length/6}}bind(window.f5BedGrid.buffer);gl.uniform4f(L.color,.66,.74,.71,.65);gl.enable(gl.BLEND);gl.blendFunc(gl.SRC_ALPHA,gl.ONE_MINUS_SRC_ALPHA);gl.depthMask(false);gl.drawArrays(gl.LINES,0,window.f5BedGrid.count);gl.depthMask(true);
"""
marker='for(let o of objects.slice().sort';assert marker in js;js=js.replace(marker,grid_code+marker)
needle='gl.depthMask(true);window.AUDIT_VIEW='
extra="""let axisHtml='';['X','Y','Z'].forEach((name,j)=>{let x=45+28*view[j],y=47-28*view[4+j],color=['#b84b44','#28734d','#2866aa'][j];axisHtml+='<line x1="45" y1="47" x2="'+x+'" y2="'+y+'" stroke="'+color+'" stroke-width="2"/><text x="'+(45+39*view[j])+'" y="'+(51-39*view[4+j])+'" fill="'+color+'" text-anchor="middle" font-size="12">'+name+'</text>'});$('#view-axes').innerHTML=axisHtml;
"""
assert needle in js;js=js.replace(needle,extra+needle)
needle="if(mesh)objects.push({role:'fin',mesh:await geometry(key+'_fin_'+pick,mesh)});draw()"
replace="if(mesh)objects.push({role:'fin',mesh:await geometry(key+'_fin_'+pick,mesh)});$('#removal-info').textContent=pick==='all'?'剪清黄色连接齿后，拆出顺序：'+data.removal_stages.map(s=>s.groups.join('、')+(s.simultaneous?' 同步取下':'')).join(' → '):pick+'：先剪清挡住拆出方向的黄色齿，退出方向（本零件视图坐标） '+mesh.removal_vector.map(v=>v.toFixed(2)).join(', ')+'。坐标轴随模型同步旋转。';draw()"
assert needle in js;js=js.replace(needle,replace)
needle="if(pick!=='all'){$('#stem-info').textContent=pick+'：整根退出方向（本零件视图坐标） '+mesh.removal_vector.map(v=>v.toFixed(2)).join(', ')+'。先断开根部，保持孔内段完整。'}draw()"
replace="if(pick!=='all'){$('#stem-info').textContent=pick+'：整根退出方向（本零件视图坐标） '+mesh.removal_vector.map(v=>v.toFixed(2)).join(', ')+'。先断开根部，保持孔内段完整。'}else{$('#stem-info').textContent=data.extractable_stems.length?'孔腔细齿应保持完整，先断根再按顺序抽出：'+data.stem_removal_record_order.map(k=>typeof k==='number'?'T'+String(k+1).padStart(3,'0'):'同步 '+k.simultaneous_records.map(x=>'T'+String(x+1).padStart(3,'0')).join('、')).join(' → '):'本件连接齿避开功能孔保护区。'}draw()"
assert needle in js;js=js.replace(needle,replace);write(D/'viewer.js',js)
print('DELIVERY439_UI_READY',flush=True)
