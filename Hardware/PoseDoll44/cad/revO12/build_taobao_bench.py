"""O12 independent coupon, adapted to user-photographed stock parts.
Zero-volume intersection is not proof of washer slip fit. O11 remains sealed.
"""
from pathlib import Path
import sys
sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent/'revO11'))
from build_printed_core import hex_prism, washer
from solid_ops import H, R, md, np, json, sha, rot, pose, cylinder, box, tri, from_tri, record
from export_print_pack import write_3mf, place
import itertools, struct

B = H/'bench/revO12'
G = H/'generated/revO12/runs/o12_20260926_r1'
PAGE = H/'tutorials/taobao-bench'
OLD = H/'bench/revO11/parts.npz'
NUT_Z, NUT_TOP, REACTION_TOP = 2.0, 4.4, 5.2
SHOULDER_FLOOR, BASE_FACE, EPS = 6.1, 8.0, 1e-4

def write_json(p, obj):
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(obj, ensure_ascii=False, indent=2, allow_nan=False)+'\n', encoding='utf-8')

def export_stl(p, s):
    t = tri(s)
    n = np.cross(t[:,1]-t[:,0], t[:,2]-t[:,0])
    n /= np.maximum(np.linalg.norm(n, axis=1, keepdims=True), 1e-14)
    rows = np.zeros(len(t), dtype=np.dtype([('n','<f4',(3,)),('v','<f4',(3,3)),('a','<u2')]))
    rows['n'], rows['v'] = n, t
    p.write_bytes(b'PoseDoll O12 coupon; mm; physical fit and strength unverified'.ljust(80,b' ')+struct.pack('<I',len(t))+rows.tobytes())
    back = np.frombuffer(p.read_bytes()[84:], dtype=rows.dtype)['v'].astype(float)
    assert abs(from_tri(back).volume()-s.volume()) < .03

def spring(z, height, flip=False):
    # Axial section envelope, not a material or force model.
    p = np.array([[2.1,z+height-.4],[4,z],[4,z+.4],[2.1,z+height]])
    if flip:
        p[:,1] = 2*z+height-p[:,1]
        p = p[::-1].copy()
    return md.CrossSection([p]).revolve(circular_segments=144)

def build(pair_height=.9):
    cavities = (hex_prism(5.8,NUT_Z-.15,NUT_TOP+.05)
                + cylinder(4.65,NUT_TOP-.05,REACTION_TOP)
                + cylinder(1.7,-.1,7) + cylinder(2.125,SHOULDER_FLOOR,8.5))
    base = box([-25,-15,0],[25,15,BASE_FACE])-cavities
    for x in (-20,20):
        base -= cylinder(2.25,-.1,8.1).translate([x,-9,0])
    parts = {}
    for n,x in enumerate((-10,10),1):
        frame, origin = rot(0,-90), [x,0,4]
        base -= pose(cylinder(1.7,-21,19),frame,origin)
        screw = cylinder(1.5,-20,15)+cylinder(2.8,15,18)-hex_prism(2.5,16.5,18.1)
        nut = hex_prism(5.5,-17.4,-15)-cylinder(1.55,-17.5,-14.9)
        parts[f'case_M3x35_{n}'] = pose(screw,frame,origin)
        parts[f'case_M3_nut_{n}'] = pose(nut,frame,origin)
    parts['printed_base_minus'] = base^box([-30,-20,-1],[30,0,9])
    parts['printed_base_plus'] = base^box([-30,0,-1],[30,20,9])
    # Exactly reuse the lever; only the two base halves need a new print.
    parts['printed_lever'] = from_tri(np.load(OLD)['printed_lever'])
    head = 13+pair_height+.8
    neck = head-8
    bolt = cylinder(1.5,neck-6,neck)+cylinder(2,neck,head)+cylinder(3.5,head,head+3)
    bolt -= hex_prism(3,head+1.5,head+3.1)  # socket depth is only a display assumption
    parts.update({
        'inner_M4_wide':washer(6,2,8,1), 'outer_M4_wide':washer(6,2,12,1),
        'spring_1':spring(13,pair_height/2),
        'spring_2':spring(13+pair_height/2,pair_height/2,True),
        'front_M4_washer':washer(4.5,2,13+pair_height,.8),
        'shoulder_D4_L8_M3_thread6':bolt,
        'M3_nut':hex_prism(5.5,NUT_Z,NUT_TOP)-cylinder(1.55,NUT_Z-.1,NUT_TOP+.1),
        'M3_reaction_washer':washer(4.5,1.5,NUT_TOP,.8)})
    # Materialize CSG before reusing it in union/intersection trees. Preserve
    # independent solids and use the inherited 1e-5 mm mesh welding precision.
    return {k:from_tri(tri(v)) for k,v in parts.items()}

