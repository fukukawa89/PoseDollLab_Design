"""Export unique, bed-oriented physical printed parts from the retained assembly.
No invisible module proxies or diagnostic G-code enter the supplier package.
"""
from common import *
from connected import build_connected,carrier_inputs
from fitted import build_fitted as build_full
from carriers_swept import ASSEMBLY_POSE
from layout_fullbody import build,fk
import print_io as pack


def hull(points):
 p=sorted(set(tuple(x) for x in points))
 def cross(o,a,b):return (a[0]-o[0])*(b[1]-o[1])-(a[1]-o[1])*(b[0]-o[0])
 if len(p)<3:return np.array(p)
 lo=[];hi=[]
 for a in p:
  while len(lo)>=2 and cross(lo[-2],lo[-1],a)<=0:lo.pop()
  lo.append(a)
 for a in reversed(p):
  while len(hi)>=2 and cross(hi[-2],hi[-1],a)<=0:hi.pop()
  hi.append(a)
 return np.array(lo[:-1]+hi[:-1])


def in_hull(c,h):
 if len(h)<3:return False
 d=np.roll(h,-1,axis=0)-h;p=c-h;return bool(np.all(d[:,0]*p[:,1]-d[:,1]*p[:,0]>=-1e-6))


def inspect(s):
 t=tri(s);rec=mesh_record(s);cr=np.cross(t[:,1]-t[:,0],t[:,2]-t[:,0]);mask=(t[:,:,2].max(1)<1e-4)&(cr[:,2]<-1e-8);contact=hull(t[mask].reshape(-1,3)[:,:2]);area=np.linalg.norm(cr,axis=1)/2
 return {**rec,'flat_contact_area_mm2':float(area[mask].sum()),'contact_hull_mm':contact.tolist(),'COM_over_model_contact_hull':in_hull(np.array(rec['COM_mm'][:2]),contact),'downward_nonbed_area_mm2':float(area[(cr[:,2]<-.7071*2*area)&~mask].sum())}


def bed_rotation(n):
 n=np.asarray(n)/np.linalg.norm(n);z=np.array([0.,0.,-1.]);c=np.clip(n@z,-1,1);axis=np.cross(n,z)
 if np.linalg.norm(axis)<1e-7:return np.eye(3) if c>0 else rot(0,180)
 return rot(axis,np.rad2deg(np.arccos(c)))


def orient(s):
 t=tri(s);cr=np.cross(t[:,1]-t[:,0],t[:,2]-t[:,0]);area=np.linalg.norm(cr,axis=1)/2;nn=cr/np.maximum(2*area[:,None],1e-20);groups={};directions={};largest={}
 for n,a in zip(nn,area):
  if a<1e-5:continue
  stamp=tuple(np.round(n,4));groups[stamp]=groups.get(stamp,0)+float(a)
  if a>largest.get(stamp,0):directions[stamp]=n;largest[stamp]=a
 candidates=sorted(groups,key=groups.get,reverse=True)[:18];rows=[]
 for n in candidates:
  Q=bed_rotation(directions[n]);v=pose(s,Q);bb=np.array(v.bounding_box());shift=-bb[:3]+[8,8,0];v=v.translate(shift);r=inspect(v);size=np.array(r['bounds_mm'][3:])-r['bounds_mm'][:3]
  if size[0]>240 or size[1]>240 or size[2]>250 or r['flat_contact_area_mm2']<=.25:continue
  # Prefer a meaningful planar seat, then less unsupported surface and lower height.
  score=10000*int(r['COM_over_model_contact_hull'])+5*r['flat_contact_area_mm2']-.5*r['downward_nonbed_area_mm2']-.15*size[2]
  rows.append((score,v,r,Q,shift))
 if not rows:raise RuntimeError('No orientation fits a 256 mm bed')
 _,v,r,Q,shift=max(rows,key=lambda x:x[0]);assert r['flat_contact_area_mm2']>.25 and abs(r['bounds_mm'][2])<1e-6
 return v,{**r,'rotation':Q.tolist(),'translation_mm':shift.tolist(),'supports_required':r['downward_nonbed_area_mm2']>1,'orientation_scope':'Planar bed contact and geometric support diagnostic; not validated layer strength or adhesion.'}


def stl(path,s):
 tt=tri(s).astype('<f4');buf=bytearray(b'PoseDoll O15 mm; prototype; re-slice for actual printer'.ljust(80,b' '));buf+=struct.pack('<I',len(tt))
 for t in tt:
  n=np.cross(t[1]-t[0],t[2]-t[0]);n/=max(np.linalg.norm(n),1e-30);buf+=struct.pack('<12fH',*n,*t.ravel(),0)
 path.write_bytes(buf)


