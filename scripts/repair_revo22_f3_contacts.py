"""Add targeted, bed-rooted short piers at geometrically disconnected starts.
Never route through a lower part; all corrections verified by solid intersection.
"""
import sys,json,math,time
import numpy as np
from build_revo22_fins_v3 import *
from check_revo22_f3_layers import check

def repair(pid):
 path=O/'parts'/f'{pid}.npz';n=dict(np.load(path));r=json.loads((O/'design'/f'{pid}.json').read_text());s=solid(n['v'],n['f']);b=solid(n['fin_v'],n['fin_f']) if len(n['fin_f']) else md.Manifold();teeth=solid(n['teeth_v'],n['teeth_f']) if len(n['teeth_f']) else md.Manifold();tm=trimesh.Trimesh(n['v'],n['f'],process=False)
 vols=next((x['volumes'] for x in json.loads((D/'all_protected_volumes.json').read_text())['objects'] if x['part']==r['part']),[]);M=np.array(r['orientation']['matrix']);off=np.array(r['orientation']['source_translation_mm']);ban=protected(vols).transform(np.c_[M,off]);added=[];fails=[]
 d=json.loads((O/'verification'/f'{pid}_layers.json').read_text());targets=d['combined_floating_islands']
 for target in targets:
  z=target['z_mm'];bb=target['bounds'];section=(s+b+teeth).slice(z);pieces=section.decompose()
  cs=min(pieces,key=lambda cc:np.linalg.norm(np.array(cc.bounds())-np.array(bb)))
  if np.linalg.norm(np.array(cs.bounds())-np.array(bb))>.15:continue
  p=polygon(cs).representative_point();x,y=p.x,p.y
  if not b.is_empty() and ((s+b+teeth).slice(z)^((s+b+teeth).slice(z-.2).offset(.025))).area()>0:
   # Still check this local component, not an unrelated connected region.
   if (cs^((s+b+teeth).slice(z-.2).offset(.025))).area()>1e-5:continue
  hit,_,_=tm.ray.intersects_location([[x,y,-.1]],[[0,0,1]],multiple_hits=False)
  if not len(hit) or abs(hit[0,2]-z)>.35:fails.append({'target':target,'reason':'occluded_from_bed'});continue
  roof=float(hit[0,2]);done=False
  for angle in np.arange(0,180,15):
   rad=math.radians(angle);rot=np.array([[math.cos(rad),-math.sin(rad),0],[math.sin(rad),math.cos(rad),0],[0,0,1]])
   # Strong local fin proportions: 1.6-mm blade, breadth >= height/3.
   width=max(2.6,roof/3);thick=1.6 if roof<35 else 2.4
   for shift in [0,-.5,.5,-1,1]:
    cx,cy=np.array([x,y])+rot[:2,0]*shift
    def blade(h):return box([-width/2,-thick/2,0],[width/2,thick/2,h]).transform(np.c_[rot,[cx,cy,0]])
    clearance=.04 if roof<.8 else .24
    lo,hi=.01,roof-clearance
    for _ in range(18):
     mid=(lo+hi)/2;probe=blade(mid)
     if (probe^s).volume()<1e-8 and (probe^ban).volume()<1e-8 and float(probe.min_gap(s,.3))>=clearance:lo=mid
     else:hi=mid
    h=lo-.015
    if h<.1 or roof-h>1.35:continue
    core=blade(h)
    tooth=box([x-.4,y-.4,max(0,h-.4)],[x+.4,y+.4,roof+.2])
    bite=(tooth^s).volume();root=(tooth^core).volume()
    if bite<.02 or bite>.5 or root<.06 or (tooth^ban).volume()>1e-8:continue
    foot=box([-(width/2+1.2),-(thick/2+1.2),0],[width/2+1.2,thick/2+1.2,min(.4,h)]).transform(np.c_[rot,[cx,cy,0]])
    if (foot^s).volume()>1e-7 or (foot^ban).volume()>1e-7:foot=md.Manifold()
    body=core+foot
    if (body^s).volume()>1e-7 or float(body.min_gap(s,.3))<clearance-.005:continue
    body=body.set_tolerance(1e-5)
    combined=union([b.set_tolerance(1e-5),body]);newteeth=union([teeth,tooth])
    if str(combined.status())!='Error.NoError' or combined.volume()<b.volume()-.01 or str(newteeth.status())!='Error.NoError':
     if angle==0 and shift==0:print('BOOLEAN',pid,'b',b.status(),b.volume(),'body',body.status(),body.volume(),'combined',combined.status(),combined.volume(),flush=True)
     continue
    b=combined;teeth=newteeth;num=len(r['segments'])+1
    r['segments'].append({'number':num,'bounds_mm':list(body.bounding_box()),'height_mm':h,'blade_width_mm':width,'blade_thickness_mm':thick,'teeth_count':1,'brace_count':0,'on_build_plate':True,'vertical_bed_path':True,'min_gap_mm':float(body.min_gap(s,.5)),'removal_vector':[0,0,-1],'targeted_island_repair':True})
    r['teeth'].append({'bounds_mm':list(tooth.bounding_box()),'part_bite_mm3':float(bite),'fin_root_mm3':float(root),'nominal_tip_penetration_mm':.2,'neck_xy_mm':[.8,.8],'contact_point_mm':[x,y,roof],'fin_number':num});added.append(target);done=True;break
   if done:break
  if not done:fails.append({'target':target,'reason':'no_collision_free_broad_vertical_blade'})
 assert not b.is_empty() or r['support_count']==0
 assert str(b.status())=='Error.NoError' and str(teeth.status())=='Error.NoError'
 assert all((tt^b).volume()>.005 and (tt^s).volume()>.005 for tt in teeth.decompose())
 n.update(fin_v=vf(b)[0],fin_f=vf(b)[1],teeth_v=vf(teeth)[0],teeth_f=vf(teeth)[1]);np.savez_compressed(path,**n)
 r.update(support_count=len(r['segments']),min_gap_mm=min([x['min_gap_mm'] for x in r['segments']],default=None),body_part_overlap_mm3=float((b^s).volume()),teeth_part_overlap_mm3=float((teeth^s).volume()),support_volume_mm3=float((b+teeth).volume()),targeted_repairs=added,unresolved_targets=fails)
 (O/'design'/f'{pid}.json').write_text(json.dumps(r,ensure_ascii=False,indent=2),encoding='utf-8');print(pid,'added',len(added),'unresolved',len(fails),flush=True)
 check(pid)
if __name__=='__main__':
 for pid in sys.argv[1:]:repair(pid)