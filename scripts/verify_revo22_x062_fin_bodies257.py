"""Withdrawal of individual fin bodies after connector material is fully cleared."""
import sys,json,numpy as np,math
from build_revo22_x062_open242 import S,OLD,put,sha
from build_revo22_fins import solid,vf,union,box
from o22_material_components import material_components
from verify_revo22_x062_removal245 import exact_clear
label=sys.argv[1];D=S/'candidates/X062'/label;n=np.load(D/'parts/X062.npz');d=json.loads((D/'design/X062.json').read_text());body=solid(n['v'],n['f']);fin=solid(n['fin_v'],n['fin_f']);teeth=solid(n['teeth_v'],n['teeth_f']);groups=material_components(fin);rows=[];out={}
for i,g in enumerate(groups,1):
 related=[]
 for q in d.get('local_route_repairs',[]):
  a=np.array(q['root'])
  if(g^box(a-[.3,.3,.15],a+[.3,.3,.15])).volume()>.005:related.append(q['removal_vector'])
 dirs=[[0.,0.,-1.]]+related+[[math.cos(a)*.8,math.sin(a)*.8,-1.]for a in np.arange(0,2*np.pi,np.pi/6)];good=None;tried=[]
 for dr in dirs:
  dr=np.array(dr);dr/=np.linalg.norm(dr)
  if any(np.allclose(dr,x)for x in tried):continue
  tried.append(dr);ok,_=exact_clear(g,body,dr*210)
  if ok:good=dr;break
 assert good is not None,i
 row=dict(id=f'S{i:02}',bounds_mm=list(g.bounding_box()),volume_mm3=float(g.volume()),bed_contact_mm2=float(g.slice(.1).area()),tooth_overlap_mm3=float((g^teeth).volume()),removal_vector=good.tolist(),continuous_sweep_distance_mm=210,continuous_body_clearance=True);assert row['bed_contact_mm2']>.01 and row['bounds_mm'][2]<1e-6 and row['tooth_overlap_mm3']>.005;rows.append(row);out[f'g{i}_v'],out[f'g{i}_f']=vf(g)
order=[];todo=list(range(len(groups)))
while todo:
 progress=False
 for i in sorted(todo,key=lambda i:abs(rows[i]['removal_vector'][2])):
  others=union([groups[j]for j in todo if j!=i]);ok,_=exact_clear(groups[i],others,np.array(rows[i]['removal_vector'])*210)
  if ok:order.append(rows[i]['id']);todo.remove(i);progress=True;break
 if not progress:break
assert not todo,todo
for idx,name in enumerate(order,1):next(r for r in rows if r['id']==name)['removal_order']=idx
contact=[]
for t in material_components(teeth):
 rec=dict(body_overlap_mm3=float((t^body).volume()),fin_overlap_mm3=float((t^fin).volume()));assert min(rec.values())>.005;contact.append(rec)
old=np.load(OLD/'parts/X062.npz');M=np.array(d['orientation']['matrix']);t=np.array(d['orientation']['source_translation_mm']);assert np.array_equal(old['source_v'],n['source_v'])and np.array_equal(old['f'],n['f']);err=float(np.max(np.abs(n['source_v']@M.T+t-n['v'])));assert err<1e-7 and(fin^body).volume()<1e-6
lengths=[q['free_vertical_mm']for q in d['teeth']]+[q['free_vertical_mm']for q in d.get('local_route_repairs',[])];v=np.concatenate([n['v'],n['fin_v'],n['teeth_v']]);report=dict(label=label,id='X062',parts_npz_sha256=sha(D/'parts/X062.npz'),body_shape_exactly_preserved=True,rigid_transform_error_mm=err,fin_body_intersection_mm3=float((fin^body).volume()),all_fins_bed_rooted=True,fin_count=len(groups),fin_bodies=rows,connected_tooth_components=contact,nominal_neck_xy_mm=[.8,.8],neck_vertical_free_length_mm=dict(min=min(lengths),median=float(np.median(lengths)),max=max(lengths)),envelope_mm=(v.max(0)-v.min(0)).tolist(),support_volume_mm3=float((fin+teeth).volume()),old_support_volume_mm3=194203.47766082024,geometric_support_volume_reduction_percent=100*(1-(fin+teeth).volume()/194203.47766082024),fin_withdrawal_order=order,all_fin_bodies_have_continuous_body_and_other_fin_clearance=True,withdrawal_condition='All yellow connector material, including intersecting branches, has been cleared out of each fin withdrawal path. This check is for fin bodies. It does not assert one scissors cut per drawn tooth will release every merged connector.',scissors_operation_and_force_not_simulated=True,physical_print_tested=False)
put(D/'verification/trial_geometry.json',report);np.savez_compressed(D/'verification/fin_groups.npz',**out);print('FIN257_PASS',len(groups),'support_mm3',report['support_volume_mm3'],'lengths',report['neck_vertical_free_length_mm'],'envelope',report['envelope_mm'],flush=True)
