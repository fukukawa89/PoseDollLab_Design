"""Retrofit tall repair panels with bed-rooted cross-braces, then verify solid clearances."""
import json,sys,math
import numpy as np
from pathlib import Path
from build_revo22_fins_v3 import *

def retrofit(pid):
    path=O/'parts'/f'{pid}.npz';n=dict(np.load(path));r=json.loads((O/'design'/f'{pid}.json').read_text());s=solid(n['v'],n['f']);b=solid(n['fin_v'],n['fin_f']);teeth=solid(n['teeth_v'],n['teeth_f'])
    targets=[x for x in r['segments'] if x['height_mm']>35 and not x.get('brace_count') and x['blade_thickness_mm']<x['height_mm']/12-.001]
    if not targets:return None
    vols=next((x['volumes'] for x in json.loads((D/'all_protected_volumes.json').read_text())['objects'] if x['part']==r['part']),[]);M=np.array(r['orientation']['matrix']);off=np.array(r['orientation']['source_translation_mm']);ban=protected(vols).transform(np.c_[M,off]);records=[]
    for seg in targets:
        bb=np.array(seg['bounds_mm']);c=(bb[:2]+bb[3:5])/2;W=seg['blade_width_mm'];T=seg['blade_thickness_mm'];h=seg['height_mm'];best=None
        for deg in range(0,180,15):
            a=math.radians(deg);Q=np.array([[math.cos(a),-math.sin(a),0],[math.sin(a),math.cos(a),0],[0,0,1.]])
            core=box([-W/2,-T/2,1],[W/2,T/2,h-.5]).transform(np.c_[Q,[*c,0]])
            overlap=float((core^b).volume())/core.volume()
            if best is None or overlap>best[0]:best=(overlap,Q,core,deg)
        fit,Q,core,deg=best;assert fit>.97,(pid,seg['number'],fit)
        braces=[]
        for x in [-W/3,0,W/3]:
            found=False
            for dep in [4.,3.2,2.4]:
                for top in [h-2.,h-8.,h-12.]:
                    if top<h*.7:continue
                    q=box([x-.7,-dep,0],[x+.7,dep,top]).transform(np.c_[Q,[*c,0]])
                    if (q^s).volume()>1e-7 or (q^ban).volume()>1e-7 or q.min_gap(s,.3)<.22:continue
                    if (q^core).volume()<1:continue
                    braces.append(q);found=True;break
                if found:break
        assert braces,(pid,seg['number'],'no full-height transverse brace')
        add=union(braces);b+=add;seg['brace_count']=len(braces);seg['retrofit_braces_bounds_mm']=[list(q.bounding_box()) for q in braces]
        records.append({'segment':seg['number'],'inferred_axis_deg':deg,'axis_fit_volume_fraction':fit,'braces':len(braces),'brace_height_fraction_min':min(q.bounding_box()[5]/h for q in braces),'added_volume_mm3':float(add.volume())})
    assert abs((b^s).volume())<1e-6 and abs((b^ban).volume())<1e-6
    n['fin_v'],n['fin_f']=vf(b);np.savez_compressed(path,**n);r.update(support_volume_mm3=float((b+teeth).volume()),brace_retrofit=records)
    (O/'design'/f'{pid}.json').write_text(json.dumps(r,ensure_ascii=False,indent=2),encoding='utf8')
    print('BRACED',pid,records,flush=True);return {'id':pid,'changes':records}

if __name__=='__main__':
    ids=sorted({i['id'] for p in json.loads((B/'a1mini/manifest.json').read_text())['plates'] if not p['optional'] for i in p['items']})
    rows=[q for pid in ids if (q:=retrofit(pid))]
    (O/'verification/brace_retrofits.json').write_text(json.dumps(rows,indent=2),encoding='utf8')
