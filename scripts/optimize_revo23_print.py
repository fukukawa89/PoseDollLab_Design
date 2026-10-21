"""Frozen O23G STL -> measured A1 mini PLA orientation/support candidates.

No CAD edits, hole filling, model scaling, printer access, or upstream output
overwrites. The selected meshes must remain exact rigid copies of the checked
STLs. Geometric layer-direction scores are screening proxies, not strength tests.
"""
from revo23_export import *
from o22_support_gcode import inspect_gcode
import xml.etree.ElementTree as ET
import subprocess, concurrent.futures, time, re, math

OUT=B/'print_optimization_G'
BASE=EXPORT_ROOT/'slicing'
Q='{http://schemas.microsoft.com/3dmanufacturing/core/2015/02}'
ORCA=Path('D:/ProgramFiles/OrcaSlicer/orca-slicer.exe')
ET.register_namespace('',Q[1:-1])
ET.register_namespace('p','http://schemas.microsoft.com/3dmanufacturing/production/2015/06')

def frame(d):
    z=np.asarray(d,float);z=z/np.linalg.norm(z)
    x=np.cross(np.eye(3)[np.argmin(abs(z))],z);x/=np.linalg.norm(x)
    return np.array([x,np.cross(z,x),z])

def placement(v,F):
    # Keep at least 5 mm for brim and support roots within the 180 mm bed.
    best=None
    for degrees in range(0,90,5):
        a=np.deg2rad(degrees);Rz=np.array([[np.cos(a),-np.sin(a),0],[np.sin(a),np.cos(a),0],[0,0,1]])
        R=Rz@F;w=v@R.T;size=np.ptp(w,axis=0)
        score=max(size[:2])*100+np.prod(size[:2])*.02
        if best is None or score<best[0]:best=(score,R,w,size)
    _,R,w,size=best;M=np.eye(4);M[:3,:3]=R
    M[:3,3]=np.r_[90-(w.min(0)[:2]+w.max(0)[:2])/2,-w[:,2].min()]
    return M,size

def rod_lines(row,N,items):
    path=B/'design/smooth_candidate'/(row['key'].replace('/','__')+'.json')
    if not path.exists():return []
    out=[];T=np.linalg.inv(N[items[row['key']]['token']])
    for r in read(path).get('rods',[]):
        pts=np.array(r['centerline_world_mm'])@T[:3,:3].T+T[:3,3]
        out.append(dict(points=pts,radius=r['radius_mm'],mount=r['mount']))
    return out

def rod_metric(lines,d):
    angles=[];weighted=[]
    for r in lines:
        vec=np.diff(r['points'],axis=0);length=np.linalg.norm(vec,axis=1);good=length>.001
        cosine=abs(vec[good]@d)/length[good]
        angles.extend(np.rad2deg(np.arcsin(np.clip(cosine,0,1))))
        weighted.extend(zip(cosine**2,length[good]*r['radius']**2))
    return dict(max_rod_angle_to_bed_deg=max(angles,default=0.),
        rod_verticality=float(sum(x*w for x,w in weighted)/sum(w for x,w in weighted)) if weighted else 0.)

def metrics(m,M,lines):
    d=M[2,:3];lo=-M[2,3];z=m.triangles_center@d-lo;nz=m.face_normals@d
    area=m.area_faces;down=(nz<-.7071068)&(z>.25)
    projected=area[down]*-nz[down]
    top=(m.triangles@d-lo).max(axis=1)
    bed=float((area*np.maximum(0,-nz)*(top<.21)).sum())
    rod=rod_metric(lines,d)
    return dict(overhang_area_mm2=float(projected.sum()),
        overhang_projection_volume_proxy_mm3=float((projected*z[down]).sum()),
        bed_contact_projection_mm2=bed,**rod)

