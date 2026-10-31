"""Search posterior placements and attachment owner without editing delivery."""
from study_revo23_backpack import *

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--owner',default='chest');ap.add_argument('--compact',action='store_true');args=ap.parse_args()
    parts=load_current();p=read(B/'profiles/device_profile.json')
    _,gb,bounds,records=prepare(parts,p,'f:'+args.owner)
    origin=controller_corner(read(CFG));rows=[]
    for z in np.arange(435.,686.,10.):
        for x in np.arange(-93.,-254.,-10.):
            shift=np.array([x,47,z])-origin;lo=gb[:3]+shift-2;hi=gb[3:]+shift+2
            indices=np.flatnonzero(np.all(np.minimum(hi,bounds[:,3:])-np.maximum(lo,bounds[:,:3])>0,axis=1))
            rows.append(dict(corner_mm=[x,47,z],aabb_count=len(indices),indices=indices.tolist()))
    # Test the best compact candidates, not only the furthest-out box.
    if args.compact:
        chosen=[]
        for x in np.arange(-103.,-204.,-10.):
            subset=[r for r in rows if r['corner_mm'][0]==x and r['corner_mm'][2]<=645]
            chosen+=sorted(subset,key=lambda r:(r['aabb_count'],abs(r['corner_mm'][2]-550)))[:4]
    else:chosen=sorted(rows,key=lambda r:(r['aabb_count'],abs(r['corner_mm'][0])+.2*abs(r['corner_mm'][2]-550)))[:40]
    cache={}
    for row in chosen:
        shift=np.array(row['corner_mm'])-origin;envelope=box(gb[:3]+shift-2,gb[3:]+shift+2);hits=[]
        for i in row['indices']:
            r=records[i]
            if i not in cache:cache[i]=move(parts[r['key']]['s'],r['matrix'])
            volume=float((envelope^cache[i]).volume())
            if volume>.0001:hits.append(dict(key=r['key'],poses=r['poses'],overlap_mm3=volume))
        row['hits']=hits;row['hit_count']=len(hits);row['poses']=sorted({a for h in hits for a in h['poses']})
        print(args.owner,row['corner_mm'],'AABB',row['aabb_count'],'HITS',row['hit_count'],'POSES',len(row['poses']),flush=True)
    for r in rows:r.pop('indices',None)
    suffix='_compact'if args.compact else ''
    put(B/'verification'/f'backpack_search_{args.owner}{suffix}.json',dict(geometry_sha256=sha(B/'assembly.npz'),owner=args.owner,
        envelope_allowance_mm=2,rows=rows,checked=chosen,pose_count=len(cases(p,'full')),
        excluded='Existing controller group and same rigid owner. Support is not screened here.',continuous_motion_proven=False))

if __name__=='__main__':main()
