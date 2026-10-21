"""Local reconstruction of O3 carrier/track geometry, not full repository CAD.
Source: b2c54e380004c90317463fa5ef26c780171a0ce6
Hardware/PoseDoll44/cad/revO3/compact_joint.py.
Only positive ear stops are investigated. Friction, deformation and bonding are not simulated.
"""
from pathlib import Path
import json, math
import cadquery as cq

def cyl(r,z0,z1): return cq.Solid.makeCylinder(r,z1-z0,cq.Vector(0,0,z0))
def ring(ro,ri,z0,z1): return cyl(ro,z0,z1).cut(cyl(ri,z0-.01,z1+.01))
def box(x,y,z,c): return cq.Workplane('XY').box(x,y,z).translate(c).val()

def main():
    # At the FRONT carrier plane (z=-0.8..0), the source cup is a 15/12.35 ring.
    # Female thread and rear details are below this cross-section.
    cup = ring(15,12.35,-.8,0)
    carrier=ring(12.1,4.3,-.8,0)
    for x in (-12.9,12.9):
        cup=cup.cut(box(2.6,4.16,14.81,(x,0,-7.405)))
        carrier=carrier.fuse(box(2.4,4.0,.8,(x,0,-.4)))
    checks=[]
    for a in (-.4,-.35,-.33,-.32,-.30,0,.30,.32,.33,.35,.4):
        v=carrier.rotate((0,0,0),(0,0,1),a).intersect(cup).Volume()
        checks.append({'angle_deg':a,'intersection_mm3':v,'overlap_above_1e_4':v>1e-4})
    # At positive rotation, the outermost ear corner y=2*cos(a)+14.1*sin(a)
    # reaches the +2.08 track side first; this is a nominal geometric bound.
    lo,hi=0.0,math.radians(1)
    for _ in range(70):
        mid=(lo+hi)/2
        if 2*math.cos(mid)+14.1*math.sin(mid)<2.08:lo=mid
        else:hi=mid
    limit=math.degrees((lo+hi)/2)
    result={'scope':'SCOPED_CAD_RECONSTRUCTION_NOT_FULL_ASSEMBLY_OR_PHYSICAL_TEST',
      'source_commit':'b2c54e380004c90317463fa5ef26c780171a0ce6',
      'nominal_track_width_mm':4.16,'nominal_ear_width_mm':4.0,
      'one_sided_positive_stop_gap_deg':limit,'full_stop_to_stop_clearance_deg':2*limit,
      'checks':checks,'interpretation':'Positive torque ear geometry allows nominal clearance. Back-face friction may restrain motion but is unqualified; this is not a measured output drift or sensor error.',
      'excluded':['Complete cup geometry outside front carrier slice','Preload friction at all contacts','Elasticity, wear, tolerance extrema','Combined shaft-key clearance']}
    path=Path(__file__).resolve().parents[1]/'results/backing_clearance.json'
    path.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2))
if __name__=='__main__':main()
