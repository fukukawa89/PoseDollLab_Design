"""Validate the assembled tutorial against source inventories; no device IO."""
from pathlib import Path
from html.parser import HTMLParser
from urllib.parse import urlsplit,unquote
from collections import Counter
import hashlib,importlib.util,json,struct,sys,tempfile
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];H=ROOT/'Hardware/PoseDoll44';B=H/'bench/revO22';G=H/'tutorials/assembly-o22'
read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
d=read(G/'guide-data.json');plates=read(B/'a1mini/manifest.json');meta=read(B/'mechanical/assembly_metadata.json')['meta']
expected={i['part']:f"{p['id']}-{i['number']:02}" for p in plates['plates'] if not p['optional'] for i in p['items']}
assert set(expected)==set(d['first_use']) and len(expected)==186
introduced=[k for s in d['steps'] for k in s['new_parts']];assert Counter(introduced)==Counter({k:1 for k in expected})
for k,address in expected.items():assert d['parts'][k]['address']==address
allocated=sum((Counter(s['stock']) for s in d['steps']),Counter());stock=Counter({k:r['net_quantity'] for k,r in d['hardware'].items()});assert allocated==stock
for s in d['steps'][:-1]:
    assert Counter(s['stock'])==Counter(v['sku'] for v in meta.values() if v.get('module')==s['id'] and v.get('sku') in stock)
    assert s['parent']!=s['child'] and set(s['new_parts'])<=set(s['parts'])
assert len(d['routes'])==46 and len({r['connector'] for r in d['routes']})==46
for r in d['routes']:
    assert all(k in d['parts'] for k in r['mounts']+[r['magnet_mount']])
    assert r['cut_length_released'] is False
native=read(G/'evidence/carrier_native_pads.json');comps={c['ref']:c for c in native['components']}
for r in d['routes']:
    c=comps[r['carrier_reference']];pins={p['pin']:p['net'] for p in c['pads']};bank=r['connector'][0]
    assert c['value'].startswith(r['connector']+' ')
    assert [pins[str(i)] for i in range(1,6)]==['GND','SENSOR_3V45','CLK_'+bank,r['connector']+'_DO','CS_'+bank]
assert next(p for p in comps['J2']['pads'] if p['pin']=='7')['net'].startswith('unconnected-')
assert hashlib.sha256((ROOT/native['source']).read_bytes()).hexdigest()==native['sha256']
class Links(HTMLParser):
    def __init__(self):super().__init__();self.ids=set();self.links=[]
    def handle_starttag(self,tag,attrs):
        a=dict(attrs)
        if 'id' in a:self.ids.add(a['id'])
        for name in ('href','src'):
            if name in a:self.links.append(a[name])
p=Links();p.feed((G/'index.html').read_text('utf8'));checked=0
for target in p.links:
    u=urlsplit(target)
    if u.scheme:continue
    if not u.path:
        assert u.fragment in p.ids,target
    else:assert (G/unquote(u.path)).resolve().is_file(),target
    checked+=1
images={}
for s in d['steps']:
    path=G/f"images/{s['step']}.png";raw=path.read_bytes();assert raw[:8]==b'\x89PNG\r\n\x1a\n';w,h=struct.unpack('>II',raw[16:24]);assert w>=750 and h>=400
    images[path.name]={'width':w,'height':h,'sha256':hashlib.sha256(raw).hexdigest()}
# Meaningful protocol checks: partial population is not silently promoted to a valid pose.
sp=importlib.util.spec_from_file_location('o22_diagnostic',G/'tools/usb_diagnostic.py');m=importlib.util.module_from_spec(sp);sp.loader.exec_module(m)
from mt6701 import crc6
routes=read(B/'harness/routing_plan.json')['rows'];words=[0]*46;i=next(r['raw_index'] for r in routes if r['connector']=='A01');payload=8192<<4;words[i]=(payload<<6)|crc6(payload);f={'words':words,'idle_high_mask':1<<i}
r=m.summarize([f],routes,['A01','B01']);assert r[0]['valid_scans']==1 and r[0]['uncalibrated_angle_min_deg']==180
assert r[1]['valid_scans']==0 and r[1]['uncalibrated_angle_min_deg'] is None
bad={**f,'words':words.copy()};bad['words'][i]^=1;r=m.summarize([bad],routes,['A01']);assert r[0]['crc_failures']==1 and r[0]['valid_scans']==0 and r[0]['uncalibrated_angle_min_deg'] is None
with patch('serial.Serial',side_effect=AssertionError('Hardware must not be opened')):
    for ports in [['A15'],['B01','B01']]:
        try:m.run('NOT_A_PORT',ports,1,ROOT/'.local/o22-guide/no-write.json')
        except ValueError:pass
        else:raise AssertionError('Bad requested ports accepted')
archive_hashes={}
for filename,expected_hash in [('PoseDoll_O22_Engineering_Package.zip','9f6a0518602049ae4ba69d32ccc192bacf1fb558c4c6bda3ea55cf3bc35ede62'),('PoseDoll_O22_A1mini_Print_Plates.zip','dee71e377d573b3ae859a8d9ad4441225c30345b11b4a0d8e10184ac399137ea')]:
    h=hashlib.sha256((B/filename).read_bytes()).hexdigest();assert h==expected_hash;archive_hashes[filename]=h
result={'status':'PASS','main_instances':186,'unique_first_use_assignments':len(introduced),'hardware_count':sum(stock.values()),'sensor_routes':46,'native_pins_verified':230,'html_links_checked':checked,'cad_images':images,'diagnostic_checks':['partial A01 valid, missing B01 remains invalid','bad SSI CRC produces no angle','unknown and duplicate requested ports rejected before serial open'],'original_archive_sha256':archive_hashes,'hardware_opened':False,'physical_validation':False}
(G/'evidence/content_validation.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
print(json.dumps({k:v for k,v in result.items() if k not in ['cad_images','original_archive_sha256']},ensure_ascii=False))
