"""Stable broad-face alternatives when low-support placements have unsupported starts."""
from optimize_revo23_print import *
import copy

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--ids',nargs='*');ap.add_argument('--count',type=int,default=2);a=ap.parse_args()
    for f in sorted((OUT/'candidates').glob('*.json')):
        s=read(f)
        if a.ids and s['id'] not in a.ids:continue
        ranked=sorted(s['ranked'],key=lambda x:-x['metrics']['bed_contact_projection_mm2']);seen=[];chosen=[]
        for r in ranked:
            d=np.array(r['matrix'])[2,:3]
            if any(d@q>.95 for q in seen):continue
            seen.append(d);chosen.append(r)
            if len(chosen)>=a.count:break
        for i,r in enumerate(chosen):
            c=copy.deepcopy(r);c.update(name=f'flat{i+1}_clear',support='snug',protect_voids=True,blocker_margin_mm=1.2)
            c['settings']=dict(support_threshold_angle='55',bridge_no_support='0')
            if c['name'] not in {x['name'] for x in s['candidates']}:s['candidates'].append(c)
        put(f,s);print('FLAT',s['id'],[(round(r['metrics']['bed_contact_projection_mm2'],1),np.round(np.array(r['matrix'])[2,:3],2).tolist()) for r in chosen],flush=True)
