from pathlib import Path
import sys,json,numpy as np,gzip,base64,shutil,hashlib
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'scripts'))
from select_revo22_f4_repairs import select,O
D=O/'repair_view'
for sub in ['geometry','records']:(D/sub).mkdir(parents=True,exist_ok=True)
choices=select();rows=[];ready=0;changed=0
for row in choices:
 pid=row['id'];label=row['label'];p=O/'candidates'/pid/label;n=np.load(p/'parts'/f'{pid}.npz');design=json.loads((p/'design'/f'{pid}.json').read_text());old=json.loads((O/'review/records'/f'{pid}.json').read_text());native=json.loads((p/'verification/full_bead_contacts.json').read_text());ref=p/'verification/full_bead_contacts_v2.json'
 if ref.exists() and json.loads(ref.read_text())['project_sha256']==native['project_sha256']:native=json.loads(ref.read_text())
 exact=p/'verification/full_bead_contacts_v4.json'
 if exact.exists() and json.loads(exact.read_text())['project_sha256']==native['project_sha256']:native=json.loads(exact.read_text())
 lateral=p/'verification/full_bead_contacts_v5.json'
 if lateral.exists():
  ld=json.loads(lateral.read_text())
  if ld.get('project_sha256')==native['project_sha256'] and ld.get('audit_schema')=='full-bead-v5-earlier-rooted-wall-104':native=ld
 gp=p/'verification/geometry.json';geometry=json.loads(gp.read_text()) if gp.exists() else {};qualified=row['eligible_before_fin_geometry_check'] and geometry.get('geometric_constraints_passed',False) and geometry.get('npz_sha256')==hashlib.sha256((p/'parts'/f'{pid}.npz').read_bytes()).hexdigest();ready+=qualified;changed+=row['body_changed'];pm=json.loads((p/'verification/plate_manifest.json').read_text());it=pm['items'][0];M=np.array(it['rotation_matrix']);t=np.array(it['translation_mm']);issues=[]
 for kind,qs in [('island',native['external_islands']),('span',native['critical_external_runs'])]:
  for q in qs:
   b=q['bounds_mm'];pts=(np.array([[x,y,q['z_mm']] for x in [b[0],b[2]] for y in [b[1],b[3]]])-t)@M;issue=dict(q,kind=kind,object_name=pid+' '+design['part'],plate_z_mm=q['z_mm'],z_mm=float(pts[:,2].mean()),bounds_mm=[*pts[:,:2].min(0),*pts[:,:2].max(0)],unsupported_footprint_diagonal_mm=float(np.linalg.norm(np.array(b)[2:]-np.array(b)[:2])),anchors_in_previous_layer=q.get('anchors',0));issues.append(issue)
 vv=np.r_[n['v'],n['fin_v'],n['teeth_v']];height=float(vv[:,2].max());assessment={'external_islands':native['external_island_count'],'external_critical_runs':native['critical_external_count'],'geometry_pass':geometry.get('geometric_constraints_passed',False),'body_changed':row['body_changed'],'body_fit':row['fit_passed'],'ready_for_plate_recheck':qualified,'physical_print_tested':False};old['candidate']={'label':label,'geometry':{'height_mm':height},'design':design,'assessment':assessment,'issues':issues,'native_complete':True,'print_release_approved':False,'project':'../candidates/'+pid+'/'+label+'/projects/'+pm['id']+'.3mf'};summary=old['summary'];summary.update(review_required=not qualified,candidate_islands=native['external_island_count'],candidate_spans=native['critical_external_count'],candidate_label=label,candidate_height_mm=height,body_changed=row['body_changed'],disposition='本件检查条件满足，待整盘复核' if qualified else '本件仍有待处理项');rows.append(summary)
 (D/'records'/f'{pid}.json').write_text(json.dumps(old,ensure_ascii=False,indent=2),encoding='utf8');(D/'records'/f'{pid}.js').write_text('window.AUDIT_DETAILS["'+pid+'"]='+json.dumps(old,ensure_ascii=False,separators=(',',':'))+';',encoding='utf8');shutil.copy2(O/'review/geometry'/f'{pid}_baseline.js',D/'geometry'/f'{pid}_baseline.js');meshes={}
 for name,v,f in [('part','v','f'),('fin','fin_v','fin_f'),('teeth','teeth_v','teeth_f')]:
  if len(n[f]):meshes[name]={'v':base64.b64encode(gzip.compress(np.array(n[v],dtype='<f4').tobytes())).decode(),'f':base64.b64encode(gzip.compress(np.array(n[f],dtype='<u4').tobytes())).decode()}
 data={'meshes':meshes,'bounds':np.r_[vv.min(0),vv.max(0)].tolist()};(D/'geometry'/f'{pid}_candidate.js').write_text('window.AUDIT_MESHES["'+pid+'_candidate"]='+json.dumps(data,separators=(',',':'))+';',encoding='utf8')
