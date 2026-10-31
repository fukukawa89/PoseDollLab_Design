from check_stock import saved
from build_stock import *
def run():
 a,ss=saved();records=[];parents={n['id']:n['parent'] for n in PROFILE['nodes']}
 def downstream(fr,root):
  while fr:
   if fr==root:return True
   fr=parents[fr]
  return False
 masses=[p['volume_mm3']*(.00124 if p['role']=='structure' else .00785)/1000 for p in a]
 for axis in PROFILE['axes']:
  max_t=0;worst=None
  for name,pose in POSES.items():
   ff=frames(pose['angles']);fr=ff[axis['id']];ax=fr[:3,:3]@np.array(axis['axis']);origin=fr[:3,3];moment=np.zeros(3)
   for p,m in zip(a,masses):
    if not downstream(p['frame'],axis['id']):continue
    c=(ff[p['frame']]@np.r_[p['mass_centroid_mm'],1])[:3];moment+=m*9.80665*np.cross(ax,(c-origin)/1000)
   upper=np.linalg.norm(moment)
   if upper>max_t:max_t=upper;worst=name
  target=max_t*1.25*1.5;is_h=axis['id'] in ['l_shoulder_abduct','l_elbow_flex','l_wrist_flex','l_wrist_deviation'];paths=4 if is_h else 2
  # Loose metal washers are serial torque interfaces: do not use only outer FW4 radius.
  radius=.0026;mu=.15;force=target/(paths*mu*radius)
  records.append(dict(axis=axis['id'],label=axis['label'],limits_deg=axis['limits_deg'],gravity_torque_envelope_Nm=float(max_t),worst_sample=worst,hold_target_Nm=float(target),mass_factor=1.25,holding_factor=1.5,serial_contact_radius_assumption_mm=2.6,mu_assumption=.15,friction_paths=paths,required_axial_force_per_stack_N=float(force),spring_force_measured=False,capacity_status='PENDING_MEASUREMENT',note='Two opposed paths for each R; two shoulder-bolt stacks, four paths for H/W. Loose washer interfaces included conservatively by 2.6 mm effective radius. Assumed dry friction is not a guaranteed material value. Holding torque is not screw tightening torque.'))
 put(OUT/'verification/holding_targets.json',dict(status='CALCULATED_TARGETS_NOT_MEASURED',geometry_sha256=sha(OUT/'production_meshes.npz'),rows=records,scope='30 relative poses; worst gravity direction at each sample, nominal mass plus 25%, holding factor1.5. No added hand payload. Actual A8 force curve, friction, FDM creep and cycle life remain unmeasured.'))
 print([(r['axis'],round(r['hold_target_Nm'],4),round(r['required_axial_force_per_stack_N'],1)) for r in records])
if __name__=='__main__':run()
