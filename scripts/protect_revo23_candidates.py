from optimize_revo23_print import *
import copy

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--ids',nargs='*');ap.add_argument('--count',type=int,default=2);ap.add_argument('--styles',nargs='*',default=['snug']);a=ap.parse_args()
    for file in sorted((OUT/'candidates').glob('*.json')):
        spec=read(file)
        if a.ids and spec['id'] not in a.ids:continue
        results=[read(p) for p in (OUT/'trials'/spec['id']).glob('*/result.json') if read(p)['passed'] and 'clear' not in p.parent.name]
        results.sort(key=lambda t:t.get('support_g',1e6)+15*t['metrics']['rod_verticality'])
        used=[];chosen=[]
        for r in results:
            d=np.array(r['matrix'])[2,:3]
            if any(np.dot(d,q)>.98 for q in used):continue
            used.append(d);chosen.append(r)
            if len(chosen)>=a.count:break
        for r in chosen:
            source=next(x for x in spec['candidates'] if x['name']==r['name'])
            for style in a.styles:
                c=copy.deepcopy(source);c.update(name=r['name']+'_clear_'+style,protect_voids=True,support=style)
                if c['name'] not in {x['name'] for x in spec['candidates']}:spec['candidates'].append(c)
        put(file,spec)
        print('PROTECT',spec['id'],[c['name'] for c in spec['candidates'] if c.get('protect_voids')],flush=True)
