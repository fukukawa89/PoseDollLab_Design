from bambu_revo23_print import *
import itertools

def diagonal(rid):
    file=OUT/'candidates'/(rid+'.json');s=read(file);m=trimesh.load(B/s['source']['staged_stl'],process=True)
    if any(read(p)['passed'] for p in (OUT/'bambu'/rid).glob('*/checked_result.json')):return
    choices=[]
    for i,d in enumerate(itertools.product([-1,1],repeat=3)):
        M,size=placement(m.vertices,frame(np.array(d,dtype=float)))
        if max(size[:2])>168 or size[2]>177:continue
        c=dict(name=f'diagonal{i}',support='snug',matrix=M,size_mm=size,metrics=metrics(m,M,s['rod_lines']),protect_voids=True,guard_revision=5,blocker_margin_mm=1.2,
            settings=dict(support_top_z_distance='0.2',support_bottom_z_distance='0.2',support_interface_spacing='0.15',support_threshold_angle='55',bridge_no_support='0',brim_width='8',default_acceleration='1000'))
        choices.append(c)
    choices.sort(key=lambda c:c['metrics']['overhang_projection_volume_proxy_mm3']/1000+25*c['metrics']['rod_verticality'])
    for c in choices:
        s['candidates']=[x for x in s['candidates'] if x['name']!=c['name']]+[c];put(file,s)
        print('DIAGONAL',rid,c['name'],flush=True)
        r=run(dict(id=rid,key=s['key'],name=c['name'],matrix=c['matrix'],metrics=c['metrics'],support=c['support'],candidate_data=c))
        if r['passed']:return r
    return None

if __name__=='__main__':
    with concurrent.futures.ProcessPoolExecutor(max_workers=3) as pool:list(pool.map(diagonal,['O23G-S09','O23G-S10','O23G-S12','O23G-S14','O23G-S22']))
