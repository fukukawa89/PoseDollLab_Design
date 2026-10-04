"""Build display-only O10 meshes and compact, source-linked page data."""
from solid_ops import *
from clavicle_trial import library
DEST=H/'tutorials/design-lab/assets'

def main():
 sources=[OUT/'braked_module/manny_l.npz',H/'bench/revO10/parts.npz',OUT/'slipring/envelopes.npz',G8/'fastened_core/fasteners.npz',G9/'bounded_mapping.json',OUT/'face_brake/continuous_yokes.json',OUT/'braked_module/target_motion.json',OUT/'face_axis_loads.json',OUT/'slipring/study.json',H/'bench/revO10/plan.json',OUT/'clavicle_trial/motion.json',OUT/'clavicle_trial/manny_states.json',OUT/'clavicle_trial/quinn_states.json',Path(__file__)]
 sources+=list((OUT/'braked_module').glob('*.npz'))+list((OUT/'old_modules').glob('*.npz'))+[OUT/'face_brake/parts.npz']
 sources=list(dict.fromkeys(sources));before={str(p.relative_to(H)).replace('\\','/'):sha(p) for p in sources};models={};dedup={}
 def add(s):
  t=tri(s.simplify(.04));vertices,index=np.unique(np.round(t.reshape(-1,3),4),axis=0,return_inverse=True);faces=index.reshape(-1,3);payload={'v':vertices.tolist(),'f':faces.tolist()};key=hashlib.sha256(json.dumps(payload,separators=(',',':')).encode()).hexdigest()[:18]
  models[key]=payload;return key
 def color(k):
  if k=='C01':return '#bb7d4a'
  if k=='C02' or 'lever' in k:return '#5b8f79'
  if k in ('C14','C15') or 'aluminium' in k:return '#8095ad'
  if 'case' in k or 'sleeve' in k:return '#c4c9c1'
  if 'spring' in k:return '#445c72'
  if 'catalogue' in k:return '#b69357'
  return '#9fa6aa'
 core=[]
 for k,t in np.load(sources[0]).items():
  role='P' if k.startswith('P_') else 'D' if k.startswith('D_') else k if k in ('C01','C02') else 'ring';core.append({'name':k,'key':add(from_tri(t)),'role':role,'color':color(k)})
 for k,t in np.load(G8/'fastened_core/fasteners.npz').items():core.append({'name':'ring_'+k,'key':add(from_tri(t)),'role':'ring','color':color(k)})
 bench=[{'name':k,'key':add(from_tri(t)),'color':color(k)} for k,t in np.load(H/'bench/revO10/parts.npz').items()]
 wire=[{'name':k,'key':add(from_tri(t)),'color':color(k)} for k,t in np.load(OUT/'slipring/envelopes.npz').items()]
 lib=library();shoulder={k:add(s) for k,s in lib.items()};states={}
 for char in ('manny','quinn'):
  raw=json.loads((OUT/f'clavicle_trial/{char}_states.json').read_text());states[char]=[raw['states'][i] for i in (0,2)]
 def read(p):return json.loads(p.read_text())
 y=read(OUT/'face_brake/continuous_yokes.json');target=read(OUT/'braked_module/target_motion.json');clav=read(OUT/'clavicle_trial/motion.json')
 assert target['complete'] and clav['complete'] and len(target['cases'])==204 and len(clav['cases'])==102
 illustrations=[{'name':'illustrative_weight','key':add(along(cylinder(5,-35,-20),1).translate([100,0,11.5])),'color':'#bb9a5d'},{'name':'illustrative_cord','key':add(along(cylinder(.22,-20,0),1).translate([100,0,11.5])),'color':'#737c72'}]
 data={'core':core,'benchIllustrations':illustrations,'bench':bench,'wire':wire,'shoulder':shoulder,'states':states,'mapping':read(G9/'bounded_mapping.json')['characters'][0],'results':{'yoke':{k:y[k] for k in ('status','required_mm','alpha_deg','beta_deg','scope')},'yoke_cells':len(y['certified_cells']),'target_count':len(target['cases']),'target_failures':sum(bool(c['findings']) for c in target['cases']),'clav_count':len(clav['cases']),'clav_failures':sum(bool(c['findings']) for c in clav['cases']),'clav_cases':[c for c in clav['cases'] if c['pose'] in ('neutral','clavicle_l.protract_20')],'loads':read(OUT/'face_axis_loads.json')['characters'],'wire':read(OUT/'slipring/study.json'),'bench':read(H/'bench/revO10/plan.json')},'physical_tested':False,'manufacturing_released':False}
 assert before=={str(p.relative_to(H)).replace('\\','/'):sha(p) for p in sources}
 DEST.mkdir(parents=True,exist_ok=True);(DEST/'models.js').write_text('window.O10_MODELS='+json.dumps(models,separators=(',',':'))+';\n',encoding='utf-8');(DEST/'data.js').write_text('window.O10_DATA='+json.dumps(data,ensure_ascii=False,separators=(',',':'))+';\n',encoding='utf-8');(DEST/'provenance.json').write_text(json.dumps({'display_only_simplification_tolerance_mm':.04,'display_coordinates_rounded_mm':.0001,'validation_uses_full_source_meshes':True,'inputs_sha256':before,'meshes':len(models)},indent=2)+'\n');print('page meshes',len(models),'MB',(DEST/'models.js').stat().st_size/1e6)
if __name__=='__main__':main()

