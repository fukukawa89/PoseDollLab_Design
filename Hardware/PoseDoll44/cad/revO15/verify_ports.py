from common import *
from layout_fullbody import libraries
import tut,three_axis
rows=[]
for kind in ('wide_tut','tut','three_axis'):
 p,o,_=libraries()[kind];limits=120 if kind=='wide_tut' else 95;cases=list(itertools.product((-170,0,170),(-25,0,25),(-limits,0),(-170,0,170))) if kind!='three_axis' else [(*q,0) for q in itertools.product((-90,0,90),(-45,0,45),(-90,0))]
 for base in (-30.5,-30.9,-31.1):
  fails=[]
  for q in cases:
   fs=tut.frames(q) if kind!='three_axis' else three_axis.frames(q[:3]);placed={k:pose(s,fs[o[k]]) for k,s in p.items()}
   for end,sg,e in [('P',-1,7.5 if kind in ('wide_tut','three_axis') else 1.5)]+([] if kind=='three_axis' else [('D',1,7)]):
    a=np.array([0,sg*11.4,sg*(-base+e)]);b=a+[0,sg*8,0];shape=md.Manifold.batch_hull([md.Manifold.sphere(2.85,24).translate(a),md.Manifold.sphere(5.25,24).translate(b)]);shape=pose(shape,fs[end]);bb=np.array(shape.bounding_box())
    for k,v in placed.items():
     if k==end+'_case_minus':continue
     vb=np.array(v.bounding_box())
     if np.any(np.minimum(bb[3:],vb[3:])<=np.maximum(bb[:3],vb[:3])):continue
     vol=(v^shape).volume()
     if vol>1e-4:fails.append({'q':list(q),'end':end,'part':k,'overlap_mm3':float(vol)})
  rows.append({'kind':kind,'base_z':base,'cases':len(cases),'findings':fails});save('structural_port_validation.json',{'trials':rows,'scope':'Root tapered connection only; long-body carrier motion remains separate'});print('PORT',kind,base,'failures',len(fails),fails[:2],flush=True)
