"""O22 collision-free, separable contour fins. Source meshes are never edited.
The prescriptions specify rib direction, spacing, breakup length, and protected
functional volumes. No Bambu-generated supports are used.
"""
from pathlib import Path
import argparse, json, math, time, collections, copy, struct, sys
import numpy as np
import manifold3d as md
from pack_revo22_a1mini import read_mesh
R=Path(__file__).resolve().parents[1]; B=R/'Hardware/PoseDoll44/bench/revO22'; O=B/'a1mini_fins'
D=B/'a1mini_supports/design'
sys.path.insert(0,str(R/'.local/fins-deps'))
import shapely
from shapely.geometry import Polygon, LineString
from shapely.ops import unary_union
GAP=.28; THICK=.8; FOOT=.2
def put(p,x):
 p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(x,ensure_ascii=False,indent=2),encoding='utf-8')
def solid(v,f): return md.Manifold(md.Mesh64(np.asarray(v,dtype=np.float64),np.asarray(f,dtype=np.uint64)))
def vf(s):
 m=s.to_mesh64();return np.array(m.vert_properties[:,:3]),np.array(m.tri_verts)
def box(lo,hi): return md.Manifold.cube(np.array(hi)-lo).translate(lo)
def union(ss):return md.Manifold.batch_boolean(ss,md.OpType.Add) if ss else md.Manifold()
def cs_union(ss):return md.CrossSection.batch_boolean(ss,md.OpType.Add) if ss else md.CrossSection()
def slab(s,y0,y1,bounds):
 lo=np.array(bounds[:3])-3;hi=np.array(bounds[3:])+3;lo[1]=y0;hi[1]=y1
 return s^box(lo,hi)
def project_xz(s):
 if s.is_empty():return md.CrossSection()
 return s.rotate([-90,0,0]).project()
def extrude_xz(cs,thick,y):
 return cs.extrude(thick).rotate([90,0,0]).translate([0,y+thick/2,0])
def protected(vols):
 out=[]
 for vol in vols:
  m=.15
  if vol['shape']=='box':s=box(np.array(vol['min_mm'])-m,np.array(vol['max_mm'])+m)
  else:
   rad=vol['radius_mm']*(1/math.cos(math.pi/6) if 'nut' in vol['feature'].lower() else 1)+m
   z0,z1=vol['z_mm'];s=md.Manifold.cylinder(z1-z0+2*m,rad,rad,64).translate([0,0,z0-m])
  out.append(s.transform(np.array(vol['local_to_source_print_matrix'])[:3,:]))
 return union(out)
def strip_targets(tris,y):
 polys=[]
 for tri in tris:
  if y<tri[:,1].min()-1e-7 or y>tri[:,1].max()+1e-7:continue
  hits=[]
  for i,j in [(0,1),(1,2),(2,0)]:
   a,b=tri[i],tri[j]
   if abs(b[1]-a[1])<1e-9:continue
   t=(y-a[1])/(b[1]-a[1])
   if -1e-8<=t<=1+1e-8:hits.append(a+t*(b-a))
  if len(hits)<2:continue
  hits.sort(key=lambda p:p[0]);a,b=hits[0],hits[-1]
  if b[0]-a[0]<.01 or max(a[2],b[2])<.48:continue
  # Continuous target roof; exact band silhouette enforces clearance.
  polys.append(md.CrossSection([[(a[0],0),(b[0],0),(b[0],max(.001,b[2]-GAP)),(a[0],max(.001,a[2]-GAP))]]))
 return cs_union(polys)
def write_stl(path,s):
 v,f=vf(s);tri=v[f];norm=np.cross(tri[:,1]-tri[:,0],tri[:,2]-tri[:,0]);length=np.linalg.norm(norm,axis=1);norm/=np.maximum(length[:,None],1e-30)
 records=np.zeros(len(f),dtype=[('n','<f4',(3,)),('v','<f4',(3,3)),('a','<u2')]);records['n']=norm;records['v']=tri
 path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(b'O22-F1 removable contour support - mm'.ljust(80,b' ')+struct.pack('<I',len(f))+records.tobytes())
