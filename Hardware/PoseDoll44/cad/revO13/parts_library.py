"""Keep physical pieces separate: exact per-part CSG after AABB broadphase.
Reported group overlap is a sum of pair volumes, not a union volume. A positive
pair is a witness; a zero sum certifies no pair overlap above numeric resolution.
"""
from solid_ops import *
import itertools
class Intersection:
 def __init__(self, parts): self.parts=parts
 def volume(self): return sum(p.volume() for p in self.parts)
class Parts:
 def __init__(self, parts):
  self.parts=list(parts)
  self.bb=np.array([s.bounding_box() for s in self.parts])
 def bounding_box(self):
  return np.r_[self.bb[:,:3].min(0),self.bb[:,3:].max(0)]
 def transform(self,M): return Parts([s.transform(M) for s in self.parts])
 def __xor__(self,other):
  if not isinstance(other,Parts):other=Parts([other])
  out=[]
  for a,ab in zip(self.parts,self.bb):
   for b,bb in zip(other.parts,other.bb):
    if np.all(np.minimum(ab[3:],bb[3:])-np.maximum(ab[:3],bb[:3])>1e-8):out.append(a^b)
  return Intersection(out)
def library():
 out={};raw={k:from_tri(t) for k,t in np.load(OUT/'printed_core/parts.npz').items()}
 fast=[from_tri(t) for t in np.load(G8/'fastened_core/fasteners.npz').values()]
 out.update(clav_input=Parts([raw['C01']]),clav_ring=Parts([s for k,s in raw.items() if k not in ('C01','C02')]+fast),clav_output=Parts([raw['C02']]))
 for c,side in itertools.product(('manny','quinn'),('l','r')):
  groups={k:[] for k in ('P','C01','ring','C02','D')}
  for k,t in np.load(OUT/'braked_module'/f'{c}_{side}.npz').items():
   role='P' if k.startswith('P_') else 'D' if k.startswith('D_') else k if k in ('C01','C02') else 'ring'
   groups[role].append(from_tri(t))
  groups['ring']+=fast
  out.update({f'{c}_{side}/{k}':Parts(v) for k,v in groups.items()})
 for owner in ('parent','child'):
  out['M4_'+owner]=Parts([from_tri(t) for t in np.load(H/'generated/revO10/runs/o10_20260926_r1/old_modules'/f'M4_{owner}.npz').values()])
 return out
