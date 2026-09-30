"""O14: quantify reference changes and classify O13 collision witnesses.
No source geometry/angle/pose deleted or silently fixed by reclassification.
"""
from pathlib import Path
import json,sys,hashlib,itertools
import numpy as np
H=Path(__file__).resolve().parents[2];G13=H/'generated/revO13/runs/o13_20260929_r1';OUT=H/'generated/revO14/runs/o14_20260929_r1'
sys.path.insert(0,str(H/'cad'));from model import fk

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def save(name,r):(OUT/name).write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def region(name):
 if name.startswith(('l/clav_','r/clav_')):return ['clavicle_'+name[0]]
 if name in ('l/integrated_bridge','r/integrated_bridge'):return ['clavicle_'+name[0],'shoulder_'+name[0]]
 if name.startswith('TUT_'):return ['shoulder_'+name[4]]
 s=name.split('/')[0]
 if s.startswith('elbow_'):return ['elbow_'+s[6]]
 if s.startswith('forearm_'):return ['forearm_'+s[8]]
 if s.startswith('hand_'):return ['wrist_flex_'+s[5] if '.flex' in s else 'wrist_deviate_'+s[5]]
 raise ValueError('Unknown mechanical region '+name)
ADJ=set()
for side in ('l','r'):
 chain=[f'{x}_{side}' for x in ('clavicle','shoulder','elbow','forearm','wrist_flex','wrist_deviate')]
 ADJ.update(frozenset((a,b)) for a,b in zip(chain,chain[1:]))
def kind(a,b):
 aa,bb=region(a),region(b)
 return 'STRUCTURAL_ADJACENT_OR_SAME_JOINT' if any(x==y or frozenset((x,y)) in ADJ for x,y in itertools.product(aa,bb)) else 'POSE_AVOIDABLE_NONADJACENT_CONTACT'

def main():
 import argparse
 parser=argparse.ArgumentParser();parser.add_argument('--revision',choices=('o13','o14'),default='o14');args=parser.parse_args()
 current=G13 if args.revision=='o13' else OUT/'selected_layout';suffix='_o13' if args.revision=='o13' else ''
 profiles=[];inputs={};motion=read(current/'integrated_arm_states.json')
 for ch in ('manny','quinn'):
  bp=H/f'generated/revO3/runs/o3_20260924_r3/layouts/{ch}/anatomy_profile.json';cp=current/f'fullbody/{ch}_profile.json';base,cur=read(bp),read(cp);T,A=fk(base,{});U,B=fk(cur,{})
  for p in (bp,cp):inputs[p.relative_to(H).as_posix()]=sha(p)
  axes=[{'axis':a,'reference_origin_mm':A[a]['origin'].tolist(),'current_origin_mm':B[a]['origin'].tolist(),'delta_mm':(B[a]['origin']-A[a]['origin']).tolist(),'distance_mm':float(np.linalg.norm(B[a]['origin']-A[a]['origin']))} for a in A]
  lengths=[]
  for side in ('l','r'):
   for label,a,b in [('upperarm',f'upperarm_{side}',f'elbow_{side}'),('forearm',f'elbow_{side}',f'hand_{side}.flex_frame'),('wrist_to_hand_tip',f'hand_{side}.flex_frame',f'hand_tip_{side}')]:
    l=float(np.linalg.norm(T[a][:3,3]-T[b][:3,3]));m=float(np.linalg.norm(U[a][:3,3]-U[b][:3,3]));lengths.append({'segment':label+'_'+side,'reference_mm':l,'current_mm':m,'delta_mm':m-l})
  poses=[]
  for s in [s for s in motion['states'] if s['character']==ch]:
   X,_=fk(base,s['requested_angles_deg']);Y,_=fk(cur,s['requested_angles_deg']);poses.append({'pose':s['pose'],'angles_deg':s['requested_angles_deg'],'hand_tip_delta_mm':{side:(Y[f'hand_tip_{side}'][:3,3]-X[f'hand_tip_{side}'][:3,3]).tolist() for side in ('l','r')},'hand_tip_distance_mm':{side:float(np.linalg.norm(Y[f'hand_tip_{side}'][:3,3]-X[f'hand_tip_{side}'][:3,3])) for side in ('l','r')}})
  w=float(np.linalg.norm(A['upperarm_l.flex']['origin']-A['upperarm_r.flex']['origin']));w2=float(np.linalg.norm(B['upperarm_l.flex']['origin']-B['upperarm_r.flex']['origin']))
  profiles.append({'character':ch,'design_reference':base['design_reference'],'shoulder_width_reference_mm':w,'shoulder_width_current_mm':w2,'shoulder_width_change_percent':100*(w2/w-1),'axis_origins':axes,'main_arm_segment_lengths':lengths,'same_angles_hand_tip_comparison':poses,'worst_hand_tip_case':max(poses,key=lambda s:max(s['hand_tip_distance_mm'].values()))})
 p=current/'integrated_arms.json';inputs[p.relative_to(H).as_posix()]=sha(p);cases=[]
 for row in read(p)['cases']:
  findings=[{**f,'classification':kind(*f['pair']),'regions':[region(n) for n in f['pair']]} for f in row['findings']]
  cases.append({**row,'findings':findings,'structural_findings':[f for f in findings if f['classification']=='STRUCTURAL_ADJACENT_OR_SAME_JOINT'],'pose_contact_findings':[f for f in findings if f['classification']=='POSE_AVOIDABLE_NONADJACENT_CONTACT']})
 report={'inputs_sha256':inputs,'scope':args.revision+' original 102 endpoint collision witnesses classified without removing poses or contacts. Same/adjacent mechanical regions are hard failures. Whole body, new-carrier paths and cables remain incomplete.','neighbor_edges':[sorted(e) for e in sorted(ADJ,key=lambda e:sorted(e))],'cases':cases,'structural_failure_endpoints':sum(bool(c['structural_findings']) for c in cases),'pose_contact_endpoints':sum(bool(c['pose_contact_findings']) for c in cases),'complete_body_structural_gate_passed':False}
 save('reference_deviations'+suffix+'.json',{'profiles':profiles,'inputs_sha256':inputs,'scope':'Against UE-derived 480 mm kinematic reference, same requested angles. This is a model-position comparison, not measured sensor accuracy or proven UE retargeting performance.'});save('collision_classification'+suffix+'.json',report)
 assert kind('elbow_l.flex/parent','forearm_l.twist/child')=='STRUCTURAL_ADJACENT_OR_SAME_JOINT'
 assert kind('hand_l.flex/parent','hand_r.deviate/child')=='POSE_AVOIDABLE_NONADJACENT_CONTACT'
 assert kind('TUT_l/C01','TUT_l/D')=='STRUCTURAL_ADJACENT_OR_SAME_JOINT'
 assert kind('l/integrated_bridge','TUT_l/D')=='STRUCTURAL_ADJACENT_OR_SAME_JOINT'
 try:region('unknown/part');raise AssertionError('unknown silently accepted')
 except ValueError:pass
 save('classifier_checks.json',{'status':'PASS','cases':5,'unknowns_fail_closed':True})
 print('structural endpoints',report['structural_failure_endpoints'],'nonadjacent contacts',report['pose_contact_endpoints'])
 for p in profiles:print(p['character'],'width change %',p['shoulder_width_change_percent'],'worst hand',p['worst_hand_tip_case']['pose'],p['worst_hand_tip_case']['hand_tip_distance_mm'])
if __name__=='__main__':main()
