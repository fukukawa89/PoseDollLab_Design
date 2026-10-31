import json,copy,shutil,gzip,base64,re,hashlib
import numpy as np
import o22f7 as r
import o22f6r1_viewer as oldview
from route_revo22_x062244 import tooth
h=r.h

def enc(v,f):return{key:base64.b64encode(gzip.compress(np.asarray(a,dtype=d).tobytes(),mtime=0)).decode()for key,a,d in[('v',v,'<f4'),('f',f,'<u4')]}
def write(p,s):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(s,encoding='utf8')
def jsdata(p):return json.loads(p.read_text('utf8').split('=',1)[1].rstrip(';'))
def main():
 m=r.manifest();changed=r.read(r.WORK/'whole_batch_audit.json')['affected_ids'];rows=[];checks=[]
 for sub in['geometry','records','assembly']:shutil.copytree(r.BASE/sub,r.OUT/sub,dirs_exist_ok=True)
 for name in['index.html','viewer.js','合盘布局.html','零件与打印盘对照.csv']:
  write(r.OUT/name,(r.BASE/name).read_text('utf-8-sig').replace('O22F6','O22F7').replace('O22-F6','O22-F7'))
 shutil.copy2(h.R/'scripts/o22f7_preview.py',r.OUT/'start_preview.py')
 shutil.copy2(h.R/'scripts/o22f7_preview.cmd',r.OUT/'打开3D与安装说明.cmd')
 shutil.copy2(h.B/'diagnostics/P095_elbow_20261016/final_removal.json',r.WORK/'removal/P095.json')
 for oldrow in m['rows']:
  row=copy.deepcopy(oldrow);pid=row['id'];n=np.load(r.OUT/f'parts/{pid}.npz');b=np.load(r.BASE/f'parts/{pid}.npz');row.update(body_changed=pid in changed,body_vertices_and_faces_identical_to_F5=pid not in changed,npz_sha256=h.sha(r.OUT/f'parts/{pid}.npz'),body_change_reference='O22F6',native_pending=True,native_review_passed=False)
  for it in row['instances']:it['project']=it['project'].replace('O22F6','O22F7')
  if pid in changed:
   a=next(x for x in r.read(r.WORK/'whole_batch_audit.json')['rows']if x['id']==pid);removal=r.read(r.WORK/f'removal/{pid}.json')if(r.WORK/f'removal/{pid}.json').exists()else None;gp=np.load(h.SRC/f'verification/parts/{pid}/f5_fin_groups.npz');oldsrc=next(x for x in r.read(h.SRC/'manifest.json')['rows']if x['id']==pid);fin=h.solid(n['fin_v'],n['fin_f']);teeth=h.solid(n['teeth_v'],n['teeth_f']);groups={q['id']:h.solid(gp[f'g{j}_v'],gp[f'g{j}_f'])^fin for j,q in enumerate(oldsrc['fin_bodies'],1)};lookup={q['id']:j for j,q in enumerate(oldsrc['fin_bodies'],1)}
   order=removal['revised_removal_order']if removal else[k for stage in oldsrc['removal_stages']for k in stage['groups']];directions={q['group']:q['vector']for q in removal['affected_groups']}if removal else{}
   merged={k:h.union([groups[x]for x in k.split('+')])for k in order};oldgeom=jsdata(r.BASE/f'geometry/{pid}_candidate.js');vs=np.vstack([n[x]for x in['v','fin_v','teeth_v']]);geom=dict(meshes={role:enc(n[v],n[f])for role,v,f in[('part','v','f'),('fin','fin_v','fin_f'),('teeth','teeth_v','teeth_f')]},bounds=np.r_[vs.min(0),vs.max(0)].tolist(),fin_groups={k:dict(enc(*h.vf(s)),bounds=list(s.bounding_box()),removal_vector=directions.get(k,[0,0,-1]))for k,s in merged.items()if s.volume()>1e-6},stem_groups=oldgeom.get('stem_groups',{}))
   write(r.OUT/f'geometry/{pid}_candidate.js','window.AUDIT_MESHES['+json.dumps(pid+'_candidate')+']='+json.dumps(geom,separators=(',',':'))+';')
   row['removal_stages']=[dict(groups=[k],vector=directions.get(k,[0,0,-1]),simultaneous='+'in k)for k in order];row['elbow_comparison']=f'elbows/{pid}/index.html';row['f7_added_contact_count']=len(r.read(r.OUT/f'design/{pid}.json').get('r1_native_contacts',[]));row['body_added_mm3']=float(h.solid(n['r1_added_body_v']if pid=='P095'else n['f7_added_body_v'],n['r1_added_body_f']if pid=='P095'else n['f7_added_body_f']).volume())
   comparison(pid,n,b,a,removal,gp,lookup,fin,teeth)
   for role,v,f in[('part','v','f'),('fin','fin_v','fin_f'),('teeth','teeth_v','teeth_f')]:
    for field,ar,dt in[('v',n[v],'<f4'),('f',n[f],'<u4')]:assert np.array_equal(np.frombuffer(gzip.decompress(base64.b64decode(geom['meshes'][role][field])),dtype=dt).reshape(ar.shape),ar.astype(dt))
  else:assert h.sha(r.OUT/f'parts/{pid}.npz')==h.sha(r.BASE/f'parts/{pid}.npz')
  rows.append(row);h.put(r.OUT/f'records/{pid}.json',dict(summary=row,source_revision='O22F6',body_changed=pid in changed,revision_geometry_proof=f'../../verification/geometry/{pid}.json'if pid in changed else'Inherited exact mesh'))
  write(r.OUT/f'records/{pid}.js','window.AUDIT_DETAILS['+json.dumps(pid)+']='+json.dumps(row,ensure_ascii=False,separators=(',',':'))+';');checks.append(dict(id=pid,npz_sha256=h.sha(r.OUT/f'parts/{pid}.npz'),actual_mesh_view=True,float32_for_display_only=True))
 m.update(version='O22F7-PLA-Final',complete=False,status='VALIDATION_IN_PROGRESS',body_changed_from_F5_type_ids=changed,rows=rows)
 for p in m['plates']:p.update(project=p['project'].replace('O22F6','O22F7'),title='O22F7 PLA 最终版',native_review_passed=False)
 h.put(r.OUT/'manifest.json',m);write(r.OUT/'audit-data.js','window.AUDIT='+json.dumps(m,ensure_ascii=False,separators=(',',':'))+';window.AUDIT_DETAILS={};window.AUDIT_MESHES={};');h.put(r.WORK/'viewer_mesh_equality.json',dict(rows=checks,types=150))
 js=(r.OUT/'viewer.js').read_text('utf8');js=js.replace('全部本体与 F5 相同；','8 类 C14 转角已补强；').replace("'本体与 F5 完全相同。'","(data.body_changed?'本件两个转角已补强。':'本件本体沿用 F6。')").replace("'与 F5 完全一致'","(data.body_changed?'转角局部补强':'本体沿用 F6')");js=js.replace("$('#title').textContent=", "$('#elbow-link').hidden=!data.body_changed;$('#elbow-link').href=data.elbow_comparison||'#';$('#title').textContent=")
 js=js.replace('49 种保留清孔改动，16 种为承托恢复原支撑（含 P095），需打印后清理孔内细齿。','16 类保留孔内可拆承托；P095、P073 的新增细齿需按本版方向拆除。')
 js=js.replace('本件恢复了 F5 孔位承托，打印后需清理。','本件保留孔位承托，打印后需清理。')
 write(r.OUT/'viewer.js',js)
 html=(r.OUT/'index.html').read_text('utf8').replace('<a id="data">','<a id="elbow-link" class="button" hidden>转角前后与剪齿定位</a><a id="data">');write(r.OUT/'index.html',html)
 for p in(r.OUT/'assembly').rglob('*'):
  if p.suffix.lower()in['.html','.json','.js','.md','.txt']:
   text=p.read_text('utf-8-sig').replace('_O22F6_PLA_final.3mf','_O22F7_PLA_final.3mf').replace('O22F6：沿用 F5 安装顺序，所有永久本体与 F5 完全相同。','O22F7：8 类 C14 转角已补强，轴线和安装顺序保持。此处为装配示意，修订形状以本版零件页实际网格为准。')
   if p.parent==r.OUT/'assembly/tutorials/assembly-o22'and p.name in['index.html','external-files.html']:text=text.replace('O22-F5','O22F7').replace('本套件已包含 O22F7 的 11 盘支撑鳍打印工程','本套件已包含 O22F7 的 14 盘 PLA 完整打印工程')
   write(p,text)
 import o22f7_assembly_guide as assembly_guide
 assembly_guide.build()
 print('VIEWER_STAGED',len(rows),flush=True)

