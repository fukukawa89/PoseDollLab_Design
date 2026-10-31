"""Test orientations that keep the cassette leaf length in the print-layer plane."""
import json,numpy as np
from explore_revo22_f3 import *
import check_revo22_f3_layers as layer
import repair_revo22_f3_contacts as repair
import repair_revo22_f3_side_contacts as side
from slice_revo22_f3_single import run
items={i['id']:i for p in json.loads((B/'a1mini/manifest.json').read_text())['plates'] for i in p['items']}
guards=json.loads((B/'a1mini_supports/design/all_protected_volumes.json').read_text())['objects']
records=[]
for pid in ['X001','X002']:
    vols=next(x['volumes'] for x in guards if x['id']==pid)
    leaf=np.array(vols[0]['local_to_source_print_matrix'])[:3,1]
    candidates=json.loads((O/'orientation_plain'/f'{pid}.json').read_text())
    for ori in candidates:
        d=np.array(ori['orientation']['gravity_in_source'])
        if abs(d@leaf)>.01 or abs(d[2])>.99 or max(abs(d))<.999:continue
        dest=O/'spring_candidates'/(pid+'_'+ori['label'])
        for sub in ['parts','design','verification']:(dest/sub).mkdir(parents=True,exist_ok=True)
        builder.O=dest;builder.AXIS=None;builder.FACE_FILTER=None;builder.PITCH_OVERRIDE=None;builder.THICKNESS_OVERRIDE=None;builder.choose=lambda _:ori['orientation']
        layer.O=dest;repair.O=dest;side.O=dest
        r=builder.make(pid,items[pid],vols);layer.check(pid);repair.repair(pid);side.repair_side(pid)
        metrics=audit(pid,dest);printed=run(pid,dest)
        records.append({'id':pid,'candidate':str(dest),'orientation':ori['orientation'],'leaf_vertical_component':float(d@leaf),'geometry':metrics,
            'floating_printed':len(printed['floating_printed_components']),'missing_teeth':printed['teeth_missing_printed_layer']})
        (O/'verification/spring_candidates.json').write_text(json.dumps(records,indent=2),encoding='utf8')
        print('SPRING',pid,ori['label'],'actual_floating',len(printed['floating_printed_components']),flush=True)

