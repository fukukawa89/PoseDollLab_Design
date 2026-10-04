"""Audit complete pose coverage, interpolation error and finite rotation budgets."""
import json,numpy as np
from common import *
from allocate_paths import inputs,compose

def angular_error(A,B):return float(np.rad2deg(np.arccos(np.clip((np.trace(A.T@B)-1)/2,-1,1))))

def main():
 path=OUT/'bounded_mapping.json';d=json.loads(path.read_text());old=json.loads((G8/'shoulder_mapping.json').read_text());rows=[];total_samples=0;total_segments=0;all_max=0.
 for (g,source_paths),new in zip(inputs(),d['characters']):
  side=g['side'];limits=np.array([[-170,50],[-30,30],[-100,100],[-95,105]]) if side=='l' else np.array([[-55,170],[-30,30],[-100,100],[-95,105]])
  paths=[];calibration=None
  for (src,mats),p in zip(source_paths,new['paths']):
   assert src['pose']==p['pose'] and src['angles_deg']==p['requested_angles_deg'];assert p['status']=='DISCRETE_ROTATION_PATH_FOUND'
   q=np.array(p['angles_deg']);offset=np.array(p['zero_offsets_deg']);assert len(q)==len(mats)
   if calibration is None:calibration=(q[0],offset)
   assert np.allclose(q[0],calibration[0],atol=1e-9) and np.allclose(offset,calibration[1],atol=1e-9)
   assert np.all(q>=limits[:,0]-1e-8) and np.all(q<=limits[:,1]+1e-8)
   # Real mechanism interpolation of q stays in the convex checked core box.
   # Compare with smooth orientation interpolation between the same requested
   # sampled rotations; this is NOT an exact unsampled human FK path certificate.
   # Use the midpoint polar factor of A+B as an independent rotation midpoint.
   errors=[]
   for i in range(len(q)-1):
    u,_,vh=np.linalg.svd(mats[i]+mats[i+1]);middle=u@vh
    if np.linalg.det(middle)<0:u[:,-1]*=-1;middle=u@vh
    errors.append(angular_error(compose((q[i]+q[i+1])/2+offset),middle))
   error=max(errors,default=0.);all_max=max(all_max,error);total_samples+=len(q);total_segments+=len(q)-1
   paths.append({'pose':p['pose'],'samples':len(q),'max_midpoint_rotation_deviation_deg':error,'return_along_reverse_path_net_joint_rotation_deg':[0,0,0,0]})
  a=np.array([q for p in new['paths'] for q in p['angles_deg']]);ranges=np.c_[a.min(0),a.max(0)];margins=np.minimum(ranges[:,0]-limits[:,0],limits[:,1]-ranges[:,1]);r={'character':g['character'],'side':side,'retained_targets':len(paths),'paths':paths,'ranges_deg':ranges.tolist(),'suggested_nominal_stop_intervals_deg':limits.tolist(),'minimum_angle_headroom_deg':margins.tolist(),'mechanical_stops_modeled':False,'proximal_span_deg':float(np.ptp(a[:,0])),'old_proximal_span_deg':float(np.ptp(np.array(g['angle_ranges_deg'])[0])),'wire_evidence':'Finite angle budget only. No routed, restrained or torsion-qualified cable, no arbitrary direct pose-to-pose path qualification.'};rows.append(r)
 save('path_audit.json',{'status':'SCOPED_DIGITAL_PATH_AUDIT','characters':rows,'total_retained_targets':sum(g['retained_targets'] for g in rows),'sampled_rotations':total_samples,'continuous_angle_linear_segments':total_segments,'max_midpoint_rotation_deviation_deg':all_max,'scope':'All original O7 target and sampled rotations retained. Actual four-joint linear interpolation is continuous and stays in the checked bend rectangle. Its intermediate orientation can deviate from the old rotation path by the reported amount. This is a candidate path network through a common neutral, not proof of arbitrary natural manipulation or full arm collision freedom.','physical_tested':False,'manufacturing_released':False,'input_sha256':{'bounded_mapping':sha(path),'old_mapping':sha(G8/'shoulder_mapping.json')}})
 print(total_samples,total_segments,'midpoint deviation',all_max,flush=True)
if __name__=='__main__':main()
