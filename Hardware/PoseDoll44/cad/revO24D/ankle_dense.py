"""Additional 2-degree ankle combinations and deep-knee sweep after encoder relocation."""
from validate import *
from itertools import product

def values(lo,hi):return sorted(set([float(x) for x in np.arange(lo,hi,2)]+[float(hi)]))

def main():
    parts,z,solids=read_assembly();digest=sha(OUT/'assembly_meshes.npz');rows=[]
    for side in ['l','r']:
        tags={side+'_'+n for n in ['thigh','shin','foot','toe']}
        idx=[i for i,p in enumerate(parts) if segment(p['frame']) in tags]
        e=Collision([parts[i] for i in idx],[solids[i] for i in idx])
        cases=[('ankle',dict(NEUTRAL_ANGLES,**{side+'_ankle_roll':r,side+'_ankle_flex':f})) for r,f in product(values(-20,25),values(-40,25))]
        cases += [('knee',dict(NEUTRAL_ANGLES,**{side+'_knee_flex':k})) for k in values(0,140)]
        for kind,q in cases:
            hits=e.check(q);rows.append(dict(side=side,kind=kind,angles=q,count=len(hits),collisions=hits))
        print('ANKLE DENSE',side,len(cases),'fail',sum(r['count']>0 for r in rows if r['side']==side),flush=True)
    failures=sum(r['count']>0 for r in rows)
    put(OUT/'verification/ankle_dense.json',dict(status='PASS_SAMPLED' if not failures else 'FAIL',geometry_sha256=digest,max_axis_step_deg=2,samples=len(rows),failed_cases=failures,cases=rows,scope='Additional local tests after moving the ankle encoder to 11 mm radial layout. All moving solids in thigh, shin, foot and toe; same/adjacent anatomy policy unchanged. Knee sweep checks shin-mounted encoders against thigh hardware; ankle combinations check shin-mounted encoders against foot. Finite nominal samples, not tolerance or continuous-space certification.'))
    if failures:raise RuntimeError('Ankle dense contacts')
if __name__=='__main__':main()
