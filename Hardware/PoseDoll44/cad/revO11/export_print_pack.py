"""Export geometry-only 3MF/STL beds and display meshes; never generate G-code."""
from solid_ops import *
import zipfile,xml.etree.ElementTree as ET
B=H/'bench/revO11';PAGE=H/'tutorials/print-first';PAGE.mkdir(parents=True,exist_ok=True)
N='http://schemas.microsoft.com/3dmanufacturing/core/2015/02'
def write_3mf(path,objects):
 ET.register_namespace('',N);root=ET.Element('{'+N+'}model',{'unit':'millimeter','{http://www.w3.org/XML/1998/namespace}lang':'en-US'});resources=ET.SubElement(root,'{'+N+'}resources');build=ET.SubElement(root,'{'+N+'}build');audit=[]
 for i,(name,s) in enumerate(objects.items(),1):
  t=tri(s);v,idx=np.unique(t.reshape(-1,3),axis=0,return_inverse=True);f=idx.reshape(-1,3)
  obj=ET.SubElement(resources,'{'+N+'}object',{'id':str(i),'type':'model','name':name});mesh=ET.SubElement(obj,'{'+N+'}mesh');vertices=ET.SubElement(mesh,'{'+N+'}vertices');faces=ET.SubElement(mesh,'{'+N+'}triangles')
  for x,y,z in v:ET.SubElement(vertices,'{'+N+'}vertex',dict(x=f'{x:.6f}',y=f'{y:.6f}',z=f'{z:.6f}'))
  for a,b,c in f:ET.SubElement(faces,'{'+N+'}triangle',dict(v1=str(a),v2=str(b),v3=str(c)))
  ET.SubElement(build,'{'+N+'}item',{'objectid':str(i)});audit.append({'part':name,**record(s)})
 with zipfile.ZipFile(path,'w',zipfile.ZIP_DEFLATED) as z:
  z.writestr('[Content_Types].xml','<?xml version="1.0"?><Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/><Default Extension="model" ContentType="application/vnd.ms-package.3dmanufacturing-3dmodel+xml"/></Types>')
  z.writestr('_rels/.rels','<?xml version="1.0"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Target="/3D/3dmodel.model" Id="rel0" Type="http://schemas.microsoft.com/3dmanufacturing/2013/01/3dmodel"/></Relationships>')
  z.writestr('3D/3dmodel.model',ET.tostring(root,encoding='utf-8',xml_declaration=True))
 with zipfile.ZipFile(path) as z:
  rr=ET.fromstring(z.read('3D/3dmodel.model'));back=rr.findall('.//{'+N+'}object');assert len(back)==len(objects)
  for o,s in zip(back,objects.values()):
   vv=np.array([[float(n.attrib[k]) for k in ('x','y','z')] for n in o.findall('.//{'+N+'}vertex')]);ff=np.array([[int(n.attrib[k]) for k in ('v1','v2','v3')] for n in o.findall('.//{'+N+'}triangle')]);assert abs(from_tri(vv[ff]).volume()-s.volume())<.03
 for a,b in __import__('itertools').combinations(objects.values(),2):assert (a^b).volume()<1e-6
 return audit

def place(s,M,x,y):
 s=pose(s,M);bb=np.array(s.bounding_box());return s.translate(np.array([x,y,0])-bb[:3])
