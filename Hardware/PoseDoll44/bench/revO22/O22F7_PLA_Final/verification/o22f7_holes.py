import sys,concurrent.futures
import o22f7 as r
import o22f7_deposited as d

def run(p):
 d.OUT=r.OUT;d.WORK=r.WORK;d.PROJECT_SUFFIX='PLA_final';d.GUARD_PART_IDS=None;d.REPORT_NAME='deposited_hole_clearance.json';d.check(p)
 d.GUARD_PART_IDS={x['id']for x in r.manifest()['rows']}-r.RESTORE;d.REPORT_NAME='deposited_retained_clearance.json';return d.check(p)
if __name__=='__main__':
 jobs=[p for p in r.manifest()['plates']if p['id']in sys.argv[1:]]
 with concurrent.futures.ProcessPoolExecutor(max_workers=2)as pool:
  for result in pool.map(run,jobs):pass
