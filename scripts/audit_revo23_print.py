"""Actual support beads vs functional voids and exact STL geometry checks."""
from optimize_revo23_print import *
from o22_f2_gcode import extract_paths
from package_revo22_fins import transform
import shapely
from shapely.geometry import Polygon, LineString
from shapely.ops import unary_union

def read_project(path):
    """Read only normal parts; audit support blockers separately from the STL."""
    P='{http://schemas.microsoft.com/3dmanufacturing/production/2015/06}'
    with zipfile.ZipFile(path) as z:
        docs={k:ET.fromstring(z.read(k)) for k in z.namelist() if k.endswith('.model')}
        root=docs['3D/3dmodel.model'];cfg=ET.fromstring(z.read('Metadata/model_settings.config'));settings=json.loads(z.read('Metadata/project_settings.config'))
    configs={x.get('id'):x for x in cfg.findall('object')};objects={};repairs=[]
    for item in root.findall(Q+'build/'+Q+'item'):
        oid=item.get('objectid');config=configs[oid]
        names={n.get('key'):n.get('value') for n in config.findall('metadata')};normal={p.get('id') for p in config.findall('part') if p.get('subtype')=='normal_part' and not any(n.get('key')=='name' and n.get('value','').startswith('Temporary peel caps') for n in p.findall('metadata'))}
        group=root.find(Q+f'resources/{Q}object[@id="{oid}"]');arrays=[];base=transform(item.get('transform'))
        for c in group.findall(Q+'components/'+Q+'component'):
            if c.get('objectid') not in normal:continue
            doc=docs[c.get(P+'path').lstrip('/')];ob=doc.find(Q+f'resources/{Q}object[@id="{c.get("objectid")}"]')
            mesh=ob.find(Q+'mesh');v=np.array([[float(t.get(k)) for k in 'xyz'] for t in mesh.findall(Q+'vertices/'+Q+'vertex')]);f=np.array([[int(t.get(k)) for k in ('v1','v2','v3')] for t in mesh.findall(Q+'triangles/'+Q+'triangle')])
            T=base@transform(c.get('transform'));arrays.append((v@T[:3,:3].T+T[:3,3],f))
        assert len(arrays)==1;objects[names['name']]=arrays[0]
        for p in config.findall('part'):
            if p.get('subtype')!='normal_part':continue
            stat=p.find('mesh_stat')
            if stat is not None:repairs.append({k:int(stat.get(k,'0')) for k in ('edges_fixed','degenerate_facets','facets_removed','facets_reversed','backwards_edges')})
    return objects,settings,repairs

def manual_caps(path):
    P='{http://schemas.microsoft.com/3dmanufacturing/production/2015/06}'
    with zipfile.ZipFile(path) as z:
        cfg=ET.fromstring(z.read('Metadata/model_settings.config'))
        wanted={p.get('id') for p in cfg.findall('object/part') if any(n.get('key')=='name' and n.get('value','').startswith('Temporary peel caps') for n in p.findall('metadata'))}
        if not wanted:return md.Manifold()
        docs={k:ET.fromstring(z.read(k)) for k in z.namelist() if k.endswith('.model')}
    root=docs['3D/3dmodel.model'];out=[]
    for item in root.findall(Q+'build/'+Q+'item'):
        ob=root.find(Q+f'resources/{Q}object[@id="{item.get("objectid")}"]');base=transform(item.get('transform'))
        for c in ob.findall(Q+'components/'+Q+'component'):
            if c.get('objectid') not in wanted:continue
            mesh=docs[c.get(P+'path').lstrip('/')].find(Q+f'resources/{Q}object[@id="{c.get("objectid")}"]/'+Q+'mesh')
            v=np.array([[float(t.get(k)) for k in 'xyz'] for t in mesh.findall(Q+'vertices/'+Q+'vertex')]);f=np.array([[int(t.get(k)) for k in ('v1','v2','v3')] for t in mesh.findall(Q+'triangles/'+Q+'triangle')])
            out.append(move(solid(v,f),base@transform(c.get('transform'))))
    return union(out)

