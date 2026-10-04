"""Independent winding-number audit of VTK signed-distance counterexamples."""
from pathlib import Path
import sys,json,hashlib,numpy as np
H=Path(__file__).resolve().parents[2];OUT=H/'generated/revO10/runs/o10_20260926_r1'
sys.path.insert(0,str(H/'cad/revO9'));from rigid_collision import Body
from common import rot
import vtk
from mesh_collision import numpy_to_vtk,numpy_to_vtkIdTypeArray

def winding(t,p):
 a,b,c=(t-p).transpose((1,0,2));la=np.linalg.norm(a,axis=1);lb=np.linalg.norm(b,axis=1);lc=np.linalg.norm(c,axis=1);num=np.einsum('ij,ij->i',a,np.cross(b,c));den=la*lb*lc+(a*b).sum(1)*lc+(b*c).sum(1)*la+(c*a).sum(1)*lb
 return float(np.arctan2(num,den).sum()/(2*np.pi))
def exact_poly(t):
 points=vtk.vtkPoints();points.SetData(numpy_to_vtk(t.reshape(-1,3)));cells=np.c_[np.full(len(t),3,dtype=np.int64),np.arange(len(t)*3).reshape(-1,3)];ca=vtk.vtkCellArray();ca.SetCells(len(t),numpy_to_vtkIdTypeArray(cells.reshape(-1)));poly=vtk.vtkPolyData();poly.SetPoints(points);poly.SetPolys(ca)
 clean=vtk.vtkCleanPolyData();clean.SetInputData(poly);clean.SetToleranceIsAbsolute(True);clean.SetAbsoluteTolerance(0.);clean.Update();return clean.GetOutput()
def main():
 p=OUT/'face_brake/parts.npz';m=dict(np.load(p));old=Body(m['C02']);new=vtk.vtkImplicitPolyDataDistance();new.SetInput(exact_poly(m['C02']));source=json.loads((OUT/'face_brake/continuous_yokes.json').read_text());rows=[]
 for case in source['failed_cells']:
  q=np.array(case['witness_source_mm'])@rot([1,0,0],case['alpha_deg'])@rot([0,1,0],case['beta_deg']);w=winding(m['C02'],q);rows.append({'alpha':case['alpha_deg'],'beta':case['beta_deg'],'query_target_mm':q.tolist(),'winding_number':w,'old_vtk_signed_mm':float(old.distance.EvaluateFunction(q)),'exact_weld_vtk_signed_mm':float(new.EvaluateFunction(q))})
 result={'rows':rows,'source_sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'all_winding_outside':all(abs(r['winding_number'])<1e-6 for r in rows),'scope':'Independent closed-surface solid-angle inside/outside test at all negative-distance witnesses. Not a motion certificate.'};(OUT/'face_brake/distance_sign_audit.json').write_text(json.dumps(result,indent=2)+'\n');print(result['all_winding_outside']);print(rows[:3],flush=True)
if __name__=='__main__':main()