def collisions(parts):
    return [{'pair':[a,b],'volume_mm3':float(v)}
            for a,b in itertools.combinations(parts,2)
            if (v:=(parts[a]^parts[b]).volume()) > EPS]

def validate(parts):
    before = {k:record(v) for k,v in parts.items()}
    cases, motion = [], []
    for h in (1.2,1.1,1,.9):
        trial = build(h)
        head = 13+h+.8
        tip,neck = head-14,head-8
        cases.append({'spring_pair_height_mm':h,'thread_tip_z_mm':round(tip,4),
                      'nominal_thread_overlap_mm':round(min(neck,NUT_TOP)-max(tip,NUT_Z),4),
                      'protrusion_past_nut_mm':round(NUT_Z-tip,4),
                      'O11_base_same_6mm_screw_protrusion_mm':round(1-tip,4),
                      'shoulder_floor_clearance_mm':round(neck-SHOULDER_FLOOR,4),
                      'findings':collisions(trial)})
        for angle in range(-180,181,5):
            lever = pose(trial['printed_lever'],rot(2,angle))
            hits = [{'part':k,'volume_mm3':float(v)} for k,s in trial.items()
                    if k!='printed_lever' and (v:=(lever^s).volume()) > EPS]
            motion.append({'pair_height_mm':h,'lever_angle_deg':angle,'findings':hits})
    insertions = []
    for name in ('M3_nut','M3_reaction_washer'):
        volumes = [(parts['printed_base_minus']^parts[name].translate([0,float(d),0])).volume()
                   for d in np.linspace(0,15,31)]
        insertions.append({'part':name,'step_mm':.5,'samples':31,'max_overlap_mm3':max(volumes)})
    fixed = parts['printed_base_minus']+parts['M3_nut']+parts['M3_reaction_washer']
    closure = max((fixed^parts['printed_base_plus'].translate([0,float(d),0])).volume()
                  for d in np.linspace(0,15,31))
    base = parts['printed_base_minus']+parts['printed_base_plus']
    retention = [{'outward_translation_mm':d,
                  'nut_into_washer_mm3':(parts['M3_nut'].translate([0,0,d])^parts['M3_reaction_washer']).volume(),
                  'washer_into_base_mm3':(parts['M3_reaction_washer'].translate([0,0,d])^base).volume()}
                 for d in (.1,.5)]
    tool = hex_prism(2.95,14.7,54.7)
    tools = [{'part':k,'volume_mm3':float(v)} for k,s in parts.items()
             if k!='shoulder_D4_L8_M3_thread6' and (v:=(tool^s).volume()) > EPS]
    fits = []
    for label,bores,shaft in [('M4_on_shoulder',(3.95,4,4.05,4.3),4),
                              ('M3_on_thread_major_envelope',(2.95,3,3.05,3.2),3)]:
        for bore in bores:
            gap = round(bore-shaft,4)
            fits.append({'interface':label,'bore_mm':bore,'shaft_mm':shaft,'diametral_clearance_mm':gap,
                         'status':'INTERFERENCE' if gap<0 else 'ZERO_ALLOWANCE_NOT_SLIP_FIT' if gap==0 else 'NOMINAL_CLEARANCE_REQUIRES_ACTUAL_FIT'})
    sensitivity = []
    for h,shoulder,thread,seat,thick,dh in itertools.product((1.2,1.1,1,.9),(7.9,8.1),(5.8,6.2),(1.8,2.2),(2.3,2.5),(-.1,.1)):
        neck = 13+h+dh+.8-shoulder
        full_start,full_end = neck-thread+.5,neck-.3
        sensitivity.append({'spring_pair_mm':h,'shoulder_mm':shoulder,'thread_mm':thread,
                            'nut_start_mm':seat,'nut_thickness_mm':thick,'stack_error_mm':dh,
                            'tip_full_thread_margin_mm':round(seat-full_start,4),
                            'effective_thread_overlap_mm':round(max(0,min(seat+thick,full_end)-max(seat,full_start)),4)})
    result = {'status':'NOMINAL_GEOMETRY_CHECKED_PHYSICAL_FIT_REQUIRED',
              'pair_checks_per_stack':len(list(itertools.combinations(parts,2))),
              'stack_cases':cases,'sampled_lever_motion':motion,'insertions':insertions,
              'half_closure_max_overlap_mm3':closure,'axial_retention_obstructions':retention,
              'straight_AF3_tool_shank_findings':tools,
              'tool_scope':'External straight shank only; socket depth and wrench handle not verified.',
              'washer_fit_counterexamples':fits,'thread_sensitivity':sensitivity,
              'sensitivity_assumptions':'Assumed +/-0.1 shoulder, +/-0.2 thread and nut seat, +/-0.1 nut thickness and stack; 0.5 tip and 0.3 root non-full-thread regions. Not measured or supplier-approved tolerances.',
              'sensitivity_min_effective_overlap_mm':min(r['effective_thread_overlap_mm'] for r in sensitivity),
              'printed_load_web_mm':round(BASE_FACE-REACTION_TOP,3),'O11_printed_load_web_mm':3.8,
              'washer_actual_slip_fit':None,'spring_measured_force_N':None,
              'strength_verified':False,'physical_tested':False,'manufacturing_released':False}
    assert not any(r['findings'] for r in cases+motion)
    assert max(r['max_overlap_mm3'] for r in insertions)<EPS and closure<EPS
    assert all(r['nut_into_washer_mm3']>.01 and r['washer_into_base_mm3']>.01 for r in retention)
    assert not tools
    assert all(record(s)['solid_components']==1 and s.volume()>0 for s in parts.values())
    assert before == {k:record(v) for k,v in parts.items()}, 'CSG checks changed an input solid'
    result['mesh_weld_precision_mm'] = 1e-5
    return result

