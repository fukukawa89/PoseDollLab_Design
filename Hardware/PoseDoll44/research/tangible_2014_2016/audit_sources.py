"""Read-only audit of the supplied 2014 hardware package and pinned atamid checkout.

Usage: python audit_sources.py --plan-root <PoseDoll_HW44_Plan>
Requires numpy and Pillow. No source files are edited; no upstream code is executed.
STL coordinates are unitless. Millimetres are a contextual assumption, not metadata.
A welded surface component is not necessarily one manufactured part.
"""
from pathlib import Path
import argparse
import hashlib
import json
import math
import re
import struct
import subprocess
import numpy as np
from PIL import Image, ImageDraw, ImageFont

PIN = '9a152b1d82374d1960ebd2216563fb30b1b6875b'
STL_DTYPE = np.dtype([('normal','<f4',(3,)),('vertices','<f4',(3,3)),('attr','<u2')])
OUT = Path(__file__).resolve().parent

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def read_stl(path):
    data = path.read_bytes()
    count = struct.unpack_from('<I',data,80)[0]
    if len(data) != 84 + count*50:
        raise ValueError(f'Not an exact binary STL: {path}')
    triangles = np.frombuffer(data, dtype=STL_DTYPE, offset=84)['vertices'].astype(float)
    if not np.isfinite(triangles).all():
        raise ValueError(f'Nonfinite coordinates: {path}')
    return triangles

def connected(triangles, decimals):
    vertices, inv = np.unique(np.round(triangles.reshape(-1,3),decimals),axis=0,return_inverse=True)
    faces = inv.reshape(-1,3)
    parent = np.arange(len(vertices))
    size = np.ones(len(vertices),dtype=int)
    def root(a):
        while parent[a] != a:
            parent[a] = parent[parent[a]]
            a = parent[a]
        return a
    def join(a,b):
        a,b = root(a),root(b)
        if a==b: return
        if size[a]<size[b]: a,b = b,a
        parent[b] = a
        size[a] += size[b]
    for a,b,c in faces:
        join(a,b)
        join(b,c)
    labels = np.array([root(a) for a in faces[:,0]])
    groups = [np.flatnonzero(labels==lab) for lab in np.unique(labels)]
    groups.sort(key=lambda g:(-len(g),tuple(triangles[g].min(axis=(0,1)))))
    return groups,faces

def assess_mesh(path):
    tri = read_stl(path)
    groups,faces = connected(tri,5)
    count_sensitivity = {'5_decimal_places':len(groups),'4_decimal_places':len(connected(tri,4)[0])}
    rows=[]
    for i,g in enumerate(groups,1):
        xyz = tri[g].reshape(-1,3)
        f=faces[g]
        edges=np.sort(np.concatenate((f[:,[0,1]],f[:,[1,2]],f[:,[2,0]])),axis=1)
        _,counts = np.unique(edges,axis=0,return_counts=True)
        rows.append({'id':i,'triangles':len(g),'bounds_min':xyz.min(axis=0).round(5).tolist(),
                     'bounds_max':xyz.max(axis=0).round(5).tolist(),
                     'extent_xyz_source_units':np.ptp(xyz,axis=0).round(5).tolist(),
                     'boundary_edges_after_weld':int((counts==1).sum()),
                     'nonmanifold_edges_after_weld':int((counts>2).sum())})
    return {'triangles':len(tri),'layout_extent_xyz_source_units':np.ptp(tri.reshape(-1,3),axis=0).round(5).tolist(),
            'component_count_sensitivity':count_sensitivity,'components':rows,
            'scope':'Print layout, not reconstructed assembly. No fit, strength, ROM, mass, or manufacturing validation.'},tri,groups

