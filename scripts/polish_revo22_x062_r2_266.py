from pathlib import Path
D=Path('PoseDoll_HW44_Plan/design/Hardware/PoseDoll44/bench/revO22/X062_SupportTrial_R2');p=D/'viewer.js';s=p.read_text('utf-8')
needle='function shader(type,source)'
wire='''async function wireGeometry(key,x){if(cache[key])return cache[key];let [v,f]=await Promise.all([unpack(x.v,Float32Array),unpack(x.f,Uint32Array)]),edges=new Map(),out=[];
for(let i=0;i<f.length;i+=3){let ids=[f[i],f[i+1],f[i+2]],a=ids[0]*3,b=ids[1]*3,c=ids[2]*3,u=[v[b]-v[a],v[b+1]-v[a+1],v[b+2]-v[a+2]],w=[v[c]-v[a],v[c+1]-v[a+1],v[c+2]-v[a+2]],n=[u[1]*w[2]-u[2]*w[1],u[2]*w[0]-u[0]*w[2],u[0]*w[1]-u[1]*w[0]],len=Math.hypot(...n)||1;n=n.map(t=>t/len);for(let j=0;j<3;j++){let a=ids[j],b=ids[(j+1)%3],k=Math.min(a,b)+':'+Math.max(a,b);if(!edges.has(k))edges.set(k,{a,b,n,show:false});else{let e=edges.get(k);e.show=e.n.reduce((t,v,k)=>t+v*n[k],0)<.97;}}}
for(let e of edges.values())if(e.show)for(let i of [e.a,e.b])out.push(v[3*i],v[3*i+1],v[3*i+2],0,0,1);let buffer=gl.createBuffer();gl.bindBuffer(gl.ARRAY_BUFFER,buffer);gl.bufferData(gl.ARRAY_BUFFER,new Float32Array(out),gl.STATIC_DRAW);return cache[key]={buffer,count:out.length/6};}
'''
s=s.replace(needle,wire+needle)
s=s.replace("Number(a.role==='part')-Number(b.role==='part')","(a.role==='guard'?2:Number(a.role==='part'))-(b.role==='guard'?2:Number(b.role==='part'))")
s=s.replace("o.role==='guard'?.20:","o.role==='guard'?1:")
s=s.replace("o.role==='guard'?[.35,.83,.48]","o.role==='guard'?[.05,.65,.25]")
s=s.replace("gl.drawArrays(gl.TRIANGLES,0,o.mesh.count)","if(o.role==='guard'){gl.disable(gl.DEPTH_TEST);gl.drawArrays(gl.LINES,0,o.mesh.count);gl.enable(gl.DEPTH_TEST)}else gl.drawArrays(gl.TRIANGLES,0,o.mesh.count)")
s=s.replace("mesh:await geometry(version+role,x)","mesh:role==='guard'?await wireGeometry(version+role,x):await geometry(version+role,x)")
s=s.replace("state.focus=[b.slice(0,3).map(x=>x-4),b.slice(3).map(x=>x+4)];","state.focus=[[-4,-12,0],[36,38,42]];")
s=s.replace("$('#guard').checked=true;$('#ghost').checked=true;","$('#guard').checked=true;$('#ghost').checked=false;")
s=s.replace("state.focus=[[-4,-12,0],[36,38,42]];state.zoom=1;state.yaw=-.8;","state.focus=[[-4,-12,0],[36,38,42]];state.zoom=1;state.yaw=index===0?-.8:2.34;")
p.write_text(s,'utf-8')