def prescription(pid,part):
 if 'sensor_cassette' in part:return dict(family='cassette',axis=0,pitch=2.4,segment=8.,reason='Low rail: one-layer peel-out shims, no tines on spring or rail')
 if 'case_plus' in part:return dict(family='half_case',axis=0,pitch=3.,segment=9.,reason='Split ribs outside bearing and PCB cavities')
 if part.endswith('/C01'):return dict(family='fork_C01',axis=0,pitch=3.,segment=11.,reason='Ribs under platform and outer fork ears; withdraw sideways')
 if part.endswith('/C02'):return dict(family='fork_C02',axis=90,pitch=3.,segment=11.,reason='Ribs under platform and outer fork ears; withdraw sideways')
 if part.endswith('/C14'):return dict(family='ring_C14',axis=0,pitch=3.,segment=10.,reason='Segmented outer ring cradle, protected fastener entries')
 return dict(family='frame',axis=90 if pid in ['X046','X038','W006','W007'] else 0,pitch=4.,segment=12.,reason='Segmented ribs under exposed load-bearing frame; no enclosed supports')
def sweep2d(cs,delta):
 delta=np.array(delta,dtype=float);polys=[cs,cs.translate(delta)]
 for loop in cs.to_polygons():
  for a,b in zip(loop,np.roll(loop,-1,axis=0)):
   poly=np.array([a,b,b+delta,a+delta])
   signed=np.sum(poly[:,0]*np.roll(poly[:,1],-1)-poly[:,1]*np.roll(poly[:,0],-1))/2
   if abs(signed)>1e-9:polys.append(md.CrossSection([poly if signed>0 else poly[::-1]]))
 return cs_union(polys)
def exit_clear(core,foot,s,axis,sign):
 bb=core.bounding_box();sb=s.bounding_box()
 distance=abs((sb[axis+3]+3-bb[axis]) if sign>0 else (bb[axis+3]-sb[axis]+3))
 delta=sign*distance
 profile=project_xz(core)
 if axis==1:
  lo=bb[1]+min(0,delta);hi=bb[4]+max(0,delta)
  swept=extrude_xz(profile,hi-lo,(hi+lo)/2)
 else:
  d=[delta,0] if axis==0 else [0,delta]
  swept=extrude_xz(sweep2d(profile,d),bb[4]-bb[1],(bb[1]+bb[4])/2)
 if (swept^s).volume()>1e-6:return False
 if not foot.is_empty():
  fp=foot.project()
  if axis==2:
   swept=fp.extrude(.2+distance).translate([0,0,min(0,delta)])
  else:
   d=[delta,0] if axis==0 else [0,delta];swept=sweep2d(fp,d).extrude(.2)
  if (swept^s).volume()>1e-6:return False
 return True
def intervals(cs,y):
 xs=[]
 for p in cs.to_polygons():
  for a,b in zip(p,np.roll(p,-1,axis=0)):
   if (a[1]<=y<b[1]) or (b[1]<=y<a[1]):
    xs.append(a[0]+(y-a[1])*(b[0]-a[0])/(b[1]-a[1]))
 xs.sort();return list(zip(xs[::2],xs[1::2]))
def make_teeth(body,s,ban,spec,part):
 # Explicitly exclude all precision ring, bearing shell and thin spring families.
 if body.is_empty() or spec['family'] not in ['fork_C01','fork_C02','frame']:return md.Manifold(),[]
 bb=s.bounding_box();lower=17.2 if 'fork_' in spec['family'] else 4.2
 teeth=[];records=[];used=[]
 for z in np.arange(lower,bb[5]-1,4.):
  z=round(z/.2)*.2
  cs=s.slice(z+.1);bs=body.slice(z+.1)
  if cs.is_empty() or bs.is_empty():continue
  for y in np.arange(bb[1]+1,bb[4]-1,1.2):
   pi=intervals(cs,y);fi=intervals(bs,y)
   for a,b in fi:
    for l,r in pi:
     for finend,wall,sgn,depth in [(b,l,1,r-l),(a,r,-1,r-l)]:
      d=sgn*(wall-finend)
      if not .20<d<.85 or depth<2.:continue
      if any(np.linalg.norm(np.array([wall,y,z])-q)<7 for q in used):continue
      # The anchor must have 1.6 mm of solid behind it and 0.8 mm vertically.
      x0,x1=sorted([wall+sgn*.15,wall+sgn*1.75])
      probe=box([x0,y-.3,z-.3],[x1,y+.3,z+.5])
      if (probe^s).volume()<probe.volume()*.98:continue
      x0,x1=sorted([finend-sgn*.16,wall+sgn*.08])
      t=box([x0,y-.3,z],[x1,y+.3,z+.2])
      bite=(t^s).volume()
      if bite<.001 or bite>.02 or (t^ban).volume()>1e-7 or (t^body).volume()<.002:continue
      teeth.append(t);used.append(np.array([wall,y,z]));records.append(dict(bounds_mm=list(t.bounding_box()),layer_height_mm=.2,width_mm=.6,nominal_bite_mm=.08,actual_bite_mm3=float(bite),note='Cut yellow tooth first; fin body has zero penetration.'))
      if len(teeth)>=12:return union(teeth),records
 return union(teeth),records

