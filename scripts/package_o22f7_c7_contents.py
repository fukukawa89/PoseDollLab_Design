"""Assemble revision contents and current user-facing catalog; final sealing is separate."""
from o22f7_animation import *
import o22f7_native as h,copy,html,csv,gzip,base64
C=WORK/'structure_revision';P=C/'print_candidate';N=B/'O22F7_PLA_AssemblyRevision';NG=N/'assembly/tutorials/assembly-o22';m=read(F/'manifest.json');g=read(NG/'guide-data.json');changed=read(P/'changed_plates.json')['plates'];removal=read(C/'C7_print_geometry_and_removal.json');newrows=[]
def enc(v,f):return {k:base64.b64encode(gzip.compress(np.asarray(a,dtype=dt).tobytes(),mtime=0)).decode() for k,a,dt in [('v',v,'<f4'),('f',f,'<u4')]}
for p in changed:
 proof=read(C/f"native_print_review/plates/{p['id']}/support_paths.json");assert proof['native_review_resolved'] and proof['external_island_count']==0 and proof['critical_external_count']==0 and proof['project_sha256']==sha(P/p['project']);p.update(project_sha256=sha(P/p['project']),native_review_passed=True,proof=f"verification/plates/{p['id']}/support_paths.json")
 for it in p['items']:
  n=np.load(P/f"parts/{it['id']}.npz");vv=np.concatenate([n[k] for k in ['v','fin_v','teeth_v'] if len(n[k])]);v=vv@np.array(it['rotation_matrix']).T+it['translation_mm'];assert v.min()>=-1e-5 and v[:,:2].min()>=3.99 and v[:,:2].max()<=176.01;it['bounds_mm']=np.r_[v.min(0),v.max(0)].tolist()
 shutil.copy2(P/p['project'],N/p['project']);shutil.copytree(C/f"native_print_review/plates/{p['id']}",N/f"verification/plates/{p['id']}",dirs_exist_ok=True)
for pid in ['W005A','W005B']:
 for sub,suf in [('parts','npz'),('design','json')]:shutil.copy2(P/f'{sub}/{pid}.{suf}',N/f'{sub}/{pid}.{suf}')
 n=np.load(N/f'parts/{pid}.npz');body,fin,teeth=[h.solid(n[v],n[f]) for v,f in [('v','f'),('fin_v','fin_f'),('teeth_v','teeth_f')]];groups={f'S{i:02}':s for i,s in enumerate(h.material_components(fin),1)};vs=np.concatenate([n[k] for k in ['v','fin_v','teeth_v']]);geom={'meshes':{role:enc(n[v],n[f]) for role,v,f in [('part','v','f'),('fin','fin_v','fin_f'),('teeth','teeth_v','teeth_f')]},'bounds':np.r_[vs.min(0),vs.max(0)].tolist(),'fin_groups':{k:dict(enc(*h.vf(s)),bounds=list(s.bounding_box()),removal_vector=[0,0,-1]) for k,s in groups.items()},'stem_groups':{}}
 write(N/f'geometry/{pid}_candidate.js','window.AUDIT_MESHES['+json.dumps(pid+'_candidate')+']='+json.dumps(geom,separators=(',',':'))+';');q=next(q for q in g['instances'] if q['id']==pid);q.update(previous_f4_address='C03-02（拆分来源）',original_address='A04-02（拆分来源）');rr=next(r for r in removal['rows'] if r['id']==pid)
 row=dict(id=pid,part=q['part'],plates=q['address'],height_mm=float(vs[:,2].max()),instances=[q],body_changed=True,structural_split=True,body_change_reference='O22F7 W005',review_required=False,npz_sha256=sha(N/f'parts/{pid}.npz'),geometry_proof='verification/C7/C7_print_geometry_and_removal.json',removed_mm3=0,added_mm3=0,extractable_stems=[],stem_removal_record_order=[],layer_height_mm=.2,layer_heights_mm=[.2],fin_count=len(groups),support_volume_mm3=float((fin+teeth).volume()),physical_print_tested=False,native_pending=False,native_review_passed=True,retained_hole_support_exception=pid=='W005B',all_fastener_clearance_support_free=pid=='W005A',support_geometry_changed=True,removal_stages=[{'groups':[k],'vector':[0,0,-1],'simultaneous':False} for k in groups],fin_bodies=[{'id':k,'bounds_mm':list(s.bounding_box()),'volume_mm3':float(s.volume()),'removal_vector':[0,0,-1]} for k,s in groups.items()],support_removal_note='先剪清黄色连接齿，再向下取下橙色承托。W005B 的新增 M2 接合沉孔边缘有一根细齿，先清理后装螺钉。' if pid=='W005B' else '先剪清接触齿，再向下取下承托；五个短柱也属于可拆承托。')
 newrows.append(row)
