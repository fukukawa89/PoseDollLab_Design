'use strict';
(() => {
const $=s=>document.querySelector(s),$$=s=>[...document.querySelectorAll(s)],data=window.TUT_MODELS;
const state={tab:'design',version:'extended',alpha:0,beta:0,step:0,progress:0,playing:false,yaw:.61,pitch:1.05,zoom:1};
const reduced=matchMedia('(prefers-reduced-motion: reduce)'),canvas=$('#model');
const gl=canvas.getContext('webgl',{antialias:true,preserveDrawingBuffer:true});
const I=()=>[1,0,0,0,0,1,0,0,0,0,1,0,0,0,0,1];
const mul=(a,b)=>Array.from({length:16},(_,k)=>{const r=Math.floor(k/4),c=k%4;return [0,1,2,3].reduce((s,i)=>s+a[r*4+i]*b[i*4+c],0);});
function rotation(axis,a){const m=I(),c=Math.cos(a),s=Math.sin(a);if(axis==='x'){m[5]=c;m[6]=-s;m[9]=s;m[10]=c;}else if(axis==='z'){m[0]=c;m[1]=-s;m[4]=s;m[5]=c;}else{m[0]=c;m[2]=s;m[8]=-s;m[10]=c;}return m;}
function translate(x,y,z){const m=I();m[3]=x;m[7]=y;m[11]=z;return m;}
const colMajor=m=>new Float32Array(Array.from({length:16},(_,i)=>m[(i%4)*4+Math.floor(i/4)]));
const colors={C01:[.82,.52,.30],C02:[.29,.57,.47],C14:[.43,.56,.73],C15:[.53,.65,.80],metal:[.67,.69,.68],gauge:[.80,.73,.57]};
let program,loc,cache={};
if(gl){
 const shader=(type,src)=>{const s=gl.createShader(type);gl.shaderSource(s,src);gl.compileShader(s);if(!gl.getShaderParameter(s,gl.COMPILE_STATUS))throw Error(gl.getShaderInfoLog(s));return s;};
 program=gl.createProgram();gl.attachShader(program,shader(gl.VERTEX_SHADER,'attribute vec3 p;attribute vec3 n;uniform mat4 M;uniform vec2 scale;varying vec3 normal;void main(){vec4 v=M*vec4(p,1.);normal=normalize((M*vec4(n,0.)).xyz);gl_Position=vec4(v.x*scale.x,v.y*scale.y,-v.z/200.,1.);}'));
 gl.attachShader(program,shader(gl.FRAGMENT_SHADER,'precision mediump float;varying vec3 normal;uniform vec3 color;void main(){vec3 n=normalize(normal);float l=.40+.60*max(0.,dot(n,normalize(vec3(-.3,.6,1.))));gl_FragColor=vec4(color*l,1.);}'));gl.linkProgram(program);if(!gl.getProgramParameter(program,gl.LINK_STATUS))throw Error(gl.getProgramInfoLog(program));
 gl.useProgram(program);loc={p:gl.getAttribLocation(program,'p'),n:gl.getAttribLocation(program,'n'),M:gl.getUniformLocation(program,'M'),scale:gl.getUniformLocation(program,'scale'),color:gl.getUniformLocation(program,'color')};gl.enable(gl.DEPTH_TEST);
}else $('#webgl-error').hidden=false;
function mesh(key){if(cache[key])return cache[key];const o=data[key],a=[];for(const f of o.f){const [p,q,r]=f.map(i=>o.v[i]),u=q.map((v,i)=>v-p[i]),v=r.map((x,i)=>x-p[i]);let n=[u[1]*v[2]-u[2]*v[1],u[2]*v[0]-u[0]*v[2],u[0]*v[1]-u[1]*v[0]],l=Math.hypot(...n)||1;n=n.map(x=>x/l);for(const point of [p,q,r])a.push(...point,...n);}const b=gl.createBuffer();gl.bindBuffer(gl.ARRAY_BUFFER,b);gl.bufferData(gl.ARRAY_BUFFER,new Float32Array(a),gl.STATIC_DRAW);return cache[key]={b,count:a.length/6};}
function placed(){
 if(state.tab==='fit'){const key=$('#part').value,o=data[key];let low=[Infinity,Infinity,Infinity],high=[-Infinity,-Infinity,-Infinity];for(const v of o.v)for(let i=0;i<3;i++){low[i]=Math.min(low[i],v[i]);high[i]=Math.max(high[i],v[i]);}const center=low.map((v,i)=>(v+high[i])/2),radius=Math.hypot(...high.map((v,i)=>(v-low[i])/2));return {items:[{key,M:translate(...center.map(v=>-v)),color:key.startsWith('fastener')?colors.metal:colors.gauge}],radius:radius*1.1};}
 const prefix=state.tab==='assembly'?'extended':state.version,items=[],t=state.progress/100,a=state.tab==='assembly'?0:state.alpha*Math.PI/180,b=state.tab==='assembly'?0:state.beta*Math.PI/180;
 for(const n of ['C01','C02','C14','C15']){
  if(state.tab==='assembly'&&((state.step===0&&['C14','C15'].includes(n))||(state.step<3&&n==='C15')))continue;
  let M=n==='C01'?I():n==='C02'?mul(rotation('x',a),rotation('y',b)):rotation('x',a);
  if(state.tab==='assembly'){
   if(state.step===0&&n==='C02')M=translate(0,0,30*(1-t));
   if(state.step===1&&n==='C14')M=translate(0,-30*(1-t),-7);
   if(state.step===2&&n==='C14')M=translate(0,0,-7*(1-t));
   if(state.step===3&&n==='C15')M=translate(30*(1-t),0,7);
   if(state.step===4&&n==='C15')M=translate(0,0,7*(1-t));
  }
  items.push({key:prefix+'_'+n,M,color:colors[n]});
 }
 if(state.tab!=='assembly'||state.step===5)for(const n of Object.keys(data).filter(k=>k.startsWith('fastener_')))items.push({key:n,M:rotation('x',a),color:colors.metal});
 return {items,radius:state.tab==='assembly'?49:32};
}
function draw(){if(!gl||state.tab==='record')return;const w=canvas.clientWidth,h=canvas.clientHeight,dpr=Math.min(devicePixelRatio||1,2);canvas.width=Math.round(w*dpr);canvas.height=Math.round(h*dpr);gl.viewport(0,0,canvas.width,canvas.height);gl.clearColor(.906,.914,.875,1);gl.clear(gl.COLOR_BUFFER_BIT|gl.DEPTH_BUFFER_BIT);const {items,radius}=placed(),scale=Math.min(w,h)*.45/radius*state.zoom,view=mul(rotation('x',state.pitch),rotation('z',state.yaw));gl.uniform2f(loc.scale,2*scale/w,2*scale/h);
 for(const p of items){const o=mesh(p.key);gl.bindBuffer(gl.ARRAY_BUFFER,o.b);gl.enableVertexAttribArray(loc.p);gl.vertexAttribPointer(loc.p,3,gl.FLOAT,false,24,0);gl.enableVertexAttribArray(loc.n);gl.vertexAttribPointer(loc.n,3,gl.FLOAT,false,24,12);gl.uniformMatrix4fv(loc.M,false,colMajor(mul(view,p.M)));gl.uniform3fv(loc.color,p.color);gl.drawArrays(gl.TRIANGLES,0,o.count);}
}
const stepInfo=[['两只叉架先交错放好','固定橙色输入叉架，让绿色输出叉架沿轴向靠近。两组小转轴互相垂直；先不要放上下半环。'],['下半环从侧面送入','下半环先放在轴心下方 7 mm，从叉架开口的一侧移到中央，避开输入叉架的根部。'],['抬起下半环，托住转轴','把下半环抬到轴心，半圆槽托住两组转轴。这时没有螺钉保持，需要稳妥扶持。'],['上半环从另一侧送入','上半环先放在轴心上方 7 mm，从另一个开口方向移到中央。不要从叉架端部硬套进去。'],['落下上半环，合拢','下移上半环，让两片对应的端面合拢。遇到明显阻力就停，先核对方向与实际尺寸。'],['四角螺钉就位后，再逐颗检查','四颗 M1.6 × 6 螺钉配四颗 M1.6 螺母，相邻角的头部朝向相反。这里只展示就位模型，不规定拧紧扭矩。转动关节分别接近各螺钉，不要用继续拧紧来消除无法解释的卡滞。']];
$('#steps').innerHTML=stepInfo.map((s,i)=>'<li><button data-step="'+i+'" title="'+s[0]+'">'+(i+1)+'</button></li>').join('');
function step(i){state.step=i;state.progress=0;pause();$('#step-title').textContent=stepInfo[i][0];$('#step-text').textContent=stepInfo[i][1];$$('[data-step]').forEach((b,j)=>b.setAttribute('aria-pressed',String(i===j)));progress(0);}
function progress(v){state.progress=v;$('#progress').value=v;$('#percent').textContent=Math.round(v)+'%';draw();}
function pause(){state.playing=false;$('#play').textContent='▶ 播放本步';$('#play').setAttribute('aria-pressed','false');}
$$('[data-step]').forEach(b=>b.onclick=()=>step(Number(b.dataset.step)));
$('#progress').oninput=e=>{pause();progress(Number(e.target.value));};
$('#play').onclick=()=>{if(state.playing){pause();return;}if(state.progress>=100)progress(0);state.playing=true;$('#play').textContent='Ⅱ 暂停';$('#play').setAttribute('aria-pressed','true');let last=performance.now();function tick(now){if(!state.playing)return;const dt=Math.min(100,now-last);last=now;progress(Math.min(100,state.progress+dt/38));if(state.progress===100)pause();else requestAnimationFrame(tick);}requestAnimationFrame(tick);};
function poseResult(manual=false){const box=$('#pose-result');box.className='callout';$('#alpha-value').textContent=state.alpha+'°';$('#beta-value').textContent=state.beta+'°';if(manual){box.classList.add('warn');box.textContent='任意角度预览：此处不自动判定碰撞或通过。请以数字报告中的姿态与范围为准。';return;}
 if($('#preset').value==='mixed'){box.classList.add('bad');box.textContent='原始与加长版本：这个双向大角度组合均已发现叉架碰撞。加长并不意味着所有方向都能随意转到极限。';}
 else if($('#preset').value==='single'){if(state.version==='original'){box.classList.add('bad');box.textContent='原始版本：这个 100° 姿态已发现两只叉架穿透。';}else box.textContent='加长 2 mm：已检查的这个姿态没有核心穿透；两叉架非配合面名义间隙经保守计算不小于 0.6 mm。仍不等于实际公差与承载通过。';}
 else box.textContent='中立姿态：四件核心和标准紧固件的名义位置已检查。半环端面、螺钉头和螺母座存在设计接触；尚无实物保持力结论。';
}
$$('[data-version]').forEach(b=>b.onclick=()=>{state.version=b.dataset.version;$$('[data-version]').forEach(x=>x.setAttribute('aria-pressed',String(x===b)));poseResult(!['neutral','single','mixed'].includes($('#preset').value));draw();});
$('#preset').onchange=()=>{const p=$('#preset').value;state.alpha=p==='mixed'?75:0;state.beta=p==='mixed'?75:p==='single'?100:0;$('#alpha').value=state.alpha;$('#beta').value=state.beta;poseResult();draw();};
for(const id of ['alpha','beta'])$('#'+id).oninput=e=>{state[id]=Number(e.target.value);$('#preset').selectedIndex=-1;poseResult(true);draw();};
const partText={gauge_hole_gauge_Z:'从缺口端数，五个孔依次为 Ø4.0 / 4.2 / 4.4 / 4.6 / 4.8 mm，孔长 6 mm。用于比较实际孔与 Ø4 打印轴的配合。',gauge_hole_gauge_Y:'孔径与上一件相同，但文件中的孔轴沿 Y 方向。供应商需要保留打印方向差异并记录，否则不能拿来比较方向效应。',gauge_pin_D4:'名义 Ø4 mm、直段长 12 mm，底部是便于拿取的圆柄。打印 3 件分别试配，观察样件之间的差异。不要用力敲入。',gauge_fastener_gauge:'从缺口端数，通孔依次 Ø1.8 / 2.0 / 2.2 / 2.4 mm，螺母槽对边依次 3.3 / 3.5 / 3.7 / 3.9 mm。更大的槽也可能导致螺母空转，不能只看是否放得进。',fastener_screw_1:'M1.6 × 6 内六角圆柱头螺钉：螺距 0.35 mm，头部约 Ø3 × 1.6 mm，用 1.5 mm 内六角工具。图中螺纹为包络。标准金属件，首批配合试验准备 6 件。',fastener_nut_1:'M1.6 六角螺母：对边 3.2 mm，厚约 1.3 mm，与同螺距螺钉配对。首批准备 6 件；核对实物规格，不能替换为 M2。'};
function part(){const key=$('#part').value;$('#part-text').textContent=partText[key];state.zoom=1;draw();}$('#part').onchange=part;
function tab(id){if(!['design','assembly','fit','record'].includes(id))id='design';state.tab=id;pause();$$('[data-tab]').forEach(a=>{if(a.dataset.tab===id)a.setAttribute('aria-current','page');else a.removeAttribute('aria-current');});for(const n of ['design','assembly','fit','record'])$('#'+n).hidden=n!==id;$('#workspace').hidden=id==='record';$('#legend').hidden=id==='fit';$('#caption').textContent=id==='fit'?'量规来自本轮实际 CAD；金属标准件按名义尺寸建模，螺纹显示为包络。屏幕不是实物比例尺。':'颜色用于辨认零件。外壳、完整电路和线束尚未加入；屏幕不是实物比例尺。';$('#scene-label').textContent=id==='fit'?'按本轮量规 STEP / 标准尺寸建模':id==='assembly'?'加长改型 · 分段装配演示':'四件核心 · 实际 STL 几何';state.zoom=1;if(id==='fit')part();draw();}
addEventListener('hashchange',()=>tab(location.hash.slice(1)));$('#reset').onclick=()=>{state.yaw=.61;state.pitch=1.05;state.zoom=1;draw();};$('#front').onclick=()=>{state.yaw=0;state.pitch=Math.PI/2;draw();};
let drag=null;canvas.onpointerdown=e=>{drag=[e.clientX,e.clientY];canvas.setPointerCapture(e.pointerId);};canvas.onpointermove=e=>{if(!drag)return;state.yaw+=(e.clientX-drag[0])*.009;state.pitch+=(e.clientY-drag[1])*.009;drag=[e.clientX,e.clientY];draw();};canvas.onpointerup=canvas.onpointercancel=()=>drag=null;canvas.onwheel=e=>{e.preventDefault();state.zoom=Math.min(2.5,Math.max(.5,state.zoom*Math.exp(-e.deltaY*.001)));draw();};canvas.onkeydown=e=>{if(!['ArrowLeft','ArrowRight','ArrowUp','ArrowDown'].includes(e.key))return;e.preventDefault();if(e.key==='ArrowLeft')state.yaw-=.12;if(e.key==='ArrowRight')state.yaw+=.12;if(e.key==='ArrowUp')state.pitch+=.12;if(e.key==='ArrowDown')state.pitch-=.12;draw();};
$('#copy').onclick=async()=>{try{await navigator.clipboard.writeText($('#brief').value);$('#copy-status').textContent='已复制，由你选择是否发送给对方。';}catch{$('#brief').focus();$('#brief').select();$('#copy-status').textContent='已选中文字，请按 Ctrl+C 复制。';}};
addEventListener('resize',draw);document.addEventListener('visibilitychange',()=>{if(document.hidden)pause();});reduced.addEventListener('change',pause);
step(0);poseResult();tab(location.hash.slice(1));window.TUT_GUIDE_READY=true;window.TUT_GUIDE_STATE=state;
})();