def paths(path):
    cache=path.parent/'audit_paths.npz';record=path.parent/'audit_paths.json';digest=sha(path)
    if cache.exists() and record.exists() and read(record)['project_sha256']==digest and read(record).get('widths') and (not read(record)['report'].get('manual_caps') or read(record)['report']['manual_caps'].get('classifier_version')==3):
        return read(record)['report'],np.load(cache)['a']
    report,raw=extract_paths(path,arc_tolerance_mm=.02,max_arc_segment_mm=1.)
    a=np.frombuffer(raw,dtype=np.float32).reshape(-1,9)
    caps=manual_caps(path)
    if not caps.is_empty():
        a=np.c_[a,np.zeros(len(a),dtype=np.float32)];components=caps.decompose()
        bodies,_,_=read_project(path);body=union([solid(*vf) for vf in bodies.values()])
        for lid in np.unique(a[:,6]).astype(int):
            ix=np.flatnonzero((a[:,6]==lid)&(a[:,7]==0));lines=a[ix]
            if not len(lines):continue
            z=float(lines[:,5].max());h=report['layers'][lid].get('height_mm') or .16
            # Thin caps can be wider in G-code than their CAD cross-section.
            # Classify the whole segment using five samples and the actual
            # half bead width, requiring every sample to be nearer the cap
            # than the real model. A fixed 0.06 mm point test missed cap edges.
            samples=lines[:,:2,None]+(lines[:,3:5,None]-lines[:,:2,None])*np.linspace(0,1,5)
            points=shapely.points(samples.transpose(0,2,1).reshape(-1,2));body_section=None
            for ci,cap in enumerate(components):
                # A rigid XML round-trip can tilt a nominally planar cap face
                # by a few micrometres. Union +/-0.0001 mm sections so sampling
                # exactly on that face does not arbitrarily lose half the cap.
                section=polygon(md.CrossSection.batch_boolean([cap.slice(z-h/2+d) for d in (-.0001,0,.0001)],md.OpType.Add))
                if section.is_empty:continue
                if body_section is None:body_section=polygon(md.CrossSection.batch_boolean([body.slice(z-h/2+d) for d in (-.0001,0,.0001)],md.OpType.Add))
                dc=shapely.distance(points,section).reshape(-1,5)
                db=shapely.distance(points,body_section).reshape(-1,5) if not body_section.is_empty else np.full_like(dc,np.inf)
                hit=np.all(dc<=lines[:,8,None]/2+.03,axis=1)&np.all(dc+.01<db,axis=1)
                a[ix[hit],7]=1;a[ix[hit],9]=ci+1
        report['manual_caps']=dict(classifier_version=3,count=len(components),nominal_solid_mass_g=caps.volume()*.00124,classified_segments=int(sum(a[:,9]>0)),
            method='Five samples per segment within the actual half bead width+0.03 mm of the cap section and all nearer the cap than the body; +/-0.0001 mm section tolerance at nominally planar faces. Source paths unchanged.')
    np.savez_compressed(cache,a=a);put(record,dict(project_sha256=digest,report=report,widths=True))
    return report,a

