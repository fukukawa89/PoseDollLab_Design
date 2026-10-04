from common import *
from layout_fullbody import *
from search_adjacent import first_cross
rr=[];base=read(H/'mechanical_manifest/revO_pose_cases.json')['cases'];poses=[base[k] for k in ('neutral','sitting','crouch','hip_abduction','kneeling','legs_crossed')]
poses+=[{f'thigh_{s}.flex':f,f'thigh_{s}.abduct':a,f'thigh_{s}.twist':t} for s,f,a,t in itertools.product(('l','r'),(-30,125),(-25,65),(-50,50))]
for dy in (4,8,12,16,20,24):
 op={f'thigh_{s}':{'offset_parent_mm':[0,sgn*dy,0]} for s,sgn in [('l',1),('r',-1)]};ss=[]
 for a in poses:
  p,m,st,f,_=build('quinn',a,op,only=('thigh_l','thigh_r'));ss.append({'angles':a,'mapping':f,'hit':first_cross(p,m)})
 rr.append({'offset_each_mm':dy,'overrides':op,'samples':ss,'failures':sum(bool(s['mapping'] or s['hit']) for s in ss)});print('hip spacing',dy,rr[-1]['failures'],flush=True);save('hip_spacing_search.json',{'trials':rr})
