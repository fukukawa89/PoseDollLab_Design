"""Study whether changing only the free connecting beam can open a direct assembly route."""
from o22f7_animation import *
from build_revo22_assembly import b
import itertools,numpy as np
x=Build();st=x.g['steps'][3];x.begin(st);key='frame/'+st['child']
def shape(k):
 o=x.obs[k];m=x.scene['meshes'][o['mesh']];return b.g.move(b.b.from_tri_exact(x.verts[m['first']:m['first']+m['count'],:3].reshape(-1,3,3)),x.mats[k])
original=shape(key);pp=b.b.L.libraries()['hinge'][0];guards=[]
for module,part,owner in [(st['id'],'lever_cup','child'),('clavicle_l.elevate','base_sensor_half','parent')]:
 bb=np.array(pp[part].bounding_box());guard=b.b.box(bb[:3]-2,bb[3:]+2);guard=b.g.move(guard,x.owners[(module,owner)]);guards.append(guard)
protected=guards[0]+guards[1];ends=original^protected;free=original-protected
print('retained components',b.g.solid_count(ends),'removed volume',free.volume(),flush=True)
fixed={k:shape(k) for k in ['frame/chest',st['id']+'/M3_nut',st['id']+'/M3_reaction_washer',st['id']+'/inner_M4_wide']};bounds={k:np.array(s.bounding_box()) for k,s in fixed.items()};rows=[];solutions=[]
for d in sorted([v for v in itertools.product([0,-1,1],repeat=3) if any(v)],key=lambda v:sum(z*z for z in v)):
 delta=x.direction(np.array(d)*150/np.linalg.norm(d));peak=0;bad=None
 for p in np.linspace(0,1,151):
  s=ends.translate(delta*p);bb=np.array(s.bounding_box())
  for k,f in fixed.items():
   if np.any(np.minimum(bb[3:],bounds[k][3:])<=np.maximum(bb[:3],bounds[k][:3])+1e-6):continue
   vol=float((s^f).volume());peak=max(peak,vol)
   if vol>.02:bad={'fraction':float(p),'obstacle':k,'volume':vol};break
  if bad:break
 row={'direction_local':list(d),'passed':bad is None,'maximum_overlap_mm3':peak,'first_conflict':bad};rows.append(row)
 if bad is None:solutions.append(row);print('CLEAR ENDPOINTS',d,peak,flush=True)
put(WORK/'clavicle_beam_repath_feasibility.json',{'status':'ENDPOINT_CLEARANCE_STUDY_ONLY','manufacturing_changed':False,'protected_endpoint_margin_mm':2,'solutions':solutions,'attempts':rows,'end_components':b.g.solid_count(ends),'removed_free_beam_mm3':float(free.volume())})
np.savez_compressed(WORK/'clavicle_endpoint_study.npz',retained_ends=b.g.tri(ends),protected_guards=b.g.tri(protected),original=b.g.tri(original))
print('DONE endpoint candidates',len(solutions),flush=True)