m['rows']=[r for r in m['rows'] if r['id']!='W005']+newrows;m['rows'].sort(key=lambda r:r['id']);m['plates']=[next((q for q in changed if q['id']==p['id']),p) for p in m['plates']]+[changed[1]];m.update(revision='assembly-r4-C7',status='DIGITAL_CHECKS_PASSED_PENDING_PACKAGE_QA',complete=False,type_count=151,main_instances=187,main_plate_count=15,installed_instances=186,total_instances=194,hardware_instances=960)
for row in m['rows']:
 for it in row['instances']:
  if it['plate']=='D05':it['project']=changed[0]['project']
 old=read(N/f"records/{row['id']}.json") if (N/f"records/{row['id']}.json").exists() else {};old['summary']=row;put(N/f"records/{row['id']}.json",old);write(N/f"records/{row['id']}.js",'window.AUDIT_DETAILS['+json.dumps(row['id'])+']='+json.dumps(row,ensure_ascii=False,separators=(',',':'))+';')
put(N/'manifest.json',m);write(N/'audit-data.js','window.AUDIT='+json.dumps(m,ensure_ascii=False,separators=(',',':'))+';window.AUDIT_DETAILS={};window.AUDIT_MESHES={};')
# Preserve originals as provenance, and identify all new evidence by hash.
vdir=N/'verification/C7';vdir.mkdir(exist_ok=True)
for name in ['W005_C7.npz','W005_C7_geometry_review.json','W005_C7_surface_review.json','W005_C7_function_review.json','W005_C7_exact_gap_review.json','W005_C7_preassembly_review.json','W005_C7_stock_review.json','W005_C7_sequence_interfaces.json','C7_chest_core_transfer_path.json','C7_chest_rotation_review.json','C7_print_geometry_and_removal.json']:shutil.copy2(C/name,vdir/name)
shutil.copytree(C/'native_print_review/contacts',vdir/'contacts',dirs_exist_ok=True)
for pid in ['W005A','W005B']:shutil.copy2(P/f'guards/{pid}.npz',vdir/f'{pid}_hole_guard.npz')
# The shared print viewer receives current mesh records and a split-specific explanation.
s=(N/'viewer.js').read_text('utf8');s=s.replace("(data.body_changed?'本件两个转角已补强。':'本件本体沿用 F6。')","(data.structural_split?'左锁骨装配拆分修订。':data.body_changed?'本件两个转角已补强。':'本件本体沿用 F6。')").replace("(data.body_changed?'转角局部补强':'本体沿用 F6')","(data.structural_split?'左锁骨拆分修订':data.body_changed?'转角局部补强':'本体沿用 F6')").replace("$('#elbow-link').hidden=!data.body_changed","$('#elbow-link').hidden=!data.body_changed||!!data.structural_split").replace('14 盘完整路径检查通过。16 类','15 盘切片承托检查通过。17 类').replace('function stemNotice(d){return ',"function stemNotice(d){if(d.structural_split)return d.support_removal_note;return ");write(N/'viewer.js',s)
s=(N/'index.html').read_text('utf8').replace('D01–D14','D01–D15').replace('逐件动画预览','逐件拼装动画').replace('PLA 最终版 · 打印与拆撑','PLA 装配修订版 · 打印与拆撑');write(N/'index.html',s)
# A compact companion page: animation is the primary way to learn, cards locate parts.
css='body{font:16px/1.7 system-ui,Microsoft YaHei;background:#f5f5ee;color:#21473d;margin:0}main{max-width:1160px;margin:auto;padding:36px 24px}h1{font-size:38px;margin:12px 0}h2{margin-top:42px}a{color:#1e6e68}button,input{font:inherit;padding:10px}input{width:min(600px,95%)}.lead{padding:28px;background:#e4ecdf;border-radius:18px}.go{display:inline-block;background:#236154;color:white;text-decoration:none;padding:12px 24px;border-radius:8px}.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(270px,1fr));gap:16px}.card{background:white;border:1px solid #ccd9cb;border-radius:12px;padding:18px}.card img{width:100%;height:auto}table{border-collapse:collapse;width:100%}td,th{padding:10px;text-align:left;border-bottom:1px solid #d4dfd1}.muted{font-size:14px;color:#667c6c}details{margin:16px 0}summary{cursor:pointer;font-weight:600}'
page=lambda title,body:'<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><link rel="icon" href="data:,"><title>'+title+'</title><style>'+css+'</style><main>'+body+'</main></html>'
body='<div class="lead"><p>O22F7 · PLA · 装配修订版 r4</p><h1>跟着动画，从第一件装到完成</h1><p>186 件装机打印件 · 960 件五金与磁铁 · 46 路电路 · 26 章</p><p><a class="go" href="animation/index.html">打开逐件拼装动画 →</a></p><p class="muted">每步默认播完暂停。支持慢放、重播、拖动换角度和查看内部；从已清理支撑、工厂预焊并检查过的电路板开始。</p></div><h2>这次更新</h2><p>原 W005 拆为 <b>D15-01 / W005A 根部</b>和 <b>D05-01 / W005B 长杆</b>，新增 1 枚 M2×6 机螺钉和 1 枚 M2 螺母。D07-02 / H008 保留原件。左右锁骨先在 S02 预装，S04 / S11 再装传感器。</p><p>W005B 接合孔边缘的一根可拆细齿需清理后再装螺钉。<a href="../../../index.html?id=W005B">查看本件与支撑</a>。</p><h2>按章节开始</h2><div class="grid">'
for st in g['steps']:body+=f'<a class="card" href="animation/index.html?step={st["step"]}">{st["step"]} · {html.escape(st["title"])}</a>'
body+='</div><h2 id="plates">当前 15 张打印盘</h2><div class="grid">'
for p in g['plates']:body+=f'<article class="card" id="plate-{p["id"]}"><b>{p["id"]} · {p["count"]} 件</b><a href="{p["preview"]}"><img loading="lazy" src="{p["preview"]}" alt="{p["id"]} 当前盘位"></a><a href="../../../{p["project"]}">打开本盘 PLA 3MF</a></article>'
body+='</div><h2>找零件、型号或盘位</h2><input id="find" type="search" placeholder="例如 W005A、P095、D01-01、左肩"><table id="parts"><thead><tr><th>盘位 / 型号</th><th>零件</th><th>动画</th></tr></thead><tbody>'
for q in g['instances']:
 use='可选小样' if q['optional'] else '工厂焊接量规，不装机' if q['part']=='fixture/xiao_spacing_gauge' else f'<a href="animation/index.html?part={q["id"]}">看安装动作</a>'
 body+=f'<tr><td>{q["address"]} / {q["id"]}</td><td>{html.escape(q["name_zh"])}</td><td>{use}</td></tr>'
