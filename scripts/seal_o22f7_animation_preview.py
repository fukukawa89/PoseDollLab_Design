"""Seal a clearly labeled animation preview without replacing the r2 print archive."""
from o22f7_animation import *
from verify_o22f7_animation import verify
from verify_o22f7_assembly_guide import verify as verify_reference
import zipfile,re
from urllib.parse import urlsplit,unquote

def preview():
 report=verify();verify_reference();d=read(OUT/'sequence.json');before=read(WORK/'before.json')
 original=B/'O22F7_PLA_完整打印包_20261016.zip'
 assert sha(original)==before['archive_sha256']
 assert sha(WORK/'r2_package.zip')==before['archive_sha256']
 assert report['unresolved_steps']==['S04','S11'] and not report['release_ready']
 rel=read(F/'RELEASED.json')
 rel['assembly_animation']={'status':'PREVIEW_TWO_INSERTION_PATHS_UNVERIFIED','revision':REV,'entry':'assembly/tutorials/assembly-o22/animation/index.html','verification':'verification/assembly_animation.json','unresolved_steps':['S04','S11'],'complete':False,'print_files_unchanged':True}
 put(F/'RELEASED.json',rel)
 for name in ['o22f7_animation.py','verify_o22f7_animation.py','check_o22f7_animation_browser.js','check_o22f7_animation_paths.py','check_o22f7_animation_magnets.py','check_o22f7_animation_hinges.py','seal_o22f7_animation_preview.py']:
  shutil.copy2(R/'scripts'/name,F/'verification'/name)
 for name in ['core_paths.json','magnet_paths.json','hinge_paths.json']:
  shutil.copy2(WORK/name,OUT/name)
 core=read(WORK/'core_paths.json');mag=read(WORK/'magnet_paths.json');hinge=read(WORK/'hinge_paths.json')
 assert len(mag['solutions'])==46 and all(v==1 for v in mag['solutions'].values())
 put(OUT/'path-review.json',{'status':'PARTIAL_SAMPLED_CHECKS','unresolved_steps':['S04','S11'],'full_swept_volume_verified':False,'physical_assembly_tested':False,'core_path_records':len(core['rows']),'magnet_holder_paths':46,'hinge_frame_paths_found':14,'scope':'Only the specified moving parts and listed obstacles were sampled. The two clavicle frame entry motions were not resolved. Search failure is not proof of physical impossibility. Flexible parts, cable motions, manufacturing tolerance and all other assembly trajectories are not certified by these checks.','sequence_sha256':sha(OUT/'sequence.json')})
 write(OUT/'预览说明.txt','''O22F7 逐件拼装动画 · 校核预览

本预览共有 26 章、1650 个动作。185 件装机打印件、958 件五金与磁铁、46 块预焊传感板和中央成品板均有相应动作。电路包含 46 路接线、插头方向、活动留线与分段通电检查，不包含拆支撑动画。

尚未完成的两步：S04 左锁骨前后、S11 右锁骨前后连接件的装入路线。
直线装入会与胸架碰撞。尚未确认出可靠的完整绕入动作；并不据此断言实物一定装不进去。
这两步只展示最终位置并暂停，其他步骤可跳转查看。必须确认实际装法后，才能补全最终教程。

默认每步暂停，可慢放、重播、回退、搜索零件或盘位。图文页和当前 D01–D14 取件盘图保持可用。
本次没有改动打印零件或人偶功能，也没有替换原来的完整打印 ZIP。
数字核对与网页检查不代替实物装配和电气验收。
''')
 put(F/'assembly/archive_manifest.json',{'schema':'POSEDOLL-O22F7-ASSEMBLY-ARCHIVE/3-PREVIEW','revision':REV,'status':d['status'],'unresolved_steps':['S04','S11'],'files':{p.relative_to(F/'assembly').as_posix():sha(p) for p in sorted((F/'assembly').rglob('*')) if p.is_file() and p.name!='archive_manifest.json' and '__pycache__' not in p.parts}})
 bad=[];links=0
 for p in F.rglob('*.html'):
  for target in re.findall(r'(?:href|src)=[\"\']([^\"\']+)',p.read_text('utf-8-sig')):
   u=urlsplit(target)
   if u.scheme or '${' in target or not u.path:continue
   links+=1
   if not (p.parent/unquote(u.path)).is_file():bad.append((str(p.relative_to(F)),target))
 assert not bad,bad
 put(F/'verification/asset_links.json',{'passed':True,'local_links_checked':links,'assembly_animation_status':d['status']})
 files=sorted(p for p in F.rglob('*') if p.is_file() and p.name!='SHA256SUMS.txt' and '__pycache__' not in p.parts)
 checks={p.relative_to(F).as_posix():sha(p) for p in files}
 write(F/'SHA256SUMS.txt',''.join(h+'  '+k+'\n' for k,h in checks.items()))
 target=B/'O22F7_拼装动画校核预览_20261016.zip'
 assert target.resolve().parent==B.resolve() and target.resolve()!=original.resolve()
 with zipfile.ZipFile(target,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
  for p in files+[F/'SHA256SUMS.txt']:z.write(p,p.relative_to(F).as_posix())
 print('Preview archive written. Verifying every file.',flush=True)
 with zipfile.ZipFile(target) as z:
  assert z.testzip() is None
  assert set(z.namelist())==set(checks)|{'SHA256SUMS.txt'}
  for k,h in checks.items():assert hashlib.sha256(z.read(k)).hexdigest()==h,k
 assert sha(original)==before['archive_sha256']
 h=sha(target);write(target.with_suffix('.zip.sha256'),h+'  '+target.name+'\n')
 delivered={'status':'PREVIEW','complete':False,'unresolved_steps':['S04','S11'],'archive':str(target),'bytes':target.stat().st_size,'sha256':h,'files':len(checks)+1,'revision':REV,'original_complete_print_archive_unchanged':True,'original_archive_sha256':before['archive_sha256'],'every_archived_file_verified':True,'print_files_unchanged':True}
 put(WORK/'preview_delivery.json',delivered);print(json.dumps(delivered,ensure_ascii=False),flush=True)
if __name__=='__main__':preview()
