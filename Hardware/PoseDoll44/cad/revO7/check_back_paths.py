"""Sample neutral-to-goal paths against one empty back reservation and actual joint parts."""
from pathlib import Path
import argparse,json,hashlib,itertools,sys,math
import numpy as np
import cadquery as cq
R=Path(__file__).resolve().parents[4];H=R/'Hardware/PoseDoll44'
sys.path.insert(0,str(H/'cad'));sys.path.insert(0,str(H/'cad/revO6'));sys.path.insert(0,str(R/'scripts'))
from model import fk,rotation
from audit_mixed import located
from thread_geometry import overlap_volume
from search_revo6_backspace import distances

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,d):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(d,indent=2)+'\n',encoding='utf-8')
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--joint',type=Path,required=True);ap.add_argument('--layout',type=Path,required=True);ap.add_argument('--targets',type=Path,required=True);ap.add_argument('--out',type=Path,required=True);a=ap.parse_args()
 target=json.loads(a.targets.read_text())['selected_thin_target'];lo=np.array(target['local_bounds_mm'][:3]);hi=np.array(target['local_bounds_mm'][3:]);back=cq.Workplane('XY').box(*(hi-lo)).val().translate(tuple((lo+hi)/2));layout=json.loads((a.layout/'layout_search.json').read_text());records={(x['character'],x['side']):x for x in layout['characters']};libs={};profiles={};sources=[Path(__file__),a.targets,a.layout/'layout_search.json',H/'cad/model.py',H/'cad/revO6/audit_mixed.py',H/'cad/revO6/thread_geometry.py',R/'scripts/search_revo6_backspace.py',R/'scripts/search_revo6_mixed.py',R/'scripts/study_revo.py',R/'scripts/revo_common.py'];localframes={}
 for fam,folder in [('LP6',a.joint),('M4',H/'generated/revO6/runs/o6_20260924_r1/joint_M4_validated')]:
  p=folder/'manifest.json';sources.append(p);m=json.loads(p.read_text());assert not m['nominal_intersections'];lib=[]
  for row in m['parts']:
   p=folder/row['step_file'];assert sha(p)==row['step_sha256'];sources.append(p);b=row['bounds_mm'];lib.append((row['part_id'],row['owner'],cq.importers.importStep(str(p)).val(),np.array(list(itertools.product(*zip(b[:3],b[3:]))))))
  libs[fam]=lib
 for key,rec in records.items():
  p=a.layout/('_'.join(key)+'_profile.json');sources.append(p);profiles[key]=json.loads(p.read_text());_,axes=fk(profiles[key],{});localframes[key]={axis:np.linalg.inv(axes[axis]['frame'])@np.array(rec['module_frames'][i][0]) for i,axis in enumerate(rec['axes'])}
 inputs={p.resolve().relative_to(R).as_posix():sha(p) for p in sources};cache={};cases=[];examples=[];statecount=0;paircount=0;minexact=None;mincaps=None
 for char in ('manny','quinn'):
  for k,goal in enumerate(records[char,'l']['poses']):
   q=dict(goal['angles_deg']);q.update(records[char,'r']['poses'][k]['angles_deg']);steps=max(1,math.ceil(max([abs(v) for v in q.values()] or [0])/5));badsteps=0;bodybad=0;mindist=math.inf;gmincap=math.inf
   for j in range(steps+1):
    t=j/steps;state={axis:val*t for axis,val in q.items()};statehits=[]
    for side in ('l','r'):
     rec=records[char,side];T,A=fk(profiles[char,side],state);inv=np.linalg.inv(T['chest'])
     for n,z,r in [('upperarm_'+side,'elbow_'+side,10),('elbow_'+side,'hand_'+side,9),('hand_'+side,'hand_tip_'+side,12)]:
      aa=(inv[:3,:3]@T[n][:3,3]+inv[:3,3])[None,:];bb=(inv[:3,:3]@T[z][:3,3]+inv[:3,3])[None,:];d=float(distances(aa,bb,lo,hi)[0]-r);gmincap=min(gmincap,d)
      if d<.5:bodybad+=1
     for i,(axis,fam) in enumerate(zip(rec['axes'],rec['families'])):
      M=A[axis]['frame']@localframes[char,side][axis];C=M.copy();C[:3,:3]=rotation(A[axis]['direction'],state.get(axis,0))@M[:3,:3]
      if j==steps:assert np.max(np.abs(M-np.array(rec['module_frames'][i][k])))<1e-7,'Path frame does not recover recorded goal'
      for name,owner,shape,corners in libs[fam]:
       F=inv@(C if owner=='child' else M);pts=corners@F[:3,:3].T+F[:3,3];b0,b1=pts.min(0),pts.max(0)
       # Euclidean AABB distance is a lower bound on part-to-box distance.
       lb=float(np.linalg.norm(np.maximum(np.maximum(lo-b1,b0-hi),0)))
       if lb>=.5:continue
       key=(fam,name,tuple(np.round(F.reshape(-1),10)))
       if key not in cache:
        solid=located(shape,F);dist=solid.distance(back);vol=overlap_volume(solid,back) if dist<1e-7 else 0.;cache[key]=(float(dist),float(vol));paircount+=1
       dist,vol=cache[key];mindist=min(mindist,dist)
       if minexact is None or dist<minexact['distance_mm']:minexact={'character':char,'goal':goal['pose'],'fraction':t,'axis':axis,'part':name,'distance_mm':dist,'intersection_mm3':vol}
       if dist<.5-1e-7:statehits.append({'axis':axis,'part':name,'distance_mm':dist,'intersection_mm3':vol})
    statecount+=1
    if statehits:
     badsteps+=1
     if len(examples)<50:examples.append({'character':char,'goal':goal['pose'],'fraction':t,'hits':statehits})
   cases.append({'character':char,'goal':goal['pose'],'path_states':steps+1,'module_guard_failure_states':badsteps,'capsule_guard_failure_pairs':bodybad,'minimum_exact_distance_among_broadphase_candidates_mm':mindist if math.isfinite(mindist) else None,'minimum_capsule_clearance_mm':gmincap})
   mincaps=gmincap if mincaps is None else min(mincaps,gmincap);print(char,goal['pose'],steps+1,badsteps,bodybad,flush=True);save(a.out/'progress.json',{'status':'RUNNING_INCOMPLETE','cases':cases})
 assert all(sha(R/n)==v for n,v in inputs.items())
 save(a.out/'back_paths.json',{'status':'FAIL_SAMPLED_GUARD' if any(x['module_guard_failure_states'] or x['capsule_guard_failure_pairs'] for x in cases) else 'PASS_SAMPLED_EMPTY_RESERVATION_ONLY','target':target,'guard_mm':.5,'max_joint_step_deg':5,'path_states_total':statecount,'goals_total':len(cases),'cases':cases,'examples':examples,'minimum_exact_candidate':minexact,'minimum_capsule_clearance_mm':mincaps,'unique_exact_distance_pairs':paircount,'transform_cache_rounding_decimal_places':10,'input_sha256':inputs,'scope':'Empty box versus LP6/M4 part solids plus declared limb capsules; excludes carriers, shell, full PCB, neck/torso hardware, wiring and general coordinated paths. Does not certify full doll motion.','physical_tested':False,'manufacturing_released':False});(a.out/'progress.json').unlink()
if __name__=='__main__':main()
