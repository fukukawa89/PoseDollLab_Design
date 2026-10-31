"""Extend the established local arm viewer without editing either baseline."""
from compact_arm import *

s=(H/'cad/revO24/viewer.js').read_text('utf8')
def change(old,new):
    global s
    assert old in s,old[:80]
    s=s.replace(old,new)
change("f.hand=mul(f.wrist_flex,rot([1,0,0],a('wrist_deviation')));return f}","f.wrist_guide=mul(f.wrist_base,rot([1,0,0],a('wrist_deviation')));f.hand_ball=mul(f.wrist_guide,rot([0,1,0],a('wrist_flex')));f.hand=f.hand_ball;return f}")
change('let pts=[];for(let p of D.parts){','let pts=[];for(let p of [...D.revisions.O24B,...D.revisions.O24C].filter(selected)){')
change("for(let item of D.parts){if(!$('#hardware')", "for(let item of D.parts.filter(selected)){if(!$('#hardware')")
change("let audit=D.audit[state.pose],status=$('#status');", "let audit=$('#revision').value==='O24C'?D.audit[state.pose]:null,status=$('#status');")
change("'手动组合：已更新几何；此组合未做实体干涉验证。'", "($('#revision').value==='O24B'?'O24B 对比模型 · 此页未验证该动作组合。':'手动组合：已更新几何；此组合未做实体干涉验证。')")
change("pose:state.pose,parts:D.parts.length", "pose:state.pose,revision:$('#revision').value,focus:$('#focus').value,frames:F,parts:D.parts.length")
change("function fit(){F=fk();", "function fit(){F=fk();updateDimensions();")
s += '''
function selected(part){
 const focus=$('#focus').value,n=part.name;
 return focus==='all'||(focus==='shoulder'&&(/^(shoulder_|humeral_)/.test(n)))||
 (focus==='elbow'&&n.startsWith('elbow_'))||(focus==='wrist'&&/^[BC]_/.test(n));
}
function updateDimensions(){
 const group=$('#focus').value,comp=D.comparison.revisions;
 if(group==='all'){$('#dimension-readout').textContent='同一骨长 · 同一动作 · 切换 B / C 时保持相同比例';return}
 const b=comp.O24B[group],cc=comp.O24C[group],fmt=x=>x.map(v=>v.toFixed(1)).join(' × ');
 const drop=(1-cc.box_volume_mm3/b.box_volume_mm3)*100;
 $('#dimension-readout').textContent=`B ${fmt(b.size_mm)} → C ${fmt(cc.size_mm)} mm · 中立包围盒体积 −${drop.toFixed(1)}%`;
}
$('#revision').onchange=e=>{D.parts=D.revisions[e.target.value];draw()};
$('#focus').onchange=()=>{$('#body').checked=false;fit()};
'''
(HERE/'viewer.js').write_text(s,encoding='utf8')
css=(H/'cad/revO24/style.css').read_text('utf8')
css+='\n#dimension-readout{position:absolute;left:30px;right:24px;bottom:55px;font-size:12px;color:#3d6256;pointer-events:none}#scale-label{bottom:78px}.comparison{padding:12px;border-radius:6px;background:#e5ede2;font-size:11px;line-height:1.9}.comparison b{font-weight:600}.control-pair{display:grid;grid-template-columns:1fr 1fr;gap:12px}.intro{margin-bottom:12px}h1{font-size:27px}.stats{padding:13px 0}.stats strong{font-size:25px}\n'
(HERE/'style.css').write_text(css,encoding='utf8')
print('Extended B/C viewer generated.')
