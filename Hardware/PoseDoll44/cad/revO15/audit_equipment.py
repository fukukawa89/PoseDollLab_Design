"""Incremental exact audit of every new backpack solid and changed frame.
Unchanged mechanical pairs retain their locked independent fine-step evidence.
"""
from common import *
from equipped import build_full,VARIANT
from layout_fullbody import build,fk
from connected import adjacent_pairs
from carriers_swept import ASSEMBLY_POSE,motion_bank
from raw_paths import paths

def main(char):
 pp,mm,st,f,pr,_=build_full(char);assert not f;keys=list(pp);T0,_=fk(pr,ASSEMBLY_POSE);inv={k:np.linalg.inv(mm[k]['transform']) for k in keys};adj=adjacent_pairs(char);cache={};rr=[];potential={}
 changed={k for k in keys if k.startswith('accessory/') or k in ('frame/chest','frame/pelvis')};corners={}
 for k,s in pp.items():
  b=np.array(s.bounding_box());corners[k]=np.c_[list(itertools.product(*zip(b[:3],b[3:]))),np.ones(8)]
 for i,a in enumerate(keys[:-1]):
  ga=mm[a].get('modules',[mm[a]['module']]);potential[i]=[]
  for j in range(i+1,len(keys)):
   b=keys[j]
   if a not in changed and b not in changed:continue
   gb=mm[b].get('modules',[mm[b]['module']]);related=mm[a]['body']==mm[b]['body'] or bool(set(ga)&set(gb)) or any(frozenset((x,y)) in adj for x in ga for y in gb)
   potential[i].append((j,related))
 def matrix(k,meta,T):return T[mm[k]['body']] if k.startswith(('frame/','accessory/')) else meta[k]['transform']
 cases=[(name,m,T,{'kind':'construction_endpoint_or_coarse_path'}) for name,m,T in motion_bank(char)]
 cases += [('fine/'+name,m,T,d) for name,m,T,d in paths(char)]
 inputs={str(p):sha(p) for p in [Path(__file__),Path(__file__).with_name('equipped.py'),Path(__file__).with_name('equipment_parts.py'),*list((OUT/VARIANT).glob(char+'*'))]};hard=0;contacts=0
 for index,(label,meta,T,detail) in enumerate(cases):
  Ms={k:matrix(k,meta,T) for k in keys};delta={k:Ms[k]@inv[k] for k in keys};bb=[];placed={};find=[]
  for k in keys:
   v=(corners[k]@delta[k].T)[:,:3];bb.append(np.r_[v.min(0),v.max(0)])
  bb=np.array(bb)
  def shape(k):
   if k not in placed:placed[k]=pose(pp[k],delta[k][:3,:3],delta[k][:3,3])
   return placed[k]
  for i,a in enumerate(keys[:-1]):
   IA=np.linalg.inv(Ms[a])
   for j,related in potential[i]:
    if not related and label!='assembly':continue
    if np.any(np.minimum(bb[i,3:],bb[j,3:])<=np.maximum(bb[i,:3],bb[j,:3])+1e-8):continue
    b=keys[j];stamp=(a,b,tuple(np.round(IA@Ms[b],9).ravel()))
    if stamp not in cache:cache[stamp]=float((shape(a)^shape(b)).volume())
    if cache[stamp]>1e-4:find.append({'pair':[a,b],'overlap_mm3':cache[stamp],'classification':'STRUCTURAL' if related else 'POSE_CONTACT'})
  hard+=sum(x['classification']=='STRUCTURAL' for x in find);contacts+=sum(x['classification']=='POSE_CONTACT' for x in find);rr.append({'pose':label,'findings':find});print('EQUIPMENT AUDIT',char,index,label,'hard',hard,'queries',len(cache),flush=True)
  if index%20==0:save('equipment/'+char+'_audit.json',{'status':'RUNNING','cases':rr,'hard_findings':hard})
 if any(sha(k)!=v for k,v in inputs.items()):raise RuntimeError('Changed evidence during audit')
 save('equipment/'+char+'_audit.json',{'status':'SAMPLED_STRUCTURE_CLEAR' if not hard else 'STRUCTURAL_COLLISION','cases':rr,'hard_findings':hard,'assembly_pose_contacts':contacts,'case_count':len(rr),'exact_queries':len(cache),'input_sha256':inputs,'scope':'Every added equipment solid and changed frame vs retained solids. Nonadjacent only assembly witness here; semantic pose contacts retained in mechanical endpoint report. No cable flexibility or RF/thermal validation.'});print('EQUIPMENT SUMMARY',char,hard,contacts,flush=True)
if __name__=='__main__':main(sys.argv[1] if len(sys.argv)>1 else 'quinn')
