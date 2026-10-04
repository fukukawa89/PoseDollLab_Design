"""3MF exporter preserving float64 coordinates through text round-trip."""
from common import *
import zipfile,xml.etree.ElementTree as ET
N='http://schemas.microsoft.com/3dmanufacturing/core/2015/02'

def write_3mf(path,objects):
 ET.register_namespace('',N);root=ET.Element('{'+N+'}model',{'unit':'millimeter','{http://www.w3.org/XML/1998/namespace}lang':'zh-CN'});resources=ET.SubElement(root,'{'+N+'}resources');build=ET.SubElement(root,'{'+N+'}build')
 for i,(name,s) in enumerate(objects.items(),1):
  t=tri(s);v,idx=np.unique(t.reshape(-1,3),axis=0,return_inverse=True);f=idx.reshape(-1,3);obj=ET.SubElement(resources,'{'+N+'}object',{'id':str(i),'type':'model','name':name});mesh=ET.SubElement(obj,'{'+N+'}mesh');vertices=ET.SubElement(mesh,'{'+N+'}vertices');faces=ET.SubElement(mesh,'{'+N+'}triangles')
  for x,y,z in v:ET.SubElement(vertices,'{'+N+'}vertex',dict(x=format(x,'.17g'),y=format(y,'.17g'),z=format(z,'.17g')))
  for a,b,c in f:ET.SubElement(faces,'{'+N+'}triangle',dict(v1=str(a),v2=str(b),v3=str(c)))
  ET.SubElement(build,'{'+N+'}item',{'objectid':str(i)})
 with zipfile.ZipFile(path,'w',zipfile.ZIP_DEFLATED) as z:
  z.writestr('[Content_Types].xml','<?xml version="1.0"?><Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/><Default Extension="model" ContentType="application/vnd.ms-package.3dmanufacturing-3dmodel+xml"/></Types>')
  z.writestr('_rels/.rels','<?xml version="1.0"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Target="/3D/3dmodel.model" Id="rel0" Type="http://schemas.microsoft.com/3dmanufacturing/2013/01/3dmodel"/></Relationships>')
  z.writestr('3D/3dmodel.model',ET.tostring(root,encoding='utf8',xml_declaration=True))
 with zipfile.ZipFile(path) as z:
  doc=ET.fromstring(z.read('3D/3dmodel.model'));back=doc.findall('.//{'+N+'}object');assert len(back)==len(objects)
  for o,s in zip(back,objects.values()):
   v=np.array([[float(n.attrib[k]) for k in ('x','y','z')] for n in o.findall('.//{'+N+'}vertex')]);f=np.array([[int(n.attrib[k]) for k in ('v1','v2','v3')] for n in o.findall('.//{'+N+'}triangle')]);recovered=from_tri_exact(v[f]);assert abs(recovered.volume()-s.volume())<.03 and solid_count(recovered)==solid_count(s),(path, recovered.volume(), s.volume(), solid_count(recovered), solid_count(s))
