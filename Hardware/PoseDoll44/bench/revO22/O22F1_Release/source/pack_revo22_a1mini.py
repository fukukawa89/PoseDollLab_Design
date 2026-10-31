"""Pack the unchanged O22 source meshes onto A1 mini plates by body region.

All coordinates remain millimetres. Only XY translation and 0/90 degree Z
rotation are allowed; quantity comes from instances, never from unique IDs.
"""
from __future__ import annotations
import argparse, collections, copy, hashlib, html, json, math, random, zipfile
import xml.etree.ElementTree as ET
from pathlib import Path
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / 'Hardware/PoseDoll44/bench/revO22'
OUT = BASE / 'a1mini'
NS = 'http://schemas.microsoft.com/3dmanufacturing/core/2015/02'
Q = '{' + NS + '}'
GAP = 6.0
EDGE = 6.0
BED = 180.0
LIMIT = BED - 2 * EDGE + GAP
LABELS = {'torso': '躯干', 'head': '头颈', 'arm_l': '左臂', 'arm_r': '右臂', 'leg_l': '左腿', 'leg_r': '右腿', 'test': '传感器小样'}
COLORS = {'torso': '#ae7649', 'head': '#9a675b', 'arm_l': '#477d73', 'arm_r': '#45738f', 'leg_l': '#667e4e', 'leg_r': '#82649a', 'test': '#71818a'}

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def region(part):
    s = part.removeprefix('frame/')
    for side in ('l', 'r'):
        if any(s.startswith(j + '_' + side) for j in ('clavicle', 'upperarm', 'elbow', 'forearm', 'hand')):
            return 'arm_' + side
        if any(s.startswith(j + '_' + side) for j in ('thigh', 'calf', 'foot', 'ball')):
            return 'leg_' + side
    return 'head' if s.startswith('head') else 'torso'

def read_mesh(path):
    with zipfile.ZipFile(path) as z:
        root = ET.fromstring(z.read('3D/3dmodel.model'))
    assert root.attrib.get('unit') == 'millimeter', path
    objects = root.findall(Q + 'resources/' + Q + 'object')
    build = root.findall(Q + 'build/' + Q + 'item')
    assert len(objects) == len(build) == 1 and 'transform' not in build[0].attrib, path
    obj = objects[0]
    v = np.array([[float(n.attrib[k]) for k in ('x', 'y', 'z')] for n in obj.findall('.//' + Q + 'vertex')])
    f = np.array([[int(n.attrib[k]) for k in ('v1', 'v2', 'v3')] for n in obj.findall('.//' + Q + 'triangle')], dtype=np.int64)
    assert np.isfinite(v).all() and f.min() >= 0 and f.max() < len(v), path
    return v, f

def volume(v, f):
    a, b, c = v[f].transpose((1, 0, 2))
    return float(np.einsum('ij,ij->i', a, np.cross(b, c)).sum() / 6)

def split_free(frees, used):
    x, y, w, h = used
    out = []
    for a, b, c, d in frees:
        if x >= a+c-1e-8 or x+w <= a+1e-8 or y >= b+d-1e-8 or y+h <= b+1e-8:
            out.append((a,b,c,d)); continue
        if x > a+1e-8: out.append((a,b,x-a,d))
        if x+w < a+c-1e-8: out.append((x+w,b,a+c-x-w,d))
        if y > b+1e-8: out.append((a,b,c,y-b))
        if y+h < b+d-1e-8: out.append((a,y+h,c,b+d-y-h))
    return [r for i,r in enumerate(out) if not any(i != j and r[0] >= s[0]-1e-8 and r[1] >= s[1]-1e-8 and r[0]+r[2] <= s[0]+s[2]+1e-8 and r[1]+r[3] <= s[1]+s[3]+1e-8 and (r != s or j < i) for j,s in enumerate(out))]

