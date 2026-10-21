from optimize_revo23_print import *
import copy

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--ids',nargs='*');ap.add_argument('--count',type=int,default=2);a=ap.parse_args()
    for f in sorted((OUT/'candidates').glob('*.json')):
        s=read(f)
        if a.ids and s['id'] not in a.ids:continue
        results=[read(p) for p in (OUT/'trials'/s['id']).glob('*/result.json') if read(p)['passed'] and 'clear' not in p.parent.name]
        results.sort(key=lambda r:r['support_g']+12*r['metrics']['rod_verticality'])
        seen=[];selected=[]
        for r in results:
            d=np.array(r['matrix'])[2,:3]
            if any(d@q>.98 for q in seen):continue
            seen.append(d);selected.append(r)
            if len(selected)>=a.count:break
        for r in selected:
            src=next(x for x in s['candidates'] if x['name']==r['name']);c=copy.deepcopy(src)
            c.update(name=r['name']+'_local_tree',protect_voids=True,block_mode='local',blocker_margin_mm=.35,support='tree')
            c['settings']=dict(support_on_build_plate_only='1',support_threshold_angle='55',bridge_no_support='0',tree_support_branch_diameter='3',tree_support_branch_distance='2')
            if c['name'] not in {x['name'] for x in s['candidates']}:s['candidates'].append(c)
        put(f,s);print('LOCAL',s['id'],[x['name'] for x in s['candidates'] if 'local_tree' in x['name']],flush=True)
