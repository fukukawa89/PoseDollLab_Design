"""Rank fine rotations with printable cross-section starts; native slicing remains required."""
from pathlib import Path
import sys,json,numpy as np,math,time,concurrent.futures
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'scripts'))
from build_revo22_fins import solid
from search_revo22_f2_orientations import frame
B=R/'Hardware/PoseDoll44/bench/revO22';O=B/'a1mini_fins_v4'
def metric(v,f,M,t):
 s=solid(v@M.T+t,f);h=s.bounding_box()[5];prev=s.slice(.1);prevopen=prev.offset(-.16,circular_segments=8).offset(.16,circular_segments=8);shadow=prev;blocksum=0;blockmax=0;floating=[]
 for z in np.arange(.3,h,.2):
  cur=s.slice(float(z));opened=cur.offset(-.16,circular_segments=8).offset(.16,circular_segments=8);block=(opened-prevopen.offset(.15,circular_segments=8))^shadow;area=float(block.area());blocksum+=area;blockmax=max(blockmax,area)
  for c in opened.decompose():
   if c.area()>.05 and (c^prevopen.offset(.025,circular_segments=8)).area()<.001:
    oc=float((c^shadow).area());floating.append({'z_mm':float(z),'area_mm2':float(c.area()),'bed_occluded_area_mm2':oc})
  shadow=shadow+cur;prevopen=opened
 blocked=[q for q in floating if q['bed_occluded_area_mm2']>.025]
 score=50*len(blocked)+30*sum(q['bed_occluded_area_mm2'] for q in blocked)+blockmax*80+blocksum*.7+len(floating)*.5+h*.025
 return {'score':score,'blocked_start_count':len(blocked),'start_count':len(floating),'blocked_max_mm2':blockmax,'blocked_sum_mm2':blocksum,'starts':floating}
def one(pid):
 st=time.time();n=np.load(B/'O22F3_Release/reference/parts'/f'{pid}.npz');v=n['source_v'];f=n['f'];orig=json.loads((O/'orientation_v2'/f'{pid}.json').read_text());dirs=[np.array(q['orientation']['gravity_in_source']) for q in orig['all_candidates']];best=orig['best'][:4]
 for q in best:
  d=np.array(q['orientation']['gravity_in_source']);F=frame(d)
  for x in [-.2,-.1,0,.1,.2]:
   for y in [-.2,-.1,0,.1,.2]:dirs.append(d+x*F[0]+y*F[1])
 seen=set();out=[]
 for i,d in enumerate(dirs):
  d=d/np.linalg.norm(d);key=tuple(np.round(d,4))
  if key in seen:continue
  seen.add(key);M=frame(d);vv=v@M.T;t=-vv.min(0);size=np.ptp(vv,axis=0)
  if max(size[:2])>164 or size[2]>174:continue
  m=metric(v,f,M,t);out.append({'orientation':{'matrix':M.tolist(),'source_translation_mm':t.tolist(),'gravity_in_source':d.tolist(),'size_mm':size.tolist()},'metrics':m,'score':m['score']})
  if len(out)%25==0:print('FINE_RANK_PROGRESS',pid,len(out),'best',round(min(q['score'] for q in out),2),flush=True)
 out.sort(key=lambda q:q['score']);dest=O/'orientation_fine';dest.mkdir(exist_ok=True);(dest/f'{pid}.json').write_text(json.dumps({'id':pid,'candidate_count':len(out),'best':out[:8],'all_candidates':out,'elapsed_s':time.time()-st},indent=2));print('FINE_RANK_DONE',pid,len(out),[(q['metrics']['blocked_start_count'],round(q['score'],2)) for q in out[:4]],flush=True)
 return pid
if __name__=='__main__':
 with concurrent.futures.ProcessPoolExecutor(max_workers=2) as pool:
  for q in pool.map(one,sys.argv[1:]):pass