def initialize():
    OUT.mkdir(parents=True,exist_ok=True)
    rows=read(EXPORT_ROOT/'repair.json')['rows'];p=read(B/'profiles/device_profile.json')
    N=frames(p,p['neutral_raw_deg']);items={x['key']:x for x in read(B/'assembly.json')['items']}
    sources={str(x.relative_to(B)):sha(x) for x in [B/'assembly.npz',B/'profiles/device_profile.json',B/'harness/wire_seats.json',B/'harness/wire_channels.json']}
    sources['cad_parameters']=sha(CFG)
    put(OUT/'source_lock.json',dict(files=sources,stls={r['id']:r['stl_sha256'] for r in rows},
        geometry_revision='O23G-smooth-seated-connections-20261021',physical_print_tested=False))
    for row in rows:
        rid=row['id'];m=trimesh.load(B/row['staged_stl'],process=True)
        assert sha(B/row['staged_stl'])==row['stl_sha256']
        lines=rod_lines(row,N,items);oldM=np.array(read(BASE/rid/'input.json')['matrix'])
        normals={}
        for n,a in zip(np.round(m.face_normals,3),m.area_faces):
            k=tuple(n);normals[k]=normals.get(k,0.)+a
        dirs=[oldM[2,:3]]+[np.array(k)*sgn for k in np.eye(3) for sgn in (-1,1)]
        dirs += [-np.array(k) for k,a in sorted(normals.items(),key=lambda x:-x[1])[:20]]
        # Broad faces dominate the bed-contact screen. Add directions aligned
        # with the wire-seat inward normals to expose small passages upward.
        for s in read(B/'harness/wire_seats.json')['seats']:
            if s['part']==row['key']:
                T=np.array(s['transform_body_mm']);dirs += [T[:3,1],-T[:3,1]]
        for r in lines:
            v=r['points'][-1]-r['points'][0]
            if np.linalg.norm(v)>.01:dirs += [d for d in frame(v)[:2]]
        seen=[];candidates=[]
        for d in dirs:
            d=d/np.linalg.norm(d)
            if any(np.dot(d,q)>.99999 for q in seen):continue
            seen.append(d)
            M,size=placement(m.vertices,frame(d))
            if max(size[:2])>170 or size[2]>178:continue
            met=metrics(m,M,lines)
            met['score']=met['overhang_projection_volume_proxy_mm3']/1000+25*met['rod_verticality']+30/(met['bed_contact_projection_mm2']+1)+size[2]*.015
            candidates.append(dict(matrix=M,size_mm=size,metrics=met))
        candidates.sort(key=lambda c:c['metrics']['score'])
        selected=[]
        for c in candidates:
            d=np.array(c['matrix'])[2,:3]
            if c['metrics']['bed_contact_projection_mm2']<2:continue
            if any(np.dot(d,np.array(s['matrix'])[2,:3])>.97 for s in selected):continue
            selected.append(c)
            if len(selected)==4:break
        old=dict(matrix=oldM,size_mm=np.ptp(m.vertices@oldM[:3,:3].T,axis=0),metrics=metrics(m,oldM,lines))
        chosen=[dict(name='base_tree',support='tree',**old),dict(name='base_snug',support='snug',**old)]
        chosen += [dict(name=f'pose{i+1}_tree',support='tree',**c) for i,c in enumerate(selected)]
        put(OUT/'candidates'/f'{rid}.json',dict(id=rid,key=row['key'],stl_sha256=row['stl_sha256'],
            source=row,rod_lines=lines,ranked=candidates,candidates=chosen))
        print('RANK',rid,'poses',len(candidates),'selected',len(chosen),'score',round(selected[0]['metrics']['score'],1) if selected else None,flush=True)

