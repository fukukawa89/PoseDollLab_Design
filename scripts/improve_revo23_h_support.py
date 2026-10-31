"""Use exact failed toolpath footprints to request local exterior support."""
from print_revo23_h import *

def improve(rid):
    file=PRINT/'candidates'/(rid+'.json');spec=read(file);original=copy.deepcopy(spec['candidates'][0])
    source=PRINT/'bambu'/rid/original['name']/'checked_result.json';old=read(source)
    assert old['native']['passed'] and old['clearance']['passed']
    for suffix,style,xy,angle in [('local','snug','0.5','45'),('local_tree','tree','0.4','0')]:
        c=copy.deepcopy(original);c.update(name='endface_'+suffix,support=style,shield_enforcers=True)
        c['enforce_sources']=c.get('enforce_sources',[])+([c['enforce_source']] if c.get('enforce_source') else [])
        c['enforce_source']=source.relative_to(HROOT).as_posix()
        c.setdefault('settings',{}).update(support_object_xy_distance=xy,support_angle=angle,bridge_no_support='0')
        trial=dict(spec,candidates=[c]);opt.build_candidate(trial,c)
        result=run_one(trial)
        if result['passed']:
            spec['candidates']=[c]+[x for x in spec['candidates'] if x['name']!=c['name']];put(file,spec)
            print('H SUPPORT FIXED',rid,c['name'],flush=True);return result
    print('H SUPPORT NEEDS CAP OR ORIENTATION',rid,flush=True)

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('id');a=ap.parse_args();configure_print();improve(a.id)
