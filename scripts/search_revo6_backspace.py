"""Find movement-aware thoracic reservation targets, never a PCB/body qualification."""
from pathlib import Path
import argparse,hashlib,json,sys,itertools,math
import numpy as np
R=Path(__file__).resolve().parents[1];H=R/'Hardware/PoseDoll44'
sys.path.insert(0,str(R/'scripts'))
from study_revo import anatomy
from search_revo6_mixed import poses
from model import fk,keyposes

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,d):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def distances(a,b,lo,hi):
 # Piecewise quadratic minimum of distance squared to an AABB. Segment
 # breakpoints at six face planes; minimization on each interval is analytic.
 v=b-a;n=len(a);ts=[np.zeros(n),np.ones(n)]
 for k in range(3):
  for face in (lo[k],hi[k]):
   t=np.divide(face-a[:,k],v[:,k],out=np.zeros(n),where=np.abs(v[:,k])>1e-14);ts.append(np.clip(t,0,1))
 t=np.sort(np.array(ts).T,axis=1);l=t[:,:-1];r=t[:,1:];mid=(l+r)/2
 points=a[:,None,:]+mid[:,:,None]*v[:,None,:]
 active=(points<lo)|(points>hi);edge=np.where(points<lo,lo,hi)
 c=np.where(active,a[:,None,:]-edge,0);vv=np.where(active,v[:,None,:],0)
 den=(vv*vv).sum(2);num=-(c*vv).sum(2);opt=np.divide(num,den,out=mid.copy(),where=den>1e-20);opt=np.maximum(l,np.minimum(r,opt))
 points=a[:,None,:]+opt[:,:,None]*v[:,None,:];d=np.maximum(np.maximum(lo-points,points-hi),0)
 return np.sqrt((d*d).sum(2).min(1))
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--out',type=Path,required=True);args=ap.parse_args()
 base={name:dict(q,**{aid.replace('_l.','_r.'):val for aid,val in q.items() if '_l.' in aid}) for name,q in poses('l')};base.update(keyposes())
 for d in (-30,30):
  for node,axis in itertools.product(('waist','chest'),('pitch','roll','yaw')):base[f'{node}_{axis}_{d}']={node+'.'+axis:d}
 base.update({'hands_low_behind':{'upperarm_l.flex':-30,'upperarm_r.flex':-30,'elbow_l.flex':55,'elbow_r.flex':55},'one_hand_up_back':{'upperarm_l.flex':-25,'upperarm_l.twist':65,'elbow_l.flex':130},'touch_back_head':{'upperarm_l.flex':150,'elbow_l.flex':115,'upperarm_l.twist':-35}})
 # Named goals retained even if the current joints fail them; sampled paths
 # are neutral->goal, not proof for arbitrary coordinated motion.
 states=[]
 for name,q in base.items():
  count=max(1,int(math.ceil(max([abs(x) for x in q.values()] or [0])/5)))
  for k in range(1,count+1):states.append((name,k/count,{aid:val*k/count for aid,val in q.items()}))
 aa=[];bb=[];rr=[];labels=[]
 for char in ('manny','quinn'):
  p=anatomy(char,480)
  for pose,t,q in states:
   T,_=fk(p,q);inv=np.linalg.inv(T['chest'])
   for side in ('l','r'):
    for x,y,r in [('upperarm_'+side,'elbow_'+side,10),('elbow_'+side,'hand_'+side,9),('hand_'+side,'hand_tip_'+side,12)]:
     aa.append(inv[:3,:3]@T[x][:3,3]+inv[:3,3]);bb.append(inv[:3,:3]@T[y][:3,3]+inv[:3,3]);rr.append(r);labels.append({'character':char,'goal':pose,'path_fraction':t,'segment':[x,y],'radius_assumption_mm':r})
 aa=np.array(aa);bb=np.array(bb);rr=np.array(rr)
 # Independent elementary distance checks, including crossing, corner and point.
 fixture_a=np.array([[2,0,0],[-2,0,0],[2,2,0],[2,2,2]],float);fixture_b=np.array([[3,0,0],[2,0,0],[2,2,0],[3,3,3]],float)
 assert np.allclose(distances(fixture_a,fixture_b,np.array([-1]*3),np.array([1]*3)),[1,0,2**.5,3**.5],atol=1e-10)
 candidates=[];guard=.5
 def screen(width,height,depth,top,label):
  lo=np.array([-28-depth,-width/2,top-height]);hi=np.array([-28,width/2,top]);clear=distances(aa,bb,lo,hi)-rr;worst=int(clear.argmin());bad=np.where(clear<guard)[0]
  return {'name':label,'outer_width_height_depth_mm':[width,height,depth],'local_bounds_mm':lo.tolist()+hi.tolist(),'volume_cm3':width*height*depth/1000,'within_declared_thoracic_zone':bool(top<=78 and top-height>=-16),'minimum_capsule_clearance_mm':float(clear[worst]),'worst_case':labels[worst],'path_samples_with_reservation_contacts_or_below_guard':len(set((labels[k]['character'],labels[k]['goal'],labels[k]['path_fraction']) for k in bad)),'scope_status':'CLEAR_SAMPLED_ANATOMY_CAPSULES_ONLY' if not len(bad) else 'FAIL_CAPSULE_RESERVATION','examples':[dict(labels[k],clearance_mm=float(clear[k])) for k in bad[:12]]}
 for width,height,depth,top in itertools.product((48,54,60,66,72,78,84),(48,60,72,84,96),(12,18,22,28,36),(48,54,60,66,72,78)):
  if top-height < -16:continue
  candidates.append(screen(width,height,depth,top,'grid'))
  if len(candidates)%250==0:print('screened',len(candidates),flush=True)
 good=[x for x in candidates if x['scope_status'].startswith('CLEAR')];pareto=[x for x in good if not any(all(u>=v for u,v in zip(y['outer_width_height_depth_mm'],x['outer_width_height_depth_mm'])) and any(u>v for u,v in zip(y['outer_width_height_depth_mm'],x['outer_width_height_depth_mm'])) for y in good)]
 # Equal-volume alternatives can expose different placement/body envelopes.
 selected=max((x for x in good if x['outer_width_height_depth_mm'][2]<=22),key=lambda x:(x['volume_cm3'],x['minimum_capsule_clearance_mm']),default=None)
 prior=[screen(83,103,83.2,58,'six-board reuse'),screen(66,76,22,58,'previous target only')]
 sources=[Path(__file__),R/'scripts/search_revo6_mixed.py',R/'scripts/study_revo.py',R/'scripts/revo_common.py',H/'cad/model.py',*[H/f'mechanical_manifest/physical_{c}_44_revG_humanform_trial.json' for c in ('manny','quinn')]]
 report={'schema':'o6-back-reservation-sweep-v1','candidate_count':len(candidates),'clear_candidate_count':len(good),'goal_count':len(base),'states_per_character':len(states),'capsule_segment_checks_per_candidate':len(labels),'maximum_interpolation_step_deg':5,'clearance_guard_mm':guard,'fixed_torso_side_x_mm':-28,'thoracic_zone_local_z_mm':[-16,78],'zone_is_design_reservation_not_skin_fit':True,'prior_targets':prior,'selected_thin_target':selected,'pareto_largest_clear_targets':pareto,'candidates':candidates,'physical_tested':False,'manufacturing_released':False,'routed_electronics_exist_for_selected_target':False,'scope_limits':['Anatomy references only; current trial joint offsets/modules and yokes are excluded','No chest/neck skin, standing/lying support, cable/connector, tool or RF clearance','Declared capsule radii do not establish real limb outer shape','5 degree neutral-to-goal paths are sampled, not continuous motion or arbitrary multi-axis proof','Maximum-volume clear grid box is an electronics target only; full native PCBA may require a larger or different box'],'input_sha256':{p.relative_to(R).as_posix():sha(p) for p in sources}}
 save(args.out/'back_reservation.json',report);print('candidates',len(candidates),'clear',len(good),'selected',selected,flush=True)
if __name__=='__main__':main()
