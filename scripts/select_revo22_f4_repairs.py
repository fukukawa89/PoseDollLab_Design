from pathlib import Path
import json,sys
R=Path(__file__).resolve().parents[1];O=R/'Hardware/PoseDoll44/bench/revO22/a1mini_fins_v4'
def select():
 best={}
 for p in (O/'candidates').glob('*/*/verification/full_bead_contacts.json'):
  if 'fine' in p.parents[1].name:continue
  d=json.loads(p.read_text());pid=d['id'];ref=p.with_name('full_bead_contacts_v2.json')
  if ref.exists() and json.loads(ref.read_text()).get('project_sha256')==d['project_sha256']:d=json.loads(ref.read_text())
  exact=p.with_name('full_bead_contacts_v4.json')
  if exact.exists() and json.loads(exact.read_text()).get('project_sha256')==d['project_sha256']:d=json.loads(exact.read_text())
  lateral=p.with_name('full_bead_contacts_v5.json')
  if lateral.exists():
   ld=json.loads(lateral.read_text())
   if ld.get('project_sha256')==d['project_sha256'] and ld.get('audit_schema')=='full-bead-v5-earlier-rooted-wall-104':d=ld
  fitp=p.with_name('body_change_fit_and_pose.json');design=json.loads((p.parents[1]/'design'/f'{pid}.json').read_text());fit=json.loads(fitp.read_text()) if fitp.exists() else {};changed=('nominal_reference' in design) or ('body_change' in design and (design['body_change'].get('removed_volume_mm3',0)+design['body_change'].get('added_volume_mm3',0))>1e-6);ok=d['native_review_resolved'] and (not changed or fit.get('fit_and_pose_geometry_passed',False));score=(not ok,d['external_island_count']+d['critical_external_count'],changed,design.get('support_volume_mm3',1e9))
  if pid not in best or score<best[pid][0]:best[pid]=(score,{'id':pid,'label':d['label'],'islands':d['external_island_count'],'critical':d['critical_external_count'],'native_clear':d['native_review_resolved'],'body_changed':changed,'fit_passed':fit.get('fit_and_pose_geometry_passed'),'eligible_before_fin_geometry_check':ok})
 rows=sorted([v[1] for v in best.values()],key=lambda q:q['id']);(O/'repair_selection_progress.json').write_text(json.dumps(rows,indent=2));print('SELECTION',len(rows),'eligible',sum(q['eligible_before_fin_geometry_check'] for q in rows),'pending',','.join(q['id'] for q in rows if not q['eligible_before_fin_geometry_check']),flush=True);return rows
if __name__=='__main__':select()
