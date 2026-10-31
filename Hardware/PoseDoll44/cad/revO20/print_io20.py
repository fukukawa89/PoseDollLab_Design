from base import *
import struct

def stl(path,shape):
 full=tri(shape);tt=full.astype('<f4');normal=np.cross(tt[:,1]-tt[:,0],tt[:,2]-tt[:,0]);length=np.linalg.norm(normal.astype(float),axis=1)
 mask=length>0;tt=tt[mask];normal=normal[mask]/length[mask,None]
 # A float32 STL can collapse distinct near-coincident vertices. If its
 # topology is not closed, use standard ASCII STL with 17-digit coordinates.
 # Do not raise tolerances or discard nonzero faces to hide the failure.
 try:
  back=from_tri_exact(tt.astype(float));valid=solid_count(back)==1
  _,ix=np.unique(tt.reshape(-1,3),axis=0,return_inverse=True);ff=ix.reshape(-1,3)
  edges=np.concatenate([ff[:,[0,1]],ff[:,[1,2]],ff[:,[2,0]]]);_,counts=np.unique(np.sort(edges,axis=1),axis=0,return_counts=True)
  valid=valid and bool(np.all(counts==2))
 except ValueError:valid=False
 if valid:
  out=bytearray(b'PoseDoll O20 mm; lightweight design; physical load test not performed'.ljust(80,b' '));out+=struct.pack('<I',len(tt))
  for t,n in zip(tt,normal):out+=struct.pack('<12fH',*n,*t.ravel(),0)
  path.write_bytes(out);return 'BINARY_FLOAT32'
 with path.open('w',encoding='ascii',newline='\n') as f:
  f.write('solid PoseDoll_O20_mm\n')
  for t in full:
   n=np.cross(t[1]-t[0],t[2]-t[0]);n/=max(np.linalg.norm(n),1e-30)
   f.write('facet normal '+' '.join(format(float(v),'.17g') for v in n)+'\nouter loop\n')
   for vertex in t:f.write('vertex '+' '.join(format(float(v),'.17g') for v in vertex)+'\n')
   f.write('endloop\nendfacet\n')
  f.write('endsolid PoseDoll_O20_mm\n')
 return 'ASCII_FLOAT64'
