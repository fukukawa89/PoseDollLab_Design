"""Search coaxial translations of retained clavicle modules against TUT envelopes.
AABB overlap is a search score, not a collision witness. No pose is removed.
"""
from assemble_shoulders import *
import math

def corners(lo,hi):return np.array(list(itertools.product(*zip(lo,hi))))
def bounds(points,F):
 p=points@F[:3,:3].T+F[:3,3];return p.min(0),p.max(0)
def main():
 states=json.loads((OUT/'shoulder_assembly/states.json').read_text())['states'];manifest={f:json.loads(p.read_text()) for f,p in [('M4',H/'generated/revO6/runs/o6_20260924_r1/joint_M4_validated/manifest.json'),('LP6',H/'generated/revO7/runs/o7_20260924_r1/LP6_current/manifest.json')]}
 oldboxes={}
 for f,m in manifest.items():
  for owner in ('parent','child'):oldboxes[f+'_'+owner]=[corners(np.array(r['bounds_mm'][:3]),np.array(r['bounds_mm'][3:])) for r in m['parts'] if r['owner']==owner]
 tutboxes={};coil=corners([-19.5,-19.5,-44.5],[19.5,19.5,-35.5])
 for ch,side in itertools.product(('manny','quinn'),('l','r')):
  for k,t in meshes(ch+'_'+side).items():
   tutboxes[ch+'_'+side+'/'+k]=[corners(t.min((0,1)),t.max((0,1)))]
   if k in ('P','D'):tutboxes[ch+'_'+side+'/'+k].append(coil)
 candidates=np.arange(-72.,73.,6);results=[]
 for ch,side in itertools.product(('manny','quinn'),('l','r')):
  prof=profile(ch,side);selected=[]
  for stem in ('protract','elevate'):
   axis=f'clavicle_{side}.{stem}';scores=np.zeros(len(candidates));violations=np.zeros(len(candidates),int)
   for state in [s for s in states if s['character']==ch]:
    _,A=fk(prof,state['requested_angles_deg']);direction=A[axis]['direction'];fixed=[]
    for ob in state['objects']:
     if ob['module'].startswith('clavicle'):continue
     lib=ob['library'];F=np.array(ob['frame']);localboxes=tutboxes.get(lib,oldboxes.get(lib))
     fixed.extend(bounds(c,F) for c in localboxes)
    fl=np.array([p[0] for p in fixed]);fh=np.array([p[1] for p in fixed])
    for ob in [o for o in state['objects'] if o['module']==axis]:
     F=np.array(ob['frame']);bl,bh=np.array([bounds(p,F) for p in oldboxes[ob['library']]]).transpose((1,0,2))
     for j,d in enumerate(candidates):
      lo=bl+direction*d;hi=bh+direction*d;ov=np.minimum(hi[:,None,:],fh[None,:,:])-np.maximum(lo[:,None,:],fl[None,:,:])+.3;score=np.prod(np.maximum(ov,0),axis=2).sum();scores[j]+=score;violations[j]+=int(score>0)
      outside=np.maximum(hi[:,2]-500,0).sum()+np.maximum(np.abs(np.r_[lo[:,0],hi[:,0]])-90,0).sum();scores[j]+=outside*1e6
   best=int(np.argmin(scores+np.abs(candidates)*.1));rows=[{'translation_mm':float(d),'overlap_score':float(s),'overlap_group_states':int(n)} for d,s,n in zip(candidates,scores,violations)];selected.append({'axis':axis,'translation_along_world_axis_mm':float(candidates[best]),'score':float(scores[best]),'candidates':rows})
   print(ch,axis,'best',candidates[best],scores[best],flush=True)
  results.append({'character':ch,'side':side,'axes':selected})
 for state in states:
  ch=state['character']
  for side in ('l','r'):
   _,A=fk(profile(ch,side),state['requested_angles_deg']);r=next(x for x in results if x['character']==ch and x['side']==side)
   for choice in r['axes']:
    for ob in state['objects']:
     if ob['module']==choice['axis']:
      F=np.array(ob['frame']);F[:3,3]+=A[choice['axis']]['direction']*choice['translation_along_world_axis_mm'];ob['frame']=F.tolist()
 dest=OUT/'shoulder_assembly';(dest/'relocation_search.json').write_text(json.dumps({'characters':results,'coil_reservation_radius_mm':19.5,'coil_reservation_depth_mm':9,'scope':'Coaxial hardware translation only; axis and anatomical anchor positions unchanged. Fine collision checks, connection shafts, rigidity, torso/neck and service required.'},indent=2)+'\n');(dest/'relocated_states.json').write_text(json.dumps({'states':states},indent=2)+'\n')
if __name__=='__main__':main()
