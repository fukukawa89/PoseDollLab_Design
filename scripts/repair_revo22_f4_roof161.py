from pathlib import Path
import sys,json,numpy as np,trimesh,math,shutil
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'scripts'))
import repair_revo22_f4_portal_high120 as portal
from build_revo22_fins import solid,vf,md,union
from slice_revo22_f4_candidate import run
from verify_revo22_f4_full_bead import check
from refine_revo22_f4_lateral104 import check as refine
from verify_revo22_f4_repaired_geometry import check as geom
from verify_revo22_f4_portal_layers import check as growth
O=R/'Hardware/PoseDoll44/bench/revO22/a1mini_fins_v4';pid='W017';parent='access158';label='roof161'
src=O/'candidates'/pid/parent;dst=O/'candidates'/pid/label
for sub,ext in [('parts','npz'),('design','json')]:
 (dst/sub).mkdir(parents=True,exist_ok=True);shutil.copy2(src/sub/f'{pid}.{ext}',dst/sub/f'{pid}.{ext}')
(dst/'verification').mkdir(exist_ok=True)
p=O/'candidates'/pid/label;n=dict(np.load(p/'parts'/f'{pid}.npz'));d=json.loads((p/'design'/f'{pid}.json').read_text());s=solid(n['v'],n['f']);fin=solid(n['fin_v'],n['fin_f']);teeth=solid(n['teeth_v'],n['teeth_f']);tm=trimesh.Trimesh(n['v'],n['f'],process=False);rows=[]
for row in d['body_change']['chamfers']:
 if row.get('kind')!='support_access_window':continue
 q=row['read_only_preinspection'];h=q['height_mm'];w=q['fin_width_mm'];a=math.radians(q['angle_deg']);A=np.array([[math.cos(a),-math.sin(a)],[math.sin(a),math.cos(a)]]);c=np.array(q['xy_mm']);count=0
 for x in np.linspace(-w/2+.35,w/2-.35,max(3,int(np.ceil((w-.7)/.9))+1)):
  for y in[-.48,.48]:
   xy=np.array([x,y])@A.T+c;hits,_,faces=tm.ray.intersects_location([[*xy,h-.01]],[[0,0,1]],multiple_hits=True);hits=[v for v,f in zip(hits,faces)if tm.face_normals[f,2]<-.1 and h+.15<v[2]<h+1.6]
   if not hits:continue
   roof=float(min(v[2]for v in hits));pts=[]
   for width,zs in [(.6,[h-.18,h+.02]),(1.2,[roof+.12,roof+.35])]:
    pts.extend([[*(np.array([x+dx,y+dy])@A.T+c),z]for dx in[-width/2,width/2]for dy in[-width/2,width/2]for z in zs])
   tt=md.Manifold.hull_points(np.array(pts));bite=float((tt^s).volume());root=float((tt^fin).volume())
   if bite<.005 or root<.005:continue
   teeth=teeth+tt;rec={'bounds_mm':list(tt.bounding_box()),'part_bite_mm3':bite,'fin_root_mm3':root,'nominal_tip_penetration_mm':.35,'neck_xy_mm':[.6,.6],'top_xy_mm':[1.2,1.2],'contact_point_mm':[*xy,roof],'window_roof_contact':True,'connector_height_mm':roof+.35-(h-.18)};d['teeth'].append(rec);rows.append(rec);count+=1
 print('ROOF120_CONTACTS',q['xy_mm'],count,flush=True)
n['teeth_v'],n['teeth_f']=vf(teeth);d.update(support_volume_mm3=float((fin+teeth).volume()),additional_window_roof_teeth=rows);np.savez_compressed(p/'parts'/f'{pid}.npz',**n);(p/'design'/f'{pid}.json').write_text(json.dumps(d,ensure_ascii=False,indent=2),encoding='utf8');shutil.copy2(O/'candidates'/pid/parent/'verification/body_change_fit_and_pose.json',p/'verification/body_change_fit_and_pose.json');from trim_revo22_f4_teeth117 import trial as trim
trim(pid,label,label+'_self')
