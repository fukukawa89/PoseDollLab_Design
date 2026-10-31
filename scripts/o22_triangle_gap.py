"""Bounded exact triangle-surface gap, independent of Manifold.min_gap.
For disjoint closed solids, includes all vertex/triangle and edge/edge minima.
"""
import numpy as np,trimesh

def segment_gap2(p0,p1,q0,q1):
 u=p1-p0;v=q1-q0;w=p0-q0;a=np.einsum('ij,ij->i',u,u);b=np.einsum('ij,ij->i',u,v);c=np.einsum('ij,ij->i',v,v);d=np.einsum('ij,ij->i',u,w);e=np.einsum('ij,ij->i',v,w);D=a*c-b*b
 sd=D.copy();td=D.copy();sn=b*e-c*d;tn=a*e-b*d;parallel=D<1e-20
 sn[parallel]=0;sd[parallel]=1;tn[parallel]=e[parallel];td[parallel]=c[parallel]
 low=sn<0;high=sn>sd;sn[low]=0;tn[low]=e[low];td[low]=c[low];sn[high]=sd[high];tn[high]=e[high]+b[high];td[high]=c[high]
 low=tn<0;high=tn>td;tn[low]=0;sn[low]=np.clip(-d[low],0,a[low]);sd[low]=a[low];tn[high]=td[high];sn[high]=np.clip(b[high]-d[high],0,a[high]);sd[high]=a[high]
 s=np.divide(sn,sd,out=np.zeros_like(sn),where=abs(sd)>1e-30);t=np.divide(tn,td,out=np.zeros_like(tn),where=abs(td)>1e-30);delta=w+s[:,None]*u-t[:,None]*v;return np.einsum('ij,ij->i',delta,delta)

def triangle_pair_gap2(a,b):
 dist=np.full(len(a),np.inf)
 for j in range(3):
  p=trimesh.triangles.closest_point(b,a[:,j]);dist=np.minimum(dist,np.sum((p-a[:,j])**2,axis=1));p=trimesh.triangles.closest_point(a,b[:,j]);dist=np.minimum(dist,np.sum((p-b[:,j])**2,axis=1))
 for i in range(3):
  for j in range(3):dist=np.minimum(dist,segment_gap2(a[:,i],a[:,(i+1)%3],b[:,j],b[:,(j+1)%3]))
 return dist

def gap(a,b,cap=.2):
 a=np.asarray(a,float);b=np.asarray(b,float);bounds=np.c_[b.min(1),b.max(1)];tree=trimesh.util.bounds_tree(bounds);left=[];right=[]
 for i,tri in enumerate(a):
  ids=list(tree.intersection(np.r_[tri.min(0)-cap,tri.max(0)+cap]))
  if ids:left.extend([i]*len(ids));right.extend(ids)
 best=cap*cap;pair=None
 for start in range(0,len(left),10000):
  ia=np.array(left[start:start+10000]);ib=np.array(right[start:start+10000]);dist=triangle_pair_gap2(a[ia],b[ib]);j=int(np.argmin(dist))
  if dist[j]<best:best=float(dist[j]);pair=[int(ia[j]),int(ib[j])]
 return {'gap_mm_capped':float(np.sqrt(best)),'pair':pair,'triangle_pairs':len(left)}

if __name__=='__main__':
 a=np.array([[[0,0,0],[2,0,0],[0,2,0]]],float);b=a+[0,0,.12];assert abs(gap(a,b)['gap_mm_capped']-.12)<1e-12
 p=np.array([[0.,0,0]]);assert np.allclose(segment_gap2(p,p+[1,0,0],p+[.5,-1,.2],p+[.5,1,.2]),.04)
 assert np.allclose(segment_gap2(p,p+[1,0,0],p+[2,0,0],p+[3,0,0]),1)
 print('triangle distance controls passed')
