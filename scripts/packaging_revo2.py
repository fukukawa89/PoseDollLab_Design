"""Surface-based packaging screen at 480 mm; never equate a corner fit with V2 acceptance."""
from revo2_evidence import *
from study_revo2 import measure_character
from study_revo import anatomy
from model import fk,rotation
import numpy as np,itertools,math

def inside_surface(points,vertices,faces):
 tri=vertices[faces];a,b,c=tri[:,0],tri[:,1],tri[:,2];u=b-a;v=c-a;det=u[:,1]*v[:,2]-u[:,2]*v[:,1];usable=abs(det)>1e-10
 a,u,v,det=a[usable],u[usable],v[usable],det[usable];result=[]
 for point in points:
  y=point[1]+1.371e-7-a[:,1];z=point[2]+2.171e-7-a[:,2]
  s=(y*v[:,2]-z*v[:,1])/det;t=(u[:,1]*z-u[:,2]*y)/det
  hit=(s>=0)&(t>=0)&(s+t<=1)&(a[:,0]+s*u[:,0]+t*v[:,0]>point[0])
  result.append(np.count_nonzero(hit)%2==1)
 return np.array(result)

def main():
 verify,out=run_paths();report=[];scenes={}
 for char in ('manny','quinn'):
  c=measure_character(char);v=c['vertices_mm'];f=np.array(c['geometry']['triangles']);p=anatomy(char,480);T,A=fk(p,{})
  bounds=[]
  for side in ('l','r'):
   start=T['upperarm_'+side][:3,3];end=T['elbow_'+side][:3,3];length=float(np.linalg.norm(end-start));available=length-32
   # Conservatively include board + vertical SH header/housing/straight wire tails,
   # two 1 mm guard allowances. Exact branch housings/loop bend remain separate gates.
   for variant,dimensions in [('distal4',[15.0,28.0,32.0]),('distal4_narrow',[15.0,22.0,38.0])]:
    dims=np.array(dimensions);corners=np.array(list(itertools.product(*[[-d/2,d/2] for d in dims])))
    trials=[]
    for angle in range(0,180,15):
     R=rotation([0,0,1],angle)
     for dx,dy in itertools.product((-3,0,3),repeat=2):
      center=(start+end)/2+[dx,dy,0];pts=corners@R.T+center;inside=inside_surface(pts,v,f)
      trials.append({'angle_deg':angle,'center_mm':center.tolist(),'inside_corners':int(inside.sum()),'corners_mm':pts.tolist()})
    best=max(trials,key=lambda x:x['inside_corners']);bounds.append({'node':'N3' if side=='l' else 'N4','variant':variant,'rigid_owner':'upperarm_'+side,'segment_length_mm':length,'board_axial_available_mm':available,'old_board_only_deficit_mm':max(0,66-available),'new_board_only_deficit_mm':max(0,(30 if variant=='distal4' else 36)-available),'guarded_envelope_axial_margin_mm':available-dims[2],'envelope_dimensions_mm':dims.tolist(),'best_surface_trial':best,'candidates_tested':len(trials),'fit_status':'FAIL_SURFACE_SCREEN' if best['inside_corners']<8 or available<dims[2] else 'PASS_SPARSE_CORNERS_ONLY','exact_mated_pcba_and_swept_cable_check':'BLOCKED_MATING_DATUM_AND_SHOULDER_GEOMETRY'})
  # Three torso boards: two proximal candidates + retained N2. Spacing is explicit,
  # collision with yet-unbuilt nested chest/shoulder mechanisms cannot be tested.
  for name,center,dims in [('N3_prox',T['chest'][:3,3]+[0,20,5],[15,36,54]),('N4_prox',T['chest'][:3,3]+[0,-20,5],[15,36,54]),('N2',T['chest'][:3,3]+[-15,0,-20],[15,40,55])]:
   corners=np.array(list(itertools.product(*[[-d/2,d/2] for d in dims])))+center;inside=inside_surface(corners,v,f)
   bounds.append({'node':name,'rigid_owner':'chest','envelope_dimensions_mm':dims,'center_mm':center.tolist(),'corners_mm':corners.tolist(),'inside_corners':int(inside.sum()),'fit_status':'FAIL_SURFACE_SCREEN' if inside.sum()<8 else 'PASS_SPARSE_CORNERS_ONLY','antenna_metal_keepout':'NOT_RUN_48x21mm_air_keepout_beyond_board_edge','actual_chest_mechanism':'NOT_BUILT'})
  report.append({'character':char,'anchor_mm':480,'placements':bounds,'status':'FAIL_PACKAGING_STUDY' if any(q['fit_status'].startswith('FAIL') for q in bounds) else 'PARTIAL_SCREEN_NOT_V2_PASS','method':'Ray parity against actual skinned neutral Manny/Quinn surface, eight envelope corners; not continuous containment, shell-wall, connector fit or path proof','next_candidate':'A rigid chest packaging search and narrower distal board if necessary; B folded 32 mm board cannot be inferred to fit from A failures','hard_height_limit_changed':False})
  scenes[char]={'surface_vertices':v.tolist(),'surface_triangles':f.tolist(),'placements':bounds,'reference_height_mm':480}
  print(char,[(q['node'],q['fit_status'],q.get('best_surface_trial',{}).get('inside_corners',q.get('inside_corners'))) for q in bounds],flush=True)
 save(verify/'packaging.json',{'characters':report,'V2':'BLOCKED_FULL_PCBA_HARNESS_AND_CHEST_ASSEMBLY','link_study':{'conductors':14,'signal_returns':5,'power_conductors':2,'SCK_Hz':250000,'planned_chest_to_upperarm_max_mm':120,'planned_farthest_total_mm':250,'source_damping_ohm':100,'wire_OD_max_assumed_mm':.8,'bend_radius_study_mm':4,'bundle_equivalent_diameter_packing065_mm':.8*math.sqrt(14/.65),'power_and_tristate':'LVC125 partial power-down/Ioff unqualified; no hot-plug rating','scope':'Length, bend radius and harness topology budgets, not a swept complete route'}})
 save(out/'packaging_scene.json',scenes)
if __name__=='__main__':main()