def render_components(tri,groups,rows,title,path):
    columns=4
    tilew,tileh=380,300
    width=columns*tilew+40
    height=math.ceil(len(groups)/columns)*tileh+160
    im=Image.new('RGB',(width,height),'#f4f5f6')
    d=ImageDraw.Draw(im)
    font_path=Path('C:/Windows/Fonts/msyh.ttc')
    font=ImageFont.truetype(str(font_path),18) if font_path.exists() else ImageFont.load_default()
    large=ImageFont.truetype(str(font_path),28) if font_path.exists() else font
    d.text((24,15),title,font=large,fill='#16252c')
    d.text((24,59),'原始 STL 按连通表面拆分；各格独立缩放。尺寸为原文件 XYZ 包络，非装配尺寸。',font=font,fill='#52616a')
    d.text((24,91),'单位按毫米理解，STL 本身无单位。C 编号仅用于本次审查，不是原作者零件名称。',font=font,fill='#52616a')
    # Orthographic illustration only; dimensions above are computed from original vertices.
    az,el=np.deg2rad(38),np.deg2rad(28)
    right=np.array([math.cos(az),-math.sin(az),0])
    up=np.array([math.sin(az)*math.sin(el),math.cos(az)*math.sin(el),math.cos(el)])
    depth=np.cross(right,up)
    matrix=np.stack([right,up,depth],axis=1)
    light=np.array([.3,-.4,.86]); light/=np.linalg.norm(light)
    for k,(g,row) in enumerate(zip(groups,rows)):
        x0=20+(k%columns)*tilew; y0=140+(k//columns)*tileh
        d.rounded_rectangle((x0,y0,x0+tilew-12,y0+tileh-12),12,fill='white',outline='#dce3e6')
        t=tri[g]
        center=(t.min(axis=(0,1))+t.max(axis=(0,1)))/2
        p=(t-center)@matrix
        ranges=np.ptp(p.reshape(-1,3),axis=0)
        scale=min((tilew-48)/max(ranges[0],1e-6),(tileh-100)/max(ranges[1],1e-6))
        normals=np.cross(t[:,1]-t[:,0],t[:,2]-t[:,0])
        normals/=np.maximum(np.linalg.norm(normals,axis=1,keepdims=True),1e-12)
        brightness=.52+.48*np.abs(normals@light)
        # Painter ordering is for visual inspection only, not a geometry intersection test.
        for idx in np.argsort(p[:,:,2].mean(axis=1)):
            points=[(float(x0+(tilew-12)/2+v[0]*scale),float(y0+132-v[1]*scale)) for v in p[idx]]
            color=tuple(int(v*brightness[idx]) for v in (81,155,166))
            d.polygon(points,fill=color)
        d.text((x0+14,y0+9),f'C{row["id"]:02d}',font=font,fill='#16252c')
        ex=' × '.join(f'{v:.2f}' for v in row['extent_xyz_source_units'])
        d.text((x0+14,y0+242),ex+' mm*',font=font,fill='#334953')
        d.text((x0+14,y0+268),f'{row["triangles"]:,} 三角面',font=font,fill='#52616a')
    im.save(path)

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--plan-root',type=Path,required=True)
    args=parser.parse_args()
    plan=args.plan_root.resolve()
    old=plan/'tangible-and-modular-input-device-for-character-articulation-supplemental'
    repo=plan/'research/tangible_reuse_20260925/atamid'
    head=subprocess.check_output(['git','-C',str(repo),'rev-parse','HEAD'],text=True).strip()
    if head!=PIN: raise ValueError(f'Unexpected upstream revision: {head}')
    source_paths=[old/'tangible-and-modular-input-device-for-character-articulation-siggraph-2014-jacobson-et-al.pdf',
                  old/'open_hardware_package/readme.pdf',plan/'Rig-Animation-Input-Device-2016.pdf',repo/'README.md']
    source_paths.extend(p for p in (repo/'Hardware').rglob('*') if p.is_file() and p.suffix.lower() in {'.stl','.t3000'})
    source_paths.extend([repo/'Hardware/Firmware/utility.c',repo/'Hardware/Firmware/mlx90363.c',
                         repo/'Hardware/Firmware/Src/main.c',repo/'Hardware/Firmware/f051-cube-first.ioc',
                         repo/'Software/RigReducer/CMakeLists.txt'])
    mesh_paths={'tbt2014':old/'open_hardware_package/STLs/pro_TBT_20121022.stl',
                'tut2016':repo/'Hardware/Mechanics/jointTUT.stl'}
    source_paths.extend(mesh_paths.values())
    source_paths.extend([old/'open_hardware_package/STLs/stl_description.pdf',
                        old/'open_hardware_package/PCBs/cBoard/cBoard_parts.pdf',
                        old/'open_hardware_package/PCBs/cBoard/cBoard_schematics.pdf',
                        old/'open_hardware_package/PCBs/uBoard/uBoard_parts.pdf',
                        old/'open_hardware_package/PCBs/uBoard/uBoard_schematics.pdf',
                        plan/'design/Hardware/PoseDoll44/docs/O7_DIGITAL_AND_BENCH.zh-CN.md',
                        plan/'design/Hardware/PoseDoll44/mechanical_manifest/requirements_revO7.json',
                        plan/'design/Hardware/PoseDoll44/bench/revO7/plan.json',
                        plan/'design/Tools/PoseDollHardwareBridge/layout.json'])
    result={'schema':'tangible-source-audit-v1','audited_date':'2026-09-25','upstream_commit':head,
            'sources':[],'meshes':{},'limitations':['No hardware tested','No PCB CAD export or electrical build',
            'No full assembly reconstruction','No upstream firmware or RigReducer build',
            'No retention/torque/accuracy qualification','STL unit assumption and component grouping are not a BOM']}
    for p in sorted(set(source_paths)):
        result['sources'].append({'path_from_plan':p.relative_to(plan).as_posix(),'bytes':p.stat().st_size,'sha256':sha(p)})
    for name,path in mesh_paths.items():
        stats,tri,groups=assess_mesh(path)
        result['meshes'][name]=stats
        render_components(tri,groups,stats['components'],name+' / 打印文件表面检查',OUT/(name+'_components.png'))
    hw_files=[p for p in (repo/'Hardware/Electronics').rglob('*') if p.is_file()]
    result['electronics_2016_files']=[p.relative_to(repo).as_posix() for p in sorted(hw_files)]
    result['license_named_files_in_2016_checkout']=[p.relative_to(repo).as_posix() for p in repo.rglob('*') if p.is_file() and '.git' not in p.parts and (p.name.lower().startswith('license') or p.name.lower().startswith('copying'))]
    # Evidence locator, not execution or a substitute for C memory-safety analysis.
    code=(repo/'Hardware/Firmware/utility.c').read_text(encoding='utf-8')
    uncommented=re.sub(r'/\*.*?\*/|//[^\n]*','',code,flags=re.S)
    match=re.search(r'static\s+uint16_t\s+anglesZ\[(\d+)\]',uncommented)
    indices=[int(x) for x in re.findall(r'anglesZ\[(\d+)\]',uncommented)]
    result['firmware_source_observation']={'declared_anglesZ_capacity':int(match[1]),'literal_indices_in_declaration_or_access':sorted(set(indices)),
        'review_note':'utility.c declares three entries, then writes index 3 and reads four entries. Source defect; no upstream firmware build executed.'}
    for entry in result['sources']:
        if sha(plan/entry['path_from_plan'])!=entry['sha256']: raise ValueError('Source changed during audit')
    (OUT/'evidence.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'revision':head,'source_files':len(result['sources']),
          'components':{k:v['component_count_sensitivity'] for k,v in result['meshes'].items()},
          'firmware_observation':result['firmware_source_observation']},ensure_ascii=False))

if __name__=='__main__': main()

