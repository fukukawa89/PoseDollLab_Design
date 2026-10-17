"""Reuse an exact, singly occupied, already-audited native project as a final plate.
Only the external file/guide address changes. 3MF bytes, process, transforms,
object names and G-code remain identical; native internal names are mapped explicitly.
"""
from pathlib import Path
import sys,json,copy,shutil,hashlib,zipfile,xml.etree.ElementTree as ET
R=Path(__file__).resolve().parents[1];B=R/'Hardware/PoseDoll44/bench/revO22';O=B/'a1mini_fins_v4';S=O/'plate_final145'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def one(pid,label,plateid,optional):
 src=O/'candidates'/pid/label;native=json.loads((src/'verification/full_bead_contacts.json').read_text())
 for name in ['full_bead_contacts_v2.json','full_bead_contacts_v4.json','full_bead_contacts_v5.json']:
  p=src/'verification'/name
  if p.exists():
   q=json.loads(p.read_text())
   if q['project_sha256']==native['project_sha256'] and(name!='full_bead_contacts_v5.json'or q.get('audit_schema')=='full-bead-v5-earlier-rooted-wall-104'):native=q
 assert native['native_review_resolved'];g=json.loads((src/'verification/geometry.json').read_text());assert g['geometric_constraints_passed']and g['npz_sha256']==sha(src/'parts'/f'{pid}.npz');pm=json.loads((src/'verification/plate_manifest.json').read_text());assert len(pm['items'])==1;project=src/'projects'/json.loads((src/'verification/local_extrusion.json').read_text())['project'];assert sha(project)==native['project_sha256']
 with zipfile.ZipFile(project)as z:
  root=ET.fromstring(z.read('3D/3dmodel.model'));assert len(root.find('{*}build').findall('{*}item'))==1;settings=json.loads(z.read('Metadata/project_settings.config'));assert settings['enable_support']=='0'
 it=copy.deepcopy(pm['items'][0]);internal=it['object_name'];source=json.loads((B/'a1mini/manifest.json').read_text());original=next(i for p in source['plates']if not p['optional']for i in p['items']if i['id']==pid)
 if optional:
  sam=json.loads((R/'.local/o22-easy-support/S00/manifest.json').read_text());original=next(i for i in sam['items']if i['id']==pid)
 it.update(original_object_name=original.get('original_object_name',original['object_name']),object_name=f'{plateid}-01 '+pid+' '+it['part'],number=1,native_internal_object_name=internal)
 p={'id':plateid,'title':'O22 F4 '+('optional sample'if optional else'main part'),'optional':optional,'items':[it],'profile':{'layer':float(settings['layer_height']),'initial':float(settings['initial_layer_print_height']),'wall':settings['wall_generator'],'overrides':json.loads((src/'design'/f'{pid}.json').read_text()).get('required_process_overrides',{}),'height_overrides':json.loads((src/'design'/f'{pid}.json').read_text()).get('required_layer_ranges',[]),'fuse':True},'exact_native_single_object_reuse':True,'source_qualified_candidate':{'id':pid,'label':label,'project_sha256':native['project_sha256']}}
 for sub,ext in [('parts','npz'),('design','json')]:
  (S/sub).mkdir(parents=True,exist_ok=True);shutil.copy2(src/sub/f'{pid}.{ext}',S/sub/f'{pid}.{ext}')
 (S/'projects').mkdir(exist_ok=True);dest=S/'projects'/f'{plateid}_O22F4_PLA_fins_DRAFT.3mf';shutil.copy2(project,dest);assert sha(dest)==sha(project)
 qp=S/'candidates'/('PLATE_'+plateid)/'native/verification';qp.mkdir(parents=True,exist_ok=True)
 for fp in (src/'verification').glob('*.json'):shutil.copy2(fp,qp/fp.name)
 result={'plate':plateid,'instances':1,'source_ids':[pid],'native_clear':True,'external_islands':0,'critical_external_runs':0,'project_sha256':sha(dest),'geometry_qualified_per_instance':True,'physical_print_tested':False,'audit_reuse_proof':'Exact byte-identical native project with one build object, same G-code and transforms. The external filename and guide address are aliases only.','source_candidate':str(src),'native_internal_object_name':internal};(qp/'plate_result.json').write_text(json.dumps(result,ensure_ascii=False,indent=2))
 mp=S/'stage_manifest.json';m=json.loads(mp.read_text())if mp.exists()else{'plates':[]};assert plateid not in[q['id']for q in m['plates']];m['plates'].append(p);mp.write_text(json.dumps(m,ensure_ascii=False,indent=2),encoding='utf8');print('EXACT_SINGLETON',plateid,pid,label,optional,sha(dest),flush=True)
if __name__=='__main__':
 for spec in sys.argv[1:]:
  pid,label,pid2,kind=spec.split(':');one(pid,label,pid2,kind=='sample')