def pack(items, seed):
    rng = random.Random(seed)
    mode = seed % 5
    def priority(p):
        bases = (p['w']*p['h'], max(p['w'],p['h'])**2, min(p['w'],p['h'])**2, p['w']**2, p['h']**2)
        return -bases[mode] * (rng.uniform(.7,1.3) if seed > 4 else 1)
    plates = []
    for item in sorted(items, key=priority):
        best = None
        for pi, plate in enumerate(plates):
            for x,y,w,h in plate['free']:
                for rot in (0,90):
                    iw,ih = (item['w']+GAP,item['h']+GAP) if rot == 0 else (item['h']+GAP,item['w']+GAP)
                    if iw > w+1e-8 or ih > h+1e-8: continue
                    score = (pi,min(w-iw,h-ih),max(w-iw,h-ih),y,x) if seed%3 else (pi,w*h-iw*ih,min(w-iw,h-ih),y,x)
                    if best is None or score < best[0]: best = (score,pi,x,y,iw,ih,rot)
        if best is None:
            pi = len(plates)
            plates.append({'free':[(0.,0.,LIMIT,LIMIT)], 'items':[]})
            iw,ih = item['w']+GAP,item['h']+GAP
            assert max(iw,ih) <= LIMIT + 1e-8, item['part']
            best = ((),pi,0.,0.,iw,ih,0)
        _,pi,x,y,iw,ih,rot = best
        plate = plates[pi]
        plate['free'] = split_free(plate['free'],(x,y,iw,ih))
        plate['items'].append(dict(item,x=x+EDGE,y=y+EDGE,rotation_z_deg=rot))
    return plates

def best_pack(items):
    # Deterministic multi-start MaxRects search, not a claim of global optimality.
    choices = (pack(items,seed) for seed in range(700))
    return min(choices,key=lambda ps:(len(ps),-len(ps[-1]['items'])))

def mesh_at(item, mesh):
    v,f = mesh
    rotation = np.eye(3) if item['rotation_z_deg'] == 0 else np.array([[0.,-1.,0.],[1.,0.,0.],[0.,0.,1.]])
    rotated = v @ rotation.T
    offset = np.array([item['x'],item['y'],0.]) - rotated.min(axis=0)
    placed = rotated + offset
    return placed, f, rotation, offset

def write_3mf(path, objects):
    ET.register_namespace('',NS)
    root = ET.Element(Q+'model',{'unit':'millimeter','{http://www.w3.org/XML/1998/namespace}lang':'zh-CN'})
    ET.SubElement(root,Q+'metadata',{'name':'Title'}).text = path.stem
    ET.SubElement(root,Q+'metadata',{'name':'Description'}).text = 'O22 A1 mini layout; separate parts; keep placement; print by layer; no scaling.'
    resources = ET.SubElement(root,Q+'resources')
    build = ET.SubElement(root,Q+'build')
    for index,(name,v,f) in enumerate(objects,1):
        obj = ET.SubElement(resources,Q+'object',{'id':str(index),'type':'model','name':name})
        mesh = ET.SubElement(obj,Q+'mesh'); verts = ET.SubElement(mesh,Q+'vertices'); faces = ET.SubElement(mesh,Q+'triangles')
        for x,y,z in v:
            ET.SubElement(verts,Q+'vertex',{'x':format(x,'.17g'),'y':format(y,'.17g'),'z':format(z,'.17g')})
        for a,b,c in f:
            ET.SubElement(faces,Q+'triangle',{'v1':str(a),'v2':str(b),'v3':str(c)})
        ET.SubElement(build,Q+'item',{'objectid':str(index)})
    path.parent.mkdir(parents=True,exist_ok=True)
    with zipfile.ZipFile(path,'w',zipfile.ZIP_DEFLATED) as z:
        z.writestr('[Content_Types].xml','<?xml version="1.0" encoding="UTF-8"?><Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/><Default Extension="model" ContentType="application/vnd.ms-package.3dmanufacturing-3dmodel+xml"/></Types>')
        z.writestr('_rels/.rels','<?xml version="1.0" encoding="UTF-8"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Target="/3D/3dmodel.model" Id="rel0" Type="http://schemas.microsoft.com/3dmanufacturing/2013/01/3dmodel"/></Relationships>')
        # Expat in Bambu Studio requires the standard UTF-8 spelling, not utf8.
        z.writestr('3D/3dmodel.model',ET.tostring(root,encoding='utf-8',xml_declaration=True))
    with zipfile.ZipFile(path) as z:
        back = ET.fromstring(z.read('3D/3dmodel.model')).findall(Q+'resources/'+Q+'object')
    assert len(back) == len(objects)
    for node,(name,v,f) in zip(back,objects):
        vb = np.array([[float(n.attrib[k]) for k in ('x','y','z')] for n in node.findall('.//'+Q+'vertex')])
        fb = np.array([[int(n.attrib[k]) for k in ('v1','v2','v3')] for n in node.findall('.//'+Q+'triangle')])
        assert node.attrib['name'] == name and np.array_equal(v,vb) and np.array_equal(f,fb), name


