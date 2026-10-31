"""O24C-T2-H: direct, coaxial disc-spring friction coupon, in mm.

O22 G1 / O12 stock stack is the dimensional reference. This is a new H
specimen, not a change to the frozen T1 H/R/W files or an O24D release.
"""
from pathlib import Path
import sys, json, math, csv, hashlib
sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
H = HERE.parents[1]
ROOT = H.parents[1]
OUT = H/'bench/revO24C_T2_H'
sys.path.insert(0, str(H/'cad/revO24C_T1'))
from kit import a, md, np, trimesh, box, cyl, tube, rot, moved, hexagon, nut, screw, washer, mesh, sha, put, X, Y, Z
sys.path.insert(0,str(HERE))

REVISION = 'O24C-T2-H'
DATE = '2026-10-24'
COLORS = {'structure':[.36,.65,.59], 'rotor':[.91,.57,.22], 'metal':[.60,.65,.70],
          'spring':[.26,.43,.70], 'friction':[.67,.40,.22], 'coupon':[.68,.73,.67]}

def disc(y, height, flipped=False):
    # Exact axial envelope only: NOT an elastic or spring-force simulation.
    p = np.array([[2.1,height-.4],[4,0],[4,.4],[2.1,height]])
    if flipped:
        p[:,1] = height-p[:,1]
        p = p[::-1].copy()
    return moved(md.CrossSection([p]).revolve(circular_segments=96), rot(X,-90)).translate([0,y,0])