def profile(style,rid):
    # Slow, reproducible structural PLA process; no shape-changing overhang or
    # hole compensation options. Horizontal rods receive more perimeter roads.
    p=dict(print_settings_id='O23G A1 mini PLA / removable supports',layer_height='0.16',initial_layer_print_height='0.2',
        wall_loops='5',sparse_infill_density='20%',sparse_infill_pattern='gyroid',top_shell_layers='5',bottom_shell_layers='5',
        outer_wall_speed='40',inner_wall_speed='65',sparse_infill_speed='90',internal_solid_infill_speed='70',
        top_surface_speed='35',bridge_speed='20',initial_layer_speed='20',initial_layer_infill_speed='25',
        default_acceleration='1500',outer_wall_acceleration='700',inner_wall_acceleration='1000',
        enable_support='1',support_type='tree(auto)' if style=='tree' else 'normal(auto)',
        support_style='tree_slim' if style=='tree' else 'snug',support_on_build_plate_only='0',
        support_threshold_angle='40',support_critical_regions_only='0',support_remove_small_overhang='0',
        support_top_z_distance='0.2',support_bottom_z_distance='0.2',support_object_xy_distance='0.4',
        support_interface_top_layers='2',support_interface_bottom_layers='2',support_interface_spacing='0.35',
        support_base_pattern='default',support_base_pattern_spacing='3',support_expansion='0',
        tree_support_branch_diameter='2',tree_support_branch_distance='4',
        tree_support_wall_count='1',tree_support_auto_brim='1',independent_support_layer_height='1',
        bridge_no_support='1',max_bridge_length='8',brim_type='outer_only',brim_width='4',brim_object_gap='0.15',
        skirt_loops='0',print_sequence='by layer',enable_prime_tower='0',elefant_foot_compensation='0.15')
    if rid.startswith('O23G-W') or rid=='O23G-C03':p.update(wall_loops='4')
    return p

