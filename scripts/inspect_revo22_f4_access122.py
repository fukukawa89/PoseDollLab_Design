"""Read-only feasibility study: small support-access windows in non-contact thin walls."""
from pathlib import Path
import sys,json,numpy as np,trimesh,math
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'scripts'))
from build_revo22_fins import solid,box,union,vf,md
from o22_material_components import material_components
from repair_revo22_f4_guarded_chamfer import context
from o22_reference_mesh import reference_solid
O=R/'Hardware/PoseDoll44/bench/revO22/a1mini_fins_v4'
def inspect(pid,label):
 p=O/'candidates'/pid/label;n=np.load(p/'parts'/f'{pid}.npz');d=json.loads((p/'design'/f'{pid}.json').read_text());f=p/'verification/full_bead_contacts_v4.json';f=f if f.exists()else p/'verification/full_bead_contacts_v2.json';q=json.loads(f.read_text());s=solid(n['v'],n['f']);orig=reference_solid(n,d);tm=trimesh.Trimesh(n['v'],n['f'],process=False);it=json.loads((p/'verification/plate_manifest.json').read_text())['items'][0];M=np.array(it['rotation_matrix']);t=np.array(it['translation_mm']);parts,key,T=context(d,pid);rows=[];seen=[]
 for issue in q['external_islands']+q['critical_external_runs']:
  b=issue['bounds_mm'];point=(np.array([(b[0]+b[2])/2,(b[1]+b[3])/2,issue['z_mm']-.1])-t)@M
  if point[2]>35 or point[2]<2 or any(np.linalg.norm(point-pp)<1 for pp in seen):continue
  seen.append(point);hits,_,fi=tm.ray.intersects_location([[*point[:2],-.1]],[[0,0,1]],multiple_hits=True);hits=[h for h,fid in zip(hits,fi)if tm.face_normals[fid,2]<-.15 and point[2]-1<h[2]<point[2]+.1]
  if not hits:continue
  roof=float(min(hits,key=lambda h:abs(h[2]-point[2]))[2]);height=roof-3.2;w=max(4.,height/5);th=1.6;best=[]
  for angle in range(0,180,15):
   a=math.radians(angle);A=np.array([[math.cos(a),-math.sin(a),0],[math.sin(a),math.cos(a),0],[0,0,1]]);shift=[point[0],point[1],0.];cutter=box([-w/2-.32,-th/2-.32,-.01],[w/2+.32,th/2+.32,height+.32]).transform(np.c_[A,shift]);removed=s^cutter;vol=float(removed.volume())
   if not .00001<vol<min(60.,orig.volume()*.008)-float((orig-s).volume()):continue
   new=s-cutter
   if len(material_components(new))!=len(material_components(s)):continue
   sample=np.arange(max(.1,removed.bounding_box()[2]),removed.bounding_box()[5],.2);loss=[]
   for z in sample:
    area=s.slice(float(z)).area();loss.append(float(removed.slice(float(z)).area()/max(area,1e-9)))
   if max(loss,default=0)>.10:continue
   wr=removed.transform(np.linalg.inv(T)[:3,:]);near=[]
   for k,v in parts.items():
    if k==key:continue
    if wr.min_gap(v,.2)<.199:near.append(k)
   if near:continue
   best.append({'angle_deg':angle,'removed_volume_mm3':vol,'largest_global_layer_area_fraction_removed':max(loss,default=0),'cut_bounds_mm':list(cutter.bounding_box()),'fin_width_mm':w,'fin_thickness_mm':th,'height_mm':height,'roof_mm':roof,'xy_mm':point[:2].tolist(),'assembly_base_clearance_at_least_mm':.199,'remaining_component_count':len(material_components(new))})
  rows.append({'native_issue':issue,'feasible_options':sorted(best,key=lambda a:a['removed_volume_mm3'])[:3]});print('ACCESS122',pid,issue['z_mm'],len(best),best[:1],flush=True)
 out={'id':pid,'label':label,'read_only_model_not_modified':True,'scope':'Candidate windows remove at most 10% of any sampled global XY body section and retain body connectivity; all actual neighboring assembly solids have >=0.199 mm clearance from the removed material in the base pose. This is not a stress test; complete bearing, pose and native checks are still required.','sites':rows};(p/'verification/support_access_window_feasibility122.json').write_text(json.dumps(out,indent=2));return out
if __name__=='__main__':
 for spec in sys.argv[1:]:inspect(*spec.split(':'))
