"""Complete C7 clavicle stock installation checks."""
from pathlib import Path
src=Path('scripts/check_o22f7_clavicle_c7_preassembly.py').read_text('utf-8-sig');head=src.split("fixed['left_root']=p['root']")[0];head=head.replace("check('left_root_into_bare_chest',{'root':p['root']},fixed,rootpath,tol=.02)",'');exec(head)
checks=[]
def save():put(C/'W005_C7_stock_review.json',{'candidate_sha256':sha(C/'W005_C7.npz'),'checks':checks,'physical_assembly_tested':False})
def choose_entry(name,s,fix):
 for axis in [np.array([0,0,-1.]),np.array([0,0,1.]),*D]:
  path=[np.zeros(3),axis*110]
  if translations_clear(s,fix,path):return check(name,{name:s},fix,[list(q)+[0,0,0] for q in path],tol=.02)
  for hh in [3,6,9,12,16,20]:
   start=axis*hh
   if not translations_clear(s,fix,[np.zeros(3),start]):continue
   for d in D:
    path=[np.zeros(3),start,start+d*110]
    if translations_clear(s,fix,path):return check(name,{name:s},fix,[list(q)+[0,0,0] for q in path],tol=.02)
 raise RuntimeError('No stock path '+name)
fixed={'chest':chest}
for k in stock[:3]:choose_entry('left_'+k,leftstock[k],fixed);fixed['left_'+k]=leftstock[k]
rot=[0,0,0,0,0,-20];fixed.update({'left_root':b.g.move(p['root'],matrix(rot)),**{'left_'+k:leftstock[k] for k in stock[3:]}})
x.begin(x.g['steps'][10]);rf=I@x.mount;right=shape('frame/clavicle_r.protract_frame')
for k in stock[:3]:choose_entry('right_'+k,rightstock[k],fixed);fixed['right_'+k]=rightstock[k]
fixed['right']=right
for k in stock[3:]:choose_entry('right_'+k,rightstock[k],fixed);fixed['right_'+k]=rightstock[k]
check('left_root_return_after_right_stock',{'root':p['root']},{k:v for k,v in fixed.items() if k!='left_root'},[rot,[0,0,0,0,0,0]],tol=.02)
print('ALL_STOCK',all(r['passed'] for r in checks),flush=True)
