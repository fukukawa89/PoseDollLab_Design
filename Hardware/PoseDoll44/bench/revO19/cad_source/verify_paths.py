"""O19 comparative interpolation samples, not a continuous swept-volume proof."""
from base import *
def main():
 p,m,pr,st,prov=load_o18();new={k:from_tri_exact(v) for k,v in np.load(OUT/'changed_parts.npz').items()};cases=g.read(H/'mechanical_manifest/revO_pose_cases.json')['cases'];rows=[];added=[]
 for target in ('sitting','crouch','hip_abduction','kneeling','hands_low_behind'):
  steps=int(np.ceil(max(abs(v) for v in cases[target].values())/10))
  for i in range(1,steps):
   angles={k:v*i/steps for k,v in cases[target].items()};old,tr,_,fail,_=position(p,m,angles)
   if fail:rows.append({'target':target,'fraction':i/steps,'decomposition_failures':fail});continue
   current=old.copy();current.update({k:g.move(s,tr[k]) for k,s in new.items()});hh=overlaps(current,set(new));inc=[]
   for h in hh:
    a,b=h['pair'];baseline=max(0,float((old[a]^old[b]).volume()))
    if h['overlap_mm3']>baseline+.001:inc.append({**h,'baseline_mm3':baseline,'increase_mm3':h['overlap_mm3']-baseline})
   rows.append({'target':target,'fraction':i/steps,'angles':angles,'findings_count':len(hh),'increased_collisions':inc})
   added.extend({'target':target,'fraction':i/steps,**h} for h in inc)
  print('SWEEP',target,'cumulative samples',len(rows),'new',len(added),flush=True)
 g.write(OUT/'path_verification.json',{'status':'PASS' if not added and not any('decomposition_failures' in r for r in rows) else 'REVIEW_REQUIRED','maximum_semantic_step_deg':10,'samples':rows,'increased_collisions':added,'continuous_collision_proof':False,'scope':'Interpolated semantic paths use deterministic CAD four-axis branches, not a verified continuous encoder branch transit. All material/stock/electronics included against four changed leg beams.'})
if __name__=='__main__':main()
