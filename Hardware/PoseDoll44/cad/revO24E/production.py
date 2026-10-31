"""Explicit one-piece bodies, part-level mesh checks, print orientations and BOM.

Only connected same-material structural features are fused. Hardware is NOT fused
into plastic, and separate components are NOT called one printed object.
"""
from build import *
from collections import defaultdict,Counter
from groups import physical_components
from connections import core
import itertools, argparse,io

def physical_frame(fr):
    while NODES[fr]['axis'] is None and NODES[fr]['parent']:fr=NODES[fr]['parent']
    return fr

def orientation(s):
    v,f=base.a.mesh_data(s);choices=[]
    for axis,angle in [([1,0,0],0),([1,0,0],90),([1,0,0],-90),([0,1,0],90),([0,1,0],-90),([1,0,0],180)]:
        R=rot(axis,angle);vv=v@R[:3,:3].T;size=np.ptp(vv,axis=0)
        # Low height reduces Z-direction tensile loading on long bone roots.
        score=size[2]+max(0,max(size[:2])-162)*100
        choices.append((score,R,size))
    _,R,size=min(choices,key=lambda x:x[0]);vv=v@R[:3,:3].T;R[:3,3]=-vv.min(0)
    return R,size

def make():
    for folder in ['stl_print','parts_assembly','custom_metal']:
        target=OUT/folder
        if target.exists():
            assert target.resolve().parent==OUT.resolve()
            for old in target.glob('*.stl'):old.unlink()
    parts=read_saved();groups=defaultdict(list);hardware=[]
    for p in parts:
        if p['role'] in ['structure','rotor','shell']:
            fr=physical_frame(p['frame']);mat=p.get('material','PLA qualification required')
            groups[(fr,mat)].append((p,moved(p['s'],np.linalg.inv(F0[fr])@F0[p['frame']])))
        else:hardware.append(p)
    inventory=[];production=[];pmap={};idx=0
    for (fr,mat),members in sorted(groups.items()):
        solids=[s for s in physical_components(union(s for p,s in members)) if s.volume()>1e-5]
        for no,s in enumerate(solids,1):
            idx+=1;metal='steel' in mat.lower();pn=f'E-{"M" if metal else "P"}{idx:03d}'
            nominal=s;datum_reliefs=[]
            if fr=='r_clavicle_elevate':
                # A circular bore tangent to the hex face produces coincident
                # STL edges. An explicit 0.02 mm radial/axial relief is inside
                # the declared 0.03 mm export tolerance, not mesh hole filling.
                s-=tube([-9.02,0,0],[-8.98,0,0],6.02,5.98)
                datum_reliefs.append(dict(type='coaxial tangent-edge relief',axis='local X',station_mm=-9,axial_width_mm=.04,radii_mm=[5.98,6.02]))
            tol=.01;s=s.as_original().simplify(tol)
            v,f=base.a.mesh_data(s);m=trimesh.Trimesh(v,f,process=False);ids=[]
            for p,t in members:
                a,b=bounds(s),bounds(t)
                if np.all(a[1]>=b[0]) and np.all(b[1]>=a[0]) and (s^t).volume()>.001:ids.append(p['name']);pmap.setdefault(p['name'],[]).append(pn)
            R,size=orientation(s);pm=m.copy();pm.apply_transform(R)
            rt=trimesh.load(io.BytesIO(pm.export(file_type='stl')),file_type='stl',process=True)
            if not rt.is_watertight:
                # Weld only coincident quantized open edges at 0.1 micrometre.
                qm=md.Mesh64(np.array(rt.vertices,dtype=np.float64,copy=True),np.array(rt.faces,dtype=np.uint64,copy=True),tolerance=.0001)
                qm.merge();fixed=md.Manifold(qm)
                if str(fixed.status())=='Error.NoError':
                    fixed=fixed.simplify(.001);vv,ff=base.a.mesh_data(fixed);pm=trimesh.Trimesh(vv,ff,process=False)
                    rt=trimesh.load(io.BytesIO(pm.export(file_type='stl')),file_type='stl',process=True)
                    s=moved(fixed,np.linalg.inv(R));v,f=base.a.mesh_data(s);m=trimesh.Trimesh(v,f,process=False)
            if not rt.is_watertight:
                for tol2 in [.015,.02,.025,.03]:
                    t=nominal.as_original().simplify(tol2);vv,ff=base.a.mesh_data(t);R,size=orientation(t);pm=trimesh.Trimesh(vv,ff,process=False);pm.apply_transform(R)
                    rt=trimesh.load(io.BytesIO(pm.export(file_type='stl')),file_type='stl',process=True)
                    qm=md.Mesh64(np.array(rt.vertices,dtype=np.float64,copy=True),np.array(rt.faces,dtype=np.uint64,copy=True),tolerance=.0001);qm.merge();fixed=md.Manifold(qm)
                    if str(fixed.status())=='Error.NoError':
                        vv,ff=base.a.mesh_data(fixed.as_original());pm=trimesh.Trimesh(vv,ff,process=True);rt=trimesh.load(io.BytesIO(pm.export(file_type='stl')),file_type='stl',process=True)
                    if rt.is_watertight:
                        s=moved(fixed,np.linalg.inv(R));v,f=base.a.mesh_data(s);m=trimesh.Trimesh(v,f,process=False);tol=tol2;break
            edge_reliefs=[]
            if not rt.is_watertight:
                # A coincident edge is not a load-bearing connection. Open it with
                # a documented 0.05 mm machining relief instead of welding shells.
                s=nominal.as_original().simplify(.01);tol=.01
                for attempt in range(4):
                    v,f=base.a.mesh_data(s);R,size=orientation(s);pm=trimesh.Trimesh(v,f,process=False);pm.apply_transform(R)
                    rt=trimesh.load(io.BytesIO(pm.export(file_type='stl')),file_type='stl',process=True)
                    if rt.is_watertight:break
                    ec=np.bincount(rt.edges_unique_inverse,minlength=len(rt.edges_unique));bad=rt.edges_unique[ec!=2]
                    cuts=[]
                    for edge in bad:
                        pt=rt.vertices[edge];pt=(pt-R[:3,3])@R[:3,:3]
                        if np.linalg.norm(pt[1]-pt[0])<1e-7:continue
                        rr=.05
                        cuts.extend([beam(pt[0],pt[1],rr),md.Manifold.sphere(rr,12).translate(pt[0]),md.Manifold.sphere(rr,12).translate(pt[1])])
                        edge_reliefs.append(dict(a=pt[0].tolist(),b=pt[1].tolist(),radius_mm=rr))
                    if not cuts:break
                    s=(s-union(cuts)).as_original().simplify(.001)
                v,f=base.a.mesh_data(s);m=trimesh.Trimesh(v,f,process=False)
            if not rt.is_watertight:raise ValueError('STL precision closure failed '+pn)
            if len([x for x in s.decompose() if x.volume()>5])!=1:raise ValueError('Relief exposed disconnected load bodies '+pn)
            finished_bodies=s.decompose()
            residue=[x.volume() for x in finished_bodies if 0<x.volume()<=.1]
            if residue:
                # Keep each main body's negative cavity shells. Only positive
                # isolated machining scallops below 0.1 mm3 are removed.
                s=md.Manifold.compose([x for x in finished_bodies if x.volume()>.1 or x.volume()<=0]);v,f=base.a.mesh_data(s);m=trimesh.Trimesh(v,f,process=False);R,size=orientation(s);pm=m.copy();pm.apply_transform(R)
                rt=trimesh.load(io.BytesIO(pm.export(file_type='stl')),file_type='stl',process=True)
                if not rt.is_watertight:raise ValueError('Post-residue closure failed '+pn)
            folder=OUT/('custom_metal' if metal else 'stl_print');folder.mkdir(exist_ok=True)
            file=folder/(pn+'.stl');pm.export(file)
            # Assembly-local export is distinct from the print-oriented STL.
            raw=OUT/'parts_assembly';raw.mkdir(exist_ok=True);m.export(raw/(pn+'.stl'))
            row=dict(part_number=pn,quantity=1,label=fr+f' / {no}',frame=fr,material=mat,
                process='CNC custom steel carrier' if metal else 'FDM PLA / 0.4 nozzle / 0.12 layer',
                source_features=ids,volume_mm3=float(m.volume),bounds_mm=m.bounds.tolist(),
                print_bounds_mm=pm.bounds.tolist(),print_matrix=R.tolist(),stl=file.relative_to(OUT).as_posix(),
                assembly_stl=f'parts_assembly/{pn}.stl',sha256=sha(file),printable=not metal,
                wall_loops=5,infill_percent=100,support='automatic, remove via open service bores',
                triangulation_tolerance_mm=tol,triangulation_volume_delta_mm3=s.volume()-nominal.volume(),stl_roundtrip_watertight=bool(rt.is_watertight),
                zero_thickness_edge_reliefs=edge_reliefs,
                datum_edge_reliefs=datum_reliefs,
                numerical_residue_volumes_removed_mm3=residue,
                status='GEOMETRY_EXPORT_ONLY',notes='一件连续材料；不同材料的五金独立装入。此标识不代表结构/装配已放行。')
            inventory.append(row)
            production.append(dict(name=pn,frame=fr,s=s,role='metal' if metal else 'structure',material=mat,sku=pn,notes=row['notes'],group=fr))
            print('PART',pn,fr,len(ids),round(s.volume(),2),flush=True)
    # Every purchased/custom metal component receives a separately addressable ID.
    hardware_rows=[];counts=Counter();pcba_members=[]
    for k,p in enumerate(hardware,1):
        pn=f'E-H{k:04d}';sku=p.get('sku') or ('CUSTOM_'+p['name'] if p['role']=='metal' else p['role'].upper()+'_'+p['name'])
        pcba=p['name'].startswith('electronics_') and p['name'] not in ['electronics_XIAO_module','electronics_XIAO_USB']
        xiao=p['name'] in ['electronics_XIAO_module','electronics_XIAO_USB']
        if not pcba and not xiao:counts[sku]+=1
        pr=dict(p);pr['name']=pn;production.append(pr);pmap[p['name']]=[pn]
        custom=sku.startswith(('CUSTOM','D4_','D6_','E_TAB','E_CAP','E_REAR','STEEL_TUBE','ROLL_PIN')) or '_trim' in sku or ('metal'==p['role'] and not p.get('sku') and not pcba and not xiao)
        hardware_rows.append(dict(part_number=pn,feature=p['name'],sku=sku,quantity=1,frame=p['frame'],role=p['role'],custom_or_secondary_operation=custom,
             disposition='补购/制作新件' if p.get('revision_change') or p['name'].startswith(('l_E_','r_E_')) or p['name'] not in {x['name'] for x in load(BASE/'assembly.json')['parts']} else '可复用，来料核对尺寸与状态',spec=p['notes'],
             procurement_item=not pcba and not xiao,physical_owner='E-B001' if pcba else ('E-B002' if xiao else pn)))
        if pcba or xiao:pcba_members.append(dict(feature=p['name'],display_id=pn,physical_owner=hardware_rows[-1]['physical_owner']))
        if custom and p['role']=='metal':
            folder=OUT/'custom_metal';folder.mkdir(exist_ok=True);v,f=base.a.mesh_data(p['s']);trimesh.Trimesh(v,f,process=False).export(folder/(pn+'.stl'));hardware_rows[-1]['stl']=f'custom_metal/{pn}.stl'
    counts['O24D_SPI_CARRIER_POPULATED_PCBA']+=1;counts['XIAO_MODULE_WITH_USB']+=1
    pcbas=[dict(part_number=id,sku=sku,quantity=1,members=[r['display_id'] for r in pcba_members if r['physical_owner']==id],disposition='可复用原D已装配PCBA；按原生PCB BOM供装，不逐焊盘采购') for id,sku in [('E-B001','O24D_SPI_CARRIER_POPULATED_PCBA'),('E-B002','XIAO_MODULE_WITH_USB')]]
    put(OUT/'production_parts.json',dict(geometry_sha256=sha(OUT/'assembly_meshes.npz'),structural_parts=inventory,hardware=hardware_rows,purchased_assemblies=pcbas,feature_to_production=pmap,manufacturing_release=False))
    put(OUT/'BOM_totals.json',dict(counts=dict(sorted(counts.items())),inventory_on_hand='UNKNOWN; reuse eligibility is not a stock count',structural_quantity=len(inventory)))
    fields=['part_number','quantity','frame','material','process','printable','stl','sha256','source_features']
    with (OUT/'PRINT_AND_MACHINING_PARTS.csv').open('w',newline='',encoding='utf-8-sig') as fh:
        w=csv.DictWriter(fh,fieldnames=fields,extrasaction='ignore');w.writeheader();w.writerows(inventory)
    with (OUT/'HARDWARE_REUSE_BUY.csv').open('w',newline='',encoding='utf-8-sig') as fh:
        w=csv.DictWriter(fh,fieldnames=list(hardware_rows[0]),extrasaction='ignore');w.writeheader();w.writerows(hardware_rows)
    z={};rows=[];scene=trimesh.Scene()
    for i,p in enumerate(production):
        v,f=base.a.mesh_data(p['s']);z[str(i)+'v']=v;z[str(i)+'f']=f
        m=trimesh.Trimesh(v,f,process=False);r={k:v for k,v in p.items() if k!='s'};r.update(i=i,volume_mm3=m.volume,mass_centroid_mm=m.center_mass.tolist(),bounds_mm=m.bounds.tolist());rows.append(r)
        mm=m.copy();mm.apply_scale(.001);mm.visual.vertex_colors=np.array([*COLORS.get(p['role'],[.7,.7,.7]),1])*255
        F=FA[p['frame']].copy();F[:3,3]*=.001;scene.add_geometry(mm,node_name=p['name'],transform=F)
    np.savez_compressed(OUT/'production_meshes.npz',**z);put(OUT/'production_assembly.json',dict(parts=rows,units='mm',geometry_sha256=sha(OUT/'assembly_meshes.npz')))
    scene.export(OUT/'O24E_production_assembly.glb')

