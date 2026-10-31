"""Conservative placement screen for the complete O23 back controller pack.

All boxes are in the neutral chest frame expressed in neutral-world axes.
This screens every actual part at the existing 343 poses; a rejected AABB
placement need not be a real collision. It does not mutate the assembly.
"""
from verify_revo23 import *


def prepare(parts, p, owner='f:chest'):
    neutral = frames(p, p['neutral_raw_deg'])[owner]
    old_neutral = frames(p, p['neutral_raw_deg'])['f:chest']
    corners = {}
    for k, part in parts.items():
        b = part['s'].bounding_box()
        corners[k] = np.array(list(itertools.product(*zip(b[:3], b[3:]))))
    group = [k for k in parts if k.startswith('o22/') and not k.startswith('o22/backpack_')]
    gb = []
    for k in group:
        c = corners[k] @ old_neutral[:3, :3].T + old_neutral[:3, 3]
        gb.append(np.r_[c.min(0), c.max(0)])
    gb = np.array(gb)
    group_box = np.r_[gb[:, :3].min(0), gb[:, 3:].max(0)]
    records = []; transforms = {}; bounds = []
    for name, q in cases(p, 'full').items():
        F = frames(p, q); inv = neutral @ np.linalg.inv(F[owner])
        for k, part in parts.items():
            if part['token'] == owner or k.startswith('o22/'):
                continue
            M = inv @ F[part['token']]
            ck = (k, tuple(np.round(M, 7).ravel()))
            if ck in transforms:
                records[transforms[ck]]['poses'].append(name)
                continue
            transforms[ck] = len(records)
            c = corners[k] @ M[:3, :3].T + M[:3, 3]
            bounds.append(np.r_[c.min(0), c.max(0)])
            records.append(dict(key=k, first_pose=name, poses=[name], matrix=M))
    return group, group_box, np.array(bounds), records


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--exact',action='store_true')
    ap.add_argument('--horizontal',action='store_true');ap.add_argument('--sagittal',action='store_true');ap.add_argument('--high',action='store_true');args=ap.parse_args()
    parts = load_current(); p = read(B/'profiles/device_profile.json')
    group, gb, bounds, records = prepare(parts, p)
    origin = controller_corner(read(CFG)); rows = []
    if args.horizontal or args.sagittal:
        old_rotation=np.array([[0,0,-1],[0,-1,0],[-1,0,0.]])
        new_rotation=np.array([[0,-1,0],[0,0,1],[-1,0,0.]])if args.sagittal else np.diag([-1.,-1.,1.]);rotation=new_rotation@old_rotation.T
        cc=np.array(list(itertools.product(*zip(gb[:3],gb[3:]))))
        cc=(cc-origin)@rotation.T+origin
        gb=np.r_[cc.min(0),cc.max(0)]
    solid_cache={}
    zs=(520.,540.,560.,580.,600.,620.)if args.sagittal else ((530.,550.,570.,590.,610.,630.)if args.horizontal else ((612.,632.,652.,672.)if args.high else ((572., 592., 552.) if args.exact else (572., 582., 592., 602., 562., 552., 542.))))
    xs=np.arange(-45.,-136.,-10.)if args.sagittal else (np.arange(-65.,-176.,-10.)if args.horizontal else np.arange(-113.,-244.,-10.))
    for z in zs:
        for x in xs:
            cy=-13.35 if args.sagittal else 47.
            shift = np.array([x, cy, z]) - origin
            lo = gb[:3] + shift - 2; hi = gb[3:] + shift + 2
            mask = np.all(np.minimum(hi, bounds[:, 3:]) - np.maximum(lo, bounds[:, :3]) > 0, axis=1)
            indices = np.flatnonzero(mask)
            row=dict(front_corner_mm=[x,cy,z], aabb_candidates=len(indices),
                parts=sorted({records[i]['key'] for i in indices}),
                first_poses=sorted({records[i]['first_pose'] for i in indices}))
            if args.exact:
                envelope=box(lo,hi);hits=[]
                for i in indices:
                    r=records[i]
                    if i not in solid_cache:solid_cache[i]=move(parts[r['key']]['s'],r['matrix'])
                    volume=float((envelope^solid_cache[i]).volume())
                    if volume>.0001:hits.append(dict(key=r['key'],poses=r['poses'],volume_mm3=volume))
                row.update(envelope_intersections=hits,hit_part_poses=len(hits),
                           poses=sorted({pose for r in hits for pose in r['poses']}))
                print('EXACT',x,z,'HITS',len(hits),'POSES',len(row['poses']),flush=True)
            rows.append(row)
    filename='backpack_sagittal_study.json'if args.sagittal else ('backpack_horizontal_study.json'if args.horizontal else ('backpack_high_study.json'if args.high else ('backpack_envelope_study.json'if args.exact else 'backpack_position_study.json')))
    put(B/'verification'/filename, dict(geometry_sha256=sha(B/'assembly.npz'),
        source_corner_mm=origin, group_keys=group, group_neutral_bbox_mm=gb,
        unique_part_poses=len(records), envelope_allowance_mm=2, rows=rows,
        note='AABB conservative screen, existing 343 discrete poses only; support not included.'))
    for z in (572.,582.,592.,602.,562.,552.,542.):
        rr = [r for r in rows if r['front_corner_mm'][2] == z]
        clear = [r for r in rr if r['aabb_candidates'] == 0]
        print('HEIGHT', z, 'FIRST_CLEAR', clear[0]['front_corner_mm'] if clear else None,
              'COUNTS', [(r['front_corner_mm'][0],r['aabb_candidates']) for r in rr], flush=True)


if __name__ == '__main__':
    main()
