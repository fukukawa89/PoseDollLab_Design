"""Retained pairwise packing experiments for O15; no suppressed interferences."""
from common import *
from layout_fullbody import *

def first_cross(p,m,pairs=None):
 bb={k:np.array(s.bounding_box()) for k,s in p.items()}
 for a,b in itertools.combinations(p,2):
  if m[a]['module']==m[b]['module']:continue
  if pairs and frozenset((m[a]['module'],m[b]['module'])) not in pairs:continue
  if m[a]['body']==m[b]['body'] and m[a]['sku'] is None and m[b]['sku'] is None:continue
  ba,bc=bb[a],bb[b]
  if np.any(np.minimum(ba[3:],bc[3:])<=np.maximum(ba[:3],bc[:3])+1e-6):continue
  v=float((p[a]^p[b]).volume())
  if v>1e-4:return {'parts':[a,b],'volume_mm3':v,'bodies':[m[a]['body'],m[b]['body']]}
 return None

def spine():
 poses=[{}]+[{f'waist.{a}':v} for a,vs in [('yaw',(-35,35)),('pitch',(-20,40)),('roll',(-25,25))] for v in vs]
 for side in ('l','r'):
  poses += [{f'thigh_{side}.{a}':v} for a,vs in [('flex',(-30,125)),('abduct',(-25,65)),('twist',(-50,50))] for v in vs]
 out=[]
 for dx in (-65,-70,-75,-80,-85,-90):
  op={'waist':{'offset_parent_mm':[dx,0,-8]},'chest':{'offset_parent_mm':[dx,0,8]}};rr=[]
  for angles in poses:
   p,m,st,f,_=build('quinn',angles,op,only=('waist','thigh_l','thigh_r'));rr.append({'angles':angles,'mapping':f,'hit':first_cross(p,m,pairs={frozenset(('waist','thigh_l')),frozenset(('waist','thigh_r'))})})
  out.append({'dx':dx,'samples':rr,'failures':sum(bool(r['mapping'] or r['hit']) for r in rr)})
  print('spine/hips',dx,out[-1]['failures'],flush=True);save('spine_hip_packing.json',{'ranked':sorted(out,key=lambda r:(r['failures'],abs(r['dx'])))})

def clav():
 out=[]
 for side in ('l','r'):
  names=(f'clavicle_{side}',f'upperarm_{side}');rows=[]
  poses=[{}]+[{names[0]+'.'+a:v} for a,vs in [('protract',(-20,30)),('elevate',(-15,30))] for v in vs]+[{names[1]+'.'+a:v} for a,vs in [('flex',(-50,160)),('abduct',(-30,150)),('twist',(-90,90))] for v in vs]
  for dx,dz in itertools.product((0,-8,-16,-24,-32), (0,8,-8)):
   op={names[0]:{'offset_parent_mm':[dx,0,dz]}};rr=[]
   for ang in poses:
    p,m,st,f,_=build('quinn',ang,op,only=names);rr.append({'angles':ang,'mapping':f,'hit':first_cross(p,m)})
   rows.append({'dx':dx,'dz':dz,'samples':rr,'failures':sum(bool(r['mapping'] or r['hit']) for r in rr)})
   print('clav',side,dx,dz,rows[-1]['failures'],flush=True)
  out.append({'side':side,'ranked':sorted(rows,key=lambda r:(r['failures'],np.hypot(r['dx'],r['dz'])))});save('clavicle_shoulder_packing.json',{'results':out})

if __name__=='__main__':
 if len(sys.argv)>1 and sys.argv[1]=='clav':clav()
 else:spine()
