"""Native support experiments; preserve the verified structural mesh."""
from print_revo23_i import *
import cap_revo23_h_support as helper
import prune_revo23_h_caps as pruner

def run(rid,source,name,mode):
    configure_print()
    for module in (helper,pruner):
        module.HROOT=IROOT;module.PRINT=PRINT;module.opt=opt
        module.audit_print=audit_print;module.run_one=run_one
    if mode=='prune':
        return pruner.prune(rid,source)
    original=opt.build_candidate
    def build(spec,c):
        c['name']=name
        if mode=='strict':
            c.update(strict_void_columns=True,blocker_margin_mm=1.0)
        if mode=='fine':
            c.setdefault('settings',{}).update(layer_height='.12',support_top_z_distance='.24',support_bottom_z_distance='.24')
        if mode=='tree':
            c.update(support='tree',blocker_margin_mm=2.5)
            c.setdefault('settings',{}).update(support_object_xy_distance='.7',support_expansion='0',support_threshold_angle='45',support_top_z_distance='.24',support_bottom_z_distance='.24',bridge_no_support='0')
        if mode=='caps_clear':
            c.update(support='snug',blocker_margin_mm=2.5)
            c.setdefault('settings',{}).update(support_object_xy_distance='.65',support_expansion='0',support_threshold_angle='45')
        return original(spec,c)
    opt.build_candidate=build
    if mode in ('caps','caps_clear'):
        return helper.fix(rid,source,.68,name)
    file=PRINT/'candidates'/(rid+'.json');spec=read(file)
    c=copy.deepcopy(read(PRINT/'trials'/rid/source/'input.json')['candidate']);c['name']=name
    trial=dict(spec,candidates=[c]);build(trial,c);r=run_one(trial)
    if r['passed']:spec['candidates']=[c]+[x for x in spec['candidates']if x['name']!=name];put(file,spec)
    print('REFINE',rid,name,r['passed'],{k:r[k]['passed']for k in('native','clearance','islands','caps')},flush=True)

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('id');ap.add_argument('source');ap.add_argument('name');ap.add_argument('mode',choices=['caps','caps_clear','prune','tree','strict','fine']);a=ap.parse_args();run(a.id,a.source,a.name,a.mode)
