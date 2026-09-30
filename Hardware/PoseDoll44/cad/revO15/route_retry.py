"""Retry a blocked pair with actual alternative port choices, not a new clearance waiver."""
def retry_pair(router,ends,esc,pp,i,j,allow_change_i):
 import numpy as np
 import manifold3d as md
 def options(index):
  seen={tuple(np.round(esc[index][-1],1))};out=[(esc[index],ends[index]['point'],ends[index]['normal'])]
  for point,normal in ends[index]['alternatives']:
   if (pp[ends[index]['part']]^md.Manifold.sphere(router.root,16).translate(point)).volume()<=1:continue
   path=router.escape(point,normal,pp[ends[index]['part']])
   if path is None:continue
   key=tuple(np.round(path[-1],1))
   if key in seen:continue
   seen.add(key);out.append((path,point,normal))
   if len(out)>=12:break
  return out
 js=options(j);ii=options(i) if allow_change_i else [(esc[i],ends[i]['point'],ends[i]['normal'])]
 candidates=sorted([(np.linalg.norm(a[0][-1]-b[0][-1]),a,b) for a in ii for b in js],key=lambda q:q[0])
 for num,(_,a,b) in enumerate(candidates):
  if np.allclose(a[0][-1],esc[i][-1]) and np.allclose(b[0][-1],esc[j][-1]):continue
  if num%12==0:print('PORT RETRY',ends[i]['part'],ends[j]['part'],num,len(candidates),flush=True)
  route=router.path(a[0][-1],b[0][-1])
  if route is None:continue
  for index,e in ((i,a),(j,b)):
   esc[index]=e[0];ends[index]['point']=e[1];ends[index]['normal']=e[2]
  print('PORT RETRY SOLVED',ends[i]['part'],ends[j]['part'],'alternative',num,flush=True)
  return route
 return None
