"""Verify the release inventory and local links, then checksum and archive it."""
from pathlib import Path
import hashlib,json,csv,zipfile,re,collections
from urllib.parse import urlsplit,unquote
from html.parser import HTMLParser
from publish_revo22_f5_compact302 import D

def sha(p):
 h=hashlib.sha256()
 with p.open('rb')as f:
  for chunk in iter(lambda:f.read(1024*1024),b''):h.update(chunk)
 return h.hexdigest()
class Links(HTMLParser):
 def __init__(self):super().__init__();self.urls=[]
 def handle_starttag(self,tag,attrs):
  for k,v in attrs:
   if k in ['href','src']and v:self.urls.append(v)
def run():
 m=json.loads((D/'manifest.json').read_text());assert m['complete']and len(m['rows'])==150;assert m['main_instances']==186 and m['sample_instances']==7
 rows=list(csv.DictReader((D/'零件与打印盘对照.csv').open(encoding='utf-8-sig',newline='')));assert len(rows)==193;assert len({r['address']for r in rows})==193
 assert sha(D/'parts/X062.npz')=='4c83dc08a2fa297821dbfa4ec6f43e4a05763b8386736d3e919957c4e726c765'
 for p in m['plates']:
  assert sha(D/p['project'])==p['project_sha256'];proof=json.loads((D/p['proof']).read_text());assert proof['native_clear']and proof['external_islands']==0 and proof['critical_external_runs']==0
 for row in m['rows']:
  p=row['id'];assert (D/'geometry'/f'{p}_candidate.js').exists()and(D/'records'/f'{p}.js').exists();g=json.loads((D/'verification/parts'/p/'f5_geometry.json').read_text());assert g['geometric_constraints_passed']and g['parts_npz_sha256']==sha(D/'parts'/f'{p}.npz')
 files=sorted(p for p in D.rglob('*')if p.is_file()and p.name!='SHA256SUMS.txt');lines=[sha(p)+'  '+p.relative_to(D).as_posix()for p in files];(D/'SHA256SUMS.txt').write_text('\n'.join(lines)+'\n','utf-8')
 failures=[]
 for p in D.rglob('*.html'):
  parser=Links();parser.feed(p.read_text(encoding='utf-8-sig'))
  for u in parser.urls:
   v=urlsplit(u)
   if v.scheme or not v.path:continue
   target=(p.parent/unquote(v.path)).resolve()
   if not target.exists():failures.append([str(p.relative_to(D)),u])
 assert not failures,failures

 zpath=D.parent/'O22F5_Compact_PrintPack.zip'
 with zipfile.ZipFile(zpath,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=5,allowZip64=True)as z:
  for p in sorted(q for q in D.rglob('*')if q.is_file()):z.write(p,D.name+'/'+p.relative_to(D).as_posix(),compress_type=zipfile.ZIP_STORED if p.suffix in ['.3mf','.npz','.png','.jpg']else zipfile.ZIP_DEFLATED)
 with zipfile.ZipFile(zpath)as z:
  assert z.testzip()is None
  for line in lines:
   expected,name=line.split('  ',1);assert hashlib.sha256(z.read(D.name+'/'+name)).hexdigest()==expected,name
 report=dict(path=str(zpath),sha256=sha(zpath),bytes=zpath.stat().st_size,files=len(files)+1,main_plates=m['main_plate_count'],optional_plates=m['sample_plate_count'],types=150,instances=193,all_local_html_links_exist=True,zip_integrity=True);(D.parent/'O22F5_Compact_PrintPack.integrity.json').write_text(json.dumps(report,ensure_ascii=False,indent=2));print('FINAL375',json.dumps(report),flush=True)
if __name__=='__main__':run()
