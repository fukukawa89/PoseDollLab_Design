"""Relieve measured joint-edge contacts while protecting actual interfaces.

No pose or limit is removed. Candidate changes are subtractive only. Shoulder
bearing housings and all fixed hardware have explicit guards; the full wrist
donor land and forearm bearing cup are retained. Every result is rechecked.
"""
from build_revo23_continuous import *
from present_revo23 import load_current
import itertools

PCB_CLIP_NUT_GUARD_MM=1.2

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--apply',action='store_true')
    ap.add_argument('--report',default='daily_motion.json');ap.add_argument('--poses',default='daily_poses.json')
    ap.add_argument('--output',default='joint_edge_reliefs.json')
    ap.add_argument('--include-edge',action='store_true');ap.add_argument('--include-fixed',action='store_true')
    args=ap.parse_args()
    p=read(B/'profiles/device_profile.json');parts=load_current();F=frames(p,p['neutral_raw_deg'])
    motion=read(B/'verification'/args.report);digest=sha(B/'assembly.npz')
    assert motion['geometry_sha256']==digest and not motion['trial']
    assert motion['complete_policy'] or args.report=='edge_paths.json'
    kz=np.load(DROOT/'source/retained_interfaces.npz')
    keeps={k:solid(kz[k+'|v'],kz[k+'|f']) for k,v in parts.items() if v['role']=='structure'}
    groups=rigid_groups(p,{v['token'] for v in parts.values()})
    poses=read(B/'profiles'/args.poses)['poses']
    hits=list(motion['blocking_contacts'])
    if args.include_edge:
        extra=read(B/'verification/edge_paths.json');assert extra['geometry_sha256']==digest
        hits+=extra['blocking_contacts'];poses.update(read(B/'profiles/edge_path_poses.json')['poses'])
    if args.include_fixed:
        fixed=read(B/'verification/fixed_interfaces.json');assert fixed['geometry_sha256']==digest
        hits+=[dict(pose='N_NEUTRAL',**r) for r in fixed['new_contacts']]
    cuts={};guards={};rows=[];failures=[]

    def guard(key):
        if key in guards:return guards[key]
        item=parts[key];N=F[item['token']];I=np.linalg.inv(N);keep=keeps[key]
        if key=='frame/chest':
            windows=[];bearing=[]
            for side in ('l','r'):
                j=next(j for j in p['joints'] if j['id']=='clavicle_'+side+'.protract')
                M=I@F['f:'+j['parent']]@np.array(j['parent_to_mount_mm'])
                windows.append(move(box([-19.5,-19.5,-11.5],[15,10,14.5]),M))
                bearing.append(move(box([-14.4,-9.4,-10.9],[14.4,9.4,-2.1]),M))
            # Measured lower-left mounting-land corner lies >8 mm from every
            # fixed native part and outside the central bearing envelope.
            j=next(j for j in p['joints'] if j['id']=='chest')
            M=I@F['f:'+j['parent']]@np.array(j['parent_to_mount_mm'])
            windows.append(move(box([-27,-15.5,19],[ -21,-8.5,25]),M))
            previous=DROOT/'checkpoints/before_collar_clock_180/source'
            if previous.exists():
                # Preserve the unchanged, already fitted neck/trunk lands.
                # Re-extraction after collar clocking can also carry along
                # nonfunctional remnants of the former shared carrier.
                op=read(previous/'device_profile.json');OF=frames(op,op['neutral_raw_deg'])
                oz=np.load(previous/'retained_interfaces.npz')
                oldkeep=solid(oz[key+'|v'],oz[key+'|f']);oldwindows=[]
                for side in ('l','r'):
                    oj=next(j for j in op['joints'] if j['id']=='clavicle_'+side+'.protract')
                    OM=np.linalg.inv(OF['f:chest'])@OF['f:'+oj['parent']]@np.array(oj['parent_to_mount_mm'])
                    oldwindows.append(move(box([-19.5,-19.5,-11.5],[15,10,14.5]),OM))
                result=(oldkeep-union(oldwindows)-union(windows))+union(bearing)
            else:result=(keep-union(windows))+union(bearing)
        elif key in ('frame/clavicle_l.protract_frame','frame/clavicle_r.protract_frame'):
            side='l' if '_l.' in key else 'r'
            j=next(j for j in p['joints'] if j['id']=='clavicle_'+side+'.protract')
            M=I@F['f:'+j['parent']]@np.array(j['parent_to_mount_mm'])
            tail=move(box([15,-25,-12],[36,25,18]),M)
            cup=move(box([-11.8,-11.8,-1.8],[14.3,11.8,10.1]),M)
            result=(keep-tail)+cup
        elif key=='frame/forearm_r':
            z=np.load(DROOT/'source/separate_forearm_lands.npz')
            tag='frame/forearm_l|wrist_l'
            donor=solid(z[tag+'|v'],z[tag+'|f'])
            W=F['j:wrist_r:C02']@np.diag([-1.,-1.,-1.,1.])@np.linalg.inv(F['j:wrist_l:C02'])
            result=move(donor,I@W@F['f:forearm_l'])
            result+=move(box([-11.8,-11.8,-1.8],[14.3,11.8,10.1]),I@F['j:forearm_r.twist:child'])
        else:result=keep
        guards[key]=result
        return result

    seen_hits=set();frame_cache={}
    for hit in hits:
        if hit['pose'] not in frame_cache:frame_cache[hit['pose']]=frames(p,poses[hit['pose']])
        ff=frame_cache[hit['pose']];options=[]
        pair=tuple(sorted(hit['pair']))
        relative=np.linalg.inv(ff[parts[pair[0]]['token']])@ff[parts[pair[1]]['token']]
        signature=(pair,tuple(np.round(relative,7).ravel()))
        if signature in seen_hits:continue
        seen_hits.add(signature)
        for key in hit['pair']:
            if parts[key]['role']!='structure':continue
            other=next(k for k in hit['pair'] if k!=key)
            T=np.linalg.inv(ff[parts[key]['token']])@ff[parts[other]['token']]
            overlap=parts[key]['s']^move(parts[other]['s'],T)
            if overlap.volume()<1e-6:continue
            options.append(((overlap^keeps[key]).volume(),key,other,overlap,T))
        if not options:
            assert any(parts[k]['role']=='structure' for k in hit['pair']),('hardware-only failure requires redesign',hit)
            continue
        attempts=[]
        for _,key,other,overlap,T in options:
            v,_=vf(overlap)
            padded=md.Manifold.hull_points(np.vstack([v+np.array(off)*.4 for off in itertools.product((-1,1),repeat=3)]))
            removable=parts[key]['s']^padded
            protected=guard(key)
            blocked=[dict(key='functional_land_guard',volume_mm3=max(0.,(overlap^protected).volume()))]
            # Preserve 2 mm around each actual fixed part. Individual convex
            # envelopes include the entire part, including screw heads and pins.
            if key in ('frame/chest','frame/forearm_r','frame/clavicle_l.protract_frame','frame/clavicle_r.protract_frame'):
                rb=np.array(removable.bounding_box())
                for k,item in parts.items():
                    if item['role']=='structure' or groups[item['token']]!=groups[parts[key]['token']]:continue
                    if k==other or (other.startswith('head/') and k.startswith('head/')):continue
                    s=move(item['s'],np.linalg.inv(F[parts[key]['token']])@F[item['token']])
                    bb=np.array(s.bounding_box())
                    if np.any(np.minimum(rb[3:],bb[3:]+2)-np.maximum(rb[:3],bb[:3]-2)<=0):continue
                    vv,_=vf(s)
                    margin=2.
                    if k.startswith('o22/backpack_screw_') or k in tuple('clavicle_'+side+'.protract/pcb_clip_'+suffix for side in ('l','r') for suffix in ('nut','screw')):
                        # This small nut retains the PCB clip, not the bearing
                        # or friction preload. Reserve 1.2 mm radially at its
                        # relieved corner; other nut faces retain the original
                        # stock. Bearing protection remains unchanged.
                        margin=PCB_CLIP_NUT_GUARD_MM if k.endswith('_nut') else 2.
                        sphere=trimesh.creation.icosphere(subdivisions=2,radius=1.)
                        inradius=float(np.min(np.einsum('ij,ij->i',sphere.face_normals,sphere.triangles[:,0])))
                        offsets=sphere.vertices*(margin/inradius)
                    else:offsets=np.array(list(itertools.product((-2.,2.),repeat=3)))
                    envelope=md.Manifold.hull_points(np.vstack([vv+off for off in offsets]))
                    volume=max(0.,(overlap^envelope).volume())
                    if volume>1e-5:blocked.append(dict(key=k,volume_mm3=volume,guard_margin_mm=margin))
                    protected=protected+envelope
            cut=padded-protected
            new=parts[key]['s']-cut
            remaining=max(0.,float((new^move(parts[other]['s'],T)).volume()))
            skinpath=DROOT/(key.replace('/','__')+'_skin.npz')
            skin=np.load(skinpath) if skinpath.exists() else None
            removed=parts[key]['s']-new
            rec=dict(pose=hit['pose'],key=key,other=other,before_overlap_mm3=hit['overlap_mm3'],
                     residual_overlap_mm3=remaining,removed_material_mm3=max(0.,removed.volume()),
                     original_keep_removed_mm3=max(0.,(removed^keeps[key]).volume()),
                     radial_skin_removed_mm3=max(0.,(removed^solid(skin['v'],skin['f'])).volume()) if skin is not None else 0.,
                     protected_material_removed_mm3=max(0.,(removed^protected).volume()),
                     blocked_by=blocked,padding_mm=.4,guard_fixed_part_margin_mm=2,
                     pcb_clip_nut_radial_guard_mm=PCB_CLIP_NUT_GUARD_MM if key=='frame/chest' else None)
            attempts.append((rec,key,new,cut))
        rec,key,new,cut=min(attempts,key=lambda a:(a[0]['residual_overlap_mm3']>.05,a[0]['original_keep_removed_mm3']))
        rec['alternative_attempts']=[a[0].copy() for a in attempts if a[1]!=key]
        remaining=rec['residual_overlap_mm3']
        rows.append(rec);print('RELIEF',rec,flush=True)
        if remaining>.05:failures.append(rec)
        parts[key]['s']=new;cuts[key]=cuts.get(key,md.Manifold())+cut

    fragments=[]
    for key,item in parts.items():
        if item['role']!='structure':continue
        components=sorted(item['s'].decompose(),key=lambda s:-s.volume())
        debris=[s for s in components[1:] if 0<s.volume()<.01]
        if not debris:continue
        removed=sum(s.volume() for s in debris);assert removed<.02,(key,removed)
        item['s']=union([s for s in components if s not in debris])
        fragments.append(dict(key=key,removed_fragments_mm3=[s.volume() for s in debris]))
    topology=[]
    for key,item in parts.items():
        if item['role']!='structure':continue
        v,f=vf(item['s']);mesh=trimesh.Trimesh(v,f,process=False)
        topology.append(dict(key=key,components=len([c for c in item['s'].decompose() if c.volume()>1e-4]),
                             watertight=bool(mesh.is_watertight),winding_consistent=bool(mesh.is_winding_consistent)))
    valid=all(r['components']==1 and r['watertight'] and r['winding_consistent'] for r in topology)
    intact_skin=all(r['radial_skin_removed_mm3']<.001 for r in rows)
    report=dict(input_geometry_sha256=digest,profile_sha256=profile_signature(p),
        rows=rows,unresolved=failures,removed_fragments=fragments,topology=topology,
        topology_passed=valid,radial_skin_unchanged=intact_skin,
        input_contact_records=len(hits),unique_relative_contacts=len(seen_hits),manufacturing_release=False)
    put(B/'verification'/args.output,report)
    if not args.apply or failures:return
    assert valid and intact_skin,('Topology or radial-skin change requires review',report)
    checkpoint=DROOT/'checkpoints'/('edges_before_'+digest[:12]);checkpoint.mkdir(parents=True,exist_ok=True)
    shutil.copy2(B/'verification'/args.report,checkpoint/args.report)
    for name,include in [('edge_paths.json',args.include_edge),('fixed_interfaces.json',args.include_fixed)]:
        if include:shutil.copy2(B/'verification'/name,checkpoint/name)
    shutil.copy2(DROOT/'source/retained_interfaces.npz',checkpoint/'retained_interfaces.npz')
    previous_keeps=sha(DROOT/'source/retained_interfaces.npz');out={k:kz[k] for k in kz.files};cut_data={}
    prior_reliefs=[];original_keeps=previous_keeps
    old_cuts=DROOT/'source/interface_edge_reliefs.npz'
    if old_cuts.exists():
        zold=np.load(old_cuts);cut_data={k:zold[k] for k in zold.files}
        oldmeta=read(old_cuts.with_suffix('.json'));prior_reliefs=oldmeta['rows']
        original_keeps=oldmeta['original_keeps_sha256']
        shutil.copy2(old_cuts,checkpoint/old_cuts.name)
        shutil.copy2(old_cuts.with_suffix('.json'),checkpoint/old_cuts.with_suffix('.json').name)
    for key,cut in cuts.items():
        newkeep=keeps[key]-cut
        out[key+'|v'],out[key+'|f']=vf(newkeep)
        cumulative=cut
        if key+'|v' in cut_data:cumulative=cumulative+solid(cut_data[key+'|v'],cut_data[key+'|f'])
        cut_data[key+'|v'],cut_data[key+'|f']=vf(cumulative)
    np.savez_compressed(DROOT/'source/retained_interfaces.npz',**out)
    np.savez_compressed(DROOT/'source/interface_edge_reliefs.npz',**cut_data)
    new_keeps=sha(DROOT/'source/retained_interfaces.npz')
    put(DROOT/'source/interface_edge_reliefs.json',dict(profile_sha256=profile_signature(p),
        original_keeps_sha256=original_keeps,approved_keeps_sha256=new_keeps,rows=prior_reliefs+rows))
    for key,item in parts.items():
        if item['role']!='structure':continue
        path=DROOT/(key.replace('/','__')+'.npz');rp=path.with_suffix('.json')
        r=read(rp)
        changed=key in cuts or any(x['key']==key for x in fragments)
        if changed:
            shutil.copy2(path,checkpoint/path.name);shutil.copy2(rp,checkpoint/rp.name)
            v,f=vf(item['s']);np.savez_compressed(path,v=v,f=f)
            keep=solid(out[key+'|v'],out[key+'|f'])
            r.update(component_count=len([x for x in item['s'].decompose() if x.volume()>1e-4]),
                source_watertight=bool(trimesh.Trimesh(v,f,process=False).is_watertight),
                volume_mm3=item['s'].volume(),retained_interface_loss_mm3=max(0.,(keep-item['s']).volume()),
                joint_edge_reliefs=[x for x in prior_reliefs+rows if x['key']==key],
                detached_fragments_removed=[x for x in fragments if x['key']==key])
        r['validated_keeps_sha256']=new_keeps
        r['keep_input_revalidation']=dict(original_hash=previous_keeps,current_hash=new_keeps,
            proof='Only recorded material subtraction. Unchanged carriers were constructed against a superset of the revised neighbouring lands; final actual-solid checks remain mandatory.')
        put(rp,r)
    print('APPLIED RELIEFS',len(cuts),'fragment cleanup',len(fragments),flush=True)


if __name__=='__main__':main()
