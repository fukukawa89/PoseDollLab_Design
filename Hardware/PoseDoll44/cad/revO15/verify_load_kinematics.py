"""Independent potential-energy derivative check against raw-axis moment selection.
Synthetic point masses occupy each actual CAD part COM; kinematics-only, no strength claim.
"""
from common import *
from layout_fullbody import *
from load_budget import raw_axes
from raw_paths import raw_state


def main():
 rows=[]
 for char in ('quinn','manny'):
  angles={'upperarm_l.abduct':30,'upperarm_r.abduct':30,'thigh_l.abduct':8,'thigh_r.abduct':8,'waist.flex':8,'chest.flex':6}
  _,meta,states,f,pr=build(char,angles,geometry=False)
  assert not f,f
  q={m['id']:np.array(m['angles_deg'],float) for m in states};module_parent={m['id']:m['parent'] for m in states}
  pts={};mass=.01
  for k,record in meta.items():
   lib=libraries()[next(m['kind'] for m in states if m['id']==record['module'])][0]
   # Each library part has a distinct, actual off-axis COM; no duplicated fused carriers.
   local=mesh_record(lib[k.split('/',1)[1]])['COM_mm'];pts[k]=np.r_[local,1.]
  children={n['id']:set() for n in pr['nodes']}
  for n in pr['nodes']:
   if n['parent'] in children:children[n['parent']].add(n['id'])
  def subtree(root):
   found={root};todo=[root]
   while todo:
    for c in children.get(todo.pop(),set()):
     if c not in found:found.add(c);todo.append(c)
   return found
  def potential(mm):return sum(mass*9.80665*(mm[k]['transform']@v)[2]/1000 for k,v in pts.items())
  h=1e-4
  for m in states:
   downstream=subtree(m['child'])
   for i,(origin,axis,owners) in enumerate(raw_axes(m)):
    moment=sum((np.cross(((meta[k]['transform']@v)[:3]-origin)/1000,[0,0,-9.80665*mass]) for k,v in pts.items() if meta[k]['body'] in downstream or meta[k]['module']!=m['id'] and module_parent.get(meta[k]['module']) in downstream or meta[k]['module']==m['id'] and meta[k]['owner'] in owners),np.zeros(3))
    expected=float(axis@moment);u=[]
    for sign in (-1,1):
     qs={k:v.copy() for k,v in q.items()};qs[m['id']][i]+=sign*h
     result,_,_=raw_state(char,qs);u.append(potential(result[1]))
    numerical=float(-(u[1]-u[0])/np.deg2rad(2*h));err=abs(expected-numerical)
    row={'character':char,'raw_axis':m['id']+'/r'+str(i),'cross_product_Nm':expected,'potential_derivative_Nm':numerical,'absolute_error_Nm':err,'pass':err<2e-5};rows.append(row);print(row,flush=True)
 save('load_kinematics_validation.json',{'tests':rows,'passed':sum(r['pass'] for r in rows),'total':len(rows),'method':'Central finite difference of full forward-kinematic gravitational potential; synthetic 10g per library solid. No measured masses or strengths.'})
if __name__=='__main__':main()
