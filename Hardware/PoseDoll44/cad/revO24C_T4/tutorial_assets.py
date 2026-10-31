"""Adapt the established offline tutorial UI without modifying the T1 baseline."""
from arm_kit import *
import shutil

def main():
 old=H/'cad/revO24C_T1'
 js=(old/'tutorial.js').read_text('utf8')
 def change(a,b):
  nonlocal js
  assert a in js,a;js=js.replace(a,b)
 change("const s=step(),map={...s.before};for(const [id,path]", "const s=step();if(s.kind==='remove'&&S.t>=1)return{...s.after};const map={...s.before};for(const [id,path]")
 change("[[0],[-45],[165],[0]]","[[0],[145],[0]]")
 change("if(p.frame==='rotor')r=rot([0,1,0],S.station==='H'?-q:q);if(p.frame==='ball')r=mul(rot([1,0,0],d),rot([0,1,0],q))", "if(p.frame==='rotor')r=rot(S.station==='H'?[0,1,0]:[0,0,1],-q);if(p.frame==='flex')r=rot([0,1,0],q);if(p.frame==='hand')r=mul(rot([0,1,0],q),rot([1,0,0],d))")
 change("o?.kind==='nylon'?1:o?.kind==='washer'?2:0", "o?.kind==='spring'?3:o?.kind==='washer'?2:0")
 change("active?[.95,.58,.18]:p.printable?[.43,.64,.57]:[.55,.62,.65]", "o?.kind==='spring'?[.18,.46,.82]:active?[.95,.58,.18]:p.printable?(p.bench_only?[.60,.62,.67]:[.32,.65,.60]):[.65,.69,.74]")
 change("o.kind==='nylon'?'蓝色尼龙圈端':o.kind==='washer'?'绿色光滑面':'普通螺母 · 无尼龙圈'", "o.kind==='spring'?'A8 内孔凸边':o.kind==='washer'?'绿色光滑面':'普通螺母承压面'")
 change("D.parts.filter(p=>p.station===S.station)", "D.parts.filter(p=>p.station===S.station&&p.id!=='F3-W'&&!p.id.startsWith('FW_'))")
 change("`已加入 ${installed} / ${T.lessons[S.station].total_parts} 件 · 含全部五金`", "`当前装配中 ${installed} 件 · 教程涉及 ${T.lessons[S.station].total_parts} 件`")
 change("s.kind==='move'?'移动已装好的零件 / 组件，本步不新增零件。'", "s.kind==='remove'?'拆下并保存；动画末尾移出工作区，不再显示。':s.kind==='reinstall'?'装回刚才拆下的同一件，不是新增五金。':s.kind==='move'?'移动已装好的零件 / 组件，本步不新增零件。'")
 change("setMini(s.kind==='add'?[id]:[])", "setMini(['add','remove','reinstall'].includes(s.kind)?[id]:[])")
 change("fit(step().kind==='add')", "fit(['add','reinstall'].includes(step().kind))")
 change("'posedoll-assembly-S3'", "'posedoll-assembly-T4'")
 change("H:'H · 肩 / 肘单轴',R:'R · 前臂扭转',W:'W · 球面腕'", "H:'H · 肘屈伸',R:'R · 前臂旋转',W:'W · 双轴腕'")
 change("T.revision+' · 五金朝向版'", "T.revision+' · 逐件装配版'")
 change("currentMatrices:Object.fromEntries", "shownMatrices:Object.fromEntries(Object.entries(offsets()).map(([id,off])=>[id,model(id,off)])),currentMatrices:Object.fromEntries")
 # Keep the initial incoming deep link intact until it has been read.
 change("try{localStorage.setItem", "try{if(ready&&window.__tutorialStarted)history.replaceState(null,'','#'+S.station+'-'+(S.index+1));localStorage.setItem")
 change("requestAnimationFrame(tick)}catch", "window.__tutorialStarted=true;requestAnimationFrame(tick)}catch")
 change("window.inspectTutorial=()=>", "window.addEventListener('hashchange',()=>{const h=location.hash.slice(1).split('-');if(['H','R','W'].includes(h[0])){station(h[0]);if(h[1])go(Number(h[1])-1)}});\nwindow.inspectTutorial=()=>")
 (HERE/'tutorial.js').write_text(js,encoding='utf8')
 markup=(old/'tutorial.html').read_text('utf8')
 markup=markup.replace('O24C-T1','O24C-T4').replace('../preview/data.js','../viewer/data.js').replace('肩 / 肘单轴','肘屈伸').replace('前臂扭转','前臂旋转').replace('球面腕','双轴腕')
 markup=markup.replace('<a href="../REPRINT_S3.html">S3 两件更新</a>','<a href="../PURCHASE_FROM_OWNED.html">已购五金补齐表</a><a href="../printing/ALL_H_R_W_T4.3mf">三样件一盘打印</a>')
 start=markup.index('<div class="revision-note">');end=markup.index('<main>',start)
 markup=markup[:start]+'''<div class="revision-note">当前整套为 <strong>T3 的 H / R + T4 双轴腕</strong>。每片垫圈、每颗螺母各一步；可暂停、拖动、放大并翻看朝向。本次教程与合盘没有修改打印件，无需因此重印。<a href="../TUTORIAL.html">全部步骤索引 →</a></div>
<details class="hardware-primer"><summary>开始前：普通螺母、平垫与反向 A8 碟簧</summary><div class="primer-grid">
<div><b>全部普通螺母 · N2 / N3</b><p>两端都是金属螺纹，<strong>没有塑料圈</strong>。本 T4 套件不使用尼龙锁紧螺母。大部分螺母先放进止转槽；W 测力杆外露螺母需要小扳手扶住。</p></div>
<div><b>蓝色 A8 · 两片相反</b><p>第一片内孔凸边朝螺钉头，第二片翻面、凸边朝关节。<strong>两个内孔凸边相对</strong>，不是同向套叠。动画的蓝色仅便于识别，实物通常为金属色。</p></div>
<div><b>绿色平垫面 · 光滑面</b><p>一般光滑面贴打印件；两片大摩擦垫的光滑面相向，中间夹转动耳。头下孔 4.3 mm 垫圈两侧均贴金属，无强制正反。所有平垫先去毛刺。</p></div>
</div><p class="primer-note">螺钉要旋入金属螺纹，动画仅简化显示进入方向。金属螺纹一开始就卡住时，退出并检查对中，不靠加力硬拧。碟簧预紧从轻接触开始，不能压平。</p></details>
''' +markup[end:]
 markup=markup.replace('蓝色＝尼龙圈','蓝色＝A8 碟簧')
 markup=markup.replace('本步零件 / 组件 <span','本步（碟簧用蓝色） <span')
 start=markup.index('<footer>');end=markup.index('<script',start)
 markup=markup[:start]+'''<footer><p>动画使用现有制造网格；蓝色碟簧和绿色光滑面是辨认标记。螺纹旋入与实际弹簧压缩为简化示意，不能用动画中的圈数或高度设定预紧力。尺寸单位 mm。</p><p>名义装入路径经过抽样干涉检查；手部空间、工具操作力、持姿、磨损与材料变形仍需实测。<a href="../TEST_PLAN.html">测试计划</a> · <a href="../TUTORIAL.html">步骤索引 / 离线说明</a></p></footer>
''' +markup[end:]
 (HERE/'tutorial.html').write_text(markup,encoding='utf8');shutil.copyfile(old/'tutorial.css',HERE/'tutorial.css')
 guide=(old/'orientation.js').read_text('utf8').replace('featureKind>1.5 &&','featureKind>1.5 && featureKind<2.5 &&').replace('float light=.55', 'if(featureKind>2.5){paint=vec3(.18,.46,.82);if(radius<featureBore+.3&&fromFace>-.08)paint=vec3(.35,.78,1.);}\n   float light=.55')
 guide=guide.replace("color:o=>o.kind==='nylon'?'#245fd2'", "color:o=>o.kind==='spring'?'#245fd2':o.kind==='nylon'?'#245fd2'")
 marker="   const start='<svg"
 spring='''   if(o.kind==='spring')return '<svg viewBox="0 0 320 125" role="img" aria-label="两片 A8 碟簧反向串联剖面示意"><rect x="10" y="25" width="35" height="67" fill="#d0e1d4"/><rect x="270" y="25" width="35" height="67" fill="#c1cbd0"/><path d="M85 25 L145 48 M85 92 L145 68 M235 25 L175 48 M235 92 L175 68" stroke="#245fd2" stroke-width="7" fill="none"/><path d="M50 58 H262" stroke="#aab6be" stroke-dasharray="3 3"/><text x="27" y="16" text-anchor="middle">关节侧</text><text x="284" y="16" text-anchor="middle">头侧</text><text x="93" y="114" text-anchor="middle">第 1 片 →</text><text x="230" y="114" text-anchor="middle">← 第 2 片</text><text x="160" y="14" text-anchor="middle">内孔凸边相对</text></svg>';
'''
 assert marker in guide;guide=guide.replace(marker,spring+marker)
 (HERE/'orientation.js').write_text(guide,encoding='utf8')
 print('Tutorial UI assets prepared')

if __name__=='__main__':main()
