"""Seal the independent supplier trial and check preserved O5/UE working inputs."""
from pathlib import Path
import argparse,hashlib,json,subprocess,sys,zipfile
R=Path(__file__).resolve().parents[1];H=R/'Hardware/PoseDoll44';RUN=H/'verification/revO5CN/runs/cn_20260924_r1';OUT=H/'verification/revO5CN/delivery';UE=Path('E:/UnrealProjects/DollSimulation')
def digest(data):return hashlib.sha256(data).hexdigest()
def sha(p):return digest(p.read_bytes())
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def save(p,d):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def verify():
 m=read(OUT/'DELIVERY_MANIFEST.json');errors=[];count=0
 for name,h in m['files_sha256'].items():
  p=R/name;count+=1
  if not p.is_file() or sha(p)!=h:errors.append(name)
 zpath=R/m['archive']
 if not zpath.is_file() or sha(zpath)!=m['archive_sha256']:errors.append(m['archive'])
 else:
  with zipfile.ZipFile(zpath) as z:
   if set(z.namelist())!=set(m['members_sha256']):errors.append('archive member set')
   for n,h in m['members_sha256'].items():
    count+=1
    if digest(z.read(n))!=h:errors.append('archive:'+n)
 print(json.dumps({'verified':not errors,'checked_hashes':count,'errors':errors,'physical_tested':False,'manufacturing_released':False}))
 return 1 if errors else 0

