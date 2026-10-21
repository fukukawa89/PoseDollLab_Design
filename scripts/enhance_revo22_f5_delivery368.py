"""Add inspectable cavity contacts and readable removal steps to the final gated release."""
from pathlib import Path
import json
import numpy as np
from publish_revo22_f5_compact302 import D,encoded,write
from build_revo22_fins import md,vf,union,box,solid

def run():
 m=json.loads((D/'manifest.json').read_text())
 for row in m['rows']:
  pid=row['id'];records=json.loads((D/'records'/f'{pid}.json').read_text());g=records['geometry'];d=records['design'];path=D/'geometry'/f'{pid}_candidate.js';text=path.read_text();data=json.loads(text.split('=',1)[1].rstrip(';'));data['stem_groups']={}
  for er in g.get('extractable_stems',[]):
   idx=er['record_index'];r=d['local_route_repairs'][idx];a=np.array(r['root']);b=np.array(r['tip']);xy=np.array([[-1,-1,0],[1,-1,0],[1,1,0],[-1,1,0]]);mid=a+(b-a)*max(0.,1-r.get('taper_height_mm',.45)/(b[2]-a[2]));mid=b-np.array([0,0,r.get('taper_height_mm',.9)]) if r.get('contact_pad') else mid;s=union([md.Manifold.hull_points(np.r_[xy*.4+a,xy*.4+mid]),md.Manifold.hull_points(np.r_[xy*.4+mid,xy*(r.get('tip_width_mm',.6)/2)+b])])
   if r.get('mesh_key'):
    nn=np.load(D/'parts'/f'{pid}.npz');s=solid(nn[r['mesh_key']+'_v'],nn[r['mesh_key']+'_f'])
   if d.get('teeth_clipped_at_bed'):s=s^box([-1000,-1000,0],[1000,1000,1000])
   if d.get('bed_drop_mm',0)>0 or d.get('teeth_clipped_by_body_relief'):
    nn=np.load(D/'parts'/f'{pid}.npz');s=s^solid(nn['teeth_v'],nn['teeth_f'])
   v,f=vf(s);data['stem_groups'][f'T{idx+1:03}']=dict(encoded(v,f),bounds=list(s.bounding_box()),removal_vector=er['removal_vector'])
  write(path,'window.AUDIT_MESHES['+json.dumps(pid+'_candidate')+']='+json.dumps(data,separators=(',',':'))+';')
 html=(D/'index.html').read_text().replace('<div id="removal-info"','<label>孔腔细齿 <select id="stempick"><option value="all">全部连接齿</option></select></label><div id="stem-info" class="muted"></div><div id="removal-info"');write(D/'index.html',html)
 js=(D/'viewer.js').read_text();js=js.replace("objects=obs;$('#finpick')", "objects=obs;$('#stempick').innerHTML='<option value=\"all\">全部连接齿</option>'+Object.keys(meshData.stem_groups||{}).map(k=>'<option>'+k+'</option>').join('');$('#stem-info').textContent=data.extractable_stems.length?'先剪除孔外普通齿并从外侧断开孔腔细齿根部，再拆橙色鳍、整根抽出孔腔细齿；不要把细齿剪碎留在孔中。顺序：'+data.stem_removal_record_order.map(k=>typeof k==='number'?'T'+String(k+1).padStart(3,'0'):'同步 '+k.simultaneous_records.map(x=>'T'+String(x+1).padStart(3,'0')).join('、')).join(' → '):'本件的连接齿避开功能孔保护区。';$('#finpick')")
 marker="$('#finpick').onchange=";ix=js.index(marker);extra="$('#stempick').onchange=async()=>{let key=state.id+'_candidate',pick=$('#stempick').value;objects=objects.filter(o=>o.role!=='teeth');let mesh=pick==='all'?meshData.meshes.teeth:meshData.stem_groups[pick];if(mesh)objects.push({role:'teeth',mesh:await geometry(key+'_stem_'+pick,mesh)});if(pick!=='all'){$('#stem-info').textContent=pick+'：整根退出方向（本零件视图坐标） '+mesh.removal_vector.map(v=>v.toFixed(2)).join(', ')+'。先断开根部，保持孔内段完整。'}draw()};\n";js=js[:ix]+extra+js[ix:];js=js.replace("<div>总高度<br><strong>'+data.height_mm.toFixed(1)+' mm</strong></div>","<div>高度 / 层高<br><strong>'+data.height_mm.toFixed(1)+' / '+(data.layer_heights_mm||[data.layer_height_mm]).map(v=>v.toFixed(2)).join(' / ')+' mm</strong></div>");write(D/'viewer.js',js)
 q=D/'验证说明.html';h=q.read_text();h=h.replace('</main>','<p>沉孔部分搭桥设置说明：<a href="https://github.com/OrcaSlicer/OrcaSlicer/wiki/quality_settings_bridging/b56b45a0638b5cc0a1884a36c29cdd3d444a5d99">OrcaSlicer 官方文档</a>。</p></main>');write(q,h)
 print('ENHANCE368_DONE',flush=True)
if __name__=='__main__':run()
