"""All retained attachment contacts with final rigid-frame associations.
Keep original end pieces separate: collision with their union is equivalent to
collision with any member. Same-body seams are excluded in this pre-route check.
"""
from associated_fit import *
from raw_paths import paths


def main(char='quinn'):
 inputs={str(p):sha(p) for p in [Path(__file__),Path(__file__).with_name('layout_fullbody.py'),Path(__file__).with_name('raw_paths.py'),*OUT.glob('*_parts.npz')]}
 print('BUILD START',char,flush=True);p0,mm,st,f,pr=build(char,ASSEMBLY_POSE);aa=anchors(st,mm);print('BUILD DONE',len(p0),flush=True)
 for ends in aa.values():
  mods=sorted(set(mm[e['part']]['module'] for e in ends))
  for e in ends:mm[e['part']]['modules']=mods
 _,m0,_,_,_=build(char,ASSEMBLY_POSE,geometry=False);keys=list(p0);adj=adjacent_pairs(char)
 I0={k:np.linalg.inv(m0[k]['transform']) for k in keys};corners={}
 for k,s in p0.items():
  b=np.array(s.bounding_box());corners[k]=np.c_[np.array(list(itertools.product(*zip(b[:3],b[3:])))),np.ones(8)]
 print('BOUNDS DONE',char,flush=True);potential={};cache={};rows=[]
 for i,a in enumerate(keys[:-1]):
  ma=mm[a];ga=ma.get('modules',[ma['module']]);others=[]
  for j in range(i+1,len(keys)):
   b=keys[j];mb=mm[b];gb=mb.get('modules',[mb['module']])
   if ma['body']!=mb['body'] and (set(ga)&set(gb) or any(frozenset((x,y)) in adj for x in ga for y in gb)):others.append(j)
  potential[i]=np.array(others,int)
 print('PAIR TABLE DONE',sum(map(len,potential.values())),flush=True)
 for label,m,T,detail in paths(char):
  delta={k:m[k]['transform']@I0[k] for k in keys};boxes=[];posed={};findings=[]
  for k in keys:
   v=(corners[k]@delta[k].T)[:,:3];boxes.append(np.r_[v.min(0),v.max(0)])
  bounds=np.array(boxes)
  def shape(k):
   if k not in posed:posed[k]=pose(p0[k],delta[k][:3,:3],delta[k][:3,3])
   return posed[k]
  for i,a in enumerate(keys[:-1]):
   ix=potential[i]
   if not len(ix):continue
   ix=ix[np.all(np.minimum(bounds[i,3:],bounds[ix,3:])>np.maximum(bounds[i,:3],bounds[ix,:3])+1e-8,axis=1)];IA=np.linalg.inv(m[a]['transform'])
   for j in ix:
    b=keys[j];stamp=(a,b,tuple(np.round(IA@m[b]['transform'],9).ravel()))
    if stamp not in cache:
     save('active_query_'+char+'.json',{'pose':label,'pair':[a,b],'query_index':len(cache)})
     cache[stamp]=float((shape(a)^shape(b)).volume())
    if cache[stamp]>1e-4:findings.append({'pair':[a,b],'volume_mm3':cache[stamp]})
  rows.append({'character':char,'pose':label,'path':detail,'findings':findings});print('ASSOCIATED',char,label,len(findings),'queries',len(cache),flush=True)
  if detail['sample']==detail['steps']:save('associated_raw_paths_'+char+'.json',{'status':'IN_PROGRESS','rows':rows})
 if any(sha(Path(k))!=v for k,v in inputs.items()):raise RuntimeError('Dependency changed')
 save('associated_raw_paths_'+char+'.json',{'status':'COMPLETE','rows':rows,'hard_findings':sum(len(r['findings']) for r in rows),'input_sha256':inputs,'scope':'All original retained attachments with eventual frame associations; no connecting tubes, no continuous proof.'})
if __name__=='__main__':main(sys.argv[1] if len(sys.argv)>1 else 'quinn')
