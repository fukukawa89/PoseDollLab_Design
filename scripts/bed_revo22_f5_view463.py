from pathlib import Path
p=Path(__file__).parent/'polish_revo22_f5_delivery439.py';s=p.read_text(encoding='utf-8-sig');s=s.replace("html=html.replace('</style>'", "html=html.replace('拖动旋转，滚轮缩放。','拖动旋转，滚轮缩放。灰色网格表示热盘平面，网格间隔 10 mm。');html=html.replace('</style>'")
a=s.index("needle='gl.depthMask(true);window.AUDIT_VIEW='")
extra='''grid_code="""if(!window.f5BedGrid||window.f5BedGrid.id!==state.id){let bb=meshData.bounds,verts=[],loX=Math.floor((bb[0]-2)/10)*10,hiX=Math.ceil((bb[3]+2)/10)*10,loY=Math.floor((bb[1]-2)/10)*10,hiY=Math.ceil((bb[4]+2)/10)*10;for(let x=loX;x<=hiX;x+=10)verts.push(x,loY,-.02,0,0,1,x,hiY,-.02,0,0,1);for(let y=loY;y<=hiY;y+=10)verts.push(loX,y,-.02,0,0,1,hiX,y,-.02,0,0,1);let buffer=window.f5BedGrid?window.f5BedGrid.buffer:gl.createBuffer();gl.bindBuffer(gl.ARRAY_BUFFER,buffer);gl.bufferData(gl.ARRAY_BUFFER,new Float32Array(verts),gl.STATIC_DRAW);window.f5BedGrid={id:state.id,buffer,count:verts.length/6}}bind(window.f5BedGrid.buffer);gl.uniform4f(L.color,.66,.74,.71,.65);gl.enable(gl.BLEND);gl.blendFunc(gl.SRC_ALPHA,gl.ONE_MINUS_SRC_ALPHA);gl.depthMask(false);gl.drawArrays(gl.LINES,0,window.f5BedGrid.count);gl.depthMask(true);
"""
marker='for(let o of objects.slice().sort';assert marker in js;js=js.replace(marker,grid_code+marker)
'''
s=s[:a]+extra+s[a:];p.write_text(s,encoding='utf-8')
