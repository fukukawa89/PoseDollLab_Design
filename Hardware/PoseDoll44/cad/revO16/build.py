"""Build O16 single-hardware design package from locked O15 geometry.
No historic output or UE asset is written. Run from any working directory.
"""
from pathlib import Path
import copy, csv, io, json, shutil, sys, zipfile, hashlib
import numpy as np
HERE=Path(__file__).resolve().parent
H=HERE.parents[1]; REPO=H.parents[1]
OLD=H/'generated/revO15/runs/o15_20260929_r1'
OUT=H/'generated/revO16'; BENCH=H/'bench/revO16'; PAGE=H/'tutorials/full-doll-o16'
sys.path.insert(0,str(H/'cad/revO15'))
import layout_fullbody as source
from device import compound, forward, digest


def read(p): return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def write(p,d):
    p=Path(p);p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(json.dumps(d,ensure_ascii=False,indent=2,allow_nan=False)+'\n',encoding='utf-8')
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def profile():
    _,_,states,fail,pr=source.build('quinn',{},geometry=False)
    if fail: raise ValueError(fail)
    T,_=source.fk(pr,{})
    legacy=read(OLD/'raw46_mapping_candidate.json'); groups={x['id']:x for x in legacy['groups']}
    joints=[]; neutral={}; limits={}
    for s in states:
        g=groups[s['id']]; A=np.eye(4); A[:3,:3]=s['world_mount'];A[:3,3]=s['origin_mm']
        pre=np.linalg.inv(T[s['parent']])@A
        post=np.linalg.inv(A@compound(s['kind'],s['angles_deg']))@T[s['child']]
        joints.append({'id':s['id'],'kind':s['kind'],'parent':s['parent'],'child':s['child'],
            'raw_ids':g['raw_ids'],'parent_to_mount_mm':pre.tolist(),'rotor_to_child_mm':post.tolist(),
            'neutral_origin_mm':s['origin_mm'],'measurement':'MEASURED_COMPOSITION'})
        neutral.update(dict(zip(g['raw_ids'],s['angles_deg'])))
        limits.update(dict(zip(g['raw_ids'],g['raw_limits_deg'])))
    # Actual mechanical tree, including serial clavicle and wrist offsets.
    ordered=[]; known={'pelvis'}
    while joints:
        batch=[j for j in joints if j['parent'] in known]
        if not batch: raise ValueError('cyclic or disconnected physical tree')
        for j in batch: ordered.append(j);known.add(j['child']);joints.remove(j)
    leaves=[{'id':n['id'],'parent':n['parent'],
        'transform_mm':(np.linalg.inv(T[n['parent']])@T[n['id']]).tolist(),
        'measurement':'FIXED_GEOMETRY_MARKER'} for n in pr['nodes']
        if n['parent'] in known and not n.get('axis_id')]
    wiring=read(OLD/'raw46_wiring_candidate.json')
    p={'schema':'POSEDOLL-O16-DEVICE/1','profile_id':'o16_universal_v1','hardware_models':['universal'],
       'status':'DIGITAL_DESIGN_CANDIDATE_NOT_PHYSICALLY_CALIBRATED',
       'coordinate_system':{'handedness':'right','axes':'X forward, Y left, Z up','length':'mm','angles':'deg','quaternion':'xyzw','vectors':'column'},
       'root_transform_mm':T['pelvis'].tolist(),'root_measurement':'NOT_MEASURED',
       'raw_order':wiring['raw_order'],'raw_limits_deg':limits,'neutral_raw_deg':neutral,
       'joints':ordered,'fixed_markers':leaves,
       'range_scope':'Raw diagnostic bounds inherited from O15; NOT a certified collision-free Cartesian product.',
       'physical_collision_domain_certified':False,
       'capture_policy':{'stable_window_ms':500,'minimum_scans':6,'maximum_scan_gap_ms':120,
           'maximum_age_ms':120,'maximum_scan_skew_ms':60,'maximum_peak_to_peak_deg':0.5},
       'policy_status':'ENGINEERING_TARGETS_PENDING_REAL_SENSOR_VALIDATION',
       'required_physical_measurement_tests':['channel_identity','zero_sign_accuracy','bidirectional_repeatability',
           'loaded_deflection','whole_window_timing','fault_injection'],
       'target_policy':{'preserve_target_bone_lengths':True,'contact_correction':False,
           'root':'authored in UE','finger_pose':'fixed physical hand, edited in UE',
           'spine_neck_twist_helpers':'derived target bones, not independent measurements'},
       'source_geometry':{'revision':'O15','variant':'quinn','commit':'c0d3ec0d7c547c00ad75669ed502ea8cd642b117',
           'scope':'Deliberately retained geometry; only one physical SKU is offered in O16.'}}
    write(BENCH/'profiles/device_profile.json',p)
    cal={'schema':'POSEDOLL-O16-CALIBRATION/1','status':'INCOMPLETE','device_id':None,
       'profile_sha256':digest(p),'axes':{k:{'sensor_zero_deg':None,'sign':None,
       'reference_joint_deg':neutral[k],'evidence':None} for k in p['raw_order']},
       'physical_tests':{k:False for k in p['required_physical_measurement_tests']}}
    write(BENCH/'profiles/calibration_INCOMPLETE.json',cal)
    rows=[r for c in wiring['chains'] for r in c['nodes']]
    with (BENCH/'profiles/channels.csv').open('w',newline='',encoding='utf-8-sig') as f:
        w=csv.DictWriter(f,fieldnames=['raw_index','raw_id','chain','position_nearest_controller_zero_based','part','label']);w.writeheader();w.writerows(rows)
    wiring['schema']='POSEDOLL-O16-WIRING/1';wiring['hardware_model']='universal'
    wiring['source_evidence']='O15 raw46 wiring; same boards and chain positions; must verify actual wiring.'
    write(BENCH/'profiles/wiring.json',wiring)
    poses=read(H/'mechanical_manifest/revO_pose_cases.json')['cases']; fixtures=[]; errors=[]
    for name,angles in poses.items():
        _,_,st,fail,physical=source.build('quinn',angles,geometry=False)
        if fail: raise ValueError((name,fail))
        q={m['id']+'/r'+str(i):v for m in st for i,v in enumerate(m['angles_deg'])}
        actual=forward(p,q); expected,_=source.fk(physical,angles)
        err=max(float(np.max(np.abs(M-expected[k]))) for k,M in actual.items())
        errors.append(err); fixtures.append({'name':name,'raw_deg':q,
            'expected_frames_mm':{k:expected[k].tolist() for k in actual},'reference_agreement_max':err})
    # Legacy inverse trig at singular poses has sub-micrometre numerical error.
    # CAD regression tolerance: 1e-4 mm / matrix element, not a physical rating.
    if max(errors)>1e-4: raise ValueError(('physical FK mismatch',max(errors)))
    write(BENCH/'profiles/pose_fixtures.json',{'scope':'regression against retained CAD transforms, not independent physical validation','poses':fixtures})
    write(OUT/'kinematic_regression.json',{'status':'PASS','poses':len(fixtures),'body_frames_per_pose':len(actual),
        'maximum_matrix_element_error_mm_or_unitless':max(errors),'physical_tested':False,
        'independent_metrology':False,'rotation_output':'matrix and quaternion; no Euler inversion'})
    return p,pr