def build(pair_height=1.0, bore=4.25):
    assert .8 <= pair_height <= 1.2
    rows=[]
    def add(id,label,s,role='structure',printed=False,orientation=None,sku=None,spec='',note='',frame='fixed'):
        assert not s.is_empty() and str(s.status())=='Error.NoError', id
        rows.append(dict(id=id,label=label,s=s,role=role,printable=printed,frame=frame,
                         orientation=np.eye(4) if orientation is None else orientation,
                         sku=sku,spec=spec,note=note))

    # Continuous reaction block. The spring force returns through the 2.8 mm
    # full annular web and the M3 D9 reaction washer, NOT through the rear cap.
    base=box([-22,-10.5,-16],[22,-2.5,16])
    base-=cyl([0,-10.6,0],[0,-6.1,0],6.05)
    base-=cyl([0,-6.2,0],[0,-5.3,0],4.65)
    base-=cyl([0,-10.6,0],[0,-2.4,0],1.7)
    base-=cyl([0,-4.4,0],[0,-2.4,0],2.125)
    for x in [-14,14]:
        base-=cyl([x,-10.6,0],[x,-2.4,0],1.7)
        base-=hexagon([x,-5.7,0],Y,5.8,3.3)
    for x in [-17,17]:
        for z in [-11,11]:base-=cyl([x,-10.6,z],[x,-2.4,z],2.25)
    add('H2-01','整体反力座',base,printed=True,orientation=rot(X,-90),
        note='44×32×8；有小轴孔的一面朝下打印。大圆腔朝后，反力垫从后方装入。')

    # One flat 3 mm plate: no bearings, split seam, raised cantilever or thin
    # stepped link. The load hole is 100 mm from the physical rotation axis.
    lever=cyl([0,-1.5,0],[0,1.5,0],8)+box([-6,-1.5,-100],[6,1.5,-4])+cyl([0,-1.5,-100],[0,1.5,-100],6)
    lever-=cyl([0,-1.6,0],[0,1.6,0],bore/2)
    lever-=cyl([0,-1.6,-100],[0,1.6,-100],1.8)
    add('H2-02','100 mm 整体转动杆',lever,'rotor',True,rot(X,90),
        note='厚3.00，轴孔4.25；两面是摩擦面，去毛刺但不磨薄。',frame='rotor')

    # Rear captive-nut carrier. Its nose ends 0.15 mm short of the reaction
    # washer, so the cap is not a parallel route around the primary nut.
    cap=box([-18,-13.7,-9],[18,-10.5,9])+cyl([0,-10.6,0],[0,-6.25,0],5.9)
    cap-=cyl([0,-13.8,0],[0,-6.1,0],1.75)
    cap-=hexagon([0,-8.65,0],Y,5.8,2.5)
    for x in [-14,14]:cap-=cyl([x,-13.8,0],[x,-10.4,0],1.7)
    add('H2-03','普通螺母止转后盖',cap,printed=True,orientation=rot(X,90),
        note='平背面朝下打印；中央六角槽装普通M3螺母，无尼龙圈；端部留0.15间隙，不承担主预紧。')

    add('M03','M3 大平垫圈 · 反力垫',washer([0,-6.1,0],Y,9,3.2,.8),'metal',sku='W_M3_D9_T0P8',
        spec='M3：外径9 / 内径3.2 / 厚0.8 mm，钢制',note='光滑面朝固定座内部反力壁（+Y）；必须使用O22的9×3.2×0.8，不能换T1小垫圈。')
    add('M02','调节用普通 M3 螺母',nut([0,-8.5,0],Y,3,5.5,2.4),'metal',sku='N3',
        spec='M3×0.5，六角对边5.5，高2.4 mm；无尼龙圈',note='平整承压面朝反力垫（+Y）；普通螺母两端均应能正常旋入。')
    for i,x in enumerate([-14,14],1):
        add(f'C_N{i}',f'后盖固定普通 M3 螺母 {i}',nut([x,-5.7,0],Y,3,5.5,2.4),'metal',sku='N3',
            spec='M3×0.5，AF5.5，高2.4 mm；无尼龙圈',note='平整承压面朝槽底（−Y）；螺母沉入固定座正面的六角槽。')
        add(f'C_W{i}',f'后盖 M3 平垫圈 {i}',washer([x,-14.2,0],Y,7,3.2,.5),'metal',sku='W3',
            spec='M3：7×3.2×0.5 mm，钢制',note='光滑面朝后盖（+Y）。')
        add(f'C_S{i}',f'后盖 M3×12 螺钉 {i}',screw([x,-14.2,0],Y,3,12),'metal',sku='M3x12',
            spec='M3×0.5×12 内六角圆柱头，头径5.5，2.5 mm内六角',note='从背面旋入；前面的普通螺母已被六角槽止转。')

    for i,y,normal in [(1,-2.5,'+Y'),(2,1.5,'−Y')]:
        add(f'F0{i}',f'M4 大垫圈 · {"内侧" if i==1 else "外侧"}',washer([0,y,0],Y,12,4.3,1),'friction',sku='W_M4_D12_T1',
            spec='M4：12×4.3×1.0 mm，钢制',note=f'光滑面朝转动杆（{normal}），两片夹住杆的圆盘；毛刺必须去除。')
    for i,flip in [(1,False),(2,True)]:
        add(f'SP0{i}',f'A8 碟簧 · 第{i}片',disc(2.5+(i-1)*pair_height/2,pair_height/2,flip),'spring',sku='A8_SS',
            spec='A8：外径8 / 内径4.2 / 材料厚0.4 / 自由高约0.6 mm',
            note='内孔凸起边朝螺钉头（+Y）' if i==1 else '翻面：内孔凸起边朝固定座（−Y）；两片内孔边相对，外圆边分开，不能同向套叠。')
    add('M04','M4 普通平垫圈 · 头下垫',washer([0,2.5+pair_height,0],Y,9,4.3,.8),'metal',sku='W_M4_D9_T0P8',
        spec='M4：9×4.3×0.8 mm，钢制',note='与碟簧、螺钉均为金属接触；两面去毛刺，正反不作为强制要求。')
    head=3.3+pair_height
    bolt=cyl([0,head-14,0],[0,head-8,0],1.5)+cyl([0,head-8,0],[0,head,0],2)+cyl([0,head,0],[0,head+3,0],3.5)
    bolt-=hexagon([0,head+3.01,0],-Y,3,1.6)
    add('AX01','O22 轴肩调节螺钉',bolt,'metal',sku='SHOULDER_D4_L8_M3_L6',
        spec='光杆Φ4×8；M3×0.5螺纹长6；头Φ7×3；内六角3 mm',
        note='只从正面调节。内藏普通螺母自动止转；不能换成普通M3全牙螺钉。')
    return rows