def comparison(pid,n,b,a,removal,gp,lookup,fin,teeth):
 dst=r.OUT/'elbows'/pid;dst.mkdir(parents=True,exist_ok=True);data={}
 for label,arr in[('before',b),('after',n)]:data[label]={role:enc(arr[v],arr[f])for role,v,f in[('body','v','f'),('fin','fin_v','fin_f'),('teeth','teeth_v','teeth_f')]}
 prefix='r1'if pid=='P095'else'f7';data['added']=enc(n[prefix+'_added_body_v'],n[prefix+'_added_body_f']);data['bounds']=np.r_[n['v'].min(0),n['v'].max(0)].tolist();vv=np.vstack([n[x]for x in['v','fin_v','teeth_v']]);data['print_bounds']=np.r_[vv.min(0),vv.max(0)].tolist();data['bends']=[x['print_centre']for x in a['candidate_bends']if x['active_flat_capped_elbow']];data['groups']={}
 for q in removal['affected_groups']if removal else[]:
  k=q['group'];oldgroup=h.union([h.solid(gp[f'g{lookup[x]}_v'],gp[f'g{lookup[x]}_f'])for x in k.split('+')]);group=oldgroup^fin;tt=[];cuts=[]
  for rr in removal['connections']:
   if rr['group']!=k:continue
   rec=rr['record'];root=np.array(rec['root']);tip=np.array(rec['tip']);cut=root+(tip-root)*((rec['cut_z_mm']-root[2])/(tip[2]-root[2]));tt.append(tooth(root,tip,.8)^teeth);cuts.append(h.md.Manifold.sphere(.55,24).translate(cut))
  z=np.array(q['vector']);z/=np.linalg.norm(z);seed=np.eye(3)[np.argmin(abs(z))];x=np.cross(seed,z);x/=np.linalg.norm(x);bb=np.array(group.bounding_box());pos=(bb[:3]+bb[3:])/2;arrow=(h.md.Manifold.cylinder(8,.18,circular_segments=16)+h.md.Manifold.cylinder(2.5,.7,0,circular_segments=24).translate([0,0,8])).transform(np.c_[x,np.cross(z,x),z,pos]);data['groups'][k]=dict(before=enc(*h.vf(oldgroup)),after=enc(*h.vf(group)),teeth=enc(*h.vf(h.union(tt))),cuts=enc(*h.vf(h.union(cuts))),arrow=enc(*h.vf(arrow)),direction=q['vector'],notice=k+'：剪断红点处新增细齿及原有连接齿，清除挡路的齿根；按绿色箭头'+('作为一组同步退出。'if'+'in k else'退出。')+'清理本体上留下的短齿后再装配。')
 write(dst/'mesh-data.js','window.MESH_DATA='+json.dumps(data,separators=(',',':'))+';');js=oldview.JS;start=js.index("note.textContent=e.target.value===");end=js.index(';draw()};for(let id',start);js=js[:start]+"note.textContent=active?source.groups[e.target.value].notice:''"+js[end:];write(dst/'compare.js',js)
 css=oldview.HTML.split('<style>',1)[1].split('</style>',1)[0];opts=''.join('<option>'+x+'</option>'for x in data['groups']);mass=h.solid(n[prefix+'_added_body_v'],n[prefix+'_added_body_f']).volume();plate=next(it['plate']for row in r.manifest()['rows']if row['id']==pid for it in row['instances']);extra='<p>P002 有一处圆接头按胸架运动空间保留小避让面；只修剪拟新增材料，原杆体不变。</p>'if pid=='P002'else''
 html='<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><link rel="icon" href="data:,"><title>'+pid+' 转角修订 · O22F7</title><style>'+css+'</style><header><p>POSEDOLL · O22F7</p><h1>'+pid+' · 转角补强与拆撑</h1></header><main><p><a href="../../index.html?id='+pid+'">返回整套零件与打印盘</a> · <a href="../../打印与拆撑.html">打印与拆撑说明</a></p><p class="intro">两段平端圆杆留下的缺口已补强，新增永久材料约 '+str(round(mass,2))+' mm³。蓝色接头属于零件本体；橙色支撑与黄色细齿需要拆除。</p>'+extra+'<div class="toolbar"><button data-view="0">转角 A</button><button data-view="1" class="active">转角 B</button><button data-view="all">整体零件</button><button id="reset">重置角度</button><label><input id="highlight" type="checkbox">突出新增材料</label><label><input id="supports" type="checkbox">显示支撑</label><label>新增细齿定位 <select id="support-group"><option value="all">全部</option>'+opts+'</select></label></div><p id="removal-note" class="note" hidden></p><div class="grid">'
 for side,title in[('before','修订前 · O22F6'),('after','修订后 · O22F7')]:html+='<section class="pane '+side+'"><div class="cap"><h2>'+title+'</h2><span>实际打印网格</span></div><div class="canvas-wrap"><div class="view-label">转角 B</div><canvas id="'+side+'" aria-label="'+pid+' '+title+'"></canvas></div><div class="legend"><span>蓝：永久本体　橙：可拆鳍　黄：可剪齿</span><span id="addlegend" hidden>金色：新增永久材料</span></div></section>'if side=='after'else'<section class="pane"><div class="cap"><h2>'+title+'</h2><span>实际打印网格</span></div><div class="canvas-wrap"><div class="view-label">转角 B</div><canvas id="before" aria-label="'+pid+' 修订前"></canvas></div><div class="legend">蓝：永久本体　橙：可拆鳍　黄：可剪齿</div></section>'
 html+='<div id="status" class="status">数字检查进行中；尚未放行打印。</div></div><p class="note">拖动同步旋转，滚轮缩放。红点与绿色箭头是剪齿和退出方向标记，不会打印。尚未实物打印、强度或疲劳测试。</p><p><a class="button" href="../../projects/'+plate+'_O22F7_PLA_final.3mf">打开 '+plate+' PLA 工程</a></p></main><script src="mesh-data.js"></script><script src="compare.js"></script></html>';write(dst/'index.html',html)
if __name__=='__main__':main()
