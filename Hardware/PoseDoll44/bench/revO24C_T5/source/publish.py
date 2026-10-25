"""T5 delivery pages and viewer, built from the same manufacturing meshes."""
from arm_kit import *
import html,base64,shutil,zipfile,hashlib,collections
sp=importlib.util.spec_from_file_location('t4_publish_helpers',H/'cad/revO24C_T4/publish.py');basepub=importlib.util.module_from_spec(sp);sp.loader.exec_module(basepub)
smooth=basepub.smooth

def page(title,body):
 nav='<nav><a href="START_HERE.html">T5 打印入口</a><a href="tutorial/index.html">逐件动画</a><a href="ONE_PRINT.html">打印工程</a><a href="HARDWARE.html">五金清单</a><a href="DESIGN_REVIEW.html">结构复核</a><a href="TEST_PLAN.html">实测方法</a></nav>'
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
 rows=json.loads((OUT/'assembly.json').read_text('utf8'))['parts'];old=json.loads((H/'bench/revO24C_T4/assembly.json').read_text('utf8'))['parts']
 count=lambda rs:collections.Counter(r['sku'] for r in rs if r['sku'])
 new=count(rows);prior=count(old);diff=[dict(sku=s,spec=SPECS[s],T4=prior[s],T5=new[s],delta=new[s]-prior[s]) for s in sorted(prior.keys()|new.keys())]
 put(OUT/'hardware_delta_from_T4.json',diff)
 body='<h1>T5 五金：无新增规格，减少 24 件</h1><p>以已经备齐 T4 的 H/R/双轴腕为基准，不需要购买新五金。取消 8 颗合模螺钉、8 片小垫圈、8 颗合模螺母；其余五金直接复用。以下数量包含三个独立测试附件及实际掌柄的替换五金，不能把掌柄和加载杆叠装。</p><p><b>全部螺母都是普通金属螺母，没有尼龙圈。</b>七组预紧组件各使用一颗 Φ4×8 / M3×6 轴肩螺钉和两片 A8；总共 7 颗轴肩螺钉、14 片 A8。</p><table><tr><th>型号</th><th>参数</th><th>T4</th><th>T5</th><th>变化</th></tr>'
 for r in diff:body+='<tr>'+''.join('<td>'+html.escape(str(r[k]))+'</td>' for k in ['sku','spec','T4','T5','delta'])+'</tr>'
 body+='</table><p>平垫参数为外径×内径×厚度；螺钉长度不含头。不能用孔 4.3 的头下垫替代孔 3.2 的反力垫。完整型号与每件用途也会在逐件动画中显示。</p>'
 write_doc('HARDWARE','T5 五金',body)

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
