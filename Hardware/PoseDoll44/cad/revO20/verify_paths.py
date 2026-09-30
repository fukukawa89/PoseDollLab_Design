"""Raw-axis branch regression for the newly integrated toe housings."""
from base import *
from raw_paths import raw_state
from connected import adjacent_pairs

def main():
 p,m,pr,st,prov=load_o19();q0={r['id']:np.array(r['angles_deg']) for r in st};profile=g.read(H/'bench/revO19/profiles/device_profile.json');changes=g.read(OUT/'changes.json');new={k:from_tri_exact(v) for k,v in np.load(OUT/'changed_parts.npz').items()};gone=set(changes['removed_stock_parts'])|{k for r in changes['replacements'] for k in r['replaces'] if k!=r['part']};sources={r['part']:r['replaces'] for r in changes['replacements']};adj=adjacent_pairs('quinn');rows=[];inc=[];inherited=[]
 def related(a,b):
  ga=m[a].get('modules',[m[a]['module']]);gb=m[b].get('modules',[m[b]['module']]);return m[a]['body']==m[b]['body'] or bool(set(ga)&set(gb)) or any(frozenset((x,y)) in adj for x in ga for y in gb)
 for side in ('l','r'):
  focus='frame/foot_'+side;keys=[k for k in p if k not in gone and (k==focus or related(focus,k))];relevant=set(keys)|set(sources[focus]);inverses={k:np.linalg.inv(m[k]['transform']) for k in relevant}
  for module in ('ball_'+side+'.flex','foot_'+side):
   joint=next(r for r in profile['joints'] if r['id']==module)
   for axis,rawid in enumerate(joint['raw_ids']):
    low,high=profile['raw_limits_deg'][rawid]
    for value in np.linspace(low,high,int(np.ceil((high-low)/5))+1):
     q={k:v.copy() for k,v in q0.items()};q[module][axis]=value;(_,mm,states,fail,prof),angles,outside=raw_state('quinn',q);assert not fail;T,A=L.fk(prof,angles)
     mats={k:T[m[k]['body']] if m[k]['owner']=='rigid_frame' else mm[m[k].get('source_anchor',m[k].get('follows_part',k))]['transform'] for k in relevant}
     old={k:g.move(p[k],mats[k]@inverses[k]) for k in relevant};current={k:g.move(new[k],mats[k]) if k in new else old[k] for k in keys};ss=current[focus];sb=np.array(ss.bounding_box());hits=[]
     for k in keys:
      if k==focus:continue
      bb=np.array(current[k].bounding_box())
      if not np.all(np.minimum(sb[3:],bb[3:])>np.maximum(sb[:3],bb[:3])+1e-8):continue
      v=max(0.,float((ss^current[k]).volume()))
      if v<.001:continue
      baseline=sum(max(0.,float((old[a]^old[b]).volume())) for a in sources[focus] for b in sources.get(k,[k]) if b in old)
      rec={'pair':[focus,k],'O20_mm3':v,'O19_mm3':baseline,'increase_mm3':v-baseline};hits.append(rec)
      if v>baseline+.001:inc.append({'raw_id':rawid,'angle_deg':float(value),**rec})
     if hits:inherited.append({'raw_id':rawid,'angle_deg':float(value),'findings':hits})
     rows.append({'raw_id':rawid,'angle_deg':float(value),'semantic_limits_exceeded':outside,'adjacent_overlap_count':len(hits)})
    print('RAW SWEEP',rawid,'samples so far',len(rows),'increases',len(inc),flush=True)
 g.write(OUT/'path_verification.json',{'status':'PASS' if not inc else 'FAIL','raw_step_deg':5,'samples':rows,'within_capture_domain_samples':sum(not r['semantic_limits_exceeded'] for r in rows),'within_capture_domain_adjacent_overlap_samples':sum(not r['semantic_limits_exceeded'] and r['adjacent_overlap_count']>0 for r in rows),'outside_capture_domain_adjacent_overlap_samples':sum(bool(r['semantic_limits_exceeded']) and r['adjacent_overlap_count']>0 for r in rows),'increased_adjacent_collisions':inc,'inherited_out_of_capture_or_pose_contacts':inherited,'continuous_collision_proof':False,'scope':'Single raw toe and ankle axis sweeps across configured raw limits, other raw joints held at assembly. Full physical branch respected. Outside-semantic-range transit states are not qualified captures. Adjacent pairs involving the two foot carrier housings only.'})
 if inc:raise SystemExit(1)
if __name__=='__main__':main()
