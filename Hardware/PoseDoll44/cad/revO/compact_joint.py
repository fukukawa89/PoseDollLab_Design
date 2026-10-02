"""Fixed-size Rev O coaxial joint study, independent from scaled anatomy.
Axial bearing datum is separate from the spring-loaded friction pressure plate.
Metal closed preload path; bearing endplay, lining friction and spring still need tests.
"""
from pathlib import Path
import sys, math
import cadquery as cq
ROOT=Path(__file__).resolve().parents[2]
REPO=ROOT.parents[1]
sys.path.insert(0,str(REPO/'scripts'))
from revo_common import read, save, sha
SPECS=read(ROOT/'mechanical_manifest/desktop_revO.json')
DENSITY={'aluminum':.00270,'steel':.00785,'pom':.00141,'lining':.00180,'magnet':.00750,'pcb':.00185,'nylon':.00114}
COLORS={'aluminum':'#9eb5c8','steel':'#6c7885','pom':'#d9d7b4','lining':'#b1764d','magnet':'#db6256','pcb':'#319b7c','nylon':'#becfe0','reservation':'#e9ae4c'}

def cylinder(r,z0,z1):
    return cq.Solid.makeCylinder(r,z1-z0,cq.Vector(0,0,z0))
def ring(ro,ri,z0,z1):
    return cylinder(ro,z0,z1).cut(cylinder(ri,z0-.1,z1+.1))
def box(x,y,z,center=(0,0,0)):
    return cq.Workplane('XY').box(x,y,z).translate(center).val()
def bounds(s):
    b=s.BoundingBox()
    return [b.xmin,b.ymin,b.zmin,b.xmax,b.ymax,b.zmax]

