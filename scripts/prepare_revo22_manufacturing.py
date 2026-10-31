"""Quote/first-article package. File completion is not hardware qualification."""
from pathlib import Path
import json,subprocess,hashlib,csv,collections,shutil
import pcbnew as pcb
R=Path(__file__).resolve().parents[1];B=R/'Hardware/PoseDoll44/bench/revO22';D=B/'manufacturing';D.mkdir(exist_ok=True)
CLI='D:/ProgramFiles/KiCad/10.0/bin/kicad-cli.exe'
rows=[];boards=[]
for kind,name,units in [('sensor','PoseDoll_O22_MT6701CT',48),('carrier','PoseDoll_O22_SSI_Carrier',1)]:
 folder=B/'electronics'/kind;out=D/kind;out.mkdir(exist_ok=True);path=folder/(name+'.kicad_pcb');board=pcb.LoadBoard(str(path))
 subprocess.run([CLI,'pcb','export','gerbers','-o',str(out/'gerbers')+'/',str(path)],check=True,capture_output=True)
 subprocess.run([CLI,'pcb','export','drill','-o',str(out/'gerbers')+'/',str(path)],check=True,capture_output=True)
 subprocess.run([CLI,'pcb','export','pos','--format','csv','--units','mm','--side','front','-o',str(out/'placement.csv'),str(path)],check=True,capture_output=True)
 subprocess.run([CLI,'sch','erc','--format','json','--severity-all','-o',str(folder/'erc.json'),str(folder/(name+'.kicad_sch'))],check=True,capture_output=True)
 subprocess.run([CLI,'pcb','drc','--format','json','--schematic-parity','--severity-all','-o',str(folder/'drc_final.json'),str(path)],check=True,capture_output=True)
 groups=collections.defaultdict(list)
 for f in board.GetFootprints():
  ref=f.GetReference()
  if ref.startswith(('H','TP')):continue
  value=f.GetValue();fp=str(f.GetFPID().GetLibItemName());groups[(value,fp)].append(ref)
 for (value,fp),refs in groups.items():
  mpn=value.split(' /')[0] if any(x in value for x in ['MT6701','SN74','CD74','AP3429','744383','1206L','0467001','2N7002']) else ''
  if 'BM05B' in value:mpn='BM05B-SRSS-TB';value='JST SH 5P top entry'
  if fp=='D_SMA':mpn='SS14';value='1A Schottky / qualification Vf <=0.5V at full load'
  if set(refs).issubset({'J1','J2'}) and kind=='carrier':mpn='2.54mm male header 1x7, 4.0mm PCB gap, rows 15.24mm';value='7P header'
  if kind=='carrier' and refs==['R50']:mpn='TNPW0603316KBEEA'
  if kind=='carrier' and refs==['R51']:mpn='TNPW060366K5BEEA'
  if kind=='carrier' and '22u' in value:mpn='GRM21BR61A226ME51L (subject to DC-bias acceptance)'
  rule='Exact listed MPN; substitutions require same pin map and documented electrical/package equivalence.' if mpn else 'Supplier to return exact manufacturer MPN in AVL before first article; meet value, dielectric, rating and package.'
  if '22u' in value:rule+=' C7 effective >=10uF at 4.1V; C8+C9 effective >=20uF at 3.45V. Supplier DC-bias curve required.'
  rows.append({'board':kind,'references':' '.join(sorted(refs)),'value':value,'footprint':fp,'mpn_or_procurement_spec':mpn,'per_board':len(refs),'assembled_boards':units,'net_quantity':len(refs)*units,'purchase_quantity_or_moq':'SUPPLIER_QUOTE_REQUIRED','acceptance':rule})
 d=json.loads((folder/'drc_final.json').read_text());e=json.loads((folder/'erc.json').read_text());assert not d['violations'] and not d['unconnected_items'] and not [v for sh in e.get('sheets',[]) for v in sh.get('violations',[])]
 boards.append({'board':kind,'assembled_quantity':units,'bare_pcb_order_basis':50 if kind=='sensor' else 5,'dimensions_mm':[12,10,1] if kind=='sensor' else [80,94,1.6],'layers':2 if kind=='sensor' else 4,'minimum_clearance_mm':.15,'outer_copper_um':35,'inner_copper_um':None if kind=='sensor' else 17.5,'finish':'Lead-free HASL or ENIG; quote both, no price presumed','ERC_DRC_PASS':True,'fabrication_sha256':hashlib.sha256(path.read_bytes()).hexdigest()})
# Board mounting, cable contacts, wire, stock and processing are deliberately separate.
extras=[{'item':'SHR-05V-S','net_quantity':48,'spares_or_loss':2,'scope':'5P harness housings'}, {'item':'SSH-003T-P0.2-H','net_quantity':240,'spares_or_loss':20,'scope':'AWG30, insulation OD 0.4..0.7mm; machine crimp'}, {'item':'Seeed Studio XIAO ESP32S3 standard','net_quantity':1,'spares_or_loss':0,'scope':'No camera/Sense add-on'}, {'item':'MT6701CT-STD-R','net_quantity':48,'spares_or_loss':2,'scope':'46 active +2 completed spares +2 assembly-loss chips; no duplicate billing'}, {'item':'M2x6 thread-forming/self-tapping for plastic, head <=4mm','net_quantity':4,'spares_or_loss':2,'scope':'New carrier mounting; do not put metal-thread screws in printed pilot bosses'}]
(D/'electronic_bom.json').write_text(json.dumps({'status':'QUOTE_AND_FIRST_ARTICLE_CANDIDATE','boards':boards,'components':rows,'separate_procurement':extras,'confirmed_quotes':0,'physical_qualification':False},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
# TSV is only a machine-readable BOM, not a hand-authored spreadsheet model.
with (D/'electronic_bom.tsv').open('w',newline='',encoding='utf-8-sig') as f:
 w=csv.DictWriter(f,fieldnames=list(rows[0]),delimiter='\t');w.writeheader();w.writerows(rows)
print('MANUFACTURING',[(x['board'],x['layers'],x['ERC_DRC_PASS']) for x in boards],flush=True)
