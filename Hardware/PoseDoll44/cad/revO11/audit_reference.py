from pathlib import Path
import json,zipfile,hashlib,urllib.request,xml.etree.ElementTree as ET
from html.parser import HTMLParser
H=Path(__file__).resolve().parents[2];out=H/'research/revO11';out.mkdir(exist_ok=True)
class Table(HTMLParser):
 def __init__(self):super().__init__();self.rows=[];self.row=None;self.cell=None
 def handle_starttag(self,t,a):
  if t=='tr':self.row=[]
  if t in ('td','th') and self.row is not None:self.cell=[]
 def handle_data(self,d):
  if self.cell is not None:self.cell.append(d)
 def handle_endtag(self,t):
  if t in ('td','th') and self.cell is not None:self.row.append(' '.join(''.join(self.cell).split()));self.cell=None
  if t=='tr' and self.row is not None:
   if any(self.row):self.rows.append(self.row)
   self.row=None
base='https://docs.google.com/spreadsheets/d/e/2PACX-1vQmoxJnTnUaQ_-WAAjnchBhaX5HZ4ElUV5pXksEV6GEbeEjiie1E_BdN9XCMt6FtfBaopXoaeSOeMDg/pubhtml/sheet?headers=false&gid='
tabs=[]
for name,gid in [('Release','738469501'),('Screws','2047113766')]:
 url=base+gid;data=urllib.request.urlopen(url,timeout=40).read();parser=Table();parser.feed(data.decode('utf-8'))
 tabs.append(dict(name=name,url=url,sha256=hashlib.sha256(data).hexdigest(),rows=parser.rows))
 print(name,len(parser.rows));print('\n'.join(' | '.join(r) for r in parser.rows if any(s in ' '.join(r).lower() for s in ('bearing','shaft','washer','filament'))))
(out/'toddlerbot_bom_readonly.json').write_text(json.dumps({'retrieved_date':'2026-09-26','tabs':tabs},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
p=H.parents[3]/'ToddlerbotV2.0_sliced_2xc_V1+.3mf'
with zipfile.ZipFile(p) as z:
 config=json.loads(z.read('Metadata/project_settings.config'));root=ET.fromstring(z.read('Metadata/model_settings.config'));objects=[]
 for obj in root.findall('object'):
  m={x.attrib['key']:x.attrib.get('value') for x in obj.findall('metadata') if 'key' in x.attrib}
  objects.append({'id':obj.attrib['id'],**{k:v for k,v in m.items() if k in ('name','extruder','sparse_infill_density','wall_loops','layer_height')}})
 keep=['printer_model','printer_settings_id','filament_settings_id','nozzle_diameter','layer_height','wall_loops','sparse_infill_density','sparse_infill_pattern','top_shell_layers','bottom_shell_layers']
 result={'source_file':p.name,'file_sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'zip_members':len(z.infolist()),'project_settings':{k:config.get(k) for k in keep},'objects':objects,'note':'Settings only, no print performed. Per-object overrides take precedence. Personal source paths omitted.'}
(out/'toddlerbot_3mf_audit.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');print('3mf objects',len(objects))

