"""T6 delivery pages and viewer, built from the same manufacturing meshes."""
from arm_kit import *
import html,base64,shutil,zipfile,hashlib,collections
sp=importlib.util.spec_from_file_location('t4_publish_helpers',H/'cad/revO24C_T4/publish.py');basepub=importlib.util.module_from_spec(sp);sp.loader.exec_module(basepub)
smooth=basepub.smooth

def page(title,body):
 nav='<nav><a href="START_HERE.html">T6 打印入口</a><a href="tutorial/index.html">逐件动画</a><a href="ONE_PRINT.html">打印工程</a><a href="HARDWARE.html">五金清单</a><a href="DESIGN_REVIEW.html">结构复核</a><a href="TEST_PLAN.html">实测方法</a></nav>'
 return '<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>'+title+'</title><link rel="icon" href="data:,"><style>'+basepub.pages.STYLE+'</style></head><body>'+nav+body+'</body></html>'

def lessons():
 data=json.loads((OUT/'tutorial/steps.json').read_text('utf8'));steps=[]
 for st,l in data['lessons'].items():
  for s in l['steps']:
   if s['kind']=='add':steps.append(dict(station=st,title=s['title'],ids=s['ids'],text=s['text'],number=len(steps)+1))
 return steps

def viewer():
 data=json.loads((OUT/'assembly.json').read_text('utf8'));z=np.load(OUT/'assembly_meshes.npz');chunks=[];count=0
 for r in data['parts']:
  v=z['v'+str(r['index'])];f=z['f'+str(r['index'])];tri=v[f];n=np.cross(tri[:,1]-tri[:,0],tri[:,2]-tri[:,0]);n/=np.maximum(np.linalg.norm(n,axis=1)[:,None],1e-15)
  packed=np.concatenate([tri,np.repeat(n[:,None,:],3,axis=1)],axis=2).reshape(-1,6).astype('<f4');chunks.append(packed);r.update(start=count,count=len(packed),smooth=smooth(r));count+=len(packed)
 data.update(geometry=base64.b64encode(np.vstack(chunks).tobytes()).decode(),geometry_sha256=sha(OUT/'assembly_meshes.npz'),steps=lessons())
 (OUT/'viewer').mkdir(exist_ok=True);(OUT/'viewer/data.js').write_text('window.KIT='+json.dumps(data,ensure_ascii=False,separators=(',',':'))+';',encoding='utf8')
 for name in ['viewer.js','viewer.html']:shutil.copyfile(HERE/name,OUT/'viewer'/('index.html' if name.endswith('.html') else name))

def write_doc(name,title,body):
 (OUT/(name+'.html')).write_text(page(title,body),encoding='utf8')

def hardware():
 from docs import hardware_page
 hardware_page()

def package():
 files=[p for p in OUT.rglob('*') if p.is_file() and p.suffix!='.zip' and p.name!='manifest.json']
 put(OUT/'manifest.json',dict(revision=REVISION,geometry_sha256=sha(OUT/'assembly_meshes.npz'),files=[dict(path=p.relative_to(OUT).as_posix(),size=p.stat().st_size,sha256=sha(p)) for p in sorted(files)]))
 path=OUT/(REVISION+'_print_and_assembly.zip')
 with zipfile.ZipFile(path,'w',zipfile.ZIP_DEFLATED) as z:
  for p in sorted(OUT.rglob('*')):
   if p.is_file() and p.suffix!='.zip':z.write(p,p.relative_to(OUT).as_posix())
 with zipfile.ZipFile(path) as z:assert z.testzip() is None
 print('PACKAGE',path.name,path.stat().st_size,flush=True)

if __name__=='__main__':viewer();hardware()
