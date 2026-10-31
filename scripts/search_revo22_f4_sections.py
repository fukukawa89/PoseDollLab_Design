"""Exact section-based direction screen including bed-blocked local overhangs."""
from pathlib import Path
import sys,json,time,itertools,math,concurrent.futures,traceback
import numpy as np
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'scripts'))
from search_revo22_f2_orientations import frame
from build_revo22_fins import solid
B=R/'Hardware/PoseDoll44/bench/revO22';SRC=B/'O22F3_Release';O=B/'a1mini_fins_v4';DEST=O/'orientation_v2';DEST.mkdir(exist_ok=True)
VOLS={q['id']:q['volumes'] for q in json.loads((B/'a1mini_supports/design/all_protected_volumes.json').read_text(encoding='utf8'))['objects']}

def section_score(v,f,M,t):
 s=solid(v@M.T+t,f);h=s.bounding_box()[5];prev=s.slice(.1);projection=prev;blocksum=0.;blockmax=0.;allsum=0.;allmax=0.;layer_count=0;worst=None
 for z in np.arange(.3,h,.2):
  curr=s.slice(float(z));excess=curr-prev.offset(.2,circular_segments=12);a=float(excess.area())
  if a>.02:
   blocked=excess^projection;b=float(blocked.area());blocksum+=b;blockmax=max(blockmax,b);allsum+=a;allmax=max(allmax,a);layer_count+=1
   if worst is None or b>worst['blocked_mm2']:worst={'z_mm':round(float(z+.1),3),'blocked_mm2':b,'all_excess_mm2':a}
  projection=projection+curr;prev=curr
 return {'blocked_layer_excess_sum_mm2':blocksum,'max_blocked_layer_excess_mm2':blockmax,'all_layer_excess_sum_mm2':allsum,'max_all_layer_excess_mm2':allmax,'flagged_layers':layer_count,'worst':worst,'score':blockmax*300+blocksum*3+allmax*.5+allsum*.04+h*.03}

def one(pid):
 start=time.time()
 try:
  n=np.load(SRC/'reference/parts'/f'{pid}.npz');v=n['source_v'];f=n['f'];d0=json.loads((SRC/'reference/design'/f'{pid}.json').read_text(encoding='utf8'));old=np.array(d0['orientation']['gravity_in_source']);dirs=[old];leaf=None
  if pid.startswith('X') and 1<=int(pid[1:])<=34:
   leaf=np.array(VOLS[pid][0]['local_to_source_print_matrix'])[:3,1];leaf/=np.linalg.norm(leaf);basis=frame(leaf);dirs += [basis[0]*math.cos(a)+basis[1]*math.sin(a) for a in np.arange(0,2*math.pi,math.pi/12)]
  else:
   dirs += [np.array(p,float) for p in itertools.product([-1,0,1],repeat=3) if any(p)]
   for i in range(24):
    z=1-2*(i+.5)/24;t=math.pi*(3-math.sqrt(5))*i;r=math.sqrt(1-z*z);dirs.append(np.array([r*math.cos(t),r*math.sin(t),z]))
   rank=json.loads((B/'a1mini_fins_v2/orientation'/f'{pid}.json').read_text(encoding='utf8'))['ranked_candidates'];dirs += [np.array(q['gravity_in_source']) for q in rank[:4]]
  if pid=='X046':dirs += [np.array([-x,y,z]) for x in [.7,.85,1.] for y in [-.35,0,.35] for z in [-.6,.6]]
  seen=set();rows=[]
  for d in dirs:
   d=d/np.linalg.norm(d);key=tuple(np.round(d,5))
   if key in seen:continue
   seen.add(key)
   if leaf is not None and abs(d@leaf)>.02:continue
   Q=frame(d);best=None
   for a in range(0,90,15):
    c=math.cos(math.radians(a));s=math.sin(math.radians(a));M=np.array([[c,-s,0],[s,c,0],[0,0,1.]])@Q;vv=v@M.T;size=np.ptp(vv,axis=0);cost=size[0]*size[1]+max(0,max(size[:2])-164)**2*100000
    if best is None or cost<best[0]:best=(cost,M,-vv.min(0),size)
   _,M,t,size=best
   if max(size[:2])>166 or size[2]>174:continue
   metrics=section_score(v,f,M,t);rows.append({'orientation':{'matrix':M.tolist(),'source_translation_mm':t.tolist(),'gravity_in_source':d.tolist(),'size_mm':size.tolist()},'metrics':metrics,'score':metrics['score'],'is_F3_direction':bool(np.linalg.norm(d-old)<1e-5)})
  rows.sort(key=lambda r:r['score']);result={'id':pid,'part':d0['part'],'method':'Exact 0.20 mm body sections; unsupported local portions intersected with cumulative lower-body projection to retain bed-occluded risks. No supports included at screening. Scores rank candidates, never certify printability.','candidate_count':len(rows),'leaf_length_kept_in_layer_plane':leaf is not None,'source_body_changed':False,'best':rows[:8],'all_candidates':rows,'elapsed_s':time.time()-start};(DEST/f'{pid}.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf8');print('SECTION_ORIENT',pid,'maxblock',round(rows[0]['metrics']['max_blocked_layer_excess_mm2'],3),'sum',round(rows[0]['metrics']['blocked_layer_excess_sum_mm2'],2),'d',np.round(rows[0]['orientation']['gravity_in_source'],2),'s',round(time.time()-start,1),flush=True);return result
 except Exception:
  result={'id':pid,'error':traceback.format_exc()};print(result,flush=True);return result
if __name__=='__main__':
 b=json.loads((O/'audit/baseline/all_parts.json').read_text(encoding='utf8'));ids=sys.argv[1:] or sorted(q['id'] for q in b['parts'] if q['needs_support_coverage_review']);out=[]
 with concurrent.futures.ProcessPoolExecutor(max_workers=3) as pool:
  jobs={pool.submit(one,p):p for p in ids}
  for f in concurrent.futures.as_completed(jobs):out.append(f.result());(O/'orientation_v2_progress.json').write_text(json.dumps({'completed':len(out),'total':len(ids),'ids':[q['id'] for q in out]},indent=2),encoding='utf8')
 (O/'orientation_v2_results.json').write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding='utf8');assert not any('error' in r for r in out)
 print('SECTION_ORIENTATION_DONE',len(out),flush=True)