summary={'rows':rows,'type_count':len(rows),'ready_for_plate_recheck':ready,'source_bodies_changed_in_current_selection':changed,'F4_print_release_approved':False,'physical_print_tested':False};(D/'all_parts.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding='utf8');(D/'audit-data.js').write_text('window.AUDIT='+json.dumps(summary,ensure_ascii=False,separators=(',',':'))+';window.AUDIT_DETAILS={};window.AUDIT_MESHES={};',encoding='utf8')
html=(O/'review/index.html').read_text(encoding='utf8');html=html.replace('O22 全零件支撑检查','O22 支撑修补工作预览').replace('150 类零件，逐层核对承托','支撑修补 · 当前工作网格').replace('原版 F3 与重新定向候选 · 实际网格 / 实际 G-code 定位','蓝色本体 / 橙色支撑鳍 / 黄色连接齿').replace('<a href="all_parts.csv" download>全部零件清单 CSV</a>','<a href="all_parts.json">当前零件清单</a>').replace('<a href="METHOD.txt">检查方法与范围</a>','<a href="../review/METHOD.txt">前一轮审查方法</a>').replace('旋转 / 支撑候选（未放行）','当前修补版本（待整盘验收）').replace('<a id="data" target="_blank">本件完整记录</a>','<a id="data" target="_blank">本件记录</a><a id="project">本件 3MF 试版</a>')
start=html.index('<section class="card notes">');end=html.index('</section></main>',start);html=html[:start]+'''<section class="card notes"><h2>修补预览与装配参考</h2><p>此页面显示正在验证的实际修改网格，整套尚未放行。蓝色为最终保留的零件；橙色支撑鳍和黄色连接齿均需在装配前去除。部分本体已添加小倒角，具体改动与接触检查见本件记录。</p><p>拆除时先逐段剪断黄色连接齿。带拱架的零件需要把橙色顶部横梁剪成数段，再分别拆下接地立腿、侧面加强筋和底脚；不要把整个拱架强行抽出，也不要用力扳动传感器弹片。孔道、螺母槽和配合面内的支撑碎屑需要清理干净，蓝色本体上的永久倒角应保留。</p><p><a href="../../O22F3_Release/assembly/tutorials/assembly-o22/index.html">O22 原有装配图解</a> · <a href="../review/index.html">前一轮全件审查报告</a></p><p>本件通过几何筛查不等于已经完成整盘或实物试印验收。受力、热变形、床面附着及拆除手感尚无实测数据。</p>'''+html[end:];(D/'index.html').write_text(html,encoding='utf8')
js=(O/'review/review.js').read_text(encoding='utf8');js=js.replace("mode:'baseline'","mode:'candidate'");a=js.index("$('#measure').innerHTML=");b=js.index("$('#clip').value=180",a)
js=js[:a]+'''let info=data.candidate?.assessment;$('#project').href=data.candidate.project;$('#project').style.display=candidate?'inline':'none';$('#measure').innerHTML=candidate?'<div>外部孤岛 / 待处理路径<br><strong>'+info.external_islands+' / '+info.external_critical_runs+'</strong></div><div>本体改形 / 配合检查<br><strong>'+(info.body_changed?(info.body_fit?'已改形，检查通过':'已改形，继续检查'):'保留原本体')+'</strong></div><div>打印总高度<br><strong>'+g.height_mm.toFixed(1)+' mm</strong></div>':'<div>F3 原版对照</div>';
$('#loading').textContent=candidate?'当前网格 '+data.candidate.label+' · '+(info.ready_for_plate_recheck?'本件检查条件满足，待整盘复核。':'本件仍有待处理项，当前仅供审阅。'):'F3 原始对照网格。';
'''+js[b:]
a=js.index("$('#notice').textContent=");b=js.index("$('#inventory').onclick=",a)
js=js[:a]+'''$('#notice').textContent='修补工作仍在进行；此页面不是整套打印放行文件。可逐件查看当前真实网格及待处理位置。';
$('#stats').innerHTML=[[A.type_count,'当前零件类型'],[A.ready_for_plate_recheck,'本件检查条件满足，待整盘复核'],[A.source_bodies_changed_in_current_selection,'当前选择中的永久改形'],['未完成','整套打印放行']].map(x=>'<div class="stat"><strong>'+x[0]+'</strong><span class="muted">'+x[1]+'</span></div>').join('');
$('#inventory').innerHTML='<table><thead><tr><th>编号</th><th>名称</th><th>当前版本</th><th>孤岛 / 待处理路径</th><th>本体改形</th><th>状态</th></tr></thead><tbody>'+A.rows.map(r=>'<tr><td><button data-id="'+r.id+'">'+r.id+'</button></td><td>'+r.part+'</td><td>'+r.candidate_label+'</td><td>'+r.candidate_islands+' / '+r.candidate_spans+'</td><td>'+(r.body_changed?'有':'无')+'</td><td>'+r.disposition+'</td></tr>').join('')+'</tbody></table>';
'''+js[b:]
js=js.replace("if(query.get('mode')==='candidate')state.mode='candidate'", "if(query.get('mode')==='baseline')state.mode='baseline'")
js=js.replace("$('#layerplot').style.display=state.mode==='baseline'&&(data.summary.Orca_spans+data.summary.Orca_islands)>0?'inline':'none'", "$('#layerplot').style.display='none'")
(D/'review.js').write_text(js,encoding='utf8');print('REPAIR_PREVIEW',len(rows),'ready',ready,'body_changed',changed,flush=True)
