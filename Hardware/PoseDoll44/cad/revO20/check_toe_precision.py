from base import *
from export_print_batch import orient
from verify_exports import topology
z=np.load(OUT/'changed_parts.npz');rows=[]
for key in ('frame/foot_l','frame/foot_r'):
 s=from_tri_exact(z[key]);print('SOURCE',key,topology(tri(s)),flush=True)
 for tol in (1e-10,1e-8,1e-6,1e-5,1e-4):
  q=s.simplify(tol);b,bed=orient(q)
  for bt in (0,1e-8,1e-6):
   t=b.simplify(bt) if bt else b;tt=tri(t);e=topology(tt);ee=topology(tt.astype('float32').astype(float));vol=abs(t.volume()-s.volume());print(key,tol,bt,'edges',e,ee,'solid',solid_count(t),'delta',vol,flush=True);rows.append({'part':key,'local_simplify_mm':tol,'bed_simplify_mm':bt,'edges64':e,'edges32':ee,'volume_delta_mm3':vol})
g.write(OUT/'toe_mesh_precision_experiment.json',{'rows':rows})