def cap_audit(result):
    path=B/result['project'];caps=manual_caps(path)
    if caps.is_empty():return dict(passed=True,count=0)
    objs,settings,_=read_project(path);body=solid(*objs[result['id']]);report,a=paths(path);rows=[]
    model=a[a[:,7]==0];model_z=np.unique(model[:,5]);model_polygons={}
    def bead_polygon(lines):
        return shapely.union_all(shapely.buffer(shapely.linestrings(lines[:,[0,1,3,4]].reshape(-1,2,2)),lines[:,8]/2,quad_segs=4))
    def height(lines):
        return report['layers'][int(lines[0,6])].get('height_mm') or float(settings['layer_height'])
    for ci,cap in enumerate(caps.decompose()):
        lines=a[a[:,9]==ci+1]
        if not len(lines):
            rows.append(dict(index=ci+1,volume_mm3=cap.volume(),omitted_by_slicer=True,passed=False))
            continue
        z=float(lines[:,5].min());first=lines[abs(lines[:,5]-z)<.001]
        region=shapely.union_all(shapely.buffer(shapely.linestrings(first[:,[0,1,3,4]].reshape(-1,2,2)),first[:,8]/2,quad_segs=3))
        base=a[(a[:,5]<z-.1)&(a[:,5]>z-.65)&(a[:,9]==0)]
        material=shapely.union_all(shapely.buffer(shapely.linestrings(base[:,[0,1,3,4]].reshape(-1,2,2)),base[:,8]/2+.15,quad_segs=3)) if len(base) else Polygon()
        contact=region.intersection(material).area
        # Caps are sliced as temporary normal parts. Layer rounding can make a
        # nominally clear cap fuse to a sidewall; check actual beads as slabs.
        bead_gap=1.
        for cz in np.unique(lines[:,5]):
            cl=lines[abs(lines[:,5]-cz)<.001];cp=bead_polygon(cl);ch=height(cl)
            for mz in model_z[abs(model_z-cz)<.8]:
                if float(mz) not in model_polygons:
                    ml=model[abs(model[:,5]-mz)<.001]
                    model_polygons[float(mz)]=(bead_polygon(ml),height(ml))
                mp,mh=model_polygons[float(mz)]
                vertical=max(float(cz)-ch-float(mz),float(mz)-mh-float(cz),0.)
                bead_gap=min(bead_gap,math.hypot(cp.distance(mp),vertical))
        row=dict(index=ci+1,volume_mm3=cap.volume(),minimum_model_gap_mm=cap.min_gap(body,1.),first_z_mm=z,first_layer_contact_mm2=contact,
            minimum_actual_bead_gap_mm=bead_gap,
            passed=cap.min_gap(body,.18)>=.179 and bead_gap>=.149 and (z<=float(settings['initial_layer_print_height'])+.001 or contact>.05))
        rows.append(row)
    out=dict(method_version=2,path_classification_version=report['manual_caps']['classifier_version'],count=len(rows),rows=rows,nominal_solid_mass_g=report['manual_caps']['nominal_solid_mass_g'],passed=all(r['passed'] for r in rows),
        scope='Temporary caps: closed nominal geometry, >=0.18 mm nominal model separation; actual declared-width bead slabs >=0.15 mm apart, allowing 0.001 mm rounding; starting layer supported. Physical removal not tested.')
    put(path.parent/'caps_audit.json',out);return out

def polygon(cs):
    result=[]
    for component in cs.decompose():
        outer=[];holes=[]
        for p in component.to_polygons():
            area=np.sum(p[:,0]*np.roll(p[:,1],-1)-p[:,1]*np.roll(p[:,0],-1))/2
            (outer if area>0 else holes).append(p)
        for p in outer:result.append(shapely.make_valid(Polygon(p,holes)))
    return shapely.union_all(result,grid_size=.00001) if result else Polygon()

def clean2d(p):
    return shapely.set_precision(shapely.make_valid(p),.0001)

