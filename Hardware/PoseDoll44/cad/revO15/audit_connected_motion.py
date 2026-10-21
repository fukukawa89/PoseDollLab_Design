"""Exact all-part intersections on the declared full-body motion bank.
Cache only repeated rigid relative transforms; keep every pose contact witness.
"""
from common import *
from layout_fullbody import *
from connected import build_connected,carrier_inputs,adjacent_pairs
from carriers_swept import ASSEMBLY_POSE,motion_bank

def main(char='quinn',variant='carriers_swept'):
 p0,mm,st,f,pr,prov=build_connected(char,ASSEMBLY_POSE,variant)
 if f:raise RuntimeError(f)
 _,m0,_,_,_=build(char,ASSEMBLY_POSE,geometry=False);T0,_=fk(pr,ASSEMBLY_POSE);bank=motion_bank(char);keys=list(p0);adj=adjacent_pairs(char)
 def matrix(k,m,T):return T[k.split('/',1)[1]] if k.startswith('frame/') else m[k]['transform']
 inv0={k:np.linalg.inv(matrix(k,m0,T0)) for k in keys};cache={};rr=[];queries=0
 inputs={str(p):sha(p) for p in [Path(__file__),*[Path(__file__).with_name(x) for x in ('common.py','layout_fullbody.py','connected.py','carriers_swept.py')],OUT/f'{variant}/{char}_parts.npz',OUT/f'{variant}/{char}_routing.json',*OUT.glob('*_parts.npz'),*OUT.glob('*_build.json')]}
 for label,meta,T in bank:
  matrices={k:matrix(k,meta,T) for k in keys};parts={k:pose(s,(matrices[k]@inv0[k])[:3,:3],(matrices[k]@inv0[k])[:3,3]) for k,s in p0.items()};bounds=np.array([s.bounding_box() for s in parts.values()]);inverses={k:np.linalg.inv(v) for k,v in matrices.items()};findings=[];candidates=0
  for i,a in enumerate(keys[:-1]):
   aa=bounds[i];indices=np.flatnonzero(np.all(np.minimum(aa[3:],bounds[i+1:,3:])>np.maximum(aa[:3],bounds[i+1:,:3])+1e-8,axis=1))+i+1
   for j in indices:
    b=keys[j];rel=inverses[a]@matrices[b];stamp=(a,b,tuple(np.round(rel,9).ravel()));candidates+=1
    if stamp not in cache:cache[stamp]=float((parts[a]^parts[b]).volume());queries+=1
    volume=cache[stamp]
    if volume<=1e-4:continue
    ma,mb=mm[a],mm[b];ga=ma.get('modules',[ma['module']]);gb=mb.get('modules',[mb['module']]);related=ma['body']==mb['body'] or bool(set(ga)&set(gb)) or any(frozenset((x,y)) in adj for x in ga for y in gb)
    findings.append({'pair':[a,b],'overlap_mm3':volume,'classification':'STRUCTURAL' if related else 'POSE_CONTACT','bodies':[ma['body'],mb['body']]})
  rr.append({'pose':label,'findings':findings,'broad_candidates':candidates});print('FULL',char,variant,label,'structural',sum(h['classification']=='STRUCTURAL' for h in findings),'contacts',sum(h['classification']=='POSE_CONTACT' for h in findings),'unique_queries',queries,flush=True)
  save(f'connected/{char}_{variant}_motion.json',{'status':'AUDIT_INCOMPLETE','cases':rr})
 if any(sha(Path(k))!=v for k,v in inputs.items()):raise RuntimeError('audit dependency changed')
 hard=sum(h['classification']=='STRUCTURAL' for r in rr for h in r['findings']);save(f'connected/{char}_{variant}_motion.json',{'status':'SAMPLED_STRUCTURE_CLEAR' if not hard else 'STRUCTURAL_COLLISION','cases':rr,'case_count':len(rr),'hard_findings':hard,'unique_narrow_phase_queries':queries,'input_sha256':inputs,'physical_tested':False,'continuous_motion_proof':False,'scope':'All retained CAD solids, including fasteners and full printed carriers. Nonadjacent pose contacts retained separately. No cable compliance or loaded deformation model.'})
 print('FULL SUMMARY',char,len(rr),'hard findings',hard,flush=True)
if __name__=='__main__':main(sys.argv[1] if len(sys.argv)>1 else 'quinn',sys.argv[2] if len(sys.argv)>2 else 'carriers_swept')
