"""Cut motion/service openings in NEW wall material, never in inherited lands.

Uses explicit named pose samples and actual obstacle geometry. The optional
six translated copies are an opening allowance, not a proven isotropic gap.
These sampled openings are not a continuous-range proof.
"""
from verify_revo23 import *

def save_parts(parts):
    out={}
    for k,part in parts.items():
        v,f=vf(part['s']);i=str(part['index']);out[i+'v']=v;out[i+'f']=f
    np.savez_compressed(B/'assembly.npz',**out)

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--gap',type=float,default=0.3);ap.add_argument('--hull',action='store_true');ap.add_argument('--keys',nargs='*');args=ap.parse_args()
    parts=load_current();p=read(B/'profiles/device_profile.json');report=read(B/'verification/motion_quick.json')
    original_hash=sha(B/'assembly.npz');zs=np.load(B/'retained_interfaces.npz')
    assert report['geometry_sha256']==original_hash,'Motion report must match current geometry.'
    focus=[k for k,v in parts.items() if v['role']=='structure' and (not args.keys or k in args.keys)]
    keeps={k:solid(zs[k+'|v'],zs[k+'|f']) for k in focus}
    adds={k:solid(*vf(parts[k]['s']-keeps[k])) for k in focus}
    cuts={k:[]for k in adds};recs=[];seen=set()
    qcases=cases(p,'quick');gap=args.gap;offsets=np.vstack([np.zeros(3),np.eye(3)*gap,-np.eye(3)*gap])
    for n,contact in enumerate(report['new_or_increased_contacts']):
        F=frames(p,qcases[contact['pose']]);a,b=contact['pair']
        pairs=([(a,b)]if a in adds else [])+([(b,a)]if b in adds else [])
        for k,other in pairs:
            rel=np.linalg.inv(F[parts[k]['token']])@F[parts[other]['token']]
            ck=(k,other,tuple(np.round(rel,7).ravel()))
            if ck in seen:continue
            seen.add(ck);obstacle=move(parts[other]['s'],rel);bb=np.array(adds[k].bounding_box());cropped=obstacle^box(bb[:3]-gap,bb[3:]+gap)
            if cropped.is_empty():continue
            if args.hull:
                v,_=vf(cropped);hull=md.Manifold.hull_points(v);hv,_=vf(hull)
                cutter=md.Manifold.hull_points((hv[:,None,:]+offsets).reshape(-1,3))
            else:cutter=union([cropped.translate(t) for t in offsets]) if gap else cropped
            # Contacts entirely inside a retained bearing land cannot be fixed
            # by trimming the added skin. Do not introduce irrelevant Boolean
            # boundaries through those already complex inherited interfaces.
            cutter=solid(*vf(cutter))
            if (adds[k]^cutter).volume()<.001:continue
            cuts[k].append(cutter)
            recs.append(dict(key=k,obstacle=other,pose=contact['pose'],gap_mm=gap))
    rows=[];newadds={};cutmeshes={}
    for k,cutters in cuts.items():
        before=parts[k]['s'];cut=solid(*vf(union(cutters)))
        add=solid(*vf(adds[k]-cut)) if cutters else adds[k]
        newadds[k]=add
        cutmeshes[k+'|v'],cutmeshes[k+'|f']=vf(cut)
        after=solid(*vf(keeps[k]+add)) if cutters else before
        parts[k]['s']=after
        row=dict(key=k,cutters=len(cutters),removed_wall_mm3=before.volume()-after.volume(),
                 inherited_interfaces_removed_mm3=max(0.,(keeps[k]-after).volume()),
                 components=len([s for s in after.decompose() if s.volume()>1e-4]))
        rows.append(row);print('RELIEF',k,row['cutters'],'removed cm3',round(row['removed_wall_mm3']/1000,2),'components',row['components'],flush=True)
    save_parts(parts);indexed={}
    for k,s in newadds.items():indexed[k+'|v'],indexed[k+'|f']=vf(s)
    np.savez_compressed(B/'refined_structure.npz',**indexed)
    np.savez_compressed(B/'clearance_cutters.npz',**cutmeshes)
    put(B/'verification/relief.json',dict(input_sha256=original_hash,output_sha256=sha(B/'assembly.npz'),rows=rows,cutters=recs,
        purpose='Named-pose opening construction, independent resampling required',continuous_proof=False))

if __name__=='__main__':main()