def void_audit(result,aperture_revision=None):
    rid=result['id'];path=B/result['project'];folder=path.parent;dest=folder/('clearance.json' if aperture_revision is None else f'clearance_geometry_v{aperture_revision}.json')
    report,a=paths(path);classification=report.get('manual_caps',{}).get('classifier_version',0)
    if dest.exists() and read(dest)['project_sha256']==sha(path) and read(dest).get('method_version')==2 and read(dest).get('path_classification_version',0)==classification:return read(dest)
    rev=aperture_revision or result.get('guard_revision',1);gdir=OUT/(f'guards_v{rev}' if rev>1 else 'guards')
    M=np.array(result['matrix']);n=np.load(gdir/(rid+'.npz'));guard=move(solid(n['v'],n['f']),M)
    w=np.load(gdir/(rid+'_wire.npz'));wire=move(solid(w['v'],w['f']),M)
    a=a.astype(float)
    sel=a[np.isin(a[:,7],[1,2,3])];layers=np.unique(sel[:,6]).astype(int)
    width=max([.42]+[x['line_width_range_mm'][1] for x in report['classes'][1:4] if x['line_width_range_mm']])
    rows=[];wrows=[]
    for lid in layers:
        lines=sel[sel[:,6]==lid];z=float(lines[:,5].max());h=report['layers'][lid].get('height_mm') or .16
        # Union lower/middle/upper slices over the deposited support thickness.
        masks=[]
        for solidmask in (guard,wire):
            if solidmask.is_empty():masks.append(Polygon());continue
            ps=[polygon(solidmask.slice(float(q))) for q in (z-h+.001,z-h/2,z-.001)]
            masks.append(unary_union(ps))
        if all(p.is_empty for p in masks):continue
        seg=shapely.linestrings(lines[:,[0,1,3,4]].reshape(-1,2,2))
        # Conservative full declared bead width plus arc chord tolerance.
        beads=shapely.buffer(seg,lines[:,8]/2+.02,quad_segs=3)
        for mask,target in zip(masks,(rows,wrows)):
            if mask.is_empty:continue
            hit=shapely.intersects(beads,mask)
            if np.any(hit):
                intersection=shapely.intersection(beads[hit],mask)
                ar=float(shapely.area(shapely.union_all(intersection)))
                if ar>1e-4:target.append(dict(layer=int(lid),z_mm=z,overlap_area_mm2=ar,segments=int(sum(hit))))
    out=dict(id=rid,name=result['name'],project_sha256=sha(path),method_version=2,path_classification_version=classification,guard_revision=rev,source_blocker_revision=result.get('guard_revision',1),guard_sha256=sha(gdir/(rid+'.npz')),
        support_bead_width_mm=width,arc_margin_mm=.02,functional_void_hits=rows,wire_void_hits=wrows,
        total_layer_overlap_area_mm2=sum(r['overlap_area_mm2'] for r in rows),wire_total_layer_overlap_area_mm2=sum(r['overlap_area_mm2'] for r in wrows),
        passed=not rows,wire_passed=not wrows,
        scope='Actual support/interface/transition LINE_WIDTH per segment plus0.02 mm arc margin; lower/middle/upper cross-sections per support layer. Local clearance screen, no physical removal guarantee.')
    put(dest,out);print('VOID',rid,result['name'],'layers',len(rows),'wire',len(wrows),flush=True)
    return out