def validate():
    info=load(OUT/'production_parts.json');rows=[]
    for p in info['structural_parts']:
        m=trimesh.load(OUT/p['stl'],process=True);s=md.Manifold(md.Mesh64(np.array(m.vertices,dtype=np.float64,copy=True,order='C'),np.array(m.faces,dtype=np.uint64,copy=True,order='C')))
        # Principal coordinates avoid a large diagonal sampling box.
        v=np.array(m.vertices);cen=v.mean(0);_,basis=np.linalg.eigh(np.cov(v.T));basis[:,0]*=np.linalg.det(basis)
        local=moved(s,T(-basis.T@cen,basis.T));screen=core(local,.3)
        if len(screen[0]['substantial_core_volumes_mm3'])!=1:screen=core(local,.2)
        cores=len(screen[0]['substantial_core_volumes_mm3'])
        status='PASS_SCREEN' if m.is_watertight and m.volume>0 and cores==1 else 'REVIEW_REQUIRED'
        row=dict(part_number=p['part_number'],watertight=bool(m.is_watertight),components=sum(x.volume()>1e-5 for x in s.decompose()),core_count_0_5=cores,core_screen=screen,status=status)
        rows.append(row);print('CORE',p['part_number'],status,cores,flush=True)
    weak=box([0,0,0],[10,18,6])+box([20,0,0],[30,18,6])+box([9,0,0],[21,18,.2]);strong=box([0,0,0],[10,18,6])+box([20,0,0],[30,18,6])+box([9,0,0],[21,18,3.2])
    controls=dict(weak_bridge_detected=len(core(weak,.25)[0]['substantial_core_volumes_mm3'])==2,strong_bridge_one_core=len(core(strong,.25)[0]['substantial_core_volumes_mm3'])==1)
    put(OUT/'verification/production_parts.json',dict(geometry_sha256=sha(OUT/'assembly_meshes.npz'),status='PASS_SCREEN' if all(r['status']=='PASS_SCREEN' for r in rows) and all(controls.values()) else 'REVIEW_REQUIRED',rows=rows,controls=controls,scope='Actual one-piece material bodies, watertight/connected plus 0.5 mm morphological core. Not FEA or fatigue qualification.'))

