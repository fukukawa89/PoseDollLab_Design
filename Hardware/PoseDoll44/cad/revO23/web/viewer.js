'use strict';
const $=s=>document.querySelector(s),D=window.O23;
const state={yaw:-.7,pitch:.13,zoom:1,pose:'A',part:'all'};
const names={pelvis:'骨盆',waist:'腰腹',chest:'胸廓',head:'头部',upperarm_l:'左上臂',upperarm_r:'右上臂',elbow_l:'左肘下段',elbow_r:'右肘下段',forearm_l:'左前臂',forearm_r:'右前臂',hand_l:'左握拳',hand_r:'右握拳',thigh_l:'左大腿',thigh_r:'右大腿',calf_l:'左小腿',calf_r:'右小腿',foot_l:'左后脚',foot_r:'右后脚',ball_l:'左前脚掌',ball_r:'右前脚掌'};
const c=$('#canvas'),gl=c.getContext('webgl',{antialias:true,preserveDrawingBuffer:true});
Object.assign(names,{clavicle_l:'左锁骨外段',clavicle_r:'右锁骨外段','clavicle_l.protract_frame':'左锁骨内段', 'clavicle_r.protract_frame':'右锁骨内段',controller_housing:'紧凑背盒',backpack_support:'可拆背盒支撑架',controller_lid:'背盒检修盖'});
const label=key=>names[key.split('/').pop()]||key;
let L,ready=false,geometryBuffer,guideBuffer;
function bindVertices(buffer){gl.bindBuffer(gl.ARRAY_BUFFER,buffer);for(const [name,offset] of [['p',0],['n',12]]){gl.enableVertexAttribArray(L[name]);gl.vertexAttribPointer(L[name],3,gl.FLOAT,false,24,offset)}}
function drawHarness(){
if(!$('#harness').checked||!D.harness)return;
const world=(token,q)=>{const m=D.poses[state.pose][token];return [0,1,2].map(i=>m[i*4]*q[0]+m[i*4+1]*q[1]+m[i*4+2]*q[2]+m[i*4+3])};
const emit=(points,color)=>{if(!points.length)return;bindVertices(guideBuffer);gl.bufferData(gl.ARRAY_BUFFER,new Float32Array(points.flatMap(p=>[...p,1,1,1])),gl.DYNAMIC_DRAW);gl.uniformMatrix4fv(L.model,false,column([1,0,0,0,0,1,0,0,0,0,1,0,0,0,0,1]));gl.uniform3fv(L.color,color);gl.drawArrays(gl.LINES,0,points.length)};
let seats=[];
for(const r of D.harness.seats){if(state.part!=='all'&&state.part!==r.part)continue;const m=r.transform_body_mm;for(const axis of [0,1,2]){const a=r.wire_center_body_mm.map((v,i)=>v-m[i][axis]*3.5),b=r.wire_center_body_mm.map((v,i)=>v+m[i][axis]*3.5);seats.push(world(r.token,a),world(r.token,b))}}
gl.disable(gl.DEPTH_TEST);emit(seats,[0,.65,.75]);let channels=[];
for(const r of D.harness.channels){if(state.part!=='all'&&state.part!==r.part)continue;const seat=D.harness.seats.find(s=>s.id===r.a),points=r.centerline_body_mm;for(let i=1;i<points.length;i++)channels.push(world(seat.token,points[i-1]),world(seat.token,points[i]))}
emit(channels,[1,.4,.05]);gl.enable(gl.DEPTH_TEST);bindVertices(geometryBuffer);
}
function shader(type,source){let s=gl.createShader(type);gl.shaderSource(s,source);gl.compileShader(s);if(!gl.getShaderParameter(s,gl.COMPILE_STATUS))throw Error(gl.getShaderInfoLog(s));return s}
const column=m=>new Float32Array(Array.from({length:16},(_,k)=>m[k%4*4+Math.floor(k/4)]));
const worldCenter=o=>{const m=D.poses[state.pose][o.token],q=o.local_center;return [0,1,2].map(i=>m[i*4]*q[0]+m[i*4+1]*q[1]+m[i*4+2]*q[2]+m[i*4+3])};
function centerSection(){if(!ready)return;let lo=Infinity,hi=-Infinity;for(const o of D.items){if(state.part!=='all'&&o.key!==state.part)continue;const x=worldCenter(o)[0],radius=o.view_span/2;lo=Math.min(lo,x-radius);hi=Math.max(hi,x+radius)}const cut=$('#cut');cut.min=Math.floor(lo-1);cut.max=Math.ceil(hi+1);cut.step=.1;cut.value=(lo+hi)/2}
function draw(){if(!ready)return;let w=c.clientWidth,h=c.clientHeight,dpr=Math.min(devicePixelRatio,2);c.width=w*dpr;c.height=h*dpr;gl.viewport(0,0,c.width,c.height);gl.clearColor(.91,.925,.89,1);gl.clear(gl.COLOR_BUFFER_BIT|gl.DEPTH_BUFFER_BIT);gl.enable(gl.DEPTH_TEST);
let sy=Math.sin(state.yaw),cy=Math.cos(state.yaw),sp=Math.sin(state.pitch),cp=Math.cos(state.pitch),V=[-sy,cy,0,0,-sp*cy,-sp*sy,cp,0,cp*cy,cp*sy,sp,0,0,0,0,1];
let center=[-10,0,340],height=760;
if(state.part!=='all'){let item=D.items.find(o=>o.key===state.part);let M=D.poses[state.pose][item.token],q=item.local_center;center=[0,1,2].map(i=>M[i*4]*q[0]+M[i*4+1]*q[1]+M[i*4+2]*q[2]+M[i*4+3]);height=Math.max(80,item.view_span)}
for(let i=0;i<3;i++)V[i*4+3]=-V[i*4]*center[0]-V[i*4+1]*center[1]-V[i*4+2]*center[2];
let scale=2*state.zoom/height;gl.uniformMatrix4fv(L.view,false,column(V));gl.uniform2f(L.scale,scale*h/w,scale);gl.uniform1f(L.cut,$('#section').checked?+$('#cut').value:10000);
let contacts=D.review.pose_contacts[state.pose],affected=new Set(contacts.affected_keys),advisory=new Set(contacts.advisory_keys);
for(let o of D.items){if(!$('#mechanisms').checked&&o.role!=='structure')continue;if(state.part!=='all'&&o.key!==state.part)continue;gl.uniformMatrix4fv(L.model,false,column(D.poses[state.pose][o.token]));let color=$('#contacts').checked&&affected.has(o.key)?[.80,.22,.12]:$('#advisories').checked&&advisory.has(o.key)?[.90,.64,.15]:o.color;gl.uniform3fv(L.color,color);gl.drawArrays(gl.TRIANGLES,o.first,o.count)}
drawHarness();
$('#selected').textContent=state.part==='all'?'完整人偶':label(state.part);$('#message').textContent=contacts.count===null?'此几何的动作检查进行中':`相邻干涉 ${contacts.count} 条 · 非相邻接触提示 ${contacts.advisory_count} 条${$('#section').checked?' · 剖切':''}`;
const exported=D.review.exports_by_key[state.part];$('#part-download').hidden=!exported;if(exported)$('#part-download').href='../'+exported;
window.O23_VIEW_STATE={...state,ready:true,objects:D.items.length};}
async function main(){if(!gl)throw Error('此浏览器无法启用 WebGL。');const program=gl.createProgram();gl.attachShader(program,shader(gl.VERTEX_SHADER,'attribute vec3 p;attribute vec3 n;uniform mat4 model;uniform mat4 view;uniform vec2 scale;varying vec3 N;varying vec3 world;void main(){vec4 q=model*vec4(p,1.);world=q.xyz;vec4 v=view*q;N=mat3(view)*mat3(model)*n;gl_Position=vec4(v.xy*scale,-v.z/2000.,1.);}'));gl.attachShader(program,shader(gl.FRAGMENT_SHADER,'precision mediump float;varying vec3 N;varying vec3 world;uniform vec3 color;uniform float cut;void main(){if(world.x>cut)discard;vec3 n=normalize(N);float a=.48+.52*max(0.,dot(n,normalize(vec3(-.4,.7,1.))));gl_FragColor=vec4(color*a,1.);}'));gl.linkProgram(program);if(!gl.getProgramParameter(program,gl.LINK_STATUS))throw Error(gl.getProgramInfoLog(program));gl.useProgram(program);L={};for(let n of ['model','view','scale','color','cut'])L[n]=gl.getUniformLocation(program,n);
const encoded=Uint8Array.from(atob(D.geometry),x=>x.charCodeAt(0)),data=new Float32Array(await new Response(new Blob([encoded]).stream().pipeThrough(new DecompressionStream('gzip'))).arrayBuffer());geometryBuffer=gl.createBuffer();guideBuffer=gl.createBuffer();for(const name of ['p','n'])L[name]=gl.getAttribLocation(program,name);bindVertices(geometryBuffer);gl.bufferData(gl.ARRAY_BUFFER,data,gl.STATIC_DRAW);
for(let o of D.items.filter(o=>o.role==='structure'||['o22/controller_housing','o22/backpack_support','o22/controller_lid'].includes(o.key))){let opt=document.createElement('option');opt.value=o.key;opt.textContent=label(o.key);$('#part').append(opt)}
$('#metrics').innerHTML=`装配高 ${(D.review.height_mm/10).toFixed(1)} cm · ${D.review.structures} 个主要结构件<br>46 路原始轴 · 四肢按 UE 比例<br>上半身整体抬高 ${D.review.upper_torso_raise_mm} mm<br>实际双髋中心距 ${D.review.actual_hip_spacing_mm.toFixed(2)} mm · 对齐 UE<br>已检查 ${D.review.daily_poses??'—'} 个日常姿态<br>相邻部位干涉记录：${D.review.daily_contacts??'检查中'}<br>非相邻接触列为提示${D.review.stl_topology_failed_count?'<br>部分 STL 导出未通过':D.review.stl_slicing_verified?'<br>STL '+D.review.stl_count+'/'+D.review.stl_count+' 封闭 · 切片通过':''}`;
$('#metrics').innerHTML+=`<br>加密过渡姿态 ${D.review.transition_poses??'—'} 个 · 相邻干涉 ${D.review.transition_contacts??'检查中'} 条`;
if(D.review.wire_seat_count)$('#metrics').innerHTML+=`<br>实际布线固定座 ${D.review.wire_seat_count} 处 · 五指固定握拳`;
if(D.review.maximum_rods_per_adjacent_component)$('#metrics').innerHTML+=`<br>每个相邻连接对象最多 ${D.review.maximum_rods_per_adjacent_component} 根杆`;
ready=true;centerSection();draw();}
$('#pose').onchange=e=>{state.pose=e.target.value;centerSection();draw()};$('#part').onchange=e=>{state.part=e.target.value;state.zoom=1;centerSection();draw()};for(let id of ['mechanisms','contacts','advisories','harness','section','cut'])$('#'+id).oninput=()=>{$('#section-control').hidden=!$('#section').checked;if(id==='section')centerSection();draw()};
document.querySelectorAll('[data-view]').forEach(b=>b.onclick=()=>{let k=b.dataset.view;state.yaw=k==='front'?0:k==='side'?-Math.PI/2:k==='back'?Math.PI:-.7;state.pitch=k==='three'?.13:0;draw()});$('#reset').onclick=()=>{Object.assign(state,{yaw:-.7,pitch:.13,zoom:1,part:'all'});$('#part').value='all';centerSection();draw()};let drag=null;c.onpointerdown=e=>{drag=[e.clientX,e.clientY];c.setPointerCapture(e.pointerId)};c.onpointermove=e=>{if(!drag)return;state.yaw-=(e.clientX-drag[0])*.007;state.pitch=Math.max(-1.4,Math.min(1.4,state.pitch+(e.clientY-drag[1])*.005));drag=[e.clientX,e.clientY];draw()};c.onpointerup=()=>drag=null;c.onpointercancel=()=>drag=null;c.onwheel=e=>{e.preventDefault();state.zoom=Math.max(.3,Math.min(5,state.zoom*Math.exp(-e.deltaY*.001)));draw()};new ResizeObserver(draw).observe(c);
main().catch(e=>{$('#error').hidden=false;$('#error').textContent='载入失败：'+e.message;console.error(e)});