def closed_hole_guard(s):
 guards=[];count=0
 for angles in [[0,-90,0],[90,0,0],[0,0,0]]:
  a=s.rotate(angles);bb=a.bounding_box()
  for h in np.arange(bb[2]+.2,bb[5],1.):
   for loop in a.slice(float(h)).to_polygons():
    signed=float(np.sum(loop[:,0]*np.roll(loop[:,1],-1)-loop[:,1]*np.roll(loop[:,0],-1))/2)
    if -650<signed<-1.2:
     # Closed small cavities: protect the full loop, including polygon corners.
     g=md.CrossSection([loop[::-1]]).offset(.18,circular_segments=12).extrude(1.4).translate([0,0,float(h)-.7])
     g=g.rotate([-x for x in angles]);guards.append(g);count+=1
 return union(guards),count

def polygon(cs):
 pos=[];neg=[]
 for p in cs.to_polygons():
  area=np.sum(p[:,0]*np.roll(p[:,1],-1)-p[:,1]*np.roll(p[:,0],-1))/2
  (pos if area>0 else neg).append(Polygon(p))
 return unary_union(pos).difference(unary_union(neg))
class BedRoutes:
 # Fin-plane reachability: every branch rises at >=45 degrees from a bed root.
 def __init__(self,avoid,bounds):
  self.step=.2;self.radius=.4;self.xs=np.arange(bounds[0]-5,bounds[3]+5,self.step);self.zs=np.arange(self.radius,bounds[5]+.1,self.step)
  xx,zz=np.meshgrid(self.xs,self.zs)
  clear=~shapely.intersects_xy(polygon(avoid).buffer(self.radius+.015),xx,zz)
  self.prev=np.zeros(clear.shape,dtype=np.int8);reach=clear[0];self.prev[0,reach]=2
  for k in range(1,len(self.zs)):
   left=np.r_[False,reach[:-1]];right=np.r_[reach[1:],False]
   choices=np.where(reach,2,np.where(left,1,np.where(right,3,0))).astype(np.int8)
   choices[~clear[k]]=0;self.prev[k]=choices;reach=choices!=0
 def connect(self,cs):
  inner=polygon(cs).buffer(-self.radius-.025)
  if inner.is_empty:return None
  lo=inner.bounds;indices=np.where((self.xs>=lo[0])&(self.xs<=lo[2]))[0]
  edges=set();endpoints=[];roots=set()
  # Cover every upper contact interval, with 0.6-mm sampling across the fin.
  for i in indices[::3]:
   x=self.xs[i];cut=inner.intersection(LineString([(x,lo[1]-1),(x,lo[3]+1)]))
   lines=list(cut.geoms) if hasattr(cut,'geoms') else [cut]
   for line in lines:
    if line.is_empty or line.geom_type!='LineString':continue
    zlo,zhi=line.bounds[1],line.bounds[3]
    js=np.where((self.zs>=zlo)&(self.zs<=zhi)&(self.prev[:,i]!=0))[0]
    if not len(js):continue
    j=int(js[-1]);k=int(i);endpoints.append((float(x),float(zhi),j,k))
    while j>0:
     choice=self.prev[j,k];nk=k+(-1 if choice==1 else 1 if choice==3 else 0)
     edges.add((j,k,j-1,nk));j-=1;k=nk
    roots.add(k)
  if not endpoints:return None
  # Continuous path walls, not a ceiling with downward dangling fragments.
  polys=[];vertices=set()
  def segment(a,b):
   d=b-a
   if np.linalg.norm(d)<1e-8:return
   perp=np.array([-d[1],d[0]])/np.linalg.norm(d)*self.radius
   polys.append(md.CrossSection([np.array([a+perp,b+perp,b-perp,a-perp])[::-1]]))
  # Merge same-direction lattice runs before boolean union.
  starts={(j,k) for j,k,_,_ in edges};used=set()
  for edge in sorted(edges,reverse=True):
   if edge in used:continue
   j,k,nj,nk=edge;used.add(edge);a=np.array([self.xs[k],self.zs[j]]);dx=nk-k
   while (nj,nk,nj-1,nk+dx) in edges and (nj,nk,nj-1,nk+dx) not in used:
    used.add((nj,nk,nj-1,nk+dx));nj,nk=nj-1,nk+dx
   b=np.array([self.xs[nk],self.zs[nj]]);segment(a,b);vertices.add(tuple(a));vertices.add(tuple(b))
  for x,z,j,k in endpoints:
   a=np.array([self.xs[k],self.zs[j]]);b=np.array([x,z]);segment(a,b);vertices.add(tuple(b))
  for q in vertices:
   q=np.array(q);pts=q+self.radius*np.c_[np.cos(np.arange(12)*math.pi/6),np.sin(np.arange(12)*math.pi/6)]
   polys.append(md.CrossSection([pts]))
  for k in roots:polys.append(md.CrossSection.square([self.radius*2,self.radius+.1]).translate([self.xs[k]-self.radius,0]))
  return cs_union(polys)