def main():
 a=argparse.ArgumentParser();a.add_argument('--verify',action='store_true');opt=a.parse_args()
 if opt.verify:return verify()
 assert not (OUT/'DELIVERY_MANIFEST.json').exists(),'Seal exists; use another run/delivery rather than overwrite.'
 old=subprocess.run([sys.executable,'scripts/seal_revo5.py','--verify'],cwd=R,capture_output=True);assert old.returncode==0,old.stdout
 old_result=json.loads(old.stdout);assert old_result['verified']
 lock=read(H/'verification/revO5/deliveries/o5_20260924_d1/FINAL_SOURCE_LOCK.json');ue_hashes={**lock['ue'],**lock['user_uncommitted_preserved']}
 for name,h in ue_hashes.items():assert sha(UE/name)==h,name
 # Compile and execute while the exact C sources are hashed on both sides.
 build=R/'.local/cn_20260924_codec_final';cfiles=[*sorted((R/'Firmware/PoseDollFullBody/revO5CN').glob('*.[ch]')),R/'scripts/Run-RevO5CN-CodecTests.cmd'];ch={p.relative_to(R).as_posix():sha(p) for p in cfiles}
 cmd=['cmd.exe','/d','/c','scripts\\Run-RevO5CN-CodecTests.cmd',str(build)]
 proc=subprocess.run(cmd,cwd=R,capture_output=True);(RUN/'codec_test.txt').write_bytes(proc.stdout+proc.stderr);assert proc.returncode==0 and b'PASS:' in proc.stdout
 for n,h in ch.items():assert sha(R/n)==h,n
 save(RUN/'codec_test.json',{'exit_code':proc.returncode,'compiler_flags':'/std:c11 /W4 /WX /O2 (assertions enabled)','command':cmd,'input_sha256':ch,'executable_sha256':sha(build/'mt6701_trial_test.exe'),'payload_combinations':262144,'single_bit_mutations':393216,'CRC_hypothesis_only':True,'capture_eligible':False,'physical_tested':False})
 pcb=read(H/'electronics/sensor_revO5CN/result.json');native=read(RUN/'native_board_check.json');cad=read(H/'generated/revO5CN/runs/cn_20260924_r1/cad_screen.json');analysis=read(RUN/'supplier_analysis.json')
 assert all(v['pass'] for v in pcb['checks'].values()) and pcb['routing_complete']
 assert native['via_in_pad_count']==0 and native['minimum_via_copper_to_SMD_land_mm']>=.2-1e-6
 assert not cad['adjusted_component_envelope_intersections'] and cad['spring_direct_swap']['status']=='REJECT'
 inputs={}
 for d in (pcb,native,cad,analysis,read(RUN/'codec_test.json')):
  for field in ('input_sha256','source_sha256'):
   for name,h in d.get(field,{}).items():
    path=Path(name) if Path(name).is_absolute() else R/name
    assert sha(path)==h,name;inputs[path]=h
 version=subprocess.check_output(['D:/ProgramFiles/KiCad/10.0/bin/kicad-cli.exe','version']).decode().strip()
 results={'schema':'cn1-digital-delivery-v1','date':'2026-09-24','supplier_records':11,'production_replacements':0,'trial_sensor_board':'MT6701QT-STD + complete CJT five-pin pair','five_wire_conductor_segments_saved_if_all_41_ports_converted':41,'erc_drc_schematic_parity':pcb['checks'],'via_in_pad_count':0,'CRC_math_tests':read(RUN/'codec_test.json'),'local_mechanical_screen':cad['status'],'spring_direct_swap':'REJECTED_CAD_INTERFERENCE','O5_preserved':old_result,'UE_preserved_files':len(ue_hashes),'user_configuration_preserved':True,'toolchain':{'KiCad':version,'CadQuery':'2.7 via project adapter','host_C':'MSVC C11'},'physical_tested':False,'manufacturing_released':False,'commit_or_push_performed':False,'open':['MT6701 EP and CRC/clock manufacturer clarification','Actual accuracy/poweroff/cable behavior','Actual prices, stock, MOQ and leadtime','Full matched plug and harness path','PCB/spring/tooling supplier DFM and lifetime','Previous O5 shoulder/RF and manufacturing gates remain'], 'known_resolved_digital_attempts':['pcbnew LSET construction API corrected','Project rules reapplied after pcbnew SaveBoard overwrote its cached project','Vias moved off all SMD lands after visual inspection','Guide identified as integral part of keyed_pressure_plate','KiCad via width queried with explicit copper layer']}
 save(RUN/'results.json',results)
 # Include new editable sources, native outputs and all project inputs actually read.
 bases=[H/'references/revO5CN',H/'electronics/sensor_revO5CN',H/'cad/revO5CN',H/'generated/revO5CN',RUN,R/'Firmware/PoseDollFullBody/revO5CN']
 files={p for base in bases for p in base.rglob('*') if p.is_file() and '__pycache__' not in p.parts and p.suffix not in ('.pyc','.kicad_prl','.lck')}
 files.update([H/'mechanical_manifest/requirements_revO5CN.json',H/'docs/CN_SUPPLIERS_AND_DESIGN.zh-CN.md',Path(__file__)])
 files.update((R/'scripts').glob('*revo5cn*.py'));files.add(R/'scripts/Run-RevO5CN-CodecTests.cmd')
 files.update(p for p in inputs if p.is_relative_to(R))
 OUT.mkdir(parents=True,exist_ok=True);zpath=OUT/'cn1_native_and_inputs.zip';members={}
 with zipfile.ZipFile(zpath,'x',zipfile.ZIP_DEFLATED,compresslevel=9) as z:
  for p in sorted(files):
   name=p.relative_to(R).as_posix();data=p.read_bytes();z.writestr(name,data);members[name]=digest(data)
  for p in sorted(set(inputs)-files):
   if p.is_relative_to(R):continue
   name='external_kicad_inputs/'+p.relative_to(Path('D:/ProgramFiles/KiCad/10.0')).as_posix();data=p.read_bytes();z.writestr(name,data);members[name]=digest(data)
 for p,h in inputs.items():assert sha(p)==h,p
 for name,h in ue_hashes.items():assert sha(UE/name)==h,name
 for n,h in read(H/'verification/revO5/deliveries/o5_20260924_d1/DELIVERY_MANIFEST.json')['files_sha256'].items():assert sha(R/n)==h,n
 save(OUT/'DELIVERY_MANIFEST.json',{'schema':'cn1-sealed-delivery-v1','files_sha256':{p.relative_to(R).as_posix():sha(p) for p in sorted(files)},'archive':zpath.relative_to(R).as_posix(),'archive_sha256':sha(zpath),'members_sha256':members,'physical_tested':False,'manufacturing_released':False})
 return verify()
if __name__=='__main__':raise SystemExit(main())
