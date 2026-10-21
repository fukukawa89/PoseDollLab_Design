from bambu_revo23_print import *
from scipy.spatial.transform import Rotation

def tilt(rid):
    file=OUT/'candidates'/(rid+'.json');s=read(file);m=trimesh.load(B/s['source']['staged_stl'],process=True)
    rr=[read(p) for p in (OUT/'bambu'/rid).glob('*/checked_result.json')]
    if any(r.get('passed') for r in rr):return
    rr.sort(key=lambda r:len(r['clearance']['wire_void_hits'])*100+len(r['clearance']['functional_void_hits'])*30+len(r['islands']['external_new_islands'])*10+r['support_g'])
    source=rr[0];original=copy.deepcopy(next(c for c in s['candidates'] if c['name']==source['name']))
    for axis,angle in [('x',7),('y',7),('x',-7),('y',-7)]:
        name=f'micro_{axis}_{angle:+d}';c=copy.deepcopy(original);F=Rotation.from_euler(axis,angle,degrees=True).as_matrix()@np.array(c['matrix'])[:3,:3];M,size=placement(m.vertices,F)
        if max(size[:2])>168 or size[2]>177:continue
        c.update(name=name,matrix=M,size_mm=size,metrics=metrics(m,M,s['rod_lines']))
        c.setdefault('settings',{})['brim_width']='6'
        s['candidates']=[x for x in s['candidates'] if x['name']!=name]+[c];put(file,s)
        print('TILT',rid,name,'from',source['name'],flush=True)
        r=run(dict(id=rid,key=s['key'],name=c['name'],matrix=c['matrix'],metrics=c['metrics'],support=c['support'],candidate_data=c))
        if r['passed']:return r
    return r

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--ids',nargs='*');ap.add_argument('--workers',type=int,default=3);a=ap.parse_args()
    ids=a.ids or [p.stem for p in sorted((OUT/'candidates').glob('*.json'))]
    with concurrent.futures.ProcessPoolExecutor(max_workers=a.workers) as pool:list(pool.map(tilt,ids))
