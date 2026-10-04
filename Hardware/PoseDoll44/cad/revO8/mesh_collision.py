"""Closed-triangle surface crossing checks, with signed-distance penetration witnesses.
A positive result is a geometric witness, not a load/tolerance/manufacture result.
No surface crossing plus no containment certifies only the nominal input mesh pose.
"""
import numpy as np
import vtk
def numpy_to_vtk(a,deep=True):
    a=np.ascontiguousarray(a,dtype=np.float64);tmp=vtk.vtkDoubleArray();tmp.SetNumberOfComponents(a.shape[1] if a.ndim>1 else 1);tmp.SetVoidArray(a.reshape(-1),a.size,1);out=vtk.vtkDoubleArray();out.DeepCopy(tmp);return out
def numpy_to_vtkIdTypeArray(a,deep=True):
    a=np.ascontiguousarray(a,dtype=np.int64);tmp=vtk.vtkIdTypeArray();tmp.SetVoidArray(a,a.size,1);out=vtk.vtkIdTypeArray();out.DeepCopy(tmp);return out
def vtk_to_numpy(a):return np.array([a.GetValue(i) for i in range(a.GetNumberOfValues())],dtype=np.int64)

def polydata(t):
    p=vtk.vtkPoints();p.SetData(numpy_to_vtk(np.asarray(t.reshape(-1,3),dtype=np.float64),deep=True))
    cells=np.c_[np.full(len(t),3,dtype=np.int64),np.arange(len(t)*3,dtype=np.int64).reshape(-1,3)]
    ca=vtk.vtkCellArray();ca.SetCells(len(t),numpy_to_vtkIdTypeArray(cells.reshape(-1),deep=True))
    out=vtk.vtkPolyData();out.SetPoints(p);out.SetPolys(ca)
    clean=vtk.vtkCleanPolyData();clean.SetInputData(out);clean.SetTolerance(1e-8);clean.Update()
    normals=vtk.vtkPolyDataNormals();normals.SetInputConnection(clean.GetOutputPort());normals.ConsistencyOn();normals.AutoOrientNormalsOn();normals.SplittingOff();normals.ComputePointNormalsOff();normals.Update()
    result=vtk.vtkPolyData();result.DeepCopy(normals.GetOutput());return result

def representatives(poly):
    # Test every connected surface, including concatenated fasteners. A single
    # point could miss a separate component completely contained in the other mesh.
    c=vtk.vtkPolyDataConnectivityFilter();c.SetInputData(poly);c.SetExtractionModeToAllRegions();c.ColorRegionsOn();c.Update()
    out=c.GetOutput();regions=out.GetPointData().GetArray('RegionId');seen=set();pts=[]
    for i in range(out.GetNumberOfPoints()):
        rid=int(regions.GetTuple1(i))
        if rid not in seen:seen.add(rid);pts.append(out.GetPoint(i))
    return np.array(pts)

def compare(a,b,tolerance=.02):
    pa,pb=polydata(a),polydata(b)
    c=vtk.vtkCollisionDetectionFilter();c.SetInputData(0,pa);c.SetInputData(1,pb)
    for i in (0,1):q=vtk.vtkTransform();q.Identity();c.SetTransform(i,q)
    c.SetCollisionModeToAllContacts();c.SetBoxTolerance(0);c.SetCellTolerance(0);c.SetNumberOfCellsPerNode(2);c.Update()
    contacts=c.GetNumberOfContacts()
    distances=[]
    for index,(source,target,target_poly) in enumerate([(a,b,pb),(b,a,pa)]):
        distance=vtk.vtkImplicitPolyDataDistance();distance.SetInput(target_poly)
        if contacts:
            cells=vtk_to_numpy(c.GetContactCells(index));selected=source[np.unique(cells)]
            pts=np.concatenate([selected.reshape(-1,3),selected.mean(1),representatives(pa if index==0 else pb)])
        else:pts=representatives(pa if index==0 else pb)
        # Return the first reproducible vertex/centroid witness beyond numerical contact tolerance.
        for p in pts:
            signed=float(distance.EvaluateFunction(p))
            if signed < -tolerance:
                return {'status':'PENETRATION','surface_contacts':contacts,'witness_from':index,'witness_mm':p.tolist(),'signed_distance_mm':signed}
        distances.append(float(distance.EvaluateFunction(source[0,0])))
    return {'status':'CONTACT_REQUIRES_REVIEW' if contacts else 'CLEAR_NOMINAL_MESH','surface_contacts':contacts,'representative_signed_distances_mm':distances}


