from pathlib import Path
p=Path('scripts/check_o22f7_clavicle_c3_preassembly.py');src=p.read_text('utf-8-sig').split("z=np.load(C/'W005_C3.npz')")[0].replace('W005_C3','W005_C4')
src+=r'''
import itertools
z=np.load(C/'W005_C4.npz');p={k:b.b.from_tri_exact(z[k]) for k in z.files};chest=shape('frame/chest');stock=['M3_nut','M3_reaction_washer','inner_M4_wide','outer_M4_wide','spring_1','spring_2','front_M4_washer','shoulder_D4_L8_M3_thread6'];leftstock={k:shape('clavicle_l.protract/'+k) for k in stock};rightstock={k:shape('clavicle_r.protract/'+k) for k in stock};rootpath=read(C/'proximal_root_escape_candidate.json')['path'];fixed={'chest':chest,**{'left_'+k:v for k,v in leftstock.items() if k in stock[:3]}}
check('left_root_into_bare_chest',{'root':p['root']},fixed,rootpath,tol=.02)
D=[np.array(d,float)/np.linalg.norm(d) for d in itertools.product([0,-1,1],repeat=3) if any(d)]
def translations_clear(s,fix,path):
 bounds={k:np.array(f.bounding_box()) for k,f in fix.items()}
 for a,c in zip(path,path[1:]):
  a=np.array(a,float);c=np.array(c,float)
  for t in np.linspace(0,1,max(2,math.ceil(np.linalg.norm(c-a)/.75)+1)):
   q=a+(c-a)*t;ss=s.translate(q);bb=np.array(ss.bounding_box())
   for k,f in fix.items():
    bo=bounds[k]
    if np.any(np.minimum(bb[3:],bo[3:])<=np.maximum(bb[:3],bo[:3])+1e-7):continue
    if(ss^f).volume()>.02:return False
 return True

def entry(name,s,fix,axis=(0,0,1)):
 axis=np.array(axis,float);path=[np.zeros(3),axis*40];found=translations_clear(s,fix,path)
 if not found:
  for h in [4,8,12,16,18,19,20]:
   start=axis*h
   if not translations_clear(s,fix,[np.zeros(3),start]):continue
   for d in D:
    trial=[np.zeros(3),start,start+d*110]
    if translations_clear(s,fix,trial):path=trial;found=True;break
   if found:break
 six=[list(map(float,q))+[0,0,0] for q in path]
 return check(name,{name:s},fix,six,tol=.02)
fixed['left_root']=p['root']
for k in stock[3:]:
 entry('left_'+k,leftstock[k],fixed);fixed['left_'+k]=leftstock[k]
# Park only the already secured left rotor; the friction stack stays on its axis.
rot=[0,0,0,0,0,-20];check('park_left_root',{'root':p['root']},{k:v for k,v in fixed.items() if k!='left_root'},[[0,0,0,0,0,0],rot],tol=.02)
fixed['left_root']=b.g.move(p['root'],matrix(rot))
x.begin(x.g['steps'][10]);rf=I@x.mount;right=shape('frame/clavicle_r.protract_frame')
for k in stock[:3]:fixed['right_'+k]=rightstock[k]
rightpath=read(WORK/'clavicle_right_parked_left_goal_0_1_path.json')['path']
check('right_frame_with_left_root_parked',{'right':right},fixed,rightpath,frame=rf,tol=.02)
fixed['right']=right
check('return_left_root',{'root':p['root']},{k:v for k,v in fixed.items() if k!='left_root'},[rot,[0,0,0,0,0,0]],tol=.02)
fixed['left_root']=p['root']
for k in ['nut_0','nut_1']:
 entry(k,p[k],fixed);fixed[k]=p[k]
check('left_distal_after_right',{'distal':p['distal']},fixed,[[0,0,0,0,0,0],[0,0,-110,0,0,0]])
fixed['distal']=p['distal']
for k in ['screw_0','screw_1']:
 check(k+'_entry',{k:p[k]},fixed,[[0,0,0,0,0,0],[0,0,-40,0,0,0]]);fixed[k]=p[k]
allfixed={k:shape(k) for k in x.obs if k!='frame/clavicle_l.protract_frame'};allfixed.update(root=p['root'],distal=p['distal'])
for k in ['nut_0','nut_1','screw_0','screw_1']:check(k+'_final_all_parts',{k:p[k]},allfixed,[[0,0,0,0,0,0],[0,0,0,0,0,0]])
'''
Path('scripts/check_o22f7_clavicle_c4_preassembly.py').write_text(src,encoding='utf8')
p=Path('scripts/check_o22f7_clavicle_c3_function.py');src=p.read_text('utf-8-sig').replace('W005_C3','W005_C4');src=src.replace("C=WORK/", "def freeze(s):\n s.volume();return b.b.from_tri_exact(b.g.tri(s))\nC=WORK/");src=src.replace("combined=new['root']+new['distal']","combined=freeze(new['root']+new['distal'])").replace('added=combined-original','added=freeze(combined-original)').replace('added+=new[k]','added=freeze(added+new[k])');Path('scripts/check_o22f7_clavicle_c4_function.py').write_text(src,encoding='utf8')
