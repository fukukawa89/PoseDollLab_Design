from base import *
p,m,pr,st,prov=load_o18()
focus={k for k in p if k.startswith(('thigh_l/','thigh_r/'))}
exclude={'frame/pelvis','frame/thigh_l','frame/thigh_r'}
cases={'neutral':{},'assembly':g.ASSEMBLY_POSE,'sit':{'thigh_l.flex':90,'thigh_r.flex':90,'calf_l.flex':90,'calf_r.flex':90}}
results=[]
for tilt,phase in [(0,0),(0,45),(0,90),(15,0),(-15,0),(30,0),(-30,0)]:
 ov=hip_overrides(tilt,phase)
 rows=[]
 for name,a in cases.items():
  q,tr,states,fail,prof=position(p,m,a,ov)
  found=overlaps(q,focus,exclude,same_body_meta=m)
  hh=[r for r in found if all(x.startswith(('thigh_','waist/','calf_','frame/calf_')) for x in r['pair'])]
  rows.append({'pose':name,'fail':fail,'all_focus_hits':len(found),'hip_leg_trunk_hits':hh,'worst':found[:6]})
  print('TRY',tilt,phase,name,'all',len(found),'leg/trunk',len(hh),'volume',round(sum(r['overlap_mm3'] for r in hh),2),'fail',fail,'worst',hh[:4],flush=True)
 results.append({'tilt':tilt,'phase':phase,'cases':rows})
g.write(OUT/'hip_orientation_search.json',results)
