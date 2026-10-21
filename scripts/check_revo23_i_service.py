"""Recheck service access and cable dimensions against the actual I assembly."""
from revo23_unified import *
import sys

mode=sys.argv.pop(1)
if mode=='access':
    import check_revo23_compact_access as a
    (IROOT/'design').mkdir(exist_ok=True)
    shutil.copy2(B/'design/compact_revision.json',IROOT/'design/compact_revision.json')
    a.B=IROOT;a.load_current=lambda:load_i()[0]
    a.main()
elif mode=='routes':
    import route_revo23_harness as r
    for name in ('wire_seats','wire_channels'):
        shutil.copy2(IHISTORY/'harness'/(name+'.json'),IROOT/(name+'.json'))
    r.EROOT=IROOT;r.DHISTORY=IHISTORY;r.DHASH=sha(IROOT/'assembly.npz');r.load_e=load_i
    r.main()
    path=IROOT/'harness/routing_plan.json';data=read(path)
    data.update(schema='POSEDOLL-O23I-HARNESS/1',geometry_sha256=sha(IROOT/'assembly.npz'))
    put(path,data)
else:raise ValueError(mode)
