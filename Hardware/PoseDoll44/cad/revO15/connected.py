"""Place actual fused carriers and audit every tested solid pair."""
from common import *
from layout_fullbody import *
from carriers import ASSEMBLY_POSE

@lru_cache(maxsize=2)
def carrier_inputs(char,variant="carriers"):
 path=OUT/f'{variant}/{char}_parts.npz';report=OUT/f'{variant}/{char}_routing.json';before=(sha(path),sha(report));rr=read(report)
 with np.load(path) as z:parts={k:from_tri_exact(v) for k,v in z.items()}
 if before!=(sha(path),sha(report)):raise RuntimeError('carrier inputs changed during read')
 for dep,digest in rr.get('input_sha256',{}).items():
  if sha(Path(dep))!=digest:raise RuntimeError('carrier dependency changed: '+dep)
 for dep,digest in rr.get('source_sha256',{}).items():
  if sha(Path(__file__).with_name(dep))!=digest:raise RuntimeError('carrier source changed: '+dep)
 return rr,parts,before

def build_connected(char,angles,variant="carriers"):
 p,m,st,f,pr=build(char,angles);T,_=fk(pr,angles);rr,z,input_hashes=carrier_inputs(char,variant);provenance={}
 for r in rr['frames']:
  if r['issues'] or r['mesh']['components']!=1:f.append({'module':r['body'],'cause':'INCOMPLETE_CARRIER','issues':r['issues'],'components':r['mesh']['components']})
  k='frame/'+r['body'];s=z[r['body']];p[k]=pose(s,T[r['body']][:3,:3],T[r['body']][:3,3]);m[k]={'body':r['body'],'module':k,'sku':None,'modules':sorted(set(v.split('/')[0] for v in r['replaces'])),'owner':'rigid_frame'};provenance[k]=r['replaces']
  for old in r['replaces']:del p[old];del m[old]
 if input_hashes!=(sha(OUT/f'{variant}/{char}_parts.npz'),sha(OUT/f'{variant}/{char}_routing.json')):raise RuntimeError('carrier inputs changed after cached read')
 return p,m,st,f,pr,provenance

def adjacent_pairs(char):
 _,mm=config(char);out=set()
 for a,b in itertools.combinations(mm,2):
  # Sequential kinematic joints are structurally adjacent. Siblings are also
  # reported separately; do not silently waive them as a successful pose.
  mirror_siblings=(a['id'].replace('_l.','_r.')==b['id'] or b['id'].replace('_l.','_r.')==a['id'] or a['id'].endswith('_l') and a['id'][:-2]+'_r'==b['id'] or b['id'].endswith('_l') and b['id'][:-2]+'_r'==a['id'])
  if a['child']==b['parent'] or b['child']==a['parent'] or (a['parent']==b['parent'] and not mirror_siblings):out.add(frozenset((a['id'],b['id'])))
 return out

def audit(char,angles,variant="carriers"):
 p,m,st,f,pr,prov=build_connected(char,angles,variant);adj=adjacent_pairs(char);hh=hits(p);out=[]
 for h in hh:
  a,b=h['pair'];ma,mb=m[a],m[b];ga=ma.get('modules',[ma['module']]);gb=mb.get('modules',[mb['module']]);related=ma['body']==mb['body'] or bool(set(ga)&set(gb)) or any(frozenset((x,y)) in adj for x in ga for y in gb)
  # Every retained finding remains visible, even if pose-avoidable.
  out.append({**h,'classification':'STRUCTURAL' if related else 'POSE_CONTACT','bodies':[ma['body'],mb['body']]})
 return out,f

def main():
 char=sys.argv[1] if len(sys.argv)>1 else 'quinn';variant=sys.argv[2] if len(sys.argv)>2 else 'carriers';poses={'assembly':ASSEMBLY_POSE,**read(H/'mechanical_manifest/revO_pose_cases.json')['cases']};rr=[]
 for name,ang in poses.items():
  hh,f=audit(char,ang,variant);rr.append({'pose':name,'angles_deg':ang,'mapping_failures':f,'findings':hh});print('CONNECTED',char,name,'structural',sum(h['classification']=='STRUCTURAL' for h in hh),'contacts',sum(h['classification']=='POSE_CONTACT' for h in hh),'map',len(f),flush=True);save(f'connected/{char}_{variant}_audit.json',{'status':'DIGITAL_CHECK_NOT_RELEASE','carrier_variant':variant,'source_sha256':{n:sha(Path(__file__).with_name(n)) for n in ('connected.py','layout_fullbody.py')},'carrier_sha256':list(carrier_inputs(char,variant)[2]),'cases':rr,'physical_tested':False,'wiring_included':False,'continuous_motion_proof':False})
if __name__=='__main__':main()
