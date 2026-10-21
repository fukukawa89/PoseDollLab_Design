"""Reseal the O22F7 package after the animated assembly tutorial is verified."""
from o22f7_animation import *
from verify_o22f7_animation import verify
from verify_o22f7_assembly_guide import verify as verify_reference
import zipfile,re
from urllib.parse import urlsplit,unquote

def release():
 report=verify();verify_reference();d=read(OUT/'sequence.json');assert not d['coverage'].get('unverified_insertion_steps'), 'Unverified insertion steps must not be released as a final tutorial';before=read(WORK/'before.json')
 assert sha(WORK/'r2_package.zip')==before['archive_sha256']
 for name in ['o22f7_animation.py','verify_o22f7_animation.py','release_o22f7_animation.py','check_o22f7_animation_browser.js','check_o22f7_animation_paths.py','check_o22f7_animation_magnets.py','o22f7_preview.py']:
  shutil.copy2(R/'scripts'/name,F/'verification'/name)
 for name in ['core_paths.json','magnet_paths.json']:
  if (WORK/name).is_file():shutil.copy2(WORK/name,OUT/name)
 rel=read(F/'RELEASED.json');rel.update(assembly_tutorial_revision=REV,assembly_tutorial='assembly/tutorials/assembly-o22/animation/index.html',assembly_reference='assembly/tutorials/assembly-o22/index.html',assembly_animation_verification='verification/assembly_animation.json',manufacturing_files_unchanged_in_tutorial_update=True);put(F/'RELEASED.json',rel)
 note=f'''O22F7 逐件拼装动画 · r3 · 2026-10-16

双击“打开逐件拼装动画.cmd”。也可从根目录 index.html 的“逐件拼装动画”进入。
原来的“O22F7 人偶拼装教程”页面顶部也有动画入口，图文清单继续保留。

26 章，{len(d['actions'])} 个动作。每件装机打印件和每件五金、磁铁分别展示；可暂停、慢放、重播、回退、跳转及搜索盘位。
185 件打印装机件、958 件五金与磁铁、46 块预焊传感板、1 套中央成品板与 XIAO、46 路接线、2 根背盖扎带纳入流程。
1 件工厂焊接量规与 7 件可选小样单独说明，不额外装到人偶上。

本次不包含拆支撑动画。以打印件已清理、工厂已焊接并检测好电路板和线束为起点。
电路部分包含磁铁与芯片朝向、传感板装入、局部固线、关节处留线、五针方向、逐路接到实际中央板插座及分段通电检查。
默认每步播放后暂停，装好后点“下一步”；“连续观看”可先看完整流程。

本次只更新教程。14 个 PLA 打印工程及本体、支撑设计均未改变。
模型、清单、最终位置及电路映射已经数字核对。装配动画不是打印公差、弹舌弹性、胶固化、完整扫掠体或电气实测的认证。
遇到卡住先停止施力，对照具体检查点排查；检查记录只有你主动勾选才会记为已检查。
'''
 write(F/'教程更新说明.txt',note)
 put(F/'assembly/archive_manifest.json',{'schema':'POSEDOLL-O22F7-ASSEMBLY-ARCHIVE/3','revision':REV,'files':{p.relative_to(F/'assembly').as_posix():sha(p) for p in sorted((F/'assembly').rglob('*')) if p.is_file() and p.name!='archive_manifest.json' and '__pycache__' not in p.parts}})
 bad=[];links=0
 for p in F.rglob('*.html'):
  for target in re.findall(r'(?:href|src)=[\"\']([^\"\']+)',p.read_text('utf-8-sig')):
   u=urlsplit(target)
   if u.scheme or '${' in target or not u.path:continue
   links+=1
   if not (p.parent/unquote(u.path)).is_file():bad.append((str(p.relative_to(F)),target))
 assert not bad,bad;put(F/'verification/asset_links.json',{'passed':True,'local_links_checked':links,'assembly_revision':REV})
 files=sorted(p for p in F.rglob('*') if p.is_file() and p.name!='SHA256SUMS.txt' and '__pycache__' not in p.parts);checks={p.relative_to(F).as_posix():sha(p) for p in files};write(F/'SHA256SUMS.txt',''.join(h+'  '+k+'\n' for k,h in checks.items()))
 staged=WORK/'updated_animation_package.zip';target=B/'O22F7_PLA_完整打印包_20261016.zip'
 with zipfile.ZipFile(staged,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
  for p in files+[F/'SHA256SUMS.txt']:z.write(p,p.relative_to(F).as_posix())
 with zipfile.ZipFile(staged) as z:
  assert z.testzip() is None;assert set(z.namelist())==set(checks)|{'SHA256SUMS.txt'}
  for k,h in checks.items():assert hashlib.sha256(z.read(k)).hexdigest()==h,k
 assert target.resolve().parent==B.resolve();shutil.copy2(staged,target);h=sha(target);write(target.with_suffix('.zip.sha256'),h+'  '+target.name+'\n')
 delivered={'complete':True,'archive':str(target),'bytes':target.stat().st_size,'sha256':h,'files':len(checks)+1,'revision':REV,'previous_archive_backup':str(WORK/'r2_package.zip'),'every_archived_file_verified':True,'print_files_unchanged':True};put(WORK/'delivery.json',delivered);put(WORK.parent/'delivery.json',delivered);print(json.dumps(delivered,ensure_ascii=False))
if __name__=='__main__':release()
