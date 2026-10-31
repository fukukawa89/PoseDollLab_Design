from optimize_revo23_print import *

if __name__=='__main__':
    seats=read(B/'harness/wire_seats.json')['seats']
    for p in sorted((OUT/'candidates').glob('*.json')):
        s=read(p);rr=[read(x) for x in (OUT/'bambu'/s['id']).glob('*/checked_result.json')]
        if any(r.get('passed') for r in rr):continue
        own=[r for r in seats if r['part']==s['key']]
        if not own:continue
        m=trimesh.load(B/s['source']['staged_stl'],process=True);axis=np.array(own[0]['transform_body_mm'])[:3,0]
        for sign in (1,-1):
            M,size=placement(m.vertices,frame(axis*sign))
            if max(size[:2])>168 or size[2]>177:continue
            name='wire_axis_up' if sign==1 else 'wire_axis_down'
            c=dict(name=name,support='snug',matrix=M,size_mm=size,metrics=metrics(m,M,s['rod_lines']),protect_voids=True,guard_revision=5,blocker_margin_mm=1.2,
                settings=dict(support_threshold_angle='55',bridge_no_support='0',brim_width='6'))
            s['candidates']=[x for x in s['candidates'] if x['name']!=name]+[c]
        put(p,s)
