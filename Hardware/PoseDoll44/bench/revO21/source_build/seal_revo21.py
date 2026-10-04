"""Seal O21 engineering design, never a manufacturing release."""
from build_revo21 import *
import zipfile,xml.etree.ElementTree as ET
def main():
    V=B/'verification';V.mkdir(exist_ok=True)
    assert read(B/'electronics/sensor/result.json')['checks']['drc']['pass']
    assert read(B/'electronics/carrier/result.json')['checks']['erc']['pass']
    assert read(V/'host_tests.json')['status']=='PASS'
    assert read(V/'device_tests.json')['status']=='PASS'
    assert read(V/'firmware_build.json')['status']=='PASS'
    sys_path=B/'source'
    # Power-domain topology: all 46 ports and the mux/control buffers share post-fuse supply.
    netroot=ET.parse(B/'electronics/carrier/netlist.xml')
    netmap={(x.attrib['ref'],x.attrib['pin']):n.attrib['name'].lstrip('/') for n in netroot.findall('./nets/net') for x in n.findall('node')}
    sensor_connectors=[str(10+j*16+i) for j,count in enumerate([14,16,16]) for i in range(count)]
    assert all(netmap[('J'+j,'2')]=='SENSOR_3V3' for j in sensor_connectors)
    assert all(netmap[(u,p)]=='SENSOR_3V3' for u,p in [('U1','20'),('U2','20'),('U3','24'),('U4','24'),('U5','24')])
    assert netmap['F5','1']=='REG_3V3' and netmap['F5','2']=='SENSOR_3V3'
    assert netmap['U6','14']=='MCU_3V3'
    usb5=[n for n in netroot.findall('./nets/net') if any(x.attrib['ref']=='J2' and x.attrib['pin']=='7' for x in n.findall('node'))]
    assert len(usb5)==1 and len(usb5[0].findall('node'))==1 and 'no_connect' in usb5[0].find('node').attrib['pintype']
    vmin=.588*(1+300000*.99/(66500*1.01));vmax=.612*(1+300000*1.01/(66500*.99))
    put(V/'power_and_netlist_review.json',{'status':'SCHEMATIC_TOPOLOGY_CHECKED_PHYSICAL_TEST_PENDING','post_fuse_ports':46,
        'independent_MCU_and_sensor_rails':True,'all_sensor_domain_logic_after_common_fuse':True,'sensor_max_current_A':46*.014,
        'analysis_load_allowance_A':.7,'nominal_regulator_V':.6*(1+300000/66500),
        'regulator_feedback_and_resistor_tolerance_min_max_V':[vmin,vmax],
        'estimated_min_remote_V':vmin-.7*.15-.014*(2*.6*.5+.08),
        'assumptions':'FB +/-2%, resistors +/-1%; 1A output fuse R<=0.15 ohm; 30AWG hot loop 0.5 ohm/m per conductor; 0.6m one-way; connector loop 0.08 ohm; no transient allowance quantified.',
        'scope':'Calculation only. Fuse exact MPN, all-power sequencing, short circuit, thermal rise and rail/SSI waveforms remain unmeasured.'})
    put(V/'browser_review.json',{'status':'PASS','desktop_viewport':[1440,1000],'mobile_viewport':[390,844],
        'mobile_horizontal_overflow':False,'broken_images':0,'console_errors':0,
        'budget_default':1482.5,'budget_sensor_changed_to_400_total':1520,'stress_total':2210,'reset_total':1482.5,
        'slot15':['unused A','hand_r.deviate/r0','ball_r.flex/r0'],'review':'Desktop/mobile screenshots inspected; budget and slot interactions exercised in Playwright.'})
    for name in ['desktop.png','mobile.png']:shutil.copy2(R/'output/playwright/o21'/name,V/name)
    status=read(B/'DESIGN_STATUS.json')
    status.update(sensor_erc_passed=True,sensor_drc_passed=True,carrier_schematic_erc_passed=True,carrier_pcb_routed=False,
                  firmware_build_passed=True,host_tests=8,inherited_FK_capture_tests=15,supplier_quotes_obtained=0)
    put(B/'DESIGN_STATUS.json',status)
    baseline=read(B/'mechanical_baseline.json')
    assert baseline['archive_sha256']=='a0cacf9862b59901e20141fb67495208716f221997a61c9599f63fdc2f3635a2'
    # O20 byte-for-byte preserved.
    manifest=read(OLD/'FILES_SHA256.json')
    for name,dig in manifest['files'].items():assert sha(OLD/name)==dig,('O20 modified',name)
    put(V/'o20_preserved.json',{'status':'PASS','files_checked':len(manifest['files']),'archive_sha256':sha(OLD/'PoseDoll_O20_Universal_Design.zip')})
    provenance=B/'source_build';provenance.mkdir(exist_ok=True)
    for p in R.glob('scripts/*revo21*.py'):shutil.copy2(p,provenance/p.name)
    shutil.copy2(R/'scripts/Run-RevO21-CodecTests.cmd',provenance/'Run-RevO21-CodecTests.cmd')
    put(B/'source_lock.json',{'O20_commit':'900f572','O20_archive_sha256':baseline['archive_sha256'],
         'generator_and_doc_sha256':{str(p.relative_to(R)).replace('\\','/'):sha(p) for p in [*R.glob('scripts/*revo21*.py'),H/'docs/DESIGN_REVO21.zh-CN.md']},
         'repository_inputs_required_for_regeneration':['Hardware/PoseDoll44/tools/build_regional_revM.py','Hardware/PoseDoll44/tools/build_sensor_revC_mini.py','scripts/route_revo5cn_sensor.py','Hardware/PoseDoll44/bench/revO20'],
         'tools':'KiCad 10.0.6; Python/numpy; ESP-IDF 6.1; MSVC C11; Playwright CLI',
         'rebuild_scope':'Native board files, firmware and host sources are included. Generator scripts depend on the complete repository and pinned historical inputs.'})
    excluded={'FILES_SHA256.json','PoseDoll_O21_CostDown_Design.zip','local_test_result.json','placement.kicad_pcb','placement.kicad_pro'}
    files={str(p.relative_to(B)).replace('\\','/'):sha(p) for p in B.rglob('*') if p.is_file() and p.name not in excluded and '__pycache__' not in p.parts}
    put(B/'FILES_SHA256.json',{'schema':'POSEDOLL-O21-FILES/1','files':files})
    archive=B/'PoseDoll_O21_CostDown_Design.zip'
    with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
        for name in sorted([*files,'FILES_SHA256.json']):z.write(B/name,name)
    with zipfile.ZipFile(archive) as z:
        assert z.testzip() is None
        for name,dig in files.items():assert hashlib.sha256(z.read(name)).hexdigest()==dig,name
    out=H/'generated/revO21';out.mkdir(parents=True,exist_ok=True)
    put(out/'package_verification.json',{'status':'PASS','files':len(files),'zip_bytes':archive.stat().st_size,'zip_sha256':sha(archive),'manufacturing_release':False})
    print(json.dumps({'files':len(files),'bytes':archive.stat().st_size,'zip_sha256':sha(archive)},indent=2))
if __name__=='__main__':main()
