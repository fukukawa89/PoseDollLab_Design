"""Reference rigid transforms recovered from circular/planar features in the TUT mesh.
This is a partial, explicitly labelled reconstruction, not a production assembly.
"""
from pathlib import Path
import numpy as np,json,hashlib
R=Path(__file__).resolve().parents[4];H=R/'Hardware/PoseDoll44'
OUT=H/'generated/revO8/runs/o8_20260925_r1/reference'
def rot(axis,angle):
 a=np.array(axis,float);a/=np.linalg.norm(a);x,y,z=a;K=np.array([[0,-z,y],[z,0,-x],[-y,x,0]]);q=np.deg2rad(angle)
 return np.eye(3)+np.sin(q)*K+(1-np.cos(q))*(K@K)
def tr(M,p):return p@M[:3,:3].T+M[:3,3]
def frame(rotation,origin):
 M=np.eye(4);M[:3,:3]=rotation;M[:3,3]=origin;return M

def circle_center(vertices,axis,guess,radius,level=None):
 cols=[i for i in range(3) if i!=axis];v=vertices.reshape(-1,3);v=v if level is None else v[np.abs(v[:,axis]-level)<1e-4];p=np.unique(v[:,cols],axis=0);p=p[np.abs(np.linalg.norm(p-guess,axis=1)-radius)<.01]
 # Algebraic circle fit uses observed vertices; no nominal center rounding in placement.
 A=np.column_stack([2*p,np.ones(len(p))]);q=np.linalg.lstsq(A,(p*p).sum(1),rcond=None)[0]
 c=q[:2];return c,float(np.sqrt(q[2]+c@c)),float(np.max(np.abs(np.linalg.norm(p-c,axis=1)-radius)))

def restored_core():
 data=np.load(OUT/'component_meshes.npz');fits={};local={};transforms={}
 for name,guess,pivot_z,angle in [('C01',[.5,33.38],-11.09650802612305,-5),('C02',[0,33.33],-13.097915649414062,0)]:
  center,r,res=circle_center(data[name],2,np.array(guess),11.5, -25.09650802612305 if name=='C01' else .902084350585938);origin=np.r_[center,pivot_z];M=frame(rot([0,0,1],angle),[0,0,0]);M[:3,3]=-M[:3,:3]@origin
  local[name]=tr(M,data[name])
  shaft_axis=0 if name=='C01' else 1;other=1-shaft_axis
  pts=np.unique(np.round(local[name].reshape(-1,3),6),axis=0)
  pts=pts[(np.abs(pts[:,shaft_axis]-5.12)<.001)&(np.abs(pts[:,2])<4)][:,[other,2]]
  A=np.c_[2*pts,np.ones(len(pts))];fit=np.linalg.lstsq(A,(pts*pts).sum(1),rcond=None)[0];rad=np.sqrt(fit[2]+fit[:2]@fit[:2]);pin_res=float(np.max(np.abs(np.linalg.norm(pts-fit[:2],axis=1)-rad)))
  assert pin_res<1e-4 and abs(fit[0])<1e-4
  pivot_delta=float(fit[1]);M[2,3]-=pivot_delta
  local[name]=tr(M,data[name]);transforms[name]=M.tolist();fits[name]={'source_cylinder_center_xy':center.tolist(),'outer_radius_mm':r,'fit_max_radial_residual_mm':res,'inferred_pivot_source_z_mm':pivot_z,'z_rotation_deg':angle,'pin_center_adjustment_z_mm':pivot_delta,'final_pivot_source_z_mm':pivot_z+pivot_delta,'journal_section_radius_mm':float(rad),'journal_fit_max_error_mm':pin_res}
 for name,center_z,ang in [('C14',-22.5998711586,90),('C15',-1.3790488243,-90)]:
  source=data[name];origin=np.array([0,source[:,:,1].max(),center_z]);M=frame(rot([1,0,0],ang),[0,0,0]);M[:3,3]=-M[:3,:3]@origin;local[name]=tr(M,source);transforms[name]=M.tolist()
 return local,transforms,fits

def at_pose(local,alpha=0,beta=0):
 A=rot([1,0,0],alpha);B=A@rot([0,1,0],beta)
 return {name:mesh@(np.eye(3) if name=='C01' else A if name in ('C14','C15') else B).T for name,mesh in local.items()}

def main():
 local,transforms,fits=restored_core();np.savez_compressed(OUT/'core_neutral.npz',**local)
 data={'status':'PARTIAL_REFERENCE_RECONSTRUCTION','original_component_ids':list(local),'transforms_from_print_file':transforms,'feature_fits':fits,
 'scope':'Two original yokes and both original intermediate ring halves. Connector housings, retaining rings, fasteners, electronics and harness not yet included.',
 'input_sha256':{'component_meshes.npz':hashlib.sha256((OUT/'component_meshes.npz').read_bytes()).hexdigest()},
 'joint_axes':[{'axis':[1,0,0],'origin_mm':[0,0,0],'parent':'C01','child':['C14','C15']},{'axis':[0,1,0],'origin_mm':[0,0,0],'parent':['C14','C15'],'child':'C02'}],
 'physical_tested':False,'manufacturing_released':False}
 (OUT/'assembly_recovery.json').write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
 print(json.dumps({'fits':fits,'bounds':{n:[*m.min((0,1)),*m.max((0,1))] for n,m in local.items()}}))
if __name__=='__main__':main()



