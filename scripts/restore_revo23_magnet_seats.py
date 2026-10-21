"""Restore original F7 negative space around fixed magnet-cartridge fittings."""
from build_revo23_continuous import *
from present_revo23 import load_current
import itertools

ap=argparse.ArgumentParser();ap.add_argument('--apply',action='store_true');args=ap.parse_args()
p=read(B/'profiles/device_profile.json');parts=load_current();base,_,_=load_baseline()
q=read(B/'profiles/default_pose.json')['raw_deg'];F=frames(p,q);O=frames(kin.profile,q)
audit=read(B/'verification/fixed_all_interfaces.json');digest=sha(B/'assembly.npz')
assert audit['geometry_sha256']==digest
z=np.load(DROOT/'source/retained_interfaces.npz');keeps={k:z[k] for k in z.files}
cuts={};rows=[]
grouped={}
for hit in audit['new_contacts']:
    key=next(k for k in hit['pair'] if parts[k]['role']=='structure')
    other=next(k for k in hit['pair'] if k!=key)
    assert other.startswith(('elbow_l.flex/','elbow_r.flex/','chest/C02_magnet_'))
    grouped.setdefault(key,[]).append((other,hit))
for key,entries in grouped.items():
    print('SEAT GROUP',key,[x[0] for x in entries],flush=True)
    I=np.linalg.inv(F[parts[key]['token']])
    natives={};envelopes=[];donor_transforms=[]
    for other,hit in entries:
        native=move(parts[other]['s'],I@F[parts[other]['token']]);natives[other]=native
        vv,_=vf(native)
        envelopes.append(md.Manifold.hull_points(np.vstack([vv+np.array(off)*.25 for off in itertools.product((-1,1),repeat=3)])))
        donor_transforms.append(I@F[parts[other]['token']]@np.linalg.inv(O[base[other]['token']])@O[base[key]['token']])
    assert max(np.max(abs(t-donor_transforms[0])) for t in donor_transforms)<1e-8
    envelope=union(envelopes)
    # Transfer the exact original frame around the same unchanged purchased
    # or printed fitting; remove only space that was already empty in F7.
    donor=move(base[key]['s'],donor_transforms[0])
    bb=np.array(envelope.bounding_box())
    donor=donor^box(bb[:3]-1.,bb[3:]+1.)
    print('LOCAL F7 DONOR',donor.volume(),flush=True)
    cut=envelope-donor
    print('LOCAL VOID',cut.volume(),flush=True)
    before=parts[key]['s'];after=before-cut;removed=before-after
    skinpath=DROOT/(key.replace('/','__')+'_skin.npz');sz=np.load(skinpath)
    common=dict(key=key,removed_material_mm3=max(0.,removed.volume()),
        original_F7_positive_material_removed_mm3=max(0.,(removed^donor).volume()),
        radial_skin_removed_mm3=max(0.,(removed^solid(sz['v'],sz['f'])).volume()))
    for other,hit in entries:
        rec=dict(common,fitting=other,original_overlap_mm3=hit['overlap_mm3'],
                 resulting_overlap_mm3=max(0.,(after^natives[other]).volume()))
        assert rec['resulting_overlap_mm3']<.05 and rec['original_F7_positive_material_removed_mm3']<.001 and rec['radial_skin_removed_mm3']<.001,rec
        rows.append(rec);print('SEAT RESTORED',rec,flush=True)
    parts[key]['s']=after;cuts[key]=cut
needs_reconnection=[]
for key in cuts:
    s=parts[key]['s'];cc=sorted(s.decompose(),key=lambda x:-x.volume())
    kept=solid(keeps[key+'|v'],keeps[key+'|f'])-cuts[key]
    skin=np.load(DROOT/(key.replace('/','__')+'_skin.npz'));skin=solid(skin['v'],skin['f'])
    debris=[c for c in cc[1:] if 0<c.volume()<1 and (c^kept).volume()<.001 and (c^skin).volume()<.001]
    assert sum(c.volume() for c in debris)<1
    if debris:s=union([c for c in cc if c not in debris]);parts[key]['s']=s
    v,f=vf(s);m=trimesh.Trimesh(v,f,process=False)
    print('SEAT TOPOLOGY',key,[(c.volume(),(c^kept).volume()) for c in s.decompose()],m.is_watertight,flush=True)
    assert m.is_watertight,key
    if len([c for c in s.decompose() if c.volume()>1e-4])>1:needs_reconnection.append(key)
put(B/'verification/magnet_seat_restoration.json',dict(input_geometry_sha256=digest,rows=rows,
    needs_web_reconnection=needs_reconnection,
    unchanged_fittings=True,method='Restore original F7 frame voids in each exact native fitting coordinate system; subtractive only.',
    manufacturing_release=False))
if not args.apply:
    print(json.dumps(rows,indent=2),flush=True);sys.exit(0)
checkpoint=DROOT/'checkpoints'/('before_magnet_seats_'+digest[:12]);checkpoint.mkdir(parents=True,exist_ok=True)
shutil.copy2(B/'assembly.npz',checkpoint/'assembly.npz')
shutil.copy2(DROOT/'source/retained_interfaces.npz',checkpoint/'retained_interfaces.npz')
rz=np.load(DROOT/'source/interface_edge_reliefs.npz');reliefs={k:rz[k] for k in rz.files}
meta=read(DROOT/'source/interface_edge_reliefs.json')
for key,cut in cuts.items():
    path=DROOT/(key.replace('/','__')+'.npz');rp=path.with_suffix('.json')
    shutil.copy2(path,checkpoint/path.name);shutil.copy2(rp,checkpoint/rp.name)
    v,f=vf(parts[key]['s']);np.savez_compressed(path,v=v,f=f)
    keep=solid(keeps[key+'|v'],keeps[key+'|f'])-cut
    keeps[key+'|v'],keeps[key+'|f']=vf(keep)
    total=cut
    if key+'|v' in reliefs:total=total+solid(reliefs[key+'|v'],reliefs[key+'|f'])
    reliefs[key+'|v'],reliefs[key+'|f']=vf(total)
    r=read(rp);r.update(component_count=len([c for c in parts[key]['s'].decompose() if c.volume()>1e-4]),
        source_watertight=True,volume_mm3=parts[key]['s'].volume(),
        needs_web_reconnection=key in needs_reconnection,
        retained_interface_loss_mm3=max(0.,(keep-parts[key]['s']).volume()),
        restored_F7_magnet_seats=[x for x in rows if x['key']==key])
    put(rp,r)
np.savez_compressed(DROOT/'source/retained_interfaces.npz',**keeps)
np.savez_compressed(DROOT/'source/interface_edge_reliefs.npz',**reliefs)
kh=sha(DROOT/'source/retained_interfaces.npz');meta['approved_keeps_sha256']=kh;meta['restored_F7_magnet_seats']=rows
put(DROOT/'source/interface_edge_reliefs.json',meta)
for rp in DROOT.glob('frame__*.json'):
    r=read(rp);r['validated_keeps_sha256']=kh
    r['magnet_seat_input_revalidation']='Only original F7 negative space is restored; no material added. Final actual-solid verification follows.'
    put(rp,r)
print('RESTORED',len(rows),'F7 fitting cavities in',len(cuts),'parts','RECONNECT',needs_reconnection,flush=True)
