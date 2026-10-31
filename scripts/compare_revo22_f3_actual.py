"""Reject geometry-only orientation wins that worsen actual extrusion islands."""
import json,collections
from pathlib import Path
from build_revo22_fins_v3 import O,B
OLD=B/'a1mini_fins_v2';old=collections.defaultdict(list);new=collections.defaultdict(list)
for p in json.loads((OLD/'verification/remaining_regions.json').read_text())['plates']:
    if p['plate']=='S01':continue
    for r in p['regions']:old[r['id']].append(r['area_mm2'])
m=json.loads((O/'manifest.json').read_text())
for p in m['plates']:
    if p['optional']:continue
    f=O/'verification'/f"{p['id']}_extrusion_contacts.json"
    if not f.exists():continue
    for r in json.loads(f.read_text())['floating_printed_components']:
        bb=r['bounds_mm'];x=(bb[0]+bb[2])/2;y=(bb[1]+bb[3])/2
        it=next(i for i in p['items'] if i['bounds_mm'][0]-.5<=x<=i['bounds_mm'][3]+.5 and i['bounds_mm'][1]-.5<=y<=i['bounds_mm'][4]+.5)
        new[it['id']].append(r['area_mm2'])
rot=json.loads((O/'verification/rotation_changes.json').read_text());rows=[]
for rr in rot:
    if not rr['selected']:continue
    pid=rr['id'];a=old[pid];b=new[pid]
    # Reject clear regressions. Keep reductions in total flagged area and the largest region.
    reject=sum(b)>sum(a)+max(.05,sum(a)*.1) or max(b,default=0)>max(a,default=0)+.15
    rows.append({'id':pid,'old_bambu_count':len(a),'old_bambu_area_mm2':sum(a),'old_bambu_max_mm2':max(a,default=0),'candidate_orca_count':len(b),'candidate_orca_area_mm2':sum(b),'candidate_orca_max_mm2':max(b,default=0),'revert_candidate':reject})
(O/'verification/actual_orientation_decisions.json').write_text(json.dumps({'note':'Preliminary regression screen across native slicers; final revisions will also be checked in the same Bambu version as F2. Small numerical count changes alone do not imply poorer reliability. Clear increases in flagged area or maximum island reject a geometric-only win.','rows':rows},indent=2),encoding='utf8')
print(json.dumps(rows,indent=2),flush=True)