def hull(points):
    points = sorted(set(map(tuple,np.round(points,7))))
    def cross(a,b,c): return (b[0]-a[0])*(c[1]-a[1])-(b[1]-a[1])*(c[0]-a[0])
    lower=[];upper=[]
    for p in points:
        while len(lower)>1 and cross(lower[-2],lower[-1],p)<=0: lower.pop()
        lower.append(p)
    for p in reversed(points):
        while len(upper)>1 and cross(upper[-2],upper[-1],p)<=0: upper.pop()
        upper.append(p)
    return lower[:-1]+upper[:-1]

def svg(plate, objects):
    parts=['<svg xmlns="http://www.w3.org/2000/svg" viewBox="-7 -7 194 201" role="img">',f'<title>{html.escape(plate["title"])}，{len(objects)} 件</title>','<rect x="-7" y="-7" width="194" height="201" rx="3" fill="#f6f4ed"/>','<rect width="180" height="180" fill="#e8ebe3" stroke="#354d48" stroke-width=".5"/>','<rect x="6" y="6" width="168" height="168" fill="none" stroke="#819088" stroke-width=".25" stroke-dasharray="2 1"/>']
    for n in range(20,180,20): parts.append(f'<path d="M{n} 0V180M0 {n}H180" stroke="#cbd1c7" stroke-width=".18"/>')
    for item,(_,v,_) in zip(plate['items'],objects):
        poly=' '.join(f'{x:.3f},{180-y:.3f}' for x,y in hull(v[:,:2]))
        x0,y0,_,x1,y1,_=item['bounds_mm']; color=COLORS[item['region']]
        parts.append(f'<g><title>{html.escape(item["object_name"])}</title><polygon points="{poly}" fill="{color}" fill-opacity=".8" stroke="{color}" stroke-width=".3"/><text x="{(x0+x1)/2:.3f}" y="{180-(y0+y1)/2:.3f}" text-anchor="middle" dominant-baseline="central" font-family="Arial,sans-serif" font-size="3.3" font-weight="bold" fill="#fff" stroke="#263d39" stroke-width=".15" paint-order="stroke">{item["number"]:02}</text></g>')
    parts.append('<text x="0" y="189" font-family="Arial,sans-serif" font-size="3.5" fill="#40574b">A1 mini · 180 × 180 mm · FRONT ↓</text></svg>')
    return '\n'.join(parts)

