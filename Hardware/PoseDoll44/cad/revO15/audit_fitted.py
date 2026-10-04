"""Incremental exact audit of every new backpack solid and changed frame.
Unchanged mechanical pairs retain their locked independent fine-step evidence.
"""
from common import *
from fitted import build_fitted as build_full
VARIANT="carriers_equipped"
from layout_fullbody import build,fk
from connected import adjacent_pairs
from carriers_swept import ASSEMBLY_POSE,motion_bank
from raw_paths import paths

def main(char):
 pp,mm,st,f,pr,prov=build_full(char);assert not f;keys=list(pp);T0,_=fk(pr,ASSEMBLY_POSE);inv={k:np.linalg.inv(mm[k]['transform']) for k in keys};adj=adjacent_pairs(char);cache={};rr=[];potential={}
 changed=set(prov['changed_fitted']);corners={}
 for k,s in pp.items():
  b=np.array(s.bounding_box());corners[k]=np.c_[list(itertools.product(*zip(b[:3],b[3:]))),np.ones(8)]
 for i,a in enumerate(keys[:-1]):
  ga=mm[a].get('modules',[mm[a]['module']]);potential[i]=[]
  for j in range(i+1,len(keys)):
   b=keys[j]
   if a not in changed and b not in changed:continue
   gb=mm[b].get('modules',[mm[b]['module']]);related=mm[a]['body']==mm[b]['body'] or bool(set(ga)&set(gb)) or any(frozenset((x,y)) in adj for x in ga for y in gb)
   potential[i].append((j,related))
 def matrix(k,meta,T):return T[mm[k]['body']] if k.startswith(('frame/','accessory/')) else meta[mm[k].get('follows_part',k)]['transform']
 cases=[(name,m,T,{'kind':'construction_endpoint_or_coarse_path'}) for name,m,T in motion_bank(char)]
 cases += [('fine/'+name,m,T,d) for name,m,T,d in paths(char)]
 inputs={str(p):sha(p) for p in [Path(__file__),Path(__file__).with_name('fitted.py'),Path(__file__).with_name('tail_fit.py'),OUT/f'harness/{char}_tails_final.json',*list((OUT/VARIANT).glob(char+'*'))]};hard=0;contacts=0
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
   candidates=potential[i]
   if not candidates:continue
   jj=np.array([j for j,r in candidates],int);keep=np.all(np.minimum(bb[i,3:],bb[jj,3:])>np.maximum(bb[i,:3],bb[jj,:3])+1e-8,axis=1)
   for ix in np.flatnonzero(keep):
    j,related=candidates[ix]
    if not related and label!='assembly':continue
    b=keys[j];stamp=(a,b,tuple(np.round(IA@Ms[b],9).ravel()))
    if stamp not in cache:cache[stamp]=float((shape(a)^shape(b)).volume())
    if cache[stamp]>1e-4:find.append({'pair':[a,b],'overlap_mm3':cache[stamp],'classification':'STRUCTURAL' if related else 'POSE_CONTACT'})
  hard+=sum(x['classification']=='STRUCTURAL' for x in find);contacts+=sum(x['classification']=='POSE_CONTACT' for x in find);rr.append({'pose':label,'findings':find});print('FITTED AUDIT',char,index,label,'hard',hard,'queries',len(cache),flush=True)
  if index%20==0:save('harness/'+char+'_complete_tail_audit.json',{'status':'RUNNING','cases':rr,'hard_findings':hard})
 if any(sha(k)!=v for k,v in inputs.items()):raise RuntimeError('Changed evidence during audit')
 save('harness/'+char+'_complete_tail_audit.json',{'status':'SAMPLED_STRUCTURE_CLEAR' if not hard else 'STRUCTURAL_COLLISION','cases':rr,'hard_findings':hard,'assembly_pose_contacts':contacts,'case_count':len(rr),'exact_queries':len(cache),'input_sha256':inputs,'scope':'Every added rigid FFC tail, rotated PCBA, modified clip/frame and power mate vs retained solids, including all other tails. Moving wire flexibility is a separate physical validation. Nonadjacent only assembly witness here; semantic pose contacts retained in mechanical endpoint report. No cable flexibility or RF/thermal validation.'});print('FITTED SUMMARY',char,hard,contacts,flush=True)
if __name__=='__main__':main(sys.argv[1] if len(sys.argv)>1 else 'quinn')