body+='</tbody></table><details><summary>五金数量与规格</summary><table><tr><th>规格</th><th>装机数量</th><th>建议采购（含备件）</th></tr>'
for k,v in g['hardware'].items():body+=f'<tr><td>{html.escape(v["name_zh"])}</td><td>{v["net_quantity"]}</td><td>{v["suggested_total"]}</td></tr>'
body+='</table></details><p class="muted">数字检查包括当前网格与切片、逐件覆盖、锁骨与胸架关键装入路径及 414 种姿态的新增干涉对照。尚未实物试装、试打或验证强度疲劳；线束余量和电气结果由你按动画逐项检查。</p><script>document.querySelector("#find").oninput=e=>{let q=e.target.value.toLowerCase();document.querySelectorAll("#parts tbody tr").forEach(r=>r.hidden=!r.textContent.toLowerCase().includes(q))}</script>'
write(NG/'index.html',page('O22F7 · 逐件拼装动画与当前取件清单',body))
with (N/'零件与打印盘对照.csv').open('w',encoding='utf-8-sig',newline='') as f:
 w=csv.writer(f);w.writerow(['盘位','型号','名称','首次安装章节','3MF','备注']);w.writerows([[q['address'],q['id'],q['name_zh'],q['first_use'],q['project'],'不装机' if q['optional'] or q['part']=='fixture/xiao_spacing_gauge' else ''] for q in g['instances']])
