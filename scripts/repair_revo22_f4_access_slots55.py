"""Draft one-part support-access slots, strictly bounded and outside actual hardware contact envelopes."""
from pathlib import Path
import sys,json,numpy as np,trimesh,math,shapely
from shapely.geometry import box as box2
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'scripts'))
from build_revo22_fins import solid,vf,box,union,md
from o22_material_components import material_components
from o22_cross_section_geometry import polygon
from o22_reference_mesh import reference_mesh
from repair_revo22_f4_guarded_chamfer import context
from slice_revo22_f4_candidate import run
from verify_revo22_f4_full_bead import check
from refine_revo22_f4_full_bead import refine
from verify_revo22_f4_body_change import check as fit
from verify_revo22_f4_repaired_geometry import check as geom
O=R/'Hardware/PoseDoll44/bench/revO22/a1mini_fins_v4'

def trial(pid,parent,label,max_channel_volume=8.):
 src=O/'candidates'/pid/parent;dst=O/'candidates'/pid/label
 for sub in ['parts','design','verification']:(dst/sub).mkdir(parents=True,exist_ok=True)
 n=dict(np.load(src/'parts'/f'{pid}.npz'));r=json.loads((src/'design'/f'{pid}.json').read_text());audit=refine(pid,parent);part=solid(n['v'],n['f']);rv,rf=reference_mesh(n,r);original=solid(rv@np.array(r['orientation']['matrix']).T+np.array(r['orientation']['source_translation_mm']),rf);fin=solid(n['fin_v'],n['fin_f']);teeth=solid(n['teeth_v'],n['teeth_f']);it=json.loads((src/'verification/plate_manifest.json').read_text())['items'][0];M=np.array(it['rotation_matrix']);shift=np.array(it['translation_mm']);parts,key,T=context(r,pid);offsets=np.array([[x,y,z] for x in [-.08,0,.08] for y in [-.08,0,.08] for z in [-.08,0,.08]]);guards={};accepted=[];rejections=[];expected=len(material_components(part))
 issues=audit['external_islands']
 for issue in issues:
  z=issue['z_mm']-.1;b=issue['bounds_mm'];xy=(np.array([[x,y,z] for x in [b[0],b[2]] for y in [b[1],b[3]]])-shift)@M;lo=xy.min(0);hi=xy.max(0);region=polygon(part.slice(z)).intersection(box2(lo[0]-.02,lo[1]-.02,hi[0]+.02,hi[1]+.02));fail=[]
  if region.is_empty or z>30:continue
  pt=region.representative_point();p=np.array([pt.x,pt.y,z]);v,f=vf(part);tm=trimesh.Trimesh(v,f,process=False);hits,_,faces=tm.ray.intersects_location([[p[0],p[1],-.1]],[[0,0,1]],multiple_hits=True);surfaces=[q for q,j in zip(hits,faces) if tm.face_normals[j,2]<-.15 and z-.8<q[2]<z+.1]
  if not surfaces:continue
  roof=float(min(surfaces,key=lambda q:abs(q[2]-z))[2]);h=roof-.55;width=max(3.,h/4);thick=1.2
  if h<.6:continue
  best=None;proposals=[]
  for angle in range(0,180,10):
   rad=math.radians(angle);A=np.array([[math.cos(rad),-math.sin(rad),0],[math.sin(rad),math.cos(rad),0],[0,0,1.]])
   for along in [0.,-.6,.6,-1.2,1.2]:
    center=p.copy();center[2]=0;center[:2]+=along*A[:2,0];footprint=md.CrossSection.square([width,thick],center=True);core=footprint.extrude(h).transform(np.c_[A,center]);clearance=footprint.offset(.28,circular_segments=16).extrude(h+.28).transform(np.c_[A,center]);removed=part^clearance;vol=float(removed.volume())
    if vol<1e-5:continue
    if vol>min(40.,original.volume()*.008):continue
    rw=removed.transform(np.linalg.inv(T)[:3,:]);bb=np.array(rw.bounding_box());protected_neighbors=[];collision=0.
    for k,s in parts.items():
     if k==key:continue
     sb=np.array(s.bounding_box());sep=np.maximum(np.maximum(sb[:3]-bb[3:],bb[:3]-sb[3:]),0)
     if np.linalg.norm(sep)>.15:continue
     if k not in guards:guards[k]=union([s.translate(o) for o in offsets])
     near=float((rw^guards[k]).volume())
     if near>1e-6:protected_neighbors.append(k);collision+=near
    if collision>1e-6:continue
    new=part-clearance
    if len(material_components(new))!=expected:continue
    if (new-original).volume()>1e-6:continue
    if float((original-new).volume())>min(60.,original.volume()*.008):continue
    tooth=box([p[0]-.45,p[1]-.45,h-.3],[p[0]+.45,p[1]+.45,roof+.2]);bite=float((tooth^new).volume());root=float((tooth^core).volume())
    if not .02<bite<.5 or root<.06:continue
    if (core^new).volume()>1e-6:continue
    nearbed=(new^box([-250,-250,0],[250,250,.8])).project().offset(.35,circular_segments=16);foot=((core.slice(.1).offset(1.8,circular_segments=16))-nearbed).extrude(.4);body=core+foot
    if (body^new).volume()>1e-6 or float(body.min_gap(new,.4))<.235:continue
    q={'angle_deg':angle,'offset_mm':along,'removed_volume_mm3':vol,'channel_bounds_mm':list(clearance.bounding_box()),'body_components_unchanged':True,'hardware_envelope_intersection_mm3':collision,'fin_height_mm':h,'fin_width_mm':width,'fin_thickness_mm':thick,'tooth_bite_mm3':bite,'tooth_root_mm3':root};proposals.append(q)
    if vol>max_channel_volume:continue
    if best is None or vol<best[0]:best=(vol,new,body,tooth,q)
  if best:
   vol,part,body,tooth,q=best;fin=fin+body;teeth=teeth+tooth;num=len(r['segments'])+1;r['segments'].append({'number':num,'bounds_mm':list(body.bounding_box()),'height_mm':h,'blade_width_mm':width,'blade_thickness_mm':thick,'teeth_count':1,'brace_count':0,'on_build_plate':True,'vertical_bed_path':True,'min_gap_mm':float(body.min_gap(part,.5)),'removal_vector':[0,0,-1],'through_dedicated_noncontact_access_slot':True});r['teeth'].append({'bounds_mm':list(tooth.bounding_box()),'part_bite_mm3':q['tooth_bite_mm3'],'fin_root_mm3':q['tooth_root_mm3'],'nominal_tip_penetration_mm':.2,'neck_xy_mm':[.9,.9],'contact_point_mm':[p[0],p[1],roof],'fin_number':num});accepted.append(dict(q,native_issue=issue,local_bounds_mm=q['channel_bounds_mm'],kind='support_access_slot'));print('ACCESS_SLOT',pid,z,q,flush=True)
  else:rejections.append({'native_issue':issue,'contact_clear_connected_proposals_above_cut_limit':sorted(proposals,key=lambda q:q['removed_volume_mm3'])[:3]})
 rep=r.get('body_change',{});rep.update(kind='small_support_access_slot',chamfers=rep.get('chamfers',[])+accepted,removed_volume_mm3=float((original-part).volume()),added_volume_mm3=0.,removed_fraction=float((original-part).volume()/original.volume()),source_body_volume_mm3=float(original.volume()),body_components_unchanged=True,assembly_contact_validation_pending=True);r['body_change']=rep;r['source_mesh_preserved']=False;r['access_slot_rejections']=rejections;(dst/'verification/access_slot_proposals.json').write_text(json.dumps({'accepted':accepted,'rejections':rejections,'channel_cut_limit_mm3':max_channel_volume},indent=2));print('ACCESS_SLOT_TOTAL',pid,len(accepted),'removed',rep['removed_volume_mm3'],flush=True)
 if not accepted:return {'no_accepted_slots':True,'rejections':rejections}
 teeth=union([c for c in material_components(teeth) if (c^part).volume()>.005 and (c^fin).volume()>.005]);fin=union([c for c in material_components(fin) if (c^teeth).volume()>.005]);n['source_f']=n.get('source_f',n['f']).copy();n['v'],n['f']=vf(part);n['removed_body_v'],n['removed_body_f']=vf(original-part);n['fin_v'],n['fin_f']=vf(fin);n['teeth_v'],n['teeth_f']=vf(teeth);r.update(support_count=len(r['segments']),support_volume_mm3=float((fin+teeth).volume()),body_part_overlap_mm3=float((fin^part).volume()),teeth_part_overlap_mm3=float((teeth^part).volume()));np.savez_compressed(dst/'parts'/f'{pid}.npz',**n);(dst/'design'/f'{pid}.json').write_text(json.dumps(r,ensure_ascii=False,indent=2),encoding='utf8');run(pid,label);d=check(pid,label);d=refine(pid,label);fr=fit(pid,label);g=geom(pid,label);print('ACCESS_SLOT_NATIVE',pid,d['external_island_count'],d['critical_external_count'],fr['fit_and_pose_geometry_passed'],g['geometric_constraints_passed'],flush=True);return d
if __name__=='__main__':trial(*sys.argv[1:])
