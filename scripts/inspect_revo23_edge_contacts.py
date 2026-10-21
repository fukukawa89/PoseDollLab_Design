"""Read-only local interface diagnostics for the final measured contacts."""
from build_revo23_continuous import *
from present_revo23 import load_current

ap=argparse.ArgumentParser();ap.add_argument('--report',default='daily_motion.json')
ap.add_argument('--poses',default='daily_poses.json');ap.add_argument('--names',nargs='*')
args=ap.parse_args()
p=read(B/'profiles/device_profile.json');parts=load_current();F=frames(p,p['neutral_raw_deg'])
poses=read(B/'profiles'/args.poses)['poses'];motion=read(B/'verification'/args.report)
groups=rigid_groups(p,{x['token'] for x in parts.values()})
hits=motion.get('blocking_contacts',[dict(pose='N_NEUTRAL',**r) for r in motion.get('new_contacts',[])])
kz=np.load(DROOT/'source/retained_interfaces.npz')
for hit in hits:
    if hit['pose'] not in (args.names or ('upperarm_l.side_raise@60','clavicle_l.elevate.elevate@-15')):continue
    ff=frames(p,poses[hit['pose']])
    for key in hit['pair']:
        item=parts[key]
        if item['role']!='structure':continue
        other=parts[next(k for k in hit['pair'] if k!=key)]
        I=np.linalg.inv(ff[item['token']])
        overlap=item['s']^move(other['s'],I@ff[other['token']])
        world=move(overlap,F[item['token']]);v,_=vf(world)
        print('\nCONTACT',hit['pose'],key,'neutral world bbox',world.bounding_box())
        print('KEEP VOLUME',max(0.,(overlap^solid(kz[key+'|v'],kz[key+'|f'])).volume()))
        for jid in ('clavicle_l.protract','chest','upperarm_l'):
            j=next(j for j in p['joints'] if j['id']==jid)
            M=F['f:'+j['parent']]@np.array(j['parent_to_mount_mm'])
            print('JOINT',jid,'local bbox',move(world,np.linalg.inv(M)).bounding_box())
        candidates=[]
        for k,x in parts.items():
            if x['role']=='structure' or groups[x['token']]!=groups[item['token']]:continue
            s=move(x['s'],F[x['token']]);vv,tt=vf(s)
            bb=np.array(s.bounding_box());wb=np.array(world.bounding_box())
            if np.any(np.minimum(wb[3:],bb[3:]+8)-np.maximum(wb[:3],bb[:3]-8)<=0):continue
            _,dist,_=trimesh.proximity.closest_point_naive(trimesh.Trimesh(vv,tt,process=False),v)
            candidates.append(dict(key=k,role=x['role'],min_surface_distance_mm=float(dist.min()),
                                   overlap_mm3=max(0.,(world^s).volume())))
        print('NEARBY',sorted(candidates,key=lambda a:a['min_surface_distance_mm']))
