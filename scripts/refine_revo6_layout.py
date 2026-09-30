"""Refine witnessed side-raise collisions; mirror axis directions, never BReps."""
from pathlib import Path
import argparse,hashlib,itertools,json,sys
import numpy as np
R=Path(__file__).resolve().parents[1];H=R/'Hardware/PoseDoll44'
sys.path.insert(0,str(R/'scripts'))
from search_revo6_layout import profile,poses,align,make_boxes
from model import fk
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,d):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(d,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--joint',type=Path,required=True);ap.add_argument('--search',type=Path,required=True);ap.add_argument('--witness',type=Path,required=True);ap.add_argument('--out',type=Path,required=True);a=ap.parse_args()
 a.joint=a.joint.resolve();a.search=a.search.resolve();a.witness=a.witness.resolve();a.out=a.out.resolve()
 baseline=json.loads(a.search.read_text());joint=json.loads(a.joint.read_text());local=make_boxes(joint);cfg=[24,24,12]
 options=[dict(x) for x in baseline['characters'][0]['options']]
 options[0]['standoff_mm']=12
 options[6]['standoff_mm']=12
 records=[];S=np.diag([1,-1,1])
 for ch,side in itertools.product(('manny','quinn'),('l','r')):
  p=profile(ch,*cfg,side)
  ns={n['id']:n for n in p['nodes']};sgn=1 if side=='l' else -1
  delta=np.array([10,sgn*20,0])/1000
  for name,sign in [('clavicle_'+side+'.protract_frame',1),('upperarm_'+side+'.flex_frame',-1)]:
   ns[name]['parent_to_axis']['translation_m']=(np.array(ns[name]['parent_to_axis']['translation_m'])+sign*delta).tolist()
  p['o6_mechanical_offsets_mm']={'sternoclavicular_forward':10,'sternoclavicular_lateral':20,'neutral_external_anchors_preserved':True}
  ps=poses(side);ids=[n['axis_id'] for n in p['nodes'] if n.get('axis_id','').startswith(tuple(x+'_'+side+'.' for x in ('clavicle','upperarm','elbow','forearm','hand')))]
  left=profile(ch,*cfg,'l');_,al=fk(left,{});_,ar=fk(p,{})
  opts=[dict(x) for x in options]
  if side=='r':
   for i,aid in enumerate(ids):
    la=aid.replace('_r.','_l.')
    opts[i]['sign']*=int(round(np.dot(S@al[la]['direction'],ar[aid]['direction'])))
  frames=[];lows=[];highs=[]
  for aid,opt in zip(ids,opts):
   node=next(n for n in p['nodes'] if n.get('axis_id')==aid);fs=[];los=[];his=[]
   for _,pose in ps:
    _,axes=fk(p,pose);M=axes[aid]['frame'].copy();M[:3,:3]=M[:3,:3]@align(np.array(node['axis_local'])*opt['sign']);M[:3,3]+=M[:3,2]*opt['standoff_mm']
    assert np.linalg.det(M[:3,:3])>.999999
    q=local@M[:3,:3].T+M[:3,3];fs.append(M.tolist());los.append(q.min(1));his.append(q.max(1))
   frames.append(fs);lows.append(los);highs.append(his)
  lows=np.array(lows);highs=np.array(highs);cases=[]
  for k,(name,pose) in enumerate(ps):
   pairs=[]
   for i,j in itertools.combinations(range(9),2):
    ov=np.minimum(highs[i,k,:,None,:],highs[j,k,None,:,:])-np.maximum(lows[i,k,:,None,:],lows[j,k,None,:,:])
    count=int((ov>0).all(2).sum())
    if count:pairs.append({'a':ids[i],'b':ids[j],'potential_box_pairs':count})
   cases.append({'pose':name,'angles_deg':pose,'pairs':pairs})
  save(a.out/(ch+'_'+side+'_profile.json'),p)
  records.append({'character':ch,'side':side,'axes':ids,'options':opts,'poses':cases,'module_frames':frames})
 inputs=[a.joint,a.search,a.witness,Path(__file__),R/'scripts/search_revo6_layout.py',H/'cad/model.py']
 save(a.out/'layout_search.json',{'schema':'o6-evidence-refined-layout-v1','changes':['Sternoclavicular pivot +10 mm forward / 20 mm lateral, compensated before shoulder; clavicle hinge gap 24 mm and protraction standoff 12 mm','Forearm twist standoff 24 to 12 mm after side-raise shoulder/forearm collision','Right-side axial polarity mapped through the reference mirror; each actual part remains a proper rotation'],'characters':records,'offsets_mm':cfg,'input_sha256':{p.relative_to(R).as_posix():sha(p) for p in inputs},'physical_tested':False,'manufacturing_released':False})
if __name__=='__main__':main()

