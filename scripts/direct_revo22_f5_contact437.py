from pathlib import Path
p=Path(__file__).parent/'verify_revo22_f5_contacts298.py';s=p.read_text(encoding='utf-8-sig');a=s.index('def envelope(');b=s.index('\n\ndef run(',a)
s=s[:a]+'''def envelope(p,region,margin=MARGIN,axes=None):
 # Exact local intersections with the body and convex boundary-triangle
 # plus cube sweeps. Avoid subtracting near-identical region copies: that
 # Boolean form creates zero-thickness shells in Manifold on tiny edits.
 out=[];offsets=np.array(list(itertools.product([-margin,margin],repeat=3)))
 if axes is not None:offsets=offsets@np.asarray(axes).T
 pad=np.max(abs(offsets),axis=0);radius=float(np.linalg.norm(offsets,axis=1).max())
 for reg in material_components(region):
  if reg.min_gap(p,radius+1e-6)>radius+1e-7:continue
  bb=np.array(reg.bounding_box());cropped=(p^box(bb[:3]-pad*2,bb[3:]+pad*2)).as_original()
  if cropped.is_empty() or abs(cropped.volume())<1e-12:continue
  pieces=[];inside=(reg^cropped).as_original()
  if inside.volume()>1e-12:pieces.append(inside)
  v,f=vf(cropped)
  for tri in v[f]:
   if np.any(tri.min(0)-pad>bb[3:]) or np.any(tri.max(0)+pad<bb[:3]):continue
   prism=md.Manifold.hull_points((tri[:,None]+offsets[None]).reshape(-1,3))
   piece=(reg^prism).as_original()
   assert piece.volume()>-1e-8,('negative intersection',piece.volume())
   if piece.volume()>1e-12:pieces.append(piece)
  if pieces:out.append(union(pieces).as_original())
 return union(out).as_original()
'''+s[b:]
p.write_text(s,encoding='utf-8')
p=Path(__file__).parent/'controls_revo22_f5_436.py';s=p.read_text(encoding='utf-8-sig').replace('[.999,.499,.499],[1.05,.501,.501]','[.999,.49,.49],[1.05,.51,.51]');p.write_text(s,encoding='utf-8')