with (N/'五金采购清单.csv').open('w',encoding='utf-8-sig',newline='') as f:
 w=csv.writer(f);w.writerow(['型号','规格','装机数量','备件','含备件合计']);w.writerows([[k,v['name_zh'],v['net_quantity'],v['optional_spares'],v['suggested_total']] for k,v in g['hardware'].items()])
write(N/'先读我.txt','''O22F7 PLA 装配修订版 r4 · 2026-10-16

双击“打开逐件拼装动画.cmd”，从第一个动作开始。默认每步播放后暂停。
26 章、1658 个动作；186 件装机打印件、960 件五金与磁铁、46 路电路。
194 件打印实例 = 186 件装机 + 1 件工厂量规 + 7 件可选小样。

打印：A1 mini / 0.4 mm 喷嘴 / PLA。共 15 盘。
D01、D02 层高 0.16 mm，其余 0.20 mm，首层均 0.20 mm。
以项目打开 projects 目录下的 3MF，保留对象参数、朝向和盘位。自动支撑关闭，承托已建在模型中。
D05 使用 D05_O22F7_PLA_assembly.3mf；新增 D15_O22F7_PLA_assembly.3mf。
其余 13 盘与原 O22F7 最终打印包完全相同。

原 D05-01 / W005 被拆成两件：
D05-01 / W005B：左锁骨长杆。
D15-01 / W005A：左锁骨根部。
新增 M2×6 内六角圆柱头机螺钉 1 枚（头径 3.8、高 2 mm）及普通 M2 六角螺母 1 枚。
D07-02 / H008 保留原件。
先在 S02 预装左右锁骨，再接入躯干；S04 / S11 安装传感器。

W005B 接合沉孔边缘有一根必要的可剪连接齿，清理后再装 M2 螺钉。
原有 16 类孔位承托例外仍保留，详见“打印与拆撑.html”。

本包通过数字网格、切片承托和列明的装配/运动检查。
尚未实物试打、试装、强度或疲劳验证。观看动画不会自动勾选实物验收。
''')
for name in ['打印与拆撑.html','检查与例外.html','合盘布局.html']:
 s=(N/name).read_text('utf8').replace('14 盘','15 盘').replace('150 类','151 类').replace('193 个实例','194 个实例').replace('186 正式件','187 正式件').replace('D01–D14','D01–D15').replace('16 类','17 类')
 banner='<div class="ok"><b>装配修订 r4：</b>原 W005 改为 D05-01 / W005B 与 D15-01 / W005A，增加 M2×6 机螺钉和 M2 螺母各一。D05、D15 使用本包 _PLA_assembly.3mf；其余 13 盘保留原文件。W005B 新接合孔边缘一根可剪齿需清理。<a href="assembly/tutorials/assembly-o22/animation/index.html">打开更新后的逐件动画</a>。</div>'
 s=s.replace('</style>','</style>'+banner,1);write(N/name,s)
write(N/'教程更新说明.txt','本版教程为 r4：逐件动画 1658 动作，包含左右锁骨的分体预装、胸部端轴磁铁盖提前安装、胸架转角与绕入动作、46 路电路。请从本目录“打开逐件拼装动画.cmd”进入。旧版动画预览不包含这些安装顺序。\n')
print('PACKAGE_CONTENTS',151,194,15,flush=True)
