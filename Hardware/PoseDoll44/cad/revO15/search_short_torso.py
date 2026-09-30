"""Packing search for the shorter trunk modules, with changed centers in FK."""
from common import *
from layout_fullbody import build,frame
from search_torso import hit_first

def options(dx,dz,ph):
 F=frame([0,1,0],[1,0,0]);return {n:{'F':(F@rot(2,p)).tolist(),'V':(F@rot(2,p)@rot(1,-42)).tolist(),'offset_parent_mm':[s*dx/2,0,s*dz/2]} for n,p,s in [('waist',ph,-1),('chest',ph+180,1)]}
def main():
 neutral=[];poses=[{}]+[{f'{j}.{a}':v} for j in ('waist','chest') for a,vs in [('yaw',(-35,35)),('pitch',(-20,40 if j=='waist' else 30)),('roll',(-25 if j=='waist' else -20,25 if j=='waist' else 20))] for v in vs]+[{'waist.pitch':25,'chest.pitch':20},{'waist.yaw':25,'chest.roll':20}]
 for dz in (0,4,8,12,16):
  for dx,ph in itertools.product((0,8,16,24,32,40),(0,15,-15,30,-30,45,-45,90)):
   op=options(dx,dz,ph);p,m,_,f,_=build('quinn',overrides=op,only=('waist','chest'));h=hit_first(p,m)
   if not h and not f:neutral.append({'dx_mm':dx,'dz_mm':dz,'phase_deg':ph,'overrides':op})
  print('short torso dz',dz,'neutral clear',len(neutral),flush=True)
 ranked=[]
 for i,opt in enumerate(neutral):
  samples=[]
  for angles in poses:
   p,m,_,f,_=build('quinn',angles,overrides=opt['overrides'],only=('waist','chest'));samples.append({'angles_deg':angles,'mapping_failures':f,'collision_witness':hit_first(p,m)})
  opt['samples']=samples;opt['fail_samples']=sum(bool(r['mapping_failures'] or r['collision_witness']) for r in samples);ranked.append(opt)
  if (i+1)%10==0:print('short torso moving',i+1,'best failures',min(r['fail_samples'] for r in ranked),flush=True)
 ranked.sort(key=lambda x:(x['fail_samples'],np.hypot(x['dx_mm'],x['dz_mm'])));save('three_axis_torso_search.json',{'neutral_tested':240,'ranked':ranked,'scope':'Discrete pair layout search; bridges and whole-body clearance not proved'});print('SHORT BEST',[(x['dx_mm'],x['dz_mm'],x['phase_deg'],x['fail_samples']) for x in ranked[:12]],flush=True)
if __name__=='__main__':main()
