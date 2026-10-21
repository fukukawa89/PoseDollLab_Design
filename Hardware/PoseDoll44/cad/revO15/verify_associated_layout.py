from associated_fit import *
from carriers_swept import motion_bank
only=sys.argv[1] if len(sys.argv)>1 else 'all'
subset=['waist','chest','head','clavicle_l.protract','clavicle_r.protract','clavicle_l.elevate','clavicle_r.elevate','upperarm_l','upperarm_r'] if only=='torso' else None
rows=[]
for char in ('quinn','manny'):
 for label,meta,T in motion_bank(char):
  # Obtain the exact named sample angles from the same motion-bank definition.
  cases={'assembly':ASSEMBLY_POSE,**read(H/'mechanical_manifest/revO_pose_cases.json')['cases']}
  for i,a in enumerate(read(OUT/'serial_clavicle_bilateral_search.json')['cases']):cases['bilateral_clavicle_'+str(i)]=a
  profile,_=config(char)
  for axis in profile['axes']:
   for i,v in enumerate(axis['limits_rad']):cases[axis['id']+'.'+str(i)]={axis['id']:float(np.rad2deg(v))}
  angles=cases[label]
  h=associated_hit(char,angles,only=subset);rows.append({'character':char,'pose':label,'first_structural_hit':h})
  if h:print('ASSOCIATED FAILURE',char,label,h,flush=True)
 print('ASSOCIATED DONE',char,'samples',sum(x['character']==char for x in rows),flush=True)
save('associated_'+only+'_verification.json',{'samples':rows,'failed':sum(x['first_structural_hit'] is not None for x in rows),'source_sha256':sha(Path(__file__).with_name('layout_fullbody.py')),'scope':'Original attachments with final body associations; connecting tubes excluded.'})
