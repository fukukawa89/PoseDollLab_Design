"""Opt-in functional review for two measured print-edge reliefs. Does not alter native support limits."""
from pathlib import Path
import json,numpy as np,shapely
from build_revo22_fins import solid,vf,md
from o22_reference_mesh import reference_solid
from o22_cross_section_geometry import polygon
import repair_revo22_f4_guarded_chamfer as ctx
R=Path(__file__).resolve().parents[1];O=R/'Hardware/PoseDoll44/bench/revO22/a1mini_fins_v4'
def criteria(kind,area_fraction,core_loss,added,other_contact_clear,whole_volume,band_width=0):
 if added>1e-6 or not other_contact_clear:return False
 if kind=='stationary_case_edge':return area_fraction>=.995 and core_loss<1e-6 and whole_volume<=5.4
 if kind=='M4_wide_outer_edge':return area_fraction>=.98 and core_loss<1e-6 and band_width>=2.399 and whole_volume<=1.1
 return False

def coaxial_washer_motion(key,target,washer,pose_checks):
 import build_revo22_assembly as assembly
 parts,meta,base,*_=ctx.CACHE;profile=assembly.profile;f0,o0=assembly.owners(base);v=vf(washer)[0];center=v.mean(0);_,Q=np.linalg.eigh(np.cov((v-center).T));axis=Q[:,0]
 poses=[('base',base),('neutral',profile['neutral_raw_deg']),('default',json.loads((ctx.B/'profiles/default_pose.json').read_text())['raw_deg'])]
 for raw,limits in profile['raw_limits_deg'].items():
  for side,val in zip(['min','max'],limits):
   q=profile['neutral_raw_deg'].copy();q[raw]=val;poses.append((raw+'/'+side,q))
 rng=np.random.default_rng(22)
 for j in range(12):poses.append(('combined_'+str(j),{k:float(rng.uniform(*v))for k,v in profile['raw_limits_deg'].items()}))
 assert [x[0]for x in poses]==[x['pose']for x in pose_checks]
 records=[]
 for name,pose in poses:
  f,o=assembly.owners(pose)
  def tf(k):
   m=meta[k];return f[m['body']]@np.linalg.inv(f0[m['body']]) if m['owner']=='rigid_frame'else o[(m['module'],m['owner'])]@np.linalg.inv(o0[(m['module'],m['owner'])])
  rel=np.linalg.inv(tf(key))@tf(target);dc=np.linalg.norm(rel[:3,:3]@center+rel[:3,3]-center);dn=np.linalg.norm(np.cross(rel[:3,:3]@axis,axis));records.append({'pose':name,'center_drift_mm':float(dc),'axis_sine_error':float(dn)})
 ok=all(x['center_drift_mm']<1e-6 and x['axis_sine_error']<1e-8 for x in records)
 return {'passed':ok,'poses':records,'washer_owner':meta[target],'frame_owner':meta[key],'basis':'A circular washer is rotationally invariant about its own measured axis. Relative pose transforms may rotate about that axis, but may not shift its centre or tilt the axis. The continuous 360-degree backing and bearing plane are retained. This classifies a rotating circular contact, not an unrelated moving contact.'}

