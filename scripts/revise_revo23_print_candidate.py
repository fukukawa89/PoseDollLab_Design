from optimize_revo23_print import *
import copy

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('id');ap.add_argument('source');ap.add_argument('name');ap.add_argument('--margin',type=float);ap.add_argument('--style',choices=['snug','tree']);ap.add_argument('--angle',type=float);ap.add_argument('--settings',type=json.loads,default={});a=ap.parse_args()
    file=OUT/'candidates'/f'{a.id}.json';s=read(file);c=copy.deepcopy(next(x for x in s['candidates'] if x['name']==a.source));c['name']=a.name
    if a.margin is not None:c.update(protect_voids=True,blocker_margin_mm=a.margin)
    if a.style:c['support']=a.style
    if a.angle is not None:c.setdefault('settings',{})['support_threshold_angle']=str(a.angle)
    c.setdefault('settings',{}).update(a.settings)
    s['candidates']=[x for x in s['candidates'] if x['name']!=a.name]+[c];put(file,s);print(a.id,a.name)
