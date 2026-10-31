from pathlib import Path
import json,base64,gzip,zipfile,collections,csv,hashlib
import numpy as np,manifold3d as md
from build_revo22_fins import R,B,O,solid,union
from pack_revo22_a1mini import read_mesh
def encoded(a,dtype):return base64.b64encode(gzip.compress(np.asarray(a,dtype=dtype).tobytes(),mtime=0)).decode()
def run():
 manifest=json.loads((B/'a1mini/manifest.json').read_text());plates=[json.loads((R/'.local/o22-easy-support/S00/manifest.json').read_text())]+[p for p in manifest['plates'] if not p['optional']]
 meshes={};reports={};local={};checks=[];allgeom={}
 for p in plates:
  for it in p['items']:
   pid=it['id']
   if pid in meshes:continue
   n=np.load(O/'parts'/f'{pid}.npz');v,f=read_mesh(B/it['source_3mf'])
   assert np.array_equal(v,n['v']) and np.array_equal(f,n['f']),pid
   meshes[pid]={};solids={}
   for role,vkey,fkey in [('part','v','f'),('fin','fin_v','fin_f'),('teeth','teeth_v','teeth_f')]:
    if len(n[fkey])==0:continue
    meshes[pid][role]={'v':encoded(n[vkey],'<f4'),'f':encoded(n[fkey],'<u4')}
    solids[role]=solid(n[vkey],n[fkey])
   local[pid]=solids
   if 'fin' in solids:assert all(x.bounding_box()[2]<1e-5 for x in solids['fin'].decompose()),pid
   r=json.loads((O/'design'/f'{pid}.json').read_text())
   reports[pid]=r
 for p in plates:
  placed=[];issues=[]
  for it in p['items']:
   M=np.c_[np.array(it['rotation_matrix']),np.array(it['translation_mm'])]
   ss={role:s.transform(M) for role,s in local[it['id']].items()};allv=union(list(ss.values()))
   bb=list(allv.bounding_box());it['fins_bounds_mm']=bb;placed.append((it,allv,bb))
   if min(bb[:3])<-.0001 or max(bb[3:])>180.0001:issues.append({'object':it['object_name'],'out_of_bed':bb})
  for j,(it,a,ab) in enumerate(placed):
   for kt,b,bb in placed[:j]:
    if np.any(np.array(ab[3:])+1<bb[:3]) or np.any(np.array(bb[3:])+1<ab[:3]):continue
    vol=float((a^b).volume())
    gap=float(a.min_gap(b,1.))
    if vol>1e-5 or gap<.6:issues.append({'pair':[it['object_name'],kt['object_name']],'overlap_mm3':vol,'gap_mm':gap})
  checks.append({'plate':p['id'],'object_count':len(p['items']),'issues':issues})
 main=[i for p in plates if not p.get('optional',False) and p['id']!='S00' for i in p['items']]
 counts=collections.Counter(i['part'] for i in main);expected=collections.Counter(i['part'] for p in manifest['plates'] if not p['optional'] for i in p['items'])
 assert counts==expected and len(main)==186
 scene={'plates':plates,'meshes':meshes,'reports':reports}
 (O/'scene.js').write_text('window.O22_FINS='+json.dumps(scene,ensure_ascii=False,separators=(',',':'))+';',encoding='utf-8')
 (O/'manifest.json').write_text(json.dumps({'plates':plates,'source_instances':186,'source_types':len(meshes),'main_quantity_matches_O22':True},ensure_ascii=False,indent=2),encoding='utf-8')
 release={'version':'O22-F1','status':'GEOMETRY_VERIFIED_SLICE_PENDING_PHYSICAL_NOT_TESTED','source_types':len(meshes),'main_instances':186,'source_meshes_exact':True,'all_support_components_touch_bed':True,'body_overlap_with_source_mm3':sum(r['overlap_with_part_mm3'] for r in reports.values()),'functional_guard_overlap_mm3':sum(r['protected_overlap_mm3'] for r in reports.values()),'teeth_count_unique_parts':sum(len(r['teeth']) for r in reports.values()),'geometry_layout_checks':checks,'physical_release':'NOT TESTED'}
 (O/'verification/release.json').write_text(json.dumps(release,ensure_ascii=False,indent=2),encoding='utf-8')
 with (O/'零件与支撑清单.csv').open('w',encoding='utf-8-sig',newline='') as fo:
  w=csv.writer(fo);w.writerow(['打印盘','盘内对象/原安装编号','零件号','安装部位','支撑分段','连接齿','最小主体间隙mm','打印文件'])
  for p in plates:
   for i in p['items']:
    r=reports[i['id']];w.writerow([p['id'],i['object_name'],i['id'],i['part'],r['support_count'],len(r['teeth']),r['min_gap_mm'],f"projects/{p['id']}_O22F1_PLA_fins.3mf"])
 with zipfile.ZipFile(B/'PoseDoll_O22_Assembly_Guide.zip') as z:
  for n in z.namelist():
   path=Path(n);rel=Path(*path.parts[1:]);dest=O/'assembly'/rel
   if '..' in rel.parts or n.endswith('/'):continue
   dest.parent.mkdir(parents=True,exist_ok=True);data=z.read(n)
   if dest.suffix in ['.html','.md']:
    text=data.decode('utf-8-sig');text=text.replace('../../bench/revO22/a1mini_supports/index.html','../../../index.html')
    text=text.replace('A1 mini · PLA 0.4 mm 易拆支撑工程','O22-F1 支撑鳍打印工程')
    text=text.replace('教程包不重复包含全部打印模型和 KiCad 制造资料，请与已保存的两个原包一起使用。','本套件已包含 O22-F1 的 11 盘支撑鳍打印工程；KiCad 制造资料仍使用原工程包。可选 T01 传感器小样属于原 O22 工程，本次未另作支撑鳍版本。')
    if dest.name=='external-files.html':
     text='<!doctype html><html lang="zh-CN"><meta charset="utf-8"><title>O22-F1 打印与工程文件</title><link rel="stylesheet" href="style.css"><main><h1>打印与工程文件</h1><p>本套件已包含 A01–A10 全部主盘和 S00 试盘。请从 <a href="../../../index.html">支撑鳍彩色三维页</a>下载对应 3MF，不再使用旧自动支撑工程。</p><p>本安装教程包含 26 个步骤、CAD 示意图、可旋转装配模型、五金及接线表。原件编号和安装尺寸均未改变。Gerber、钻孔及原生 PCB 制造文件继续使用已保存的 PoseDoll_O22_Engineering_Package.zip。</p><p><a href="index.html">返回完整安装教程</a></p></main></html>'
    if dest.name=='index.html' and 'assembly-o22' in str(dest):
     text=text.replace('<main>','<main><p style="padding:14px;background:#fff4dc">本副本配套 O22-F1 支撑鳍工程。先按彩色三维页剪断黄色连接齿、移除橙色鳍和底脚，再按下方原编号装配。<a href="../../../index.html">返回支撑识别与打印入口</a></p>')
    data=text.encode('utf-8')
   dest.write_bytes(data)
 print(json.dumps({k:v for k,v in release.items() if k!='geometry_layout_checks'},ensure_ascii=False))
 print('LAYOUT',json.dumps(checks,ensure_ascii=False))
if __name__=='__main__':run()