def build_candidate(row,c):
    rid=row['id'];work=OUT/'trials'/rid/c['name'];work.mkdir(parents=True,exist_ok=True)
    with zipfile.ZipFile(BASE/rid/'input.3mf') as z:data={n:z.read(n) for n in z.namelist()}
    root=ET.fromstring(data['3D/3dmodel.model']);item=root.find(Q+'build/'+Q+'item')
    M=np.array(c['matrix']);item.set('transform',' '.join(f'{x:.17g}' for x in M[:3,:].T.flat))
    data['3D/3dmodel.model']=ET.tostring(root,encoding='utf-8',xml_declaration=True)
    enforcers=[]
    caps=md.Manifold()
    if c.get('manual_caps'):
        n=np.load(B/c['manual_caps']);caps=move(solid(n['v'],n['f']),M)
        enforcers.extend([caps.translate([0,0,z]) for z in (-.1,0,.1)])
    if c.get('enforce_mesh'):
        n=np.load(B/c['enforce_mesh']);enforcers.append(move(solid(n['v'],n['f']),M))
    for enforce_source in c.get('enforce_sources',[])+([c['enforce_source']] if c.get('enforce_source') else []):
        rr=read(B/enforce_source);before=np.array(rr['matrix']);change=M@np.linalg.inv(before)
        for issue in rr['islands']['external_new_islands']:
            x0,y0,x1,y1=issue['bounds_mm'];z=issue['z_mm']
            enforcers.append(move(box([x0-.35,y0-.35,z-.6],[x1+.35,y1+.35,z+.25]),change))
    enforce=union(enforcers)
    if c.get('protect_voids'):
        # The mask is a separate slicer-only support blocker, never printable
        # geometry. A column above each void prevents a support grown from a
        # higher overhang from travelling through the protected aperture.
        rev=c.get('guard_revision',1);gdir=OUT/(f'guards_v{rev}' if rev>1 else 'guards')
        n=np.load(gdir/(rid+'.npz'));guard=move(solid(n['v'],n['f']),M)
        if c.get('shield_enforcers') and not enforce.is_empty():
            # A local contact request must never punch through the actual bore
            # or wire void. Only remove its shadow where a contact is clear.
            near=guard^box(np.array(enforce.bounding_box()[:3])-1,np.array(enforce.bounding_box()[3:])+1)
            shield=union([near.translate([x,y,z]) for x in (-.35,0,.35) for y in (-.35,0,.35) for z in (-.16,0,.16)])
            enforce=enforce-shield
        blockers=[];top=float(c['size_mm'][2])+1
        if c.get('block_mode')=='local':
            margin=c.get('blocker_margin_mm',.3)
            blockers=[guard.translate([x,y,z]) for x in (-margin,0,margin) for y in (-margin,0,margin) for z in (-.3,0,.3)]
        else:
            for component in guard.decompose():
                bb=component.bounding_box();cs=component.project().offset(c.get('blocker_margin_mm',.8),circular_segments=16)
                if not cs.is_empty():blockers.append(cs.extrude(max(.1,top-bb[2]+.3)).translate([0,0,bb[2]-.3]))
        exclusion=union(blockers)
        if c.get('strict_void_columns'):
            # A contact above a bore must not open a vertical support path
            # through that bore. Keep the complete exclusion column.
            enforce=enforce-exclusion
        block=move(exclusion-enforce,np.linalg.inv(M));bv,bf=vf(block)
        sub=ET.fromstring(data['3D/Objects/object_1.model']);resources=sub.find(Q+'resources')
        ob=ET.SubElement(resources,Q+'object',{'id':'100','type':'model','name':'Functional void support exclusion'})
        mesh=ET.SubElement(ob,Q+'mesh');vs=ET.SubElement(mesh,Q+'vertices');fs=ET.SubElement(mesh,Q+'triangles')
        for vtx in bv:ET.SubElement(vs,Q+'vertex',{k:f'{x:.12g}' for k,x in zip('xyz',vtx)})
        for face in bf:ET.SubElement(fs,Q+'triangle',{k:str(x) for k,x in zip(('v1','v2','v3'),face)})
        P='{http://schemas.microsoft.com/3dmanufacturing/production/2015/06}'
        ET.SubElement(root.find(Q+'resources/'+Q+'object/'+Q+'components'),Q+'component',{'objectid':'100',P+'path':'/3D/Objects/object_1.model','transform':'1 0 0 0 1 0 0 0 1 0 0 0'})
        cfg=ET.fromstring(data['Metadata/model_settings.config']);ob=cfg.find('object')
        part=ET.SubElement(ob,'part',{'id':'100','subtype':'support_blocker'})
        ET.SubElement(part,'metadata',{'key':'name','value':'Keep holes and wiring clear — non-printing support blocker'})
        ET.SubElement(part,'metadata',{'key':'matrix','value':'1 0 0 0 0 1 0 0 0 0 1 0 0 0 0 1'})
        data['Metadata/model_settings.config']=ET.tostring(cfg,encoding='utf-8',xml_declaration=True)
        data['3D/3dmodel.model']=ET.tostring(root,encoding='utf-8',xml_declaration=True)
        data['3D/Objects/object_1.model']=ET.tostring(sub,encoding='utf-8',xml_declaration=True)
        np.savez_compressed(work/'support_blocker.npz',v=bv,f=bf)
    if not enforce.is_empty():
        ev,ef=vf(move(enforce,np.linalg.inv(M)))
        sub=ET.fromstring(data['3D/Objects/object_1.model']);resources=sub.find(Q+'resources')
        ob=ET.SubElement(resources,Q+'object',{'id':'101','type':'model','name':'Local exterior island support contacts'})
        mesh=ET.SubElement(ob,Q+'mesh');vs=ET.SubElement(mesh,Q+'vertices');fs=ET.SubElement(mesh,Q+'triangles')
        for vtx in ev:ET.SubElement(vs,Q+'vertex',{k:f'{x:.12g}' for k,x in zip('xyz',vtx)})
        for face in ef:ET.SubElement(fs,Q+'triangle',{k:str(x) for k,x in zip(('v1','v2','v3'),face)})
        P='{http://schemas.microsoft.com/3dmanufacturing/production/2015/06}'
        ET.SubElement(root.find(Q+'resources/'+Q+'object/'+Q+'components'),Q+'component',{'objectid':'101',P+'path':'/3D/Objects/object_1.model','transform':'1 0 0 0 1 0 0 0 1 0 0 0'})
        cfg=ET.fromstring(data['Metadata/model_settings.config']);part=ET.SubElement(cfg.find('object'),'part',{'id':'101','subtype':'support_enforcer'})
        ET.SubElement(part,'metadata',{'key':'name','value':'Local support contacts — non-printing enforcer'})
        ET.SubElement(part,'metadata',{'key':'matrix','value':'1 0 0 0 0 1 0 0 0 0 1 0 0 0 0 1'})
        data['Metadata/model_settings.config']=ET.tostring(cfg,encoding='utf-8',xml_declaration=True)
        data['3D/3dmodel.model']=ET.tostring(root,encoding='utf-8',xml_declaration=True)
        data['3D/Objects/object_1.model']=ET.tostring(sub,encoding='utf-8',xml_declaration=True)
    if not caps.is_empty():
        cv,cf=vf(move(caps,np.linalg.inv(M)))
        sub=ET.fromstring(data['3D/Objects/object_1.model']);resources=sub.find(Q+'resources')
        ob=ET.SubElement(resources,Q+'object',{'id':'102','type':'model','name':'Temporary peel caps'})
        mesh=ET.SubElement(ob,Q+'mesh');vs=ET.SubElement(mesh,Q+'vertices');fs=ET.SubElement(mesh,Q+'triangles')
        for vtx in cv:ET.SubElement(vs,Q+'vertex',{k:f'{x:.12g}' for k,x in zip('xyz',vtx)})
        for face in cf:ET.SubElement(fs,Q+'triangle',{k:str(x) for k,x in zip(('v1','v2','v3'),face)})
        P='{http://schemas.microsoft.com/3dmanufacturing/production/2015/06}'
        ET.SubElement(root.find(Q+'resources/'+Q+'object/'+Q+'components'),Q+'component',{'objectid':'102',P+'path':'/3D/Objects/object_1.model','transform':'1 0 0 0 1 0 0 0 1 0 0 0'})
        cfg=ET.fromstring(data['Metadata/model_settings.config']);part=ET.SubElement(cfg.find('object'),'part',{'id':'102','subtype':'normal_part'})
        ET.SubElement(part,'metadata',{'key':'name','value':'Temporary peel caps - REMOVE after printing'})
        ET.SubElement(part,'metadata',{'key':'extruder','value':'1'})
        data['Metadata/model_settings.config']=ET.tostring(cfg,encoding='utf-8',xml_declaration=True)
        data['3D/3dmodel.model']=ET.tostring(root,encoding='utf-8',xml_declaration=True)
        data['3D/Objects/object_1.model']=ET.tostring(sub,encoding='utf-8',xml_declaration=True)
    settings=json.loads(data['Metadata/project_settings.config']);settings.update(profile(c['support'],rid));settings.update(c.get('settings',{}))
    data['Metadata/project_settings.config']=json.dumps(settings).encode()
    source=work/'input.3mf'
    with zipfile.ZipFile(source,'w',zipfile.ZIP_DEFLATED) as z:
        for n,b in data.items():z.writestr(n,b)
    put(work/'input.json',dict(id=rid,key=row['key'],stl_sha256=row['stl_sha256'],candidate=c,source_sha256=sha(source)))
    return work,source

