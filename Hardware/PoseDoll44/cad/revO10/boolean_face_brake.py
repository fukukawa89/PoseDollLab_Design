"""Closed-volume Boolean screening avoids confusing friction-face contact with collision.
This is a nominal mesh/CSG test, not a continuous-path or load certificate.
"""
from solid_ops import *
import itertools,time

def main():
 build=json.loads((OUT/'face_brake/build.json').read_text());assert build['generator_sha256']==sha(Path(__file__).with_name('build_face_brake.py')), 'Stale generated face-brake geometry';p=OUT/'face_brake/parts.npz';raw=dict(np.load(p));mesh={k:from_tri(t) for k,t in raw.items()};fast=np.load(G8/'fastened_core/fasteners.npz');ring=md.Manifold()
 for k,s in mesh.items():
  if k not in ('C01','C02'):ring+=s
 for t in fast.values():ring+=from_tri(t)
 # Regression: adjacent faces have zero intersection, containment is positive,
 # and translating a solid into another produces the known intersection volume.
 a=box([0,0,0],[2,3,4]);assert (a^a.translate([2,0,0])).volume()<1e-9;assert abs((a^a.translate([1,0,0])).volume()-12)<1e-9
 rows=[];start=time.time();poses=list(itertools.product((-28,-25,-15,0,15,25,28),(-98,-96.2,-75,-50,-25,0,25,50,75,96.2,98)))+[(29,0),(-29,0),(0,99),(0,-99),(75,75)]
 for alpha,beta in poses:
  A=rot(0,alpha);B=A@rot(1,beta);shapes={'C01':mesh['C01'],'C02':pose(mesh['C02'],B),'ring':pose(ring,A)};hits=[]
  for x,y in itertools.combinations(shapes,2):
   inter=shapes[x]^shapes[y];vol=inter.volume()
   if vol>1e-5:hits.append({'pair':[x,y],'intersection_mm3':vol,'bounds_mm':list(inter.bounding_box())})
  rows.append({'alpha':alpha,'beta':beta,'findings':hits});print(alpha,beta,[(x['pair'],round(x['intersection_mm3'],5)) for x in hits],flush=True)
  save('face_brake/boolean_motion.json',{'cases':rows,'source_sha256':sha(p),'elapsed_s':time.time()-start,'volume_tolerance_mm3':1e-5,'scope':'Complete nominal closed volume at listed states; intentional zero-volume face contact is retained, not deleted. No continuous or tolerance acceptance.','manufacturing_released':False})
if __name__=='__main__':main()

