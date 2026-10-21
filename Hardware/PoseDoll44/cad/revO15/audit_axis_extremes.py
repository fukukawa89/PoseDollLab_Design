from carriers_swept import motion_bank
from connected import adjacent_pairs
from layout_fullbody import *
from collision_fast import first_cross
char=sys.argv[1] if len(sys.argv)>1 else 'quinn';bank=motion_bank(char);adj=adjacent_pairs(char);kinds={m['id']:m['kind'] for m in config(char)[1]};raw={}
for name,kind in kinds.items():
 for local,shape in libraries()[kind][0].items():
  if kind=='hinge' and local=='lever_cup':shape=shape^box([-50,-50,-50],[14,50,50])
  raw[name+'/'+local]=shape
inputs={str(p):sha(p) for p in [Path(__file__),Path(__file__).with_name('layout_fullbody.py'),Path(__file__).with_name('collision_fast.py'),*[Path(__file__).with_name(x) for x in ('common.py','carriers_swept.py','connected.py','tut.py','three_axis.py')],H/'mechanical_manifest/revO_pose_cases.json',G3/f'layouts/{char}/anatomy_profile.json',OUT/'serial_clavicle_bilateral_search.json',*OUT.glob('*_parts.npz'),*OUT.glob('*_build.json')]}
rr=[];printed=set()
for index,(label,meta,T) in enumerate(bank):
 pp={k:pose(s,meta[k]['transform'][:3,:3],meta[k]['transform'][:3,3]) for k,s in raw.items()};hit=first_cross(pp,meta,adj,skip_same_body=True)
 rr.append({'case':label,'first_moving_finding':hit,'moving_pair_findings':int(hit is not None)})
 pair=tuple(hit['parts']) if hit else None
 if pair not in printed or index%20==0:print('AXES',char,index,label,hit,flush=True);printed.add(pair)
if any(sha(Path(k))!=v for k,v in inputs.items()):raise RuntimeError('inputs changed during audit')
save(f'axis_extremes_{char}.json',{'cases':rr,'scope':'Bare-module moving adjacent pairs. Stops at first witness per failed pose. Same-body integrations require the connected audit.','input_sha256':inputs,'passed':sum(not x['moving_pair_findings'] for x in rr),'total':len(rr)})
print('AXES SUMMARY',char,len(rr),sum(x['moving_pair_findings'] for x in rr),flush=True)
