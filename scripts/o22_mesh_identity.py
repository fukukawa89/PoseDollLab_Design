import hashlib,numpy as np
def body_sha(n):
 h=hashlib.sha256()
 for key,dtype in [("v","<f8"),("f","<i8")]:
  a=np.asarray(n[key],dtype=dtype,order="C");h.update(str(a.shape).encode());h.update(a.tobytes())
 return h.hexdigest()
