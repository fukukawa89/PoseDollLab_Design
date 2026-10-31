from check_geometry import *
from tool_r5 import fork

def run():
    a,ss=saved();data=load(OUT/'assembly_guide/steps.json');P={p['part_number']:p for p in a};S={p['part_number']:moved(s,F0[p['frame']]) for p,s in zip(a,ss)};important={p['part_number'] for p in a if not p.get('baseline_name') or p.get('reprint')}
    from build_views import readjs
    old=readjs(OUT/'assembly_guide/data.js');raw=np.frombuffer(__import__('base64').b64decode(old['geometry']),dtype='<f4').reshape(-1,6)
    for p in old['parts']:
        if p['role']=='tool':
            pts=raw[p['first']:p['first']+p['count'],:3].astype(float);m=trimesh.Trimesh(pts,np.arange(len(pts)).reshape(-1,3),process=True);S[p['id']]=moved(md.Manifold(md.Mesh64(np.array(m.vertices,copy=True),np.array(m.faces,dtype=np.uint64,copy=True))),F0[p['frame']]);P[p['id']]=dict(name=p['feature'],role='tool')
            if p['id'].startswith(('R5-J003','J004')):important.add(p['id'])
    bounds={n:e.bounds(s) for n,s in S.items()};issues={};samples=0;start=time.time();checks=0
    for si,step in enumerate(data['steps']):
        if not step['animated'] or step['kind']=='pose':continue
        if '--new-only' in sys.argv and step.get('source_step') is not None:continue
        moving=set(step['parts']);static=set(step['visible'])-moving;path=np.array(step['path']);points=[]
        for x,y in zip(path,path[1:]):points.extend(np.linspace(x,y,max(2,math.ceil(np.linalg.norm(y-x)/2)+1)))
        sb={n:bounds[n]+np.array(step['offsets'].get(n,[0,0,0])) for n in static};sw={}
        for point in points:
            samples+=1
            for n in moving:
                off=np.array(step['part_base_offsets'].get(n,step['base_offset']))+point;bb=bounds[n]+off;current=None
                for o in static:
                    if n not in important and o not in important:continue
                    if np.any(sb[o][0]>=bb[1]-.001) or np.any(sb[o][1]<=bb[0]+.001):continue
                    if current is None:current=S[n].translate(off)
                    if o not in sw:sw[o]=S[o].translate(step['offsets'].get(o,[0,0,0]))
                    v=(current^sw[o]).volume();checks+=1
                    pair=tuple(sorted([P[n]['name'],P[o]['name']]))
                    is_pad=('F1' in pair[0] and pair[1] in ['SHOULDER_PITCH','UPPER_ARM']) or ('KEEP_E-P019' in pair and any(k in pair for k in ['KEEP_E-H1133','KEEP_E-H1141','KEEP_E-H1149','KEEP_E-H1157']))
                    if v>.04 and not(is_pad and v<.13):
                        key=(si,n,o)
                        if key not in issues or v>issues[key]['overlap_mm3']:issues[key]=dict(step=si+1,title=step['title'],moving=n,stationary=o,moving_name=P[n]['name'],static_name=P[o]['name'],overlap_mm3=v,offset_mm=off.tolist(),source_R4_step=step.get('source_step'))
        if si%25==0:print('ASSEMBLY',si+1,'/',len(data['steps']),'issues',len(issues),'seconds',round(time.time()-start,1),flush=True)
    rows=sorted(issues.values(),key=lambda x:-x['overlap_mm3']);put(OUT/'verification/assembly_paths.json',dict(passed=not rows,geometry_sha256=sha(OUT/'production_meshes.npz'),steps=len(data['steps']),samples=samples,intersection_checks=checks,issues=rows,scope='Moving groups vs stationary shown bodies, <=2 mm translation sampling. R4 unchanged-vs-unchanged pairs inherited. Manual reorientation, hand transfer and thread rotation are not animated or certified.'))
    print('ASSEMBLY ISSUES',len(rows),flush=True)
    for r in rows[:35]:print({k:v for k,v in r.items() if k!='title'},flush=True)

if __name__=='__main__':run()