def signature(s):
 t=np.round(tri(s),4);rows=sorted(tuple(np.array(sorted(map(tuple,v))).ravel()) for v in t);return hashlib.sha256(np.array(rows).tobytes()).hexdigest()


def main(variant='fitted'):
 folder=BENCH/'print_batch';folder.mkdir(parents=True,exist_ok=True);unique=[];by_hash={};instances=[];inputs={str(Path(__file__)):sha(Path(__file__))}
 for char in ('quinn','manny'):
  pp,mm,st,f,pr,prov=build_full(char) if variant=='fitted' else build_connected(char,ASSEMBLY_POSE,variant)
  if f:raise RuntimeError(f)
  _,meta,_,_,_=build(char,ASSEMBLY_POSE,geometry=False);T,_=fk(pr,ASSEMBLY_POSE)
  for source in (OUT/f'carriers_equipped/{char}_parts.npz',OUT/f'carriers_equipped/{char}_routing.json'):inputs[str(source)]=sha(source)
  if variant=='fitted':
   for source in [Path(__file__).with_name('fitted.py'),OUT/f'harness/{char}_tails_final.json',OUT/f'harness/{char}_frame_reliefs.npz',OUT/f'harness/{char}_frame_reliefs.json']:inputs[str(source)]=sha(source)
   for source in (OUT/f'carriers_equipped/{char}_accessories.npz',OUT/f'carriers_equipped/{char}_accessories.json'):inputs[str(source)]=sha(source)
  for k,s in pp.items():
   if mm[k]['sku'] is not None:continue
   M=mm[k]['transform'] if variant=='fitted' else T[k.split('/',1)[1]] if k.startswith('frame/') else meta[k]['transform'];Q=M[:3,:3].copy()
   if np.linalg.det(Q)<0:Q=Q@np.diag([1,-1,1])
   local=pose(s,Q.T,-Q.T@M[:3,3]);h=signature(local);idx=by_hash.get(h)
   if idx is not None:
    other=unique[idx]['shape']
    if (local-other).volume()+(other-local).volume()>1e-3:raise RuntimeError('Hash grouping geometry mismatch')
   else:
    idx=len(unique);by_hash[h]=idx;unique.append({'id':f'P{idx+1:03}','shape':local,'instances':[]})
   inst={'character':char,'part':k,'body':mm[k]['body'],'print_id':unique[idx]['id']};unique[idx]['instances'].append(inst);instances.append(inst)
 fixtures=read(OUT/'fixtures.json')
 if fixtures['findings']:raise RuntimeError('Fixture collisions remain')
 inputs[str(OUT/'fixtures.npz')]=sha(OUT/'fixtures.npz');inputs[str(OUT/'fixtures.json')]=sha(OUT/'fixtures.json')
 for k,tt in np.load(OUT/'fixtures.npz').items():
  if fixtures['sku'][k] is not None:continue
  idx=len(unique);insts=[{'character':c,'part':'fixture/'+k,'body':'desktop','print_id':f'P{idx+1:03}'} for c in ('quinn','manny')];unique.append({'id':f'P{idx+1:03}','shape':from_tri_exact(tt),'instances':insts});instances.extend(insts)
 save('print_export_index.json',{'parts':[{'id':r['id'],'instances':r['instances']} for r in unique]})
 rows=[]
 for r in unique:
  v,bed=orient(r['shape']);pid=r['id'];dst=folder/(pid+'.stl');stl(dst,v);pack.write_3mf(folder/(pid+'.3mf'),{pid:v});assert bed['components']==1
  rows.append({'id':pid,'instances':r['instances'],'quantity_by_character':{c:sum(i['character']==c for i in r['instances']) for c in ('quinn','manny')},'stl':str(dst.relative_to(H)),'stl_sha256':sha(dst),'bed':bed});print('PRINT',pid,'count',len(r['instances']),'contact',round(bed['flat_contact_area_mm2'],2),'support',bed['supports_required'],flush=True)
 if any(sha(Path(k))!=v for k,v in inputs.items()):raise RuntimeError('Print source changed')
 report={'status':'ORIENTED_CANDIDATE_REQUIRES_SLICING','variant':variant,'units':'mm','rows':rows,'instances':instances,'input_sha256':inputs,'physical_tested':False,'one_character_only':'Choose Quinn OR Manny quantities; do not add them together.','no_machine_gcode':True}
 save('print_batch_manifest.json',report);(folder/'manifest.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
if __name__=='__main__':main(sys.argv[1] if len(sys.argv)>1 else 'fitted')
