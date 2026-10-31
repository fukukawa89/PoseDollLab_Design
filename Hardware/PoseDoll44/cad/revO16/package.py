"""Assemble O16's portable review archive; keep old artifacts unchanged."""
from pathlib import Path
import shutil,json,hashlib,sys,zipfile
HERE=Path(__file__).resolve().parent;H=HERE.parents[1];ROOT=H.parents[1]
B=H/'bench/revO16';G=H/'generated/revO16';V=H/'tutorials/full-doll-o16'
sys.path.insert(0,str(HERE))
from device import digest,capture_window
from verify_package import verify

def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def write(p,d):
    p=Path(p);p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(d,ensure_ascii=False,indent=2,allow_nan=False)+'\n',encoding='utf-8')
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()

def main():
    p=read(B/'profiles/device_profile.json')
    tests=read(G/'device_tests.json')
    assert tests['status']=='PASS' and tests['profile_sha256']==digest(p)
    assert tests['runtime_sha256']==sha(HERE/'device.py')
    targets=[]
    for name in ('manny','quinn'):
        probe=H/f'reference/ue58/{name}_mesh_probe.json';d=read(probe)
        targets.append({'target':name,'device_profile_id':p['profile_id'],
            'mesh':d['mesh_asset'],'rig_class':d['rig_class'],'skeleton':d['skeleton_asset'],
            'source':str(probe.relative_to(ROOT)).replace('\\','/'),'source_sha256':sha(probe),
            'legacy_manny_profile':'Shared/Profiles/manny_body_ue582_v1.json' if name=='manny' else None,
            'o16_live_adapter_implemented':False,'o16_capture_save_reopen_test':'NOT_RUN',
            'preserve_target_reference_translations':True,'contact_correction':False,
            'root_and_fingers':'AUTHORED_IN_UE','spine_neck_twist_helpers':'DERIVED_NOT_MEASURED'})
    write(B/'target_adapter_contract.json',{'schema':'POSEDOLL-O16-TARGET-CONTRACT/1',
        'status':'DESIGN_CONTRACT_NOT_PRODUCTION_TARGET_PROFILE','targets':targets,
        'conversion_failure_policy':'preserve valid raw capture; reject/mark target application separately; never clip or fill zero'})
    c={'schema':'POSEDOLL-O16-CALIBRATION/1','status':'SYNTHETIC','device_id':'synthetic-only',
        'profile_sha256':digest(p),'axes':{k:{'sensor_zero_deg':180.,'sign':1,
        'reference_joint_deg':q,'evidence':'generated fixture, NOT measured'} for k,q in p['neutral_raw_deg'].items()},
        'physical_tests':{k:False for k in p['required_physical_measurement_tests']}}
    scans=[{'device_id':'synthetic-only','boot_id':'synthetic-boot','capture_id':1,'sequence':i,
        'time_ms':1000.+i*100,'integrity':'valid','channels':{k:{'sensor_deg':180.,
        'time_ms':990.+i*100,'status':'valid'} for k in p['raw_order']}} for i in range(6)]
    result=capture_window(p,c,scans,expected_capture_id=1,evaluation_time_ms=1510.)
    assert result['status']=='VALID_MEASUREMENT' and not result['hardware_capture_eligible']
    write(B/'profiles/measurement_SYNTHETIC.json',result)
    shutil.copy2(H/'docs/DESIGN_REVO16.zh-CN.md',B/'DESIGN.zh-CN.md')
    (B/'source').mkdir(exist_ok=True);(B/'viewer').mkdir(exist_ok=True);(B/'verification').mkdir(exist_ok=True)
    for f in ('device.py','test_device.py','verify_package.py'):shutil.copy2(HERE/f,B/'source'/f)
    for f in V.iterdir():
        if not f.is_file():continue
        if f.suffix in ('.html','.js'):
            text=f.read_text(encoding='utf-8-sig').replace('../../bench/revO16/','../').replace('../../docs/DESIGN_REVO16.zh-CN.md','../DESIGN.zh-CN.md')
            (B/'viewer'/f.name).write_text(text,encoding='utf-8')
        else:shutil.copy2(f,B/'viewer'/f.name)
    for f in G.glob('*.json'):
        if f.name not in ('package_verification.json',):shutil.copy2(f,B/'verification'/f.name)
    # Screenshots are taken from actual browser views, never generated artwork.
    for f in (ROOT/'output/playwright/o16').glob('*.png'):shutil.copy2(f,B/'verification'/f.name)
    inputs=[*HERE.glob('*.py'),H/'docs/DESIGN_REVO16.zh-CN.md',
        H/'generated/revO15/runs/o15_20260929_r1/FINAL_BATCH_SUMMARY.json',
        H/'generated/revO15/runs/o15_20260929_r1/raw46_mapping_candidate.json',
        H/'generated/revO15/runs/o15_20260929_r1/raw46_wiring_candidate.json',
        H/'bench/revO15/PoseDoll_O15_Quinn_Prototype.zip',
        *list((H/'cad/revO15').glob('*.py'))]
    write(B/'source_lock.json',{'base_commit':'c0d3ec0d7c547c00ad75669ed502ea8cd642b117',
        'geometry_policy':'O15 Quinn geometry retained without modification; single universal SKU',
        'files':{str(f.relative_to(ROOT)).replace('\\','/'):sha(f) for f in inputs}})
    report={'revision':'O16','status':'DIGITAL_DESIGN_CANDIDATE','hardware_models':['universal'],
        'height_mm':read(G/'exact_geometry_check.json')['height_mm'],'height_limit_mm':600,
        'raw_sensors':46,'physical_modules':25,'print_types':214,'print_pieces':273,
        'geometry_modified':False,'offline_measurement_tests':read(G/'device_tests.json'),
        'cad_regression':read(G/'kinematic_regression.json'),
        'continuous_collision_proof':False,'physical_tests':'NOT_RUN','o16_UE_tests':'NOT_RUN',
        'automatic_contact_correction':False,'manufacturing_released':False}
    write(B/'DESIGN_STATUS.json',report)
    (B/'README.zh-CN.md').write_text('''# PoseDoll O16 Universal\n\n一个实体型号，46路原始测量，25个模块，数字中立高度492.14 mm。\n\n先读 DESIGN.zh-CN.md 与 DESIGN_STATUS.json。本包是数字设计候选，不是整机制造放行。连续全域避碰、带线实测、标定、保持力及O16的Manny/Quinn端到端UE验证尚未通过。\n\n本轮保留O15 Quinn机械几何，取消第二体型；新建目标无关的实际机械模型与采集参考实现。不是重新优化后的另一套关节STL。完整打印数量见 PRINT_UNIVERSAL.csv：214种、273件；同一编号的STL/3MF不要重复打印。\n\n查看三维：解压后在本目录运行 `python -m http.server 8771 --bind 127.0.0.1`，打开 http://127.0.0.1:8771/viewer/index.html 。页面不依赖互联网库。\n\n完整性检查：`python source/verify_package.py`，仅用标准库。\n测量参考测试：安装独立环境的NumPy后运行 `python source/test_device.py`。\n\nprofiles/calibration_INCOMPLETE.json必须保持未标定状态，直到填写真实证据；measurement_SYNTHETIC.json只是格式示例。source/device.py是离线参考，未接入生产串口或UE。target_adapter_contract.json是适配任务契约，不是已完成的角色配置。\n\nhistorical_o15/仅提供原装配/采购工艺参考；原文中的Quinn指本版几何来源，不代表还需要第二台人偶。电子和固件使用原型号名称以保持可追溯。默认固件未绑定真实MAC，不直接作为已配对硬件。\n\n原工作区可用 cad/revO16/build.py 复建配置、清单与查看器，用package.py重建本包；完整机械重建仍需要工作区内的历史CAD依赖。\n''',encoding='utf-8')
    (B/'requirements-reference.txt').write_text('numpy==2.5.3\n',encoding='utf-8')
    archive=B/'PoseDoll_O16_Universal_Design.zip'
    files=sorted(f for f in B.rglob('*') if f.is_file() and f not in (archive,B/'FILES_SHA256.json') and '__pycache__' not in f.parts and f.name!='local_test_result.json')
    write(B/'FILES_SHA256.json',{'schema':'POSEDOLL-PACKAGE-HASHES/1','files':{f.relative_to(B).as_posix():sha(f) for f in files}})
    with zipfile.ZipFile(archive,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=5) as z:
        for f in [*files,B/'FILES_SHA256.json']:z.write(f,f.relative_to(B).as_posix())
    checked=verify(B);write(G/'package_verification.json',checked)
    print(json.dumps(checked,indent=2))
    print('ZIP',archive,'MB',round(archive.stat().st_size/1e6,2))

if __name__=='__main__':main()
