"""Reuse rigid body collision trees; never decimate validation geometry."""
import numpy as np
import vtk
from common import rot
from mesh_collision import polydata,representatives,compare

class Body:
 def __init__(self,mesh):
  self.mesh=np.asarray(mesh);self.poly=polydata(self.mesh);self.reps=representatives(self.poly)
  self.distance=vtk.vtkImplicitPolyDataDistance();self.distance.SetInput(self.poly)
  self.low=self.mesh.min((0,1));self.high=self.mesh.max((0,1))
  self.corners=np.array([[x,y,z] for x in (self.low[0],self.high[0]) for y in (self.low[1],self.high[1]) for z in (self.low[2],self.high[2])])
  # Read the actual processed cell vertices rather than assuming VTK cell IDs
  # retain exactly the source winding or point order.
  self.faces=np.array([[self.poly.GetPoint(self.poly.GetCell(i).GetPointId(j)) for j in range(3)] for i in range(self.poly.GetNumberOfCells())])
 def bound(self,M,offset=np.zeros(3)):
  p=self.corners@M.T+offset;return p.min(0),p.max(0)

class Pair:
 def __init__(self,a,b):
  self.a=a;self.b=b;self.c=vtk.vtkCollisionDetectionFilter();self.c.SetInputData(0,a.poly);self.c.SetInputData(1,b.poly);self.c.SetCollisionModeToAllContacts();self.c.SetBoxTolerance(0);self.c.SetCellTolerance(0);self.c.SetNumberOfCellsPerNode(2)
  self.t=[vtk.vtkTransform(),vtk.vtkTransform()]
  for i,t in enumerate(self.t):self.c.SetTransform(i,t)
 def check(self,A=np.eye(3),B=np.eye(3),tol=.02,ta=np.zeros(3),tb=np.zeros(3)):
  alo,ahi=self.a.bound(A,ta);blo,bhi=self.b.bound(B,tb)
  if np.any(np.minimum(ahi,bhi)<np.maximum(alo,blo)):return {'status':'CLEAR_BOUNDS'}
  for t,M,offset in zip(self.t,(A,B),(ta,tb)):
   mat=vtk.vtkMatrix4x4();mat.Identity()
   for i in range(3):
    for j in range(3):mat.SetElement(i,j,float(M[i,j]))
   for i in range(3):mat.SetElement(i,3,float(offset[i]))
   t.SetMatrix(mat)
  self.c.Update();contacts=self.c.GetNumberOfContacts()
  for i,(source,target,S,T,st,tt) in enumerate(((self.a,self.b,A,B,ta,tb),(self.b,self.a,B,A,tb,ta))):
   pts=source.reps
   if contacts:
    cells=self.c.GetContactCells(i);ids=np.unique([cells.GetValue(j) for j in range(cells.GetNumberOfValues())]);sel=source.faces[ids];pts=np.concatenate((sel.reshape(-1,3),sel.mean(1),pts))
   query=(pts@S.T+st-tt)@T
   for p,q in zip(pts,query):
    d=float(target.distance.EvaluateFunction(q))
    if d < -tol:return {'status':'PENETRATION','surface_contacts':contacts,'witness_body':i,'witness_world_mm':(p@S.T+st).tolist(),'witness_local_mm':p.tolist(),'signed_distance_mm':d}
  return {'status':'CONTACT_REQUIRES_REVIEW' if contacts else 'CLEAR_NOMINAL_MESH','surface_contacts':contacts}

def regression(meshes):
 pairs=[('C01','C02',0,0),('C01','C02',75,75),('C01','C02',0,100),('C01','C14',0,0),('C02','C15',-30,60)]
 rows=[]
 for x,y,a,b in pairs:
  mats={'C01':np.eye(3),'C02':rot([1,0,0],a)@rot([0,1,0],b),'C14':rot([1,0,0],a),'C15':rot([1,0,0],a)};X,Y=mats[x],mats[y]
  r=Pair(Body(meshes[x]),Body(meshes[y])).check(X,Y);old=compare(meshes[x]@X.T,meshes[y]@Y.T)
  assert (r['status']=='PENETRATION')==(old['status']=='PENETRATION'),(x,y,r,old)
  assert ('REVIEW' in r['status'])==('REVIEW' in old['status']), (x,y,r,old)
  rows.append({'pair':[x,y],'angles':[a,b],'compiled':r,'rebuilt':old})
 return rows
