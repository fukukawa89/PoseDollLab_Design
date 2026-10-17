"""Add individually placed bed-rooted fins under new layer islands.
Used after the family prescriptions, with an exact source-clearance audit.
"""
import json,math,sys,shutil,collections
import numpy as np
from build_revo22_fins import *

def apply(pid,issues):
 n=np.load(O/'parts'/f'{pid}.npz');v=n['v'];f=n['f'];s=solid(v,f);body=solid(n['fin_v'],n['fin_f']);teeth=solid(n['teeth_v'],n['teeth_f']);report=json.loads((O/'design'/f'{pid}.json').read_text());volumes=next((x['volumes'] for x in json.loads((D/'all_protected_volumes.json').read_text())['objects'] if x['part']==report['part']),[]);ban=protected(volumes)+closed_hole_guard(s)[0]
 backup=R/'.local/fins-before-island-caps';backup.mkdir(exist_ok=True)
 for src in [O/'parts'/f'{pid}.npz',O/'design'/f'{pid}.json']:
  dest=backup/src.name
  if not dest.exists():shutil.copyfile(src,dest)
 added=[];audit=[]
 for q in issues:
  z=q['z_mid_mm'];bb=q['bounds'];window=md.CrossSection.square([bb[2]-bb[0]+.002,bb[3]-bb[1]+.002]).translate([bb[0]-.001,bb[1]-.001]);cs=s.slice(z)^window
  if cs.area()<.08:continue
  previous=s.slice(z-.2)
  # Evaluate two empty layers, which a 0.28-mm CAD gap can quantize to.
  below=body.slice(z-.2)+body.slice(z-.4)+body.slice(z-.6)
  backing=below.offset(1.6)+previous.offset(.65)
  missing=cs-backing
  before=missing.area()/cs.area()
  if before<.03:continue
  rowaudit={'z_mid_mm':z,'island_area_mm2':cs.area(),'unbacked_fraction_before':before,'added_fins':0,'failures':collections.Counter()}
  # A fixed fin direction first; angled alternatives avoid all existing fins.
  base=report['prescription']['axis']
  for angle in [base,(base+90)%180,(base+45)%180,(base+135)%180]:
   sw=s.rotate([0,0,angle]);bw=ban.rotate([0,0,angle]);bounds=sw.bounding_box();rot=cs.rotate(angle);rb=rot.bounds();ys=list(np.arange(rb[1]+.4,rb[3],1.8))+[(rb[1]+rb[3])/2]
   for y in ys:
    current_below=body.slice(z-.2)+body.slice(z-.4)+body.slice(z-.6)
    remaining=cs-current_below.offset(1.6)-previous.offset(.65)
    if remaining.area()/cs.area()<.03:break
    rotmissing=remaining.rotate(angle)
    ints=intervals(rotmissing,y)
    for x0,x1 in ints:
     for x in np.arange(x0+.01,x1+.01,max(1.5,(x1-x0)/4)):
      existing=body.rotate([0,0,angle]);other=project_xz(slab(existing,y-THICK/2-.25,y+THICK/2+.25,bounds)).offset(.2,circular_segments=12) if not existing.is_empty() else md.CrossSection()
      silhouette=project_xz(slab(sw,y-THICK/2-GAP,y+THICK/2+GAP,bounds)).offset(GAP,circular_segments=12)
      gb=project_xz(slab(bw,y-THICK/2-.05,y+THICK/2+.05,bounds))
      avoid=silhouette+gb+other
      target=md.CrossSection.square([2.4,max(.001,z-.3)]).translate([x-1.2,0])-avoid
      routes=BedRoutes(avoid,bounds)
      root=cs_union([q for q in target.decompose() if q.bounds()[1]<1e-5]) if z<1.3 else routes.connect(target)
      if root is None or root.is_empty():rowaudit['failures']['no_bed_route']+=1;continue
      core=extrude_xz(root,THICK,float(y))
      if len(core.decompose())!=1 or core.bounding_box()[2]>1e-5:rowaudit['failures']['disconnected']+=1;continue
      footprint=core.slice(.01).offset(1.4,circular_segments=12);nearby=(sw^box([bounds[0]-5,bounds[1]-5,0],[bounds[3]+5,bounds[4]+5,.48])).project().offset(.45,circular_segments=12);foot=(footprint-nearby).extrude(.2)-bw;rib=core+foot
      if (rib^sw).volume()>1e-6 or (rib^bw).volume()>1e-6:rowaudit['failures']['collision']+=1;continue
      gap=float(rib.min_gap(sw,.5))
      if gap<.195:rowaudit['failures']['gap']+=1;continue
      direction=None
      for ax,sign in [(1,-1),(1,1),(0,-1),(0,1),(2,-1),(2,1)]:
       if exit_clear(core,foot,sw,ax,sign):direction=np.eye(3)[ax]*sign;break
      if direction is None:rowaudit['failures']['no_exit']+=1;continue
      rib=rib.rotate([0,0,-angle]);improve=(cs^(rib.slice(z-.2)+rib.slice(z-.4)+rib.slice(z-.6)).offset(1.6)).area()
      if improve<.01:rowaudit['failures']['no_contact_coverage']+=1;continue
      body=body+rib;rr=math.radians(-angle);mat=np.array([[math.cos(rr),-math.sin(rr),0],[math.sin(rr),math.cos(rr),0],[0,0,1]])
      record={'number':len(report['segments'])+len(added)+1,'rib_row':'island','min_gap_mm':gap,'volume_mm3':float(rib.volume()),'bounds_mm':list(rib.bounding_box()),'removal_vector':(mat@direction).tolist(),'on_build_plate':True,'routed_to_bed':True,'island_z_mid_mm':z}
      added.append(record);rowaudit['added_fins']+=1
   if (cs-(body.slice(z-.2)+body.slice(z-.4)+body.slice(z-.6)).offset(1.6)-previous.offset(.65)).area()/cs.area()<.03:break
  rowaudit['unbacked_fraction_after']=(cs-(body.slice(z-.2)+body.slice(z-.4)+body.slice(z-.6)).offset(1.6)-previous.offset(.65)).area()/cs.area();audit.append(rowaudit)
 if added:
  report['segments']+=added;report['support_count']=len(report['segments']);report['supports_volume_mm3']=float((body+teeth).volume());report['overlap_with_part_mm3']=float((body^s).volume());report['protected_overlap_mm3']=float(((body+teeth)^ban).volume());report['min_gap_mm']=min(r['min_gap_mm'] for r in report['segments']);report['additional_island_fins']=sum(r['rib_row']=='island' for r in report['segments'])
  assert report['overlap_with_part_mm3']<1e-6 and report['protected_overlap_mm3']<1e-6
  np.savez_compressed(O/'parts'/f'{pid}.npz',v=v,f=f,fin_v=vf(body)[0],fin_f=vf(body)[1],teeth_v=n['teeth_v'],teeth_f=n['teeth_f']);put(O/'design'/f'{pid}.json',report);write_stl(O/'parts'/f'{pid}_fins.stl',body+teeth)
 put(O/'verification'/f'{pid}_island_caps.json',{'id':pid,'added_fins':len(added),'islands':audit});print(pid,'added',len(added),'remaining',[(r['z_mid_mm'],round(r['island_area_mm2'],2),round(r['unbacked_fraction_after'],3)) for r in audit if r['unbacked_fraction_after']>.03],flush=True)
if __name__=='__main__':
 rows=json.loads((O/'verification/source_island_review.json').read_text())['parts']
 for row in rows:
  if len(sys.argv)>1 and row['id'] not in sys.argv[1:]:continue
  if row['islands']:apply(row['id'],[q for q in row['islands'] if q['role']=='part'])