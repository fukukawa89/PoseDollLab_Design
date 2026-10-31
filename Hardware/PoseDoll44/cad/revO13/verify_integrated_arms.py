"""Audit the compact-wrist + integrated shoulder-carrier candidate together.
Keeps same-body hardware as obstacles in separate carrier verification.
"""
from check_full_motion import *
from refine_compact_wrists import transform_states
from build_compact_hinge import make as compact_make
from fullbody_stage import merged_profile

def main():
 carrier=json.loads((OUT/'carriers/endpoints.json').read_text());assert carrier['complete']
 if carrier['failed_endpoints']:
  save('integrated_arms.json',{'status':'BLOCKED_BY_CARRIER_COLLISIONS','carrier_failed_endpoints':carrier['failed_endpoints'],'full_body_manufacturing_released':False});return
 lib=library();_,_,_,packed=compact_make();lib.update({'compact_'+k:v for k,v in packed.items()})
 raw=np.load(OUT/'carriers/parts.npz');mount=json.loads((OUT/'compact_hinge/wrist_selected_endpoints.json').read_text())['mounts'];states=[]
 for char,side in itertools.product(('manny','quinn'),('l','r')):lib[f'{char}_{side}/bridge']=Parts([from_tri(raw[f'{char}_{side}_bridge'])])
 for char in ('manny','quinn'):
  source=json.loads((OUT/f'clavicle_trial/{char}_states.json').read_text())['states'];states+=transform_states(source,mount['flex_mount_deg'],mount['deviate_mount_deg'])
 for st in states:
  for side in ('l','r'):
   source=next(o for o in st['objects'] if o['id']==f'{side}/clav_output');st['objects'].append({**source,'id':f'{side}/integrated_bridge','library':f"{st['character']}_{side}/bridge"})
 bb={k:bounds(v) for k,v in lib.items()};rows=[]
 for st in states:
  rows.append({'character':st['character'],'pose':st['pose'],'findings':check(st,lib,bb,True)})
 # Back-space now includes new carrier solids, unlike the earlier empty-box test.
 boxes=[]
 for dz in (-8,-12,-16,-20,-24):
  low=np.array([-40,-24,dz],float);high=np.array([-28,24,48+dz],float);target=md.Manifold.cube(high-low+1).translate(low-.5);br=[]
  for st in states:
   p=merged_profile(st['character']);T,_=fk(p,st['requested_angles_deg']);F=T['chest'];s=pose(Parts([target]),F[:3,:3],F[:3,3]);tb=s.bounding_box();findings=[]
   for o in st['objects']:
    F=np.array(o['frame']);g=pose(lib[o['library']],F[:3,:3],F[:3,3]);gb=g.bounding_box()
    if np.any(np.minimum(tb[3:],gb[3:])<=np.maximum(tb[:3],gb[:3])):continue
    v=(s^g).volume()
    if v>1e-4:findings.append({'part':o['id'],'volume_mm3':v})
   br.append({'character':st['character'],'pose':st['pose'],'findings':findings})
  boxes.append({'shift_down_mm':-dz,'low_mm':low.tolist(),'high_mm':high.tolist(),'expanded_by_mm':.5,'cases':br,'failed_endpoints':sum(bool(r['findings']) for r in br)})
 clear=[b for b in boxes if not b['failed_endpoints']]
 save('integrated_arms.json',{'complete':True,'status':'ENDPOINT_LAYOUT_CANDIDATE','cases':rows,'failed_endpoints':sum(bool(r['findings']) for r in rows),'back_box_candidates':boxes,'selected_back_box':clear[0] if clear else None,'scope':'Actual printed bridge plus compact wrist with explicit sensor reservations. Same-body printed unions intended; carrier report separately checks screws/nuts/other shell half. Baseline path samples do not certify these new bridges. Missing complete torso/neck/legs/arm links, actual electronics/wiring, strength, tool handles and continuous proof.','full_body_manufacturing_released':False})
 save('integrated_arm_states.json',{'states':states})
 print('integrated endpoint failures',sum(bool(r['findings']) for r in rows),'back boxes',[(b['shift_down_mm'],b['failed_endpoints']) for b in boxes],flush=True)
if __name__=='__main__':main()
