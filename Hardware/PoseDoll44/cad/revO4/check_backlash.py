"""Local reconstruction of O3 carrier/track geometry, not full repository CAD.
Source: b2c54e380004c90317463fa5ef26c780171a0ce6
Hardware/PoseDoll44/cad/revO3/compact_joint.py.
Only positive ear stops are investigated. Friction, deformation and bonding are not simulated.
"""
from pathlib import Path
import json, math
import cadquery as cq
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[4]/'scripts'))
from revo4_evidence import run_paths,save,sha,HW

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
    v,o=run_paths();folder=o/'backlash';folder.mkdir(parents=True,exist_ok=True)
    cq.exporters.export(cq.Compound.makeCompound([cup,carrier]),str(folder/'O3_front_section.step'))
    result['source_file_sha256']=sha(HW/'cad/revO3/compact_joint.py')
    result['tolerance_study']=[]
    for ew,sw in ((4.0,4.16),(4.02,4.14),(3.98,4.18),(4.0,4.04),(4.02,4.02),(4.04,4.00)):
        low,high=0,math.radians(1)
        for _ in range(70):
            a=(low+high)/2
            if ew/2*math.cos(a)+14.1*math.sin(a)<sw/2:low=a
            else:high=a
        result['tolerance_study'].append({'ear_width_mm':ew,'slot_width_mm':sw,'full_clearance_deg':math.degrees(low+high) if sw>=ew else None,'interference_mm':max(0,ew-sw),'qualification':'GEOMETRY_ONLY_NO_LOADED_SLIDING_CREDIT'})
    result['wall_candidate']={'current_radius_mm':15,'thicker_radius_mm':16,'slot_corner_radius_mm':math.hypot(14.2,2.08),'current_radial_ligament_mm':15-math.hypot(14.2,2.08),'thicker_radial_ligament_mm':16-math.hypot(14.2,2.08),'strength':'NOT_QUALIFIED; thread interruptions remain; separate rail/load path still to design'}
    result['required_next_tests']=['fixed front backing positive retention','rear axial guide loaded slip and anti-backlash','bond coupon shear/peel/creep','output coupler and full reverse torque chain','actual maximum spring force and stop','complete chest/shoulder/arm with A/C harness']
    save(v/'backlash.json',result)
    print(json.dumps(result,indent=2))
if __name__=='__main__':main()
