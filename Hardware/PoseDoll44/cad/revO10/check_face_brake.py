"""Check enlarged face-brake motion and classify only declared contact surfaces."""
from module_frames import *
from rigid_collision import Body,Pair
import itertools,argparse,time

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--quick',action='store_true');args=ap.parse_args();raw=dict(np.load(OUT/'face_brake/parts.npz'));fast=np.load(H/'generated/revO8/runs/o8_20260925_r1/fastened_core/fasteners.npz')
 metal=np.concatenate([t for n,t in raw.items() if n not in ('C01','C02')]+list(fast.values()));m={'C01':raw['C01'],'C02':raw['C02'],'ring':metal};lib={n:Body(t) for n,t in m.items()};pairs={(x,y):Pair(lib[x],lib[y]) for x,y in [('C01','C02'),('C01','ring'),('C02','ring')]};rows=[]
 angles=[(0,0),(25,96.2),(-25,-96.2),(28,0),(29,0),(0,98),(0,99)] if args.quick else list(itertools.product((-28,-25,-15,0,15,25,28),(-98,-96.2,-75,-50,-25,0,25,50,75,96.2,98)))
 for a,b in angles:
  A=rot([1,0,0],a);M={'C01':np.eye(3),'ring':A,'C02':A@rot([0,1,0],b)};findings=[]
  for (x,y),pair in pairs.items():
   r=pair.check(M[x],M[y],tol=.01)
   if r['status']=='CONTACT_REQUIRES_REVIEW' and y=='ring':
    # Collision filter points on the fork body, tested in its local frame.
    cell=pair.c.GetContactCells(0);ids=np.unique([cell.GetValue(i) for i in range(cell.GetNumberOfValues())]);t=pair.a.faces[ids];pts=t.reshape(-1,3);ax=0 if x=='C01' else 1;rad=np.linalg.norm(np.delete(pts,ax,axis=1),axis=1)
    # Full faces adjacent to a contact may extend outside the patch; use actual
    # contact segment endpoints from vtk rather than label entire touched faces.
    cp=pair.c.GetContactsOutput().GetPoints();p=np.array([cp.GetPoint(i) for i in range(cp.GetNumberOfPoints())])@M[x]
    rr=np.linalg.norm(np.delete(p,ax,axis=1),axis=1);planes=np.minimum(abs(abs(p[:,ax])-11.5),abs(abs(p[:,ax])-14.5));ok=(planes<.02)&(rr>=2.1)&(rr<=6.02)
    r['declared_friction_contact_points']=int(ok.sum());r['other_contact_points']=int((~ok).sum())
    if np.all(ok):r['status']='DECLARED_FRICTION_FACE_CONTACT_ONLY'
   if not r['status'].startswith('CLEAR'):findings.append({'pair':[x,y],**r})
  row={'alpha':a,'beta':b,'findings':findings};rows.append(row);print(a,b,findings if args.quick else [(r['pair'],r['status']) for r in findings],flush=True)
  (OUT/'face_brake'/('quick_motion.json' if args.quick else 'motion_grid.json')).write_text(json.dumps({'cases':rows,'scope':'Nominal enlarged face brake, explicit steel axles/springs, inherited ring fasteners. Only recognized annular friction-plane contact is intentional. Stop endpoints remain separately reviewable.','manufacturing_released':False},indent=2)+'\n')
if __name__=='__main__':main()