def measure(path):
    report=inspect_gcode(path,arc_tolerance_mm=.03,max_arc_segment_mm=2.)
    with zipfile.ZipFile(path) as z:
        code=z.read('Metadata/plate_1.gcode').decode();settings=json.loads(z.read('Metadata/project_settings.config'))
        cfg=ET.fromstring(z.read('Metadata/model_settings.config'))
    t=re.search(r'total estimated time\s*[:=]\s*([^\n]+)',code)
    times=t.group(1) if t else ''
    seconds=sum(float(n)*dict(d=86400,h=3600,m=60,s=1)[u] for n,u in re.findall(r'(\d+(?:\.\d+)?)\s*([dhms])',times))
    masses={x['id']:x.get('estimated_mass_g',0) for x in report['classes']}
    repairs=sum(int(s.get(k,'0')) for s in cfg.findall('.//mesh_stat') for k in ('edges_fixed','degenerate_facets','facets_removed','facets_reversed','backwards_edges'))
    return dict(project_sha256=sha(path),gcode_sha256=report['gcode_sha256'],support_g=sum(masses[x] for x in ('support','interface','transition')),
        model_g=masses['model'],brim_g=masses['brim'],total_deposited_g=sum(masses.values()),estimated_s=seconds,
        repairs=repairs,bed_violations=report['out_of_bed_segment_count'],layers=len(report['layers']),
        warnings=report['warnings'],classes=report['classes'],settings={k:settings.get(k) for k in profile('tree','').keys()},
        passed=repairs==0 and report['out_of_bed_segment_count']==0 and report['extrusion_moves']>10)

