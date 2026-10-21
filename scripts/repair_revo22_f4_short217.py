"""Short 1-2 mm contact wedges from an existing bed-rooted fin, aimed at the actual first isolated bead."""
from pathlib import Path
import sys,json,numpy as np,shapely,math,shutil
from shapely.geometry import Point
from shapely.ops import nearest_points
from collections import Counter
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'scripts'))
from build_revo22_fins import solid,vf,union,md
from o22_cross_section_geometry import polygon
from trim_revo22_f4_teeth117 import trial as trim
O=R/'Hardware/PoseDoll44/bench/revO22/a1mini_fins_v4'
def trial(pid,parent,label):
 src=O/'candidates'/pid/parent;dst=O/'candidates'/pid/label;n=dict(np.load(src/'parts'/f'{pid}.npz'));d=json.loads((src/'design'/f'{pid}.json').read_text());s=solid(n['v'],n['f']);fin=solid(n['fin_v'],n['fin_f']);teeth=solid(n['teeth_v'],n['teeth_f']);a=json.loads((src/'verification/full_bead_contacts_v5.json').read_text());it=json.loads((src/'verification/plate_manifest.json').read_text())['items'][0];M=np.array(it['rotation_matrix']);off=np.array(it['translation_mm']);added=[]
 for issue in a['external_islands']:
  if not 8<issue['z_mm']<12:continue
  b=issue['bounds_mm'];p=(np.array([(b[0]+b[2])/2,(b[1]+b[3])/2,issue['z_mm']-.1])-off)@M;best=None;why=Counter()
  for rise in [.6,.8,1.,1.2,1.6,2.,2.4]:
   hz=p[2]-rise;cs=polygon(fin.slice(hz-.1));inset=cs.buffer(-.42)
   if inset.is_empty:continue
   q=nearest_points(inset,Point(p[:2]))[0];c0=np.array([q.x,q.y]);cand=[c0]+[c0+np.array([x,y])for x in[-.4,0,.4]for y in[-.4,0,.4]]
   for c in cand:
    reach=np.linalg.norm(c-p[:2])
    if reach>3.2:continue
    direction=(p[:2]-c)/max(reach,1e-9);tangent=np.array([-direction[1],direction[0]])
    for rw,tw in[(.8,.7),(1.,.8),(1.2,1.),(.8,1.)]:
     rootxy=np.array([c+x*direction+y*tangent for x in[-rw/2,rw/2]for y in[-.8,.8]])
     if shapely.MultiPoint(rootxy).convex_hull.difference(cs).area>.02:why['root_fit']+=1;continue
     root=np.array([[x,y,z]for x,y in rootxy for z in[hz-.2,hz+.1]])
     tip=np.array([[p[0]+x,p[1]+y,z]for x in[-tw/2,tw/2]for y in[-.7,.7]for z in[p[2]-.4,p[2]+.3]])
     tooth=md.Manifold.hull_points(np.r_[root,tip]);bite=float((tooth^s).volume());ov=float((tooth^fin).volume())
     if not .015<bite<3 or ov<.05:why['contact']+=1;continue
     prev=fin.slice(math.floor((hz-.3)/.2)*.2+.1);pieces=[]
     for z in np.arange(math.floor((hz-.2)/.2)*.2+.1,p[2]+.4,.2):
      sec=tooth.slice(float(z))^prev.offset(.195,circular_segments=12)
      if not sec.is_empty():pieces.append(sec.extrude(.200002).translate([0,0,float(z-.100001)]))
      prev=fin.slice(float(z))+sec
     grown=union(pieces)^tooth;gb=float((grown^s).volume());gf=float((grown^fin).volume());dist=polygon(grown.slice(p[2]-.2)).distance(Point(p[:2]))
     if gb<.015 or gf<.05 or dist>.18:
      if why['growth_target']<16:print('SHORT217_GROWTH_DETAIL',rise,c.tolist(),rw,tw,'reach',reach,'bite',gb,'root',gf,'gap',dist,flush=True)
      why['growth_target']+=1;continue
     score=reach+rise*.2+float(grown.volume())*.1
     if best is None or score<best[0]:best=(score,grown,dict(bounds_mm=list(grown.bounding_box()),part_bite_mm3=gb,fin_root_mm3=gf,root_xy_mm=[rw,1.6],tip_xy_mm=[tw,1.4],short_connector_horizontal_reach_mm=float(reach),connector_rise_mm=rise,contact_point_mm=p.tolist(),rooted_on_existing_bed_fin=True,native_issue=issue,previous_layer_target_gap_mm=dist))
  print('SHORT217_SEARCH',pid,p.tolist(),dict(why),best[2]if best else None,flush=True)
  if best:teeth=teeth+best[1];d['teeth'].append(best[2]);added.append(best[2])
 if not added:return
 for sub in['parts','design','verification']:(dst/sub).mkdir(parents=True,exist_ok=True)
 n['teeth_v'],n['teeth_f']=vf(teeth);d['short_contact_wedges217']=added;d['support_volume_mm3']=float((fin+teeth).volume());np.savez_compressed(dst/'parts'/f'{pid}.npz',**n);(dst/'design'/f'{pid}.json').write_text(json.dumps(d,indent=2))
 if(src/'verification/body_change_fit_and_pose.json').exists():shutil.copy2(src/'verification/body_change_fit_and_pose.json',dst/'verification/body_change_fit_and_pose.json')
 trim(pid,label,label+'_self')
if __name__=='__main__':trial(*sys.argv[1:])

