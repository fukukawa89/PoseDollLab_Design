from common import *
from layout_fullbody import *
from search_adjacent import first_cross
pr,mm=config('quinn');pairs=set()
for a,b in itertools.combinations(mm,2):
 if a['child']==b['parent'] or b['child']==a['parent'] or a['parent']==b['parent']:pairs.add(frozenset((a['id'],b['id'])))
poses=read(H/'mechanical_manifest/revO_pose_cases.json')['cases'];out=[]
for label,angles in poses.items():
 p,m,st,f,_=build('quinn',angles);hh=module_hits(p,m,pairs);hard=[{'modules':g['modules'],'records':[h for h in g['findings'] if not(h['same_rigid_body'] and h['both_printed'])]} for g in hh];hard=[g for g in hard if g['records']];out.append({'pose':label,'angles':angles,'mapping_failures':f,'findings':hard,'integration_findings':hh});print(label,'mapping',len(f),'hard pairs',[(g['modules'],len(g['records'])) for g in hard],flush=True);save('adjacent_layout_audit.json',{'pairs':[sorted(x) for x in pairs],'samples':out,'scope':'Bare module placement, connecting frames and wires still excluded'})
