from build_guide import *
from html.parser import HTMLParser
from urllib.parse import urlsplit,unquote
import zipfile

def main():
 data=load(DEST/'steps.json');report=load(DEST/'verification/assembly_paths.json');browser=load(DEST/'verification/browser_review.json');checks=[]
 def ck(n,ok):checks.append(dict(check=n,passed=bool(ok)))
 ck('frozen production geometry',data['geometry_sha256']==EXPECTED and sha(SOURCE/'production_meshes.npz')==EXPECTED)
 ck('all source output fingerprints unchanged',all(sha(H/n)==v for n,v in load(DEST/'source_fingerprints.json').items()))
 ck('all 161 tutorial steps checked against production bodies',report['status']=='PASS_GUIDE_GEOMETRY' and report['geometry_sha256']==EXPECTED and report['steps']==161)
 ck('all 483 browser states and 146 part directions displayed',browser['steps']==161 and browser['render_states']==483 and browser['part_orientations']==146 and not browser['errors'] and browser['final_visible']==146 and browser['final_shoulder_abduction_deg']==45)
 ck('playback controls exercised',all(browser['playback'][n] for n in ['play_moves','pause_stable','replay_moves','continuous_advanced']))
 ck('browser runtime has no errors after repair',browser['console_errors']==0 and not browser['playback']['errors'])
 ck('browser checked these exact viewer assets',all(sha(DEST/n)==v for n,v in browser['asset_sha256'].items()))
 # Inline all rendering assets to provide a network-independent animation file.
 single=(DEST/'index.html').read_text('utf8');single=single.replace('<link rel="stylesheet" href="style.css">','<style>'+(DEST/'style.css').read_text('utf8')+'</style>')
 for n in ['data.js','guide.js','enhance.js']:single=single.replace(f'<script src="{n}"></script>','<script>'+(DEST/n).read_text('utf8')+'</script>')
 offline=DEST/'R2_Assembly_Offline.html';offline.write_text(single,encoding='utf8')
 ck('offline animation contains all rendering code and geometry',not re.search(r'<script\b[^>]*\bsrc=',single) and 'window.ARM_GUIDE=' in single and 'window.GUIDE_API=' in single and not re.search(r'<link\b[^>]*rel="stylesheet"',single))
 class Links(HTMLParser):
  def __init__(self):super().__init__();self.links=[]
  def handle_starttag(self,t,attrs):self.links.extend(v for k,v in attrs if k in ['src','href'] and v)
 missing=[]
 for p in DEST.glob('*.html'):
  h=Links();h.feed(p.read_text('utf8'))
  for link in h.links:
   u=urlsplit(link)
   if not u.scheme and u.path and not (p.parent/unquote(u.path)).exists():missing.append(p.name+': '+link)
 ck('all tutorial links resolve',not missing)
 result=dict(status='PASS_TUTORIAL_DELIVERY' if all(c['passed'] for c in checks) else 'FAIL',geometry_sha256=EXPECTED,checks=checks,missing_links=missing,offline_file_url_test='NOT_EXECUTED: browser automation tool blocks file: protocol; single-file asset completeness verified. HTTP-hosted same viewer and all controls were exercised.',scope='Tutorial release only. No production geometry, mechanical BOM or physical acceptance status changed.')
 put(DEST/'verification/delivery_audit.json',result);print(result['status'],[c for c in checks if not c['passed']],flush=True);assert result['status']=='PASS_TUTORIAL_DELIVERY'
 for n in ['build_guide.py','verify_guide.py','docs_guide.py','package_guide.py','index.html','style.css','guide.js','enhance.js']:shutil.copyfile(HERE/n,DEST/'source'/n)
 readme=(DEST/'README.txt').read_text('utf8');readme=readme.replace('打开 index.html 即可离线使用，不需要联网；解压后请保持同目录文件完整。','解压后可双击 R2_Assembly_Offline.html 打开单文件动画；index.html 为同内容分文件入口。\n动画的代码和模型已全部内嵌，不依赖联网；文字卡仍在同一目录。自动化工具禁止file:协议，未执行双击文件的浏览器实测；本机HTTP页面和播放控制已实测。')
 (DEST/'README.txt').write_text(readme,encoding='utf8')
 files=[p for p in DEST.rglob('*') if p.is_file() and p.suffix not in ['.zip','.pyc'] and p.name not in ['checksums.json','package_audit.json'] and '__pycache__' not in p.parts];put(DEST/'checksums.json',{p.relative_to(DEST).as_posix():sha(p) for p in files});files.append(DEST/'checksums.json');target=DEST/'O24E_R2_Arm_Assembly_Tutorial.zip'
 with zipfile.ZipFile(target,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as out:
  for p in sorted(files):out.write(p,p.relative_to(DEST).as_posix())
 with zipfile.ZipFile(target) as z:
  bad=z.testzip();m=json.loads(z.read('checksums.json'));match=all(hashlib.sha256(z.read(n)).hexdigest()==v for n,v in m.items())
 audit=dict(status='PASS_PACKAGE' if bad is None and match else 'FAIL',files=len(files),bytes=target.stat().st_size,sha256=sha(target),crc_error=bad,all_manifest_hashes_match=match);put(DEST/'verification/package_audit.json',audit);print(audit,flush=True);assert audit['status']=='PASS_PACKAGE'
if __name__=='__main__':main()
