"""Collect exact audited plate artifacts. Refuse a final release until all identities and proofs exist."""
from pathlib import Path
import json,hashlib,collections,sys,shutil,numpy as np
R=Path(__file__).resolve().parents[1];B=R/'Hardware/PoseDoll44/bench/revO22';O=B/'a1mini_fins_v4';D=O/'delivery_stage'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def collect(require_complete=False):
 registry={};pending=[]
 for name in ['plate_stage97','plate_stage119','plate_stage136','plate_final145']:
  root=O/name;mp=root/'stage_manifest.json'
  if not mp.exists():continue
  m=json.loads(mp.read_text())
  for p in m['plates']:
   qp=root/'candidates'/('PLATE_'+p['id'])/'native/verification/plate_result.json'
   if not qp.exists():pending.append({'stage':name,'plate':p['id'],'reason':'audit absent'});continue
   result=json.loads(qp.read_text());project=root/'projects'/f"{p['id']}_O22F4_PLA_fins_DRAFT.3mf"
   if not result.get('native_clear'):pending.append({'stage':name,'plate':p['id'],'reason':'native audit not clear'});continue
   assert sha(project)==result['project_sha256'],p['id']
   registry[p['id']]={'plate':p,'stage':name,'source_directory':str(root),'native_project':str(project),'proof':result}
 source=json.loads((B/'a1mini/manifest.json').read_text());expected=collections.Counter(i['object_name']for p in source['plates']if not p['optional']for i in p['items']);actual=collections.Counter(i['original_object_name']for x in registry.values()if not x['plate']['optional']for i in x['plate']['items']);sampleexpected=collections.Counter(i['id']for p in json.loads((B/'O22F3_Release/manifest.json').read_text())['plates']if p['optional']for i in p['items']);sampleactual=collections.Counter(i['id']for x in registry.values()if x['plate']['optional']for i in x['plate']['items']);missing=list((expected-actual).elements());extra=list((actual-expected).elements());assert not extra,extra
 parts={};clearance=[]
 for pid,x in registry.items():
  p=x['plate'];root=Path(x['source_directory'])
  for i,it in enumerate(p['items']):
   npz=root/'parts'/f"{it['id']}.npz";h=sha(npz);parts.setdefault(it['id'],{'npz_sha256':h,'source_directory':str(root),'plates':[]});assert parts[it['id']]['npz_sha256']==h,('same part identity differs between plates',it['id']);parts[it['id']]['plates'].append(pid)
   n=np.load(npz);v=np.r_[n['v'],n['fin_v'],n['teeth_v']]@np.array(it['rotation_matrix']).T+np.array(it['translation_mm']);lo=v.min(0);hi=v.max(0);assert min(lo[:2])>=3.99 and max(hi[:2])<=176.01 and abs(lo[2])<1e-5 and hi[2]<180
   for other in p['items'][i+1:]:
    b=np.array(other['bounds_mm']);gap=float(np.linalg.norm(np.maximum(np.maximum(lo[:2]-b[3:5],b[:2]-hi[:2]),0)));assert gap>=5.99,(pid,it['id'],other['id'],gap);clearance.append(gap)
 report={'version':'O22-F4','complete':not missing and sampleactual==sampleexpected and len(parts)==150,'main_instances':sum(actual.values()),'optional_instances':sum(sampleactual.values()),'type_count':len(parts),'main_missing':missing,'samples_missing':list((sampleexpected-sampleactual).elements()),'plates':sorted(registry.values(),key=lambda x:x['plate']['id']),'parts':parts,'historical_or_pending_audits':pending,'minimum_interobject_bbox_clearance_mm':min(clearance,default=None),'physical_print_tested':False,'force_or_thermal_simulated':False}
 D.mkdir(exist_ok=True);(D/'collection_status.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8')
 if require_complete:assert report['complete'],(report['main_missing'],report['samples_missing'],report['type_count'])
 print('COLLECTION',report['main_instances'],report['optional_instances'],report['type_count'],'complete',report['complete'],'missing',missing,flush=True);return report
if __name__=='__main__':collect('--require-complete'in sys.argv)
