"""Reorient existing O13 core; mechanical geometry remains unchanged.
Large flat fork ear on bed, plus required slicer supports under the offset stem.
Contact/COM inspection distinguishes bed contact from actual printability.
"""
from pathlib import Path
import sys,json,hashlib,importlib.util
import numpy as np
H=Path(__file__).resolve().parents[2];R=H.parents[1];OUT=H/'generated/revO14/runs/o14_20260929_r1';B=H/'bench/revO14';G13=H/'generated/revO13/runs/o13_20260929_r1'
sys.path.insert(0,str(H/'cad/revO13'));from solid_ops import from_tri,tri,pose,rot,export_stl
spec=importlib.util.spec_from_file_location('geometry_bed_helpers',H/'cad/revO11/export_print_pack.py');helper=importlib.util.module_from_spec(spec);spec.loader.exec_module(helper)

def hull(points):
 p=sorted(set(tuple(x) for x in points))
 def cross(o,a,b):return (a[0]-o[0])*(b[1]-o[1])-(a[1]-o[1])*(b[0]-o[0])
 if len(p)<3:return np.array(p)
 lo=[];hi=[]
 for a in p:
  while len(lo)>=2 and cross(lo[-2],lo[-1],a)<=0:lo.pop()
  lo.append(a)
 for a in reversed(p):
  while len(hi)>=2 and cross(hi[-2],hi[-1],a)<=0:hi.pop()
  hi.append(a)
 return np.array(lo[:-1]+hi[:-1])
def in_hull(c,h):
 if len(h)<3:return False
 d=np.roll(h,-1,axis=0)-h;p=c-h;return bool(np.all(d[:,0]*p[:,1]-d[:,1]*p[:,0]>=-1e-6))
def inspect(s):
 t=tri(s);v=np.einsum('ij,ij->i',t[:,0],np.cross(t[:,1],t[:,2]))/6;c=(v[:,None]*(t[:,0]+t[:,1]+t[:,2])/4).sum(0)/v.sum();cr=np.cross(t[:,1]-t[:,0],t[:,2]-t[:,0]);mask=(t[:,:,2].max(1)<1e-4)&(cr[:,2]<-1e-8);contact=hull(t[mask].reshape(-1,3)[:,:2])
 return {'bounds_mm':list(s.bounding_box()),'volume_mm3':float(v.sum()),'solid_COM_mm':c.tolist(),'flat_contact_area_mm2':float(np.linalg.norm(cr[mask],axis=1).sum()/2),'contact_hull_mm':contact.tolist(),'COM_over_unsupported_part_contact_hull':in_hull(c[:2],contact),'support_free_approved':False}
def main():
 raw={k:from_tri(t) for k,t in np.load(G13/'printed_core/parts.npz').items() if k in ('C01','C02','C14','C15')};bed=B/'print_beds';bed.mkdir(exist_ok=True)
 newrot={'C01':rot(1,90),'C02':rot(0,90),'C14':rot(0,180),'C15':np.eye(3)};oldrot={'C01':rot(0,90),'C02':rot(1,90),'C14':rot(0,180),'C15':np.eye(3)};xy={'C01':(15,15),'C02':(80,15),'C14':(15,90),'C15':(65,90)};parts={};report=[]
 for k,s in raw.items():
  old=helper.place(s,oldrot[k],*xy[k]);new=helper.place(s,newrot[k],*xy[k]);a,b=inspect(old),inspect(new);assert abs(a['volume_mm3']-b['volume_mm3'])<.02
  parts[k]=new;export_stl(bed/(k+'_flat_face.stl'),tri(new));report.append({'part':k,'old':a,'new':b,'needs_support_under_stem':k in ('C01','C02'),'user_action':'Wait for supplier slicing/support review; never print either fork with supports disabled.' if k in ('C01','C02') else 'Flat split face on bed; inspect pockets and any generated support for removal.'})
 helper.write_3mf(bed/'O14_core_flat_faces_supports_required.3mf',parts)
 np.savez_compressed(OUT/'oriented_parts.npz',**{k:tri(s) for k,s in parts.items()})
 d={'source_core_sha256':hashlib.sha256((G13/'printed_core/parts.npz').read_bytes()).hexdigest(),'generator_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'mechanical_geometry_changed':False,'orientation_only':True,'parts':report,'support_required':True,'actual_slicing':False,'manufacturing_released':False,'warning':'A flat ear touching the bed is insufficient for the forks: their COM lies beyond that ear, and the offset stem needs support. The later slicing report evaluates model+support footprints.'}
 (OUT/'bed_geometry.json').write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
 print([(r['part'],round(r['old']['flat_contact_area_mm2'],2),round(r['new']['flat_contact_area_mm2'],2),r['new']['COM_over_unsupported_part_contact_hull']) for r in report])
if __name__=='__main__':main()
