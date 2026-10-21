from pathlib import Path
import sys,json,numpy as np,concurrent.futures,time
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'scripts'))
from search_revo22_f4_fine_orientations import metric
O=R/'Hardware/PoseDoll44/bench/revO22/a1mini_fins_v4';F=O.parent/'O22F3_Release/reference'
def rank(spec):
 pid,parent=spec.split(':');d=json.loads((O/'candidates'/pid/parent/'design'/f'{pid}.json').read_text());n=np.load(F/'parts'/f'{pid}.npz');v=n['source_v'];f=n['f'];M0=np.array(d['orientation']['matrix']);out=[];st=time.time()
 for ax in [-6.,-3.,0.,3.,6.]:
  for ay in [-6.,-3.,0.,3.,6.]:
   if ax==ay==0:continue
   x,y=np.deg2rad([ax,ay]);Rx=np.array([[1,0,0],[0,np.cos(x),-np.sin(x)],[0,np.sin(x),np.cos(x)]]);Ry=np.array([[np.cos(y),0,np.sin(y)],[0,1,0],[-np.sin(y),0,np.cos(y)]]);M=Rx@Ry@M0;vv=v@M.T;t=-vv.min(0);m=metric(v,f,M,t);out.append({'orientation':{'matrix':M.tolist(),'source_translation_mm':t.tolist(),'gravity_in_source':M[2].tolist(),'size_mm':np.ptp(vv,axis=0).tolist()},'metrics':m,'score':m['score'],'angles_deg':[ax,ay]})
 out.sort(key=lambda q:q['score']);p=O/'orientation_local110';p.mkdir(exist_ok=True);(p/f'{pid}.json').write_text(json.dumps({'id':pid,'parent':parent,'all_candidates':out,'best':out[:4]},indent=2));print('LOCAL110_RANK',pid,round(time.time()-st,1),[(q['angles_deg'],q['metrics']['blocked_start_count'],round(q['score'],1))for q in out[:5]],flush=True)
if __name__=='__main__':
 with concurrent.futures.ProcessPoolExecutor(max_workers=2)as p:
  for f in concurrent.futures.as_completed([p.submit(rank,s)for s in sys.argv[1:]]):f.result()