def main():
 bench={k:from_tri(t) for k,t in np.load(B/'parts.npz').items()};core={k:from_tri(t) for k,t in np.load(OUT/'printed_core/parts.npz').items()}
 layouts={'bench':{'printed_lever':place(bench['printed_lever'],np.eye(3),8,8),'printed_base_minus':place(bench['printed_base_minus'],rot(0,-90),8,35),'printed_base_plus':place(bench['printed_base_plus'],rot(0,90),70,35)},
 'core_fit_only':{'C01':place(core['C01'],rot(0,90),10,10),'C02':place(core['C02'],rot(1,90),65,10),'C14':place(core['C14'],rot(0,180),10,70),'C15':place(core['C15'],np.eye(3),50,70)}}
 reports={};folder=B/'print_beds';folder.mkdir(exist_ok=True)
 for label,parts in layouts.items():
  reports[label]=write_3mf(folder/(label+'.3mf'),parts)
  for name,s in parts.items():export_stl(folder/(name+'_on_bed.stl'),tri(s))
  assert all(s.bounding_box()[5]>0 and abs(s.bounding_box()[2])<1e-7 and max(s.bounding_box()[3:5])<180 for s in parts.values())
 (folder/'export_check.json').write_text(json.dumps({'beds':reports,'units':'mm','roundtrip_volume_tolerance_mm3':.03,'gcode_included':False,'printer_profile_included':False,'slicer_validation':False,'orientation_is_candidate':True,'bed_requirement_including_5mm_brim_mm':[135,115],'scope':'Geometry and layout validation only. Slice for the actual printer; inspect supports, layer continuity and holes before printing.'},indent=2)+'\n')
 models={};groups={};labels={'printed_base_minus':'打印底座 · 后半','printed_base_plus':'打印底座 · 前半','printed_lever':'打印长臂 · 100 mm 力臂','C01':'近端打印叉架','C02':'远端打印叉架','C14':'打印承力环 · 下半','C15':'打印承力环 · 上半','M3_nut':'M3 六角螺母','M3_reaction_washer':'M3 大垫圈 · 9×3.2×0.8','inner_M4_wide':'内侧 M4 大垫圈 · 12×4.3×1','outer_M4_wide':'外侧 M4 大垫圈 · 12×4.3×1','front_M4_washer':'M4 平垫圈 · 9×4.3×0.8','shoulder_SBSM_M3_4_8':'成品轴肩螺钉 · Φ4 肩长8','spring_1':'碟簧 · 第一片','spring_2':'碟簧 · 第二片（反向）'}
 core.update({'ring_'+k:from_tri(t) for k,t in np.load(G8/'fastened_core/fasteners.npz').items()})
 for mode,parts in [('bench',bench),('core',core)]:
  groups[mode]=[]
  for k,s in parts.items():
   t=tri(s.simplify(.03));v,idx=np.unique(np.round(t.reshape(-1,3),4),axis=0,return_inverse=True);key=mode+'/'+k;models[key]={'v':v.tolist(),'f':idx.reshape(-1,3).tolist()};printed=k.startswith('printed_') or k in ('C01','C02','C14','C15');color='#ad6744' if printed and ('lever' in k or k=='C02') else '#507565' if printed else '#485d73' if 'spring' in k else '#a8afb4'
   label=labels.get(k,k.replace('case_M3x35_','底座连接螺钉 M3×35 · ').replace('case_M3_nut_','底座连接螺母 M3 · ').replace('ring_screw_','合拢螺钉 M1.6×6 · ').replace('ring_nut_','合拢螺母 M1.6 · '))
   if k.startswith(('C01_-1_','C01_+1_','C02_-1_','C02_+1_')):
    prefix,side,tail=k.split('_',2);label=('第一轴' if prefix=='C01' else '第二轴')+' '+side+'侧 · '+labels.get(tail,tail)
   groups[mode].append({'name':k,'label':label,'key':key,'color':color,'printed':printed})
 (PAGE/'models.js').write_text('window.O11_MODELS='+json.dumps(models,separators=(',',':'))+';\nwindow.O11_GROUPS='+json.dumps(groups,ensure_ascii=False,separators=(',',':'))+';\n',encoding='utf-8')
 (PAGE/'model_sources.json').write_text(json.dumps({'generator_sha256':sha(__file__),'bench_sha256':sha(B/'parts.npz'),'core_sha256':sha(OUT/'printed_core/parts.npz'),'display_simplification_mm':.03,'rounding_mm':.0001,'checks_use_full_meshes':True},indent=2)+'\n')
 print('exported geometry-only beds',list(layouts),'display MB',(PAGE/'models.js').stat().st_size/1e6)
if __name__=='__main__':main()


