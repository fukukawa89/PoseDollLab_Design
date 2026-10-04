"""Orient the compact candidate at wrists only; retain legacy elbow/forearm.
No target angles or joint origins changed. Reversal requires future sensor sign
calibration, not an automatic UE profile update.
"""
from build_compact_hinge import make
from check_full_motion import *
def transform_states(states,flex,deviate):
 out=copy.deepcopy(states)
 for st in out:
  for o in st['objects']:
   if o['id'].startswith(('hand_l.','hand_r.')):
    owner=o['library'].split('_')[1];o['library']='compact_'+owner
    a,b=flex if '.flex/' in o['id'] else deviate
    F=np.array(o['frame']);F[:3,:3]=F[:3,:3]@rot(0,a)@rot(2,b);o['frame']=F.tolist()
 return out
def main():
 raw,res,bare,packed=make();lib=library();lib.update({'compact_'+k:v for k,v in packed.items()});bb={k:bounds(s) for k,s in lib.items()}
 c=json.loads((OUT/'clavicle_trial/motion.json').read_text())['candidate']
 states=sum([frames(ch,c['x_mm'],c['lateral_mm'],c['z_shift_mm'])[0] for ch in ('manny','quinn')],[])
 risk={'neutral','upperarm_l.abduct_-20','upperarm_l.twist_-90','forearm_l.twist_-90','arms_crossed','arms_crossed_asymmetric_candidate','hand_l.flex_-60','elbow_l.flex_140'}
 rows=[]
 for flex,deviate in itertools.product(((0,0),(180,0),(0,180),(180,180)),repeat=2):
  findings=[]
  for st in transform_states([s for s in states if s['pose'] in risk],flex,deviate):
   hits=check(st,lib,bb,True)
   if hits:findings.append({'character':st['character'],'pose':st['pose'],'findings':hits})
  row={'flex_mount_deg':flex,'deviate_mount_deg':deviate,'failed_endpoints':len(findings),'sum_overlap_mm3':sum(h['sum_piece_overlap_mm3'] for r in findings for h in r['findings']),'findings':findings};rows.append(row)
  save('compact_hinge/wrist_mount_search.json',{'complete':False,'candidates':rows})
 rows.sort(key=lambda r:(r['failed_endpoints'],r['sum_overlap_mm3']));best=rows[0]
 save('compact_hinge/wrist_mount_search.json',{'complete':True,'candidates':rows,'scope':'Risk-pose search only; final all-102 audit required'})
 full=[]
 for st in transform_states(states,best['flex_mount_deg'],best['deviate_mount_deg']):
  full.append({'character':st['character'],'pose':st['pose'],'findings':check(st,lib,bb,True)})
 save('compact_hinge/wrist_selected_endpoints.json',{'complete':True,'mounts':{k:best[k] for k in ('flex_mount_deg','deviate_mount_deg')},'cases':full,'failed_endpoints':sum(bool(r['findings']) for r in full),'scope':'Compact wrist mechanical geometry plus sensor/holder reservation. No physical linkage, PCB attachment, cable, field, calibration or strength qualification.'})
 print('selected',best['flex_mount_deg'],best['deviate_mount_deg'],'failures',sum(bool(r['findings']) for r in full),flush=True)
if __name__=='__main__':main()
