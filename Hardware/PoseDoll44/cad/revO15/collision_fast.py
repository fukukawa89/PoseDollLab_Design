"""Vectorized broad phase; the narrow phase is the same exact manifold CSG."""
from common import *

def first_cross(p,m,pairs=None,skip_same_body=False):
 bounds={k:np.array(s.bounding_box()) for k,s in p.items()};groups={}
 for k in p:groups.setdefault(m[k]['module'],[]).append(k)
 arrays={g:np.array([bounds[k] for k in ids]) for g,ids in groups.items()}
 envelopes={g:np.r_[bb[:,:3].min(0),bb[:,3:].max(0)] for g,bb in arrays.items()}
 for ga,gb in itertools.combinations(groups,2):
  if pairs and frozenset((ga,gb)) not in pairs:continue
  aa,ab=envelopes[ga],envelopes[gb]
  if np.any(np.minimum(aa[3:],ab[3:])<=np.maximum(aa[:3],ab[:3])+1e-6):continue
  keys=groups[gb];bb=arrays[gb]
  for a in groups[ga]:
   ba=bounds[a];idx=np.flatnonzero(np.all(np.minimum(ba[3:],bb[:,3:])>np.maximum(ba[:3],bb[:,:3])+1e-6,axis=1))
   for i in idx:
    b=keys[i]
    if skip_same_body and m[a]['body']==m[b]['body']:continue
    if m[a]['body']==m[b]['body'] and m[a]['sku'] is None and m[b]['sku'] is None:continue
    volume=float((p[a]^p[b]).volume())
    if volume>1e-4:return {'parts':[a,b],'volume_mm3':volume,'bodies':[m[a]['body'],m[b]['body']]}
 return None
