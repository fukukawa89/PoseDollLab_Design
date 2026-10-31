"""Route a broad bed fin through a collision-free 2D corridor, with a short tapered contact."""
import sys,json,math,shutil,traceback,concurrent.futures,collections
import numpy as np,trimesh,shapely
from scipy.ndimage import binary_erosion
from shapely.geometry import LineString
from search_revo22_f5_orientation268 import O,put
from build_revo22_fins import solid,vf,union,box,md,slab,project_xz,extrude_xz
from o22_cross_section_geometry import polygon
from o22_material_components import material_components
from verify_revo22_x062_removal245 import exact_clear
from audit_revo22_f5_native271 import run as audit
from optimize_revo22_f5_276 import candidates,pick
from verify_revo22_f5_geometry292 import run as geometry
from verify_revo22_f5_contacts298 import run as fit

def create(pid,src,label):
 a=O/'candidates'/pid/src;b=O/'candidates'/pid/label
 if(b/'parts'/f'{pid}.npz').exists():return True
 n=dict(np.load(a/'parts'/f'{pid}.npz'));d=json.loads((a/'design'/f'{pid}.json').read_text());rep=json.loads((a/'verification/native_final.json').read_text());it=json.loads((a/'verification/plate_manifest.json').read_text())['items'][0];M=np.array(it['rotation_matrix']);t=np.array(it['translation_mm']);s=solid(n['v'],n['f']);fin=solid(n['fin_v'],n['fin_f']);ts=solid(n['teeth_v'],n['teeth_f']);gn=np.load(a/'verification/guards.npz');ban=solid(gn['v'],gn['f'])-s;mesh=trimesh.Trimesh(n['v'],n['f'],process=False);records=[];why=collections.Counter();targets=[]
 for q in rep['external_islands']:
  r=q['bounds_mm'];targets.append((np.array([(r[0]+r[2])/2,(r[1]+r[3])/2,q['z_mm']])-t)@M)
 for q in rep['critical_external_runs']:
  l=LineString(q['xy_mm']);count=max(1,int(math.ceil(l.length/2.)));targets +=[(np.r_[l.interpolate(x).coords[0],q['z_mm']]-t)@M for x in(np.arange(count)+.5)*l.length/count]
 unique=[]
 for p in targets:
  if not any(np.linalg.norm(p-q)<.85 for q in unique):unique.append(p)
 def tooth(a,b):
  sq=np.array([[-1,-1,0],[1,-1,0],[1,1,0],[-1,1,0]]);m=a+(b-a)*max(0,1.-.4/(b[2]-a[2]));return union([md.Manifold.hull_points(np.r_[sq*.4+a,sq*.4+m]),md.Manifold.hull_points(np.r_[sq*.4+m,sq*.3+b])])
 for p in unique:
  samples=np.array([[p[0]+dx,p[1]+dy,p[2]-.1]for dx,dy in [(0,0)]+[(r*math.cos(an),r*math.sin(an))for r in [.4,.8,1.4]for an in np.arange(0,2*np.pi,np.pi/4)]])
  cp,dd,fi=trimesh.proximity.closest_point(mesh,samples);contacts=[]
  for h,dist,f in zip(cp,dd,fi):
   norm=mesh.face_normals[f]
   if dist>.8 or norm[2]>.75 or abs(h[2]-p[2])>.8:continue
   tip=h-norm*.35+[0,0,.08];tip[2]=max(tip[2],p[2]+.28)
   if (tooth(tip-[0,0,.1],tip)^ban).volume()>1e-7:continue
   if not any(np.linalg.norm(tip-bb)<.25 for _,bb in contacts):contacts.append((h,tip))
  contacts.sort(key=lambda q:np.linalg.norm(q[0]-p));success=False
  for h,tip in contacts[:12]:
   for gap in [5.2,7.2,3.2,9.2]:
    height=math.floor((h[2]-gap)/.2)*.2
    if height<.6:continue
    for angle in range(0,180,30):
     ang=math.radians(angle);A=np.array([[math.cos(ang),math.sin(ang),0],[-math.sin(ang),math.cos(ang),0],[0,0,1.]]);sp=s.transform(np.c_[A,[0,0,0]]);hp=A@h;bb=np.array(sp.bounding_box());thick=1.2 if height<60 else 1.6
     for shift in [0.,-2.,2.]:
      root=A.T@np.array([hp[0],hp[1]+shift,height-.35]);tt=tooth(root,tip);bite=tt^s
      if not .008<bite.volume()<4 or bite.bounding_box()[2]<h[2]-1.5:why['bite']+=1;continue
      if(tt^ban).volume()>1e-7:why['guard']+=1;continue
      if(tt-(s+fin+ts)).volume()<1e-4:continue
      y=hp[1]+shift;obs=polygon(project_xz(slab(sp,y-thick/2-.4,y+thick/2+.4,bb)).offset(.4,circular_segments=8));x0=max(bb[0]-12,hp[0]-height-12);x1=min(bb[3]+12,hp[0]+height+12);dx=.2;xs=np.arange(x0+.1,x1,dx);zs=np.arange(.1,height+.01,.2);X,Z=np.meshgrid(xs,zs);free=~shapely.contains_xy(obs,X,Z);widths=2.+(max(5.,height*.28)-2.)*(1-zs/height);cost=np.full(len(xs),1e12);parents=np.full(free.shape,-1,dtype=np.int16)
      for j,z in enumerate(zs):
       count=max(3,int(math.ceil(widths[j]/dx)));count+=1-count%2;ok=binary_erosion(free[j],structure=np.ones(count,bool),border_value=0)
       if j==0:cost=np.where(ok,abs(xs-hp[0])*.002,1e12)
       else:
        choices=np.stack([np.r_[1e12,cost[:-1]],cost,np.r_[cost[1:],1e12]]) if j%3==0 else np.stack([cost+1e12,cost,cost+1e12]);sel=np.argmin(choices,axis=0);parents[j]=np.arange(len(xs))+sel-1;cost=np.where(ok,np.min(choices,axis=0)+abs(xs-hp[0])*.0001,1e12)
      k=int(np.argmin(abs(xs-hp[0])))
      if cost[k]>1e10:why['route']+=1;continue
      centers=[]
      for j in range(len(zs)-1,-1,-1):centers.append((xs[k],zs[j],widths[j]));k=int(parents[j,k])if j else k
      centers.reverse();verts=[]
      for x,z,w in centers:verts.append([x-w/2,z])
      for x,z,w in centers[::-1]:verts.append([x+w/2,z])
      verts[0][1]=0;verts[-1][1]=0;profile=md.CrossSection([verts[::-1]]);core=extrude_xz(profile,thick,y);core+=core.slice(.1).offset(.8,circular_segments=8).extrude(.4);core=core.transform(np.c_[A.T,[0,0,0]])
      if(core^s).volume()>1e-7:why['collision']+=1;continue
      if(tt^core).volume()<.02:why['root']+=1;continue
      direction=None
      for dr in [A.T@np.array([0.,1.,0.]),A.T@np.array([0.,-1.,0.]),np.array([0,0,-1.])]:
       if exact_clear(core,s,dr*240)[0]:direction=dr;break
      if direction is None:why['extraction']+=1;continue
      vv=np.r_[n['v'],vf(fin+core)[0],vf(ts+tt)[0]]
      if max(np.ptp(vv,axis=0)[:2])>172:why['bed']+=1;continue
      fin+=core;ts+=tt;records.append(dict(target=h.tolist(),tip=tip.tolist(),root=root.tolist(),neck_xy_mm=[.8,.8],tip_width_mm=.6,taper_height_mm=.4,free_vertical_mm=float(h[2]-root[2]),new_bed_fin=True,removal_vector=direction.tolist(),kind='bent_bed_fin_325',fin_plane_angle_deg=angle));success=True;break
     if success:break
    if success:break
   if success:break
  print('BENT329_TARGET',pid,np.round(p,2).tolist(),success,dict(why),flush=True)
 if not records:return False
 for sub in ['parts','design','verification','projects']:(b/sub).mkdir(parents=True,exist_ok=True)
 n['fin_v'],n['fin_f']=vf(fin);n['teeth_v'],n['teeth_f']=vf(ts);np.savez_compressed(b/'parts'/f'{pid}.npz',**n);shutil.copy2(a/'verification/guards.npz',b/'verification/guards.npz');d.update(trial=label,new_tooth_count=d['new_tooth_count']+len(records),local_route_repairs=d.get('local_route_repairs',[])+records,support_count=len(material_components(fin)),support_volume_mm3=float((fin+ts).volume()),removable_core_may_transit_empty_hardware_space=True);put(b/'design'/f'{pid}.json',d);return True

def run(pid):
 if pick(pid):return(pid,True)
 src=next(q[2]for q in candidates(pid)if not q[4].get('part_body_modified_from_F4')and list((O/'candidates'/pid/q[2]/'projects').glob('*.3mf')))
 for i in range(3):
  label=f'bent329_{i}'
  if not create(pid,src,label):break
  q=audit(pid,label)
  if q['native_review_resolved']:pick(pid);geometry(pid);return(pid,True)
  score=q['external_island_count']*5+sum(x['length_mm']for x in q['critical_external_runs'])
  if score>100:break
  src=label
 return(pid,False)
if __name__=='__main__':
 with concurrent.futures.ProcessPoolExecutor(max_workers=3)as ex:
  fs={ex.submit(run,p):p for p in sys.argv[1:]}
  for f in concurrent.futures.as_completed(fs):
   try:print('BENT329_RESULT',f.result(),flush=True)
   except Exception:traceback.print_exc();print('BENT329_ERROR',fs[f],flush=True)
