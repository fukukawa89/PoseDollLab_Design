"""Refine only CAD-witnessed clashes; retain clear separation from UE calibration."""
from pathlib import Path
import argparse,copy,hashlib,json,sys,itertools
import numpy as np
R=Path(__file__).resolve().parents[1];H=R/'Hardware/PoseDoll44'
sys.path.insert(0,str(R/'scripts'))
from search_revo6_layout import align,make_boxes
from model import fk
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,d):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(d,indent=2)+'\n',encoding='utf-8')
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--large',type=Path,required=True);ap.add_argument('--small',type=Path,required=True);ap.add_argument('--search',type=Path,required=True);ap.add_argument('--out',type=Path,required=True);ap.add_argument('--clavicle-lateral',type=float,default=10);a=ap.parse_args()
 a.large=a.large.resolve();a.small=a.small.resolve();a.search=a.search.resolve();data=json.loads(a.search.read_text());source=[a.large,a.small,a.search,Path(__file__),R/'scripts/search_revo6_layout.py',H/'cad/model.py'];local={'L6':make_boxes(json.loads(a.large.read_text())),'M4':make_boxes(json.loads(a.small.read_text()))}
 out=[]
 for ch in data['characters']:
  c=copy.deepcopy(ch);c['families'][0]='M4';path=a.search.parent/(c['character']+'_'+c['side']+'_profile.json');source.append(path);p=json.loads(path.read_text());side=c['side'];nodes={n['id']:n for n in p['nodes']};sgn=1 if side=='l' else -1
  delta=np.array([0,sgn*a.clavicle_lateral,0])/1000
  for n,sign in [('clavicle_'+side+'.protract_frame',1),('upperarm_'+side+'.flex_frame',-1)]:
   nodes[n]['parent_to_axis']['translation_m']=(np.array(nodes[n]['parent_to_axis']['translation_m'])+sign*delta).tolist()
  p['o6_clavicle_lateral_shift_mm']=a.clavicle_lateral;p['status']='MECHANICAL_TRIAL_NOT_FROZEN_OR_CALIBRATED'
  c['options'][0]['standoff_mm']=20;c['options'][4]['standoff_mm']=16;c['options'][6]['standoff_mm']=12
  for sign in (-1,1):
   for node in ('waist','chest'):
    for axis in ('pitch','roll'):
     c['poses'].append({'pose':f'{node}_{axis}_{sign*30}_arm_side','angles_deg':{f'{node}.{axis}':sign*30,f'upperarm_{side}.abduct':90},'pairs':[]})
  states=[fk(p,q['angles_deg']) for q in c['poses']];frames=[];lows=[];highs=[]
  for i,(axis,opt,fam) in enumerate(zip(c['axes'],c['options'],c['families'])):
   node=next(n for n in p['nodes'] if n.get('axis_id')==axis);fs=[];ll=[];hh=[]
   for T,A in states:
    M=A[axis]['frame'].copy();M[:3,:3]=M[:3,:3]@align(np.array(node['axis_local'])*opt['sign']);M[:3,3]+=M[:3,2]*opt['standoff_mm'];points=local[fam]@M[:3,:3].T+M[:3,3];fs.append(M.tolist());ll.append(points.min(1));hh.append(points.max(1))
   frames.append(fs);lows.append(ll);highs.append(hh)
  c['module_frames']=frames
  lo=np.array(lows);hi=np.array(highs)
  for k,q in enumerate(c['poses']):
   q['pairs']=[]
   for i,j in itertools.combinations(range(9),2):
    v=np.minimum(hi[i,k,:,None,:],hi[j,k,None,:,:])-np.maximum(lo[i,k,:,None,:],lo[j,k,None,:,:]);count=int((v>0).all(2).sum())
    if count:q['pairs'].append({'a':c['axes'][i],'b':c['axes'][j],'potential_box_pairs':count})
  oldp=json.loads(path.read_text());t,_=fk(p,{});old,_=fk(oldp,{})
  c['preserved_neutral_anchor_error_mm']={n:float(np.linalg.norm(t[n][:3,3]-old[n][:3,3])) for n in ['upperarm_'+side+'.flex_frame','elbow_'+side,'hand_'+side+'.flex_frame','hand_tip_'+side]}
  assert max(c['preserved_neutral_anchor_error_mm'].values())<1e-8
  save(a.out/(c['character']+'_'+side+'_profile.json'),p);out.append(c)
 save(a.out/'layout_search.json',{'schema':'o6-refined-mixed-trial-v1','characters':out,'changes':{'protract_family':'M4','protract_standoff_mm':20,'small_twist_standoff_mm':16,'forearm_twist_standoff_mm':12,'clavicle_lateral_offset_mm':a.clavicle_lateral},'input_sha256':{p.relative_to(R).as_posix():sha(p) for p in source},'physical_tested':False,'manufacturing_released':False,'full_mechanical_assembly':False})
if __name__=='__main__':main()

