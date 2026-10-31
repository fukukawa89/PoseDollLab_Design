"""Validate the current tutorial against native projects and unchanged release files."""
from pathlib import Path
from collections import Counter
from html.parser import HTMLParser
from urllib.parse import urlsplit,unquote
import hashlib,json,re,struct,zipfile
import xml.etree.ElementTree as ET
import numpy as np
import o22f7_assembly_guide as g
read=g.read;sha=g.sha;put=g.put;F=g.F;G=g.G

class Links(HTMLParser):
    def __init__(self):super().__init__();self.ids=set();self.links=[];self.text=[]
    def handle_starttag(self,tag,attrs):
        a=dict(attrs)
        if 'id' in a:self.ids.add(a['id'])
        for name in ('href','src'):
            if name in a:self.links.append(a[name])
    def handle_data(self,data):self.text.append(data)

def verify():
    d=read(G/'guide-data.json');m=read(F/'manifest.json');before=read(g.WORK/'before.json')
    assert sha(F/'manifest.json')==before['manifest_sha256'],'Manufacturing manifest changed'
    for path,h in before['mechanical_files'].items():assert sha(F/path)==h,path
    native=[];expected={}
    for p in m['plates']:
        with zipfile.ZipFile(F/p['project']) as z:
            root=ET.fromstring(z.read('Metadata/model_settings.config'));names=[o.find("metadata[@key='name']").get('value') for o in root.findall('object')]
        assert Counter(names)==Counter(q['object_name'] for q in p['items'])
        assert d['native_project_sha256'][p['project']]==sha(F/p['project'])
        native.extend(names)
        for i in p['items']:
            a=f"{p['id']}-{i['number']:02}"
            expected[a]=(i['id'],i['part'],bool(i['optional_sample']))
    actual={i['address']:(i['id'],i['part'],i['optional']) for i in d['instances']}
    assert expected==actual and len(actual)==193 and len(native)==193
    assert len(d['plates'])==14 and [p['id'] for p in d['plates']]==[f'D{i:02}' for i in range(1,15)]
    assert len(d['parts'])==186 and len({i['id'] for i in d['instances']})==150
    assert sum(i['optional'] for i in d['instances'])==7
    for k,q in d['parts'].items():assert expected[q['address']]==(q['id'],k,False)
    introduced=Counter(k for s in d['steps'] for k in s['new_parts'])
    assert introduced==Counter({k:1 for k in d['parts']})
    for s in d['steps']:
        assert s['plates']==sorted({d['parts'][k]['plate'] for k in s['parts']})
        assert all(d['first_use'][k]==s['step'] for k in s['new_parts'])
    stock=sum((Counter(s['stock']) for s in d['steps']),Counter());assert stock==Counter({k:r['net_quantity'] for k,r in d['hardware'].items()})
    assert sum(stock.values())==958
    original=read(g.base.H/'tutorials/assembly-o22/guide-data.json')
    assert d['routes']==original['routes'] and d['pin_order']==original['pin_order'] and d['hardware']==original['hardware']
    assert len(d['routes'])==46 and len({r['connector'] for r in d['routes']})==46
    for route in d['routes']:assert set(route['mounts']+[route['magnet_mount']])<=set(d['parts'])
    linkcount=0;visible=[];id_cache={}
    for path in G.glob('*.html'):
        parser=Links();parser.feed(path.read_text('utf8'));visible+=parser.text
        for target in parser.links:
            u=urlsplit(target)
            if u.scheme:continue
            dest=(path.parent/unquote(u.path)).resolve() if u.path else path.resolve()
            assert dest.is_relative_to(F.resolve()),(path.name,target,'outside package')
            assert dest.is_file(),(path.name,target,'missing')
            if u.fragment and dest.suffix=='.html':
                if dest not in id_cache:
                    t=Links();t.feed(dest.read_text('utf-8-sig'));id_cache[dest]=t.ids
                assert u.fragment in id_cache[dest],(path.name,target,'missing anchor')
            linkcount+=1
    text='\n'.join(visible)+'\n'+(G/'ASSEMBLY.zh-CN.md').read_text('utf8')
    assert not re.search(r'盘 A\d{2}|A\d{2}-\d{2}|原始分组|原 10 盘|原始 CAD 已载入',text)
    for p in d['plates']:
        assert (G/p['preview']).is_file()
        assert p['count']==len(p['items'])
    models=read(G/'evidence/current_body_meshes.json');scene=read(G/'scene.json')
    assert sha(G/scene['geometry_url'])==scene['geometry_sha256']
    assert len(models['rows'])==185
    by={o['label']:o for o in scene['objects']};original_scene=read(g.base.H/'tutorials/assembly-o22/scene.json');original_by={o['label']:o for o in original_scene['objects']}
    for q in models['rows']:
        assert sha(F/f"parts/{q['id']}.npz")==q['npz_sha256']
        assert q['float32_roundtrip_max_mm']<.0001
        o=by[q['part']];assert o['address']==q['address'] and o['print_id']==q['id']
        assert o['matrix']==original_by[q['part']]['matrix'],'Assembly placement changed'
        assert scene['meshes'][o['mesh']]['count']==q['triangle_count']*3
    images={}
    for s in d['steps']:
        p=G/f"images/{s['step']}.png";raw=p.read_bytes();assert raw[:8]==b'\x89PNG\r\n\x1a\n';w,h=struct.unpack('>II',raw[16:24]);assert w>=750 and h>=400
        images[s['step']]={'sha256':sha(p),'width':w,'height':h}
    capture=read(G/'evidence/browser_review.json');assert capture['passed'] and capture['step_images']==26 and capture['revision']==g.REV
    assert capture['console_errors']==0 and capture['console_warnings']==0
    assert capture['html_sha256']==sha(G/'index.html') and capture['guide_data_sha256']==sha(G/'guide-data.json')
    assert capture['geometry_sha256']==scene['geometry_sha256']
    assert capture['step_images_sha256']=={k:v['sha256'] for k,v in images.items()}
    old=read(G/'verification.json')
    report={'status':'PASS','revision':g.REV,'scope':'Current native plate inventory, assembly body mesh, part/step mappings, links and browser interaction; no physical assembly claims.','main_plates':14,'main_print_instances':186,'on_doll_print_instances':185,'assembly_tools':1,'optional_sample_instances':7,'print_types':150,'unique_native_instances_checked':193,'joint_steps':25,'controller_steps':1,'stock_instances_including_magnets':958,'magnet_instances':46,'sensor_routes':46,'electrical_routes_hardware_and_pin_order_unchanged':True,'native_connector_pin_checks':230,'mechanical_files_unchanged':len(before['mechanical_files']),'native_project_sha256':d['native_project_sha256'],'manifest_sha256':sha(F/'manifest.json'),'local_html_links_and_anchors_checked':linkcount,'current_body_instances':185,'step_images':images,'physical_assembly_verified':False}
    put(G/'verification.json',report);put(G/'evidence/content_validation.json',report);put(F/'verification/assembly_guide.json',report)
    print(json.dumps({k:v for k,v in report.items() if k not in ['step_images','native_project_sha256']},ensure_ascii=False))
    return report

if __name__=='__main__':verify()
