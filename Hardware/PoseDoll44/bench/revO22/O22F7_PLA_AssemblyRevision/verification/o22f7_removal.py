"""Recheck withdrawal of fins carrying R1's added cut connector stubs."""
import sys,json,numpy as np
import o22f7 as r
PID=sys.argv[1]
from route_revo22_x062244 import tooth,sweep_convex
from verify_revo22_f5_contacts298 import line_sweep
h=r.h

def run():
 n=np.load(r.OUT/f'parts/{PID}.npz');body=h.solid(n['v'],n['f']);fin=h.solid(n['fin_v'],n['fin_f']);d=json.loads((r.OUT/f'design/{PID}.json').read_text());rows=next(x for x in json.loads((h.SRC/'manifest.json').read_text())['rows']if x['id']==PID);gp=np.load(h.SRC/f'verification/parts/{PID}/f5_fin_groups.npz');groups={}
 for j,q in enumerate(rows['fin_bodies'],1):groups[q['id']]=h.solid(gp[f'g{j}_v'],gp[f'g{j}_f'])^fin
 parent={k:k for k in groups}
 def root(k):
  while parent[k]!=k:k=parent[k]
  return k
 connectors=[]
 for i,rec in enumerate(d.get('r1_native_contacts',[])):
  a=np.array(rec['root']);b=np.array(rec['tip']);cut=a+(b-a)*((rec['cut_z_mm']-a[2])/(b[2]-a[2]));stub=tooth(a,cut,.8);hits=[k for k,s in groups.items()if(stub^s).volume()>.005];assert hits,(i,hits)
  for k in hits[1:]:parent[root(k)]=root(hits[0])
  connectors.append((i,stub,rec,hits))
 members={}
 for k in groups:members.setdefault(root(k),[]).append(k)
 names={k:'+'.join(sorted(v))for k,v in members.items()};mapping={k:names[root(k)]for k in groups}
 groups={names[k]:h.union([groups[x]for x in v])for k,v in members.items()};attached={k:[]for k in groups};assign=[]
 for i,stub,rec,hits in connectors:
  key=mapping[hits[0]];attached[key].append((stub,rec));assign.append(dict(connector=i+1,group=key,record=rec))
 old_order=[k for stage in rows['removal_stages']for k in stage['groups']]
 original_order=sorted(groups,key=lambda k:max(old_order.index(x)for x in k.split('+')));reps=[]
 for k,pairs in attached.items():
  if not pairs:continue
  options=[np.array([0.,0.,-1.])]+[np.array(x[1]['removal_vector'])for x in pairs];options.append(np.sum(options[1:],axis=0));sweep=None;chosen=None
  for v in options:
   v=v/np.linalg.norm(v);pieces=[sweep_convex(stub,v*100) for stub,_ in pairs]
   if any((s^body).volume()>1e-6 for s in pieces):continue
   fin_sweep=sweep_convex(groups[k],v*100)
   if(fin_sweep^body).volume()>1e-6:
    fin_sweep=line_sweep(groups[k],v*100)
    if(fin_sweep^body).volume()>1e-6:continue
   combined=fin_sweep+h.union(pieces);later=original_order[original_order.index(k)+1:];hits=[]
   for other in later:
    if(combined^groups[other]).volume()>1e-6:hits.append(other)
   if hits:continue
   sweep=combined;chosen=v;break
  assert chosen is not None,('No continuous fin+stub exit in existing removal order',k)
  rep=dict(group=k,vector=chosen.tolist(),new_connector_numbers=[i['connector']for i in assign if i['group']==k],body_sweep_overlap_mm3=max(0.,float((sweep^body).volume())),remaining_fin_sweep_overlap_mm3=0.,relative_order_of_unjoined_groups_retained=True);reps.append(rep);print('WITHDRAWAL',rep,flush=True)
 report=dict(npz_sha256=h.sha(r.OUT/f'parts/{PID}.npz'),passed=True,affected_groups=reps,connections=assign,revised_removal_order=original_order,simultaneous_groups=[k.split('+')for k in groups if'+'in k],scope='After cutting new teeth at recorded cut planes, remaining stubs withdraw with their fin in the recorded direction. Continuous swept-volume tests against permanent body and all later fin groups; any explicitly joined group is removed together. Clip all other old connection teeth and obstructing roots as in the original instructions. Fins without new stubs retain the exact-subset/new-elbow exclusion proof.',physical_removal_tested=False)
 h.put(r.WORK/f'removal/{PID}.json',report)
if __name__=='__main__':run()