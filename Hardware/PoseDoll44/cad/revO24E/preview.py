from build import *
import base64,re

def main(preview_pending=False):
    dest=OUT/'preview';dest.mkdir(exist_ok=True);data=load(OUT/'production_assembly.json');z=np.load(OUT/'production_meshes.npz');inv=load(OUT/'production_parts.json');by={r['part_number']:r for r in inv['structural_parts']+inv['hardware']};geo=sha(OUT/'assembly_meshes.npz');packed=[];cursor=0
    for p in data['parts']:
        i=str(p['i']);v=z[i+'v'];f=z[i+'f'];m=trimesh.Trimesh(v,f,process=False);ar=np.concatenate([v[f],np.repeat(m.face_normals[:,None,:],3,axis=1)],axis=2).reshape(-1,6).astype('<f4')
        p.update(first=cursor,count=len(ar),color=COLORS.get(p['role'],[.6,.6,.6]),source_features=by[p['name']].get('source_features',[by[p['name']].get('feature','')]))
        if p['name'].startswith('E-M'):p['color']=COLORS['metal']
        cursor+=len(ar);packed.append(ar)
    motion=load(OUT/'verification/motion_named_endpoints.json');paths=load(OUT/'verification/motion_task_paths.json');rom=load(OUT/'verification/rom_examination_dense.json')
    pending=[]
    for name,r in [('motion',motion),('paths',paths),('ROM',rom)]:
        if r['geometry_sha256']!=geo:
            assert preview_pending,'Stale '+name
            pending.append(name);r['cases']=[]
    audit={r['pose']:dict(count=r['count'],pairs=r['collisions'],affected=list(dict.fromkeys(pn for h in r['collisions'] for key in ['a','b'] for pn in inv['feature_to_production'].get(h[key],[])))) for r in motion['cases']}
    shown=load(OUT/'profiles/poses.json');contexts={};labels={a['id']:a['label'] for a in PROFILE['axes']}
    for r in rom['cases']:
        if '/step/' in r['case']:continue
        n=r['case'];shown[n]=dict(label=labels[r['axis']]+' '+str(r['value_deg'])+'°',angles=r['angles']);audit[n]=dict(count=r['count'],pairs=r['collisions'],affected=[])
    ue=[dict(id=r['bone'],parent=r['parent'],frame=r['frame'],local_point=(np.linalg.inv(F0[r['frame']])@np.r_[r['neutral_position_mm'],1])[:3].tolist()) for r in load(OUT/'reference/full_UE_N_pose.json')['bones']]
    route=load(OUT/'harness/routes.json');assert route['geometry_sha256']==geo;nodes={n['id']:n for n in route['nodes']};wire=[]
    for r in route['spans']:
        a=nodes[r['start']];b=nodes[r['end']];q=np.array(r['guide_A_mm']);ds=np.r_[0,np.cumsum(np.linalg.norm(np.diff(q,axis=0),axis=1))];ts=ds/max(ds[-1],1e-9)
        points=[dict(a=(np.linalg.inv(FA[a['frame']])@np.r_[p,1])[:3].tolist(),b=(np.linalg.inv(FA[b['frame']])@np.r_[p,1])[:3].tolist(),t=float(t)) for p,t in zip(q,ts)]
        wire.append(dict(id=r['id'],start=r['start'],end=r['end'],start_frame=a['frame'],end_frame=b['frame'],points=points,bank=r['cables'][0][0]))
    payload=dict(profile=PROFILE,parts=data['parts'],poses=shown,contexts=contexts,audit=audit,geometry=base64.b64encode(np.vstack(packed).tobytes()).decode(),height=load(OUT/'verification/envelope.json'),geometry_sha256=geo,ueBones=ue,harness=wire,paths={r['pose']:r for r in paths['cases']},expectedFrames={n:{fr:m.tolist() for fr,m in frames(p['angles']).items()} for n,p in shown.items()},assembly=load(OUT/'tutorial/steps.json')['modules'])
    (dest/'data.js').write_text('window.O24D='+json.dumps(payload,ensure_ascii=False,separators=(',',':'))+';\n',encoding='utf8')
    with (dest/'data.js').open('a',encoding='utf8') as f:f.write('window.O24D.production_mesh_sha256='+json.dumps(sha(OUT/'production_meshes.npz'))+';\n')
    src=H/'cad/revO24D';view=(src/'viewer.js').read_text('utf8')
    start=view.index('function selected(p)');end=view.index('function shader',start)
    view=view[:start]+'''function selected(p){if(state.assemblyVisible)return state.assemblyVisible.has(p.name);let f=$('#focus').value,n=[p.name,p.frame,...p.source_features||[]].join(' ').toLowerCase(),s=$('#search').value.toLowerCase();if(s&&!n.includes(s))return false;return f==='all'||f==='electronics'&&n.includes('electronics')||f==='arms'&&/clavicle|shoulder|humeral|upperarm|elbow|forearm|wrist|palm/.test(n)||f==='torso'&&/lumbar|thorax|thoracic|neck|head|clavicle/.test(n)||f==='pelvis'&&/hip_|pelvi/.test(n)||f==='legs'&&/knee|ankle|shin|toe|heel|thigh/.test(n)||f==='wrist'&&/l_wrist|l_e_w|l_palm/.test(n)}\n'''+view[end:]
    view=view.replace("gl.uniformMatrix4fv(L.model,false,col(F[p.frame]));", "gl.uniformMatrix4fv(L.model,false,col(state.offsets?.[p.name]?mul(trans(state.offsets[p.name]),F[p.frame]):F[p.frame]));")
    view=view.replace("function setPose(n){stopPlayback();", "function setPose(n){stopPlayback();state.assemblyVisible=null;state.offsets={};")
    view=view.replace("$('#focus').onchange=fit", "$('#focus').onchange=()=>{state.assemblyVisible=null;state.offsets={};fit()}")
    view=view.replace("$('#search').oninput=fit", "$('#search').oninput=()=>{state.assemblyVisible=null;state.offsets={};fit()}")
    view=view.replace("revision:'O24D'","revision:'O24E'").replace("'O24D_pose.json'","'O24E_pose.json'").replace('个几何特征','个装配显示实体（PCBA子特征归整件采购）')
    view=view.replace('window.O24D_VIEW_STATE={',"if(state.assemblyVisible){$('#current').textContent='逐件装配';$('#status').textContent='装配方向示意；实体路径验证范围见对应报告。';}window.O24D_VIEW_STATE={")
    (dest/'viewer.js').write_text(view,encoding='utf8');(dest/'style.css').write_bytes((src/'style.css').read_bytes())
    text=(src/'index.html').read_text('utf8').replace('O24D','O24E').replace('几何特征','装配显示实体').replace('S1 通过仍是假设，未作实物或制造放行。','H/W用户接受状态已记录；本改版实配、载荷与百次循环尚未作为实测通过。').replace('左腕 S1 接口','左腕 T6 双轴接口').replace('O24E_full_body.blend','O24E_production_assembly.blend').replace('O24E_full_body.glb','O24E_production_assembly.glb').replace('../REVIEW.html','../START_HERE.html').replace('../electronics/SYSTEM.html','../ELECTRONICS.html').replace('../BOM_candidate.csv','../HARDWARE_REUSE_BUY.csv')
    panel='''<details id="assembly-panel"><summary>逐件装配 / 受控插装动画</summary><label class="field">模块<select id="assembly-module"></select></label><div class="buttons"><button id="assembly-prev">上一步</button><button id="assembly-next">下一步</button><button id="assembly-move">重播装入</button><button id="assembly-exit">回整机</button></div><b id="assembly-title"></b><p id="assembly-parts"></p><p id="assembly-note"></p><small>方向示意动画；实际实体路径验证范围见装配报告。已出现的相同件号仍是同一件。</small></details>'''
    text=text.replace('<div id="sliders"></div>',panel+'<div id="sliders"></div>');text=text.replace('<script src="viewer.js"></script>','<script src="viewer.js"></script><script src="assembly.js"></script>')
    if pending:text=text.replace('<body>','<body><div style="position:fixed;top:0;left:40%;z-index:10;background:#ffe8ad;padding:8px">仅供界面核对：'+','.join(pending)+'验证更新中</div>')
    (dest/'index.html').write_text(text,encoding='utf8');(dest/'assembly.js').write_text(ASSEMBLY_JS,encoding='utf8')
    print('PREVIEW',len(data['parts']),cursor//3,flush=True)

ASSEMBLY_JS=r'''let am=0,ai=0,at=0;const ams=D.assembly;for(let i=0;i<ams.length;i++){let o=document.createElement('option');o.value=i;o.textContent=ams[i].label;$('#assembly-module').appendChild(o)}
function astep(animate=true){cancelAnimationFrame(at);stopPlayback();let m=ams[am],s=m.steps[ai];if(!s)return;state.angles={...D.poses.neutral.angles};state.pose='custom';state.offsets={};state.assemblyVisible=new Set(m.context);state.highlight=s.part_numbers;$('#assembly-title').textContent=(ai+1)+' / '+m.steps.length+' · '+s.title;$('#assembly-parts').textContent=s.part_numbers.join(' · ');$('#assembly-note').textContent=s.note;$('#harness').checked=false;$('#bones').checked=false;fit();state.assemblyVisible=new Set(m.steps.slice(0,ai+1).flatMap(x=>x.part_numbers));draw();if(!animate)return;const start=performance.now();function tick(now){let t=Math.min(1,(now-start)/1400),d=s.animation_travel_mm*(1-t);for(let p of s.part_numbers)state.offsets[p]=s.entry_world_A.map(x=>x*d);draw();$('#status').textContent='装配方向示意 · '+s.part_numbers.join(', ')+' · 此动画不新增实体路径验收结论';if(t<1)at=requestAnimationFrame(tick);else state.offsets={}}at=requestAnimationFrame(tick)}
$('#assembly-module').onchange=e=>{am=+e.target.value;ai=0;astep()};$('#assembly-prev').onclick=()=>{ai=Math.max(0,ai-1);astep()};$('#assembly-next').onclick=()=>{ai=Math.min(ams[am].steps.length-1,ai+1);astep()};$('#assembly-move').onclick=()=>astep();$('#assembly-exit').onclick=()=>{cancelAnimationFrame(at);state.assemblyVisible=null;state.offsets={};$('#harness').checked=true;$('#bones').checked=true;setPose('neutral')};if(location.hash==='#assembly'){$('#assembly-panel').open=true;astep(false)}
$('#assembly-panel').addEventListener('toggle',()=>{if($('#assembly-panel').open&&!state.assemblyVisible)astep(false)});
const originalAssemblyStep=astep;astep=function(animate=true){originalAssemblyStep(animate);$('#pose').value='custom';for(let a of D.profile.axes){document.getElementById('axis-'+a.id).value=state.angles[a.id]||0;document.getElementById('out-'+a.id).textContent=(state.angles[a.id]||0).toFixed(1)+'°'}};
window.O24E_SELF_CHECK=function(){let saved=state.angles,worst=0;for(let n of Object.keys(D.expectedFrames)){state.angles=D.poses[n].angles;let actual=fk();for(let fr of Object.keys(actual)){let expected=D.expectedFrames[n][fr].flat();for(let i=0;i<16;i++)worst=Math.max(worst,Math.abs(actual[fr][i]-expected[i]))}}state.angles=saved;return {geometry_sha256:D.geometry_sha256,production_mesh_sha256:D.production_mesh_sha256,ready:window.O24D_VIEW_STATE.ready,sliders:document.querySelectorAll('input[type=range]').length,pose_count:Object.keys(D.expectedFrames).length,max_matrix_error:worst,assembly_modules:ams.length}};
window.O24E_ASSEMBLY_CHECK=()=>({module:am,step:ai,part_numbers:ams[am].steps[ai].part_numbers,visible:state.assemblyVisible?.size||0});'''
if __name__=='__main__':main()