def export(parts,checks):
    np.savez_compressed(B/'parts.npz',**{k:tri(s) for k,s in parts.items()})
    beds = {'printed_lever':place(parts['printed_lever'],np.eye(3),8,8),
            'printed_base_minus':place(parts['printed_base_minus'],rot(0,-90),8,35),
            'printed_base_plus':place(parts['printed_base_plus'],rot(0,90),70,35)}
    folder = B/'print_beds'
    folder.mkdir(exist_ok=True)
    audit = write_3mf(folder/'O12_taobao_bench.3mf',beds)
    for k,s in beds.items():
        export_stl(folder/(k+'_on_bed.stl'),s)
        assert abs(s.bounding_box()[2])<1e-7
    write_json(folder/'export_check.json',{'parts':audit,'unit':'mm','roundtrip_volume_tolerance_mm3':.03,
                                         'gcode_included':False,'printer_profile_included':False,'slicer_tested':False})
    labels = {'printed_base_minus':'打印底座 · 后半（螺母座前移 1 mm）',
              'printed_base_plus':'打印底座 · 前半（螺母座前移 1 mm）',
              'printed_lever':'打印长臂 · 沿用 O11',
              'M3_nut':'内部 M3 六角螺母 · 对边 5.5 / 厚 2.4',
              'M3_reaction_washer':'M3 大垫圈 · 标称孔 3 / 外径 9 / 厚 0.8',
              'inner_M4_wide':'内侧 M4 大垫圈 · 标称孔 4 / 外径 12 / 厚 1',
              'outer_M4_wide':'外侧 M4 大垫圈 · 标称孔 4 / 外径 12 / 厚 1',
              'front_M4_washer':'M4 普通垫圈 · 标称孔 4 / 外径 9 / 厚 0.8',
              'shoulder_D4_L8_M3_thread6':'304 轴肩螺钉 · Φ4×8 / M3 螺纹长 6 / 扳手 3',
              'spring_1':'不锈钢 A8 碟簧 · 第一片（弹力待测）',
              'spring_2':'不锈钢 A8 碟簧 · 第二片（反向）'}
    models,group = {},[]
    for k,s in parts.items():
        t = tri(s.simplify(.03))
        v,idx = np.unique(np.round(t.reshape(-1,3),4),axis=0,return_inverse=True)
        models[k] = {'v':v.tolist(),'f':idx.reshape(-1,3).tolist()}
        printed = k.startswith('printed_')
        color = '#ad6744' if k=='printed_lever' else '#507565' if printed else '#485d73' if 'spring' in k else '#a8afb4'
        label = labels.get(k,k.replace('case_M3x35_','M3×35 底座连接螺钉 · ').replace('case_M3_nut_','M3 外侧螺母 · '))
        group.append({'name':k,'key':k,'label':label,'color':color,'printed':printed})
    (PAGE/'models.js').write_text('window.O12_MODELS='+json.dumps(models,separators=(',',':'))+';\nwindow.O12_GROUPS='+json.dumps({'bench':group},ensure_ascii=False,separators=(',',':'))+';\n',encoding='utf-8')
    (PAGE/'results.js').write_text('window.O12_RESULTS='+json.dumps({'parts':len(parts),'pairChecks':checks['pair_checks_per_stack'],
                                'stackCases':len(checks['stack_cases']),'motionCases':len(checks['sampled_lever_motion']),
                                'actualFit':None,'physicalTested':False})+';\n',encoding='utf-8')

