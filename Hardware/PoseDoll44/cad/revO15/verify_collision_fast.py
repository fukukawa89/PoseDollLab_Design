from collision_fast import first_cross as fast
from search_adjacent import first_cross as slow
from layout_fullbody import *
rows=[]
for label,ang in list(read(H/'mechanical_manifest/revO_pose_cases.json')['cases'].items())[:8]+[('waist_roll',{'waist.roll':-25}),('clavicle30',{'clavicle_l.protract':30})]:
 p,m,_,_,_=build('quinn',ang,only=('waist','chest','thigh_l','upperarm_l','clavicle_l'));a=slow(p,m);b=fast(p,m);rows.append({'case':label,'same_collision_decision':bool(a)==bool(b),'old':a,'new':b});assert bool(a)==bool(b)
for name,shift,same,metal,expect in [('separate',3,False,False,False),('touch',1,False,False,False),('penetrate',.5,False,False,True),('same_body_print',.5,True,False,False),('same_body_metal',.5,True,True,True),('contained',0,False,False,True)]:
 p={'a':box([0,0,0],[1,1,1]),'b':box([shift,0,0],[shift+1,1,1])};m={'a':{'module':'a','body':'one','sku':None},'b':{'module':'b','body':'one' if same else 'two','sku':'metal' if metal else None}};ok=bool(slow(p,m))==bool(fast(p,m))==expect;assert ok;rows.append({'case':name,'same_collision_decision':ok})
save('collision_fast_method_checks.json',{'checks':rows,'source_sha256':sha(Path(__file__).with_name('collision_fast.py')),'scope':'Broad-phase optimization equivalence; does not change accepted geometry or thresholds.'});print('BROAD_PHASE_CHECKS',len(rows),'passed',flush=True)
