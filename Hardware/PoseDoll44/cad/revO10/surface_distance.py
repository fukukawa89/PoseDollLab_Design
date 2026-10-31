"""O10 unsigned distance adapter, retaining the complete input surface.
No relative cleaning or normal-orientation containment oracle. Zero-area facets
are represented by their three segments, not dropped. Closed-volume initial
separation is established independently with CSG.
"""
import sys
from pathlib import Path
from types import SimpleNamespace
import numpy as np
import vtk
H=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(H/'cad/revO9'))
from continuous_clearance import Certificate,Node
sys.path.insert(0,str(H/'cad/revO8'))
from mesh_collision import numpy_to_vtk,numpy_to_vtkIdTypeArray

def exact_polydata(t):
 vertices,index=np.unique(t.reshape(-1,3),axis=0,return_inverse=True)
 points=vtk.vtkPoints();points.SetData(numpy_to_vtk(vertices))
 cells=np.c_[np.full(len(t),3,dtype=np.int64),index.reshape(-1,3)]
 ca=vtk.vtkCellArray();ca.SetCells(len(t),numpy_to_vtkIdTypeArray(cells.reshape(-1)))
 poly=vtk.vtkPolyData();poly.SetPoints(points);poly.SetPolys(ca)
 assert poly.GetNumberOfPolys()==len(t)
 return poly

class AllTriangleDistance:
 def __init__(self,triangles):
  t=np.asarray(triangles,dtype=np.float64);assert np.isfinite(t).all()
  regular=np.linalg.norm(np.cross(t[:,1]-t[:,0],t[:,2]-t[:,0]),axis=1)>0
  self.poly=exact_polydata(t[regular]);self.implicit=vtk.vtkImplicitPolyDataDistance();self.implicit.SetInput(self.poly)
  z=t[~regular];self.starts=z[:,[0,1,2],:].reshape(-1,3);self.ends=z[:,[1,2,0],:].reshape(-1,3)
  self.v=self.ends-self.starts;self.v2=(self.v*self.v).sum(1)
  self.counts={'source_facets':len(t),'regular_facets':int(regular.sum()),'degenerate_facets_as_segments':int((~regular).sum()),'discarded_facets':0}
 def EvaluateFunction(self,p):
  p=np.asarray(p);d=abs(float(self.implicit.EvaluateFunction(p)))
  if len(self.starts):
   u=np.clip(((p-self.starts)*self.v).sum(1)/np.where(self.v2>0,self.v2,1),0,1)
   d=min(d,float(np.linalg.norm(self.starts+u[:,None]*self.v-p,axis=1).min()))
  assert np.isfinite(d)
  return d

class UnsignedCertificate(Certificate):
 def __init__(self,a,b):
  self.unsigned=True;self.a=a;self.root=Node(a)
  self.target=SimpleNamespace(distance=AllTriangleDistance(b))
  self.radial_exclusion=self.target.distance.EvaluateFunction([0.,0.,0.])
