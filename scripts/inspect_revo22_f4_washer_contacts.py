from pathlib import Path
import sys,json,numpy as np
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'scripts'))
from repair_revo22_f4_guarded_chamfer import context,O
from build_revo22_fins import solid,box,union,md,vf
from o22_cross_section_geometry import polygon
from o22_reference_mesh import reference_solid

def contact_sides(washer,old,new):
 # A metadata frame need not align its Z axis with the physical washer axis.
 # Recover the thin axis and disk centre from the actual washer mesh.
 v=vf(washer)[0];center=v.mean(0);eig,Q=np.linalg.eigh(np.cov((v-center).T));axis=Q[:,0];u=Q[:,1];tangent=np.cross(axis,u);A=np.array([u,tangent,axis]);Ti=np.c_[A,-A@center];w=washer.transform(Ti);a=old.transform(Ti);b=new.transform(Ti);wb=w.bounding_box();section=polygon(w.slice((wb[2]+wb[5])/2));vv=vf(w)[0];outer=float(np.linalg.norm(vv[:,:2],axis=1).max());samples=[]
 for z in [wb[2]-.002,wb[5]+.002]:
  pa=polygon(a.slice(z)).intersection(section);pb=polygon(b.slice(z)).intersection(section);loss=pa.difference(pb);ring=md.Manifold.cylinder(1.,outer,outer,128)-md.Manifold.cylinder(1.01,max(0,outer-1),max(0,outer-1),128);ring=ring.translate([0,0,z if z>wb[5] else z-1]);lost=float(((a-b)^ring).volume());samples.append({'outer_1mm_bearing_ring_lost_volume_mm3':lost,'z':z,'original_contact_area_mm2':pa.area,'new_contact_area_mm2':pb.area,'lost_area_mm2':loss.area,'retained_fraction':pb.area/max(pa.area,1e-12),'lost_bounds':list(loss.bounds)if not loss.is_empty else []})
 supported=[x for x in samples if x['original_contact_area_mm2']>.1];approved=bool(supported)and all(x['retained_fraction']>=.98 and x['outer_1mm_bearing_ring_lost_volume_mm3']<1e-6 for x in supported)
 return {'entry_chamfer_geometric_criteria_passed':approved,'washer_local_bounds':list(wb),'washer_axis_from_actual_mesh':axis.tolist(),'washer_center':center.tolist(),'contact_sides':samples,'scope':'Physical disk axis is recovered from the actual washer geometry, independent of metadata frame axes. At least 98% of original washer contact area and the entire outer 1 mm bearing ring through 1 mm of original backing must remain. Geometry only, not a load test.'}
def assess(pid,label):
 p=O/'candidates'/pid/label;n=np.load(p/'parts'/f'{pid}.npz');r=json.loads((p/'design'/f'{pid}.json').read_text());parts,key,T=context(r,pid)
 import repair_revo22_f4_guarded_chamfer as ctx
 old=reference_solid(n,r).transform(np.linalg.inv(T)[:3,:]);new=solid(n['v'],n['f']).transform(np.linalg.inv(T)[:3,:]);cuts=union([box(q['local_bounds_mm'][:3],q['local_bounds_mm'][3:])for q in r['body_change']['chamfers']]).transform(np.linalg.inv(T)[:3,:]);delta=(old-new)^cuts;rows=[]
 for k,s in parts.items():
  sku=ctx.CACHE[1][k].get('sku')or''
  if k==key or not sku.startswith('W_')or float(delta.min_gap(s,.08))>=.08:continue
  row=contact_sides(s,old,new);row.update(part=k,sku=sku);rows.append(row);print('WASHER_CONTACT',pid,k,row['entry_chamfer_geometric_criteria_passed'],flush=True)
 (p/'verification/washer_contact_surfaces.json').write_text(json.dumps(rows,indent=2));return rows
if __name__=='__main__':assess(*sys.argv[1:])
