from pathlib import Path
D=Path('PoseDoll_HW44_Plan/design/Hardware/PoseDoll44/bench/revO22/X062_SupportTrial_R1');p=D/'viewer.js';s=p.read_text()
s=s.replace("gl.uniform4f(L.color,...color,alpha);gl.drawArrays", "if(o.group&&$('#group').value)color=o.group===$('#group').value?[1,.35,.08]:[.65,.72,.70];gl.uniform4f(L.color,...color,alpha);gl.drawArrays")
s=s.replace("gl.depthMask(true);window.AUDIT_VIEW=", """if($('#stage').value==='fins'&&meshData.groups&&meshData.groups[$('#group').value]){let q=meshData.groups[$('#group').value],d=q.removal_vector,t=+$('#move').value*.5,a=q.bounds_mm.slice(0,3).map((x,i)=>(x+q.bounds_mm[i+3])/2+d[i]*t),b=a.map((x,i)=>x+d[i]*16),u=Math.abs(d[2])>.98?[1,0,0]:[-d[1],d[0],0],ul=Math.hypot(...u);u=u.map(x=>x/ul);let pts=[a,b,b,b.map((x,i)=>x-d[i]*4+u[i]*2),b,b.map((x,i)=>x-d[i]*4-u[i]*2)],values=pts.flatMap(p=>[...p,0,0,1]),bf=window.arrowBuffer||(window.arrowBuffer=gl.createBuffer());gl.bindBuffer(gl.ARRAY_BUFFER,bf);gl.bufferData(gl.ARRAY_BUFFER,new Float32Array(values),gl.DYNAMIC_DRAW);bind(bf);gl.uniformMatrix4fv(L.M,false,column(view));gl.uniform4f(L.color,.85,.04,.10,1);gl.disable(gl.DEPTH_TEST);gl.drawArrays(gl.LINES,0,values.length/6);}gl.depthMask(true);window.AUDIT_VIEW=""")
p.write_text(s,encoding='utf8')
p=D/'index.html';s=p.read_text().replace('选择鳍后，查看连接齿全部清除时的移动方向。','所选鳍以亮橙色标出，红箭头表示连接齿全部清除后的移动方向。');p.write_text(s,encoding='utf8')
(D/'start_preview.py').write_text('''from pathlib import Path
import http.server,functools,threading,webbrowser
root=Path(__file__).resolve().parent
server=http.server.ThreadingHTTPServer(('127.0.0.1',0),functools.partial(http.server.SimpleHTTPRequestHandler,directory=str(root.parent)))
url=f'http://127.0.0.1:{server.server_address[1]}/{root.name}/index.html'
print(url);threading.Timer(.3,lambda:webbrowser.open(url)).start()
try:server.serve_forever()
except KeyboardInterrupt:server.server_close()
''',encoding='utf8')
print('VIEWER_POLISHED')
