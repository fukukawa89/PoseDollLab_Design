"""Restore shoulder reference width under the user's nonadjacent-contact policy.
O13 source and sealed outputs stay unchanged. Same mechanical stock parts;
printed clavicle-to-shoulder carriers are rebuilt for the restored anchors.
"""
from pathlib import Path
import sys,json,itertools,copy
import numpy as np
from audit_reference_and_collisions import H,G13,OUT,save,kind,sha
sys.path.insert(0,str(H/'cad/revO13'))
import clavicle_trial as ct
from parts_library import library,Parts
from solid_ops import from_tri,pose,tri
from check_full_motion import check,PAIR_CACHE
from build_compact_hinge import make as compact_make
from refine_compact_wrists import transform_states
from build_clavicle_carriers import make as make_carrier
original_profile=ct.profile

def width_restored(char,side):
 p=original_profile(char,side);n=next(n for n in p['nodes'] if n['id']==f'upperarm_{side}.flex_frame');n['parent_to_axis']['translation_m'][1]-=(8 if side=='l' else -8)/1000
 p['o13_shoulder_mount_offset_mm']=0;p['o13_shoulder_mount_note']='O14 candidate: restore neutral anatomical shoulder width; nonadjacent self-contact remains a pose warning';return p

def main():
 ct.profile=width_restored
 lib=library();_,_,_,packed=compact_make();lib.update({'compact_'+k:v for k,v in packed.items()});mount=json.loads((G13/'compact_hinge/wrist_selected_endpoints.json').read_text())['mounts'];states=[];contexts={}
 target=OUT/'selected_layout';target.mkdir(exist_ok=True)
 for ch in ('manny','quinn'):
  rows,ctx=ct.frames(ch,-60,38,10);contexts[ch]=ctx;states+=transform_states(rows,mount['flex_mount_deg'],mount['deviate_mount_deg'])
  base=json.loads((H/f'generated/revO3/runs/o3_20260924_r3/layouts/{ch}/anatomy_profile.json').read_text());nodes={}
  for side in ('l','r'):
   p=ctx[side][0];nodes.update({n['id']:n for n in p['nodes'] if n['id'].startswith(tuple(f'{x}_{side}' for x in ('clavicle','upperarm','elbow','forearm','hand','hand_tip')))})
  base['nodes']=[nodes.get(n['id'],n) for n in base['nodes']];base['profile_id']=f'o14_{ch}_shoulder_width_restored';base['status']='DESIGN_ONLY_NOT_DEVICE_CALIBRATION'
  d=target/'fullbody';d.mkdir(exist_ok=True);(d/f'{ch}_profile.json').write_text(json.dumps(base,indent=2)+'\n')
 rows=[];candidates=[]
 for h,skew in ((0,0),(0,-8),(8,0)):
  parts={};merged={}
  for ch,side in itertools.product(('manny','quinn'),('l','r')):
   st=next(s for s in states if s['character']==ch and s['pose']=='neutral');br,whole,rel=make_carrier(ch,side,st,h,skew);parts[ch,side]=br;merged[ch,side]=whole
   lib[f'{ch}_{side}/bridge_o14']=Parts([br])
   raw=np.load(G13/f'braked_module/{ch}_{side}.npz');lib[f'{ch}_{side}/P_except_plus']=Parts([from_tri(t) for k,t in raw.items() if k.startswith('P_') and k!='P_case_plus'])
  cases=[];carrier_cases=[];bb={k:ct.bounds(v) for k,v in lib.items()};PAIR_CACHE.clear();derived=copy.deepcopy(states)
  for st in derived:
   ch=st['character'];ob={o['id']:o for o in st['objects']};cfind=[]
   for side in ('l','r'):
    source=ob[f'{side}/clav_output'];st['objects'].append({**source,'id':f'{side}/integrated_bridge','library':f'{ch}_{side}/bridge_o14'})
    # Explicit co-body check keeps all hardware and the detachable shell half.
    A=np.array(source['frame']);B=np.array(ob[f'TUT_{side}/P']['frame']);br=pose(Parts([parts[ch,side]]),A[:3,:3],A[:3,3]);rest=pose(lib[f'{ch}_{side}/P_except_plus'],B[:3,:3],B[:3,3]);v=(br^rest).volume()
    if v>1e-4:cfind.append({'pair':[f'{side}/integrated_bridge',f'TUT_{side}/P_hardware'],'sum_piece_overlap_mm3':v,'classification':'STRUCTURAL_ADJACENT_OR_SAME_JOINT'})
   hits=[{**f,'classification':kind(*f['pair'])} for f in check(st,lib,bb,True)]+cfind
   cases.append({'character':ch,'pose':st['pose'],'findings':hits})
  hard=sum(any(f['classification']=='STRUCTURAL_ADJACENT_OR_SAME_JOINT' for f in r['findings']) for r in cases);soft=sum(any(f['classification']=='POSE_AVOIDABLE_NONADJACENT_CONTACT' for f in r['findings']) for r in cases)
  row={'rise_mm':h,'skew_mm':skew,'structural_failure_endpoints':hard,'pose_contact_endpoints':soft,'single_integrated_components':{ch+'_'+side:len(s.decompose()) for (ch,side),s in merged.items()},'cases':cases};candidates.append(row)
  save('shoulder_width_trials.json',{'complete':False,'candidates':candidates});print('restored shoulder candidate',h,skew,'structural',hard,'pose contact',soft,flush=True)
  if hard==0 and set(row['single_integrated_components'].values())=={1}:
   np.savez_compressed(target/'carriers.npz',**{ch+'_'+side+'_bridge':tri(s) for (ch,side),s in parts.items()},**{ch+'_'+side+'_integrated':tri(s) for (ch,side),s in merged.items()})
   (target/'integrated_arm_states.json').write_text(json.dumps({'states':derived},indent=2)+'\n')
   (target/'integrated_arms.json').write_text(json.dumps({'complete':True,'cases':cases,'selected_candidate':row|{'cases':None},'scope':'All unlike-body pairs at original 102 endpoints plus co-body carrier hardware. Adjacent/same-joint collisions are structural failures; nonadjacent contacts remain unsuitable simultaneous poses. New carrier paths, full body, PCBA/cables, strength and calibration are not certified.','manufacturing_released':False},indent=2)+'\n');break
 save('shoulder_width_trials.json',{'complete':True,'candidates':candidates,'selected':len(candidates)-1 if hard==0 else None,'old_O13_verified_geometry_modified':False,'shoulder_shift_per_side_mm':0,'physical_tested':False})
if __name__=='__main__':main()
