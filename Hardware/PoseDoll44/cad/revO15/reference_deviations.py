from layout_fullbody import *
rows=[]
for char in ('quinn','manny'):
 ref=read(G3/f'layouts/{char}/anatomy_profile.json');rr=[];poses=read(H/'mechanical_manifest/revO_pose_cases.json')['cases']
 for name,angles in poses.items():
  _,_,st,f,pr=build(char,angles,geometry=False);T,A=fk(pr,angles);RT,RA=fk(ref,angles)
  points={k:{'reference_mm':RT[k][:3,3].tolist(),'candidate_mm':T[k][:3,3].tolist(),'error_mm':float(np.linalg.norm(T[k][:3,3]-RT[k][:3,3]))} for k in ('head_tip','hand_tip_l','hand_tip_r','toe_tip_l','toe_tip_r')}
  axes={k:{'error_mm':float(np.linalg.norm(A[k]['origin']-RA[k]['origin'])),'delta_mm':(A[k]['origin']-RA[k]['origin']).tolist()} for k in A}
  rr.append({'pose':name,'angles_deg':angles,'endpoints':points,'axes':axes,'mapping_failures':f})
 row={'character':char,'poses':rr,'maximum_endpoint_error_mm':max(v['error_mm'] for r in rr for v in r['endpoints'].values()),'maximum_axis_origin_error_mm':max(v['error_mm'] for r in rr for v in r['axes'].values())};rows.append(row)
 print(char,'max endpoint',row['maximum_endpoint_error_mm'],'max axis',row['maximum_axis_origin_error_mm'],flush=True)
 for r in rr:
  print(r['pose'],[(k,round(v['error_mm'],1)) for k,v in r['endpoints'].items()],flush=True)
save('reference_deviations.json',{'status':'MEASURED_DIGITAL_DEVIATIONS_NO_ACCEPTANCE_THRESHOLD','numeric_tolerance_user_approved':False,'characters':rows,'source_sha256':sha(Path(__file__).with_name('layout_fullbody.py')),'notes':['Current rear spine and clavicle placement are substantial candidate deviations, not an exact anatomical replica.','Rotation composition is distinct from physical endpoint agreement.','Lying case empty angles do not model contact or root placement.']})