def starting_islands(result):
    """Find actual printed model islands with neither prior material nor support.

    Uses actual LINE_WIDTH bead footprints and a0.025 mm contact allowance.
    A normal support separation is deliberately included in the vertical search.
    A bridge whose ends are anchored is connected; its span is a trial-print item.
    """
    path=B/result['project'];dest=path.parent/'islands.json'
    report,a=paths(path);classification=report.get('manual_caps',{}).get('classifier_version',0)
    if dest.exists() and read(dest)['project_sha256']==sha(path) and read(dest).get('method_version')==2 and read(dest).get('path_classification_version',0)==classification:return classify_islands(result,read(dest))
    support={};model={}
    for lid in np.unique(a[:,6]).astype(int):
        rows=a[a[:,6]==lid];z=float(rows[:,5].max())
        for ids,table in (([0],model),([1,2,3],support)):
            lines=rows[np.isin(rows[:,7],ids)]
            if not len(lines):continue
            seg=shapely.linestrings(lines[:,[0,1,3,4]].reshape(-1,2,2))
            buffers=shapely.orient_polygons(shapely.buffer(seg,np.maximum(lines[:,8]/2,.0001),quad_segs=3))
            table[z]=md.CrossSection([np.round(np.asarray(g.exterior.coords)[:-1],4) for g in buffers if not g.is_empty])
    previous=md.CrossSection();issues=[];supported=[]
    heights=sorted(model);support_heights=np.array(sorted(support));overhang=[]
    for zi,z in enumerate(heights):
        cur=model[z];components=cur.decompose()
        nearby=support_heights[(support_heights<=z-.10)&(support_heights>=z-.65)]
        base=md.CrossSection.batch_boolean([support[float(t)] for t in nearby],md.OpType.Add).offset(.15,circular_segments=16) if len(nearby) else md.CrossSection()
        if zi>0:
            prev=previous.offset(.025,circular_segments=16)
            for c in components:
                if c.area()<.05:continue
                contact=float((c^prev).area())
                if contact<.002:
                    sup=float((c^base).area());row=dict(z_mm=z,area_mm2=c.area(),bounds_mm=c.bounds(),support_contact_mm2=sup)
                    (supported if sup>.01 else issues).append(row)
        previous=cur
    out=dict(id=result['id'],name=result['name'],project_sha256=sha(path),method_version=2,path_classification_version=classification,unbacked_new_islands=issues,support_backed_new_islands=supported,
        wider_bridges_or_cantilevers=overhang,model_first_z_mm=heights[0] if heights else None,model_last_z_mm=heights[-1] if heights else None,
        passed=not issues and bool(heights) and heights[0]<=.201,
        scope='Actual G-code LINE_WIDTH footprints, Manifold/Clipper booleans at0.0001 mm, predecessor allowance0.025 mm. Connected bridges and supported overhang finish still require first-article inspection. Not physical extrusion or strength certification.')
    put(dest,out);print('ISLAND',result['id'],result['name'],'unbacked',len(issues),'wide',len(overhang),flush=True)
    return classify_islands(result,out)

def classify_islands(result,raw):
    """Separate enclosed infill gaps from truly unsupported external geometry.

    Uses the established O22 audit's previous-solid/bounding-box99.5% rule;
    retains every raw unbacked footprint and its actual overlap evidence.
    """
    path=B/result['project'];dest=path.parent/'islands_classified.json'
    if dest.exists() and read(dest).get('method_version')==4 and read(dest)['project_sha256']==sha(path) and read(dest).get('raw_island_report_sha256')==sha(path.parent/'islands.json'):return read(dest)
    objects,settings,_=read_project(path);v,f=objects[result['id']];host=solid(v,f)
    report,a=paths(path);heights=np.sort(np.unique(a[a[:,7]==0,5])).astype(float)
    rows=[]
    for r in raw['unbacked_new_islands']:
        idx=int(np.argmin(abs(heights-r['z_mm'])));previous=heights[idx-1];previous_previous=heights[idx-2] if idx>1 else 0.
        nominal=host.slice(float((previous+previous_previous)/2));section=nominal.offset(.015,circular_segments=16)
        bb=r['bounds_mm'];region=md.CrossSection.square([bb[2]-bb[0],bb[3]-bb[1]]).translate(bb[:2])
        fraction=float((region^section).area()/max(region.area(),1e-12))
        core_fraction=0.;interior_tiny=False
        if fraction<=.995 and r['area_mm2']<.5:
            # A tiny closed perimeter can start over an interior infill gap.
            # Its 0.4 mm bead bbox can cross a nearby cavity despite the whole
            # extrusion centreline being inside the preceding nominal solid.
            # Require a 0.025 mm tube around every actual segment, with no CAD
            # dilation; retain the raw unsupported-bead evidence separately.
            lines=a[(abs(a[:,5]-r['z_mm'])<.001)&(a[:,7]==0)]
            mid=(lines[:,:2]+lines[:,3:5])/2
            lines=lines[(mid[:,0]>=bb[0])&(mid[:,0]<=bb[2])&(mid[:,1]>=bb[1])&(mid[:,1]<=bb[3])]
            if len(lines):
                buffers=shapely.orient_polygons(shapely.buffer(shapely.linestrings(lines[:,[0,1,3,4]].reshape(-1,2,2)),.025,quad_segs=3))
                core=md.CrossSection([np.round(np.asarray(g.exterior.coords)[:-1],5)for g in buffers if not g.is_empty])
                core_fraction=float((core^nominal).area()/max(core.area(),1e-12))
                interior_tiny=core_fraction>.995
        rows.append(dict(r,previous_solid_bbox_coverage=fraction,tiny_path_core_coverage=core_fraction,tiny_path_interior_probe_mm=.025,
            small_internal_path_classified=interior_tiny,inside_previous_solid_geometry=fraction>.995 or interior_tiny,
            previous_solid_section_z_mm=(previous+previous_previous)/2))
    external=[r for r in rows if not r['inside_previous_solid_geometry']];internal=[r for r in rows if r['inside_previous_solid_geometry']]
    out=dict(raw,method_version=4,raw_island_report_sha256=sha(path.parent/'islands.json'),classified_islands=rows,
        external_new_islands=external,internal_infill_gaps=internal,required_first_layer_z_mm=float(settings['initial_layer_print_height']),passed=not external and raw['model_first_z_mm'] is not None and abs(raw['model_first_z_mm']-float(settings['initial_layer_print_height']))<.001,
        scope='All raw unsupported beads remain recorded. Internal starts require >99.5% bbox coverage with the established +0.015 mm CAD allowance, or, only for footprints <0.5 mm2, >99.5% coverage of a 0.025 mm tube around their actual extrusion centrelines by the undilated preceding nominal solid. This distinguishes small perimeter starts above interior infill gaps from exterior unsupported geometry; it does not certify physical infill or bridge strength. All remaining exterior islands must be absent.')
    put(dest,out);print('CLASSIFY',result['id'],result['name'],'external',len(external),'internal',len(internal),flush=True);return out

