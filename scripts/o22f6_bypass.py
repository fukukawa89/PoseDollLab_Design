"""Try bed-rooted external bypasses for cut fins, with continuous body-clear withdrawal."""
import sys,json,collections,numpy as np
from o22f6_holeclear import *
from o22_cross_section_geometry import polygon
from route_revo22_x062244 import sweep_convex

def trial(pid):
 n=dict(np.load(OUT/f'parts/{pid}.npz'));old=np.load(SRC/f'parts/{pid}.npz');g=np.load(WORK/f'guards/{pid}.npz');ban=solid(g['v'],g['f']);body=solid(n['v'],n['f']);oldfin=solid(old['fin_v'],old['fin_f']);fin=solid(n['fin_v'],n['fin_f']);teeth=solid(n['teeth_v'],n['teeth_f']);oldteeth=solid(old['teeth_v'],old['teeth_f']);rows=[];counts=collections.Counter()
 for orphan in material_components(oldfin-ban):
  bb=np.array(orphan.bounding_box())
  if bb[2]<.01:continue
  parent=max(material_components(oldfin),key=lambda c:(c^orphan).volume());others=oldfin-parent;success=False
  for z in [bb[5]-.35,(bb[2]+bb[5])/2,bb[2]+.6]:
   pp=polygon(orphan.slice(z));points=[np.array(q.representative_point().coords[0])for q in getattr(pp,'geoms',[pp])if not q.is_empty]
   for top in points:
    for shift in [0,4,8,12,18,25,32]:
     for ang in np.arange(0,2*np.pi,np.pi/12):
      u=np.array([np.cos(ang),np.sin(ang)]);perp=np.array([-u[1],u[0]]);base=top+shift*u;pts=[]
      if shift>z*.8:continue
      for c,zz,w,t in [(base,0.,max(4.5,z*.17),1.2),(top,z,.7,.7)]:
       for a,b in [(-1,-1),(1,-1),(1,1),(-1,1)]:pts.append([*(c+u*a*w/2+perp*b*t/2),zz])
      core=md.Manifold.hull_points(np.array(pts));core+=core.slice(.1).offset(.7,circular_segments=8).extrude(.4)
      limits=np.r_[np.r_[old['v'],old['fin_v'],old['teeth_v']].min(0),np.r_[old['v'],old['fin_v'],old['teeth_v']].max(0)];cb=np.array(core.bounding_box())
      if np.any(cb[:3]<limits[:3]-1e-5)or np.any(cb[3:]>limits[3:]+1e-5):continue
      if(core^orphan).volume()<.008:counts['contact']+=1;continue
      if(core^ban).volume()>1e-6:counts['hole']+=1;continue
      if(core^body).volume()>1e-6:counts['body']+=1;continue
      if any((core^c).volume()>1e-6 and (sweep_convex(c,np.array([0,0,-150.]))^body).volume()>1e-6 for c in material_components(others)):counts['otherfin_locked']+=1;continue
      if(sweep_convex(core,np.array([0,0,-150.]))^body).volume()>1e-6:counts['withdrawal']+=1;continue
      join=np.array((core^orphan).bounding_box());cut_z=min(float(z)-.12,float(join[2])+.28);restored=(parent-ban-orphan)+(orphan^box([-1000,-1000,cut_z],[1000,1000,1000]));ts=union([c for c in material_components(oldteeth-ban)if(c^restored).volume()>.001 and (c^body).volume()>.001]);fin+=restored+core;teeth+=ts;rows.append(dict(trimmed_orphan_below_z_mm=cut_z,top=[*top,z],base=base.tolist(),added_mm3=float(core.volume()),restored_fin_mm3=float(restored.volume()),withdrawal_vector=[0,0,-1],continuous_withdrawal_clear=True));success=True;print('BYPASS',pid,rows[-1],flush=True);break
     if success:break
    if success:break
   if success:break
  if not success:print('BYPASS_NONE',pid,bb.tolist(),dict(counts),flush=True)
 if rows:
  assert((fin+teeth)^ban).volume()<1e-6;assert(fin^body).volume()<1e-6
  fin=union([c for c in material_components(fin) if (c^teeth).volume()>.001]); assert all(c.bounding_box()[2]<1e-6 for c in material_components(fin));assert len(material_components(body+fin+teeth))==len(material_components(body))
  n['fin_v'],n['fin_f']=vf(fin);n['teeth_v'],n['teeth_f']=vf(teeth);folder=WORK/'bypass';(folder/'parts').mkdir(parents=True,exist_ok=True);np.savez_compressed(folder/f'parts/{pid}.npz',**n);d=json.loads((OUT/f'design/{pid}.json').read_text());d['f6_external_bypasses']=rows;put(folder/f'design/{pid}.json',d)
 put(WORK/f'bypass/verification/{pid}.json',dict(id=pid,bypasses=rows))
if __name__=='__main__':
 for p in sys.argv[1:]:trial(p)