'use strict';
(() => {
  const D=window.O24,C=window.O24_LESSONS,$=s=>document.querySelector(s),canvas=$('#scene');
  const gl=canvas.getContext('webgl',{antialias:true,alpha:false,preserveDrawingBuffer:true});
  const I=()=>[1,0,0,0,0,1,0,0,0,0,1,0,0,0,0,1];
  const mul=(a,b)=>Array.from({length:16},(_,i)=>[0,1,2,3].reduce((s,k)=>s+a[Math.floor(i/4)*4+k]*b[k*4+i%4],0));
  const trans=v=>{const m=I();v.forEach((x,i)=>m[i*4+3]=x);return m};
  const rot=(axis,angle)=>{const[x,y,z]=axis,a=angle*Math.PI/180,s=Math.sin(a),c=Math.cos(a),t=1-c;return[t*x*x+c,t*x*y-s*z,t*x*z+s*y,0,t*x*y+s*z,t*y*y+c,t*y*z-s*x,0,t*x*z-s*y,t*y*z+s*x,t*z*z+c,0,0,0,0,1]};
  const col=m=>new Float32Array(Array.from({length:16},(_,i)=>m[i%4*4+Math.floor(i/4)]));
  const pos=(m,v=[0,0,0])=>[0,1,2].map(i=>m[i*4]*v[0]+m[i*4+1]*v[1]+m[i*4+2]*v[2]+m[i*4+3]);
  const vec=(m,v)=>pos(m,v).map((x,i)=>x-m[i*4+3]);
  const add=(a,b)=>a.map((x,i)=>x+b[i]),scale=(a,t)=>a.map(x=>x*t),cross=(a,b)=>[a[1]*b[2]-a[2]*b[1],a[2]*b[0]-a[0]*b[2],a[0]*b[1]-a[1]*b[0]];
  const clamp=t=>Math.max(0,Math.min(1,t)),ease=t=>{t=clamp(t);return t*t*(3-2*t)};
  const state={chapter:'elbow',motion:'elbow_flex',mode:'rotate',time:0,playing:!matchMedia('(prefers-reduced-motion: reduce)').matches,speed:1,yaw:.78,pitch:.24,span:160,center:[0,0,0],zoom:1,selected:null};
  const fixedColor=[.29,.53,.51],movingColor=[.92,.65,.30],axisColor=[.52,.37,.75],boneColor=[.78,.29,.46];
  let ready=false,dirty=true,F,V,models=new Map(),buffer,lineBuffer,program,L,lastTime=0,lastUi=-1,labelButtons=[];
  const chapter=()=>C.chapters.find(c=>c.id===state.chapter),motion=()=>C.motions[state.motion];
  const parts=()=>D.parts.filter(p=>p.i>=chapter().range[0]&&p.i<=chapter().range[1]);
  function fk(angles={}){
    const a=n=>angles[n]||0,p=D.profile,f={chest:trans(p.root)};
    f.collar_z=mul(f.chest,rot([0,0,-1],a('clavicle_protract')));f.collar=mul(f.collar_z,rot([1,0,0],a('clavicle_elevate')));
    f.shoulder_base=mul(f.collar,trans(p.clavicle_vector));f.shoulder_pitch=mul(f.shoulder_base,rot([0,-1,0],a('shoulder_flex')));
    f.shoulder_swing=mul(f.shoulder_pitch,rot([1,0,0],a('shoulder_abduct')));f.upper=mul(f.shoulder_swing,rot([0,0,-1],a('upperarm_roll')));
    f.elbow_base=mul(f.upper,trans([0,0,-p.upperarm_mm]));f.elbow=mul(f.elbow_base,rot([0,-1,0],a('elbow_flex')));
    f.fore=mul(f.elbow,rot([0,0,-1],p.forearm_zero_clocking_deg+a('forearm_roll')));f.wrist_base=mul(f.fore,trans([0,0,-p.forearm_mm]));
    f.wrist_flex=mul(f.wrist_base,rot([0,1,0],a('wrist_flex')));f.hand=mul(f.wrist_flex,rot([1,0,0],a('wrist_deviation')));return f;
  }
  function anglesAt(t){if(state.mode!=='rotate')return{};const m=motion(),at=Math.min(3,Math.floor(t*4)),v=m.keys[at]+(m.keys[at+1]-m.keys[at])*ease(t*4-at);return{...m.base,[state.motion]:v}}
  const centerOf=p=>p.bounds_mm[0].map((x,i)=>(x+p.bounds_mm[1][i])/2);
  function offset(p){
    // Teaching separation vectors only; these are not verified physical insertion paths.
    if(state.chapter==='whole'){const g=C.group(p);return [0,g*44,-g*17]}
    const n=p.name,mid=centerOf(p),s=C.stage(p);let a;
    if(/^clavicle_z/.test(n)||n==='chest_mount')a=[0,0,1];
    else if(/^clavicle_(x|elevation)/.test(n))a=[1,0,0];
    else if(/^clavicle_link/.test(n))return[n.endsWith('_-1')?-17:17,13,-12];
    else if(/^shoulder_pitch/.test(n))a=[0,-1,0];
    else if(/^shoulder_(swing|cross)/.test(n))a=[Math.sign(mid[0])||1,0,0];
    else if(n==='shoulder_open_yoke')return[0,12,12];
    else if(/^humeral|^upperarm/.test(n))a=[0,0,-1];
    else if(/^elbow/.test(n))a=[0,Math.sign(mid[1])||1,0];
    else if(/^forearm/.test(n))a=[0,0,-1];
    else if(/^wrist_(flex|input)/.test(n))a=[0,Math.sign(mid[1])||1,0];
    else if(/^wrist_(dev|output)/.test(n))a=[Math.sign(mid[0])||1,0,0];
    else a=[0,0,-1];
    if(/_(magnet|pcb|connector|sensor_holder)$/.test(n)){
      if(n.startsWith('clavicle_z'))a=[0,0,1];
      else if(n.startsWith('clavicle_x')||n.startsWith('wrist_deviation'))a=[1,0,0];
      else if(n.startsWith('shoulder_swing'))a=[-1,0,0];
      else if(n.startsWith('humeral')||n.startsWith('forearm'))a=[0,0,1];
      else a=[0,-1,0];
    }
    let distance=[9,22,32,43,54,71][s];
    if(p.role==='bearing')distance+=Math.abs(mid.find((_,i)=>a[i]!==0)||0)*.27;
    if(n.endsWith('_connector'))distance+=3;
    if(n.endsWith('_sensor_holder'))distance-=13;
    if(n==='elbow_hub')return[0,0,-24];
    if(n==='wrist_cross')return[0,0,0];
    if(n==='shoulder_cross_head')return[0,0,-16];
    if(/_housing$/.test(n)&&s===0)return scale(a,5);
    return scale(a,distance);
  }
  function amount(p,t){if(state.mode==='rotate')return 0;if(state.mode==='explode')return ease(t);return 1-ease(t*6-(state.chapter==='whole'?C.group(p):C.stage(p)))}
  function model(p,frames,t){const d=scale(offset(p),amount(p,t));return state.chapter==='whole'?mul(trans(d),frames[p.frame]):mul(frames[p.frame],trans(d))}
  function fit(resetView=false){
    if(resetView){state.yaw=chapter().yaw;state.pitch=chapter().pitch}
    const samples=state.mode==='rotate'?Array.from({length:17},(_,i)=>i/16):[0,1],points=[];
    for(const t of samples){const f=fk(anglesAt(t));for(const p of parts()){
      const m=model(p,f,t),[lo,hi]=p.bounds_mm;
      for(const x of [lo[0],hi[0]])for(const y of [lo[1],hi[1]])for(const z of [lo[2],hi[2]])points.push(pos(m,[x,y,z]));
    }
      if(state.mode==='rotate'){
        if(state.chapter==='elbow')points.push(pos(f.wrist_base));
        if(state.chapter==='forearm')points.push(pos(f.elbow_base),pos(f.wrist_base),pos(f.hand,[0,0,-45]));
      }
    }
    const sy=Math.sin(state.yaw),cy=Math.cos(state.yaw),sp=Math.sin(state.pitch),cp=Math.cos(state.pitch);
    const basis=[-sy,cy,0,0,-sp*cy,-sp*sy,cp,0,cp*cy,cp*sy,sp,0,0,0,0,1],projected=points.map(p=>pos(basis,p));
    const lo=[0,1,2].map(k=>Math.min(...projected.map(p=>p[k]))),hi=[0,1,2].map(k=>Math.max(...projected.map(p=>p[k]))),middle=lo.map((x,i)=>(x+hi[i])/2);
    state.center=[0,1,2].map(i=>basis[i]*middle[0]+basis[4+i]*middle[1]+basis[8+i]*middle[2]);const aspect=canvas.clientWidth/Math.max(1,canvas.clientHeight);
    state.span=Math.max((hi[1]-lo[1])*1.38,(hi[0]-lo[0])/aspect*1.42);
    if(state.mode==='rotate'&&state.chapter!=='whole')state.span=Math.max(state.span,chapter().span);
    state.zoom=1;dirty=true;
  }
  function shader(type,source){const s=gl.createShader(type);gl.shaderSource(s,source);gl.compileShader(s);if(!gl.getShaderParameter(s,gl.COMPILE_STATUS))throw Error(gl.getShaderInfoLog(s));return s}
  function bind(b){gl.bindBuffer(gl.ARRAY_BUFFER,b);for(const[k,off]of[['p',0],['n',12]]){gl.enableVertexAttribArray(L[k]);gl.vertexAttribPointer(L[k],3,gl.FLOAT,false,24,off)}}
  function setup(){
    if(!gl)throw Error('此浏览器未启用 WebGL，无法显示三维动画。请使用支持 WebGL 的浏览器打开。');
    program=gl.createProgram();
    gl.attachShader(program,shader(gl.VERTEX_SHADER,'attribute vec3 p,n;uniform mat4 model,view;uniform vec2 scale;varying vec3 norm;void main(){vec4 v=view*model*vec4(p,1.);gl_Position=vec4(v.x*scale.x,v.y*scale.y,-v.z/2000.,1.);norm=mat3(view*model)*n;}'));
    gl.attachShader(program,shader(gl.FRAGMENT_SHADER,'precision mediump float;varying vec3 norm;uniform vec3 color;uniform float opacity,line;void main(){float light=.58+.42*abs(dot(normalize(norm),normalize(vec3(.35,.45,1.))));gl_FragColor=vec4(color*mix(light,1.,line),opacity);}'));
    gl.linkProgram(program);if(!gl.getProgramParameter(program,gl.LINK_STATUS))throw Error(gl.getProgramInfoLog(program));gl.useProgram(program);L={};
    for(const k of['model','view','scale','color','opacity','line'])L[k]=gl.getUniformLocation(program,k);for(const k of['p','n'])L[k]=gl.getAttribLocation(program,k);
    buffer=gl.createBuffer();lineBuffer=gl.createBuffer();const bin=atob(D.geometry),bytes=new Uint8Array(bin.length);for(let i=0;i<bin.length;i++)bytes[i]=bin.charCodeAt(i);
    bind(buffer);gl.bufferData(gl.ARRAY_BUFFER,new Float32Array(bytes.buffer),gl.STATIC_DRAW);ready=true;
  }
  function lines(points,color,opacity=1){if(!points.length)return;bind(lineBuffer);gl.bufferData(gl.ARRAY_BUFFER,new Float32Array(points.flatMap(p=>[...p,0,0,1])),gl.DYNAMIC_DRAW);gl.uniformMatrix4fv(L.model,false,col(I()));gl.uniform3fv(L.color,color);gl.uniform1f(L.line,1);gl.uniform1f(L.opacity,opacity);gl.drawArrays(gl.LINES,0,points.length)}
  function dashed(a,b,color,segments=18){const points=[];for(let i=0;i<segments;i+=2)for(const t of[i/segments,(i+1)/segments])points.push(a.map((x,j)=>x+(b[j]-x)*t));lines(points,color)}
  function drawAxes(){
    const m=motion(),origin=pos(F[m.parent]),direction=vec(F[m.parent],m.axis),len=state.chapter==='whole'?37:state.chapter==='forearm'?85:30;
    let start=add(origin,scale(direction,-len*.5)),end=add(origin,scale(direction,len));
    lines([start,end],axisColor);const u=Math.abs(direction[2])<.8?cross(direction,[0,0,1]):cross(direction,[0,1,0]),v=cross(direction,u);
    for(const w of[u,v])lines([add(end,add(scale(direction,-5),scale(w,2.4))),end,add(end,add(scale(direction,-5),scale(w,-2.4))),end],axisColor);
    const circle=[],radius=state.chapter==='whole'?13:12,angle=(anglesAt(state.time)[state.motion]||0)*Math.PI/180;
    for(let i=0;i<36;i++){const point=t=>add(origin,add(scale(u,Math.cos(t)*radius),scale(v,Math.sin(t)*radius)));circle.push(point(i/36*angle),point((i+1)/36*angle))}
    lines(circle,axisColor);const tick=add(origin,add(scale(u,Math.cos(angle)*radius),scale(v,Math.sin(angle)*radius)));lines([origin,tick],axisColor);
  }
  function drawBones(){
    const ids=state.chapter==='elbow'?['shoulder_base','elbow_base','wrist_base']:state.chapter==='forearm'?['elbow_base','wrist_base']:state.chapter==='wrist'?['wrist_base']:['chest','shoulder_base','elbow_base','wrist_base'];
    const points=ids.map(n=>pos(F[n]));if(['whole','wrist'].includes(state.chapter))points.push(pos(F.hand,[0,0,-45]));
    for(let i=1;i<points.length;i++)dashed(points[i-1],points[i],boneColor);
    const marks=[];for(const p of points)for(let i=0;i<3;i++){const a=[...p],b=[...p];a[i]-=1.8;b[i]+=1.8;marks.push(a,b)}lines(marks,boneColor);
  }
  function project(point){const p=pos(V,point),h=canvas.clientHeight,w=canvas.clientWidth;return[w/2+p[0]*h*state.zoom/state.span,h/2-p[1]*h*state.zoom/state.span]}
  function updateLabels(){
    const enabled=$('#show-labels').checked;$('#labels').hidden=!enabled;$('#leaders').hidden=!enabled;if(!enabled)return;
    const w=canvas.clientWidth,h=canvas.clientHeight,width=w<500?114:139;
    let svg='';labelButtons.forEach(({button,p},i)=>{
      const m=models.get(p.name),xy=project(pos(m,centerOf(p))),right=i%2===1,rows=Math.ceil(labelButtons.length/2);
      const x=right?w-width-13:13,y=66+Math.floor(i/2)*Math.min(70,(h-190)/Math.max(1,rows-1));
      button.style.left=x+'px';button.style.top=y+'px';button.style.maxWidth=width+'px';button.classList.toggle('selected',state.selected===p.name);
      const edge=right?x:x+button.offsetWidth;
      if(xy[0]>=0&&xy[0]<=w&&xy[1]>=0&&xy[1]<=h)svg+=`<line x1="${edge}" y1="${y+14}" x2="${xy[0]}" y2="${xy[1]}"/><circle cx="${xy[0]}" cy="${xy[1]}" r="2.5"/>`;
    });
    if(state.mode==='rotate'&&$('#show-bones').checked){
      const centers=state.chapter==='whole'?[['chest','C'],['shoulder_base','S'],['elbow_base','E'],['wrist_base','W']]:state.chapter==='forearm'?[['elbow_base','E · 肘中心'],['wrist_base','W · 腕中心']]:[[chapter().anchor,({elbow:'E · 肘中心',wrist:'W · 腕中心',shoulder:'S · 肩中心',clavicle:'C · 锁骨根'})[state.chapter]]];
      for(const[frame,name]of centers){const[x,y]=project(pos(F[frame]));if(x>8&&x<w-90&&y>35&&y<h-80)svg+=`<text x="${x+9}" y="${y-13}" font-size="10" fill="#a34564" stroke="#edf2e9" stroke-width="3" paint-order="stroke">${name}</text>`}
    }
    $('#leaders').innerHTML=svg;
  }
  function draw(){
    if(!ready)return;const w=canvas.clientWidth,h=canvas.clientHeight,dpr=Math.min(2,devicePixelRatio||1);if(canvas.width!==Math.round(w*dpr)||canvas.height!==Math.round(h*dpr)){canvas.width=Math.round(w*dpr);canvas.height=Math.round(h*dpr)}
    gl.viewport(0,0,canvas.width,canvas.height);gl.clearColor(.9294,.9490,.9137,1);gl.clear(gl.COLOR_BUFFER_BIT|gl.DEPTH_BUFFER_BIT);gl.enable(gl.DEPTH_TEST);gl.enable(gl.BLEND);gl.blendFunc(gl.SRC_ALPHA,gl.ONE_MINUS_SRC_ALPHA);
    const sy=Math.sin(state.yaw),cy=Math.cos(state.yaw),sp=Math.sin(state.pitch),cp=Math.cos(state.pitch);V=[-sy,cy,0,0,-sp*cy,-sp*sy,cp,0,cp*cy,cp*sy,sp,0,0,0,0,1];
    for(let i=0;i<3;i++)V[i*4+3]=-V[i*4]*state.center[0]-V[i*4+1]*state.center[1]-V[i*4+2]*state.center[2];
    gl.uniformMatrix4fv(L.view,false,col(V));gl.uniform2f(L.scale,2*state.zoom/state.span*h/w,2*state.zoom/state.span);gl.uniform1f(L.line,0);F=fk(anglesAt(state.time));
    const active=parts(),set=new Set(active.map(p=>p.name));models=new Map(active.map(p=>[p.name,model(p,F,state.time)]));const diagnostics=[];
    bind(buffer);
    if($('#show-context').checked&&state.chapter!=='whole'&&state.mode==='rotate'){
      gl.depthMask(false);for(const p of D.parts){if(set.has(p.name))continue;gl.uniformMatrix4fv(L.model,false,col(F[p.frame]));gl.uniform3fv(L.color,C.descendant(p.frame,motion().child)?[.80,.63,.39]:[.55,.68,.62]);gl.uniform1f(L.opacity,.13);gl.drawArrays(gl.TRIANGLES,p.first,p.count)}gl.depthMask(true);
    }
    const step=Math.min(5,Math.floor(state.time*6));
    for(const p of active){
      let color=state.mode==='rotate'?(C.descendant(p.frame,motion().child)?movingColor:fixedColor):p.color;
      if(state.selected===p.name)color=[.97,.79,.37];
      const a=amount(p,state.time),ps=state.chapter==='whole'?C.group(p):C.stage(p),opacity=state.mode==='assemble'&&ps>step?.24:1;
      if(opacity<1)gl.depthMask(false);gl.uniformMatrix4fv(L.model,false,col(models.get(p.name)));gl.uniform3fv(L.color,color);gl.uniform1f(L.opacity,opacity);gl.drawArrays(gl.TRIANGLES,p.first,p.count);gl.depthMask(true);
      diagnostics.push({name:p.name,stage:ps,separation:a,matrix:models.get(p.name),opacity});
    }
    gl.disable(gl.DEPTH_TEST);gl.uniform1f(L.opacity,1);
    if(state.mode==='rotate'){if($('#show-bones').checked)drawBones();drawAxes()}
    else if(state.mode==='explode'&&state.time>.01){
      // Tethers terminate at the true assembled positions, not at imaginary joint centers.
      for(const[name]of chapter().labels){const p=active.find(p=>p.name===name);dashed(pos(F[p.frame],centerOf(p)),pos(models.get(name),centerOf(p)),[.67,.74,.64],12)}
    }
    gl.enable(gl.DEPTH_TEST);updateLabels();updatePlaybackUI();
    const m=motion();window.O24_TUTORIAL_STATE={ready:true,chapter:state.chapter,mode:state.mode,motion:state.motion,time:state.time,playing:state.playing,angles:anglesAt(state.time),frames:F,parts:diagnostics,axis:{origin:pos(F[m.parent]),direction:vec(F[m.parent],m.axis)},geometryParts:D.parts.length,manufacturingRelease:false};
    dirty=false;
  }
  function labelUI(){
    $('#labels').replaceChildren();labelButtons=[];for(const[name,label]of chapter().labels){const p=D.parts.find(p=>p.name===name);if(!p)throw Error('标签未匹配实际零件：'+name);const button=document.createElement('button');button.className='part-label';button.innerHTML=`<b>${labelButtons.length+1}</b>${label}`;button.setAttribute('aria-label','认识零件：'+label);button.onclick=()=>selectPart(name);$('#labels').append(button);labelButtons.push({button,p})}
  }
  function selectPart(name){state.selected=name;$('#part-select').value=name;$('#parts-details').open=true;partInfo();dirty=true}
  function partInfo(){
    const p=D.parts.find(p=>p.name===$('#part-select').value);if(!p)return;const s=C.stage(p);
    let text=[
      '支承结构负责连接与定位。外形围绕骨线展开，孔位决定实际转轴。',
      '轴承支撑轴与支座的相对旋转。显示的是简化外形，内外圈及滚珠没有分别建模。',
      '此件参与传递转动。轴与输出件的具体防转、轴向锁固和装配配合仍需细化。',
      '摩擦与轴向预紧用于持姿；不能从当前外形直接得到可靠的持姿力矩。',
      '磁铁随被测转动件转动。专用磁铁座和防转固定仍待完成。',
      '传感板及其安装空间用于测角。支架锁固、插头型号与线束路线尚待细化。'
    ][s];
    if(p.name.endsWith('_connector'))text='这是插头预留空间的实体占位，实际连接器型号与出线方向尚未冻结。';
    $('#part-info').replaceChildren();const strong=document.createElement('strong');strong.textContent=C.partName(p);const code=document.createElement('code');code.textContent=p.name;const detail=document.createElement('div');detail.textContent=text;$('#part-info').append(strong,code,detail);
  }
  function refreshLesson(){
    const c=chapter(),m=motion(),index=C.chapters.indexOf(c);$('#lesson-counter').textContent=`CHAPTER ${String(index+1).padStart(2,'0')} / 06`;$('#lesson-title').textContent=c.title;$('#lesson-intro').textContent=c.intro;$('#takeaway').textContent=c.takeaway;$('#chapter-limit').textContent=c.limit;
    $('#scene-name').textContent=c.nav+' / '+({rotate:'观察相对转动',explode:'零件展开',assemble:'分步装配关系'})[state.mode];
    for(const b of document.querySelectorAll('[data-chapter]'))b.setAttribute('aria-current',String(b.dataset.chapter===state.chapter));
    for(const b of document.querySelectorAll('[data-mode]'))b.setAttribute('aria-pressed',String(b.dataset.mode===state.mode));
    $('#motion-options').replaceChildren();$('#motion-options').hidden=state.mode!=='rotate';for(const id of c.motions){const b=document.createElement('button');b.textContent=C.motions[id].short;b.dataset.motion=id;b.setAttribute('aria-pressed',String(id===state.motion));b.onclick=()=>{state.motion=id;state.time=0;state.selected=null;refreshLesson();fit(true)};$('#motion-options').append(b)}
    $('#relationship').hidden=state.mode!=='rotate';$('#relationship').innerHTML=`<div class="relation-row"><i style="background:#4a8782"></i><b>固定</b><span>${m.fixed}</span></div><div class="relation-row"><i style="background:#eaa64c"></i><b>转动</b><span>${m.moving}</span></div>`;
    $('#scene-note').textContent=state.mode==='rotate'?'颜色表示当前这一根轴的相对运动；淡色为相邻结构。':'教学展开：虚线连接原位置；展开距离与移入路径不代表实际装配工艺。';
    $('#legend').innerHTML=(state.mode==='rotate'?[['#4a8782','固定侧'],['#eaa64c','转动侧'],['#855ebf','旋转轴'],['#c74a75','UE 骨线']]:[['#a6c9c2','支架'],['#e9a34a','转动件'],['#485461','轴承'],['#bb3b40','磁铁'],['#146d4c','传感板']]).map(([c,t])=>`<span><i style="background:${c}"></i>${t}</span>`).join('');
    $('#show-bones').disabled=state.mode!=='rotate';$('#show-context').disabled=state.mode!=='rotate'||state.chapter==='whole';
    $('#timeline-title').textContent=({rotate:'动作进度 · 教学角度',explode:'拆解程度',assemble:'装配进度 · 每步可暂停'})[state.mode];
    const list=parts();$('#part-count').textContent=list.length+' 件';$('#part-select').replaceChildren();for(const p of list){const o=document.createElement('option');o.value=p.name;o.textContent=`${String(p.i+1).padStart(3,'0')} · ${C.partName(p)}`;$('#part-select').append(o)}
    if(state.selected&&list.some(p=>p.name===state.selected))$('#part-select').value=state.selected;else $('#parts-details').open=false;partInfo();labelUI();lastUi=-1;dirty=true;
  }
  function updatePlaybackUI(){
    const stamp=Math.floor(state.time*1000);if(lastUi===stamp&&!dirty)return;lastUi=stamp;
    $('#timeline').value=String(stamp);$('#progress').textContent=Math.round(state.time*100)+'%';$('#play').textContent=state.playing?'Ⅱ 暂停':'▶ 播放';$('#play').setAttribute('aria-label',state.playing?'暂停动画':'播放动画');
    $('#prev-step').disabled=state.time<=0;$('#next-step').disabled=state.time>=1;
    if(state.mode==='rotate'){
      const m=motion(),axis=D.profile.axes.find(a=>a.id===state.motion);$('#readout').textContent=Math.round(anglesAt(state.time)[state.motion])+'°';
      $('#instruction-kicker').textContent='这一根轴怎样转';$('#instruction-title').textContent=m.short;$('#instruction-text').textContent=m.text;
      $('#step-caption').textContent=`示范 ${Math.min(...m.keys)}° ～ ${Math.max(...m.keys)}°`;
      $('#readout').title=`模型名义范围 ${axis.limits_deg[0]}° ～ ${axis.limits_deg[1]}°`;
    }else if(state.mode==='explode'){
      $('#readout').textContent='展开 '+Math.round(state.time*100)+'%';$('#instruction-kicker').textContent=state.chapter==='whole'?'按六个模块拆开':'按零件关系拆开';
      $('#instruction-title').textContent=state.time<.02?'从装好状态开始':'拉开间距，看清内外层次';$('#instruction-text').textContent=state.chapter==='whole'?'肩带、肩与上臂、肘、前臂、腕、手掌依次展开。点标签可查看真实模型中的对应零件。':'外壳、轴承、转轴、摩擦片和传感器分开显示。虚线指向装好时的位置；点标签可以了解零件的作用。';
      $('#step-caption').textContent=state.time>=1?'完全展开 · 可切换「装回去」':'拖动进度，逐渐拉开零件';
    }else{
      const index=Math.min(5,Math.floor(state.time*6)),steps=state.chapter==='whole'?C.wholeSteps:C.steps,step=steps[index],n=parts().filter(p=>amount(p,state.time)<1e-8).length;
      $('#readout').textContent=`就位 ${n} / ${parts().length} 件`;$('#instruction-kicker').textContent=`装配关系 · 第 ${index+1} / 6 步`;
      $('#instruction-title').textContent=state.time>=1?'全部回到名义位置':step.title;$('#instruction-text').textContent=state.time>=1?'现在可以切换「看旋转」，观察这些零件如何一起工作。尚未完成的锁固、预紧和磁铁座不能由这段动画代替。':step.text;
      $('#step-caption').textContent=state.time>=1?'6 / 6 · 关系展示完成':`${index+1} / 6 · ${step.title}`;
    }
  }
  function changeChapter(id){state.chapter=id;state.motion=chapter().motions[0];state.time=0;state.selected=null;refreshLesson();fit(true)}
  for(const[c,i]of C.chapters.map((c,i)=>[c,i])){const b=document.createElement('button');b.dataset.chapter=c.id;b.innerHTML=`<span class="chapter-index">${String(i+1).padStart(2,'0')}</span><span><span class="chapter-name">${c.nav}</span><span class="chapter-subtitle">${c.sub}</span></span>`;b.onclick=()=>changeChapter(c.id);$('#chapters').append(b)}
  for(const b of document.querySelectorAll('[data-mode]'))b.onclick=()=>{state.mode=b.dataset.mode;state.time=0;state.selected=null;refreshLesson();fit(true)};
  $('#play').onclick=()=>{if(!state.playing&&state.time>=1)state.time=0;state.playing=!state.playing;lastTime=0;dirty=true};
  $('#restart').onclick=()=>{state.time=0;state.playing=true;lastTime=0;dirty=true};
  $('#timeline').oninput=e=>{state.time=+e.target.value/1000;state.playing=false;dirty=true};$('#speed').onchange=e=>{state.speed=+e.target.value};
  function step(dir){const count=state.mode==='assemble'?6:4;state.time=clamp((dir>0?Math.floor(state.time*count+1e-6)+1:Math.ceil(state.time*count-1e-6)-1)/count);state.playing=false;dirty=true}
  $('#prev-step').onclick=()=>step(-1);$('#next-step').onclick=()=>step(1);$('#fit').onclick=()=>fit(true);
  for(const b of document.querySelectorAll('[data-view]'))b.onclick=()=>{[state.yaw,state.pitch]=({three:[chapter().yaw,chapter().pitch],front:[0,0],side:[Math.PI/2,0]})[b.dataset.view];fit(false)};
  for(const id of['show-bones','show-labels','show-context'])$('#'+id).onchange=()=>{dirty=true};
  $('#part-select').onchange=e=>{state.selected=e.target.value;partInfo();dirty=true};
  let drag=null;
  canvas.onpointerdown=e=>{drag=[e.clientX,e.clientY];canvas.setPointerCapture(e.pointerId)};canvas.onpointerup=canvas.onpointercancel=()=>{drag=null};
  canvas.onpointermove=e=>{if(!drag)return;state.yaw-=(e.clientX-drag[0])*.008;state.pitch=Math.max(-1.35,Math.min(1.35,state.pitch+(e.clientY-drag[1])*.008));drag=[e.clientX,e.clientY];dirty=true};
  canvas.onwheel=e=>{e.preventDefault();state.zoom=Math.max(.5,Math.min(4,state.zoom*Math.exp(-e.deltaY*.001)));dirty=true};
  new ResizeObserver(()=>{if(ready)fit(false)}).observe(canvas);document.addEventListener('visibilitychange',()=>{if(document.hidden){state.playing=false;dirty=true}});
  canvas.addEventListener('webglcontextlost',e=>{e.preventDefault();state.playing=false;$('#error').hidden=false;$('#error').textContent='三维图形上下文已暂停。请刷新页面重新载入模型。'});
  function tick(now){if(lastTime&&state.playing){const duration=state.mode==='rotate'?10:state.mode==='explode'?9:22;state.time+=Math.min(.1,(now-lastTime)/1000)*state.speed/duration;if(state.time>=1){if(state.mode==='rotate')state.time%=1;else{state.time=1;state.playing=false}}dirty=true}lastTime=now;if(dirty)draw();requestAnimationFrame(tick)}
  try{setup();refreshLesson();fit(true);draw();requestAnimationFrame(tick)}catch(e){$('#error').hidden=false;$('#error').textContent=e.message;console.error(e)}
})();
