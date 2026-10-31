"""Search cassette tilts about the leaf length, preserving in-layer fibers."""
import json,math,concurrent.futures
import numpy as np
from explore_revo22_f3 import *
from search_revo22_f3_plain import metrics
from search_revo22_f2_orientations import frame
from pack_revo22_a1mini import read_mesh
import check_revo22_f3_layers as layer
import repair_revo22_f3_contacts as repair
import repair_revo22_f3_side_contacts as side
from slice_revo22_f3_single import run
from verify_revo22_f3_spans import check as spans

def test(pid):
    item=next(i for p in json.loads((B/'a1mini/manifest.json').read_text())['plates'] for i in p['items'] if i['id']==pid)
    vols=next(x['volumes'] for x in json.loads((B/'a1mini_supports/design/all_protected_volumes.json').read_text())['objects'] if x['id']==pid)
    v,f=read_mesh(B/item['source_3mf']);leaf=np.array(vols[0]['local_to_source_print_matrix'])[:3,1]
    old=np.array(json.loads((OLD/'design'/f'{pid}.json').read_text())['orientation']['gravity_in_source']);u=np.cross(leaf,old);u/=np.linalg.norm(u)
    ranked=[]
    for angle in [-75,-60,-45,-30,-15,15,30,45,60,75]:
        d=old*math.cos(math.radians(angle))+u*math.sin(math.radians(angle));M=frame(d);vv=v@M.T;tr=-vv.min(0)
        ori={'matrix':M.tolist(),'source_translation_mm':tr.tolist(),'gravity_in_source':d.tolist(),'size_mm':np.ptp(vv,axis=0).tolist(),'leaf_preserving_tilt_deg':angle}
        q=metrics(v,f,M,tr);ranked.append({'angle':angle,'orientation':ori,'plain':q})
    ranked.sort(key=lambda r:r['plain']['score']);print(pid,'SAFE_RANK',[(q['angle'],round(q['plain']['score'],2)) for q in ranked],flush=True)
    records=[]
    for row in ranked[:2]:
        dest=O/'spring_candidates'/(pid+'_tilt_'+str(row['angle']).replace('-','minus'))
        for sub in ['parts','design','verification']:(dest/sub).mkdir(parents=True,exist_ok=True)
        builder.O=dest;builder.choose=lambda _:row['orientation'];builder.AXIS=None;builder.FACE_FILTER=None;builder.PITCH_OVERRIDE=2.5;builder.THICKNESS_OVERRIDE=None
        layer.O=dest;repair.O=dest;side.O=dest
        builder.make(pid,item,vols);layer.check(pid);repair.repair(pid);side.repair_side(pid)
        geo=audit(pid,dest);printed=run(pid,dest);sp=spans(next((dest/'projects').glob('*.3mf')),dest/'verification/bridge_spans.json')
        row.update(candidate=str(dest),geometry=geo,floating_printed=len(printed['floating_printed_components']),missing_teeth=printed['teeth_missing_printed_layer'],span_summary={k:sp[k] for k in ['span_count','max_span_mm','zero_anchor_spans','one_anchor_spans']})
        records.append(row)
        (O/'verification'/f'{pid}_safe_tilt_candidates.json').write_text(json.dumps({'id':pid,'ranked':ranked,'tested':records},indent=2),encoding='utf8')
    return records
if __name__=='__main__':
    with concurrent.futures.ProcessPoolExecutor(max_workers=2) as pool:list(pool.map(test,['X001','X002']))
