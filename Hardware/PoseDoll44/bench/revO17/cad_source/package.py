"""Seal the O17 review package, preserving the O16 snapshot byte-for-byte."""
from pathlib import Path
import csv,io,json,shutil,hashlib,zipfile,subprocess,sys
from geometry import H,OUT,BENCH,read,write,sha
REPO=H.parents[1];PAGE=H/'tutorials/full-doll-o17';FW=REPO/'Firmware/PoseDollFullBody/revO17'

def main():
    geom=read(OUT/'geometry_verification.json');assert not geom['new_collisions']
    assert len(geom['poses'])==24
    manifest=read(BENCH/'print_batch/manifest.json');assert manifest['print_pieces']==202 and manifest['print_types']==124
    assert read(OUT/'device_tests.json')['status']=='PASS'
    # Re-run only package-relevant host tests when producing a seal; retain logs.
    for name in ['test_usb.py']:
        proc=subprocess.run([sys.executable,str(H/'cad/revO17'/name)],cwd=REPO,capture_output=True,text=True,encoding='utf-8',errors='replace')
        (OUT/(name+'.log')).write_text(proc.stdout+proc.stderr,encoding='utf-8');assert proc.returncode==0,proc.stdout+proc.stderr
    native=(OUT/'native_tests.log').read_text(encoding='utf-8-sig',errors='replace');assert 'P17 native PASS' in native and 'P17 session PASS' in native
    log=(OUT/'firmware_build.log').read_text(encoding='utf-8-sig',errors='replace');assert 'Project build complete.' in log and 'error:' not in log
    shutil.copy2(H/'docs/DESIGN_REVO17.zh-CN.md',BENCH/'DESIGN.zh-CN.md')
    for name in ('device.py','test_device.py','usb_capture.py','test_usb.py','verify_package.py'):
        dst=BENCH/'source'/name;dst.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(H/'cad/revO17'/name,dst)
    shutil.copy2(OUT/'codec_fixture.bin',BENCH/'source/codec_fixture.bin')
    for name in ('geometry.py','export.py','verify_geometry.py','print_io17.py','package.py','verify_package.py','test_native.cmd'):
        dst=BENCH/'cad_source'/name;dst.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(H/'cad/revO17'/name,dst)
    shutil.copytree(FW,BENCH/'firmware_source',dirs_exist_ok=True,ignore=shutil.ignore_patterns('__pycache__'))
    binaries=OUT/'firmware_build/USB'
    for source,rel in [(binaries/'posedoll_o17_usb_raw46.bin','app.bin'),(binaries/'bootloader/bootloader.bin','bootloader.bin'),(binaries/'partition_table/partition-table.bin','partition-table.bin')]:
        dst=BENCH/'firmware_binaries'/rel;dst.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(source,dst)
    fwreport={'status':'COMPILED_AND_NATIVE_TESTS_PASSED','platform':'ESP-IDF v6.1 / ESP32-S3','transport':'USB Serial/JTAG, P17R/1','radio_started':False,'hardware_flashed':False,'physical_tested':False,
        'packet_bit_flips':1536,'packet_truncations':192,'sensor_response_bit_flips':4400,'sensor_chain_lengths_tested':10,
        'session_tests':['identity and reboot','fresh scans','idempotent ACK','retired capture replay','cancel and stale cancel','faulty axis','clock rollback','capture timeout','token overflow','forged completion','capture capacity'],
        'source_sha256':{str(p.relative_to(FW)).replace('\\','/'):sha(p) for p in FW.rglob('*') if p.is_file()},
        'binary_sha256':{p.name:sha(p) for p in (BENCH/'firmware_binaries').iterdir()},'build_log_sha256':sha(OUT/'firmware_build.log')}
    write(OUT/'firmware_verification.json',fwreport)
    write(OUT/'usb_tests.json',{'status':'PASS','tests':6,'C_compiler_fixture_checked':True,'sensor_to_35_frames_synthetic_regression':True,'physical_tested':False,'runner_sha256':sha(H/'cad/revO17/test_usb.py')})
    # Same bare-board artwork; revised assembly, not a new copper claim.
    shutil.copytree(H/'bench/revO16/electronics',BENCH/'electronics',dirs_exist_ok=True)
    central=BENCH/'electronics/central_c1';bom=read(central/'BOM.json');bom=[r for r in bom if r['references']!=['D1']];write(central/'BOM.json',bom)
    text=(central/'placement.csv').read_text(encoding='utf-8-sig');reader=csv.DictReader(io.StringIO(text));fields=reader.fieldnames;rows=[r for r in reader if r['Ref']!='D1']
    with (central/'placement.csv').open('w',newline='',encoding='utf-8-sig') as f:w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(rows)
    (central/'ORDER_NOTES.zh-CN.md').write_text('# C1-U 装配变体\n\nO17使用原C1裸板铜层，但D1不装。BOM与坐标表已删除D1。原ERC/DRC仅属于裸板历史证据，不构成双电源上电验收。\n\nUSB只供主控；J7独立5V只供传感器降压电路；正电源分开、GND共地。旧板先拆D1，禁止一边保留D1一边同时接电脑和外部5V。详细接线及检查见根目录POWER_AND_USB.zh-CN.md。\n\n不得写传感器OTP。只做小样，待实物上电、反灌、温升、压降和通信测试通过再决定批量。\n',encoding='utf-8')
    write(central/'assembly_variant.json',{'variant':'C1-U','same_copper_as':'O15 C1','DNP':['D1'],'sources':'local build_controller.py and original connectivity','electrical_power_tested':False})
    selected=['changes.json','bom_comparison.json','print_grouping.json','geometry_verification.json','viewer_geometry.json','device_tests.json','usb_tests.json','firmware_verification.json','browser_review.json']
    for name in selected:
        dst=BENCH/'verification'/name;dst.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(OUT/name,dst)
    for p in (REPO/'output/playwright/o17').glob('*.png'):shutil.copy2(p,BENCH/'verification'/p.name)
    for p in PAGE.iterdir():
        if not p.is_file():continue
        dst=BENCH/'viewer'/p.name;dst.parent.mkdir(parents=True,exist_ok=True)
        if p.suffix in ('.html','.js'):
            text=p.read_text(encoding='utf-8-sig').replace('../../bench/revO17/','../').replace('../../docs/DESIGN_REVO17.zh-CN.md','../DESIGN.zh-CN.md')
            text=text.replace('../PoseDoll_O17_Universal_Design.zip','../README.zh-CN.md').replace('下载 O17 单人偶设计包','阅读本地设计包说明')
            dst.write_text(text,encoding='utf-8')
        else:shutil.copy2(p,dst)
    write(BENCH/'FIRST_PRINT.json',{'status':'COUPONS_BEFORE_FULL_DOLL','parts':[{'id':k,'quantity':1} for k in ['N001','N002','N003','N004']],
        'material':'PETG prototype; qualify actual printer, orientation and adhesive','full_doll_print_release':False,
        'checks':['PCB position and latch release','FFC service','bonded magnet angular retention','M2 cartridge retention and M3 service access','independent angle accuracy and repeatability']})
    (BENCH/'requirements-reference.txt').write_text('numpy\npyserial\n',encoding='utf-8')
    (BENCH/'README.zh-CN.md').write_text('# O17 简化小样候选\n\nO16已保存为26255df / posedoll-o16-saved-20260930。O17为一台人偶，202件/124种打印件，46路测量、41个语义旋转自由度，USB直连，无摄像头。\n\n先读DESIGN.zh-CN.md和POWER_AND_USB.zh-CN.md。原有整机干涉仍存在；禁止把增量回归通过当作整机无干涉或制造放行。先做FIRST_PRINT.json中的四件小样。\n\n- print_batch与PRINT_UNIVERSAL.csv：净数量，STL/3MF二选一。\n- electronics：C1-U装配，D1不装；裸板铜层沿用。\n- source：离线FK、故障检查、USB参考工具；需实测标定。\n- firmware_source与firmware_binaries：USB固件源代码及编译产物，未刷入实物。P17R与旧P15R不兼容。\n- verification：实际检查结果与截图，含已有干涉配对。\n- cad_source：复建源代码；依赖原设计仓库冻结输入。\n\n用Python运行serve_preview.py，再打开http://127.0.0.1:8771/viewer/index.html。命令行可运行python source/test_device.py与python source/test_usb.py；这些离线测试不会连接或刷写硬件。运行python source/verify_package.py可核验全部文件及原ZIP的SHA-256。\n',encoding='utf-8')
    (BENCH/'serve_preview.py').write_text('from pathlib import Path\nfrom functools import partial\nfrom http.server import ThreadingHTTPServer,SimpleHTTPRequestHandler\nroot=Path(__file__).resolve().parent\nprint("http://127.0.0.1:8771/viewer/index.html",flush=True)\nThreadingHTTPServer(("127.0.0.1",8771),partial(SimpleHTTPRequestHandler,directory=str(root))).serve_forever()\n',encoding='utf-8')
    status={'revision':'O17','status':'SIMPLIFICATION_PROTOTYPE_KNOWN_INHERITED_COLLISIONS','O16_snapshot':'26255df / posedoll-o16-saved-20260930',
        'print_pieces':202,'print_types':124,'raw_channels':46,'semantic_dof':41,'height_mm':geom['neutral_exact_geometry']['height_mm'],
        'USB_firmware_compiled':True,'new_part_collision_regression_passed':True,'inherited_overlap_cases':geom['inherited_overlap_cases'],
        'continuous_collision_proof':False,'physical_tested':False,'ue_end_to_end_tested':False,'manufacturing_release':False}
    write(BENCH/'DESIGN_STATUS.json',status)
    sources=[*HERE.glob('*.py'),*HERE.glob('*.cmd'),*[p for p in FW.rglob('*') if p.is_file()],H/'docs/DESIGN_REVO17.zh-CN.md']
    write(BENCH/'source_lock.json',{'O16_commit':'26255df','O16_archive_sha256':sha(H/'bench/revO16/PoseDoll_O16_Universal_Design.zip'),
        'source_sha256':{str(p.relative_to(REPO)).replace('\\','/'):sha(p) for p in sources},'note':'CAD also reads frozen O15 inputs from the O16 git snapshot; original source locks are preserved there.'})
    files={str(p.relative_to(BENCH)).replace('\\','/'):sha(p) for p in BENCH.rglob('*') if p.is_file() and p.name not in ('FILES_SHA256.json','PoseDoll_O17_Universal_Design.zip','local_test_result.json') and '__pycache__' not in p.parts}
    write(BENCH/'FILES_SHA256.json',{'schema':'POSEDOLL-O17-FILES/1','files':files})
    archive=BENCH/'PoseDoll_O17_Universal_Design.zip'
    with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
        for name in sorted([*files,'FILES_SHA256.json']):z.write(BENCH/name,name)
    with zipfile.ZipFile(archive) as z:
        assert z.testzip() is None and set(z.namelist())==set(files)|{'FILES_SHA256.json'}
        for name,digest in files.items():assert hashlib.sha256(z.read(name)).hexdigest()==digest,name
    write(OUT/'package_verification.json',{'status':'PASS','files_checked':len(files),'zip_sha256':sha(archive),'zip_bytes':archive.stat().st_size,'physical_qualification':False})
    print('O17 sealed',len(files),'files',round(archive.stat().st_size/1024/1024,2),'MiB',sha(archive))
HERE=Path(__file__).resolve().parent
if __name__=='__main__':main()
