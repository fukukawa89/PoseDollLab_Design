"""X062 R2: preserve physically fitted R1 body; protect radial cap nut access."""
from pathlib import Path
import json,sys,copy,numpy as np
from build_revo22_fins import solid,vf,box,union,md,write_stl
from route_revo22_x062244 import tooth
from o22_material_components import material_components
from build_revo22_x062_open242 import R,B,put,sha
S=B/'a1mini_fins_v4/x062_trial_r2';D=B/'X062_SupportTrial_R1'

def baseline():
 n=dict(np.load(D/'parts/X062.npz'));d=json.loads((D/'design/X062.json').read_text());s=solid(n['v'],n['f']);fin=solid(n['fin_v'],n['fin_f']);tt=[];rows=[]
 for i,q in enumerate(d['teeth']):
  a=np.array([q['x'],q['root_y'],max(.4,q['roof']-q['free_vertical_mm']-.3)]);b=np.array([q['x'],q['y'],q['roof']+.18]);tt.append(tooth(a,b));rows.append(dict(id='B%03d'%i,kind='baseline',index=i,root=a.tolist(),tip=b.tolist(),record=q))
 for i,q in enumerate(d['local_route_repairs']):
  a=np.array(q['root']);b=np.array(q['target'])+[0,0,.24];tt.append(tooth(a,b));rows.append(dict(id='L%03d'%i,kind='local',index=i,root=a.tolist(),tip=b.tolist(),record=q))
 old=solid(n['teeth_v'],n['teeth_f']);u=union(tt);assert (u-old).volume()+(old-u).volume()<1e-4
 return n,d,s,fin,tt,rows

def guards():
 nuts=json.loads((S/'nearby_all_nuts.json').read_text());out=[];rows=[]
 for q in nuts:
  if 'clavicle_r.elevate/magnet_cap_nut_' not in q['name']:continue
  x=float(q['name'].split('_')[-1]);A=np.array(q['hardware_to_print']);ang=np.arange(6)*np.pi/3;r=4.3/np.sqrt(3)+.30
  pocket=md.CrossSection([np.c_[r*np.cos(ang)+x,r*np.sin(ang)]]).extrude(2.4).translate([0,0,5.75])
  access=box([7.6 if x>0 else -23,-2.5,5.75],[23 if x>0 else -7.6,2.5,8.10]);bore=md.Manifold.cylinder(5.9,1.4,1.4,48).translate([x,0,5.4]);g=(pocket+access+bore).transform(A[:3,:]);out.append(g);rows.append(dict(name=q['name'],hardware_to_print=A.tolist(),local_radial_entry_x_mm=[7.6,23]if x>0 else[-23,-7.6],local_y_mm=[-2.5,2.5],local_z_mm=[5.75,8.1],mouth_margin_mm=.3,bounds_mm=list(g.bounding_box())))
 assert len(out)==2
 return union(out),out,rows

def build(label,selected=None,spacing=3.0):
 n,d,body,fin,tt,rows=baseline();guard,gs,gr=guards();bad=[i for i,t in enumerate(tt)if (t^guard).volume()>1e-7];available=[i for i in range(len(tt))if i not in bad]
 if selected is None:
  keep=[i for i in available if rows[i]['record'].get('critical_foundation')]
  for i in sorted(available,key=lambda i:(rows[i]['tip'][2],np.linalg.norm(np.array(rows[i]['tip'])-rows[i]['root']))):
   if i not in keep and min((np.linalg.norm(np.array(rows[i]['tip'])-rows[j]['tip'])for j in keep),default=999)>=spacing:keep.append(i)
 else:keep=[i for i in selected if i in available]
 keep=sorted(set(keep));teeth=union([tt[i]for i in keep]);fin=union([g for g in material_components(fin-guard)if g.bounding_box()[2]<1e-6 and (g^teeth).volume()>.005]);teeth=union([t for t in material_components(teeth)if(t^body).volume()>.005 and(t^fin).volume()>.005])
 # Individual authored records must have genuine fin and body contact; do not hide detached teeth.
 for i in keep:assert(tt[i]^fin).volume()>.005 and(tt[i]^body).volume()>.005,rows[i]['id']
 assert (fin^body).volume()<1e-6 and(teeth^guard).volume()<1e-7
 p=S/'candidates/X062'/label
 for sub in ['parts','design','verification','projects','stl']:(p/sub).mkdir(parents=True,exist_ok=True)
 n['fin_v'],n['fin_f']=vf(fin);n['teeth_v'],n['teeth_f']=vf(teeth);np.savez_compressed(p/'parts/X062.npz',**n)
 d.update(trial=label,published_version='X062 support trial R2 candidate',physical_print_tested=False,baseline_R1_physically_printed_and_nut_fit_confirmed_except_one_blocked_cap_hole=True,teeth=[rows[i]['record']for i in keep if rows[i]['kind']=='baseline'],local_route_repairs=[rows[i]['record']for i in keep if rows[i]['kind']=='local'],retained_R1_tooth_indices=keep,tooth_count=len(keep),baseline_R1_tooth_count=len(tt),protected_features=gr,support_count=len(material_components(fin)),support_volume_mm3=float((fin+teeth).volume()),previous_support_volume_mm3=10675.341945198688,status='R2 reduced connector candidate; native slice audit required',native_previous_label=None)
 put(p/'design/X062.json',d);rep=dict(label=label,parts_npz_sha256=sha(p/'parts/X062.npz'),selected_indices=keep,forbidden_indices=bad,forbidden_ids=[rows[i]['id']for i in bad],baseline_tooth_count=len(tt),new_tooth_count=len(keep),reduction_percent=100*(1-len(keep)/len(tt)),body_vertices_exact_R1=bool(np.array_equal(n['v'],np.load(D/'parts/X062.npz')['v'])),body_faces_exact_R1=True,guards=gr,baseline_guard_tooth_collision_mm3=[float((union(tt)^g).volume())for g in gs],new_guard_tooth_collision_mm3=[float((teeth^g).volume())for g in gs],new_guard_fin_collision_mm3=[float((fin^g).volume())for g in gs],guard_scope='Both radial nut insertion corridors, hex pockets, cap screw bores and 0.30 mm mouth margin. Permanent part body is untouched.',support_count=d['support_count'])
 put(p/'verification/reduction.json',rep);put(p/'verification/geometry.json',rep)
 for name,s in [('body',body),('fins',fin),('teeth',teeth),('combined',body+fin+teeth),('protected_access',guard)]:write_stl(p/'stl'/('X062_'+name+'.stl'),s)
 gv,gf=vf(guard);np.savez_compressed(p/'verification/protected_access.npz',v=gv,f=gf)
 print('R2_BUILT',label,'teeth',len(keep),'from',len(tt),'forbidden',rep['forbidden_ids'],'guard_before',rep['baseline_guard_tooth_collision_mm3'],'fins',d['support_count'],flush=True)
 return rep
if __name__=='__main__':build(sys.argv[1],spacing=float(sys.argv[2])if len(sys.argv)>2 else 3.)
