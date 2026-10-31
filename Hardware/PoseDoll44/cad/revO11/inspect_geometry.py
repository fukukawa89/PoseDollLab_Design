from solid_ops import *
r={k:from_tri(t) for k,t in np.load(OUT/'printed_core/parts.npz').items()};r.update({'old_'+k:from_tri(t) for k,t in np.load(G8/'fastened_core/fasteners.npz').items()})
for fk,axis,q in [('C01',0,-25),('C02',1,75)]:
 f=pose(r[fk],rot(axis,q))
 for k,s in r.items():
  if k in ('C01','C02'):continue
  i=f^s
  if i.volume()>1e-4:print(fk,k,record(i))
