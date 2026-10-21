"""Trim only sacrificial caps whose quantized beads meet body sidewalls."""
from cap_revo23_print import *
from audit_revo23_print import paths, polygon
import shapely

def build_trim(job):
    rid,source=job;name='peel_clearance'
    r=read(OUT/'bambu'/rid/source/'checked_result.json')
    c=copy.deepcopy(read((B/r['source_project']).parent/'input.json')['candidate'])
    report,a=paths(B/r['project']);caps=manual_caps(B/r['project']);fixed=[];records=[]
    for ci,cap in enumerate(caps.decompose()):
        lines=a[a[:,9]==ci+1];tops=[]
        for z in np.unique(lines[:,5]):
            cc=lines[abs(lines[:,5]-z)<.001];mm=a[(a[:,7]==0)&(abs(a[:,5]-z)<.001)]
            if not len(mm):continue
            footprint=lambda x:shapely.union_all(shapely.buffer(shapely.linestrings(x[:,[0,1,3,4]].reshape(-1,2,2)),x[:,8]/2,quad_segs=4))
            gap=footprint(cc).distance(footprint(mm))
            if gap<.18:
                lid=int(cc[0,6]);h=report['layers'][lid].get('height_mm') or .16
                tops.append(float(z)-h/2-.02)
                records.append(dict(cap=ci+1,z=float(z),old_bead_xy_gap_mm=gap,cut_top_mm=tops[-1]))
        if tops:
            bb=np.array(cap.bounding_box());cap=cap^box(bb[:3]-.01,[bb[3]+.01,bb[4]+.01,min(tops)])
        assert not cap.is_empty();fixed.append(cap)
    assert records,rid
    M=np.array(c['matrix']);v,f=vf(move(union(fixed),np.linalg.inv(M)))
    p=OUT/'candidates'/(rid+'_'+name+'.npz');np.savez_compressed(p,v=v,f=f)
    c.update(name=name,manual_caps=p.relative_to(B).as_posix(),cap_bead_clearance_adjustments=records)
    file=OUT/'candidates'/(rid+'.json');s=read(file);s['candidates']=[x for x in s['candidates'] if x['name']!=name]+[c];put(file,s)
    print('TRIM',rid,records,flush=True)
    return run(dict(id=rid,key=s['key'],name=name,matrix=c['matrix'],metrics=c['metrics'],support=c['support'],candidate_data=c))

if __name__=='__main__':
    with concurrent.futures.ProcessPoolExecutor(max_workers=2) as pool:
        list(pool.map(build_trim,[('O23G-S10','peel_exact'),('O23G-S14','classic_caps2')]))
