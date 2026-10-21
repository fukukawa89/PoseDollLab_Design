"""Connected material components, retaining nested enclosed cavities.
Manifold.decompose separates surface shells; a negative-volume inner shell is
an enclosed void, not a floating piece of plastic.
"""
import numpy as np
import manifold3d as md

def material_components(s,tolerance=1e-6):
 shells=s.decompose();pos=[p for p in shells if p.volume()>tolerance];neg=[p for p in shells if p.volume()<-tolerance];holes=[[] for _ in pos]
 for hole in neg:
  m=hole.to_mesh64();v=np.array(np.asarray(m.vert_properties)[:,:3],dtype=np.float64,copy=True);f=np.array(np.asarray(m.tri_verts)[:,[0,2,1]],dtype=np.uint64,copy=True,order='C');void=md.Manifold(md.Mesh64(v,f));vol=float(void.volume());bb=np.array(void.bounding_box());owners=[]
  for i,p in enumerate(pos):
   pb=np.array(p.bounding_box())
   if np.any(bb[:3]<pb[:3]-1e-5) or np.any(bb[3:]>pb[3:]+1e-5):continue
   if abs(float((void^p).volume())-vol)<=max(tolerance,vol*1e-5):owners.append(i)
  assert owners,('orphan_negative_surface_shell',vol,bb.tolist())
  owner=min(owners,key=lambda i:pos[i].volume());holes[owner].append(void)
 result=[p-md.Manifold.batch_boolean(h,md.OpType.Add) if h else p for p,h in zip(pos,holes)]
 assert abs(sum(float(p.volume()) for p in result)-float(s.volume()))<=max(1e-5,abs(s.volume())*1e-6)
 return result

if __name__=='__main__':
 outer=md.Manifold.cube([3,3,3]);void=md.Manifold.cube([1,1,1]).translate([1,1,1]);island=md.Manifold.cube([.5,.5,.5]).translate([1.25,1.25,1.25])
 for s,expected in [(outer-void,[26.]),(outer-void+island,[.125,26.])]:
  got=sorted(float(x.volume()) for x in material_components(s));assert np.allclose(got,expected),(got,expected)
 print('MATERIAL_COMPONENT_CONTROLS_PASSED')
