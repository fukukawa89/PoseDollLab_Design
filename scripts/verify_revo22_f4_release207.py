"""Validate self-contained release, identities, native bytes, and build a checked ZIP only when complete."""
from pathlib import Path
from html.parser import HTMLParser
from urllib.parse import urlsplit,unquote
import sys,json,hashlib,zipfile
R=Path(__file__).resolve().parents[1];B=R/'Hardware/PoseDoll44/bench/revO22';D=B/'O22F4_Release'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def verify(archive=None):
 m=json.loads((D/'manifest.json').read_text());assert m['complete']and m['main_instances']==186 and m['sample_instances']==7 and m['type_count']==150
 broken=[]
 class Links(HTMLParser):
  def handle_starttag(self,tag,attrs):
   for k,v in attrs:
    if k not in ['src','href']or not v:continue
    u=urlsplit(v)
    if u.scheme or u.netloc or not u.path:continue
    if not (self.path.parent/unquote(u.path)).resolve().exists():broken.append([str(self.path.relative_to(D)),v])
 for p in D.rglob('*.html'):
  h=Links();h.path=p;h.feed(p.read_text(encoding='utf-8-sig'))
 assert not broken,broken
 addresses=[];native=[]
 for p in m['plates']:
  path=D/p['project'];assert sha(path)==p['project_sha256'];proof=json.loads((D/p['proof']).read_text());assert proof['native_clear']and proof['project_sha256']==p['project_sha256'];assert proof['external_islands']==0 and proof['critical_external_runs']==0
  with zipfile.ZipFile(path)as z:
   assert z.testzip()is None;s=json.loads(z.read('Metadata/project_settings.config'));assert s['enable_support']=='0';assert any(n.endswith('.gcode')for n in z.namelist())
  addresses.extend(i['object_name'].split()[0]for i in p['items']);native.append({'plate':p['id'],'file':p['project'],'sha256':p['project_sha256']})
 assert len(addresses)==193 and len(set(addresses))==193
 for row in m['rows']:
  pid=row['id'];assert sha(D/'parts'/f'{pid}.npz')==row['npz_sha256'];g=json.loads((D/row['geometry_proof']).read_text());assert g['npz_sha256']==row['npz_sha256']and g['geometric_constraints_passed'];assert g['fin_body_overlap_mm3']<=1e-6
  if row['body_changed']:
   f=json.loads((D/'verification/parts'/pid/'body_change_fit_and_pose.json').read_text());assert f['fit_and_pose_geometry_passed']
 result={'complete':True,'type_count':150,'main_instances':186,'optional_instances':7,'main_and_optional_addresses_unique':True,'all_html_local_links_resolve':True,'all_native_3mf_hashes_match_frozen_audits':True,'all_native_support_generation_disabled':True,'all_native_projects_contain_gcode':True,'all_part_files_match_geometry_certificates':True,'physical_print_tested':False,'native_projects':native};(D/'verification/release_integrity207.json').write_text(json.dumps(result,indent=2))
 sums={str(p.relative_to(D)).replace('\\','/'):sha(p)for p in sorted(D.rglob('*'))if p.is_file()and p.name!='SHA256SUMS.txt'};(D/'SHA256SUMS.txt').write_text(''.join(v+'  '+k+'\n'for k,v in sums.items()),encoding='utf8');archive=Path(archive) if archive is not None else B/'O22F4_手工支撑鳍_完整包.zip'
 with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED,compresslevel=6)as z:
  for p in sorted(D.rglob('*')):
   if p.is_file():z.write(p,str(Path(D.name)/p.relative_to(D)))
 with zipfile.ZipFile(archive)as z:
  assert z.testzip()is None
  for name,value in sums.items():assert hashlib.sha256(z.read(D.name+'/'+name)).hexdigest()==value,name
 print('RELEASE_VERIFIED',len(m['plates']),'plates',len(sums),'files',archive,'bytes',archive.stat().st_size,'sha256',sha(archive),flush=True)
if __name__=='__main__':verify()
