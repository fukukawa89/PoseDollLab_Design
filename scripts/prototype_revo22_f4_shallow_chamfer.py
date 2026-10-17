"""Minimal permanent underside chamfers for two fin-inaccessible H006 start corners.
Trial only: assembly/contact validation and native reslicing are required.
"""
from pathlib import Path
import sys,json,shutil
import numpy as np
from shapely.geometry import Point
from shapely.ops import nearest_points
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'scripts'))
from build_revo22_fins import solid,vf,box,union,extrude_xz,md
from o22_cross_section_geometry import polygon
from o22_material_components import material_components
from slice_revo22_f4_candidate import run
from verify_revo22_f4_full_bead import check
O=R/'Hardware/PoseDoll44/bench/revO22/a1mini_fins_v4'
def trial(pid,label,newlabel):
 src=O/'candidates'/pid/label;dst=O/'candidates'/pid/newlabel
 for sub in ['parts','design','verification']:(dst/sub).mkdir(parents=True,exist_ok=True)
 n=dict(np.load(src/'parts'/f'{pid}.npz'));r=json.loads((src/'design'/f'{pid}.json').read_text());audit=json.loads((src/'verification/full_bead_contacts.json').read_text());it=json.loads((src/'verification/plate_manifest.json').read_text())['items'][0];M=np.array(it['rotation_matrix']);t=np.array(it['translation_mm']);old=solid(n['v'],n['f']);new=old;cuts=[];rows=[]
 for issue in audit['external_islands']:
  b=issue['bounds_mm'];z=issue['z_mm']-.1;points=(np.array([[x,y,z] for x in [b[0],b[2]] for y in [b[1],b[3]]])-t)@M;lo=points.min(0);hi=points.max(0);p=(lo+hi)/2;zlo=z-.35;prev=polygon(new.slice(zlo));q=nearest_points(prev,Point(p[:2]))[0];q=np.array([q.x,q.y]);direction=p[:2]-q;distance=np.linalg.norm(direction);direction/=max(distance,1e-12);tangent=np.array([-direction[1],direction[0]]);rot=np.eye(3);rot[:2,0]=direction;rot[:2,1]=tangent
  # The retained underside rises 1 mm per 0.65 mm outward advance.
  slope=.65;zhi=z+.55;cs=md.CrossSection([[[-4,zlo-1],[slope*(zlo-1-zlo),zlo-1],[slope*(zhi+1-zlo),zhi+1],[-4,zhi+1]]]);allow=extrude_xz(cs,8,0).transform(np.c_[rot,[*q,0.]])
  roi=box([lo[0]-.22,lo[1]-.22,zlo],[hi[0]+.22,hi[1]+.22,zhi]);cut=roi-allow;removed=new^cut
  assert removed.volume()<2.,('chamfer_too_large',removed.volume())
  new=new-cut;rows.append({'native_island':issue,'local_bounds_mm':list(roi.bounding_box()),'removed_volume_mm3':float(removed.volume()),'printable_slope_xy_per_z':slope,'nearest_existing_material_xy_mm':q.tolist(),'horizontal_distance_to_parent_mm':float(distance)});cuts.append(removed)
 delta=old-new;assert (new-old).volume()<1e-6;assert len(material_components(new))==len(material_components(old));assert np.allclose(old.bounding_box(),new.bounding_box(),atol=1e-5)
 fin=solid(n['fin_v'],n['fin_f']);teeth=solid(n['teeth_v'],n['teeth_f']);teeth=union([c for c in material_components(teeth) if (c^new).volume()>.005 and (c^fin).volume()>.005]);fin=union([c for c in material_components(fin) if (c^teeth).volume()>.005]);n['source_f']=n.get('source_f',n['f']).copy();n['v'],n['f']=vf(new);n['removed_body_v'],n['removed_body_f']=vf(delta);n['fin_v'],n['fin_f']=vf(fin);n['teeth_v'],n['teeth_f']=vf(teeth);np.savez_compressed(dst/'parts'/f'{pid}.npz',**n)
 rep={'kind':'local_print_chamfer','reason':'All tested broad vertical fins were blocked by the part at these two local starts, including 5-degree direction and 0.1 mm offset search. Modify only the undersides at these corners.','removed_volume_mm3':float(delta.volume()),'added_volume_mm3':float((new-old).volume()),'outer_bounds_unchanged':True,'body_components_unchanged':True,'chamfers':rows,'assembly_contact_validation_pending':True,'source_body_volume_mm3':float(old.volume()),'removed_fraction':float(delta.volume()/old.volume())};r.update(source_mesh_preserved=False,body_change=rep);(dst/'design'/f'{pid}.json').write_text(json.dumps(r,ensure_ascii=False,indent=2),encoding='utf8');(dst/'verification/body_change_trial.json').write_text(json.dumps(rep,indent=2));print('BODY_CHAMFER_TRIAL',pid,rep['removed_volume_mm3'],rep['removed_fraction'],flush=True);run(pid,newlabel);check(pid,newlabel)
if __name__=='__main__':trial(*sys.argv[1:])
