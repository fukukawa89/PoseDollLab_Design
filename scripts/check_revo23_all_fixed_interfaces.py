"""Audit every new carrier's fixed mates against the original F7 fitted pair."""
import verify_revo23 as v
from revo23_daily import rigid_groups

parts=v.load_current();base,_,_=v.load_baseline();p=v.read(v.B/'profiles/device_profile.json')
v.cases=lambda profile,suite:{'A_STAND_35':v.read(v.B/'profiles/default_pose.json')['raw_deg']}
result=v.motion(parts,base,p,'fixed_reference')
groups=rigid_groups(p,{x['token'] for x in parts.values()})
rows=[r for case in result['rows'] for r in case['contacts']
      if groups[parts[r['pair'][0]]['token']]==groups[parts[r['pair'][1]]['token']]]
hits=[r for r in rows if r['increased']]
report=dict(geometry_sha256=v.sha(v.B/'assembly.npz'),rows=rows,new_contacts=hits,
    passed=not hits,pose_count=1,
    scope='Every new carrier, redesigned wrist part and moved controller part versus fixed rigid mates; five random configurations establish rigid grouping. Same-pair fitted F7 overlaps and wrist ankle-donor fits are recorded explicitly.',
    physical_tested=False,manufacturing_release=False)
v.put(v.B/'verification/fixed_all_interfaces.json',report)
print('ALL FIXED INTERFACES',not hits,len(hits),flush=True)
for r in hits:print(r,flush=True)
seat_path=v.B/'verification/magnet_seat_restoration.json'
if seat_path.exists():
    seats=v.read(seat_path)
    F=v.frames(p,v.read(v.B/'profiles/default_pose.json')['raw_deg'])
    final=[]
    for row in seats['rows']:
        key=row['key'];other=row['fitting'];body=parts[key]
        native=v.move(parts[other]['s'],v.np.linalg.inv(F[body['token']])@F[parts[other]['token']])
        points,faces=v.vf(body['s'])
        final.append(dict(key=key,fitting=other,
            resulting_overlap_mm3=max(0.,(body['s']^native).volume()),
            component_count=len([c for c in body['s'].decompose() if c.volume()>1e-4]),
            source_watertight=v.trimesh.Trimesh(points,faces,process=False).is_watertight))
    seats.setdefault('initial_needs_web_reconnection',seats.get('needs_web_reconnection',[]))
    seats['final_verification']=final
    seats['geometry_sha256']=report['geometry_sha256']
    seats['needs_web_reconnection']=sorted({r['key'] for r in final if r['component_count']!=1})
    seats['passed']=report['passed'] and all(r['component_count']==1 and r['source_watertight']
        and r['resulting_overlap_mm3']<.05 for r in final)
    v.put(seat_path,seats)
    print('RESTORED SEAT VERIFICATION',seats['passed'],flush=True)
