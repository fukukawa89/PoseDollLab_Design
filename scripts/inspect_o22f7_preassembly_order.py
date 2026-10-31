from o22f7_animation import *
x=Build()
for s in x.g['steps'][:13]:print(s['step'],s['id'],s['kind'],s.get('parent'),s.get('child'),s.get('raw_ids'), {k:x.target[k] for k in s.get('raw_ids',[])})
for j in x.profile['joints']:
 if 'clavicle' in str(j):print(j)
print('rightpath',len(read(WORK/'clavicle_right_goal_0_1_path.json')['path']),read(WORK/'clavicle_right_goal_0_1_path.json')['path'][-1])
