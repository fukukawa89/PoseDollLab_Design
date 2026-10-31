"""Independent analytical solids challenge the mesh collision classifier."""
import json,itertools
import numpy as np
from reference_assembly import OUT,rot
from mesh_collision import compare

def box(low,high):
 v=np.array(list(itertools.product(*zip(low,high))))
 # Each quad's orientation is corrected outward without relying on VTK.
 qs=[[0,1,3,2],[4,6,7,5],[0,4,5,1],[2,3,7,6],[0,2,6,4],[1,5,7,3]];tris=[]
 for q in qs:
  a=v[q];n=np.cross(a[1]-a[0],a[2]-a[0])
  if np.dot(n,a.mean(0)-v.mean(0))<0:a=a[::-1]
  tris.extend([a[[0,1,2]],a[[0,2,3]]])
 return np.array(tris)

def main():
 a=box([-1,-1,-1],[1,1,1]);cases=[('disjoint',a+[3,0,0],'CLEAR_NOMINAL_MESH'),('face_contact',a+[2,0,0],'CONTACT_REQUIRES_REVIEW'),('edge_contact',a+[2,2,0],'CONTACT_REQUIRES_REVIEW'),('overlap',a+[1.5,.2,.3],'PENETRATION'),('contained',a*.25,'PENETRATION'),('contains',a*3,'PENETRATION'),('rotated',a@rot([0,0,1],37).T+[1.4,.1,.4],'PENETRATION'),('below_penetration_tolerance',a+[1.99,0,0],'CONTACT_REQUIRES_REVIEW')]
 rows=[]
 for name,b,expected in cases:
  for order,x,y in [('ab',a,b),('ba',b,a)]:
   r=compare(x,y);assert r['status']==expected,(name,order,r);rows.append({'name':name,'order':order,'expected':expected,'result':r})
 # A separated first component must not hide another component's containment.
 c=np.concatenate([a+[6,0,0],a*.2]);r=compare(c,a);assert r['status']=='PENETRATION',r;rows.append({'name':'disconnected_hidden_containment','result':r})
 from clearance import certify
 for gap,expected in ((.8,'CERTIFIED_NOMINAL_CLEARANCE'),(.4,'INSUFFICIENT_CLEARANCE')):
  r=certify(a,a+[2+gap,0,0]);assert r['status']==expected,r;rows.append({'name':'clearance_'+str(gap),'result':r})
 (OUT.parent/'collision_regression.json').write_text(json.dumps({'pass':len(rows),'cases':rows},indent=2)+'\n',encoding='utf-8');print('PASS',len(rows))
if __name__=='__main__':main()
