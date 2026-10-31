"""Read-only local self-supporting permanent gusset feasibility. No print file is modified."""
from pathlib import Path
import sys,json,numpy as np,shapely,math
from shapely.geometry import Point
from shapely.ops import nearest_points
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'scripts'))
from build_revo22_fins import solid,vf,union,md,box
from o22_cross_section_geometry import polygon
from repair_revo22_f4_guarded_chamfer import context
from o22_f3_gcode import extract_paths
O=R/'Hardware/PoseDoll44/bench/revO22/a1mini_fins_v4'
def inspect(pid,label):
 folder=O/'candidates'/pid/label;n=np.load(folder/'parts'/f'{pid}.npz');d=json.loads((folder/'design'/f'{pid}.json').read_text());s=solid(n['v'],n['f']);fin=solid(n['fin_v'],n['fin_f']);parts,key,T=context(d,pid);it=json.loads((folder/'verification/plate_manifest.json').read_text())['items'][0];M=np.array(it['rotation_matrix']);off=np.array(it['translation_mm']);ap=folder/'verification/full_bead_contacts_v5.json';ap=ap if ap.exists() else folder/'verification/full_bead_contacts_v2.json';audit=json.loads(ap.read_text());rows=[]
 proj=folder/'projects'/json.loads((folder/'verification/local_extrusion.json').read_text())['project'];_,raw=extract_paths(proj,arc_tolerance_mm=.025,max_arc_segment_mm=1.);a=np.asarray(raw).reshape(-1,9);a=a[a[:,7]==0]
 for issue in audit['external_islands']+audit['critical_external_runs']:
  b=issue['bounds_mm'];z=issue['z_mm']-.1
  if 'xy_mm' in issue:pp=shapely.LineString(issue['xy_mm']).interpolate(.5,normalized=True);p=(np.array([pp.x,pp.y,z])-off)@M
  else:
   ar=a[abs(a[:,5]-issue['z_mm'])<.002];xy=np.stack([ar[:,:2],ar[:,3:5]],axis=1);buf=shapely.orient_polygons(shapely.buffer(shapely.linestrings(xy),np.maximum(ar[:,8]/2,.001),quad_segs=3));cs=md.CrossSection([np.round(np.asarray(g.exterior.coords)[:-1],4) for g in buf if not g.is_empty]);island=min(cs.decompose(),key=lambda c:np.max(abs(np.array(c.bounds())-b)));assert np.max(abs(np.array(island.bounds())-b))<1e-4
   reg=shapely.transform(polygon(island),lambda q:(q-off[:2])@M[:2,:2]).intersection(polygon(s.slice(z)));pt=reg.representative_point();p=np.array([pt.x,pt.y,z])
  found=[]
  for rise in [.6,1.,1.4,2.,2.6,3.2,4.,5.]:
   hz=z-rise
   if hz<.3:continue
   section=polygon(s.slice(hz)).buffer(-.45)
   if section.is_empty:continue
   base=nearest_points(section,Point(p[:2]))[0];roots=[np.array([base.x,base.y])]
   for dist in [.4,.8,1.2,1.6,2.,2.6,3.2,4.]:
    if dist/rise>.8:continue
    roots.extend(p[:2]+dist*np.array([math.cos(ang),math.sin(ang)]) for ang in np.arange(0,2*math.pi,math.pi/12))
   for c in roots:
    if not section.covers(Point(c)):continue
    distance=float(np.linalg.norm(c-p[:2]))
    if distance/rise>.8:continue
    for width in [.6,1.]:
     rootpts=[[c[0]+x,c[1]+y,h]for x in[-width/2,width/2]for y in[-width/2,width/2]for h in[hz-.15,hz+.15]];tips=[[p[0]+x,p[1]+y,h]for x in[-.35,.35]for y in[-.35,.35]for h in[z+.12,z+.35]];wedge=md.Manifold.hull_points(np.array(rootpts+tips));add=wedge-s;vol=float(add.volume())
     if not 1e-5<vol<15:continue
     aw=add.transform(np.linalg.inv(T)[:3,:]);rb=np.array(aw.bounding_box());near=[];collisions=[]
     for k,part in parts.items():
      if k==key:continue
      pb=np.array(part.bounding_box());sep=np.maximum(np.maximum(rb[:3]-pb[3:],pb[:3]-rb[3:]),0)
      if np.linalg.norm(sep)>1.:continue
      gap=float(aw.min_gap(part,1.))
      if gap<.99:
       ov=float((aw^part).volume());near.append({'part':k,'gap_mm':gap,'intersection_mm3':ov})
       if gap<.08:collisions.append(k)
     if collisions:continue
     found.append({'rise':rise,'root_width':width,'tip_width':.7,'target':p.tolist(),'root':c.tolist(),'added_mm3':vol,'slope':distance/rise,'nearest_parts':near,'fin_overlap_mm3':float((fin^add).volume()),'local_bounds_mm':list(add.bounding_box())})
  found.sort(key=lambda q:q['added_mm3']);rows.append({'issue':issue,'options':found[:6]});print('GUSSET180',pid,issue['z_mm'],len(found),found[:1],flush=True)
 (folder/'verification/gusset_feasibility180.json').write_text(json.dumps({'read_only':True,'part':pid,'label':label,'rows':rows},indent=2))
if __name__=='__main__':
 for spec in sys.argv[1:]:inspect(*spec.split(':'))
