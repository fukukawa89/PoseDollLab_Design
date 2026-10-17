from pathlib import Path
import sys,json,concurrent.futures,traceback
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'scripts'))
from repair_revo22_f4_clean_chamfer import trial
from verify_revo22_f4_body_change import check as fit
from verify_revo22_f4_repaired_geometry import check as geom
from transfer_revo22_f4_congruent_repair import transfer
from select_revo22_f4_repairs import select
O=R/'Hardware/PoseDoll44/bench/revO22/a1mini_fins_v4'
def one(spec):
 pid,label,targets=spec;out=[]
 try:
  for j in range(1,5):
   new='adapt20_'+str(j).zfill(2);dst=O/'candidates'/pid/new
   d=json.loads((dst/'verification/full_bead_contacts.json').read_text()) if (dst/'verification/full_bead_contacts.json').exists() else trial(pid,label,new)
   z={k:d[k] for k in ['id','label','external_island_count','critical_external_count','native_review_resolved']};out.append(z);print('ADAPT20_RESULT',z,flush=True)
   if d['native_review_resolved']:
    f=fit(pid,new);g=geom(pid,new)
    if f['fit_and_pose_geometry_passed'] and g['geometric_constraints_passed']:
     for target in targets:
      td=transfer(pid,new,target,'transfer20');tg=geom(target,'transfer20');out.append({k:td[k] for k in ['id','label','external_island_count','critical_external_count','native_review_resolved']})
    break
   before=json.loads((O/'candidates'/pid/label/'design'/f'{pid}.json').read_text()).get('body_change',{}).get('removed_volume_mm3',0);after=json.loads((dst/'design'/f'{pid}.json').read_text()).get('body_change',{}).get('removed_volume_mm3',0)
   if after-before<1e-5:break
   label=new
  return {'id':pid,'results':out}
 except Exception:return {'id':pid,'results':out,'error':traceback.format_exc()}
if __name__=='__main__':
 rows={q['id']:q for q in select()};wanted=set(sys.argv[1:]);jobs=[]
 for group in json.loads((O/'source_canonical_groups.json').read_text()):
  members=[rows[q['id']] for q in group['members'] if not rows[q['id']]['eligible_before_fin_geometry_check'] and (not wanted or q['id'] in wanted)]
  if not members:continue
  q=min(members,key=lambda q:q['islands']+q['critical']);jobs.append((q['id'],q['label'],[r['id'] for r in members if r['id']!=q['id']]))
 out=[]
 with concurrent.futures.ProcessPoolExecutor(max_workers=2) as pool:
  for f in concurrent.futures.as_completed([pool.submit(one,j) for j in jobs]):
   out.append(f.result());(O/'adapt20_progress.json').write_text(json.dumps({'completed':len(out),'total':len(jobs),'results':out},indent=2))
 print('ADAPT20_DONE',len(out),flush=True)
