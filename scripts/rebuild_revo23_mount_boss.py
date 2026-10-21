"""Redesign a printed mounting head around a full, buried circular stem end.

This is a local, convex load-spreading carrier extension, not a supplementary
rod. Native fastener locations/material are retained. Every added head is tested
against functional apertures and every adjacent-motion state; the whole part's
native-to-wall minimum cut is screened independently before acceptance.
"""
from repair_revo23_endfaces import *
from audit_revo23_load_paths import screen

def relieve_head(head,native,space):
    """Functional bearing/fastener clearances in the head, never in the stem."""
    used=[]
    for _ in range(180):
        ok,why=space.clear(head-native)
        if ok:return head,used
        row=next(x for x in space.records if x['key']==why['part'] and x['pose']==why['pose'])
        obstacle=row['solid'];vertices,_=vf(obstacle)
        # A convex envelope avoids reproducing decorative/mesh details. A 0.2 mm
        # Cartesian clearance is included; original native material is restored.
        padding=np.array(list(itertools.product((-.2,.2),repeat=3)))
        relief=md.Manifold.hull_points((vertices[:,None,:]+padding).reshape(-1,3))
        head-=relief;used.append(dict(part=why['part'],pose=why['pose'],clearance_mm=.2))
    raise RuntimeError('Carrier relief did not converge')

def repair(key,index,ends=('source',),baseline_record=False):
    parts,p,cfg=load_h();N=frames(p,p['neutral_raw_deg']);M=N[parts[key]['token']];I=np.linalg.inv(M)
    report=copy.deepcopy(connection_records(key))
    if baseline_record:report['rods'][index]=copy.deepcopy(read(GHISTORY/'connections'/(key.replace('/','__')+'.json'))['rods'][index])
    r=report['rods'][index];original=copy.deepcopy(r)
    hosts=native_hosts(key,parts,p,N);radius=r['radius_mm'];space=Space(key,parts,p,N,False);wires=move(wire_spaces(key),M)
    heads={};diagnosis=[];full=np.array(r['centerline_world_mm'])
    if len(full)==2:full=np.linspace(full[0],full[1],max(12,int(np.linalg.norm(full[1]-full[0])*1.5)))
    if 'target_mount' not in r:
        for trim in (0,1,2,3,4):
            q=full if trim==0 else full[:-trim]
            if face_witness(wall_pad(r),q[-1],q[-2]-q[-1],radius)['passed']:
                r['wall_foot_reference_endpoint_world_mm']=r.get('wall_foot_reference_endpoint_world_mm',full[-1]);full=q;break
        else:raise RuntimeError(('wall end needs rerouting',key,index))
    for end in ends:
        path=full if end=='source' else full[::-1];mount=r['mount'] if end=='source' else r['target_mount'];native=hosts[mount]
        found=False;fails={}
        for trim in (0,1,2,3,4,6,8,10,14):
            if trim>=len(path)-3:continue
            pts=path[trim:].copy();a=pts[0];d=pts[1]-a;d/=np.linalg.norm(d)
            if trim==0 and len(pts)>3 and np.dot(d,pts[2]-pts[1])<0:continue
            probe=cyl(a-d*1.4,a+d*1.2,radius+.7)
            body=positive_round_sweep(pts,radius) if len(pts)>2 else cyl(*pts,radius)
            if (body^wires).volume()>.01:fails['stem aperture']=fails.get('stem aperture',0)+1;continue
            ok,why=space.clear(body)
            if not ok:fails['stem '+why['part']]=fails.get('stem '+why['part'],0)+1;continue
            for span in (6.,8.,10.,12.,15.):
              for shift in (0.,-4.,4.):
                center=a+d*shift
                anchor=native^box(center-span,center+span)
                if anchor.volume()<60:continue
                head=md.Manifold.hull_points(np.vstack([vf(anchor)[0],vf(probe)[0]]))
                # Only named, original functional voids may cross the carrier;
                # a complete circular stem is never trimmed by this operation.
                head-=wires
                head,reliefs=relieve_head(head,native,space)
                if len([s for s in head.decompose() if s.volume()>.001])!=1:continue
                if not face_witness(native+head,a,d,radius)['passed']:continue
                added=head-native;ok,why=space.clear(added)
                if not ok:fails[why['part']]=fails.get(why['part'],0)+1;continue
                updated=copy.deepcopy(r);newfull=pts if end=='source' else pts[::-1]
                updated['centerline_world_mm']=newfull
                updated.pop(end+'_socket',None)
                if end=='source':updated.pop('source_feet',None)
                testrecords=copy.deepcopy(report['rods']);testrecords[index]=updated
                candidate=preserved_material(key,parts,p,N)+union(list(heads.values()))+head+structural_connectors(testrecords)
                s=move(candidate,I);cc=[c for c in s.decompose() if c.volume()>.001]
                if len(cc)!=1:continue
                strength=screen(key,cc[0],native_keep(key),clean_skin(key),1.)
                values=[q['conservative_cut_area_mm2'] for q in strength['rows']]
                if not values or min(values)<20:
                    fails['section below 20']=fails.get('section below 20',0)+1;continue
                heads[mount]=head;full=newfull;r=updated;found=True
                diagnosis.append(dict(end=end,mount=mount,trimmed_centerline_points=trim,
                    added_volume_mm3=added.volume(),native_overlap_mm3=(head^native).volume(),
                    anchor_box_span_mm=2*span,minimum_part_cut_area_mm2=min(values),
                    functional_clearances=reliefs,
                    source_end_face=face_witness(native+head,a,d,radius),all_adjacent_states_clear=True,
                    functional_void_overlap_mm3=(head^wires).volume()))
                print('INTEGRATED MOUNT',key,end,'trim',trim,'span',span,'cut',min(values),flush=True)
                break
              if found:break
            if found:break
        if not found:raise RuntimeError(('No sound complete mounting boss',key,end,fails))
    dest=HROOT/'mount_reinforcement';dest.mkdir(exist_ok=True)
    for mount,head in heads.items():
        path=dest/(key.replace('/','__')+f'__m{mount}.npz');save_s(path,move(head,I))
        put(path.with_suffix('.json'),dict(part=key,mount=mount,geometry_sha256=sha(path),source_geometry_sha256=GHASH,
            method='Local convex integrated carrier head; full stem end buried, original hardware apertures and native material retained.',
            checks=[q for q in diagnosis if q['mount']==mount]))
    r.update(positive_cells=True,method='Round stem with complete end purchase in a locally redesigned integrated mounting head.',
        integrated_mount_checks=diagnosis)
    r.pop('foot_only',None);report['rods'][index]=r
    s=move(preserved_material(key,parts,p,N)+structural_connectors(report['rods']),I)
    cc=[c for c in s.decompose() if c.volume()>.001];assert len(cc)==1
    path=HROOT/(key.replace('/','__')+'.npz');save_s(path,cc[0]);report.update(revision=HREV,candidate_sha256=sha(path),source_geometry_sha256=GHASH,components=1)
    put(path.with_suffix('.json'),report);print('MOUNT REBUILT',key,index,flush=True)

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('key');ap.add_argument('index',type=int);ap.add_argument('--both',action='store_true');ap.add_argument('--baseline-record',action='store_true');a=ap.parse_args()
    repair(a.key,a.index,('source','target') if a.both else ('source',),a.baseline_record)
