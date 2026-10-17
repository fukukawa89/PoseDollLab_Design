"""Experimental low, broad window fins with bed roots and a verified sideways exit."""
from pathlib import Path
import sys,json,numpy as np,trimesh,shapely,math
from scipy.ndimage import binary_dilation,binary_opening
from shapely.geometry import box as box2
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'scripts'))
from build_revo22_fins import solid,vf,box,union,md,project_xz,slab,extrude_xz,exit_clear
from o22_cross_section_geometry import polygon
from o22_material_components import material_components
from slice_revo22_f4_candidate import run
from verify_revo22_f4_full_bead import check
O=R/'Hardware/PoseDoll44/bench/revO22/a1mini_fins_v4'
def trial(pid,parent,label):
 src=O/'candidates'/pid/parent;dst=O/'candidates'/pid/label;n=dict(np.load(src/'parts'/f'{pid}.npz'));r=json.loads((src/'design'/f'{pid}.json').read_text());audit=check(pid,parent);it=json.loads((src/'verification/plate_manifest.json').read_text())['items'][0];M=np.array(it['rotation_matrix']);tt=np.array(it['translation_mm']);s=solid(n['v'],n['f']);fin=solid(n['fin_v'],n['fin_f']);teeth=solid(n['teeth_v'],n['teeth_f']);tm=trimesh.Trimesh(n['v'],n['f'],process=False);added=[];reject={}
 for issue in audit['external_islands']:
  bb=issue['bounds_mm'];z=issue['z_mm']-.1;pts=(np.array([[x,y,z] for x in [bb[0],bb[2]] for y in [bb[1],bb[3]]])-tt)@M;lo=pts.min(0);hi=pts.max(0);poly=polygon(s.slice(z)).intersection(box2(lo[0]-.05,lo[1]-.05,hi[0]+.05,hi[1]+.05))
  if poly.is_empty or z>25:continue
  point=poly.representative_point();p=np.array([point.x,point.y,z]);hits,_,faces=tm.ray.intersects_location([[p[0],p[1],-.1]],[[0,0,1]],multiple_hits=True);choices=[(abs(float(q[2])-z),q) for q,f in zip(hits,faces) if q[2]<=z+.1 and q[2]>=z-1. and tm.face_normals[f,2]<-.15]
  if not choices:continue
  roof=float(min(choices,key=lambda x:x[0])[1][2]);height=math.floor((roof-.45)/.2)*.2
  if height<.8:continue
  success=False
  for angle in range(0,180,15):
   rad=math.radians(angle);A=np.array([[math.cos(rad),math.sin(rad),0],[-math.sin(rad),math.cos(rad),0],[0,0,1.]]);sp=s.transform(np.c_[A,[0,0,0]]);pr=A@p;bounds=np.array(sp.bounding_box());thick=1.2
   for shift in [0.,-.4,.4,-.6,.6]:
    y=pr[1]+shift;obstacle=polygon(project_xz(slab(sp,y-thick/2-.45,y+thick/2+.45,bounds)).offset(.45,circular_segments=12));half=max(8.,height*.8);dx=.2;dz=.2;x0=pr[0]-half;xs=np.arange(x0+dx/2,pr[0]+half,dx);zs=np.arange(dz/2,height,dz);X,Z=np.meshgrid(xs,zs);free=~shapely.contains_xy(obstacle,X,Z);reach=np.zeros_like(free);previous=np.zeros(len(xs),bool)
    for j in range(len(zs)):
     allowed=free[j] if j==0 else free[j]&binary_dilation(previous,structure=np.ones(3,bool));previous=binary_opening(allowed,structure=np.ones(20,bool));reach[j]=previous
    xi=int(round((pr[0]-x0-dx/2)/dx))
    if not reach[-1,max(0,min(len(xs)-1,xi))]:continue
    rectangles=[]
    for j,row in enumerate(reach):
     edges=np.diff(np.r_[False,row,False].astype(int));beg=np.flatnonzero(edges==1);end=np.flatnonzero(edges==-1)
     for a,b in zip(beg,end):rectangles.append(md.CrossSection.square([(b-a)*dx,dz]).translate([x0+a*dx,j*dz]))
    profile=md.CrossSection.batch_boolean(rectangles,md.OpType.Add);core=extrude_xz(profile,thick,y);tooth=box([pr[0]-.5,pr[1]-.5,height-.25],[pr[0]+.5,pr[1]+.5,roof+.2]);bite=float((tooth^sp).volume());root=float((tooth^core).volume())
    if not .015<bite<.5 or root<.05:continue
    comps=[c for c in material_components(core) if (c^tooth).volume()>.005];core=union(comps)
    if not comps or (core^sp).volume()>1e-6 or float(core.min_gap(sp,.4))<.235:continue
    if any(c.bounding_box()[2]>1e-5 or c.slice(.1).area()<8 for c in comps):continue
    back=core.transform(np.c_[A.T,[0,0,0]]);collision=float((back^(fin+teeth)^box([-200,-200,.6],[250,250,250])).volume())
    if collision>1e-6:continue
    exits=[sign for sign in [-1,1] if exit_clear(core,md.Manifold(),sp,1,sign)]
    if not exits:continue
    foot=core.slice(.1).offset(1.5,circular_segments=12).extrude(.2);foot=foot-(sp^box(bounds[:3]-1,[*list(bounds[3:5]+1),.8])).project().offset(.3,circular_segments=12).extrude(.3)
    if (foot^sp).volume()>1e-6:foot=md.Manifold()
    body=(core+foot).transform(np.c_[A.T,[0,0,0]]);tooth=tooth.transform(np.c_[A.T,[0,0,0]]);fin=fin+body;teeth=teeth+tooth;num=len(r['segments'])+1;row={'number':num,'bounds_mm':list(body.bounding_box()),'height_mm':height,'blade_width_mm':2*half,'blade_thickness_mm':thick,'teeth_count':1,'brace_count':0,'on_build_plate':True,'vertical_bed_path':False,'bed_connected_window_panel':True,'max_modeled_layer_lateral_step_mm':.2,'modeled_layer_height_mm':.2,'minimum_leg_width_mm':4.,'min_gap_mm':float(body.min_gap(s,.5)),'removal_vector':(A.T@np.array([0,exits[0],0])).tolist(),'sideways_core_sweep_collision_mm3':0.,'requires_separating_base_joins_below_mm':.6,'existing_fins_overlap_above_06mm_mm3':collision};r['segments'].append(row);r['teeth'].append({'bounds_mm':list(tooth.bounding_box()),'part_bite_mm3':bite,'fin_root_mm3':root,'nominal_tip_penetration_mm':.2,'neck_xy_mm':[1.,1.],'contact_point_mm':[p[0],p[1],roof],'fin_number':num});added.append(row);success=True;print('WINDOW_FIN',pid,z,angle,shift,height,flush=True);break
   if success:break
  if not success:reject[str(round(z,3))]='No short broad panel with bed roots, no body or upper support intersection, and a straight sideways exit was found.'
 n['fin_v'],n['fin_f']=vf(fin);n['teeth_v'],n['teeth_f']=vf(teeth);r.update(support_count=len(r['segments']),support_volume_mm3=float((fin+teeth).volume()),body_part_overlap_mm3=float((fin^s).volume()),teeth_part_overlap_mm3=float((teeth^s).volume()),window_panels_added=added,window_panel_rejections=reject)
 for sub in ['parts','design','verification']:(dst/sub).mkdir(parents=True,exist_ok=True)
 np.savez_compressed(dst/'parts'/f'{pid}.npz',**n);(dst/'design'/f'{pid}.json').write_text(json.dumps(r,ensure_ascii=False,indent=2),encoding='utf8');print('WINDOW_FIN_RESULT',pid,len(added),reject,flush=True);run(pid,label);return check(pid,label)
if __name__=='__main__':trial(*sys.argv[1:])