def run_job(job):
    row,c=job;work,source=build_candidate(row,c);dest=work/'sliced.3mf'
    command=[str(ORCA),'--allow-newer-file','--arrange','0','--slice','0','--debug','3','--export-3mf',str(dest),str(source)]
    start=time.time()
    with (work/'console.log').open('wb') as log:
        proc=subprocess.Popen(command,cwd=work,stdout=log,stderr=log,creationflags=subprocess.CREATE_NO_WINDOW)
        try:code=proc.wait(timeout=900)
        except subprocess.TimeoutExpired:proc.terminate();code=proc.wait(timeout=15)
    r=dict(id=row['id'],key=row['key'],name=c['name'],matrix=c['matrix'],metrics=c['metrics'],support=c['support'],guard_revision=c.get('guard_revision',1),
        project=dest.relative_to(B).as_posix(),source_project=source.relative_to(B).as_posix(),returncode=code,command=command,elapsed_s=time.time()-start,passed=False)
    if code==0 and dest.exists():r.update(measure(dest))
    put(work/'result.json',r)
    print('SLICE',r['id'],r['name'],r['passed'],'support',r.get('support_g'),'g','model',r.get('model_g'),'g',flush=True)
    return r

def baseline():
    rows=[]
    for r in read(BASE/'results.json')['rows']:
        out=dict(id=r['id'],key=r['key'],project=r['project'],**measure(B/r['project']))
        rows.append(out);print('BASE',r['id'],round(out['support_g'],2),'g',flush=True)
    put(OUT/'baseline.json',dict(rows=rows,total_support_g=sum(r['support_g'] for r in rows),total_s=sum(r['estimated_s'] for r in rows)))

def select():
    rows=[]
    for f in sorted((OUT/'candidates').glob('*.json')):
        spec=read(f);trials=[read(x) for x in (OUT/'trials'/spec['id']).glob('*/result.json')]
        for t in trials:
            # No nearly vertical critical connection solely for a tiny support saving.
            t['selection_score']=t.get('support_g',1e6)+15*t['metrics']['rod_verticality']+t.get('estimated_s',1e9)/20000
        for r in trials:
            cp=(B/r['project']).parent/'clearance.json';ip=(B/r['project']).parent/'islands.json'
            r['clearance_passed']=read(cp)['passed'] if cp.exists() else False
            r['islands_passed']=read(ip)['passed'] if ip.exists() and read(ip).get('method_version')==2 else None
        passed=sorted([r for r in trials if r['passed'] and r['clearance_passed'] and r['islands_passed'] is not False],key=lambda r:r['selection_score'])
        rows.append(dict(id=spec['id'],key=spec['key'],selected=passed[0] if passed else None,trials=trials))
        if passed:print('BEST',spec['id'],passed[0]['name'],round(passed[0]['support_g'],2),'g','rod',round(passed[0]['metrics']['max_rod_angle_to_bed_deg'],1),flush=True)
    put(OUT/'selection.json',dict(rows=rows,passed=all(r['selected'] for r in rows)))

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('mode',choices=['init','slice','baseline','select']);ap.add_argument('--ids',nargs='*');ap.add_argument('--names',nargs='*');ap.add_argument('--workers',type=int,default=3);a=ap.parse_args()
    if a.mode=='init':initialize()
    elif a.mode=='baseline':baseline()
    elif a.mode=='select':select()
    else:
        jobs=[]
        for f in sorted((OUT/'candidates').glob('*.json')):
            row=read(f)
            if a.ids and row['id'] not in a.ids:continue
            for c in row['candidates']:
                if a.names and c['name'] not in a.names:continue
                path=OUT/'trials'/row['id']/c['name']/'result.json'
                if path.exists() and read(path)['passed']:continue
                jobs.append((row,c))
        with concurrent.futures.ThreadPoolExecutor(max_workers=a.workers) as pool:list(pool.map(run_job,jobs))
