"""Small bed-rooted contacts below newly split root edges, driven by native islands."""
from o22f7_animation import *
import o22f7_native as h,trimesh
from build_revo22_assembly import b
C=WORK/'structure_revision';O=C/'print_candidate';W=C/'native_print_review';pid='W005A';n=dict(np.load(O/f'parts/{pid}.npz'));body,fin,teeth=[h.solid(n[v],n[f]) for v,f in [('v','f'),('fin_v','fin_f'),('teeth_v','teeth_f')]];g=np.load(O/f'guards/{pid}.npz');guard=h.solid(g['v'],g['f']);mesh=trimesh.Trimesh(n['v'],n['f'],process=False);it=read(O/'changed_plates.json')['plates'][1]['items'][0];M=np.array(it['rotation_matrix']);t=np.array(it['translation_mm']);rows=[];freeze=lambda s:b.b.from_tri_exact(b.g.tri(s))
rep=read(W/'plates/D15/support_paths.json')
for issue in rep['external_islands']+rep['critical_external_runs']:
 bb=issue['bounds_mm'];p=(np.r_[(np.array(bb[:2])+bb[2:])/2,issue['z_mm']]-t)@M;done=False
 for radius in [0,.2,.4,.6]:
  for angle in ([0] if radius==0 else np.arange(0,2*np.pi,np.pi/4)):
   xy=p[:2]+radius*np.array([np.cos(angle),np.sin(angle)]);hh,_,ff=mesh.ray.intersects_location([[*xy,-.1]],[[0,0,1]],multiple_hits=True)
   if not len(hh):continue
   ix=np.argmin(hh[:,2]);hit=hh[ix];roof=float(hit[2])
   if abs(roof-p[2])>1 or mesh.face_normals[ff[ix],2]>-.1 or roof<.6:continue
   core=h.box([*list(xy-.6),0],[*list(xy+.6),max(.3,roof-.4)]);tooth=h.box([*list(xy-.4),max(0,roof-.65)],[*list(xy+.4),max(roof+.2,p[2]+.15)])
   if(core^body).volume()>1e-6 or (tooth^body).volume()>.85 or(tooth^body).volume()<.01:continue
   if(core^guard).volume()>1e-6 or(tooth^guard).volume()>1e-6:continue
   fin=freeze(fin+core);teeth=freeze(teeth+tooth);rows.append({'native_island':issue,'root':[float(xy[0]),float(xy[1]),0.0],'tip':[float(xy[0]),float(xy[1]),max(roof+.2,p[2]+.15)],'bounds':list(core.bounding_box()),'body_bite_mm3':float((tooth^body).volume()),'removal_vector':[0,0,-1]});done=True;break
  if done:break
 assert done,('no direct contact',p.tolist())
assert len(h.material_components(body+fin+teeth))==1
n['fin_v'],n['fin_f']=h.vf(fin);n['teeth_v'],n['teeth_f']=h.vf(teeth);np.savez_compressed(O/f'parts/{pid}.npz',**n);d=read(O/f'design/{pid}.json');d['c7_bed_contacts']=d.get('c7_bed_contacts',[])+rows;put(O/f'design/{pid}.json',d);put(W/'contacts/W005A_bed.json',{'rows':rows,'npz_sha256':sha(O/f'parts/{pid}.npz')});print('CONTACTS',len(rows),flush=True)
