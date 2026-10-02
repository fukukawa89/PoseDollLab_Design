"""Coupled coarse back reservation screen against the O7 trial and retained body goals."""
from pathlib import Path
import hashlib,json,itertools,sys
import numpy as np
R=Path(__file__).resolve().parents[1];H=R/'Hardware/PoseDoll44';G=H/'generated/revO7/runs/o7_20260924_r1';V=H/'verification/revO7/runs/o7_20260924_r1'
sys.path.insert(0,str(R/'scripts'));from search_revo6_backspace import distances
from model import fk,rotation

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 lp=G/'bilateral_current/layout_search.json';prior=H/'verification/revO6/runs/o6_20260924_r1/backspace/back_reservation.json';layout=json.loads(lp.read_text());old=json.loads(prior.read_text());paths=[Path(__file__),lp,prior,R/'scripts/search_revo6_backspace.py',R/'scripts/search_revo6_mixed.py',R/'scripts/study_revo.py',R/'scripts/revo_common.py',H/'cad/model.py'];libs={}
 for fam,p in [('LP6',G/'LP6_current/manifest.json'),('M4',H/'generated/revO6/runs/o6_20260924_r1/joint_M4_validated/manifest.json')]:
  paths.append(p);m=json.loads(p.read_text());libs[fam]=[(r['part_id'],r['owner'],np.array(list(itertools.product(*zip(r['bounds_mm'][:3],r['bounds_mm'][3:]))))) for r in m['parts']]
 lows=[];highs=[];labels=[];a=[];b=[];radii=[]
 for rec in layout['characters']:
  char,side=rec['character'],rec['side'];p=G/'bilateral_current'/(char+'_'+side+'_profile.json');paths.append(p);profile=json.loads(p.read_text())
  for k,pose in enumerate(rec['poses']):
   T,A=fk(profile,pose['angles_deg']);inv=np.linalg.inv(T['chest'])
   for n,z,rad in [('upperarm_'+side,'elbow_'+side,10),('elbow_'+side,'hand_'+side,9),('hand_'+side,'hand_tip_'+side,12)]:
    a.append(inv[:3,:3]@T[n][:3,3]+inv[:3,3]);b.append(inv[:3,:3]@T[z][:3,3]+inv[:3,3]);radii.append(rad)
   for i,(axis,fam) in enumerate(zip(rec['axes'],rec['families'])):
    M=np.array(rec['module_frames'][i][k]);C=M.copy();C[:3,:3]=rotation(A[axis]['direction'],pose['angles_deg'].get(axis,0))@M[:3,:3]
    for name,owner,pts in libs[fam]:
     frame=inv@(C if owner=='child' else M);q=pts@frame[:3,:3].T+frame[:3,3];lows.append(q.min(0));highs.append(q.max(0));labels.append((char,pose['pose'],axis,name))
 lows=np.array(lows);highs=np.array(highs);a=np.array(a);b=np.array(b);radii=np.array(radii);candidates=[]
 for row in old['candidates']:
  lo=np.array(row['local_bounds_mm'][:3]);hi=np.array(row['local_bounds_mm'][3:]);capsule=distances(a,b,lo,hi)-radii;delta=np.minimum(highs,hi)-np.maximum(lows,lo);hit=np.where((delta+.5>0).all(1))[0];poses=set(labels[k][:2] for k in hit)
  candidates.append({'outer_width_height_depth_mm':row['outer_width_height_depth_mm'],'local_bounds_mm':row['local_bounds_mm'],'volume_cm3':row['volume_cm3'],'minimum_trial_capsule_clearance_mm':float(capsule.min()),'poses_with_part_AABB_overlap_or_under_guard':len(poses),'coarse_penetration_score_mm3':float(np.maximum(delta[hit]+.5,0).prod(1).sum()),'first_potential_pair':labels[int(hit[0])] if len(hit) else None,'coarse_clear':bool(not len(hit) and capsule.min()>=.5)})
 good=[c for c in candidates if c['coarse_clear']];fit=[c for c in candidates if c['minimum_trial_capsule_clearance_mm']>=.5];pool=fit or candidates;best=max(good,key=lambda c:c['volume_cm3']) if good else min(pool,key=lambda c:(c['poses_with_part_AABB_overlap_or_under_guard'],c['coarse_penetration_score_mm3']))
 result={'schema':'o7-coupled-back-reservation-coarse-v1','candidate_count':len(candidates),'clear_count':len(good),'capsule_clear_count':len(fit),'selected_for_exact_audit':dict(best,name='O7 coupled back target'),'all_candidates':candidates,'guard_mm':.5,'discrete_states_per_character':51,'scope':'Actual joint part AABB envelopes and current trial anatomical segments. Potential AABB overlap is NOT proof of solid collision. No PCB, skin, harness, mount, RF or arbitrary-path approval.','native_central_PCBA_exists':False,'input_sha256':{p.relative_to(R).as_posix():sha(p) for p in paths},'physical_tested':False,'manufacturing_released':False}
 p=V/'back_coarse.json';p.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8');(V/'back_exact_targets.json').write_text(json.dumps({'prior_targets':[old['selected_thin_target']],'selected_thin_target':dict(best,name='O7 coupled back target'),'input_sha256':{p.relative_to(R).as_posix():sha(p),prior.relative_to(R).as_posix():sha(prior)}},indent=2)+'\n',encoding='utf-8');print('candidates',len(candidates),'clear',len(good),'capsule clear',len(fit),'best',best)
if __name__=='__main__':main()
