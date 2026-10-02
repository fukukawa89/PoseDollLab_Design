"""Recheck the old empty rear-PCB target against current arm hardware.
The box remains empty: passing is only a spatial reservation, not routed PCBA.
"""
from clavicle_trial import *
from parts_library import Parts
from fullbody_stage import merged_profile
def main():
 lib=library();bb={k:bounds(s) for k,s in lib.items()};rows=[]
 target=md.Manifold.cube([12,48,48]).translate([-40,-24,0]);tb=bounds(target)
 for char in ('manny','quinn'):
  p=merged_profile(char)
  for st in json.loads((OUT/f'clavicle_trial/{char}_states.json').read_text())['states']:
   T,_=fk(p,st['requested_angles_deg']);F=T['chest'];world=pose(Parts([target]),F[:3,:3],F[:3,3]);b=tb@F[:3,:3].T+F[:3,3];lo,hi=b.min(0),b.max(0);hits=[]
   for o in st['objects']:
    M=np.array(o['frame']);b=bb[o['library']]@M[:3,:3].T+M[:3,3]
    if np.any(np.minimum(hi,b.max(0))<=np.maximum(lo,b.min(0))):continue
    s=pose(lib[o['library']],M[:3,:3],M[:3,3])
    if (v:=(world^s).volume())>1e-4:hits.append({'part':o['id'],'overlap_mm3':v})
   rows.append({'character':char,'pose':st['pose'],'findings':hits})
 save('back_reservation.json',{'complete':True,'chest_local_box_mm':[[-40,-24,0],[-28,24,48]],'cases':rows,'scope':'Old empty 48x48x12 mm target, endpoint screen against current arm hardware only. No torso/neck shell, actual PCB, connectors, fixing bracket, RF or wire qualification.','PCB_manufacturing_released':False})
 print('back-box endpoint failures',sum(bool(r['findings']) for r in rows),'/',len(rows),flush=True)
if __name__=='__main__':main()
