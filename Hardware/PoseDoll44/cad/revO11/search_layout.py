from clavicle_trial import *

def main():
 lib=library();bb={k:bounds(s) for k,s in lib.items()};rows=[];start=time.time()
 for x,y in itertools.product((-40,-50,-60,-70),(20,26,32,38)):
  findings=[]
  for char in ('manny','quinn'):
   states,_=frames(char,x,y,10)
   for st in states:
    if st['pose'] not in ('neutral','clavicle_l.protract_20','elbow_l.flex_140','clavicle_l.elevate_40'):continue
    world={};bbox={}
    for o in st['objects']:
     F=np.array(o['frame']);world[o['id']]=pose(lib[o['library']],F[:3,:3],F[:3,3]);p=bb[o['library']]@F[:3,:3].T+F[:3,3];bbox[o['id']]=(p.min(0),p.max(0))
    for a,b in itertools.combinations(st['objects'],2):
     if not relevant(a,b):continue
     al,ah=bbox[a['id']];bl,bh=bbox[b['id']]
     if np.any(np.minimum(ah,bh)<=np.maximum(al,bl)):continue
     v=(world[a['id']]^world[b['id']]).volume()
     if v>1e-4:findings.append({'character':char,'pose':st['pose'],'pair':[a['id'],b['id']],'volume_mm3':v})
  row={'x':x,'y':y,'z':10,'hits':len(findings),'overlap_mm3':sum(r['volume_mm3'] for r in findings),'findings':findings};rows.append(row);print(x,y,row['hits'],round(row['overlap_mm3'],2),flush=True)
  save('layout_candidates.json',{'complete':False,'cases':rows,'scope':'Eight risk endpoints per candidate; ranking only, must run all 102 endpoints on chosen layout.'})
 rows.sort(key=lambda r:(r['hits'],r['overlap_mm3']));save('layout_candidates.json',{'complete':True,'cases':rows,'elapsed_s':time.time()-start,'scope':'Eight risk endpoints per candidate; ranking only, must run all 102 endpoints on chosen layout.'});print('best',[(r['x'],r['y'],r['hits']) for r in rows[:3]])
if __name__=='__main__':main()
