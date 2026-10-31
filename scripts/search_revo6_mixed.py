"""O6 deterministic multi-pose layout search. AABB search is NOT a fit certificate."""
from pathlib import Path
import argparse,copy,hashlib,itertools,json,sys
import numpy as np
R=Path(__file__).resolve().parents[1];H=R/'Hardware/PoseDoll44'
sys.path.insert(0,str(R/'scripts'));from study_revo import anatomy
from model import fk,rotation,keyposes
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,d):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(d,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
def align(z):
 z=np.asarray(z,float);x=np.cross([0,1,0] if abs(z[1])<.9 else [1,0,0],z);x/=np.linalg.norm(x);return np.column_stack([x,np.cross(z,x),z])
def poses(side):
 p=[('neutral',{})]
 # Defined coverage, not user-approved final range or continuous collision proof.
 for stem,angles in [('clavicle.protract',[-20,20]),('clavicle.elevate',[-10,20,40]),('upperarm.flex',[-45,45,90,135,160]),('upperarm.abduct',[-20,30,60,90,120,160]),('upperarm.twist',[-90,-45,45,90]),('elbow.flex',[30,60,90,120,140]),('forearm.twist',[-90,90]),('hand.flex',[-60,60]),('hand.deviate',[-30,30])]:
  bone,axis=stem.split('.');aid=bone+'_'+side+'.'+axis
  p.extend((aid+'_'+str(v),{aid:v}) for v in angles)
 for n,d in keyposes().items():
  if any(k.startswith(('clavicle','upperarm','elbow','forearm','hand')) for k in d):p.append((n,{k:v for k,v in d.items() if '_'+side+'.' in k}))
 p.extend(('back_reach_'+str(a),{f'upperarm_{side}.flex':-a,f'elbow_{side}.flex':90,f'upperarm_{side}.twist':-45}) for a in (15,30,45))
 return p
def profile(char,clav,shoulder,wrist,side):
 p=anatomy(char,480);n={x['id']:x for x in p['nodes']};sgn=1 if side=='l' else -1
 def change(name,delta):
  q=n[name]['parent_to_axis']['translation_m'];n[name]['parent_to_axis']['translation_m']=(np.array(q)+np.array(delta)/1000).tolist()
 # Redistribute within existing bone length, unlike simply lengthening the arm.
 change('clavicle_'+side,[0,sgn*clav,0]);change('upperarm_'+side+'.flex_frame',[0,-sgn*clav,0])
 change('upperarm_'+side+'.abduct_frame',[0,0,-shoulder]);change('upperarm_'+side,[0,0,-shoulder]);change('elbow_'+side,[0,0,2*shoulder])
 change('hand_'+side,[0,0,-wrist]);change('hand_tip_'+side,[0,0,wrist])
 p['profile_id']=f'o6_{char}_{side}_layout_only';p['status']='GEOMETRIC_TRIAL_NOT_DEVICE_CALIBRATION'
 return p
def make_boxes(joint):
 # Union actual part bounds into five axial groups. Overlapping groups enclose
 # every part; cross-group volume scores are heuristic, not physical volumes.
 if 'section_bounds_mm' in joint:return np.array([list(itertools.product(*zip(b[:3],b[3:]))) for b in joint['section_bounds_mm']])
 bands=[(-24,-15),(-15,0),(0,5),(5,20),(20,32)]
 boxes=[]
 for z0,z1 in bands:
  clipped=[]
  for row in joint['parts']:
   b=np.array(row['bounds_mm']).copy();b[2]=max(b[2],z0);b[5]=min(b[5],z1)
   if b[5]>b[2]:clipped.append(b)
  low=np.min(np.array(clipped)[:,:3],0);high=np.max(np.array(clipped)[:,3:],0)
  boxes.append(np.array(list(itertools.product(*zip(low,high)))))
 return np.array(boxes)
def geometry(char,side,cfg,options,local):
 p=profile(char,*cfg,side);ps=poses(side);nodes=[n for n in p['nodes'] if n.get('axis_id','').startswith(tuple(x+'_'+side+'.' for x in ('clavicle','upperarm','elbow','forearm','hand')))]
 states=[fk(p,pose)[1] for _,pose in ps]
 frames=[];lo=[];hi=[]
 for index,node in enumerate(nodes):
  axislocal=local[index] if isinstance(local,list) else local
  allf=[];alllo=[];allhi=[]
  for sign,distance in options:
   fs=[];ls=[];hs=[]
   for axes in states:
    axis=axes[node['axis_id']]
    M=axis['frame'].copy();M[:3,:3]=M[:3,:3]@align(np.array(node['axis_local'])*sign);M[:3,3]+=M[:3,2]*distance
    points=axislocal@M[:3,:3].T+M[:3,3];ls.append(points.min(1));hs.append(points.max(1));fs.append(M)
   allf.append(fs);alllo.append(ls);allhi.append(hs)
  frames.append(allf);lo.append(alllo);hi.append(allhi)
 return p,ps,[n['axis_id'] for n in nodes],np.array(frames),np.array(lo),np.array(hi)
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--joint',type=Path,required=True);ap.add_argument('--small',type=Path,required=True);ap.add_argument('--out',type=Path,required=True);a=ap.parse_args();a.joint=a.joint.resolve();a.small=a.small.resolve();a.out=a.out.resolve()
 joint=json.loads(a.joint.read_text());small=json.loads(a.small.read_text());local=[make_boxes(joint)]*4+[make_boxes(small)]*5;options=list(itertools.product((-1,1),(12,20,28,36,44)))
 rng=np.random.default_rng(604480);summaries=[];best=None
 configs=list(itertools.product((12,20),(12,20),(8,16)))
 for cfg in configs:
  # Both body references are scored; right-hand geometry is subsequently
  # evaluated independently, never reflected as a left-handed CAD transform.
  data=[geometry(ch,'l',cfg,options,local) for ch in ('manny','quinn')]
  costs={};unary=np.zeros((9,len(options)))
  for i,j in itertools.combinations(range(9),2):
   mat=np.zeros((len(options),len(options)))
   for _,_,_,_,low,high in data:
    ov=np.minimum(high[i][:,None,:, :,None,:],high[j][None,:, :,None,:,:])-np.maximum(low[i][:,None,:, :,None,:],low[j][None,:, :,None,:,:])
    # Minimum 0.5 mm coarse search allowance is included on every axis.
    volume=np.prod(np.maximum(ov+.5,0),axis=-1)
    mat+=volume.sum(axis=(2,3,4))
   costs[(i,j)]=mat
  for _,_,_,_,low,high in data:
   # Do not prefer spreading modules indefinitely just to avoid collisions.
   # Target envelope is a search box, not anatomy/shell acceptance.
   unary+=np.square(np.maximum(high[:,:,0,:,2]-500,0)).sum(2)*1000
   unary+=np.square(np.maximum(abs((high[:,:,:,:,0]+low[:,:,:,:,0])/2)-65,0)).sum((2,3))*10
   unary+=np.square(np.maximum(high[:,:,:,:,1]-125,0)).sum((2,3))*10
   unary+=np.array([[d*.02 for _,d in options]]*9)
  def score(choice):
   return float(sum(unary[i,c] for i,c in enumerate(choice))+sum(mat[choice[i],choice[j]] for (i,j),mat in costs.items()))
  localbest=None
  for trial in range(100):
   choice=rng.integers(len(options),size=9)
   for _ in range(30):
    previous=choice.copy()
    for i in rng.permutation(9):
     values=unary[i].copy()
     for j in range(9):
      if i<j:values+=costs[(i,j)][:,choice[j]]
      elif j<i:values+=costs[(j,i)][choice[j],:]
     choice[i]=int(np.argmin(values))
    if np.array_equal(previous,choice):break
   val=score(choice)
   if localbest is None or val<localbest[0]:localbest=(val,choice.copy())
  val,choice=localbest;summary={'clavicle_offset_mm':cfg[0],'shoulder_stage_offset_mm':cfg[1],'wrist_offset_mm':cfg[2],'heuristic_score':val,'choices':[options[k] for k in choice]}
  summaries.append(summary);print(cfg,round(val),choice.tolist(),flush=True)
  if best is None or val<best[0]:best=(val,cfg,choice)
 val,cfg,choice=best;characters=[]
 for ch,side in itertools.product(('manny','quinn'),('l','r')):
  sidechoice=choice.copy()
  if side=='r':
   lp=profile(ch,*cfg,'l');rp=profile(ch,*cfg,'r');_,la=fk(lp,{});_,ra=fk(rp,{})
   aids=[n['axis_id'] for n in rp['nodes'] if n.get('axis_id','').startswith(tuple(x+'_r.' for x in ('clavicle','upperarm','elbow','forearm','hand')))]
   for i,aid in enumerate(aids):
    polarity=int(round(np.dot(np.diag([1,-1,1])@la[aid.replace('_r.','_l.')]['direction'],ra[aid]['direction'])))
    sign,d=options[choice[i]];sidechoice[i]=options.index((sign*polarity,d))
  p,ps,ids,frames,low,high=geometry(ch,side,cfg,options,local);selected=np.array([frames[i,c] for i,c in enumerate(sidechoice)])
  hits=[]
  for k,(name,pose) in enumerate(ps):
   pairs=[]
   for i,j in itertools.combinations(range(9),2):
    ov=np.minimum(high[i,sidechoice[i],k,:,None,:],high[j,sidechoice[j],k,None,:,:])-np.maximum(low[i,sidechoice[i],k,:,None,:],low[j,sidechoice[j],k,None,:,:])
    count=int((ov>0).all(-1).sum())
    if count:pairs.append({'a':ids[i],'b':ids[j],'potential_box_pairs':count})
   hits.append({'pose':name,'angles_deg':pose,'pairs':pairs})
  original=anatomy(ch,480);tn,_=fk(p,{});to,_=fk(original,{})
  preserved={n:float(np.linalg.norm(tn[n][:3,3]-to[n][:3,3])) for n in ('upperarm_'+side+'.flex_frame','elbow_'+side,'hand_'+side+'.flex_frame','hand_tip_'+side)}
  assert max(preserved.values())<1e-8
  a.out.mkdir(parents=True,exist_ok=True);save(a.out/(ch+'_'+side+'_profile.json'),p)
  characters.append({'character':ch,'side':side,'axes':ids,'families':['L6']*4+['M4']*5,'options':[{'sign':options[k][0],'standoff_mm':options[k][1]} for k in sidechoice],'preserved_neutral_anchor_error_mm':preserved,'poses':hits,'module_frames':selected.tolist()})
 inputs=[a.joint,a.small,Path(__file__),R/'scripts/study_revo.py',H/'cad/model.py']
 inputs += [H/f'mechanical_manifest/physical_{c}_44_revG_humanform_trial.json' for c in ('manny','quinn')]
 save(a.out/'layout_search.json',{'schema':'o6-layout-search-v1','method':'Deterministic AABB heuristic, 100 restarts per configuration; not an exhaustive feasibility proof','configurations':summaries,'selected':{'offsets_mm':list(cfg),'heuristic_score':val},'characters':characters,'joint_groups_local_corners_mm':[b.tolist() for b in local],'input_sha256':{p.relative_to(R).as_posix():sha(p) for p in inputs},'physical_tested':False,'manufacturing_released':False,'requires':'Exact imported-solid audit, actual yokes, shell/RF/service, continuous paths and wire routes'})
if __name__=='__main__':main()


