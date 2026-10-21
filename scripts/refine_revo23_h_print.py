"""Targeted H slicer-only adjustments; structural STL meshes remain unchanged."""
from print_revo23_h import *

def refine(rid, variant):
    specfile=PRINT/'candidates'/(rid+'.json');spec=read(specfile)
    source_name='endface_caps78' if rid=='O23H-S12' else 'revised_connections'
    if variant=='endface_flip_local':source_name='endface_tilt180_clean'
    reportfile=PRINT/'bambu'/rid/source_name/'checked_result.json';r=read(reportfile)
    c=copy.deepcopy(read((HROOT/r['source_project']).parent/'input.json')['candidate'])
    c.update(name=variant,shield_enforcers=True)
    settings=c.setdefault('settings',{})
    if rid=='O23H-S12':
        caps=[];records=[]
        for i,cap in enumerate(audit_print.manual_caps(HROOT/r['project']).decompose()):
            if not r['caps']['rows'][i]['passed']:
                if variant.startswith('endface_cap_lower'):
                    cap=cap.translate([0,0,-.24])
                    records.append(dict(cap=i+1,z_shift_mm=-.24,reason='Separate the cap bead slab from the next model layer.'))
                else:
                    bb=np.array(cap.bounding_box());top=44.56
                    cap=cap^box(bb[:3]-.01,[bb[3]+.01,bb[4]+.01,top])
                    records.append(dict(cap=i+1,new_top_mm=top,reason='Remove the quantized top layer that approaches the structural wall.'))
            caps.append(cap)
        path=PRINT/'candidates'/(rid+'_'+variant+'.npz')
        save_s(path,move(union(caps),np.linalg.inv(np.array(c['matrix']))))
        c.update(manual_caps=path.relative_to(HROOT).as_posix(),cap_bead_clearance_adjustments=records)
        if variant.startswith('endface_cap_lower'):
            c['blocker_margin_mm']=2.2
            if variant.endswith('snug'):
                c['support']='snug';settings.update(support_angle='45')
    else:
        if r['islands']['external_new_islands'] and variant!='endface_mirror_left':
            c['enforce_sources']=c.get('enforce_sources',[])+([c['enforce_source']] if c.get('enforce_source') else [])
            c['enforce_source']=reportfile.relative_to(HROOT).as_posix()
        if rid=='O23H-S08':
            c.update(support='snug',blocker_margin_mm=1.1)
            if variant=='endface_flip_local':c['blocker_margin_mm']=2.2
            settings.update(support_object_xy_distance='0.6',support_angle='45',bridge_no_support='0')
            if variant.startswith('endface_tilt'):
                angle=variant.removeprefix('endface_tilt').removesuffix('_clean')
                a=np.deg2rad(float(angle))
                R=np.array([[np.cos(a),0,np.sin(a)],[0,1,0],[-np.sin(a),0,np.cos(a)]])@np.array(c['matrix'])[:3,:3]
                m=trimesh.load(HROOT/spec['source']['staged_stl'],process=True)
                M,size=opt.placement(m.vertices,R)
                assert max(size[:2])<170 and size[2]<178,size
                c.update(matrix=M,size_mm=size,metrics=opt.metrics(m,M,[]),blocker_margin_mm=2.2)
                if variant.endswith('_clean'):
                    c['enforce_sources']=[]
                    for name in ('enforce_source','enforce_mesh','manual_caps'):c.pop(name,None)
                    settings.update(support_top_z_distance='0.2',support_bottom_z_distance='0.2')
        elif rid=='O23H-S23':
            c.update(support='snug',blocker_margin_mm=1.1)
            settings.update(support_object_xy_distance='0.6',support_angle='45',support_top_z_distance='0.16',support_bottom_z_distance='0.16',bridge_no_support='0')
            if variant=='endface_mirror_left':
                left=read(PRINT/'candidates/O23H-S18.json')['candidates'][0]
                c.update(support=left['support'],settings=copy.deepcopy(left['settings']),blocker_margin_mm=2.2,enforce_sources=[])
                for name in ('enforce_source','enforce_mesh','manual_caps'):c.pop(name,None)
                flip=np.diag([-1,1,1]);R=flip@np.array(left['matrix'])[:3,:3]@flip
                m=trimesh.load(HROOT/spec['source']['staged_stl'],process=True)
                M,size=opt.placement(m.vertices,R);c.update(matrix=M,size_mm=size)
        elif rid=='O23H-S24':
            c.update(support='snug',blocker_margin_mm=1.1)
            settings.update(support_object_xy_distance='0.5',support_expansion='0',bridge_no_support='0')
        else:raise ValueError(rid)
    parts,p,cfg=load_h();N=frames(p,p['neutral_raw_deg']);part=parts[spec['key']];lines=[]
    if part['role']=='structure':
        T=np.linalg.inv(N[part['token']])
        for rod in connection_records(spec['key'])['rods']:
            pts=np.array(rod['centerline_world_mm'])@T[:3,:3].T+T[:3,3]
            lines.append(dict(points=pts,radius=rod['radius_mm'],mount=rod['mount']))
    m=trimesh.load(HROOT/spec['source']['staged_stl'],process=True)
    c['metrics']=opt.metrics(m,np.array(c['matrix']),lines)
    trial=dict(spec,candidates=[c]);opt.build_candidate(trial,c);result=run_one(trial)
    if result['passed']:
        spec['candidates']=[c]+[x for x in spec['candidates'] if x['name']!=variant];put(specfile,spec)
    print('H REFINEMENT',rid,variant,result['passed'],{k:result[k]['passed'] for k in ('native','clearance','islands','caps')},flush=True)

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('id');ap.add_argument('variant');a=ap.parse_args();configure_print();refine(a.id,a.variant)
