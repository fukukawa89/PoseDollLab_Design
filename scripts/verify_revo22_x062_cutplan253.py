"""Concrete middle-of-neck scissor cuts and continuous extraction, including residual tips."""
import sys,json,numpy as np,math
from build_revo22_x062_open242 import S,OLD,put,sha
from build_revo22_fins import solid,vf,union,box
from o22_material_components import material_components
from route_revo22_x062244 import tooth
from verify_revo22_x062_removal245 import exact_clear

def run(label):
 folder=S/'candidates/X062'/label;n=np.load(folder/'parts/X062.npz');d=json.loads((folder/'design/X062.json').read_text());body=solid(n['v'],n['f']);fin=solid(n['fin_v'],n['fin_f']);teeth=solid(n['teeth_v'],n['teeth_f']);rebuilt=[];cuts=[];bands=[]
 pairs=[]
 for q in d['teeth']:pairs.append((np.array([q['x'],q['root_y'],max(.4,q['roof']-q['free_vertical_mm']-.3)]),np.array([q['x'],q['y'],q['roof']+.18]),q['roof'],q['cut_height_mm']-.4))
 for q in d.get('local_route_repairs',[]):pairs.append((np.array(q['root']),np.array(q['target'])+[0,0,.24],q['target'][2],q['cut_z_mm']-.4))
 for a,b,roof,cz in pairs:
  rebuilt.append(tooth(a,b));p=a+(b-a)*((cz-a[2])/(b[2]-a[2]));u=a+(b-a)*((cz-.10-a[2])/(b[2]-a[2]));v=a+(b-a)*((cz+.10-a[2])/(b[2]-a[2]));band=tooth(u,v,.86);assert(band^body).volume()<1e-6;bands.append(band);cuts.append(dict(point=p.tolist(),cut_band_vertical_mm=.2,neck_xy_mm=[.8,.8],nominal_distance_above_root_mm=float(cz-a[2]),distance_to_part_mm=float(roof-cz)))
 # Two long diagonal branch links require one extra cut each after their upper cuts.
 for idx in [109,116]:
  q=d['local_route_repairs'][idx];a=np.array(q['root']);b=np.array(q['target'])+[0,0,.24];cz=(a[2]+q['target'][2])/2;p=a+(b-a)*((cz-a[2])/(b[2]-a[2]));u=a+(b-a)*((cz-.1-a[2])/(b[2]-a[2]));v=a+(b-a)*((cz+.1-a[2])/(b[2]-a[2]));band=tooth(u,v,.86);assert(band^body).volume()<1e-6;bands.append(band);cuts.append(dict(point=p.tolist(),cut_band_vertical_mm=.2,neck_xy_mm=[.8,.8],extra_branch_cut=True,route_index=idx,label='B'+str(len([c for c in cuts if c.get('extra_branch_cut')])+1)))
 rebuilt=union(rebuilt);error=float((teeth-rebuilt).volume()+(rebuilt-teeth).volume());assert error<1e-4,error
 cuttool=union(bands);clipped=fin+(teeth-cuttool);pieces=material_components(clipped);attached=[];groups=[];offcuts=[]
 for p in pieces:
  if(p^body).volume()>.00001:attached.append(p)
  elif(p^fin).volume()>.005:groups.append(p)
  else:offcuts.append(p)
 fixed=body+union(attached);assert(fixed^fin).volume()<1e-6,('Fin still connected to body',(fixed^fin).volume());assert abs(float((union(groups)^fin).volume())-float(fin.volume()))<1e-4
 rows=[];out={}
 for i,g in enumerate(groups,1):
  related=[]
  for q in d.get('local_route_repairs',[]):
   a=np.array(q['root'])
   if(g^box(a-[.3,.3,.15],a+[.3,.3,.15])).volume()>.005:related.append(q['removal_vector'])
  dirs=[[0.,0.,-1.]]+related+[[math.cos(a)*.8,math.sin(a)*.8,-1.]for a in np.arange(0,2*np.pi,np.pi/6)];good=None;attempts=[]
  for dr in dirs:
   dr=np.array(dr);dr/=np.linalg.norm(dr)
   if any(np.allclose(dr,x)for x in attempts):continue
   attempts.append(dr);ok,checks=exact_clear(g,fixed,dr*210)
   if ok:good=dr;break
  print('MIDCUT_GROUP',i,'of',len(groups),'clear',good is not None,flush=True)
  rows.append(dict(id=f'S{i:02}',bounds_mm=list(g.bounding_box()),volume_mm3=float(g.volume()),removal_vector=good.tolist()if good is not None else None,swept_distance_mm=210,continuous_sweep_passed=good is not None));out[f'g{i}_v'],out[f'g{i}_f']=vf(g)
 out['retained_teeth_v'],out['retained_teeth_f']=vf(union(attached));np.savez_compressed(folder/'verification/removal_groups.npz',**out)
 old=np.load(OLD/'parts/X062.npz');M=np.array(d['orientation']['matrix']);t=np.array(d['orientation']['source_translation_mm']);same=np.array_equal(n['source_v'],old['source_v'])and np.array_equal(n['f'],old['f']);err=float(np.max(np.abs(n['source_v']@M.T+t-n['v'])));assert same and err<1e-7
 report=dict(id='X062',label=label,parts_npz_sha256=sha(folder/'parts/X062.npz'),original_mesh_exactly_preserved=same,source_transform_error_mm=err,teeth_reconstruction_difference_mm3=error,cut_count=len(cuts),cuts=cuts,cut_instruction='Cut each long yellow neck at the marked point, 1.2-1.5 mm below the body. Remove the fins in the numbered order, then trim the short yellow tips remaining on the body.',remaining_support_groups=len(groups),loose_small_offcuts=len(offcuts),groups=rows,all_groups_have_continuous_body_clearance=all(r['continuous_sweep_passed']for r in rows),fin_body_intersection_mm3=float((fin^body).volume()),post_cut_fin_to_part_connection_mm3=float((fixed^fin).volume()),scope='Continuous sweep tests include both permanent body and all tooth material still attached after the explicit cuts. Sequence must also clear other detached supports. Scissor force and physical material behaviour are not simulated.',physical_print_tested=False)
 put(folder/'verification/removal.json',report);assert report['all_groups_have_continuous_body_clearance']
 # Find a concrete sequence clearing every remaining support as well as the body.
 todo=list(range(len(groups)));order=[]
 while todo:
  progress=False
  for i in sorted(todo,key=lambda i:abs(rows[i]['removal_vector'][2])):
   obstacles=union([groups[j]for j in todo if j!=i]);dr=np.array(rows[i]['removal_vector']);ok,_=exact_clear(groups[i],obstacles,dr*210)
   if ok:order.append(rows[i]['id']);todo.remove(i);progress=True;print('REMOVE_IN_ORDER',rows[i]['id'],'remaining',len(todo),flush=True);break
  if not progress:break
 report.update(removal_order=order,all_groups_clear_other_supports_in_order=not todo,unresolved_order_groups=[rows[i]['id']for i in todo]);put(folder/'verification/removal.json',report);assert not todo,report['unresolved_order_groups'];print('MIDCUT249_PASS',label,len(groups),len(cuts),flush=True)
if __name__=='__main__':run(sys.argv[1])




