"""Removable local supports for changed I start footprints."""
from print_revo23_i import *
import cap_revo23_h_support as helper

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('ids',nargs='+');ap.add_argument('--source',default='unified_contours');ap.add_argument('--name',default='unified_caps');ap.add_argument('--workers',type=int,default=2);ap.add_argument('--walls',type=int);ap.add_argument('--clearance',action='store_true');a=ap.parse_args()
    configure_print();helper.HROOT=IROOT;helper.PRINT=PRINT;helper.opt=opt;helper.audit_print=audit_print;helper.run_one=run_one
    original_build=opt.build_candidate
    def build(spec,c):
        if a.walls:c.setdefault('settings',{})['wall_loops']=str(a.walls)
        if a.clearance:
            c.update(support='snug',blocker_margin_mm=2.5)
            c.setdefault('settings',{}).update(support_object_xy_distance='.65',support_expansion='0',support_threshold_angle='45')
        return original_build(spec,c)
    opt.build_candidate=build
    with concurrent.futures.ThreadPoolExecutor(max_workers=a.workers)as pool:
        list(pool.map(lambda rid:helper.fix(rid,a.source,.78,a.name),a.ids))
