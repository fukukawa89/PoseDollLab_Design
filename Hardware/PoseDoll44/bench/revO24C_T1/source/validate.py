"""Independent mesh intersection audit; contact areas are named, never broad frame exclusions."""
from kit import *
import argparse, time

def overlaps(u,v):
    a0,a1=np.array(u.bounding_box()).reshape(2,3);b0,b1=np.array(v.bounding_box()).reshape(2,3)
    return np.all(np.minimum(a1,b1)-np.maximum(a0,b0)>1e-6)

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--quick',action='store_true');args=ap.parse_args()
    k=build();t=time.time();errors=[];static=[]
    for st in ['H','R','W']:
        rows=[p for p in k.parts if p['station']==st]
        for i,p in enumerate(rows):
            for r in rows[i+1:]:
                if overlaps(p['s'],r['s']):
                    vol=(p['s']^r['s']).volume()
                    if vol>.02:static.append(dict(station=st,pair=[p['id'],r['id']],volume_mm3=vol))
    print('STATIC',json.dumps(static,ensure_ascii=False),flush=True)
    samples=0;worst={};counts={}
    if not args.quick:
        for st,limits in [('H',(-45,165)),('R',(-85,80)),('W',(-65,70))]:
            rows=[p for p in k.parts if p['station']==st]
            fixed=[p for p in rows if p['frame']=='fixed'];moving=[p for p in rows if p['frame']!='fixed']
            # 1 degree for hinge; wrist 5 degree grid plus every boundary degree.
            poses=[(q,0) for q in range(limits[0],limits[1]+1)] if st!='W' else sorted(set([(q,d) for q in range(-65,71,5) for d in range(-20,31,5)]+[(q,d) for q in range(-65,71) for d in [-20,30]]+[(q,d) for q in [-65,70] for d in range(-20,31)]))
            counts[st]=len(poses)
            for q,d in poses:
                F=frames(st,q,d);samples+=1
                for p in moving:
                    s=moved(p['s'],F[p['frame']])
                    for r in fixed:
                        if not overlaps(s,r['s']):continue
                        vol=(s^r['s']).volume()
                        if vol>.02:
                            key=p['id']+' / '+r['id']
                            if key not in worst or vol>worst[key]['volume_mm3']:worst[key]=dict(station=st,pair=[p['id'],r['id']],q=q,dev=d,volume_mm3=vol)
            print('MOTION',st,'poses',len(poses),'colliding_pairs',len(worst),flush=True)
    report=dict(passed=not static and not worst,geometry_sha256=sha(OUT/'assembly_meshes.npz'),static_collisions=static,motion_collisions=list(worst.values()),pose_count=samples,pose_counts=counts,threshold_mm3=.02,elapsed_s=time.time()-t,
        scope='Nominal rigid geometry; all different parts at neutral, then every fixed vs moving part. Bearing ring internals and thread helices omitted. Zero-volume intended contact is allowed. Not a loaded deformation or physical fit qualification.')
    put(OUT/'verification/collisions.json',report)
    print('RESULT',json.dumps(dict(passed=report['passed'],static=len(static),motion=list(worst.values()),elapsed=round(time.time()-t,1))),flush=True)

if __name__=='__main__':main()
