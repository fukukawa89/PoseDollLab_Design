import sys,json,shutil,traceback,numpy as np,trimesh
from search_revo22_f5_orientation268 import O,put
from build_revo22_fins import solid,vf,md,union,box
from o22_material_components import material_components
from verify_revo22_x062_removal245 import exact_clear
from verify_revo22_f5_contacts298 import envelope,run as fit
from verify_revo22_f5_geometry292 import run as geo
from audit_revo22_f5_native271 import run as audit
from optimize_revo22_f5_276 import pick

def clear_shape(region,body,dr):
 remaining=(region-body-body.translate(-dr*220)).as_original();bb=np.array(region.bounding_box());v,f=vf(body);delta=-dr*220;count=0
 for tri in v[f]:
  pts=np.r_[tri,tri+delta]
  if np.any(pts.max(0)<bb[:3])or np.any(pts.min(0)>bb[3:]):continue
  norm=np.cross(tri[1]-tri[0],tri[2]-tri[0]);dot=np.dot(norm,delta)
  if abs(dot)<1e-8:continue
  if dot<0:tri=tri[[0,2,1]]
  points=np.r_[tri,tri+delta];faces=np.array([[2,1,0],[3,4,5],[0,1,4],[0,4,3],[1,2,5],[1,5,4],[2,0,3],[2,3,5]],dtype=np.uint64);prism=solid(points,faces)
  remaining=(remaining-prism).as_original();count+=1
  if remaining.is_empty():return remaining
 print('CLEAR405_PRISMS',count,'volume',remaining.volume(),flush=True);return remaining

def create(src,l):
 p='P130';a=O/'candidates'/p/src;b=O/'candidates'/p/l
 if(b/'parts'/f'{p}.npz').exists():return True
 n=dict(np.load(a/'parts'/f'{p}.npz'));d=json.loads((a/'design'/f'{p}.json').read_text());s=solid(n['v'],n['f']);fin=solid(n['fin_v'],n['fin_f']);ts=solid(n['teeth_v'],n['teeth_f']);gn=np.load(a/'verification/strict_magnet_guards.npz');ban=solid(gn['v'],gn['f'])-s;r=json.loads((a/'verification/native_final.json').read_text());it=json.loads((a/'verification/plate_manifest.json').read_text())['items'][0];mv,mf=vf(fin+ts);mesh=trimesh.Trimesh(mv,mf,process=False);xy=np.array([[-1,-1,0],[1,-1,0],[1,1,0],[-1,1,0]]);records=[]
 for q in r['external_islands']+r['critical_external_runs']:
  bb=q['bounds_mm'];p0=(np.array([(bb[0]+bb[2])/2,(bb[1]+bb[3])/2,q['z_mm']])-it['translation_mm'])@np.array(it['rotation_matrix']);success=False
  for depth in [1.6,2.4,4.,5.2]:
   hh,dist,_=trimesh.proximity.closest_point(mesh,[p0-[0,0,depth]]);root=hh[0].copy();root[2]-=.12
   for width in [1.2,1.6]:
    tip=p0+[0,0,.2];mid=tip-[0,0,.65]
    if mid[2]<=root[2]+.2:continue
    pad=union([md.Manifold.hull_points(np.r_[xy*.4+root,xy*.4+mid]),md.Manifold.hull_points(np.r_[xy*.4+mid,xy*width/2+tip])])
    for dr in [root-tip,np.array([0.,0.,-1.])]+[np.array(d['orientation']['matrix'])[:,i]*sg for i in range(3)for sg in[-1.,1.]]:
     dr=dr/np.linalg.norm(dr);free=clear_shape(pad,s,dr)
     if free.volume()<.05 or(free^(fin+ts)).volume()<.02:continue
     embed=envelope(free,pad^s,margin=.18);tt=free+embed
     if(embed.volume()<.005 or(tt^ban).volume()>1e-6 or(tt-s-fin-ts).volume()<.03):continue
     if not exact_clear(tt-s,s,dr*220)[0]:continue
     key='custom405_'+str(len(d.get('local_route_repairs',[]))+len(records));n[key+'_v'],n[key+'_f']=vf(tt);ts+=tt;records.append(dict(kind='extractable_void_contact_341',mesh_key=key,contact_pad=True,target=p0.tolist(),tip=tip.tolist(),root=root.tolist(),neck_xy_mm=[.8,.8],tip_width_mm=width,taper_height_mm=.65,free_vertical_mm=float(tip[2]-root[2]),body_overlap_mm3=float(embed.volume()),stem_removal_vector=dr.tolist(),removal_vector=dr.tolist(),custom_shape_method='Trim only the temporary tooth by exact reverse body sweep, then embed its accessible surface by at most 0.18 mm per axis.'));success=True;break
    if success:break
   if success:break
  print('CLEAR405_TARGET',p0.tolist(),success,flush=True)
 if not records:return False
 for sub in ['parts','design','verification','projects']:(b/sub).mkdir(parents=True,exist_ok=True)
 n['teeth_v'],n['teeth_f']=vf(ts);np.savez_compressed(b/'parts'/f'{p}.npz',**n)
 for fn in ['guards.npz','strict_magnet_guards.npz']:shutil.copy2(a/'verification'/fn,b/'verification'/fn)
 d.update(trial=l,local_route_repairs=d.get('local_route_repairs',[])+records,new_tooth_count=d['new_tooth_count']+len(records),support_volume_mm3=float((fin+ts).volume()));put(b/'design'/f'{p}.json',d);return True
if __name__=='__main__':
 src='ends366_0'
 for i in range(4):
  l='clear405_'+str(i)
  if not create(src,l):break
  q=audit('P130',l)
  if q['native_review_resolved']:
   g=geo('P130',l)
   if g['body_change_fit_and_pose_required']:assert fit('P130',l)['fit_and_pose_geometry_passed']
   assert pick('P130');print('CLEAR405_PASS',l,flush=True);break
  src=l