def single_bom():
    old=read(H/'bench/revO15/print_batch/manifest.json'); rows=[]
    for row in old['rows']:
        qty=row['quantity_by_character'].get('quinn',0)
        if not qty: continue
        r=copy.deepcopy(row);r['quantity_by_character']={'universal':qty}
        r['instances']=[{**i,'character':'universal'} for i in r['instances'] if i['character']=='quinn']
        r['stl']='print_batch/'+r['id']+'.stl'; rows.append(r)
    manifest={'status':'SINGLE_HARDWARE_CANDIDATE_NOT_MANUFACTURING_RELEASE','hardware_model':'universal',
       'units':'mm','rows':rows,'print_types':len(rows),'print_pieces':sum(r['quantity_by_character']['universal'] for r in rows),
       'physical_tested':False,'source_note':'O15 Quinn geometry retained byte for byte; one universal physical model.'}
    write(BENCH/'print_batch/manifest.json',manifest)
    proc=read(H/'bench/revO15/procurement.json'); entry=copy.deepcopy(next(x for x in proc['characters'] if x['character']=='quinn'))
    entry['character']='universal';write(BENCH/'procurement.json',{'status':'DESIGN_BOM_NOT_ORDER_RELEASE','characters':[entry]})
    harness=read(H/'bench/revO15/harness/cut_and_binding_plan.json'); harness['characters']=[copy.deepcopy(next(x for x in harness['characters'] if x['character']=='quinn'))]
    harness['characters'][0]['character']='universal';harness['hardware_model']='universal';write(BENCH/'harness/cut_and_binding_plan.json',harness)
    archive=H/'bench/revO15/PoseDoll_O15_Quinn_Prototype.zip'
    if sha(archive)!='83981bd77a43e3ca6ae00cf691d2a072229715fc54f09c2cc00b507f0e017b36': raise ValueError('source ZIP changed')
    keep={f"print_batch/{r['id']}.{ext}" for r in rows for ext in ('stl','3mf')}
    with zipfile.ZipFile(archive) as z:
        for name in z.namelist():
            if name not in keep and not name.startswith(('electronics/','firmware_source/')):continue
            target=(BENCH/name).resolve()
            if not target.is_relative_to(BENCH.resolve()):raise ValueError('unsafe archive path')
            target.parent.mkdir(parents=True,exist_ok=True); target.write_bytes(z.read(name))
        # Historic guide is explicitly segregated; none of its release claims apply to O16.
        for name in ('guide.html','style.css','PRINT_QUINN.zh-CN.md','PROCUREMENT_QUINN.zh-CN.md'):
            target=BENCH/'historical_o15'/name;target.parent.mkdir(exist_ok=True);target.write_bytes(z.read(name))
    for r in rows:
        if sha(BENCH/r['stl'])!=r['stl_sha256']:raise ValueError('printed geometry hash mismatch')
    write(OUT/'single_model_inventory.json',{'status':'PASS','hardware_models':['universal'],
        'print_types':len(rows),'print_pieces':manifest['print_pieces'],'raw_sensors':46,
        'source_zip_sha256':sha(archive),'geometry_modified':False,'quantity_multiplier':1})
    with (BENCH/'PRINT_UNIVERSAL.csv').open('w',newline='',encoding='utf-8-sig') as f:
        w=csv.writer(f);w.writerow(['print_id','quantity','supports_required','file','parts'])
        for r in rows:w.writerow([r['id'],r['quantity_by_character']['universal'],r['bed']['supports_required'],r['stl'],'; '.join(i['part'] for i in r['instances'])])
    return manifest


