"""A short bed-rooted support through an existing clearance, searched in full XY at each layer."""
from pathlib import Path
import sys,json,numpy as np,shapely,math,shutil
from scipy.ndimage import minimum_filter
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'scripts'))
from build_revo22_fins import solid,vf,union,md,box
from o22_cross_section_geometry import polygon
from trim_revo22_f4_teeth117 import trial as trim
O=R/'Hardware/PoseDoll44/bench/revO22/a1mini_fins_v4'
def trial(pid,parent,label):
 src=O/'candidates'/pid/parent;dst=O/'candidates'/pid/label;n=dict(np.load(src/'parts'/f'{pid}.npz'));d=json.loads((src/'design'/f'{pid}.json').read_text());s=solid(n['v'],n['f']);fin=solid(n['fin_v'],n['fin_f']);teeth=solid(n['teeth_v'],n['teeth_f']);a=src/'verification/full_bead_contacts_v5.json';a=a if a.exists()else src/'verification/full_bead_contacts_v2.json';q=json.loads(a.read_text());it=json.loads((src/'verification/plate_manifest.json').read_text())['items'][0];M=np.array(it['rotation_matrix']);off=np.array(it['translation_mm']);added=[]
 for issue in q['external_islands']:
  b=issue['bounds_mm'];p=(np.array([(b[0]+b[2])/2,(b[1]+b[3])/2,issue['z_mm']-.1])-off)@M
  if not 2<p[2]<12:continue
  xs=np.arange(p[0]-10,p[0]+10.001,.1);ys=np.arange(p[1]-10,p[1]+10.001,.1);X,Y=np.meshgrid(xs,ys);best=None
  for rise in [.8,1.2,1.8,2.4,3.2]:
   h=math.floor((p[2]-rise)/.2)*.2;levels=np.arange(0,h+.01,.2);history=[];cost=np.zeros(X.shape)
   for j,z in enumerate(levels):
    w=2.4+1.6*max(0,1-z/2);th=1.6+2.4*max(0,1-z/2);rad=math.hypot(w/2,th/2)+.25;ob=polygon(s.slice(float(max(.01,z)))).buffer(rad,quad_segs=8);free=~shapely.contains_xy(ob,X,Y)
    if j:cost=minimum_filter(cost,size=3,mode='constant',cval=np.inf)
    cost=cost+.02*np.hypot(X-p[0],Y-p[1]);cost[~free]=np.inf;history.append(cost.copy())
   endpoints=np.argwhere(np.isfinite(cost)&(np.hypot(X-p[0],Y-p[1])<=3.2));endpoints=sorted(endpoints,key=lambda a:float(cost[tuple(a)]+np.hypot(X[tuple(a)]-p[0],Y[tuple(a)]-p[1])))[:80]
   print('ROUTE185_ENDPOINTS',pid,rise,len(endpoints),flush=True)
   for end in endpoints:
    ij=end.copy();path=[ij.copy()]
    for j in range(len(levels)-2,-1,-1):
     lo=np.maximum(ij-1,0);hi=np.minimum(ij+2,cost.shape);sub=history[j][lo[0]:hi[0],lo[1]:hi[1]];ij=lo+np.array(np.unravel_index(np.argmin(sub),sub.shape));path.append(ij.copy())
    path=path[::-1];pieces=[]
    for j in range(len(levels)-1):
     points=[]
     for k in [j,j+1]:
      z=float(levels[k]);c=np.array([X[tuple(path[k])],Y[tuple(path[k])]]);w=2.4+1.6*max(0,1-z/2);th=1.6+2.4*max(0,1-z/2);points.extend([[c[0]+x,c[1]+y,z]for x in[-w/2,w/2]for y in[-th/2,th/2]])
     pieces.append(md.Manifold.hull_points(np.array(points)))
    core=union(pieces);c=np.array([X[tuple(end)],Y[tuple(end)]]);rootpts=[[c[0]+x,c[1]+y,z]for x in[-.9,.9]for y in[-.65,.65]for z in[h-.25,h+.1]];tippts=[[p[0]+x,p[1]+y,z]for x in[-.45,.45]for y in[-.45,.45]for z in[p[2]+.12,p[2]+.35]];tt=md.Manifold.hull_points(np.array(rootpts+tippts));bite=float((tt^s).volume());root=float((tt^core).volume())
    if not .015<bite<3 or root<.1:continue
    if (core^s).volume()>1e-6 or core.min_gap(s,.5)<.235:continue
    if np.linalg.norm(c-p[:2])>p[2]-h+.5:continue
    best=(core,tt,c,h,bite,root,path);break
   if best:break
  if not best:continue
  core,tt,c,h,bite,root,path=best;fin=fin+core;teeth=teeth+tt;num=len(d['segments'])+1;d['segments'].append({'number':num,'bounds_mm':list(core.bounding_box()),'height_mm':h,'blade_width_mm':4.,'blade_thickness_mm':1.6,'teeth_count':1,'brace_count':0,'on_build_plate':True,'bed_connected_portal':True,'low_compact_passage_fin':True,'minimum_base_leg_width_mm':4.,'modeled_growth_xy_per_z':.7072,'cross_brace_depth_mm':0.,'min_gap_mm':float(core.min_gap(s,.5)),'removal_requires_cutting_portal_crown':True,'removal_instruction':'Cut the short yellow contact, then withdraw the short support through the existing hole; cut into sections if needed.'});rec={'bounds_mm':list(tt.bounding_box()),'part_bite_mm3':bite,'fin_root_mm3':root,'contact_point_mm':p.tolist(),'root_point_mm':[*c,h],'fin_number':num,'neck_xy_mm':[.9,.9],'short_connector_horizontal_reach_mm':float(np.linalg.norm(c-p[:2])),'connector_total_height_mm':p[2]+.35-h+.25,'native_issue':issue};d['teeth'].append(rec);added.append(rec);print('ROUTE185_ADDED',pid,rec,flush=True)
 if not added:print('ROUTE185_NONE',pid,flush=True);return
 for sub in ['parts','design','verification']:(dst/sub).mkdir(parents=True,exist_ok=True)
 n['fin_v'],n['fin_f']=vf(fin);n['teeth_v'],n['teeth_f']=vf(teeth);np.savez_compressed(dst/'parts'/f'{pid}.npz',**n);d.update(support_volume_mm3=float((fin+teeth).volume()),short_bed_passage_supports185=added);(dst/'design'/f'{pid}.json').write_text(json.dumps(d,indent=2));fp=src/'verification/body_change_fit_and_pose.json'
 if fp.exists():shutil.copy2(fp,dst/'verification/body_change_fit_and_pose.json')
 trim(pid,label,label+'_self')
if __name__=='__main__':trial(*sys.argv[1:])
