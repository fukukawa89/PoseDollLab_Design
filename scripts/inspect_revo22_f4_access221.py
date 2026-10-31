"""Read-only search for a short, broad bed fin through a non-contact access opening. No existing reports or meshes are edited."""
from pathlib import Path
import sys,json,numpy as np,math
from collections import Counter
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'scripts'))
from build_revo22_fins import solid,box,union,vf,md
from o22_material_components import material_components
from repair_revo22_f4_guarded_chamfer import context
O=R/'Hardware/PoseDoll44/bench/revO22/a1mini_fins_v4'
def inspect(pid,label):
 p=O/'candidates'/pid/label;n=np.load(p/'parts'/f'{pid}.npz');d=json.loads((p/'design'/f'{pid}.json').read_text());q=json.loads((p/'verification/full_bead_contacts_v5.json').read_text());s=solid(n['v'],n['f']);it=json.loads((p/'verification/plate_manifest.json').read_text())['items'][0];M=np.array(it['rotation_matrix']);off=np.array(it['translation_mm']);parts,key,T=context(d,pid);others=[]
 for k,v in parts.items():
  if k==key:continue
  v=v.transform(T[:3,:]);b=np.array(v.bounding_box())
  if b[2]<13 and b[5]>0 and b[0]<12 and b[3]>-4 and b[1]<18 and b[4]>5:others.append((k,v,b))
 rows=[];why=Counter()
 for issue in q['external_islands']:
  if not 8<issue['z_mm']<12:continue
  b=issue['bounds_mm'];target=(np.array([(b[0]+b[2])/2,(b[1]+b[3])/2,issue['z_mm']-.1])-off)@M
  for height in[8.2,8.6,9.0]:
   for angle in[90,75,105,60,120,45,135,0]:
    a=math.radians(angle);A=np.array([[math.cos(a),-math.sin(a),0],[math.sin(a),math.cos(a),0],[0,0,1]])
    for dx in[-.6,-1.,-1.4,-1.8,-2.2]:
     for dy in[0.,-.6,.6,-1.2,1.2]:
      w=4.;th=1.6;c=target[:2]+[dx,dy];cutter=box([-w/2-.32,-th/2-.32,-.01],[w/2+.32,th/2+.32,height+.32]).transform(np.c_[A,[*c,0.]]);removed=s^cutter;vol=float(removed.volume())
      if not .001<vol<60:why['volume']+=1;continue
      rb=np.array(removed.bounding_box());near=[]
      for k,v,bb in others:
       sep=np.maximum(np.maximum(rb[:3]-bb[3:],bb[:3]-rb[3:]),0)
       if np.linalg.norm(sep)>.21:continue
       gap=float(removed.min_gap(v,.21))
       if gap<.199:near.append(k)
      if near:
       why['contact']+=1
       if why['contact']<10:print('ACCESS221_CONTACT',height,angle,dx,dy,vol,near,flush=True)
       continue
      new=s-cutter
      if len(material_components(new))!=len(material_components(s)):why['connectivity']+=1;continue
      losses=[removed.slice(float(z)).area()/max(s.slice(float(z)).area(),1e-9)for z in np.arange(.1,height+.4,.2)]
      if max(losses)>.10:why['section_loss']+=1;continue
      core=box([-w/2,-th/2,0],[w/2,th/2,height]).transform(np.c_[A,[*c,0.]]);root=box([-1.2,-.6,height-.25],[1.2,.6,height+.1]).transform(np.c_[A,[*c,0.]]);cap=box([target[0]-.5,target[1]-.6,target[2]-.15],[target[0]+.5,target[1]+.6,target[2]+.3]);tooth=md.Manifold.hull_points(np.r_[vf(root)[0],vf(cap)[0]]);bite=float((tooth^new).volume())
      if not .015<bite<3:why['bite']+=1;continue
      row={'native_issue':issue,'target':target.tolist(),'xy_mm':c.tolist(),'angle_deg':angle,'height_mm':height,'fin_width_mm':w,'fin_thickness_mm':th,'removed_volume_mm3':vol,'largest_global_layer_area_fraction_removed':max(losses),'contact_clearance_mm':.199,'part_bite_mm3':bite};rows.append(row);print('ACCESS221_FEASIBLE',row,flush=True)
 rows.sort(key=lambda q:q['removed_volume_mm3']);out={'read_only':True,'id':pid,'label':label,'options':rows[:20],'rejections':dict(why)};(p/'verification/access_feasibility221.json').write_text(json.dumps(out,indent=2));print('ACCESS221_DONE',len(rows),dict(why),flush=True)
if __name__=='__main__':inspect(*sys.argv[1:])
