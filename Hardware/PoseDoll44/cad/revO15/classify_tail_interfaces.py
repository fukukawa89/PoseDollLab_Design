"""Separate explicit overlapping envelopes in one encapsulated FFC termination.
The two CAD proxies describe the SAME manufactured tail; no inter-part clash
is waived. All 46*689 volumes must match the independent local overlap.
"""
from common import *
from sensor_tails import pigtail
r,p,e=pigtail(2,15);expected=float((r^p).volume());assert 2.44<expected<2.46
for char in ('quinn','manny'):
 path=OUT/f'harness/{char}_complete_tail_audit.json';d=read(path);assert d['case_count']==689;records=[];bad=[]
 for case in d['cases']:
  for h in case['findings']:
   a,b=h['pair'];same=a.startswith('tail/') and a.rsplit('/',1)[0]==b.rsplit('/',1)[0] and {a.rsplit('/',1)[1],b.rsplit('/',1)[1]}=={'ribbon','transition'}
   if same and abs(h['overlap_mm3']-expected)<1e-5:records.append({**h,'pose':case['pose'],'classification':'INTENDED_FFC_TERMINATION_ENVELOPE'})
   else:bad.append({**h,'pose':case['pose']})
 assert len(records)==46*689
 save(f'harness/{char}_final_audit.json',{'status':'SAMPLED_STRUCTURE_CLEAR' if not bad else 'COLLISION_REMAINS','case_count':d['case_count'],'hard_findings':bad,'nonadjacent_contacts':d['assembly_pose_contacts'],'intentional_interface_count':len(records),'interface_definition':'Polyimide ribbon inside its bonded/insulated solder-transition outer envelope, same physical pigtail. Both proxies retained for assembly illustration; not two independent hard solids.','local_overlap_mm3':expected,'raw_report_sha256':sha(path),'source_sha256':sha(__file__),'input_sha256':d['input_sha256'],'scope':d['scope'],'physical_tested':False,'continuous_sweep_proven':False})
 print('FINAL TAIL AUDIT',char,len(bad),len(records))
