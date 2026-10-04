"""Separate unilateral joint range from bilateral pose self-collision.
Original failures remain in their own reports; these are additional cases.
"""
from refine_compact_wrists import *

def side_of(o):
 s=o['id']
 return 'l' if s.startswith(('l/','TUT_l/')) or '_l.' in s else 'r'

def main():
 _,_,_,packed=make();lib=library();lib.update({'compact_'+k:v for k,v in packed.items()});bb={k:bounds(s) for k,s in lib.items()}
 selected=json.loads((OUT/'compact_hinge/wrist_selected_endpoints.json').read_text())['mounts']
 c=json.loads((OUT/'clavicle_trial/motion.json').read_text())['candidate'];rows=[];outputs=[];diagnoses=[]
 for char in ('manny','quinn'):
  originals=frames(char,c['x_mm'],c['lateral_mm'],c['z_shift_mm'])[0]
  states=transform_states(originals,selected['flex_mount_deg'],selected['deviate_mount_deg']);neutral=next(s for s in states if s['pose']=='neutral')
  for st in states:
   q=st['requested_angles_deg']
   left={k:v for k,v in q.items() if k.split('.')[0].endswith('_l')}
   right={k:v for k,v in q.items() if k.split('.')[0].endswith('_r')}
   if len(left)!=1 or len(right)!=1 or len(q)!=2:continue
   for side in ('l','r'):
    trial={'character':char,'pose':st['pose']+'_only_'+side,'requested_angles_deg':left if side=='l' else right,
       'objects':[copy.deepcopy(o) for o in st['objects'] if side_of(o)==side]+[copy.deepcopy(o) for o in neutral['objects'] if side_of(o)!=side]}
    hits=check(trial,lib,bb,True);rows.append({'character':char,'pose':trial['pose'],'source_pose':st['pose'],'angles_deg':trial['requested_angles_deg'],'findings':hits});outputs.append(trial)
   if st['pose']=='upperarm_l.abduct_-20':
    ob={o['id']:np.array(o['frame']) for o in st['objects']}
    diagnoses.append({'character':char,'original_pose':st['pose'],'bilateral_angles_deg':q,'wrist_deviation_axis_origins_distance_mm':float(np.linalg.norm(ob['hand_l.deviate/parent'][:3,3]-ob['hand_r.deviate/parent'][:3,3])),
      'interpretation':'The original test simultaneously brings both wrists into the same area. It remains a failed combined pose, not automatically a loss of unilateral shoulder angular range.'})
 save('compact_hinge/unilateral_endpoints.json',{'complete':True,'scope':'Additional unilateral endpoint checks using unchanged stock axes, neutral opposite arm, compact wrist with explicit sensor reservations. Original bilateral failed cases retained; no torso/carriers/cables/path acceptance.','cases':rows,'failed_endpoints':sum(bool(r['findings']) for r in rows),'original_pose_diagnoses':diagnoses})
 save('compact_hinge/unilateral_states.json',{'states':outputs})
 print('unilateral',len(rows),'failed',sum(bool(r['findings']) for r in rows),flush=True)
if __name__=='__main__':main()
