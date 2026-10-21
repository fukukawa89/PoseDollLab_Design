from pathlib import Path
import sys,json,time,numpy as np,concurrent.futures
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'scripts'))
from build_revo22_fins import solid,union
O=R/'Hardware/PoseDoll44/bench/revO22/a1mini_fins_v4'
def check(pid,label):
 p=O/'candidates'/pid/label;n=np.load(p/'parts'/f'{pid}.npz');s=union([solid(n[v],n[f]) for v,f in [('v','f'),('fin_v','fin_f'),('teeth_v','teeth_f')] if len(n[f])]);h=s.bounding_box()[5];rows=[];prev=None;st=time.time()
 for z in np.arange(.1,h,.2):
  cs=s.slice(float(z)).offset(-.16,circular_segments=12).offset(.16,circular_segments=12)
  if prev is not None:
   back=prev.offset(.02,circular_segments=12)
   for c in cs.decompose():
    if c.area()>.05 and (c^back).area()<.001:rows.append({'z_mm':float(z+.1),'area_mm2':float(c.area()),'bounds_mm':list(c.bounds())})
  prev=cs
 d={'id':pid,'label':label,'count':len(rows),'total_area_mm2':sum(q['area_mm2'] for q in rows),'max_area_mm2':max([q['area_mm2'] for q in rows],default=0),'rows':rows,'method':'Geometry-only 0.16 mm radius opening approximates printable thin-feature limits. Orientation ranking only, not native pass.','elapsed_s':time.time()-st};(p/'verification/morphological_starts.json').write_text(json.dumps(d,indent=2));print('MORPH_STARTS',pid,label,len(rows),round(d['total_area_mm2'],2),'s',round(time.time()-st,1),flush=True);return d
if __name__=='__main__':
 specs=[(pid,'cov_'+str(k).zfill(2)) for pid in sys.argv[1:] for k in range(4) if (O/'candidates'/pid/('cov_'+str(k).zfill(2))/'parts'/f'{pid}.npz').exists()]
 with concurrent.futures.ProcessPoolExecutor(max_workers=3) as pool:
  for f in concurrent.futures.as_completed([pool.submit(check,*spec) for spec in specs]):f.result()
