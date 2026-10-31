"""Choose F4 directions by inaccessible overhang area, never by island count alone."""
from pathlib import Path
import sys,json,time,itertools,math,concurrent.futures,traceback
import numpy as np,trimesh
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'scripts'))
from search_revo22_f2_orientations import frame
from build_revo22_fins import solid
B=R/'Hardware/PoseDoll44/bench/revO22';SRC=B/'O22F3_Release';O=B/'a1mini_fins_v4';DEST=O/'orientation';DEST.mkdir(exist_ok=True)
VOLS={q['id']:q['volumes'] for q in json.loads((B/'a1mini_supports/design/all_protected_volumes.json').read_text(encoding='utf8'))['objects']}

def samples(v,f):
 tr=v[f];cr=np.cross(tr[:,1]-tr[:,0],tr[:,2]-tr[:,0]);area=np.linalg.norm(cr,axis=1)/2;norm=cr/np.maximum(2*area[:,None],1e-18);pts=[];ws=[];ns=[];faces=[]
 for i in np.flatnonzero(area>1e-7):
  count=max(1,int(np.ceil(np.sqrt(area[i]/10))))
  weight=area[i]/(count*(count+1)/2)
  for j in range(count):
   for k in range(count-j):
    u=(j+1/3)/count;w=(k+1/3)/count;pts.append(tr[i,0]*(1-u-w)+tr[i,1]*u+tr[i,2]*w);ws.append(weight);ns.append(norm[i]);faces.append(i)
 return np.asarray(pts),np.asarray(ws),np.asarray(ns),np.asarray(faces)

def evaluate(pid):
 start=time.time();n=np.load(SRC/'reference/parts'/f'{pid}.npz');v=n['source_v'];f=n['f'];d0=json.loads((SRC/'reference/design'/f'{pid}.json').read_text(encoding='utf8'));old=np.array(d0['orientation']['gravity_in_source']);pts,w,norm,fi=samples(v,f);tm=trimesh.Trimesh(v,f,process=False)
 dirs=[old]
 leaf=None
 if pid.startswith('X') and 1<=int(pid[1:])<=34:
  leaf=np.array(VOLS[pid][0]['local_to_source_print_matrix'])[:3,1];leaf/=np.linalg.norm(leaf);basis=frame(leaf)
  dirs += [basis[0]*math.cos(a)+basis[1]*math.sin(a) for a in np.arange(0,2*math.pi,math.pi/12)]
 else:
  dirs += [np.array(p,float) for p in itertools.product([-1,0,1],repeat=3) if any(p)]
  for i in range(32):
   z=1-2*(i+.5)/32;t=math.pi*(3-math.sqrt(5))*i;r=math.sqrt(1-z*z);dirs.append(np.array([r*math.cos(t),r*math.sin(t),z]))
  oldrank=json.loads((B/'a1mini_fins_v2/orientation'/f'{pid}.json').read_text(encoding='utf8'))['ranked_candidates'];dirs += [np.array(q['gravity_in_source']) for q in oldrank[:6]]
 if pid=='X046':dirs += [np.array([-x,y,z]) for x in [.7,.8,.9,1.] for y in [-.35,0,.35] for z in [-.6,.6]]
 seen=set();rows=[]
 for d in dirs:
  d=d/np.linalg.norm(d);key=tuple(np.round(d,5))
  if key in seen:continue
  seen.add(key)
  if leaf is not None and abs(d@leaf)>.02:continue
  Q=frame(d);vv=v@Q.T;best=None
  for a in range(0,90,15):
   c=math.cos(math.radians(a));s=math.sin(math.radians(a));Z=np.array([[c,-s,0],[s,c,0],[0,0,1.]]);M=Z@Q;uv=v@M.T;size=np.ptp(uv,axis=0);cost=size[0]*size[1]+max(0,max(size[:2])-164)**2*100000
   if best is None or cost<best[0]:best=(cost,M,-uv.min(0),size)
  _,M,t,size=best
  if max(size[:2])>166 or size[2]>174:continue
  z=pts@d+t[2];critical=(norm@d<-.7072)&(z>.3);cp=pts[critical];weights=w[critical];nz=norm[critical]@d;heights=z[critical]
  blocked=np.zeros(len(cp),bool)
  if len(cp):
   hit,ri,_=tm.ray.intersects_location(cp-.04*d,np.tile(-d,(len(cp),1)),multiple_hits=False);blocked[ri]=True
  block=float(weights[blocked].sum());visible=float(weights[~blocked].sum());tall=float((weights[~blocked]*np.maximum(heights[~blocked]-45,0)).sum())
  group={}
  for no,ww in zip(np.round(norm[critical][blocked],3),weights[blocked]):group[tuple(no)]=group.get(tuple(no),0)+ww
  largest=max(group.values(),default=0)
  score=block*100+largest*80+visible*.6+tall*.1+size[2]*.5
  row={'orientation':{'matrix':M.tolist(),'source_translation_mm':t.tolist(),'gravity_in_source':d.tolist(),'size_mm':size.tolist()},'blocked_critical_area_mm2':block,'largest_blocked_normal_group_mm2':largest,'bed_accessible_critical_area_mm2':visible,'tall_accessible_cost_mm3':tall,'score':score,'is_F3_direction':bool(np.linalg.norm(d-old)<1e-5)}
  if leaf is not None:row['leaf_vertical_component']=float(d@leaf)
  rows.append(row)
 rows.sort(key=lambda q:q['score']);result={'id':pid,'part':d0['part'],'candidate_count':len(rows),'best':rows[:8],'all_candidates':rows,'leaf_direction_constrained':leaf is not None,'source_body_changed':False,'elapsed_s':time.time()-start}
 (DEST/f'{pid}.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf8');b=rows[0];print('ORIENT',pid,'blocked',round(b['blocked_critical_area_mm2'],2),'h',round(b['orientation']['size_mm'][2],1),'d',np.round(b['orientation']['gravity_in_source'],2),'s',round(time.time()-start,1),flush=True);return result

def one(pid):
 try:return evaluate(pid)
 except Exception:return {'id':pid,'error':traceback.format_exc()}
if __name__=='__main__':
 baseline=json.loads((O/'audit/baseline/all_parts.json').read_text(encoding='utf8'));ids=sorted(q['id'] for q in baseline['parts'] if q['needs_support_coverage_review'])
 if len(sys.argv)>1:ids=sys.argv[1:]
 out=[]
 with concurrent.futures.ProcessPoolExecutor(max_workers=3) as pool:
  for r in pool.map(one,ids):out.append(r)
 (O/'orientation_search.json').write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding='utf8');assert not any('error' in r for r in out),[r for r in out if 'error' in r]
 print('ORIENTATION_DONE',len(out),flush=True)
