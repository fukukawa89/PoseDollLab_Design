"""Refine clavicle relocation against discovered high-abduction failures too."""
from clavicle_trial import *
def main():
 lib=library();bb={k:bounds(s) for k,s in lib.items()};rows=[];start=time.time()
 poses={'neutral','clavicle_l.protract_20','elbow_l.flex_140','clavicle_l.elevate_40','upperarm_l.abduct_120','upperarm_l.abduct_160'}
 for x,y,z in itertools.product((-45,-42,-39),(38,50,62),(-30,-20,-10)):
  findings=[]
  for char in ('manny','quinn'):
   states,_=frames(char,x,y,z)
   for st in states:
    if st['pose'] not in poses:continue
    world={};bbox={}
    for o in st['objects']:
     F=np.array(o['frame']);world[o['id']]=pose(lib[o['library']],F[:3,:3],F[:3,3]);p=bb[o['library']]@F[:3,:3].T+F[:3,3];bbox[o['id']]=(p.min(0),p.max(0))
    for a,b in itertools.combinations(st['objects'],2):
     if not relevant(a,b):continue
     al,ah=bbox[a['id']];bl,bh=bbox[b['id']]
     if np.any(np.minimum(ah,bh)<=np.maximum(al,bl)):continue
     v=(world[a['id']]^world[b['id']]).volume()
     if v>1e-4:findings.append({'character':char,'pose':st['pose'],'pair':[a['id'],b['id']],'volume_mm3':v})
  row={'x':x,'y':y,'z':z,'hits':len(findings),'overlap_mm3':sum(r['volume_mm3'] for r in findings),'findings':findings};rows.append(row)
  save('layout_refinement.json',{'complete':False,'cases':rows})
  print(x,y,z,row['hits'],flush=True)
 rows.sort(key=lambda r:(r['hits'],r['overlap_mm3'],r['y'],abs(r['z']+20)))
 save('layout_refinement.json',{'complete':True,'cases':rows,'scope':'Twelve risk endpoints; all 102 required before acceptance'})
 print('best',rows[0],flush=True)
if __name__=='__main__':main()
