"""Export F6's actual meshes and retained F5 removal directions for offline viewing."""
import json,copy,shutil,gzip,base64,re
import numpy as np
import o22f6_final as f
h=f.h;f.configure()

def encoded(v,faces):return dict(v=base64.b64encode(gzip.compress(np.asarray(v,dtype='<f4').tobytes(),mtime=0)).decode(),f=base64.b64encode(gzip.compress(np.asarray(faces,dtype='<u4').tobytes(),mtime=0)).decode())
def write(p,s):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(s,encoding='utf-8')
def jsdata(p):return json.loads(p.read_text().split('=',1)[1].rstrip(';'))

def main():
 m=f.manifest();proof={r['id']:r for r in json.loads((f.WORK/'geometry_verification.json').read_text())['rows']};rows=[];checks=[]
 for source in m['rows']:
  pid=source['id'];a=np.load(f.OUT/f'parts/{pid}.npz');b=np.load(h.SRC/f'parts/{pid}.npz');g=proof[pid];fin=h.solid(a['fin_v'],a['fin_f']);teeth=h.solid(a['teeth_v'],a['teeth_f']);oldfin=h.solid(b['fin_v'],b['fin_f']);oldteeth=h.solid(b['teeth_v'],b['teeth_f']);fin_added=max(0.,float((fin-oldfin).volume()));teeth_added=max(0.,float((teeth-oldteeth).volume()));assert fin_added<1e-6 and teeth_added<1e-6,(pid,'non_subset_support')
  oldgeom=jsdata(h.SRC/f'geometry/{pid}_candidate.js');row=copy.deepcopy(source);row.update(g);row.update(f6_status='NOT_RELEASED',height_mm=float(np.vstack([a['v'],a['fin_v'],a['teeth_v']])[:,2].max()),body_changed=False,body_change_reference='F5',physical_print_tested=False,review_required=False,geometry_proof=f'verification/parts/{pid}/geometry.json',support_reduction_from_F5_percent=100*(1-float((fin+teeth).volume())/float((oldfin+oldteeth).volume()))if(oldfin+oldteeth).volume()>0 else 0.)
  for it in row['instances']:it['project']=it['project'].replace('_O22F5_PLA_fins.3mf','_O22F6_PLA_final.3mf')
  if not g['support_geometry_changed']:
   geom=oldgeom
   # Exact original NPZ equality makes the original directional removal records applicable.
  else:
   vs=np.vstack([a['v'],a['fin_v'],a['teeth_v']]);geom=dict(meshes={role:encoded(a[vk],a[fk])for role,vk,fk in [('part','v','f'),('fin','fin_v','fin_f'),('teeth','teeth_v','teeth_f')]if len(a[fk])},bounds=np.r_[vs.min(0),vs.max(0)].tolist(),fin_groups={},stem_groups={});groups=[];gp=np.load(h.SRC/f'verification/parts/{pid}/f5_fin_groups.npz');new_bodies=[]
   for j,q in enumerate(source['fin_bodies'],1):
    original=h.solid(gp[f'g{j}_v'],gp[f'g{j}_f']);new=original^fin
    if new.volume()<1e-6:continue
    groups.append(new);geom['fin_groups'][q['id']]=dict(encoded(*h.vf(new)),bounds=list(new.bounding_box()),removal_vector=q['removal_vector']);new_bodies.append(dict(q,bounds_mm=list(new.bounding_box()),volume_mm3=float(new.volume()),subset_of_F5_fin_group=True))
   joined=h.union(groups);delta=abs(float((joined-fin).volume()))+abs(float((fin-joined).volume()));assert delta<1e-5,(pid,'viewer_fin_coverage',delta)
   row['fin_bodies']=new_bodies;row['removal_stages']=[dict(s,groups=[k for k in s['groups']if k in geom['fin_groups']])for s in source['removal_stages']if any(k in geom['fin_groups']for k in s['groups'])];row['extractable_stems']=[];row['stem_removal_record_order']=[];row['historical_F5_tooth_records']=row.pop('tooth_records',None)
  write(f.OUT/f'geometry/{pid}_candidate.js','window.AUDIT_MESHES['+json.dumps(pid+'_candidate')+']='+json.dumps(geom,separators=(',',':'))+';')
  h.put(f.OUT/f'records/{pid}.json',dict(summary=row,geometry=g,removal_directions_source='F5 exact retained supports or geometric subsets; permanent body unchanged',historical_F5_removal_stages=source['removal_stages']))
  write(f.OUT/f'records/{pid}.js','window.AUDIT_DETAILS['+json.dumps(pid)+']='+json.dumps(row,ensure_ascii=False,separators=(',',':'))+';');rows.append(row);checks.append(dict(id=pid,source_npz_sha256=h.sha(f.OUT/f'parts/{pid}.npz'),support_subset_of_F5=True,added_fin_mm3=fin_added,added_connector_mm3=teeth_added,original_directions_preserved=True));print('VIEWER',pid,flush=True)
 h.put(f.WORK/'viewer_rows.json',rows);h.put(f.WORK/'support_subset_proof.json',checks)
 audit=dict(m,rows=rows,complete=False,version='O22F6-PLA-Final-staging')
 for p in audit['plates']:p['project']=p['project'].replace('_O22F5_PLA_fins.3mf','_O22F6_PLA_final.3mf');p['proof']=f"verification/plates/{p['id']}/support_paths.json"
 write(f.OUT/'audit-data.js','window.AUDIT='+json.dumps(audit,ensure_ascii=False,separators=(',',':'))+';window.AUDIT_DETAILS={};window.AUDIT_MESHES={};')
 html=(h.SRC/'index.html').read_text().replace('O22-F5','O22F6').replace('稀疏支撑 · 合盘与安装','PLA 最终版 · 打印与拆撑').replace('合盘布局与旧盘对照','打印盘布局').replace('验证说明.html','检查与例外.html').replace('打印与拆除.html','打印与拆撑.html')
 write(f.OUT/'index.html',html)
 js=(h.SRC/'viewer.js').read_text().replace("id:'X046'","id:'P095'")
 old="$('#notice').textContent=A.complete?'本套已重新设计并减少支撑，完成几何检查和整盘原生出丝检查。X062 R2 沿用实测通过的网格，其余新版尚待实物验证。请保留项目中的朝向与参数。':'交付页面正在整理，主套件尚未齐全；当前是工作预览。';"
 new="$('#notice').textContent=A.complete?'O22F6 PLA 最终版：14 盘完整路径检查通过。49 种保留清孔改动，16 种为承托恢复原支撑（含 P095），需打印后清理孔内细齿。全部本体与 F5 相同；本批尚未实物试打。':'正在完成最终检查；此预览尚未放行。';"
 assert old in js;js=js.replace(old,new)
 js=re.sub(r"\$\('#stem-info'\)\.textContent=data\.extractable_stems\.length\?.*?;", "$('#stem-info').textContent=stemNotice(data);",js)
 start="$('#removal-info').textContent='连接齿记录 ";ix=js.index(start);end=js.index(";$('#title')",ix)
 js=js[:ix]+"$('#removal-info').textContent='本体与 F5 完全相同。'+(data.support_geometry_changed?'保留通过检查的孔位避让。':'保留 F5 支撑形状。')+(data.removal_stages.length?' 剪清黄色连接齿后，按顺序拆鳍：'+data.removal_stages.map(s=>s.groups.join('、')+(s.simultaneous?' 同步取下':'')).join(' → '):' 本件直接落在热盘上。')"+js[end:]
 js=js.replace("(data.body_changed?'局部改形并复核配合':'沿用 F4 本体')","'与 F5 完全一致'")
 js=js.replace("<strong>未检出所列悬空问题</strong>","<strong>全盘检查通过</strong>")
 js=js.replace("$('#loading').textContent=data.physical_print_tested?'X062 R2：沿用已实测通过的网格。':'显示本件最终打印网格；已完成数字检查，尚未实物验证。';","$('#loading').textContent=A.complete?'显示与最终文件对应的实际网格。'+(data.original_F5_support_restored?'本件恢复了 F5 孔位承托，打印后需清理。':'本件支撑与螺钉、沉孔、螺母位保护区无实体交叠。'):'最终检查进行中；此预览尚未放行。';")
 js=js.replace("data.fin_count+' 片'","Object.keys(meshData.fin_groups||{}).length+' 组'")
 js+="\nfunction stemNotice(d){return d.extractable_stems.length?'先从外侧剪断孔腔细齿根部，保持孔内段完整；依序整根抽出：'+d.stem_removal_record_order.map(k=>typeof k==='number'?'T'+String(k+1).padStart(3,'0'):'同步 '+k.simultaneous_records.map(x=>'T'+String(x+1).padStart(3,'0')).join('、')).join(' → '):d.original_F5_support_restored?'本件保留原有孔位承托。请结合半透明和剖切视图，清理孔道、沉孔及螺母位中的支撑残留。':'本件支撑与螺钉、沉孔、螺母位保护区无实体交叠。'}\n"
 js=js.replace("$('#stem-info').textContent=stemNotice(data);\n$('#finpick')","$('#stem-info').textContent=stemNotice(data);}draw()};\n$('#finpick')")
 js=js.replace("data.fin_count+' 片</option>'","Object.keys(meshData.fin_groups||{}).length+' 组</option>'").replace("r.id==='X046')?'X046'","r.id==='P095')?'P095'")
 js=js.replace("<strong>全盘检查通过</strong>","<strong>'+ (A.complete?'全盘检查通过':'检查中') +'</strong>")
 js=js.replace("getContext('webgl',{antialias:true,preserveDrawingBuffer:true})","getContext('webgl',{antialias:true,alpha:false,preserveDrawingBuffer:true})")
 write(f.OUT/'viewer.js',js)
 for name in ['start_preview.py','打开3D与安装说明.cmd']:
  content=(h.SRC/name).read_text(encoding='utf-8-sig').replace('O22-F5','O22F6').replace('O22F5','O22F6');write(f.OUT/name,content)
 shutil.copytree(h.SRC/'assembly',f.OUT/'assembly',dirs_exist_ok=True)
 for p in (f.OUT/'assembly').rglob('*'):
  if p.suffix.lower()in ['.html','.json','.js','.md','.txt']:
   text=p.read_text(encoding='utf-8-sig');text=text.replace('_O22F5_PLA_fins.3mf','_O22F6_PLA_final.3mf')
   if p.name=='index.html':text=text.replace('<body>','<body><p style="padding:14px;background:#e5f3ed">O22F6：沿用 F5 安装顺序，所有永久本体与 F5 完全相同。先按<a href="../../../打印与拆撑.html">本版拆撑说明</a>清理孔内支撑，再安装五金。</p>',1)
   write(p,text)
 print('VIEWER_COMPLETE',len(rows),flush=True)
if __name__=='__main__':main()