def assess(pid,label,washer_rows,pose_checks):
 p=O/'candidates'/pid/label;n=np.load(p/'parts'/f'{pid}.npz');d=json.loads((p/'design'/f'{pid}.json').read_text());kind=d.get('functional_edge_relief_review');out=[]
 if kind not in ['stationary_case_edge','M4_wide_outer_edge']:return out
 parts,key,T=ctx.context(d,pid);old=reference_solid(n,d).transform(np.linalg.inv(T)[:3,:]);new=solid(n['v'],n['f']).transform(np.linalg.inv(T)[:3,:]);delta=old-new;added=float((new-old).volume())
 if kind=='M4_wide_outer_edge'and pid in ['W006','W007']:
  target='calf_'+('r'if pid=='W006'else'l')+'.flex/outer_M4_wide';base=next((q for q in washer_rows if q['part']==target),None)
  if base is None:return out
  w=parts[target];v=vf(w)[0];center=v.mean(0);_,Q=np.linalg.eigh(np.cov((v-center).T));axis=Q[:,0];u=Q[:,1];A=np.array([u,np.cross(axis,u),axis]);Ti=np.c_[A,-A@center];w=w.transform(Ti);a=old.transform(Ti);b=new.transform(Ti);wb=w.bounding_box();inner=float(np.linalg.norm(vf(w)[0][:,:2],axis=1).min());rin=inner+.15;rout=rin+2.4;records=[]
  for side in base['contact_sides']:
   if side['original_contact_area_mm2']<.1:continue
   z=side['z'];z0=z-1 if z<wb[2]else z;ring=(md.Manifold.cylinder(1.,rout,rout,160)-md.Manifold.cylinder(1.02,rin,rin,160).translate([0,0,-.01])).translate([0,0,z0]);lost=float(((a-b)^ring).volume());oldvoid=float((ring-a).volume());newvoid=float((ring-b).volume());ok=criteria(kind,side['retained_fraction'],max(lost,oldvoid,newvoid),added,True,float(delta.volume()),rout-rin);records.append({'original_contact_area_mm2':side['original_contact_area_mm2'],'new_contact_area_mm2':side['new_contact_area_mm2'],'retained_fraction':side['retained_fraction'],'same_force_average_pressure_ratio':1/side['retained_fraction'],'continuous_backing_inner_radius_mm':rin,'continuous_backing_outer_radius_mm':rout,'continuous_backing_width_mm':rout-rin,'continuous_backing_depth_mm':1.,'original_missing_backing_mm3':oldvoid,'new_missing_backing_mm3':newvoid,'backing_lost_mm3':lost,'passed':ok})
  same=all(c['same_rigid_motion']for q in pose_checks for c in q['near_removed_material']if c['part']==target)
  motion=coaxial_washer_motion(key,target,parts[target],pose_checks)
  out.append({'part':target,'kind':kind,'qualified':bool(records)and all(q['passed']for q in records)and motion['passed'],'qualified_geometrically_invariant_moving_contact':motion['passed'],'coaxial_motion':motion,'same_rigid_motion_in_all_contact_samples':same,'bearing_sections':records,'scope':'Localized outer-rim entry bevel retains >=98% washer bearing area and an exact continuous 2.4 mm wide by 1 mm deep annular backing. This protects seat plane, bore axis and a complete load path; it does not certify PLA strength, preload, fatigue or washer bending. Other parts and motion contacts remain independently screened.'})
 if kind=='stationary_case_edge'and pid=='X038':
  target='thigh_l/P_case_plus';cap=parts[target];v,f=vf(cap);tri=v[f];cr=np.cross(tri[:,1]-tri[:,0],tri[:,2]-tri[:,0]);area=np.linalg.norm(cr,axis=1)/2;norm=cr/np.maximum(2*area[:,None],1e-30);groups={}
  for j,(nn,tt,aa)in enumerate(zip(norm,tri,area)):
   if aa>1e-7:groups.setdefault(tuple(np.round(np.r_[nn,np.dot(nn,tt[0])],5)),[]).append(j)
  records=[]
  for ids in groups.values():
   nn=norm[ids[0]];origin=tri[ids[0],0];u=np.cross(np.eye(3)[np.argmin(abs(nn))],nn);u/=np.linalg.norm(u);A=np.array([u,np.cross(nn,u),nn]);off=-A@origin;face=shapely.union_all([shapely.Polygon((tt-origin)@A[:2].T)for tt in tri[ids]]);aold=polygon(old.transform(np.c_[A,off]).slice(.002)).intersection(face);anew=polygon(new.transform(np.c_[A,off]).slice(.002)).intersection(face)
   if aold.area<1e-5:continue
   loss=aold.difference(anew);coreloss=float(loss.intersection(face.buffer(-1.)).area);frac=anew.area/aold.area;records.append({'original_contact_area_mm2':aold.area,'new_contact_area_mm2':anew.area,'retained_fraction':frac,'loss_in_face_core_1mm_from_boundary_mm2':coreloss,'passed':criteria(kind,frac,coreloss,added,True,float(delta.volume()))})
  same=all(c['same_rigid_motion']for q in pose_checks for c in q['near_removed_material']if c['part']==target)
  # The original face is clamped by four unchanged M2 case screws. Preserve actual screw/nut envelopes and 0.08 mm clearance.
  fasteners=[k for k in parts if k.startswith('thigh_l/P_case_')and('screw'in k or'nut'in k)];fast=[{'part':k,'removed_material_gap_mm':float(delta.min_gap(parts[k],.2))}for k in fasteners];fast_ok=len([k for k in fasteners if'screw'in k])==4 and all(x['removed_material_gap_mm']>=.08-1e-6 for x in fast)
  out.append({'part':target,'kind':kind,'qualified':bool(records)and all(q['passed']for q in records)and same and fast_ok,'same_rigid_motion_in_all_contact_samples':same,'contact_faces':records,'fastener_clearances':fast,'scope':'Only the outermost 1 mm boundary of the stationary case mating face may lose material; >=99.5% contact area and the complete inner face core remain. Four case screws and their current clearances remain. Shaft, nuts, magnet retainers and other contacts are checked separately. This is a geometric edge chamfer review, not strength/thermal FEA.'})
 for q in out:q.update(removed_volume_mm3=float(delta.volume()),added_volume_mm3=added)
 (p/'verification/functional_edge_reliefs188.json').write_text(json.dumps(out,indent=2));print('FUNCTIONAL_EDGE188',pid,[(x['part'],x['qualified'])for x in out],flush=True);return out

if __name__=='__main__':
 for kind,fraction,width,vol in [('stationary_case_edge',.9973,0,5.078),('M4_wide_outer_edge',.9897,2.4,.989)]:
  assert criteria(kind,fraction,0,0,True,vol,width)
  for kwargs in [dict(area_fraction=.97),dict(core_loss=.0001),dict(added=.01),dict(other_contact_clear=False),dict(whole_volume=100)]:
   a=dict(kind=kind,area_fraction=fraction,core_loss=0,added=0,other_contact_clear=True,whole_volume=vol,band_width=width);a.update(kwargs);assert not criteria(**a)
 assert not criteria('M4_wide_outer_edge',.999,0,0,True,.3,1.)
 print('FUNCTIONAL_EDGE188_NEGATIVE_CONTROLS_PASSED')
