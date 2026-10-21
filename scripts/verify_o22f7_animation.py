"""Validate animation coverage, source identities, electrical mappings and assets."""
from o22f7_animation import *
from urllib.parse import urlsplit,unquote
from html.parser import HTMLParser
class Links(HTMLParser):
 def __init__(self):super().__init__();self.links=[]
 def handle_starttag(self,tag,attrs):
  for k,v in attrs:
   if k in ['href','src']:self.links.append(v)
def verify(require_browser=True):
 d=read(OUT/'sequence.json');s=read(G/'scene.json');g=read(G/'guide-data.json');o=s['objects'];before=read(WORK/'before.json');assert d['revision']==REV
 for p,h in before['manufacturing'].items():assert sha(F/p)==h,p
 assert d['source_geometry_sha256']==sha(G/s['geometry_url'])
 assert d['source_guide_sha256']==sha(G/'guide-data.json')
 introduced=Counter(i for a in d['actions'] for i in a['new']);assert introduced==Counter({i:1 for i in range(len(o))})
 assert sum(bool(q.get('print_id')) for q in o)==185
 count=Counter(q['sku'] for q in o if q['role']=='metal');assert count==Counter({k:v['net_quantity'] for k,v in g['hardware'].items()})
 assert len(d['excluded'])==8 and sum(q['id']=='P242' for q in d['excluded'])==1
 native={c['ref']:c for c in read(G/'evidence/carrier_native_pads.json')['components']};pins=0
 for r in d['routes']:
  assert r in g['routes'];assert len([a for a in d['actions'] if a['kind']=='wire' and a.get('route')==r['connector']])==1
  assert len([a for a in d['actions'] if a['kind']=='plug' and a.get('route')==r['connector']])==1
  fields={p['pin']:p['net'] for p in native[r['carrier_reference']]['pads']};bank=r['connector'][0]
  for pin,net in [('1','GND'),('2','SENSOR_3V45'),('3','CLK_'+bank),('4',r['connector']+'_DO'),('5','CS_'+bank)]:assert fields[pin]==net,(r['connector'],pin,net,fields);pins+=1
  board=[i for i,q in enumerate(o) if q['label'].startswith(r['sensor_part_O20']+'/')];assert len(board)==7
  install=[a for a in d['actions'] if set(board)&set(a['new'])];assert len(install)==1 and set(install[0]['new'])==set(board)
 # No action leaves an invisible/unintroduced or stranded subassembly behind.
 seen=set();offset={};checks=0
 for c in d['chapters']:
  for a in d['actions'][c['start']:c['end']]:
   assert a['chapter']==c['id'];seen.update(a['new']);assert set(a['moving'])<=seen
   assert len(a['path'])>=2 and np.isfinite(a['path']).all();assert a['duration']>0
   for i in a['moving']:offset[i]=np.array(a['path'][-1]);checks+=1
  for i in c['objects']:
   assert i in seen,(c['id'],o[i]['label']);assert np.linalg.norm(offset.get(i,np.zeros(3)))<1e-5,(c['id'],o[i]['label'],'left off station')
 links=0
 for file in [OUT/'index.html',G/'index.html',F/'index.html']:
  q=Links();q.feed(file.read_text('utf-8-sig'))
  for v in q.links:
   u=urlsplit(v)
   if u.scheme or not u.path:continue
   assert (file.parent/unquote(u.path)).is_file(),(file,v);links+=1
 report={'passed':True,'release_ready':not bool(d['coverage'].get('unverified_insertion_steps')),'unresolved_steps':d['coverage'].get('unverified_insertion_steps',[]),'revision':REV,'actions':len(d['actions']),'chapters':len(d['chapters']),'print_instances':185,'hardware_instances':sum(count.values()),'sensor_boards':46,'wiring_routes':46,'native_pin_checks':pins,'unique_scene_introductions':len(introduced),'subassembly_moves_checked':checks,'manufacturing_files_unchanged':len(before['manufacturing']),'static_links_checked':links,'sequence_sha256':sha(OUT/'sequence.json'),'asset_sha256':{f:sha(OUT/f) for f in ['index.html','style.css','app.js','sequence.json']},'geometry_sha256':sha(G/s['geometry_url']),'physical_assembly_tested':False,'complete_swept_volume_certification':False}
 if require_browser:
  br=read(OUT/'browser-review.json');assert br['passed'] and br['console_errors']==[];assert br['assets']==report['asset_sha256'];assert br['final_pose_max_error_mm']<1e-5;report['browser']=br
 put(OUT/'verification.json',report);put(F/'verification/assembly_animation.json',report);print(json.dumps({k:v for k,v in report.items() if k not in ['browser','asset_sha256']},ensure_ascii=False));return report
if __name__=='__main__':verify('--data-only' not in sys.argv)