def native_audit(result):
    rid=result['id'];before,_,_=read_project(B/result['source_project']);after,settings,repairs=read_project(B/result['project'])
    v,f=before[rid];w,g=after[rid];same=np.array_equal(f,g);err=float(abs(v-w).max()) if v.shape==w.shape else 1e9
    m=trimesh.Trimesh(w,g,process=False)
    r=dict(id=rid,project_sha256=sha(B/result['project']),same_indices=same,vertex_shift_mm=err,watertight=bool(m.is_watertight),
        winding=bool(m.is_winding_consistent),components=len(m.split(only_watertight=False)),repairs=sum(sum(x.values()) for x in repairs),
        min_mm=w.min(0),max_mm=w.max(0),matrix_is_rigid=bool(np.allclose(np.array(result['matrix'])[:3,:3].T@np.array(result['matrix'])[:3,:3],np.eye(3),atol=1e-9)))
    r['passed']=bool(same and err<.0002 and r['watertight'] and r['winding'] and r['components']==1 and r['repairs']==0 and r['matrix_is_rigid'] and w.min()>-.0001 and w.max()<180.0001)
    put((B/result['project']).parent/'native.json',r);return r

def job(x):
    row,mode=x
    return starting_islands(row) if mode else void_audit(row)

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--ids',nargs='*');ap.add_argument('--names',nargs='*');ap.add_argument('--selected',action='store_true');ap.add_argument('--clears',action='store_true');ap.add_argument('--islands',action='store_true');ap.add_argument('--workers',type=int,default=2);a=ap.parse_args()
    if a.selected:rows=[r['selected'] for r in read(OUT/'selection.json')['rows'] if r['selected']]
    else:rows=[read(x) for x in (OUT/'trials').glob('*/*/result.json') if read(x)['passed']]
    jobs=[]
    for row in rows:
        if a.ids and row['id'] not in a.ids:continue
        if a.names and row['name'] not in a.names:continue
        if a.clears and 'clear' not in row['name']:continue
        jobs.append((row,a.islands))
    with concurrent.futures.ProcessPoolExecutor(max_workers=a.workers) as pool:list(pool.map(job,jobs))
