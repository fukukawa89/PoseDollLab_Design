'use strict';
(() => {
const $ = s => document.querySelector(s);
const $$ = s => [...document.querySelectorAll(s)];
const ASSETS = window.BENCH_ASSETS;
const reduced = matchMedia('(prefers-reduced-motion: reduce)');
const clamp = (x,a,b) => Math.min(b,Math.max(a,x));
const parts = [
 {id:'B8',short:'B 型碟簧',sub:'8 × 4.2 × 0.3',title:'小碟簧 · B 型',subtitle:'标准件 / 锐尔立 B 系列',type:'直接采购 · 至少 6 片',purpose:'用在 LP6 大关节候选中。像带孔的小圆碟，略微拱起；压下时提供夹紧力。它不是普通平垫圈。',specs:[['外径',8],['内径',4.2],['材料厚度',.3],['自由高度',.55]],quantity:6,color:[146,163,168],r:4,t:.3,h:.55,caption:'名义尺寸模型 · 锥度按尺寸绘制，可转到侧面观察',note:'6 片组成 3 对，两片反向叠放。B8 是尺寸简称，下单请写完整规格。',source:'https://www.raleigh-spring.cn/discspring/',sourceText:'查看中国厂家目录 ↗'},
 {id:'A8',short:'A 型碟簧',sub:'8 × 4.2 × 0.4',title:'小碟簧 · A 型',subtitle:'标准件 / 锐尔立 A 系列',type:'直接采购 · 至少 12 片',purpose:'用在 M4 小关节候选中。外径与 B 型相同，但材料更厚、自由高度不同；不要把两种混在同一袋里。',specs:[['外径',8],['内径',4.2],['材料厚度',.4],['自由高度',.6]],quantity:12,color:[146,163,168],r:4,t:.4,h:.6,caption:'名义尺寸模型 · 与 B 型同外径，厚度和自由高度不同',note:'12 片组成 3 组，每组 4 片交替朝向。请按袋标记 A / B、批次和编号。',source:'https://www.raleigh-spring.cn/discspring/',sourceText:'查看中国厂家目录 ↗'},
 {id:'LP6_PEEK_coupon',short:'大 PEEK 片',sub:'接触环 Ø28',title:'大号摩擦试片',subtitle:'LP6 / 未填充 PEEK',type:'按图加工 · 至少 3 片',purpose:'米白色工程塑料薄片，与金属表面摩擦。三个小外耳供夹具固定，位于接触环外，不计入有效摩擦面积。',specs:[['接触区外径',28],['接触区内径',12],['厚度',.6],['外耳数量',3,'个']],quantity:3,color:[217,188,132],r:15.6,caption:'从当前 STEP 提取 · 3 个外耳在接触环外，颜色为示意',note:'指定可追溯的未填充 PEEK，不使用玻纤 / 碳纤填充料代替。加工前确认平面度、装夹和实际厚度。',source:'../../bench/revO7/coupons/LP6_PEEK_coupon.step',sourceText:'下载 LP6 塑料试片 STEP ↓'},
 {id:'M4_PEEK_coupon',short:'小 PEEK 片',sub:'接触环 Ø14.8',title:'小号摩擦试片',subtitle:'M4 / 未填充 PEEK',type:'按图加工 · 至少 3 片',purpose:'与大试片使用同类材料，但接触环更小。单独测试，才能判断小关节的保持力是否足够；不能直接套用大试片结果。',specs:[['接触区外径',14.8],['接触区内径',5.2],['厚度',.4],['外耳数量',3,'个']],quantity:3,color:[217,188,132],r:9,caption:'从当前 STEP 提取 · 本页自动放大，比较尺寸请看标注',note:'外耳是夹具固定位置，不能压在活动摩擦面上。试片和对应金属件一起询价。',source:'../../bench/revO7/coupons/M4_PEEK_coupon.step',sourceText:'下载 M4 塑料试片 STEP ↓'},
 {id:'LP6_metal_counterface',short:'大金属片',sub:'外径 Ø34',title:'大号金属对偶件',subtitle:'与 LP6 PEEK 试片配对',type:'按图加工 · 至少 1 件',purpose:'“对偶件”就是和塑料片接触的另一件。它绕中心转动；外围 4 个孔用于装夹，不属于摩擦接触环。',specs:[['外径',34],['中心孔径',6.1],['厚度',3],['安装孔径',2.2]],quantity:1,color:[136,160,169],r:17,caption:'从当前 STEP 提取 · 4 个外围孔用于实验室装夹',note:'金属牌号、表面加工与平面度还需确认。STEP 中的颜色不代表已选定钢号，报价时要写明实际材料。',source:'../../bench/revO7/coupons/LP6_metal_counterface.step',sourceText:'下载 LP6 金属件 STEP ↓'},
 {id:'M4_metal_counterface',short:'小金属片',sub:'外径 Ø20',title:'小号金属对偶件',subtitle:'与 M4 PEEK 试片配对',type:'按图加工 · 至少 1 件',purpose:'与小 PEEK 环形成一对测试表面。金属的材质、粗糙度、清洁和温度都要记录，结果只适用于该材料配对。',specs:[['外径',20],['中心孔径',3.1],['厚度',3],['安装孔径',1.7]],quantity:1,color:[136,160,169],r:10,caption:'从当前 STEP 提取 · 本页模型可转动，不包含完整测矩夹具',note:'安装孔在分布圆 Ø17.8 上，4 孔均布，首孔 45°。加工与检测方需确认夹具匹配后再制作。',source:'../../bench/revO7/coupons/M4_metal_counterface.step',sourceText:'下载 M4 金属件 STEP ↓'}
];
const state = {view:'parts', part:0, yaw:.35, tilt:.9, zoom:1, spin:false,
 spring:{type:'B8',step:0,progress:0,playing:false},
 friction:{type:'LP6',step:0,progress:0,playing:false}};
let toastTimer;
function toast(message){$('#toast').textContent=message;$('#toast').hidden=false;clearTimeout(toastTimer);toastTimer=setTimeout(()=>$('#toast').hidden=true,3600);}
async function copy(text){
 try { if(!navigator.clipboard)throw Error('Clipboard unavailable');await navigator.clipboard.writeText(text);toast('已复制，可粘贴给对方。'); }
 catch {$('#copy-fallback').value=text;$('#copy-dialog').showModal();$('#copy-fallback').select();}
}
$('#close-copy').onclick=()=>$('#copy-dialog').close();
function icon(part){
 const c=part.id.includes('PEEK')?'#cfb582':'#93a8ae';
 return '<svg viewBox="0 0 40 40" aria-hidden="true"><ellipse cx="20" cy="23" rx="16" ry="10" fill="#dfe4de"/><path d="M4 20a16 10 0 1 0 32 0a16 10 0 1 0-32 0M14 18a6 4 0 1 1 12 0a6 4 0 1 1-12 0" fill="'+c+'" fill-rule="evenodd" stroke="#647a7d" stroke-width=".6"/></svg>';
}
$('#part-selector').innerHTML=parts.map((p,i)=>'<button class="part-choice" data-part="'+i+'" aria-pressed="false">'+icon(p)+'<span><b>'+p.short+'</b><small>'+p.sub+'</small></span></button>').join('');
const canvas=$('#part-canvas'), ctx=canvas.getContext('2d');
function springMesh(t,h){
 const vertices=[],faces=[],n=96;
 for(let k=0;k<4;k++){
  const r=k%2?2.1:4, z=(k%2?h-t:0)+(k>1?t:0);
  for(let i=0;i<n;i++){const a=i*2*Math.PI/n;vertices.push([r*Math.cos(a),r*Math.sin(a),z-h/2]);}
 }
 for(const [a,b] of [[0,1],[1,3],[3,2],[2,0]])for(let i=0;i<n;i++){const j=(i+1)%n;faces.push([a*n+i,b*n+i,b*n+j],[a*n+i,b*n+j,a*n+j]);}
 return {vertices,faces};
}
parts.forEach(p=>{
 const mesh=p.h?springMesh(p.t,p.h):ASSETS.models[p.id];
 let low=Infinity,high=-Infinity;for(const v of mesh.vertices){low=Math.min(low,v[2]);high=Math.max(high,v[2]);}
 p.mesh={vertices:mesh.vertices.map(v=>[v[0],v[1],v[2]-(low+high)/2]),faces:mesh.faces};
});
function partSelect(i){
 state.part=i;state.spin=false;state.yaw=.35;state.tilt=.9;state.zoom=1;
 const p=parts[i];
 $$('.part-choice').forEach((b,j)=>b.setAttribute('aria-pressed',String(i===j)));
 $('#part-info').innerHTML='<span class="part-type">'+p.type+'</span><h2>'+p.title+'</h2><p class="part-subtitle">'+p.subtitle+'</p><p class="purpose">'+p.purpose+'</p><dl class="specs">'+p.specs.map(s=>'<div><dt>'+s[0]+'</dt><dd>'+s[1]+' <small>'+(s[2]||'mm')+'</small></dd></div>').join('')+'</dl><div class="purchase-note"><strong>准备时记住</strong>'+p.note+'<br><a href="'+p.source+'" '+(p.source.startsWith('http')?'target="_blank" rel="noopener noreferrer"':'download')+'>'+p.sourceText+'</a></div>';
 $('#model-origin').textContent=p.h?'按目录尺寸建模':'当前试片 STEP 模型';
 $('#model-index').textContent=String(i+1).padStart(2,'0')+' / 06';
 $('#model-caption').textContent=p.caption;
 $('#model-spin').textContent='▷ 自动旋转';$('#model-spin').setAttribute('aria-pressed','false');
 drawPart();
}
$$('[data-part]').forEach(b=>b.onclick=()=>partSelect(Number(b.dataset.part)));
function drawPart(){
 if(state.view!=='parts')return;
 const w=canvas.clientWidth,h=canvas.clientHeight,dpr=Math.min(devicePixelRatio||1,2);
 if(canvas.width!==Math.round(w*dpr)||canvas.height!==Math.round(h*dpr)){canvas.width=Math.round(w*dpr);canvas.height=Math.round(h*dpr);}
 ctx.setTransform(dpr,0,0,dpr,0,0);ctx.clearRect(0,0,w,h);
 ctx.strokeStyle='#dbe2d6';ctx.lineWidth=.6;
 for(let x=20;x<w;x+=24)for(let y=55;y<h-40;y+=24){ctx.beginPath();ctx.moveTo(x-1.5,y);ctx.lineTo(x+1.5,y);ctx.moveTo(x,y-1.5);ctx.lineTo(x,y+1.5);ctx.stroke();}
 const p=parts[state.part],sc=Math.min(w*.34,h*.35)/p.r*state.zoom, cx=w*.5,cy=h*.5+5;
 const ca=Math.cos(state.yaw),sa=Math.sin(state.yaw),ct=Math.cos(state.tilt),st=Math.sin(state.tilt);
 const pts=p.mesh.vertices.map(([x,y,z])=>{const u=x*ca-y*sa,v=x*sa+y*ca;return [u,v*ct-z*st,v*st+z*ct];});
 const grad=ctx.createRadialGradient(cx,cy+h*.2,0,cx,cy+h*.2,p.r*sc*1.15);grad.addColorStop(0,'#1f352124');grad.addColorStop(1,'#1f352100');ctx.fillStyle=grad;ctx.save();ctx.translate(0,cy+h*.2);ctx.scale(1,.26);ctx.translate(0,-(cy+h*.2));ctx.fillRect(0,cy-h,w,h*2);ctx.restore();
 const sorted=p.mesh.faces.map(f=>({f,z:f.reduce((s,i)=>s+pts[i][2],0)/3})).sort((a,b)=>a.z-b.z);
 for(const {f} of sorted){
  const a=pts[f[0]],b=pts[f[1]],c=pts[f[2]],u=b.map((v,i)=>v-a[i]),v=c.map((d,i)=>d-a[i]);
  let n=[u[1]*v[2]-u[2]*v[1],u[2]*v[0]-u[0]*v[2],u[0]*v[1]-u[1]*v[0]];
  const len=Math.hypot(...n)||1;n=n.map(x=>x/len);if(n[2]<0)n=n.map(x=>-x);
  const light=.48+.5*Math.max(0,n[0]*-.25+n[1]*.42+n[2]*.86),rgb=p.color.map(x=>Math.round(clamp(x*light+12,0,255)));
  ctx.fillStyle='rgb('+rgb.join(',')+')';ctx.strokeStyle=ctx.fillStyle;ctx.lineWidth=.5;ctx.beginPath();ctx.moveTo(cx+a[0]*sc,cy-a[1]*sc);ctx.lineTo(cx+b[0]*sc,cy-b[1]*sc);ctx.lineTo(cx+c[0]*sc,cy-c[1]*sc);ctx.closePath();ctx.fill();ctx.stroke();
 }
 // This dimension label is a nominal diameter, not a screen ruler.
 const rw=Math.min(w*.58,210),ry=h-26;
 ctx.strokeStyle='#9aa99a';ctx.lineWidth=1;ctx.beginPath();ctx.moveTo(cx-rw/2,ry);ctx.lineTo(cx+rw/2,ry);ctx.moveTo(cx-rw/2,ry-4);ctx.lineTo(cx-rw/2,ry+4);ctx.moveTo(cx+rw/2,ry-4);ctx.lineTo(cx+rw/2,ry+4);ctx.stroke();
 ctx.fillStyle='#526955';ctx.font='11px "Microsoft YaHei",sans-serif';ctx.textAlign='center';
 ctx.fillText((p.id.includes('PEEK')?'接触环外径 ':'外径 ')+p.specs[0][1]+' mm · 放大示意',cx,ry-10);
}
new ResizeObserver(drawPart).observe(canvas);
let drag=null;
canvas.addEventListener('pointerdown',e=>{drag={x:e.clientX,y:e.clientY};canvas.setPointerCapture(e.pointerId);stopSpin();});
canvas.addEventListener('pointermove',e=>{if(!drag)return;state.yaw+=(e.clientX-drag.x)*.012;state.tilt=clamp(state.tilt+(e.clientY-drag.y)*.01,0,Math.PI);drag={x:e.clientX,y:e.clientY};drawPart();});
canvas.addEventListener('pointerup',()=>drag=null);canvas.addEventListener('pointercancel',()=>drag=null);
canvas.addEventListener('wheel',e=>{e.preventDefault();state.zoom=clamp(state.zoom*Math.exp(-e.deltaY*.001),.65,1.7);drawPart();},{passive:false});
canvas.addEventListener('keydown',e=>{
 if(!['ArrowLeft','ArrowRight','ArrowUp','ArrowDown','+','-','Home'].includes(e.key))return;
 e.preventDefault();stopSpin();
 if(e.key==='ArrowLeft')state.yaw-=.15;if(e.key==='ArrowRight')state.yaw+=.15;
 if(e.key==='ArrowUp')state.tilt=clamp(state.tilt-.15,0,Math.PI);
 if(e.key==='ArrowDown')state.tilt=clamp(state.tilt+.15,0,Math.PI);
 if(e.key==='+')state.zoom=clamp(state.zoom+.1,.65,1.7);if(e.key==='-')state.zoom=clamp(state.zoom-.1,.65,1.7);
 if(e.key==='Home'){state.yaw=.35;state.tilt=.9;state.zoom=1;}drawPart();
});
function stopSpin(){state.spin=false;$('#model-spin').textContent='▷ 自动旋转';$('#model-spin').setAttribute('aria-pressed','false');}
$('#model-spin').onclick=()=>{state.spin=!state.spin;$('#model-spin').textContent=state.spin?'Ⅱ 暂停旋转':'▷ 自动旋转';$('#model-spin').setAttribute('aria-pressed',String(state.spin));scheduleFrame();};
$('#model-topview').onclick=()=>{stopSpin();state.tilt=0;state.yaw=0;drawPart();};
$('#model-sideview').onclick=()=>{stopSpin();state.tilt=1.46;state.yaw=0;drawPart();};
$('#model-reset').onclick=()=>{stopSpin();state.tilt=.9;state.yaw=.35;state.zoom=1;drawPart();};


const lessons = {
 spring:[
  ['编号，先看单片','把两种碟簧分别装袋，给每片和每组编号。先测单片的实际尺寸与压缩曲线，作为后续组合测试的基准。','你可以做','拍清楚袋标签、正反面和编号；请检测方测厚度、自由高、内外径，并记录批次。','保存：样件编号、朝向、实测尺寸与单片原始曲线。'],
  ['反向叠放，装入导向','让相邻两片的锥面朝向相反。动画显示对合串联；每片之间的接触位置在内缘与外缘之间交替。','请检测方完成','用合适的中心导向保持同轴；确认配合间隙、压板平行度和限位。B 型每组 2 片，A 型每组 4 片。','保存：组合编号和侧面照片，避免混片、同向套叠或装反。'],
  ['慢慢压下，同时测力','上压板缓慢移动，使碟簧的拱起变小。力传感器读出压紧力，位移测量给出此时的高度或压缩量。','请检测方完成','先确认厂家的允许行程，再在台架上逐步加载。目录工作点不是最大力，不把动画位置当作压缩限位。','保存：原始力（N）—高度 / 位移（mm）数据；不要只给一个峰值。'],
  ['缓慢卸载，比较重复结果','压板返回，碟簧回弹。加载与卸载不一定沿着同一条曲线；换组、重复后也可能有差别。','你要收回','单片和各组合的加载 / 卸载曲线、重复条件、仪器校准信息、批次与照片。请对方说明组间差异。','用途：用实测曲线决定后续预紧范围，不能凭目录点宣称整个关节合格。']
 ],
 friction:[
  ['认出接触面，确认装夹','塑料试片不转，金属对偶件绕中心转动。固定塑料片的外耳，避免夹具进入接触环形成额外摩擦。','请检测方完成','确认金属牌号、表面工艺、平面度与清洁方法；设计外耳定位座和金属件安装连接。','保存：材料批次、实测尺寸、夹具照片、金属表面信息。'],
  ['先测夹具自身的阻力','先在不让这对试片接触的条件下测量空载阻力。传感器读到的阻力可能包含轴承、密封和夹具的贡献。','请检测方完成','确定能够分离夹具阻力的测试方法；空载条件、补偿方法与原始值都应保留。','保存：空载基线与处理方法，不能把夹具阻力算作材料摩擦力。'],
  ['贴合，在已知力下压紧','沿轴向加载，使两件试片贴合。法向力是传感器的真实读数；先从低载荷开始，再在已确认的范围内增加。','请检测方完成','使用校准测力装置控制与记录真实法向力，不按螺丝转数或碟簧目录值推定。','保存：每次实际法向力（N）与预紧设置编号。不同设置分别记录。'],
  ['缓慢转动，测起动扭矩','保持法向力稳定，让金属件缓慢转动；记录从静止到刚开始运动时的扭矩。塑料片仍固定在定位座中。','请检测方完成','测量并说明低速转动条件。轴向力用 N，转动扭矩用 N·m，两者分别记录。','保存：单面起动扭矩、方向与对应法向力；这里没有第二个摩擦面。'],
  ['加上停留扭矩，观察 60 秒','在规定法向力下施加并记录停留扭矩，观察它是否缓慢滑动。角度变化由测量装置读取，不靠肉眼估计。','请检测方完成','记录实际施加的单面扭矩、实际停留时长和角度变化。60 秒动画已加速，不是正在执行实验。','保存：停留扭矩（N·m）、时长（s）、漂移（°）。暂定 0.3° 筛选线仍待后续确认。'],
  ['两个方向，分别重复','同一预紧设置下，顺时针与逆时针各至少 3 次；再换下一个实测法向力设置，重复同样流程。','你要收回','每条记录的样件编号、方向、设置编号和原始文件。重复测量是初筛，还不能代表长期磨损或寿命。','后续：我们把小样结果与关节载荷一起分析，再决定单关节的材料和预紧。']
 ]
};
const defs = id => '<defs><pattern id="'+id+'grid" width="28" height="28" patternUnits="userSpaceOnUse"><path d="M0 0h2M0 0v2" stroke="#b5c4b5" stroke-width="1"/></pattern><marker id="'+id+'arrow" markerWidth="7" markerHeight="7" refX="5.5" refY="3.5" orient="auto-start-reverse"><path d="M0 0L7 3.5L0 7Z" fill="#bf592d"/></marker><marker id="'+id+'torque" markerWidth="7" markerHeight="7" refX="5.5" refY="3.5" orient="auto-start-reverse"><path d="M0 0L7 3.5L0 7Z" fill="#7561a1"/></marker><linearGradient id="'+id+'metal" x2="0" y2="1"><stop stop-color="#d5dfe0"/><stop offset="1" stop-color="#8b9fa3"/></linearGradient></defs><rect width="760" height="460" fill="url(#'+id+'grid)"/>';
const label=(x,y,t,cls='',anchor='start')=>'<text x="'+x+'" y="'+y+'" class="'+cls+'" text-anchor="'+anchor+'">'+t+'</text>';
const line=(x,y,a,b,col='#94a897',dash='')=>'<line x1="'+x+'" y1="'+y+'" x2="'+a+'" y2="'+b+'" stroke="'+col+'" stroke-width="1.3" '+(dash?'stroke-dasharray="'+dash+'"':'')+'/>';
function drawSpring(){
 const s=state.spring,p=s.progress/100,count=s.step===0?1:(s.type==='B8'?2:4);
 const compression=s.step===2?p:(s.step===3?1-p:0);
 const cone=23-14*compression,th=9,H=cone+th,gap=s.step===1?22*(1-p):0,base=337,cx=277,ro=82,ri=43;
 const top=base-count*H-(count-1)*gap,clear=s.step<2?28:0;
 const mobile=innerWidth<=720;$('#spring-svg').setAttribute('viewBox',mobile?'0 0 480 610':'0 0 760 460');
 let svg=defs('s');
 svg+=label(28,35,'A / 压缩力—高度','svg-mini');
 svg+=label(mobile?462:731,35,'演示 · 非仪器读数','svg-mini','end');
 svg+='<rect x="139" y="87" width="12" height="302" rx="4" fill="#c7d2c5"/><rect x="403" y="87" width="12" height="302" rx="4" fill="#c7d2c5"/>';
 svg+='<rect x="125" y="88" width="303" height="15" rx="3" fill="#b8c7b7"/>';
 svg+='<rect x="266" y="145" width="22" height="207" fill="#a1c3c5" opacity=".8"/>';
 svg+=line(cx,117,cx,385,'#6d999e','4 4');
 for(let i=0;i<count;i++){
  const z0=i*(H+gap),flip=i%2===1;
  for(const side of [-1,1]){
   const outerZ=z0+(flip?cone:0),innerZ=z0+(flip?0:cone);
   const pts=[[cx+side*ro,base-outerZ],[cx+side*ri,base-innerZ],[cx+side*ri,base-innerZ-th],[cx+side*ro,base-outerZ-th]];
   svg+='<polygon data-disc="'+i+'" points="'+pts.map(x=>x.join(',')).join(' ')+'" fill="'+(i%2?'#86a7b4':'#b5c5ce')+'" stroke="#57727c" stroke-width="1.3"/>';
  }
 }
 svg+='<rect x="167" y="'+(top-clear-16)+'" width="220" height="16" rx="2" fill="url(#smetal)" stroke="#81969c"/>';
 svg+='<rect x="262" y="103" width="30" height="'+Math.max(0,top-clear-119)+'" fill="#b3bfc3"/>';
 svg+='<rect x="167" y="337" width="220" height="16" rx="2" fill="url(#smetal)" stroke="#81969c"/>';
 svg+='<rect x="226" y="361" width="103" height="27" rx="4" fill="#3e8182"/>'+label(cx,380,'力传感器','svg-mini','middle').replace('class="svg-mini"','style="fill:white;font-size:12px"');
 svg+='<rect x="124" y="399" width="306" height="18" rx="3" fill="#bdcbb8"/>'+line(cx,353,cx,361)+line(cx,388,cx,399);
 svg+=line(445,top,445,base,'#819379')+line(438,top,453,top)+line(438,base,453,base);
 svg+=label(mobile?467:468,(base+top)/2+5,'高度','svg-mini',mobile?'end':'start');
 if(s.step>=2){
  const ay=Math.max(118,top-76);
  svg+='<path d="M352 '+(s.step===3?top-26:ay)+'V'+(s.step===3?ay:top-26)+'" stroke="#bf592d" stroke-width="3" marker-end="url(#sarrow)"/>';
  svg+=label(350,ay-12,s.step===3?'逐步卸载':'逐步加载','orange-text','middle');
 }else if(!mobile)svg+=label(498,120,count===1?'先测单片':'组合：相邻片朝向相反','svg-bold');
 if(mobile){
  svg+='<rect x="30" y="440" width="420" height="105" rx="8" fill="#fcfdf8" stroke="#cdd8c7"/>';
  svg+=label(48,466,'仪器应记录','svg-mini')+label(48,499,'压缩力  —— N','svg-bold')+label(238,499,'高度  —— mm','svg-bold')+label(48,528,'数值留空，等待实测','svg-mini');
 }else{
  svg+='<rect x="510" y="177" width="213" height="123" rx="8" fill="#fcfdf8" stroke="#cdd8c7"/>';
  svg+=label(528,204,'仪器应记录','svg-mini')+label(528,239,'压缩力  —— N','svg-bold')+label(528,271,'高度 / 位移  —— mm','svg-bold');
  svg+=label(518,325,'数值留空，等待实测','svg-mini');
 }
 svg+=line(69,287,191,287)+label(39,270,count===1?'单片碟簧':'反向叠放','svg-mini');
 svg+=line(147,148,266,165)+label(39,140,'中心导向','svg-mini');
 if(s.step===0){const jaw=cx+ro+36*(1-p);svg+=line(cx-ro,225,jaw,225,'#bb592e')+line(cx-ro,220,cx-ro,232,'#bb592e')+line(jaw,220,jaw,232,'#bb592e');svg+=label(cx,210,'外径标注示意','svg-mini','middle');}
 svg+=label(28,mobile?587:443,s.type+' · '+(s.step===0?'先测单片':count+' 片对合串联')+' / 不按动画行程加载','svg-mini');
 $('#spring-svg').innerHTML=svg;
 $('#spring-stack-note').textContent=s.type==='B8'?'B8 单片目录工作点 118 N。两片串联仍是约 118 N；LP6 的三组理想并联才是 354 N。这些都是目录 / 理想参考，不是实测值，也不是最大力。':'A8 单片目录工作点 210 N。四片串联仍是约 210 N，行程相加；四片不等于四倍力。实际曲线和允许行程需要厂家与检测方确认。';
}
function topRing(cx,cy,ro,ri,fill,id,angle=0,holes=false,ears=false){
 let out='<g transform="rotate('+angle+' '+cx+' '+cy+')">';
 if(ears)for(let i=0;i<3;i++){const a=i*120;out+='<rect x="'+(cx+ro-2)+'" y="'+(cy-6)+'" width="14" height="12" fill="'+fill+'" stroke="#8e805e" transform="rotate('+a+' '+cx+' '+cy+')"/>';}
 out+='<path d="M'+(cx-ro)+' '+cy+'a'+ro+' '+ro+' 0 1 0 '+(2*ro)+' 0a'+ro+' '+ro+' 0 1 0 '+(-2*ro)+' 0M'+(cx-ri)+' '+cy+'a'+ri+' '+ri+' 0 1 1 '+(2*ri)+' 0a'+ri+' '+ri+' 0 1 1 '+(-2*ri)+' 0" fill="'+fill+'" fill-rule="evenodd" stroke="#8b9ca0" stroke-width="1.2"/>';
 if(holes)for(let i=0;i<4;i++){const a=(45+i*90)*Math.PI/180;out+='<circle cx="'+(cx+(ro-13)*Math.cos(a))+'" cy="'+(cy+(ro-13)*Math.sin(a))+'" r="6" fill="#edf2e9" stroke="#7b959a"/>';}
 out+='<circle cx="'+cx+'" cy="'+(cy-ro+23)+'" r="5" fill="#bb572f"/>';
 return out+'</g>';
}
function drawFriction(){
 const s=state.friction,p=s.progress/100,sm=s.type==='M4';
 const angle=(s.step===1?110*p:s.step===3?65*p:s.step===5?(p<.5?p*110:(1-p)*110):0);
 const topCx=183,topCy=238,ro=sm?68:91,ri=sm?24:39;
 const mobile=innerWidth<=720;$('#friction-svg').setAttribute('viewBox',mobile?'0 0 480 810':'0 0 760 460');
 let svg=defs('f');
 svg+=label(28,35,'B / 单面摩擦','svg-mini')+label(mobile?462:731,35,'演示 · 非实测','svg-mini','end');
 svg+='<g transform="'+(mobile?'translate(57 -30)':'')+'">';
 svg+=label(topCx,83,s.step===1?'空载基线（测试面脱开）':'俯视：金属件转，塑料片固定','svg-mini','middle');
 if(s.step!==1){
  svg+=topRing(topCx,topCy,ro,ri,'#d9be84','peek',0,false,true);
  // The stationary witness line remains outside the rotating metal outline.
  svg+=line(topCx-ro-32,topCy,topCx-ro-14,topCy,'#438985');
 }
 svg+=topRing(topCx,topCy,ro+12,sm?13:19,'url(#fmetal)','metal',angle,true,false);
 svg+=line(topCx,topCy-ro-45,topCx,topCy-ro-25,'#9ba896');
 svg+=label(topCx,topCy+ro+52,'橙色圆点标记转动位置','svg-mini','middle');
 if([1,3,4,5].includes(s.step)){
  const reverse=s.step===5&&p>.5;
  svg+='<path d="M'+(topCx-ro-32)+' '+(topCy-32)+' A'+(ro+36)+' '+(ro+36)+' 0 0 1 '+(topCx+ro+24)+' '+(topCy-42)+'" stroke="#7561a1" stroke-width="3" fill="none" marker-'+(reverse?'start':'end')+'="url(#ftorque)"/>';
  svg+=label(topCx,118,s.step===4?'施加并保持停留扭矩':reverse?'逆时针 ↶':'顺时针 ↷','purple-text','middle');
 }
 svg+='</g><g transform="'+(mobile?'translate(-310 340)':'')+'">';
 // Schematic section, intentionally enlarged thickness for legibility.
 const cx=546,base=303,sep=s.step<2?43:s.step===2?43*(1-p):0,metalY=base-13-sep;
 const half=sm?66:83,hole=sm?12:16,contactHole=sm?23:36;
 svg+=label(cx,83,'侧剖面：轴向压紧','svg-mini','middle');
 svg+='<rect x="432" y="327" width="230" height="35" rx="5" fill="#75a4a1" stroke="#4e8b84"/>';
 svg+=label(cx,350,'固定座 / 反力支承','svg-mini','middle').replace('class="svg-mini"','style="fill:white;font-size:12px"');
 if(s.step!==1){
  for(const side of [-1,1]){
   const x=side===-1?cx-half+9:cx+contactHole;
   svg+='<rect x="'+x+'" y="'+base+'" width="'+(half-9-contactHole)+'" height="12" fill="#d9be84" stroke="#9b895e"/>';
  }
  svg+='<rect x="'+(cx-half-4)+'" y="309" width="17" height="18" fill="#adbb9a"/><rect x="'+(cx+half-13)+'" y="309" width="17" height="18" fill="#adbb9a"/>';
  svg+=line(cx-half+10,base+12,cx-half+10,327)+line(cx+half-10,base+12,cx+half-10,327);
 }
 for(const side of [-1,1]){
  const x=side===-1?cx-half:cx+hole;
  svg+='<rect x="'+x+'" y="'+metalY+'" width="'+(half-hole)+'" height="13" fill="url(#fmetal)" stroke="#829ba2"/>';
 }
 svg+='<path d="M'+(cx-half+24)+' '+metalY+'v-36h'+(2*half-48)+'v36" fill="none" stroke="#91a6aa" stroke-width="10"/>';
 svg+='<rect x="'+(cx-12)+'" y="'+(metalY-61)+'" width="24" height="25" fill="#91a6aa"/>';
 if(s.step>=2){
  svg+='<path d="M'+cx+' 123V'+(metalY-73)+'" fill="none" stroke="#bf592d" stroke-width="3" marker-end="url(#farrow)"/>';
  svg+=label(cx+18,151,'压紧力 N','orange-text');
 }
 svg+=line(417,metalY+4,cx-half-3,metalY+4)+label(407,metalY+9,'金属','svg-mini','end');
 if(s.step!==1){svg+=line(691,309,cx+half+3,309)+label(697,314,'PEEK','svg-mini');}
 svg+=label(cx,390,'接触面：塑料上表面 × 金属下表面','svg-mini','middle');
 svg+='</g>';
 let bottom=s.step===4?'60 秒停留 · 加速演示 '+Math.round(p*60)+' / 60 s':s.step===5?'顺时针至少 3 次 + 逆时针至少 3 次':'扭矩 / 角度读数留空，等待仪器记录';
 svg+='<rect x="28" y="'+(mobile?760:412)+'" width="'+(mobile?424:704)+'" height="30" rx="5" fill="#e2e9dc"/>'+label(mobile?240:380,mobile?781:433,bottom,'svg-mini','middle');
 $('#friction-svg').innerHTML=svg;
}
function drawLesson(id){id==='spring'?drawSpring():drawFriction();$('#'+id+'-progress').value=state[id].progress;$('#'+id+'-percent').textContent=Math.round(state[id].progress)+'%';}
function updatePlay(id){$('#'+id+'-play').textContent=state[id].playing?'Ⅱ 暂停动画':'▶ 播放本步';$('#'+id+'-play').setAttribute('aria-label',(state[id].playing?'暂停':'播放')+(id==='spring'?'碟簧':'摩擦')+'测试动画');}
function changeStep(id,step){
 const s=state[id];s.step=clamp(step,0,lessons[id].length-1);s.progress=0;s.playing=false;updatePlay(id);
 const l=lessons[id][s.step];$('#'+id+'-instruction').innerHTML='<span class="step-eyebrow">STEP '+String(s.step+1).padStart(2,'0')+' / '+String(lessons[id].length).padStart(2,'0')+'</span><h2>'+l[0]+'</h2><p>'+l[1]+'</p><div class="do-block"><span class="do-label">'+l[2]+'</span>'+l[3]+'</div><div class="record">'+l[4]+'</div>';
 $$('#'+id+'-steps button').forEach((b,i)=>{if(i===s.step)b.setAttribute('aria-current','step');else b.removeAttribute('aria-current');});
 $('#'+id+'-prev').disabled=s.step===0;
 $('#'+id+'-next').textContent=s.step===lessons[id].length-1?(id==='spring'?'去看摩擦测试 →':'去准备送检 →'):'下一步 →';
 drawLesson(id);
}
for(const id of ['spring','friction']){
 $('#'+id+'-steps').innerHTML=lessons[id].map((l,i)=>'<li><button data-step="'+i+'" aria-label="第 '+(i+1)+' 步：'+l[0]+'" title="'+l[0]+'">'+String(i+1).padStart(2,'0')+'</button></li>').join('');
 $$('#'+id+'-steps button').forEach(b=>b.onclick=()=>changeStep(id,Number(b.dataset.step)));
 $('#'+id+'-prev').onclick=()=>changeStep(id,state[id].step-1);
 $('#'+id+'-next').onclick=()=>{if(state[id].step===lessons[id].length-1)location.hash=id==='spring'?'friction':'prepare';else changeStep(id,state[id].step+1);};
 $('#'+id+'-play').onclick=()=>{const s=state[id];if(s.progress>=100)s.progress=0;s.playing=!s.playing;updatePlay(id);scheduleFrame();};
 $('#'+id+'-progress').addEventListener('input',e=>{state[id].progress=Number(e.target.value);state[id].playing=false;updatePlay(id);drawLesson(id);});
 $$('[data-'+id+']').forEach(b=>b.onclick=()=>{state[id].type=b.dataset[id];$$('[data-'+id+']').forEach(q=>q.setAttribute('aria-pressed',String(q===b)));changeStep(id,state[id].step);});
}


const shopping=[
 ['B 系列碟簧 · 8 × 4.2 × 0.3 mm','标准采购 / 锐尔立；自由高 0.55 mm；两片对合为一组','至少 6 片'],
 ['A 系列碟簧 · 8 × 4.2 × 0.4 mm','标准采购 / 锐尔立；自由高 0.60 mm；四片对合为一组','至少 12 片'],
 ['LP6 未填充 PEEK 试片','按图加工 / 接触区 ID12、OD28、厚 0.6 mm；带 3 外耳','至少 3 片'],
 ['M4 未填充 PEEK 试片','按图加工 / 接触区 ID5.2、OD14.8、厚 0.4 mm；带 3 外耳','至少 3 片'],
 ['LP6 金属对偶件','按图加工 / OD34、中心孔 6.1、厚 3 mm；4 安装孔','至少 1 件'],
 ['M4 金属对偶件','按图加工 / OD20、中心孔 3.1、厚 3 mm；4 安装孔','至少 1 件']
];
const briefs={
 spring:'您好，我在做小型可摆姿关节的材料验证，想先询价两种碟形弹簧小样：\n\n1. B 系列：外径 8、内径 4.2、厚 0.3、自由高 0.55 mm，至少 6 片，计划组成 3 组两片对合串联。\n2. A 系列：外径 8、内径 4.2、厚 0.4、自由高 0.60 mm，至少 12 片，计划组成 3 组四片对合串联。\n\n请确认材料与批次、尺寸与负荷公差、允许工作行程、单片及组合的加载/卸载实测曲线、检测条件、价格和最小采购量。B8/A8 只是我们的尺寸简称，请按完整系列与尺寸核对型号。\n\n是否能代测这些组合的力—高度曲线？请提供所用仪器的量程、分辨率、校准信息、重复条件及原始记录。目录的 118 / 210 N 仅为工作点参考，不作为已测曲线或最大允许载荷。请先报价和确认能力。',
 shop:'您好，我需要先加工少量摩擦试片，附送检包中有 4 个 STEP 和尺寸表：\n\n1. LP6 未填充 PEEK：接触环 ID12 / OD28 / 厚 0.6 mm，3 外耳，至少 3 片。\n2. M4 未填充 PEEK：接触环 ID5.2 / OD14.8 / 厚 0.4 mm，3 外耳，至少 3 片。\n3. LP6 金属对偶件：OD34 / ID6.1 / 厚 3 mm，4×Ø2.2 安装孔，至少 1 件。\n4. M4 金属对偶件：OD20 / ID3.1 / 厚 3 mm，4×Ø1.7 安装孔，至少 1 件。\n\n外耳用于试验夹具固定，不计入塑料接触环直径。请核对 STEP 孔位与尺寸表。\n\n请先与检测方确认装夹、实际材料牌号、表面工艺、平面度及尺寸公差后报价，再决定加工。PEEK 要可追溯的未填充牌号；金属牌号尚待确认，不能仅按 CAD 的 steel 分类采购。请提供原料批次、表面信息与完工尺寸记录。这是研究小样，不是整个人偶或整关节的生产订单。',
 lab:'您好，我想委托两项小样测试，请先确认能力、夹具方案、样件数量与报价：\n\nA. 碟簧力—高度曲线：8×4.2×0.3 mm B 系列（单片和两片对合）；8×4.2×0.4 mm A 系列（单片和四片对合）。每种组合至少 3 组。记录加载/卸载、重复与组间差异。工作行程须按实际锥高与厂家允许范围确认。\n\nB. 单面摩擦：固定未填充 PEEK 的外耳，让金属对偶件缓慢转动。两种接触环为 ID12/OD28 和 ID5.2/OD14.8 mm。夹具图尚未提供，请确认外耳固定、法向加载、测矩及角度测量方案。先测空载阻力并说明处理方法。\n\n在数个实测法向力设置下，从低载荷开始，每个方向至少重复 3 次。记录实际法向力 N、单面起动扭矩 N·m、60 s 加载停留时的实际施加扭矩、时长、角度漂移和温度。不能用目录弹簧力替代实测值。\n\n供量程评估的参考：LP6 三组理想并联目录力 354 N、双面保持预算约 0.463 N·m；M4 目录力 210 N、双面预算约 0.304 N·m。不是要求直接按这些力试验，也不是单面实测目标。具体载荷及测量不确定度需共同确认。\n\n请列明仪器量程、分辨率、校准编号、夹具方案、金属牌号/表面、材料批次与准备方法，并交付原始曲线和日志。附件有 STEP、尺寸表、任务书和空白数据模板。当前只做材料/弹簧初筛，不做整机关节合格判定。'
};
const storageKey='posedoll-first-bench-prep-v1';
let saved={};
try{const x=JSON.parse(localStorage.getItem(storageKey)||'{}');if(x&&typeof x==='object'&&!Array.isArray(x))saved=x;}catch{}
$('#shopping-list').innerHTML=shopping.map((r,i)=>'<div class="shopping-item"><input type="checkbox" id="shop-'+i+'" '+(saved[i]===true?'checked':'')+'><label for="shop-'+i+'"><strong>'+r[0]+'</strong><small>'+r[1]+'</small></label><span>'+r[2]+'</span></div>').join('');
$$('.shopping-item input').forEach((el,i)=>el.onchange=()=>{
 saved[i]=el.checked;
 try{localStorage.setItem(storageKey,JSON.stringify(saved));}catch{$('#storage-status').textContent='浏览器未允许保存；本次勾选仅在当前页面有效。';}
});
const shoppingText='PoseDoll 第一轮小样清单（先确认夹具与检测能力，再采购）\n\n'+shopping.map((r,i)=>(i+1)+'. '+r[0]+'；'+r[2]+'\n   '+r[1]).join('\n')+'\n\n加工前确认：未填充 PEEK 牌号与批次、金属牌号、表面、平面度、公差及装夹方式。\n检测方提供：校准压缩测力装置、导向与限位、位移测量、单面摩擦测矩夹具和角度测量。\n先准备分装盒、标签和拍照工具；不先购买整套测试仪器、不订购整个人偶或整关节。\n碟簧厂家目录：https://www.raleigh-spring.cn/discspring/\n价格与库存未确认，数量在询价时确认。';
$('#brief-text').value=briefs.spring;
const editedBriefs={...briefs};let currentRole='spring';
$('#brief-role').onchange=e=>{editedBriefs[currentRole]=$('#brief-text').value;currentRole=e.target.value;$('#brief-text').value=editedBriefs[currentRole];};
$('#copy-shopping').onclick=()=>copy(shoppingText);
$('#copy-brief').onclick=()=>copy($('#brief-text').value);
$('#print-list').onclick=()=>window.print();
$('#screen-values').innerHTML='<table><thead><tr><th>尺寸</th><th>双面保持预算</th><th>目录力参考</th></tr></thead><tbody>'+ASSETS.plan.families.map(f=>'<tr><td>'+f.family+'</td><td>'+f.hold_screen_Nm.toFixed(3)+' N·m</td><td>'+f.catalog_nominal_force_N+' N</td></tr>').join('')+'</tbody></table>';
let frameId=0,lastTick=0;
function scheduleFrame(){if(!frameId&&!document.hidden)frameId=requestAnimationFrame(tick);}
function tick(now){
 frameId=0;const dt=lastTick?Math.min(now-lastTick,80):0;lastTick=now;
 if(document.hidden)return;
 if(state.view==='parts'&&state.spin){state.yaw+=dt*.00028;drawPart();}
 if(['spring','friction'].includes(state.view)){
  const id=state.view,s=state[id];
  if(s.playing){s.progress=Math.min(100,s.progress+dt/70);if(s.progress===100){s.playing=false;updatePlay(id);}drawLesson(id);}
 }
 if((state.view==='parts'&&state.spin)||(['spring','friction'].includes(state.view)&&state[state.view].playing))scheduleFrame();else lastTick=0;
}
function pauseAll(){stopSpin();for(const id of ['spring','friction']){state[id].playing=false;updatePlay(id);}lastTick=0;}
document.addEventListener('visibilitychange',()=>{if(document.hidden)pauseAll();});
reduced.addEventListener('change',()=>{if(reduced.matches)pauseAll();});
function navigate(initial=false){
 const wanted=location.hash.slice(1),next=['parts','spring','friction','prepare','results'].includes(wanted)?wanted:'parts';
 pauseAll();clearTimeout(toastTimer);$('#toast').hidden=true;state.view=next;
 $$('.view').forEach(el=>el.hidden=el.id!==next);
 $$('[data-nav]').forEach(a=>{if(a.dataset.nav===next)a.setAttribute('aria-current','page');else a.removeAttribute('aria-current');});
 if(next==='parts')requestAnimationFrame(drawPart);if(['spring','friction'].includes(next))drawLesson(next);
 if(!initial){window.scrollTo({top:0,behavior:'instant'});$('#main').focus({preventScroll:true});}
}
window.addEventListener('hashchange',()=>navigate());
window.addEventListener('resize',()=>{if(['spring','friction'].includes(state.view))drawLesson(state.view);});
partSelect(0);changeStep('spring',0);changeStep('friction',0);navigate(true);
window.BENCH_GUIDE_READY=true;
})();

