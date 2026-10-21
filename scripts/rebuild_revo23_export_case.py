"""Re-evaluate the case's existing analytic features without legacy Boolean faces."""
from build_revo23 import *
from build_revo23_wire_seats import saddle
from deepen_revo23_backpack import screw_frame
import itertools

def clean_case():
    floor=box([-5,-5,0],[69,65,2])
    wall=box([-5,-5,1],[69,65,32])-box([-3,-3,.9],[67,63,32.1])
    for u in (-6,66):wall=wall-box([u,10,4],[u+4,50,29])
    wall=wall-box([2,-6,21],[23,-2,32.1])-box([25,62,16],[40,66,32.1])
    mounts=[(3,3),(61,3),(3,57),(61,57)]
    posts=union([(kin.b.b.cyl(2.8,1.8,14)-kin.b.b.cyl(.85,8,15)).translate([u,v,0]) for u,v in mounts])
    capboss=union([(kin.b.b.cyl(2.5,1.5,32)-kin.b.b.cyl(.85,25,33)).translate([u,v,0]) for u,v in [(-2,-2),(66,-2),(-2,62),(66,62)]])
    capboss=capboss-box([-.3,-.3,12],[64.3,60.3,33])
    C0=np.eye(4);C0[:3,:3]=[[0,0,-1],[-1,0,0],[0,1,0]];C0[:3,3]=[-55,32,496]
    ears=union([box([-57,y-5,z-6],[-55,y+5,z+6]) for y,z in itertools.product((-40.,40.),(500.,521.))])
    for y,z in itertools.product((-40.,40.),(500.,521.)):
        ears-=move(kin.b.b.cyl(1.7,-9,3.5),screw_frame([-57.2,y,z]))
    housing=union([floor,wall,posts,capboss,move(ears,np.linalg.inv(C0))])
    p=read(B/'profiles/device_profile.json');N=frames(p,p['neutral_raw_deg'])['f:chest']
    C=C0.copy();C[:3,3]=read(CFG)['controller_front_corner_neutral_mm'];T=np.linalg.inv(N)@C
    pad,tunnel=saddle(16)
    for r in read(B/'harness/wire_seats.json')['seats']:
        if r['part']!='o22/controller_housing':continue
        M=np.linalg.inv(T)@np.array(r['transform_body_mm'])
        M=np.round(M,10)
        shape=move(pad,M)^box([-30,-10,0],[95,75,50])
        shape-=box([-5.3,-5.3,31.9],[69.3,65.3,50])
        housing+=shape
    return move(housing,T)

if __name__=='__main__':
    from probe_revo23_stl import load_current,WORK,trial
    src=load_current()['o22/controller_housing']['s'];c=clean_case()
    print('CASE SOURCE',src.volume(),'NEW',c.volume(),'components',len(c.decompose()),'genus',c.genus(),flush=True)
    print('DIFF',(src-c).volume(),(c-src).volume(),flush=True)
    v,f=vf(c);np.savez_compressed(WORK/'case_rebuilt.npz',v=v,f=f)
    for tol in (0,.0001):
        m,r=trial(c,tol);print('REBUILT',r,flush=True)