def viewer(p,pr):
    oldpage=H/'tutorials/full-doll-o15';data=read(oldpage/'scene_quinn.json')
    data['character']='universal';data['status']='O16 单一通用人偶 · 数字设计候选；连续避碰、实物标定与双角色 UE 验收待完成。'
    data.pop('reference_deviations',None);data['print_index']=[r for r in read(BENCH/'print_batch/manifest.json')['rows']]
    data['coverage']=['一套实体、46路实测，Manny / Quinn 仅作为软件目标。',
       '沿用 O15 Quinn 的已建模机械件；O16 没有重新设计这批打印几何。',
       '实体数字骨架包含实际偏移；目标角色保留自己的骨长。',
       '根部位移/整体旋转、手指未测；目标多段颈椎、脊柱辅助骨为派生姿态。',
       '不要求目标接触保持，不自动贴地、防穿模或美化。',
       '历史离散避碰检查不能证明整个允许工作域连续无干涉。']
    cases=read(H/'mechanical_manifest/revO_pose_cases.json')['cases']; raw=np.fromfile(oldpage/'geometry_quinn.bin',dtype='<f4').reshape(-1,6)
    bounds={}
    for scene in data['scenes']:
        pose={'upperarm_l.abduct':30,'upperarm_r.abduct':30,'thigh_l.abduct':8,'thigh_r.abduct':8} if scene['pose']=='assembly' else cases[scene['pose']]
        _,_,st,fail,_=source.build('quinn',pose,geometry=False)
        q={m['id']+'/r'+str(i):v for m in st for i,v in enumerate(m['angles_deg'])};T=forward(p,q)
        scene['reference_bones']=[{'a':T[j['parent']][:3,3].tolist(),'b':T[j['child']][:3,3].tolist()} for j in p['joints']]
        scene['caption']='实际机构与测量参考骨架。分解仅供认件；此姿势显示不代表全域避碰或实物验收通过。'
        lo=[];hi=[]
        for o in scene['objects']:
            m=data['meshes'][o['mesh']];v=raw[m['first']:m['first']+m['count'],:3];M=np.array(o['matrix']).reshape(4,4);world=v@M[:3,:3].T+M[:3,3]
            lo.append(world.min(0));hi.append(world.max(0))
        low=np.min(lo,0);high=np.max(hi,0)
        bounds[scene['pose']]={'min_mm':low.tolist(),'max_mm':high.tolist(),'size_mm':(high-low).tolist()}
    write(PAGE/'scene_universal.json',data);shutil.copy2(oldpage/'geometry_quinn.bin',PAGE/'geometry_universal.bin')
    shutil.copy2(oldpage/'style.css',PAGE/'style.css')
    app=(oldpage/'app.js').read_text(encoding='utf-8-sig')
    start="const $=s=>document.querySelector(s),char=new URLSearchParams(location.search).get('character')==='manny'?'manny':'quinn';$('#character').value=char;$('#character').onchange=e=>location.search='?character='+e.target.value;"
    assert start in app;app=app.replace(start,"const $=s=>document.querySelector(s),char='universal';")
    app=app.replace('revO15','revO16').replace("O15_VIEWER","O16_VIEWER").replace('O15_READY','O16_READY')
    app=app.replace("'../../bench/revO16/PoseDoll_O15_'+(char==='quinn'?'Quinn':'Manny')+'_Prototype.zip'","'../../bench/revO16/PoseDoll_O16_Universal_Design.zip'")
    app=app.replace("'下载 '+(char==='quinn'?'Quinn':'Manny')+' 统一测试包'","'下载 O16 单人偶设计包'")
    app=app.replace('（只打印当前体型）','（一套通用人偶，勿翻倍）')
    (PAGE/'app.js').write_text(app,encoding='utf-8')
    write(OUT/'dimensions.json',{'status':'PASS_MESH_HEIGHT','neutral_height_mm':bounds['neutral']['size_mm'][2],
        'maximum_height_mm':600,'source':'final retained mesh, including rigid equipment and tails',
        'mesh_simplification_mm':0.03,'includes_desktop_base':False,'physical_measured':False,'poses':bounds})
    return bounds


def main():
    OUT.mkdir(parents=True,exist_ok=True);BENCH.mkdir(parents=True,exist_ok=True);PAGE.mkdir(parents=True,exist_ok=True)
    p,pr=profile(); m=single_bom(); b=viewer(p,pr)
    write(BENCH/'requirements.json',{'revision':'O16','hardware_quantity':1,'hardware_model':'universal',
        'height_max_mm':600,'measurement':'static supported physical joints','target_characters':['Manny','Quinn'],
        'target_geometry_coincidence_required':False,'automatic_contact_correction':False,
        'adjacent_physical_interference_allowed':False,'root_measurement':False,'finger_measurement':False,
        'collision_release':'NOT_VERIFIED','physical_tests':'NOT_RUN','new_UE_end_to_end_tests':'NOT_RUN'})
    print(json.dumps({'hardware_models':1,'raw_sensors':len(p['raw_order']),'physical_modules':len(p['joints']),
        'height_mm':b['neutral']['size_mm'][2],'print_types':m['print_types'],'print_pieces':m['print_pieces']},indent=2))

if __name__=='__main__':main()