def coupon():
    s=box([0,0,0],[38,25,4])
    for x,d in [(6,4.15),(18,4.25),(30,4.35)]:s-=cyl([x,6,-.1],[x,6,4.1],d/2)
    s-=hexagon([7,18,1.4],Z,5.8,2.7)
    s-=cyl([7,18,-.1],[7,18,4.1],1.7)
    s-=cyl([27,17,3],[27,17,4.1],6.15)
    return s

def export():
    OUT.mkdir(parents=True,exist_ok=True)
    (OUT/'stl_print').mkdir(exist_ok=True)
    (OUT/'verification').mkdir(exist_ok=True)
    parts=build();records=[];arrays={};bom={};scene=trimesh.Scene()
    parts.append(dict(id='H2-C01',label='孔、普通螺母及垫圈试配片（不装入样件）',s=coupon(),role='coupon',
        printable=True,frame='coupon',orientation=np.eye(4),sku=None,spec='',note='从左到右孔径4.15 / 4.25 / 4.35；六角AF5.8；浅圆座D12.3。'))
    for i,p in enumerate(parts):
        m=mesh(p['s']);arrays['v'+str(i)]=m.vertices;arrays['f'+str(i)]=m.faces
        r={k:v for k,v in p.items() if k not in ['s','orientation']}
        r.update(index=i,volume_mm3=float(m.volume),bounds_mm=m.bounds.tolist(),watertight=bool(m.is_watertight),components=len(p['s'].decompose()),color=COLORS[p['role']])
        if p['printable']:
            pm=m.copy();M=p['orientation'].copy();pm.apply_transform(M);shift=-pm.bounds[0];M[:3,3]+=shift;pm.apply_translation(shift)
            path=OUT/'stl_print'/(p['id']+'.stl');pm.export(path);back=trimesh.load(path,process=True)
            r.update(stl=path.relative_to(OUT).as_posix(),stl_sha256=sha(path),print_matrix=M.tolist(),print_bounds_mm=pm.bounds.tolist(),print_qty=1,
                     stl_watertight=bool(back.is_watertight),roundtrip_volume_error_mm3=abs(back.volume-m.volume))
        else:
            b=bom.setdefault(p['sku'],dict(sku=p['sku'],spec=p['spec'],qty=0,ids=[],source='O22 沿用' if p['sku'] not in ['W3','M3x12'] else 'T1 H 可拆用'))
            b['qty']+=1;b['ids'].append(p['id'])
        if p['frame']!='coupon':
            g=m.copy();g.apply_scale(.001);g.visual.vertex_colors=np.array([*COLORS[p['role']],1])*255
            scene.add_geometry(g,node_name=p['id'],geom_name=p['id'])
        records.append(r)
    np.savez_compressed(OUT/'assembly_meshes.npz',**arrays);scene.export(OUT/'O24C_T2_H.glb')
    put(OUT/'assembly.json',dict(revision=REVISION,units='mm',nominal_spring_pair_height_mm=1.0,axis=[0,1,0],origin_mm=[0,0,0],parts=records))
    put(OUT/'BOM.json',list(bom.values()))
    with (OUT/'BOM.csv').open('w',encoding='utf-8-sig',newline='') as f:
        w=csv.writer(f);w.writerow(['编号','规格','数量','来源','动画编号'])
        for b in bom.values():w.writerow([b['sku'],b['spec'],b['qty'],b['source'],' / '.join(b['ids'])])
    put(OUT/'verification/geometry.json',dict(passed=all(r['watertight'] and r['components']==1 and r.get('stl_watertight',True) and r.get('roundtrip_volume_error_mm3',0)<.01 for r in records),parts=records,geometry_sha256=sha(OUT/'assembly_meshes.npz')))
    print(json.dumps(dict(revision=REVISION,assembly_parts=len(parts)-1,assembly_prints=3,fit_coupon=1,bom_lines=len(bom)),ensure_ascii=False))

if __name__=='__main__':export()
