"""Convert Manifold regions without losing islands nested inside holes."""
import numpy as np
from shapely.geometry import Polygon,GeometryCollection
from shapely.ops import unary_union
from shapely import make_valid
def _polygon_fast(cs):
 pieces=[];all_positive=[];all_negative=[];orphan_hole=False
 for region in cs.decompose():
  positive=[];negative=[]
  for ring in region.to_polygons():
   q=np.asarray(ring);area2=np.sum(q[:,0]*np.roll(q[:,1],-1)-np.roll(q[:,0],-1)*q[:,1])
   if len(q)<3 or abs(area2)<1e-15:continue
   (positive if area2>0 else negative).append(q)
  all_positive.extend(positive);all_negative.extend(negative)
  if not positive:
   orphan_hole=orphan_hole or bool(negative)
   continue
  if len(positive)==1:
   p=Polygon(positive[0],negative)
   if not p.is_valid:p=make_valid(p)
   pieces.append(p)
  else:
   # Multiple outer contours can meet at a single point and be reported as one region.
   shells=[Polygon(q) for q in positive];assigned=[[] for _ in shells]
   for hole in negative:
    pt=Polygon(hole).representative_point();parents=[i for i,p in enumerate(shells) if p.covers(pt)]
    assert parents,'Hole has no containing shell'
    owner=min(parents,key=lambda i:shells[i].area);assigned[owner].append(hole)
   for shell,holes in zip(positive,assigned):
    p=Polygon(shell,holes);pieces.append(p if p.is_valid else make_valid(p))
 if orphan_hole:
  # Manifold can return a negative-only component when a hole touches its
  # containing shell at floating-point precision. Keep its subtractive sign.
  # Assign holes globally; then union separate positive islands back in.
  shells=[Polygon(q) for q in all_positive];assigned=[[] for _ in shells]
  assert all(p.is_valid for p in shells),'Invalid shell in signed-contour fallback'
  for ring in all_negative:
   hole=Polygon(ring);assert hole.is_valid
   pt=hole.representative_point()
   parents=[i for i,p in enumerate(shells) if p.covers(pt) and hole.difference(p).area<=1e-8 and p.area>=hole.area]
   assert parents,'Negative contour has no containing shell'
   assigned[min(parents,key=lambda i:shells[i].area)].append(hole)
  pieces=[shell.difference(unary_union(holes)) if holes else shell for shell,holes in zip(shells,assigned)]
 result=unary_union(pieces) if pieces else GeometryCollection()
 assert abs(result.area-cs.area())<=max(1e-5,abs(cs.area())*1e-6),(result.area,cs.area())
 return result



def _polygon_winding_fallback(cs):
 """Node the signed boundaries and retain cells with positive material winding.
 Only topology conversion is repaired. Signed area must still agree with Manifold.
 """
 from shapely.geometry import LineString
 from shapely.ops import polygonize
 from shapely import set_precision
 rings=[np.asarray(q,dtype=float)for q in cs.to_polygons()if len(q)>=3]
 if not rings:return GeometryCollection()
 lines=[LineString(np.vstack([q,q[0]]))for q in rings]
 def winding(p):
  total=0;x,y=p.x,p.y
  for q in rings:
   a=q;b=np.roll(q,-1,axis=0);cross=(b[:,0]-a[:,0])*(y-a[:,1])-(x-a[:,0])*(b[:,1]-a[:,1])
   total+=int(np.sum((a[:,1]<=y)&(b[:,1]>y)&(cross>0))-np.sum((a[:,1]>y)&(b[:,1]<=y)&(cross<0)))
  return total
 for precision in [None,1e-8]:
  network=unary_union(lines if precision is None else[set_precision(g,precision)for g in lines]);cells=list(polygonize(network));out=unary_union([p for p in cells if winding(p.representative_point())>0]);error=abs(out.area-cs.area())
  if out.is_valid and error<=max(1e-5,abs(cs.area())*1e-6):return out
 raise AssertionError(('Signed winding fallback area mismatch',out.area,cs.area()))

def polygon(cs):
 try:return _polygon_fast(cs)
 except AssertionError:return _polygon_winding_fallback(cs)