def module(family):
    s=SPECS['joint_families'][family];r=s['journal_mm']/2;ro=s['body_outer_radius_mm'];fr=s['friction_outer_radius_mm'];ri=s['friction_inner_radius_mm']
    rows=[]
    def add(name,shape,material,role='solid',note=''):
        assert shape.isValid(),name
        rows.append(dict(name=name,shape=shape,material=material,role=role,note=note))
    # A closed cup reacts spring force into the bearing shoulder. Its threaded
    # rear cap pushes a floating keyed plate, NOT the sensor or bearing spacer.
    housing=ring(ro,fr+.4,-9,-1).fuse(ring(ro,r+1,-1,4))
    for x in (-ro-3,ro+3):
        ear=box(8,7,3,(x,0,2.5)).cut(cylinder(1.35,.9,4.1).translate((x,0,0)))
        housing=housing.fuse(ear)
    add('fixed_metal_housing',housing,'aluminum',note='Machined 6061; rear adjustment thread not helically modeled. M2.5 mounting pilots need supplier review.')
    add('radial_bush',ring(r+.98,r+.03,-.8,3.8),'pom',note='Nominal 0.06 mm diametral running clearance; test and ream by supplier.')
    add('axial_datum_washer',ring(fr,ri,-1.4,-1),'pom',note='Hard bearing datum. Preload friction lining is on the opposite face of the rotor disk.')
    shaft=cylinder(r,-14,4.03).fuse(cylinder(fr,-2.4,-1.4)).fuse(cylinder(r+1.5,4.03,4.83)).fuse(cylinder(4.2,4.83,9))
    shaft=shaft.cut(cylinder(3.05,6.5,9.1))
    shaft=shaft.cut(box(10,12,6,(r-.5+5,0,-11.5)))
    add('integral_rotor_shaft_and_magnet_seat',shaft,'aluminum',note='7075 preferred for D-tail; separate 4/6 mm journal. Axial endplay nominal 0.03 mm; precision production and axial retention review pending.')
    add('replaceable_friction_lining',ring(fr,ri,-3,-2.4),'lining',note='One friction face; mu 0.08–0.22 is a hypothesis, not a material rating.')
    plate=ring(fr,ri,-4.2,-3)
    for sx in (-1,1):
        # Key pockets are explicitly cut in the housing, not hidden overlaps.
        key=box(1.3,2,1.2,(sx*(fr+.25),0,-3.6))
        plate=plate.fuse(key)
        rows[0]['shape']=rows[0]['shape'].cut(box(1.5,2.2,2.8,(sx*(fr+.25),0,-3.5)))
    add('keyed_floating_pressure_plate',plate,'steel')
    # The spring volume is a packaging reservation. Do not count it as a real
    # spring rate, catalogue selection, or a solid collision success.
    add('wave_spring_space',ring(fr-.3,ri+.3,-7.4,-4.2),'steel','reservation','Custom wave/disc spring pack, 3.2 mm working space; spring curve NOT_SELECTED.')
    cap=ring(ro-.05,r+.3,-10,-7.4)
    for x in (-ro+2.1,ro-2.1):
        cap=cap.cut(cylinder(.8,-10.1,-8.4).translate((x,0,0)))
    add('threaded_adjuster_cap',cap,'aluminum',note='Pin-spanner adjustment; nominal thread engagement 1.6 mm is NOT production qualified.')
    # Nominal thread envelope is kept separate from actual thread interference.
    rows[0]['shape']=rows[0]['shape'].cut(cylinder(ro,-9.1,-7.4))
    add('diametric_6x2p5_magnet',cylinder(3,6.5,9),'magnet')
    add('removable_magnet_keeper',ring(4.2,2.8,9,9.5),'nylon',note='Retention fastening unfinished; no adhesive-only manufacturing release.')
    pcbdatum=9+1.5+1.995
    actual=cq.importers.importStep(str(ROOT/'electronics/sensor_revM_side/sensor_revM_side.step')).val()
    actual=actual.translate((-100,100,0)).rotate((0,0,0),(1,0,0),180).translate((0,0,pcbdatum))
    for i,shape in enumerate(actual.Solids()):
        add(f'sensor_pcba_existing_{i}',shape,'pcb',note='Actual unscaled sensor_revM_side STEP; board, AS5048A and connector retained.')
    for sx in (-1,1):
        x=sx*(ro-1)
        post=ring(1.8,.85,4,pcbdatum-.91).translate((x,0,0))
        saddle=box(max(2,ro-5),3,.8,(sx*(ro+5)/2,0,pcbdatum-1.31))
        add(f'fixed_sensor_post_{sx}',post.fuse(saddle),'aluminum',note='Support only; final edge clamp screw/counterbore and assembly reach pending.')
    add('sensor_plug_and_wire_tail',box(9,6,12,(0,0,pcbdatum+9)),'reservation','reservation','Independent reservation; not ignored by space report. Exact mating plug/strain relief pending supplier STEP.')
    add('adjustment_tool_access',cylinder(ro,-24,-10.01),'reservation','reservation','Service space, not a physical part; remove downstream limb to access rear cap.')
    for q in rows:assert q['shape'].isValid(),q['name']
    reff=2/3*(fr**3-ri**3)/(fr**2-ri**2)/1000
    pre=s['preload_explore_N'];mu=SPECS['uncertainty']['friction_mu_range_assumed']
    solids=[q for q in rows if q['role']=='solid']
    compound=cq.Compound.makeCompound([q['shape'] for q in solids])
    meta={'family':family,'status':'KINEMATIC_SINGLE_AXIS_DESIGN_STUDY_NOT_READY_FOR_MANUFACTURE',
          'solid_bounds_mm':bounds(compound),'magnet_face_mm':9,'sensor_package_face_mm':10.5,'nominal_gap_mm':1.5,
          'fixed_hardware_scaled':False,'journal_mm':s['journal_mm'],'core_diameter_mm':2*ro,
          'preload_explore_N':pre,'assumed_mu_range':mu,'effective_friction_radius_m':reff,
          'torque_explore_Nm':[pre[0]*mu[0]*reff,pre[1]*mu[1]*reff],
          'preload_to_holding_vs_breakaway_ratio_mu_only':mu[1]/mu[0],
          'modeled_mass_g_excluding_spring_fasteners_plug':sum(q['shape'].Volume()*DENSITY[q['material']] for q in solids),
          'unresolved':['Spring part/curve and pressure stress','Endplay and axial datum production tolerance','Final magnet keeper fasteners','Final PCB edge clamps','Metal thread tolerance/engagement','Wear/friction/creep and full load test'],
          'physical_tested':False,'manufacturing_released':False}
    return rows,meta