def printing():
    # Reuse the already-established native Orca / A1 mini profile, not a mesh-only 3MF.
    check=load(OUT/'verification/production_parts.json')
    assert check['geometry_sha256']==sha(OUT/'assembly_meshes.npz') and check['status']=='PASS_SCREEN','Resolve production-body review before slicing'
    sys.path.insert(0,str(H/'cad/revO24C_T1'));import printing as p
    p.OUT=OUT;p.REVISION='O24E';p.WORK=OUT/'verification/slicer_work'
    rows=[r for r in load(OUT/'production_parts.json')['structural_parts'] if r['printable']];plates=[]
    plate=dict(id='E_PRINT_01',items=[],optional=False,replacement=False);x=y=8.;rowh=0;number=1
    for r in sorted(rows,key=lambda r:-r['print_bounds_mm'][1][1]):
        size=np.array(r['print_bounds_mm'][1])-r['print_bounds_mm'][0];w,h,z=size
        if max(size)>180 or max(size[:2])>164:raise ValueError('Part does not fit A1 mini: '+r['part_number']+str(size))
        if x+w>172:x=8.;y+=rowh+8;rowh=0
        if y+h>172:
            p.project(plate);plates.append(plate);number+=1;plate=dict(id=f'E_PRINT_{number:02d}',items=[],optional=False,replacement=False);x=y=8.;rowh=0
        plate['items'].append(dict(id=r['part_number'],stl=r['stl'],offset_mm=[x,y,0],stl_sha256=r['sha256']));x+=w+8;rowh=max(rowh,h)
    if plate['items']:p.project(plate);plates.append(plate)
    put(OUT/'printing/plates.json',dict(plates=plates,printer='Bambu A1 mini / 180 mm',profile='0.4 nozzle / PLA / 0.12 layer / 5 walls / solid / support / 3 mm brim',manufacturing_release=False))
    for plate in plates:
        try:r=p.run(plate)
        except Exception as e:r=dict(id=plate['id'],passed=False,error=str(e))
        put(OUT/f'verification/slice_{plate["id"]}.json',r)

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('mode',choices=['make','validate','printing']);args=ap.parse_args()
    globals()[args.mode]()
