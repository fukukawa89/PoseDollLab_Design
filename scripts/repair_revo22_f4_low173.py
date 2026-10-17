"""Draft broad, cross-braced portal panels: all roots start on the bed.
A 45-degree growing front routes around the box without using it as a support.
Temporary support may occupy empty assembly holes and must be cut out completely.
"""
from pathlib import Path
import sys,json,math,numpy as np,trimesh,shapely
from scipy.ndimage import binary_dilation,binary_opening
from shapely.geometry import box as box2
from collections import Counter
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'scripts'))
from build_revo22_fins import solid,vf,box,union,md,project_xz,slab,extrude_xz
from o22_cross_section_geometry import polygon
from o22_material_components import material_components
from slice_revo22_f4_candidate import run
from verify_revo22_f4_full_bead import check
from refine_revo22_f4_full_bead import refine
O=R/'Hardware/PoseDoll44/bench/revO22/a1mini_fins_v4'
def trial(pid,parent,label):
 src=O/'candidates'/pid/parent;dst=O/'candidates'/pid/label
 for sub in ['parts','design','verification']:(dst/sub).mkdir(parents=True,exist_ok=True)
 n=dict(np.load(src/'parts'/f'{pid}.npz'));r=json.loads((src/'design'/f'{pid}.json').read_text());s=solid(n['v'],n['f']);fin=solid(n['fin_v'],n['fin_f']);teeth=solid(n['teeth_v'],n['teeth_f']);tm=trimesh.Trimesh(n['v'],n['f'],process=False);it=json.loads((src/'verification/plate_manifest.json').read_text())['items'][0];M=np.array(it['rotation_matrix']);off=np.array(it['translation_mm']);report=src/'verification/full_bead_contacts_v5.json';report=report if report.exists()else src/'verification/full_bead_contacts_v2.json';audit=json.loads(report.read_text()) if report.exists() else json.loads((src/'verification/local_extrusion.json').read_text());issues=audit.get('external_islands',audit.get('detached_bead_regions',[]))+audit.get('critical_external_runs',[]);added=[];why=Counter()
 for issue in issues:
  z=float(issue['z_mm'])-.1;b=issue['bounds_mm'];pts=(np.array([[x,y,z]for x in [b[0],b[2]]for y in[b[1],b[3]]])-off)@M;lo=pts.min(0);hi=pts.max(0);region=polygon(s.slice(z)).intersection(box2(lo[0]-.03,lo[1]-.03,hi[0]+.03,hi[1]+.03))
  if region.is_empty or z<1.8 or z>15:continue
  pt=region.representative_point();p=np.array([pt.x,pt.y,z]);hits,_,faces=tm.ray.intersects_location([[p[0],p[1],-.1]],[[0,0,1]],multiple_hits=True);h=[q for q,f in zip(hits,faces)if tm.face_normals[f,2]<-.15 and z-.9<q[2]<z+.1]
  if not h:continue
  roof=float(min(h,key=lambda q:abs(q[2]-z))[2]);height=math.floor((roof-3.2)/.2)*.2;done=False
  if height<.2:continue
  for angle in range(0,180,15):
   rad=math.radians(angle);A=np.array([[math.cos(rad),math.sin(rad),0],[-math.sin(rad),math.cos(rad),0],[0,0,1.]]);sp=s.transform(np.c_[A,[0,0,0]]);pr=A@p;bb=np.array(sp.bounding_box());thick=1.6
   for shift,root_shift in __import__("itertools").product([0.,-1.,1.,-2.,2.,-2.4,2.4],[0.,-1.2,1.2,-2.4,2.4]):
    y=pr[1]+shift;obstacle=polygon(project_xz(slab(sp,y-thick/2-.02,y+thick/2+.02,bb)).offset(.5,circular_segments=12));x0=bb[0]-16.;x1=bb[3]+16.
    if x1-x0>170:continue
    dx=dz=.2;xs=np.arange(x0+.1,x1,dx);zs=np.arange(.1,height,dz);X,Z=np.meshgrid(xs,zs);free=~shapely.contains_xy(obstacle,X,Z);reach=np.zeros_like(free);previous=np.zeros(len(xs),bool)
    for j,zz in enumerate(zs):
     allowed=free[j] if j==0 else free[j]&binary_dilation(previous,structure=np.ones(3,bool));minwidth=max(1.6,min(height/4,4.,(height-zz)/2+1.6));previous=binary_opening(allowed,structure=np.ones(max(1,int(math.ceil(minwidth/dx))),bool));reach[j]=previous
    xi=int(round((pr[0]+root_shift-x0-.1)/dx))
    if not reach[-1,max(0,min(len(xs)-1,xi))]:why['no_broad_reachable_top']+=1;continue
    rect=[]
    for j,row in enumerate(reach):
     edges=np.diff(np.r_[False,row,False].astype(int))
     for a,bx in zip(np.flatnonzero(edges==1),np.flatnonzero(edges==-1)):rect.append(md.CrossSection.square([(bx-a)*dx,dz+.00001]).translate([x0+a*dx,j*dz]))
    profile=md.CrossSection.batch_boolean(rect,md.OpType.Add);core=extrude_xz(profile,thick,y);tooth=md.Manifold.hull_points(np.array([[xx,yy,zz] for xx in [pr[0]+root_shift-.65,pr[0]+root_shift+.65] for yy in [y-1.2,y+1.2] for zz in [height-.25,height+.15]]+[[x,y,zz] for x in [pr[0]-.5,pr[0]+.5] for y in [pr[1]-.5,pr[1]+.5] for zz in [roof+.2,roof+.35]]));bite=float((tooth^sp).volume());root=float((tooth^core).volume())
    if not .015<bite<3.0 or root<.05:
     if why['tooth_contact']<20:print('PORTAL151_CONTACT_REJECT',pid,z,angle,shift,root_shift,'bite',bite,'root',root,flush=True)
     why['tooth_contact']+=1;continue
    # The human explicitly permits embedding the short teeth. The fin body remains collision-free.
    # This connector has <=3.2 mm total horizontal reach and <4 mm height; its whole growth is checked below.
    if math.hypot(root_shift,shift)>3.20001:continue
    core=union([c for c in material_components(core) if (c^tooth).volume()>.005]);cs=core.slice(.1);legs=cs.decompose()
    single_low_wide=len(legs)==1 and legs[0].bounds()[2]-legs[0].bounds()[0]>=(max(4.,height/3) if height<30 else max(12.,height/5))
    if len(legs)<2 and not single_low_wide:why['not_two_bed_legs_or_low_wide_base']+=1;continue
    braces=[]
    for leg in legs:
     lb=leg.bounds()
     for frac in ([.2,.5,.8] if height>25 else [.5]):
      cx=lb[0]+(lb[2]-lb[0])*frac;ray=polygon(profile).intersection(shapely.LineString([[cx,0],[cx,height+1]]));legheight=min(height-4,float(ray.bounds[3]));brace=box([cx-1.6,y-7.,0],[cx+1.6,y+7.,legheight])
      if legheight>height*.5 and (brace^sp).volume()<1e-6 and brace.min_gap(sp,.4)>.24:braces.append(brace)
    required_braces=0 if height<=25 else 2
    if len(braces)<required_braces:why['no_required_transverse_buttresses']+=1;continue
    core=core+union(braces);foot=core.slice(.1).offset(1.5,circular_segments=12).extrude(.4);foot=foot-(sp^box(bb[:3]-1,[bb[3]+1,bb[4]+1,.8])).project().offset(.35,circular_segments=12).extrude(.5);body=core+foot
    if (body^sp).volume()>1e-6 or body.min_gap(sp,.5)<.235:why['body_collision_or_gap']+=1;continue
    bod=body.transform(np.c_[A.T,[0,0,0]]);tt=tooth.transform(np.c_[A.T,[0,0,0]]);fv=np.r_[n['v'],vf(fin+bod)[0]];size=np.ptp(fv,axis=0)
    if max(size[:2])>172:why['bed_bounds']+=1;continue
    fin=fin+bod;teeth=teeth+tt;num=len(r['segments'])+1;row={'number':num,'bounds_mm':list(bod.bounding_box()),'height_mm':height,'blade_width_mm':x1-x0,'blade_thickness_mm':thick,'teeth_count':1,'brace_count':len(braces),'on_build_plate':True,'vertical_bed_path':False,'bed_connected_portal':True,'low_compact_passage_fin':True,'broad_buttressed_single_leg_allowed':True,'single_leg_minimum_width_height_ratio':.2,'single_leg_minimum_cross_buttresses':2,'minimum_base_leg_width_mm':min((q.bounds()[2]-q.bounds()[0]) for q in legs),'modeled_growth_xy_per_z':1.,'cross_brace_depth_mm':14.,'min_gap_mm':float(bod.min_gap(s,.5)),'removal_requires_cutting_portal_crown':True,'removal_instruction':'Cut teeth first; cut the orange crown into sections, then remove the two bed-rooted legs and transverse buttresses independently. Do not pry against the blue joint seats.'};r['segments'].append(row);r['teeth'].append({'bounds_mm':list(tt.bounding_box()),'part_bite_mm3':bite,'fin_root_mm3':root,'nominal_tip_penetration_mm':.35,'neck_xy_mm':[1.,1.],'broad_connector_root_xy_mm':[1.3,2.4],'short_connector_horizontal_reach_mm':math.hypot(root_shift,shift),'connector_total_height_mm':roof+.35-(height-.25),'embedded_short_connector_allowed':True,'contact_point_mm':[p[0],p[1],roof],'fin_number':num});added.append(dict(row,native_issue=issue));print('PORTAL114_ADDED',pid,z,angle,shift,'legs',len(legs),'size',size,flush=True);done=True;break
   if done:break
  if not done:print('PORTAL114_NO_ROUTE',pid,z,dict(why),flush=True)
 n['fin_v'],n['fin_f']=vf(fin);n['teeth_v'],n['teeth_f']=vf(teeth);r.update(support_count=len(r['segments']),support_volume_mm3=float((fin+teeth).volume()),body_part_overlap_mm3=float((fin^s).volume()),teeth_part_overlap_mm3=float((teeth^s).volume()),portal_panels_added=added,portal_rejection_counts=dict(why),portal_geometry_requires_native_validation=True);np.savez_compressed(dst/'parts'/f'{pid}.npz',**n);(dst/'design'/f'{pid}.json').write_text(json.dumps(r,ensure_ascii=False,indent=2),encoding='utf8');print('PORTAL114_TOTAL',pid,len(added),dict(why),flush=True)
 if added:
  import shutil
  if(src/'verification/body_change_fit_and_pose.json').exists():shutil.copy2(src/'verification/body_change_fit_and_pose.json',dst/'verification/body_change_fit_and_pose.json')
  from trim_revo22_f4_teeth117 import trial as trim
  trim(pid,label,label+'_self')
if __name__=='__main__':trial(*sys.argv[1:])

