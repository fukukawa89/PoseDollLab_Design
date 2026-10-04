from common import *
a=box([0,0,0],[10,10,10])-box([4,4,4],[6,6,6]);b=box([0,0,0],[10,10,10])+box([14,4,4],[16,6,6]);c=a+box([4.5,4.5,4.5],[5.5,5.5,5.5]);cases=[('closed_void',a,1),('disconnected_control',b,2),('island_inside_void',c,2)];rr=[]
for label,s,expect in cases:
 rec=mesh_record(s);assert rec['components']==expect;rr.append({'case':label,'expected_material_components':expect,'mesh':rec,'signed_boundary_volumes':[v.volume() for v in s.decompose()]})
save('component_count_validation.json',{'cases':rr,'source_sha256':sha(Path(__file__).with_name('common.py'))});print('Material connectivity controls passed',len(rr))
