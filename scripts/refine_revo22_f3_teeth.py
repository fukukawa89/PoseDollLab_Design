"""Physically remove unused needle tails or strengthen a short missing connection.
Only targets measured from actual extrusion; body meshes are unchanged.
"""
import json,math,sys,faulthandler
faulthandler.enable()
import numpy as np
from build_revo22_fins_v3 import *
stage=O/'iteration1';manifest=json.loads((stage/'manifest.json').read_text());reverted=set(json.loads((O/'verification/selection.json').read_text())['actual_extrusion_reverted_types']);targets={}
for p in manifest['plates']:
 report=json.loads((stage/'verification'/f"{p['id']}_extrusion_contacts.json").read_text());byname={i['object_name']:i for i in p['items']}
 for t in report['teeth']:
  if t['continuous_printed_stack']:continue
  item=byname[t['object_name']]
  if item['id'] in reverted:continue
  targets[(item['id'],t['tooth'])]=t
records=[]
for pid in sorted({k[0] for k in targets}):
 if len(sys.argv)>1 and pid not in sys.argv[1:]:continue
 n=dict(np.load(O/'parts'/f'{pid}.npz'));r=json.loads((O/'design'/f'{pid}.json').read_text());s=solid(n['v'],n['f']);b=solid(n['fin_v'],n['fin_f']);t=solid(n['teeth_v'],n['teeth_f']);before=t.volume();changes=[]
 vols=next((x['volumes'] for x in json.loads((D/'all_protected_volumes.json').read_text())['objects'] if x['part']==r['part']),[]);ban=protected(vols).transform(np.c_[r['orientation']['matrix'],r['orientation']['source_translation_mm']])
 for (part,index),evidence in targets.items():
  if part!=pid:continue
  print('TOOTH_START',pid,index,flush=True);rec=r['teeth'][index-1];bb=np.array(rec['bounds_mm']);piece=t^box(bb[:3]-1e-6,bb[3:]+1e-6);oldbite=float((piece^s).volume());bad=[q for q in evidence['layers'] if q['printed_overlap_mm2']<q['minimum_required_overlap_mm2']];first=min(q['z_mm'] for q in bad)
  earlier=[q for q in evidence['layers'] if q['z_mm']<first and q.get('printed_part_contact_area_lower_bound_mm2',0)>.005]
  candidate=None;kind=None
  if earlier:
   cap=first-.101;cut=box([bb[0]-1,bb[1]-1,cap],[bb[3]+1,bb[4]+1,bb[5]+1]);q=piece-cut
   if (q^s).volume()>=max(.005,oldbite*.6) and (q^b).volume()>.02:candidate=q;kind='trim_unused_upper_tail';detail={'new_cap_z_mm':cap,'previous_printed_contact_lower_bound_mm2':max(q['printed_part_contact_area_lower_bound_mm2'] for q in earlier)}
  if candidate is None:
   for widen in [.04,.08,.16]:
    q=box(bb[:3]-[widen,widen,0],bb[3:]+[widen,widen,.3]);bite=float((q^s).volume())
    if bite<.02 or bite>max(1.,oldbite*3) or (q^b).volume()<.02 or (q^ban).volume()>1e-7:continue
    candidate=q;kind='flat_printable_contact_tip';detail={'xy_extra_each_side_mm':widen,'extra_top_mm':.3};break
  if candidate is None:
   changes.append({'tooth':index,'unresolved':True});continue
  t=(t-cut).set_tolerance(1e-5) if kind=='trim_unused_upper_tail' else (t+candidate).set_tolerance(1e-5);rec.update(bounds_mm=list(candidate.bounding_box()),part_bite_mm3=float((candidate^s).volume()),fin_root_mm3=float((candidate^b).volume()),actual_extrusion_revision=kind)
  bite=candidate^s;bbb=np.array(bite.bounding_box());rec['contact_point_mm']=((bbb[:3]+bbb[3:])/2).tolist()
  changes.append({'tooth':index,'change':kind,'old_bite_mm3':oldbite,'new_bite_mm3':rec['part_bite_mm3'],**detail})
 assert abs((t^ban).volume())<1e-6
 for c in t.decompose():assert (c^s).volume()>.005 and (c^b).volume()>.005,(pid,c.volume())
 n['teeth_v'],n['teeth_f']=vf(t);np.savez_compressed(O/'parts'/f'{pid}.npz',**n);r.update(actual_tooth_refinements=changes,support_volume_mm3=float((b+t).volume()),teeth_part_overlap_mm3=float((t^s).volume()));(O/'design'/f'{pid}.json').write_text(json.dumps(r,ensure_ascii=False,indent=2),encoding='utf8');records.append({'id':pid,'changes':changes,'removed_tooth_volume_mm3':before-t.volume()});print('TOOTH_REVISED',pid,len(changes),'unresolved',sum(x.get('unresolved',False) for x in changes),flush=True)
(O/'verification'/('tooth_refinements_'+('_'.join(sys.argv[1:]) or 'all')+'.json')).write_text(json.dumps(records,indent=2),encoding='utf8')
