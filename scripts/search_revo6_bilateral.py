"""Bilateral layout optimization: both arms scored together, no global optimum claim."""
from pathlib import Path
import argparse,hashlib,itertools,json,sys,copy
import numpy as np
R=Path(__file__).resolve().parents[1];H=R/'Hardware/PoseDoll44'
sys.path.insert(0,str(R/'scripts'))
import search_revo6_mixed as ms
from model import fk
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,d):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(d,indent=2)+'\n',encoding='utf-8')
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--large',type=Path,required=True);ap.add_argument('--small',type=Path,required=True);ap.add_argument('--out',type=Path,required=True);a=ap.parse_args()
 a.large=a.large.resolve();a.small=a.small.resolve();large=ms.make_boxes(json.loads(a.large.read_text()));small=ms.make_boxes(json.loads(a.small.read_text()));families=['M4','L6','L6','L6','M4','M4','M4','M4','M4'];local=[large if f=='L6' else small for f in families]
 options=list(itertools.product((-1,1),(12,20,28,36)));defaultprofile=ms.profile;defaultposes=ms.poses
 def allposes(side):
  p=defaultposes(side)
  for sign,node,axis in itertools.product((-1,1),('waist','chest'),('pitch','roll')):p.append((f'{node}_{axis}_{sign*30}_arm_side',{f'{node}.{axis}':sign*30,f'upperarm_{side}.abduct':90}))
  return p
 ms.poses=allposes
 def build(char,side,cfg,lateral):
  def profile(ch,clav,shoulder,wrist,ss):
   p=defaultprofile(ch,clav,shoulder,wrist,ss);n={n['id']:n for n in p['nodes']};d=np.array([0,(1 if ss=='l' else -1)*lateral,0])/1000
   for name,sign in [('clavicle_'+ss+'.protract_frame',1),('upperarm_'+ss+'.flex_frame',-1)]:n[name]['parent_to_axis']['translation_m']=(np.array(n[name]['parent_to_axis']['translation_m'])+sign*d).tolist()
   p['o6_clavicle_lateral_shift_mm']=lateral;return p
  ms.profile=profile
  p,ps,ids,f,l,h=ms.geometry(char,side,cfg,options,local)
  if side=='r':
   _,al=fk(profile(char,*cfg,'l'),{});_,ar=fk(p,{})
   for i,aid in enumerate(ids):
    polarity=int(round(np.dot(np.diag([1,-1,1])@al[aid.replace('_r.','_l.')]['direction'],ar[aid]['direction'])))
    if polarity<0:f[i]=f[i][[4,5,6,7,0,1,2,3]];l[i]=l[i][[4,5,6,7,0,1,2,3]];h[i]=h[i][[4,5,6,7,0,1,2,3]]
  return p,ps,ids,f,l,h
 rng=np.random.default_rng(604482);records=[];best=None
 def pair(l1,h1,l2,h2):
  d=np.minimum(h1[:,None,:,:,None,:],h2[None,:,:,None,:,:])-np.maximum(l1[:,None,:,:,None,:],l2[None,:,:,None,:,:])
  return np.prod(np.maximum(d+.3,0),axis=-1).sum((2,3,4))
 for lateral,clav,shoulder,wrist in itertools.product((10,16,22),(12,20),(16,20),(8,)):
  cfg=[clav,shoulder,wrist];data={(c,s):build(c,s,cfg,lateral) for c,s in itertools.product(('manny','quinn'),('l','r'))};costs={};unary=np.zeros((9,8))
  for i in range(9):
   for char in ('manny','quinn'):
    l,h=data[char,'l'][4:];lr,hr=data[char,'r'][4:]
    unary[i]+=np.diag(pair(l[i],h[i],lr[i],hr[i]))
   for _,_,_,_,l,h in data.values():
    # Neutral body envelope penalties; pose excursions are not height failures.
    unary[i]+=np.square(np.maximum(np.abs((l[i,:,0,:,0]+h[i,:,0,:,0])/2)-60,0)).sum(1)*80
    unary[i]+=np.square(np.maximum(np.abs((l[i,:,0,:,1]+h[i,:,0,:,1])/2)-90,0)).sum(1)*80
    unary[i]+=np.square(np.maximum(h[i,:,0,:,2]-495,0)).sum(1)*500
  for i,j in itertools.combinations(range(9),2):
   matrix=np.zeros((8,8))
   for char in ('manny','quinn'):
    for s1,s2 in itertools.product(('l','r'),repeat=2):
     l1,h1=data[char,s1][4:];l2,h2=data[char,s2][4:];matrix+=pair(l1[i],h1[i],l2[j],h2[j])
   costs[i,j]=matrix
  def score(c):return float(sum(unary[i,v] for i,v in enumerate(c))+sum(m[c[i],c[j]] for (i,j),m in costs.items()))
  cbest=None
  for _ in range(100):
   choice=rng.integers(8,size=9)
   for _ in range(40):
    previous=choice.copy()
    for i in rng.permutation(9):
     v=unary[i].copy()
     for j in range(9):
      if j>i:v+=costs[i,j][:,choice[j]]
      if j<i:v+=costs[j,i][choice[j],:]
     choice[i]=int(v.argmin())
    if np.array_equal(previous,choice):break
   val=score(choice)
   if cbest is None or val<cbest[0]:cbest=(val,choice.copy())
  val,choice=cbest;records.append({'lateral_mm':lateral,'offsets_mm':cfg,'score':val,'options':[options[k] for k in choice]});print(lateral,cfg,round(val),choice.tolist(),flush=True)
  if best is None or val<best[0]:best=(val,lateral,cfg,choice)
 val,lateral,cfg,choice=best;characters=[]
 for char,side in itertools.product(('manny','quinn'),('l','r')):
  p,ps,ids,frames,l,h=build(char,side,cfg,lateral);selected=np.array([frames[i,c] for i,c in enumerate(choice)]);_,axes=fk(p,{})
  opts=[]
  for i,aid in enumerate(ids):
   direction=selected[i,0,:3,2];sign=int(round(np.dot(direction,axes[aid]['direction'])));opts.append({'sign':sign,'standoff_mm':options[choice[i]][1]})
  save(a.out/(char+'_'+side+'_profile.json'),p)
  characters.append({'character':char,'side':side,'axes':ids,'families':families,'options':opts,'module_frames':selected.tolist(),'poses':[{'pose':n,'angles_deg':q} for n,q in ps]})
 inputs=[a.large,a.small,Path(__file__),R/'scripts/search_revo6_mixed.py',R/'scripts/study_revo.py',H/'cad/model.py']+[H/f'mechanical_manifest/physical_{c}_44_revG_humanform_trial.json' for c in ('manny','quinn')]
 save(a.out/'layout_search.json',{'schema':'o6-bilateral-coarse-search-v1','method':'12 configurations, seeded 100 restarts each; actual sliced BRep bounds with 0.3mm search allowance. Not continuous or global optimum proof.','selected':{'score':val,'lateral_mm':lateral,'offsets_mm':cfg},'configurations':records,'characters':characters,'input_sha256':{p.relative_to(R).as_posix():sha(p) for p in inputs},'physical_tested':False,'manufacturing_released':False})
if __name__=='__main__':main()


