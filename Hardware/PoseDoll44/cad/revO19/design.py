"""O19: straighten free leg spans; preserve O18 joint interfaces and kinematics."""
from base import *

def tube(points,r=5):
 s=md.Manifold()
 for a,b in zip(points,points[1:]):s+=beam(a,b,r)+md.Manifold.sphere(r,24).translate(a)+md.Manifold.sphere(r,24).translate(b)
 return s

def at_z(points,z):
 for a,b in zip(points,points[1:]):
  if min(a[2],b[2])-1e-7<=z<=max(a[2],b[2])+1e-7:
   t=(z-a[2])/(b[2]-a[2]);return a+(b-a)*t
 raise ValueError((points,z))

def make():
 p,m,pr,st,prov=load_o18();neutral,tr,st,f,pr=position(p,m,{});T,A=L.fk(pr,{});Ta,_=L.fk(pr,g.ASSEMBLY_POSE)
 rr=g.read(H/'generated/revO15/runs/o15_20260929_r1/carriers_refined/quinn_routing.json');routing={r['body']:r for r in rr['frames']};new={};rows=[]
 for body in ('thigh_l','thigh_r','calf_l','calf_r'):
  key='frame/'+body;B=T[body]@np.linalg.inv(Ta[body]);source=routing[body]
  paths=[np.array([B[:3,:3]@v+B[:3,3] for v in path]) for path in source['paths_world_mm']];original_path=paths[-1]
  side=body[-1];is_thigh=body.startswith('thigh');refxy=A['calf_'+side+'.flex']['origin'][:2];xy=refxy.copy()
  if is_thigh and side=='r':xy[0]+=6
  low,high=(153,198) if is_thigh else (67,110)
  upper,lower=(186,161) if is_thigh else (103,74)
  start=at_z(original_path,high);end=at_z(original_path,low)
  points=np.array([start,[*xy,upper],[*xy,lower],end])
  outside=box([-1000,-1000,-1000],[1000,1000,low])+box([-1000,-1000,high],[1000,1000,1000])
  kept=neutral[key]^outside;s=kept+(tube(points)^box([-1000,-1000,low],[1000,1000,high]))
  assert solid_count(s)==1,(key,mesh_record(s))
  # No geometry changes are allowed near either friction/encoder interface.
  endpoint_change=float(((s-neutral[key])^outside).volume())+float(((neutral[key]-s)^outside).volume())
  assert endpoint_change<1e-4,(key,endpoint_change)
  local=g.move(s,np.linalg.inv(T[body]));new[key]=local
  old_mid=at_z(original_path,(upper+lower)/2);before=float(np.linalg.norm(old_mid[:2]-refxy))
  rows.append({'part':key,'anchor':key,'replaces':[key],'kind':'bone_aligned_free_span','body':body,
   'neutral_path_world_mm':points.tolist(),'old_neutral_main_path_world_mm':original_path.tolist(),
   'central_span_mm':upper-lower,'central_span_radial_offset_mm':float(np.linalg.norm(xy-refxy)),'old_same_midheight_offset_mm':before,
   'joint_centres_changed':False,'diameter_mm':10,'preserved_region_z_mm':['below '+str(low),'above '+str(high)],
   'endpoint_geometry_difference_mm3':endpoint_change,**mesh_record(local)})
  print('O19',key,'aligned',upper-lower,'mm; offset',round(before,3),'->',float(np.linalg.norm(xy-refxy)),'; solids',solid_count(s),'endpoint_delta',endpoint_change,flush=True)
 np.savez_compressed(OUT/'changed_parts.npz',**{k:tri(v) for k,v in new.items()})
 g.write(OUT/'changes.json',{'schema':'POSEDOLL-O19-CHANGES/1','replacements':rows,'removed_stock_parts':[],
 'raw_channels':46,'semantic_dof':41,'kinematics_unchanged':True,'printed_pieces':188,'extra_friction_parts':0,
 'hip_offset_per_side_mm':16,'hip_exact_reference_candidate':'REJECTED_COLLISIONS_IN_SQUAT_AND_ABDUCTION',
 'joint_interface_policy':'Preserve frozen O18 interfaces; only replace free leg beam spans. User O11 friction test accepted, no added friction reserve.',
 'O18_commit':'08e8f8b','O18_tag':'posedoll-o18-prototype-20260930','O18_zip_sha256':g.sha(H/'bench/revO18/PoseDoll_O18_Universal_Design.zip'),
 'physical_tested':False,'manufacturing_release':False})
 return new
if __name__=='__main__':make()
