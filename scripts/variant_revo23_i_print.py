"""Slicer-only process alternatives without changing the structural mesh."""
from print_revo23_i import *

def variant(rid,source,name,classic=False,clearance=False):
    file=PRINT/'candidates'/(rid+'.json');spec=read(file);c=copy.deepcopy(read(PRINT/'trials'/rid/source/'input.json')['candidate']);c['name']=name
    if classic:c.setdefault('settings',{})['wall_generator']='classic'
    if clearance:
        c.update(blocker_margin_mm=2.5,support='snug')
        c.setdefault('settings',{}).update(support_object_xy_distance='.65',support_expansion='0',support_threshold_angle='45')
    trial=dict(spec,candidates=[c]);opt.build_candidate(trial,c);r=run_one(trial)
    if r['passed']:spec['candidates']=[c]+[x for x in spec['candidates']if x['name']!=name];put(file,spec)
    print('PROCESS VARIANT',rid,name,r['passed'],{k:r[k]['passed']for k in('native','clearance','islands','caps')},flush=True)

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('ids',nargs='+');ap.add_argument('--source',required=True);ap.add_argument('--name',required=True);ap.add_argument('--classic',action='store_true');ap.add_argument('--clearance',action='store_true');ap.add_argument('--workers',type=int,default=2);a=ap.parse_args();configure_print()
    with concurrent.futures.ThreadPoolExecutor(max_workers=a.workers)as pool:list(pool.map(lambda rid:variant(rid,a.source,a.name,a.classic,a.clearance),a.ids))
