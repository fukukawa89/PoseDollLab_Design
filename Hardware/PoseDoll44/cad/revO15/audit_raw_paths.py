"""Full physical-path audit: exact new-carrier contacts plus locked attachment evidence.
Unchanged different-body retained parts reuse the completed original-attachment
check. Every pair involving a fused frame and every same-body retained pair is
checked here. This avoids repeating hundreds of thousands of identical queries.
"""
from common import *
from layout_fullbody import *
from connected import build_connected,carrier_inputs,adjacent_pairs
from carriers_swept import ASSEMBLY_POSE
from raw_paths import paths

def main(char='quinn',variant='carriers_finished'):
 prior_path=OUT/f'associated_raw_paths_{char}.json';prior=read(prior_path)
 if prior['status']!='COMPLETE' or prior['hard_findings']:raise ValueError('attachment paths not clear')
 for p,h in prior['input_sha256'].items():
  if sha(Path(p))!=h:raise ValueError('attachment path evidence stale: '+p)
 p0,mm,st,f,pr,prov=build_connected(char,ASSEMBLY_POSE,variant)
 if f:raise RuntimeError(f)
 _,m0,_,_,_=build(char,ASSEMBLY_POSE,geometry=False);T0,_=fk(pr,ASSEMBLY_POSE);keys=list(p0);adj=adjacent_pairs(char)
 def matrix(k,m,T):return T[k.split('/',1)[1]] if k.startswith('frame/') else m[k]['transform']
 inv0={k:np.linalg.inv(matrix(k,m0,T0)) for k in keys};cache={};rr=[];potential={};corners={}
 for k,s in p0.items():
  b=np.array(s.bounding_box());corners[k]=np.c_[np.array(list(itertools.product(*zip(b[:3],b[3:])))),np.ones(8)]
 for i,a in enumerate(keys[:-1]):
  ma=mm[a];ga=ma.get('modules',[ma['module']]);indices=[]
  for j in range(i+1,len(keys)):
   b=keys[j];mb=mm[b];gb=mb.get('modules',[mb['module']]);same=ma['body']==mb['body']
   if not same and not a.startswith('frame/') and not b.startswith('frame/'):continue
   if same or set(ga)&set(gb) or any(frozenset((x,y)) in adj for x in ga for y in gb):indices.append(j)
  potential[i]=np.array(indices,int)
 inputs={str(p):sha(p) for p in [Path(__file__),prior_path,*[Path(__file__).with_name(x) for x in ('common.py','layout_fullbody.py','connected.py','carriers_swept.py','raw_paths.py')],OUT/f'{variant}/{char}_parts.npz',OUT/f'{variant}/{char}_routing.json',*OUT.glob('*_parts.npz'),*OUT.glob('*_build.json')]}
 for label,meta,T,detail in paths(char):
  matrices={k:matrix(k,meta,T) for k in keys};delta={k:matrices[k]@inv0[k] for k in keys};bounds=[];posed={};findings=[]
  for k in keys:
   v=(corners[k]@delta[k].T)[:,:3];bounds.append(np.r_[v.min(0),v.max(0)])
  bounds=np.array(bounds)
  def shape(k):
   if k not in posed:posed[k]=pose(p0[k],delta[k][:3,:3],delta[k][:3,3])
   return posed[k]
  for i,a in enumerate(keys[:-1]):
   ix=potential[i]
   if not len(ix):continue
   ix=ix[np.all(np.minimum(bounds[i,3:],bounds[ix,3:])>np.maximum(bounds[i,:3],bounds[ix,:3])+1e-8,axis=1)];IA=np.linalg.inv(matrices[a])
   for j in ix:
    b=keys[j];stamp=(a,b,tuple(np.round(IA@matrices[b],9).ravel()))
    if stamp not in cache:cache[stamp]=float((shape(a)^shape(b)).volume())
    if cache[stamp]>1e-4:findings.append({'pair':[a,b],'overlap_mm3':cache[stamp],'classification':'STRUCTURAL','bodies':[mm[a]['body'],mm[b]['body']]})
  rr.append({'pose':label,'path':detail,'findings':findings});print('FULL',char,label,'hard',len(findings),'queries',len(cache),flush=True)
  if detail['sample']==detail['steps']:save(f'connected/{char}_{variant}_raw_paths.json',{'status':'AUDIT_INCOMPLETE','cases':rr})
 if [x['pose'] for x in prior['rows']]!=[x['pose'] for x in rr]:raise ValueError('path evidence mismatch')
 if any(sha(Path(k))!=v for k,v in inputs.items()):raise RuntimeError('audit dependency changed')
 hard=sum(len(r['findings']) for r in rr);save(f'connected/{char}_{variant}_raw_paths.json',{'status':'SAMPLED_STRUCTURE_CLEAR' if not hard else 'STRUCTURAL_COLLISION','cases':rr,'case_count':len(rr),'hard_findings':hard,'new_carrier_and_same_body_queries':len(cache),'reused_attachment_path_report_sha256':sha(prior_path),'input_sha256':inputs,'physical_tested':False,'continuous_motion_proof':False,'scope':'Retained solid pairs: frame-involving and same-body pairs checked here, unchanged different-body attachment pairs reused from locked zero-finding report. Nonadjacent pose contacts remain in endpoint audit. No cable compliance or loaded deformation proof.'})
 print('FULL SUMMARY',char,len(rr),'hard',hard,flush=True)
if __name__=='__main__':main(sys.argv[1] if len(sys.argv)>1 else 'quinn',sys.argv[2] if len(sys.argv)>2 else 'carriers_finished')