def main():
    assert not (G/'evidence_manifest.json').exists(),'Sealed run: create a new revision.'
    for p in (B,G,PAGE): p.mkdir(parents=True,exist_ok=True)
    inputs = [OLD,H/'generated/revO11/runs/o11_20260926_r1/evidence_manifest.json',
              Path(__file__),B/'procurement.json',HERE.parent/'revO11/solid_ops.py',
              HERE.parent/'revO11/build_printed_core.py',HERE.parent/'revO11/export_print_pack.py',
              H/'generated/revO11/runs/o11_20260926_r1/loads.json']
    hashes = {p.relative_to(R).as_posix():sha(p) for p in inputs}
    parts = build()
    checks = validate(parts)
    checks['inputs_sha256'] = hashes
    export(parts,checks)
    loads = json.loads(inputs[-1].read_text(encoding='utf-8'))
    target = max(r['required_hold_Nm'] for c in loads['characters'] for n,r in c['physical_axes'].items() if n in ('alpha','beta'))/2
    plan = {'schema':'o12-taobao-coupon-v1','scope':'Independent coupon only; O11 core/full-body evidence is not re-certified.',
            'parts':{k:record(s) for k,s in parts.items()},'custom_metal_parts':0,
            'base_dimensions_mm':[50,30,8],'nut_axial_range_mm':[NUT_Z,NUT_TOP],
            'reaction_washer_axial_range_mm':[NUT_TOP,REACTION_TOP],'printed_load_web_mm':round(BASE_FACE-REACTION_TOP,3),
            'shoulder_thread_length_mm':6,'shoulder_socket_AF_mm':3,'socket_depth_display_assumption_mm':1.5,
            'washer_bores_as_advertised_mm':{'M4':4,'M3':3},'washer_bores_measured_mm':None,
            'stock_parts_fit_confirmed':False,'spring_material':'stainless steel, grade and condition unspecified',
            'spring_force_N':None,'spring_force_curve':None,'reuse_O11_210N_force_reference':False,
            'spring_pair_height_geometry_reference_mm':[1.1,1,.9],'free_pair_height_reference_mm':1.2,
            'single_site_screening_target_Nm':target,'target_source_sha256':sha(inputs[-1]),
            'physical_tested':False,'slicer_tested':False,'manufacturing_released':False,
            'nominal_findings':collisions(parts),'lever_geometry_unchanged_from_O11':True,'inputs_sha256':hashes}
    write_json(B/'plan.json',plan)
    write_json(G/'digital_checks.json',checks)
    fields = ['sample_id','printer_filament_orientation','actual_shoulder_diameter_mm','actual_shoulder_length_mm',
              'actual_thread_length_mm','thread_tip_chamfer_mm','M4_wide_slides_over_shoulder',
              'M4_normal_slides_over_shoulder','M3_wide_passes_thread_without_screwing',
              'actual_washer_dimensions_mm','actual_nut_dimensions_mm','spring_grade_and_batch',
              'spring_free_heights_mm','spring_material_thickness_mm','permanent_spring_set_mm',
              'spring_pair_height_mm','measured_axial_force_N','load_mass_g','actual_moment_arm_mm',
              'lever_hook_string_self_weight_torque_Nm','load_direction','hold_seconds','base_angle_change_deg',
              'lever_angle_change_deg','measurement_uncertainty_deg','breakaway_torque_Nm',
              'running_torque_Nm','screw_witness_mark_change','notes']
    write_json(B/'measurement_template.json',{'schema':'o12-taobao-observations-v1',**dict.fromkeys(fields)})
    assert hashes == {p.relative_to(R).as_posix():sha(p) for p in inputs}
    print(json.dumps({'parts':len(parts),'stack_cases':len(checks['stack_cases']),'motion_samples':len(checks['sampled_lever_motion']),
                      'nominal_findings':plan['nominal_findings'],'washer_fit':'REQUIRES_PHYSICAL_CHECK','spring_force_N':None,
                      'web_mm':plan['printed_load_web_mm'],'sensitivity_min_overlap_mm':checks['sensitivity_min_effective_overlap_mm']}))

if __name__=='__main__': main()
