"""Search both core handed orientations and smaller anatomical offsets."""
from common import *
from layout_fullbody import *
from collision_fast import first_cross

def override(delta,flip=0,side='l'):
 sg=1 if side=='l' else -1;W=np.c_[[-1,0,0],[0,0,-sg],[0,-sg,0]]
 if flip:W=W@rot(flip-1,180)
 bs=-1 if W[2,1]*sg<0 else 1;aa=sg*W[0,0];bias=-20 if bs==-1 else -30
 original=read(G3/'layouts/quinn/anatomy_profile.json');_,A=fk(original,{});origin=A['clavicle_'+side+'.protract']['origin']+np.array([delta[0],sg*delta[1],delta[2]])
 off=origin-np.array([-55,sg*38,A['clavicle_'+side+'.protract']['origin'][2]+5])
 return {'F':(W@rot(1,bias)).tolist(),'W':W.tolist(),'beta0':bias,'alpha_sign':aa,'beta_sign':bs,'offset_parent_mm':off.tolist()}

def main():
 cases=[{}, {'clavicle_l.protract':30},{'clavicle_l.protract':-20},{'clavicle_l.elevate':30},{'clavicle_l.elevate':-15},{'clavicle_l.protract':30,'clavicle_l.elevate':30},{'clavicle_l.protract':-20,'clavicle_l.elevate':30},{'upperarm_l.abduct':150},{'upperarm_l.flex':160}]
 positions=list(itertools.product((-36,-24,-12,0,12,24),(12,24,36),(-16,-8,0,8,16)))
 positions.sort(key=lambda x:np.linalg.norm(x));seen=[];winners=[];pairset={frozenset(('clavicle_l',x)) for x in ('upperarm_l','head','chest')}
 for count,(delta,flip) in enumerate(itertools.product(positions,range(4)),1):
  ov={'clavicle_l':override(delta,flip)};reason=None
  for i,ang in enumerate(cases):
   p,m,st,f,pr=build('quinn',ang,overrides=ov,only=['clavicle_l','upperarm_l','head','chest']);hit=first_cross(p,m,pairset)
   if f or hit:reason={'case':i,'collision':hit,'mapping':f};break
  if reason is None:
   winner={'delta_from_reference_mm':delta,'flip':flip,'override':ov,'cases':cases};winners.append(winner);print('CLAV WIN',delta,flip,flush=True)
   save('clavicle_compact_search.json',{'winners':winners,'tested':count,'scope':'Nine sampled poses, left-side nearby modules; full bilateral and connected checks still required.'})
   if len(winners)>=8:break
  if count%80==0:print('CLAV SEARCH',count,'winners',len(winners),flush=True)
 save('clavicle_compact_search.json',{'winners':winners,'tested':count,'scope':'Nine sampled poses, left-side nearby modules; full bilateral and connected checks still required.'})
if __name__=='__main__':main()