def main():
    source_path=BASE/'print_batch/manifest.json'
    source=json.loads(source_path.read_text(encoding='utf-8-sig'))
    meshes={};items=[]
    for row in source['rows']:
        path=BASE/'print_batch'/(row['id']+'.3mf');v,f=read_mesh(path);meshes[row['id']] = (v,f)
        dims=v.max(axis=0)-v.min(axis=0)
        assert dims[2]<=180 and len(row['instances'])==row['quantity_by_character']['universal']
        for instance in row['instances']:
            items.append({'id':row['id'],'part':instance['part'],'body':instance['body'],'region':region(instance['part']),'w':float(dims[0]),'h':float(dims[1]),'source_3mf':path.relative_to(BASE).as_posix(),'source_sha256':sha(path),'supports_diagnostic':row['bed']['supports_required']})
    leg_bones=set()
    for side in ('l','r'):
        leg_bones.update('frame/'+p+'_'+side for p in ('calf','foot','ball'))
        leg_bones.update('foot_'+side+'/'+p for p in ('C14','C15'))
    groups=[
        ('head','头颈与背盒盖',[i for i in items if i['region']=='head' or i['part']=='o22/controller_lid']),
        ('torso','躯干',[i for i in items if i['region']=='torso' and i['part']!='o22/controller_lid']),
        ('left_arm','左臂',[i for i in items if i['region']=='arm_l']),
        ('right_arm','右臂',[i for i in items if i['region']=='arm_r']),
        ('left_leg','左大腿与左腿关节小件',[i for i in items if i['region']=='leg_l' and i['part'] not in leg_bones]),
        ('right_leg','右大腿与右腿关节小件',[i for i in items if i['region']=='leg_r' and i['part'] not in leg_bones]),
        ('lower_legs','双侧小腿与脚掌骨架',[i for i in items if i['part'] in leg_bones]),
    ]
    assert collections.Counter(i['part'] for _,_,g in groups for i in g)==collections.Counter(i['part'] for i in items)
    plates=[]
    for slug,title,group in groups:
        packed=best_pack(group)
        for j,p in enumerate(packed,1):
            number=len(plates)+1
            plates.append({'id':f'A{number:02}','slug':slug+(f'_{j}' if len(packed)>1 else ''),'title':title+(f' {j}/{len(packed)}' if len(packed)>1 else ''),'optional':False,'items':p['items']})
    assert len(plates)==10, 'Review unexpected layout count before releasing.'
    optional=[]
    for part,pid in [('sensor_bridge','T001'),('magnet_bridge','T002')]:
        path=BASE/'physical_tests/sensor_coupon'/(part+'.3mf');v,f=read_mesh(path);meshes[pid]=(v,f);dims=v.max(axis=0)-v.min(axis=0)
        optional.append({'id':pid,'part':'sensor_coupon/'+part,'body':'test_fixture','region':'test','w':float(dims[0]),'h':float(dims[1]),'source_3mf':path.relative_to(BASE).as_posix(),'source_sha256':sha(path),'supports_diagnostic':True})
    test_plates=best_pack(optional);assert len(test_plates)==1
    plates.append({'id':'T01','slug':'sensor_coupon','title':'可选：O22 传感器安装小样','optional':True,'items':test_plates[0]['items']})
    (OUT/'previews').mkdir(parents=True,exist_ok=True)
    for p in plates:
        objects=[]
        for number,item in enumerate(p['items'],1):
            v,f,rot,offset=mesh_at(item,meshes[item['id']]); bounds=np.r_[v.min(axis=0),v.max(axis=0)]
            assert bounds[0]>=EDGE-1e-7 and bounds[1]>=EDGE-1e-7 and bounds[3]<=BED-EDGE+1e-7 and bounds[4]<=BED-EDGE+1e-7
            assert abs(bounds[2])<1e-9 and bounds[5]<=180
            original_volume=volume(*meshes[item['id']]); placed_volume=volume(v,f)
            assert abs(original_volume-placed_volume)<max(1e-6,abs(original_volume)*1e-9)
            name=f'{p["id"]}-{number:02} {item["id"]} {item["part"]}'
            item.update({'number':number,'object_name':name,'bounds_mm':bounds.tolist(),'rotation_matrix':rot.tolist(),'translation_mm':offset.tolist(),'source_volume_mm3':original_volume,'placed_volume_mm3':placed_volume,'triangles':len(f)})
            objects.append((name,v,f))
        gaps=[]
        for ai,a in enumerate(p['items']):
            for b in p['items'][ai+1:]:
                ba,bb=a['bounds_mm'],b['bounds_mm'];dx=max(ba[0]-bb[3],bb[0]-ba[3],0);dy=max(ba[1]-bb[4],bb[1]-ba[4],0)
                gap=math.hypot(dx,dy);gaps.append(gap);assert gap>=GAP-1e-7,(a['part'],b['part'],gap)
        filename=p['id']+'_'+p['slug']+'.3mf';rel=('optional/' if p['optional'] else 'plates/')+filename
        write_3mf(OUT/rel,objects)
        p.update({'file':rel,'sha256':sha(OUT/rel),'count':len(objects),'max_height_mm':max(i['bounds_mm'][5] for i in p['items']),'minimum_model_bbox_gap_mm':min(gaps),'preview':'previews/'+p['id']+'.svg'})
        (OUT/p['preview']).write_text(svg(p,objects),encoding='utf-8')
        print(p['id'],p['title'],len(objects),'height',round(p['max_height_mm'],2),flush=True)
    mainitems=[i for p in plates if not p['optional'] for i in p['items']]
    assert len(mainitems)==186 and collections.Counter(i['part'] for i in mainitems)==collections.Counter(i['part'] for i in items)
    manifest={'schema':'POSEDOLL-O22-A1MINI-PLATES/1','generated_date':'2026-10-02','source_manifest':source_path.relative_to(BASE).as_posix(),'source_manifest_sha256':sha(source_path),'source_version':'posedoll-o22-engineering-20261001 / 91dbf0dda5e4ada8e8d14c12888b6886188911e2','printer':'Bambu Lab A1 mini','build_volume_mm':[180,180,180],'model_edge_margin_mm':EDGE,'model_bbox_gap_mm':GAP,'print_sequence':'by layer','scale':1.0,'orientations':'Source bed orientations preserved; only 0/90 degree rotation about Z and translation','main_plates':10,'main_pieces':186,'on_doll_pieces':185,'assembly_gauge_pieces':1,'optional_plates':1,'optional_pieces':2,'packing':'Deterministic 700-start MaxRects per anatomical group; not a proof of global optimum','geometry_roundtrip':'PASS: every output vertex and triangle equals the rigidly transformed source mesh','coverage_check':'PASS: all 186 source instances appear exactly once','physical_print_tested':False,'slicer_validation':'pending','plates':plates}
    (OUT/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')

if __name__=='__main__': main()
