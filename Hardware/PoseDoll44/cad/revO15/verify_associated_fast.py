from associated_fit import *
from carriers_swept import motion_bank

def main():
 rows=[];inputs={str(p):sha(p) for p in [Path(__file__),Path(__file__).with_name('layout_fullbody.py'),Path(__file__).with_name('associated_fit.py'),*OUT.glob('*_parts.npz')]}
 for char in ('quinn','manny'):
  p0,mm,f=associated_parts(char,ASSEMBLY_POSE);_,m0,_,_,pr=build(char,ASSEMBLY_POSE,geometry=False);T0,_=fk(pr,ASSEMBLY_POSE);adj=adjacent_pairs(char);keys=list(p0)
  def matrix(k,m,T):return T[k.split('/',1)[1]] if k.startswith('frame/') else m[k]['transform']
  I0={k:np.linalg.inv(matrix(k,m0,T0)) for k in keys};cache={};potential={}
  for i,a in enumerate(keys[:-1]):
   ma=mm[a];ga=ma.get('modules',[ma['module']]);others=[]
   for j in range(i+1,len(keys)):
    b=keys[j];mb=mm[b];gb=mb.get('modules',[mb['module']])
    if ma['body']==mb['body']:continue
    if set(ga)&set(gb) or any(frozenset((x,y)) in adj for x in ga for y in gb):others.append(j)
   potential[i]=np.array(others,int)
  for label,m,T in motion_bank(char):
   matrices={k:matrix(k,m,T) for k in keys};parts={k:pose(s,(matrices[k]@I0[k])[:3,:3],(matrices[k]@I0[k])[:3,3]) for k,s in p0.items()};bounds=np.array([s.bounding_box() for s in parts.values()]);findings=[]
   for i,a in enumerate(keys[:-1]):
    ix=potential[i]
    if not len(ix):continue
    ix=ix[np.all(np.minimum(bounds[i,3:],bounds[ix,3:])>np.maximum(bounds[i,:3],bounds[ix,:3])+1e-8,axis=1)]
    IA=np.linalg.inv(matrices[a])
    for j in ix:
     b=keys[j];stamp=(a,b,tuple(np.round(IA@matrices[b],9).ravel()))
     if stamp not in cache:cache[stamp]=float((parts[a]^parts[b]).volume())
     v=cache[stamp]
     if v>1e-4:findings.append({'pair':[a,b],'volume_mm3':v})
   rows.append({'character':char,'pose':label,'findings':findings});print('ASSOCIATED',char,label,len(findings),flush=True)
  print('ASSOCIATED CHARACTER DONE',char,flush=True)
 if any(sha(Path(k))!=v for k,v in inputs.items()):raise RuntimeError('Dependency changed')
 save('associated_all_fast.json',{'rows':rows,'hard_findings':sum(len(r['findings']) for r in rows),'input_sha256':inputs,'scope':'Actual retained attachments with eventual frame associations, no connecting tubes, same-body integration deferred.'})
if __name__=='__main__':main()
