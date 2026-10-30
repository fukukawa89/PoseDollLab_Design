from build_guide import *
from assembly_plan import tools_for_guide
import time

def intentional(a,b):
    a,b=P[a],P[b]
    allowed={'HS_HL_F1':'SHOULDER_PITCH','HS_HR_F1':'SHOULDER_PITCH','HE_HL_F1':'UPPER_ARM','HE_HR_F1':'UPPER_ARM','KEEP_E-H1133':'KEEP_E-P019','KEEP_E-H1141':'KEEP_E-P019','KEEP_E-H1149':'KEEP_E-P019','KEEP_E-H1157':'KEEP_E-P019'}
    return allowed.get(a['name'])==b['name'] or allowed.get(b['name'])==a['name']

def main():
    global P
    started=time.time();d=load(DEST/'steps.json');a=load(SOURCE/'production_assembly.json')['parts'];z=np.load(SOURCE/'production_meshes.npz');P={p['part_number']:p for p in a};S={}
    for p in a:
        i=str(p['i']);S[p['part_number']]=moved(md.Manifold(md.Mesh64(np.array(z[i+'v'],copy=True),np.array(z[i+'f'],dtype=np.uint64,copy=True))),F0[p['frame']])
    for p in tools_for_guide():P[p['part_number']]=p;S[p['part_number']]=moved(p['s'],F0[p['frame']])
    rows=[]
    for st in d['steps']:
        if st['kind']=='pose':continue
        active=st['parts'];others=[n for n in st['visible'] if n not in active];FS={n:S[n].translate(st['offsets'].get(n,[0,0,0])) for n in others};fixed=union(FS.values());MS={n:S[n].translate(st.get('part_base_offsets',{}).get(n,st['base_offset'])) for n in active};moving=union(MS.values());pts=np.array(st['path']);shifts=[]
        for p,q in zip(pts[:-1],pts[1:]):shifts.extend(p*(1-t)+q*t for t in np.linspace(0,1,math.ceil(np.linalg.norm(q-p)/.5)+1))
        if not shifts:shifts=[pts[0]]
        allowed=[(n,m) for n in active for m in others if intentional(n,m)];mx=0.;raw=0.;elastic=0.;bad=[]
        for off in shifts:
            vol=(moving.translate(off)^fixed).volume();fit=sum((MS[n].translate(off)^FS[m]).volume() for n,m in allowed);net=vol-fit;mx=max(mx,net);raw=max(raw,vol);elastic=max(elastic,fit)
            if net>.02 and len(bad)<2:
                pairs=[]
                for n in active:
                    for m in others:
                        vv=(MS[n].translate(off)^FS[m]).volume()
                        if vv>.02 and not intentional(n,m):pairs.append((n,m,round(vv,4)))
                bad.append(dict(offset=off.tolist(),pairs=pairs,raw=vol))
        # Active members must not pass through each other during coupled transfers.
        internal=[]
        if st['title']=='肩钉顶出导向针，连续接替定位':
            for i,n in enumerate(active):
                for m in active[i+1:]:
                    vv=(MS[n]^MS[m]).volume()
                    if vv>.02:internal.append((n,m,vv))
        row=dict(step=st['number'],title=st['title'],support=st['support'],samples=len(shifts),maximum_unintended_overlap_mm3=mx,maximum_raw_overlap_mm3=raw,declared_radial_pad_interference_mm3=elastic,passed=mx<.02 and not internal,bad_samples=bad,internal_collisions=internal);rows.append(row)
        if not row['passed'] or len(rows)%20==0:print('PATH',st['number'],st['title'],round(mx,4),bad,flush=True)
    ids={p['part_number'] for p in a};new=[n for st in d['steps'] for n in st['new_parts'] if n in ids]
    checks=[dict(check='each mechanical item introduced once',passed=len(new)==len(ids) and set(new)==ids),dict(check='final tool-free assembly',passed=set(d['steps'][-1]['visible'])==ids),dict(check='all steps explicitly define support',passed=all(st['support'] for st in d['steps'])),dict(check='eight inner-stack retention gates',passed=sum(st['support']=='retention_fit_gate' for st in d['steps'])==8),dict(check='all translated paths clear except declared radial fits',passed=all(r['passed'] for r in rows)),dict(check='exactly three continuous pin transfers',passed=sum(st['support']=='continuous_pin_transfer' for st in d['steps'])==3)]
    result=dict(status='PASS_GUIDE_GEOMETRY' if all(x['passed'] for x in checks) else 'REVIEW_REQUIRED',geometry_sha256=d['geometry_sha256'],checks=checks,paths=rows,total_samples=sum(r['samples'] for r in rows),seconds=time.time()-started,scope='Final STL meshes; <=0.5 mm sampled translation. Radial pad/FW4 contact is explicitly reported, not a zero-collision claim. Does not establish actual fit force, hand dexterity or vibration resistance. Physical assembly trial remains necessary.')
    put(DEST/'verification/assembly_paths.json',result);print(result['status'],[x for x in checks if not x['passed']],flush=True)
if __name__=='__main__':main()
