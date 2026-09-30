"""Discrete torso packing search; only verified samples are reported as clear."""
from common import *
from layout_fullbody import build,frame,module_hits

def hit_first(p,meta):
 g={a:{k:s for k,s in p.items() if meta[k]['module']==a} for a in ('waist','chest')};bb={k:np.array(s.bounding_box()) for k,s in p.items()}
 for a,b in itertools.product(g['waist'],g['chest']):
  ba,bc=bb[a],bb[b]
  if np.any(np.minimum(ba[3:],bc[3:])<=np.maximum(ba[:3],bc[:3])+1e-6):continue
  v=(p[a]^p[b]).volume()
  if v>1e-4:return {'parts':[a,b],'volume_mm3':v}
 return None

def options(dx,ph1,ph2):
 F=frame([1,0,0],[0,1,0]);return {n:{'F':(F@rot(2,ph)).tolist(),'V':(F@rot(2,ph)).tolist(),'offset_parent_mm':[dx*sgn/2,0,0]} for n,ph,sgn in [('waist',ph1,-1),('chest',ph2,1)]}

def main():
 neutral=[];tested=0
 for dx in range(0,49,8):
  for p1,p2 in itertools.product(range(0,360,45),repeat=2):
   pp,meta,states,fail,_=build('quinn',overrides=options(dx,p1,p2),only=('waist','chest'));h=hit_first(pp,meta);tested+=1
   if not h and not fail:neutral.append({'dx_mm':dx,'clocking_deg':[p1,p2],'overrides':options(dx,p1,p2)})
  print('neutral dx',dx,'clear total',len(neutral),flush=True)
 poses=[{}]+[{f'{joint}.{ax}':v} for joint in ('waist','chest') for ax,vs in [('yaw',(-35,35)),('pitch',(-20,30)),('roll',(-20,20))] for v in vs]+[{'waist.pitch':25,'chest.pitch':20},{'waist.yaw':25,'chest.roll':20}]
 ranked=[]
 for i,opt in enumerate(neutral):
  results=[]
  for angles in poses:
   pp,meta,states,fail,_=build('quinn',angles,overrides=opt['overrides'],only=('waist','chest'));h=hit_first(pp,meta);results.append({'angles_deg':angles,'mapping_failures':fail,'collision_witness':h})
  opt['samples']=results;opt['fail_samples']=sum(bool(x['mapping_failures'] or x['collision_witness']) for x in results);ranked.append(opt)
  if (i+1)%10==0:print('motion candidates',i+1,'best',min(x['fail_samples'] for x in ranked),flush=True)
 ranked.sort(key=lambda x:(x['fail_samples'],x['dx_mm']));save('torso_packing_search.json',{'neutral_candidates_tested':tested,'neutral_clear':len(neutral),'ranked':ranked,'continuous_motion_proved':False,'physical_tested':False});print('BEST',[(x['dx_mm'],x['clocking_deg'],x['fail_samples']) for x in ranked[:12]],flush=True)
if __name__=='__main__':main()
