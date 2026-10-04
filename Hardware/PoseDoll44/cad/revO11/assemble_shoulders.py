"""Concurrent TUT shoulder trial preserving neutral anatomical anchors.
Only shoulder stage translations are collapsed. All 51 old named poses per
side, including stress cases, retain their requested angles and orientation.
"""
from pathlib import Path
import sys,json,copy,hashlib,itertools
import numpy as np
H=Path(__file__).resolve().parents[2];R=H.parents[1];OUT=H/'generated/revO11/runs/o11_20260926_r1';G9=H/'generated/revO9/runs/o9_20260926_r1';G7=H/'generated/revO7/runs/o7_20260924_r1/bilateral_current'
sys.path.insert(0,str(H/'cad'));from model import fk,rotation
sys.path.insert(0,str(Path(__file__).parent));from module_frames import matrices,meshes

def profile(char,side):
 p=json.loads((G7/f'{char}_{side}_profile.json').read_text());n={q['id']:q for q in p['nodes']};delta=np.zeros(3)
 for name in [f'upperarm_{side}.abduct_frame',f'upperarm_{side}']:
  delta+=np.array(n[name]['parent_to_axis']['translation_m']);n[name]['parent_to_axis']['translation_m']=[0.,0.,0.]
 n[f'elbow_{side}']['parent_to_axis']['translation_m']=(np.array(n[f'elbow_{side}']['parent_to_axis']['translation_m'])+delta).tolist()
 p['profile_id']=f'o10_{char}_{side}_concurrent_shoulder_trial';p['status']='UNQUALIFIED_GEOMETRY_TRIAL';return p

def build():
 layout=json.loads((G7/'layout_search.json').read_text());records={(c['character'],c['side']):c for c in layout['characters']};paths=json.loads((G9/'bounded_mapping.json').read_text());mapping={(c['character'],c['side']):c for c in paths['characters']};local={};profiles={};checks=[]
 dest=OUT/'shoulder_assembly';dest.mkdir(exist_ok=True)
 for key,rec in records.items():
  char,side=key;p=profile(char,side);old=json.loads((G7/f'{char}_{side}_profile.json').read_text());To,Ao=fk(old,{});T,A=fk(p,{})
  checks.append({'id':'_'.join(key),'neutral_anchor_errors_mm':{n:float(np.linalg.norm(T[n][:3,3]-To[n][:3,3])) for n in [f'upperarm_{side}.flex_frame',f'elbow_{side}',f'hand_{side}',f'hand_tip_{side}']}})
  assert max(checks[-1]['neutral_anchor_errors_mm'].values())<1e-8
  profiles[key]=p;local[key]={axis:np.linalg.inv(Ao[axis]['frame'])@np.array(rec['module_frames'][i][0]) for i,axis in enumerate(rec['axes'])}
  (dest/('_'.join(key)+'_profile.json')).write_text(json.dumps(p,indent=2)+'\n')
 states=[]
 for char in ('manny','quinn'):
  for k,goal in enumerate(records[char,'l']['poses']):
   q={**goal['angles_deg'],**records[char,'r']['poses'][k]['angles_deg']};objects=[];anchors={}
   for side in ('l','r'):
    key=char,side;rec=records[key];T,A=fk(profiles[key],q);maps=mapping[key];mp=maps['paths'][k];assert mp['pose']==rec['poses'][k]['pose']
    # Retained 2 clavicle and 4 elbow/forearm/wrist axes per arm.
    for i in (0,1,5,6,7,8):
     axis=rec['axes'][i];fam=rec['families'][i];M=A[axis]['frame']@local[key][axis];C=M.copy();C[:3,:3]=rotation(A[axis]['direction'],q.get(axis,0))@M[:3,:3]
     for owner,F in [('parent',M),('child',C)]:objects.append({'id':axis+'/'+owner,'module':axis,'library':fam+'_'+owner,'frame':F.tolist()})
    mount=np.array(maps['mount_matrix']);B=T[f'clavicle_{side}'][:3,:3]@mount;origin=A[f'upperarm_{side}.flex']['origin'];qs=mp['angles_deg'][-1];Ms=matrices(qs,mp['zero_offsets_deg'])
    for name,M in Ms.items():
     F=np.eye(4);F[:3,:3]=B@M;F[:3,3]=origin;objects.append({'id':f'TUT_{side}/'+name,'module':f'TUT_{side}','library':f'{char}_{side}/'+name,'frame':F.tolist()})
    anchors[side]={n:T[n][:3,3].tolist() for n in [f'upperarm_{side}.flex_frame',f'elbow_{side}',f'hand_{side}',f'hand_tip_{side}']}
   states.append({'character':char,'pose':goal['pose'],'requested_angles_deg':q,'objects':objects,'anchors_mm':anchors})
 (dest/'states.json').write_text(json.dumps({'neutral_anchor_checks':checks,'states':states,'scope':'Concurrent shoulder rotation plus retained O7 other modules. Real connecting carriers, torso/neck hardware, shell and wires still absent. No full-body acceptance.'},indent=2)+'\n')
 print('states',len(states),'objects',len(states[0]['objects']))
if __name__=='__main__':build()