def build_one(pid,item,dec,candidate,extra,vols):
 v,f=read_mesh(B/item['source_3mf']);s=solid(v,f);assert str(s.status())=='Error.NoError'
 spec=prescription(pid,item['part']);angle=spec['axis'];sw=s.rotate([0,0,angle]);vw=v@np.array([[math.cos(math.radians(angle)),-math.sin(math.radians(angle)),0],[math.sin(math.radians(angle)),math.cos(math.radians(angle)),0],[0,0,1]]).T
 holeguard,hole_count=closed_hole_guard(s) if dec['support_strategy'].startswith('external_') and spec['family']!='cassette' else (md.Manifold(),0)
 allban=protected(vols)+holeguard
 forbidden=allban.rotate([0,0,angle]);bounds=sw.bounding_box()
 indices=sorted(set(candidate['external_downward_candidate_faces'])|set(extra))
 tris=vw[f[indices]]
 chunks=[];records=[];rejected=collections.Counter();roof_area=0
 if not dec['support_strategy'].startswith('external_'):indices=[];tris=np.empty((0,3,3))
 y0,y1=bounds[1],bounds[4];ys=np.arange(y0+THICK/2+.3,y1,spec['pitch'])
 # Cassette low rails need exactly one printable layer, and a graspable strip.
 for row,y in enumerate(ys):
  target=strip_targets(tris,y)
  if target.is_empty():continue
  silhouette=project_xz(slab(sw,y-THICK/2-GAP,y+THICK/2+GAP,bounds)).offset(GAP,circular_segments=12)
  ban=project_xz(slab(forbidden,y-THICK/2-.05,y+THICK/2+.05,bounds)) if not forbidden.is_empty() else md.CrossSection()
  available=target-silhouette-ban
  if available.is_empty():continue
  routes=None
  for x in np.arange(bounds[0]-.1,bounds[3],spec['segment']+.8):
   window=md.CrossSection.square([spec['segment'],bounds[5]+5]).translate([x,0])
   seg=available^window
   for small in seg.decompose():
    if small.area()<.24:continue
    rib=extrude_xz(small,THICK,float(y));bb=rib.bounding_box()
    # Quantize tiny bed supports to a complete 0.20-mm first layer.
    if bb[5]<.6:
     if bb[2]>.001 or bb[5]<.2-1e-7:rejected['below_one_layer']+=1;continue
     rib=box([bb[0],y-THICK/2,0],[bb[3],y+THICK/2,.2])
     # Contact gap and functional exclusions are still enforced.
     if (rib^sw).volume()>1e-6 or (rib^forbidden).volume()>1e-6:continue
    routed=False
    if (rib.bounding_box()[5]>.8 and spec['family']!='cassette') or rib.bounding_box()[2]>1e-5:
     if routes is None:routes=BedRoutes(silhouette+ban,bounds)
     rooted=routes.connect(small)
     if rooted is None:rejected['no_bed_route']+=1;continue
     rib=extrude_xz(rooted,THICK,float(y));bb=rib.bounding_box();routed=True
     if bb[2]>1e-5 or len(rib.decompose())!=1:rejected['route_disconnected']+=1;continue
    core=rib;foot=md.Manifold()
    # Broad, thin feet; only around actual bed-contacting rib sections.
    if bb[2]<1e-5:
     footprint=rib.slice(.01).offset(1.4,circular_segments=12)
     nearby=(sw^box([bounds[0]-5,bounds[1]-5,0],[bounds[3]+5,bounds[4]+5,.2+GAP])).project().offset(.45,circular_segments=12)
     foot=(footprint-nearby).extrude(.2)
     if not forbidden.is_empty():foot=foot-forbidden
     rib=rib+foot
    if (rib^sw).volume()>1e-6 or (rib^forbidden).volume()>1e-6:rejected['collision']+=1;continue
    # Continuous swept-volume tests in six cardinal directions.
    direction=None
    for axis,sign in [(1,-1),(1,1),(0,-1),(0,1),(2,-1),(2,1)]:
     if exit_clear(core,foot,sw,axis,sign):
      direction=np.eye(3)[axis]*sign;break
    if direction is None:rejected['no_straight_exit']+=1;continue
    gap=float(rib.min_gap(sw,.5))
    if gap<.195:rejected['gap_under_0_195']+=1;continue
    chunks.append(rib.rotate([0,0,-angle]))
    records.append(dict(number=len(chunks),rib_row=row,min_gap_mm=gap,volume_mm3=float(rib.volume()),bounds_mm=list(rib.rotate([0,0,-angle]).bounding_box()),removal_vector=direction@np.array([[math.cos(math.radians(-angle)),math.sin(math.radians(-angle)),0],[-math.sin(math.radians(-angle)),math.cos(math.radians(-angle)),0],[0,0,1]]),on_build_plate=bool(bb[2]<1e-5),routed_to_bed=routed))
 bodies=union(chunks)
 teeth,anchors=make_teeth(bodies,s,allban,spec,item['part'])
 result=bodies+teeth
 assert (bodies^s).volume()<1e-6
 assert all(c.bounding_box()[2]<1e-5 for c in bodies.decompose()),'Floating support component'
 assert all(rec['on_build_plate'] for rec in records)
 assert (result^allban).volume()<1e-6
 if not allban.is_empty():write_stl(O/'parts'/f'{pid}_protected.stl',allban)
 if not result.is_empty():write_stl(O/'parts'/f'{pid}_fins.stl',result)
 np.savez_compressed(O/'parts'/f'{pid}.npz',v=v,f=f,fin_v=vf(bodies)[0],fin_f=vf(bodies)[1],teeth_v=vf(teeth)[0],teeth_f=vf(teeth)[1])
 for rec in records:rec['removal_vector']=rec['removal_vector'].tolist()
 report=dict(id=pid,part=item['part'],prescription=spec,source_mesh_preserved=True,support_count=len(chunks),supports_volume_mm3=float(result.volume()),overlap_with_part_mm3=float((bodies^s).volume()),intentional_teeth_overlap_mm3=float((teeth^s).volume()),teeth=anchors,protected_overlap_mm3=float((result^allban).volume()),closed_hole_sections=hole_count,min_gap_mm=min([r['min_gap_mm'] for r in records],default=None),rejected_candidates=dict(rejected),segments=records,source_triangles=len(f),target_faces=len(indices))
 put(O/'design'/f'{pid}.json',report)
 return report
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--id',nargs='*');args=ap.parse_args()
 for d in ['parts','design','verification']: (O/d).mkdir(parents=True,exist_ok=True)
 manifest=json.loads((B/'a1mini/manifest.json').read_text());items={i['id']:i for p in manifest['plates'] if not p['optional'] for i in p['items']}
 decisions={x['object_name']:x for x in json.loads((D/'object_strategy.json').read_text())['objects']}
 candidates=json.loads((D/'mesh_candidates.json').read_text())
 extra={x['part']:x['additional_enforcer_faces'] for x in json.loads((D/'additional_enforcers.json').read_text())['objects']}
 volumes={x['part']:x['volumes'] for x in json.loads((D/'all_protected_volumes.json').read_text())['objects']}
 for pid,item in items.items():
  if args.id and pid not in args.id:continue
  t=time.time();report=build_one(pid,item,decisions[item['object_name']],candidates[item['source_3mf']],extra.get(item['part'],[]),volumes.get(item['part'],[]))
  print(pid,report['support_count'],round(report['supports_volume_mm3'],1),report['rejected_candidates'],round(time.time()-t,2),flush=True)
if __name__=='__main__':main()
