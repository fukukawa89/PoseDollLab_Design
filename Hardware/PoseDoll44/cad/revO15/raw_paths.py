"""Continuous physical-axis interpolation for digital assembly inspection.
Intermediate orientations can leave the semantic capture range; they are never
published as valid captures. Physical stops and actual geometry remain checked.
"""
from common import *
import layout_fullbody as layout
from layout_fullbody import fk
from carriers_swept import ASSEMBLY_POSE
sys.path.insert(0,str(R/'Tools/PoseDollHardwareBridge'))
from o15_kinematics import compose_matrix,decode_rotation


def raw_state(char,qmap,previous=None):
 prof,modules=layout.config(char);axes={n['axis_id']:n['axis_local'] for n in prof['nodes'] if n.get('axis_id')};angles={};outside=[];limits={a['id']:np.rad2deg(a['limits_rad']) for a in prof['axes']}
 for m in modules:
  q=qmap[m['id']];kind=m['kind']
  if kind in ('tut','wide_tut','three_axis'):
   M=np.array(m['F'])@compose_matrix(kind,q)@np.array(m['V']).T;vv=decode_rotation(M,[axes[a] for a in m['axis_ids']],[[-180,180]]*3,previous.get(m['id']) if previous else None)
  elif kind in ('core','clavicle_core','ankle_core'):vv=[m['beta0']-q[1],q[0]/m['alpha_sign']]
  else:vv=[q[0]/m['hinge_sign']]
  for a,v in zip(m['axis_ids'],vv):
   angles[a]=v
   if not limits[a][0]-1e-7<=v<=limits[a][1]+1e-7:outside.append(a)
 names=[m['id'] for m in modules if m['kind'] in ('tut','wide_tut')];counter=[0];old=layout.candidates
 def force(M,max_b=95):
  name=names[counter[0]];counter[0]+=1;return np.array([qmap[name]])
 layout.candidates=force
 try:result=layout.build(char,angles,geometry=False)
 finally:layout.candidates=old
 for m in result[2]:
  if np.max(np.abs(np.array(m['angles_deg'])-qmap[m['id']]))>1e-5:raise ValueError(('raw path changed branch',m['id'],m['angles_deg'],qmap[m['id']]))
 return result,angles,outside


def paths(char,targets=None,step=5):
 cases=read(H/'mechanical_manifest/revO_pose_cases.json')['cases'];start={m['id']:np.array(m['angles_deg']) for m in layout.build(char,ASSEMBLY_POSE,geometry=False)[2]}
 for name,target in cases.items():
  if targets and name not in targets:continue
  end={m['id']:np.array(m['angles_deg']) for m in layout.build(char,target,geometry=False)[2]};n=max(1,int(np.ceil(max(np.max(np.abs(end[k]-start[k])) for k in start)/step)));previous={}
  for i in range(n+1):
   q={k:start[k]+i/n*(end[k]-start[k]) for k in start};(_,meta,st,f,pr),angles,outside=raw_state(char,q,previous);previous={m['id']:[angles[a] for a in m['axis_ids']] for m in st};T,_=fk(pr,angles)
   if f:raise ValueError(f)
   yield name+f'/{i:03}',meta,T,{'target':name,'sample':i,'steps':n,'angles_deg':angles,'raw_angles_deg':{k:v.tolist() for k,v in q.items()},'transit_outside_capture_semantics':outside}

if __name__=='__main__':
 for char in ('quinn','manny'):
  n=0;outside=0
  for label,meta,T,detail in paths(char):n+=1;outside+=bool(detail['transit_outside_capture_semantics'])
  print('RAW PATH',char,n,'out-of-capture transit samples',outside,flush=True)
