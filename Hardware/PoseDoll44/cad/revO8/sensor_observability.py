"""Ideal-dipole observability experiment. No actual sensor calibration or firmware.
The sensor is centered on the output-yoke Z axis, the magnet axis on input-yoke Z.
"""
import json,numpy as np
from reference_assembly import OUT,rot

def ideal_field(alpha,beta,magnet_on_ring=False):
 A=rot([1,0,0],alpha);R=A@rot([0,1,0],beta);mag=A@np.array([0.,0.,1.]) if magnet_on_ring else np.array([0.,0.,1.]);r=R@np.array([0.,0.,1.]);B=3*r*np.dot(mag,r)-mag
 return R.T@B

def inverse_field(B):
 m=np.array([-B[0],-B[1],B[2]/2]);length=np.linalg.norm(m)
 if not np.isfinite(m).all() or length<1e-9:raise ValueError('INVALID_FIELD')
 m/=length;cos_a=np.hypot(m[0],m[2])
 if cos_a<.5-1e-9:raise ValueError('OUTSIDE_ASSUMED_ALPHA_60_DOMAIN')
 return np.rad2deg([np.arctan2(m[1],cos_a),np.arctan2(-m[0],m[2])])

def folded_angles(B):
 # Representative on-chip joystick form from the datasheet: both formulas
 # square the third component. Constants set to one to isolate sign loss.
 x,y,z=B;return np.rad2deg([np.arctan2(np.hypot(y,z),x),np.arctan2(np.hypot(x,z),y)])

def main():
 errors=[]
 for a in range(-60,61,15):
  for b in range(-100,101,10):
   recovered=inverse_field(ideal_field(a,b));errors.append(float(np.max(np.abs(recovered-[a,b]))))
 assert max(errors)<1e-10
 pairs=[]
 for name,p,q,kind in [('joystick_fold_85_95',(0,85),(0,95),'folded'),('ring_magnet_loses_alpha',(0,25),(40,25),'ring'),('alpha90_loses_beta',(90,0),(90,60),'raw'),('out_of_domain_alias',(100,0),(80,180),'raw')]:
  a=ideal_field(*p,magnet_on_ring=kind=='ring');b=ideal_field(*q,magnet_on_ring=kind=='ring');u,v=(folded_angles(a),folded_angles(b)) if kind=='folded' else (a,b);error=float(np.linalg.norm(u-v));assert error<1e-12; pairs.append({'name':name,'pose_a_deg':p,'pose_b_deg':q,'observed_a':u.tolist(),'observed_b':v.tolist(),'difference_norm':error})
 rejected=0
 for v in ([0,0,0],[float('nan'),0,1]):
  try:inverse_field(v)
  except ValueError:rejected+=1
 assert rejected==2
 result={'status':'IDEAL_MODEL_EXPERIMENT_ONLY','roundtrip_cases':len(errors),'matrix_derived_field_roundtrip_max_error_deg':max(errors),'ambiguity_counterexamples':pairs,'invalid_field_cases_rejected':rejected,'decision':'Preserve raw signed X/Y/Z for a central 2-axis sensor trial; do not reuse legacy folded joystick-angle outputs as joint angles across 90 degrees. Magnet must span both bend joints. Physical alpha stops / verified workspace and calibrated sensor model are required; software cannot distinguish every out-of-domain alias.','prerequisites':['Finite magnet size and gap/off-axis calibration','IMC Z sensitivity correction and board orientation','CRC/marker/diagnostic/rolling-counter/fresh acquisition validation','Actual magnetic interference and repeatability measurements'],'source_url':'https://media.melexis.com/-/media/files/documents/datasheets/mlx90363-datasheet-melexis.pdf','datasheet_sections':['13.4.1','16.2','18.2'],'scope':'Dimensionless point-dipole model, perfect centering and corrected vector gains; no achieved physical angular accuracy. No production driver or UE capture contract changed.','physical_tested':False}
 (OUT.parent/'sensor_observability.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8');print('Roundtrips',len(errors),'counterexamples',len(pairs),'invalid',rejected)
if __name__=='__main__':main()
