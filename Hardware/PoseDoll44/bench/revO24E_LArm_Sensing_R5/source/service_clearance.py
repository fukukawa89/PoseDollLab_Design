"""Clear added material from the R4 physical insertion paths, retaining R4 load faces."""
from common import *
import base64

def trim(parts,expand):
    s=(BASE/'assembly_guide/data.js').read_text('utf8');guide=json.loads(s[s.index('=')+1:].rstrip(';'))
    a,ss=baseline();P={p['part_number']:p for p in a};S={p['part_number']:moved(s,F0[p['frame']]) for p,s in zip(a,ss)}
    raw=np.frombuffer(base64.b64decode(guide['geometry']),dtype='<f4').reshape(-1,6)
    for p in guide['parts']:
        if p['role']!='tool':continue
        pts=raw[p['first']:p['first']+p['count'],:3].astype(float);m=trimesh.Trimesh(pts,np.arange(len(pts)).reshape(-1,3),process=True)
        S[p['id']]=moved(md.Manifold(md.Mesh64(np.array(m.vertices,copy=True),np.array(m.faces,dtype=np.uint64,copy=True))),F0[p['frame']])
    bounds={n:e.bounds(s) for n,s in S.items()};rows=[]
    for p in parts:
        if not p.get('reprint'):continue
        name=p['source'];world=moved(p['s'],F0[p['frame']]);added=world-S[name]
        if added.is_empty():continue
        region=expand(added,.5);bb=e.bounds(region);cuts=[];steps=[]
        for st in guide['steps']:
            if name not in st['visible'] or not st['animated'] or st['kind']=='pose':continue
            moving=set(st['parts']);static=set(st['visible'])-moving
            others=static if name in moving else moving
            for x,y in zip(st['path'],st['path'][1:]):
                for pt in np.linspace(x,y,max(2,math.ceil(np.linalg.norm(np.array(y)-x)/.5)+1)):
                    def off(n):return np.array(st.get('part_base_offsets',{}).get(n,st['base_offset']))+pt if n in moving else np.array(st['offsets'].get(n,[0,0,0]))
                    base=off(name)
                    for n in others:
                        delta=off(n)-base;b=bounds[n]+delta
                        if np.any(b[0]>=bb[1]) or np.any(b[1]<=bb[0]):continue
                        piece=S[n].translate(delta)^region
                        if piece.volume()>.0001:cuts.append(expand(piece,.3));steps.append(st['number'])
        before=world.volume()
        if cuts:world-=union(cuts)-S[name]
        chunks=sorted(world.decompose(),key=lambda s:-s.volume())
        debris=sum(abs(c.volume()) for c in chunks[1:])
        assert debris<25 and all(abs((c^S[name]).volume())<.001 for c in chunks[1:]),(p['name'],debris)
        world=chunks[0]
        p['s']=moved(world,np.linalg.inv(F0[p['frame']]))
        rows.append(dict(name=p['name'],removed_added_material_mm3=before-world.volume(),detached_added_debris_removed_mm3=debris,source_R4_steps=sorted(set(steps)),original_load_geometry_carved=False))
    put(OUT/'verification/R4_service_clearance.json',dict(rows=rows,sampling_mm=.5,additional_clearance_mm=.3,scope='Only newly added material, clipped against R4 tools, metal and mating-body insertion paths. R4 bearing/load surfaces are protected.'))
