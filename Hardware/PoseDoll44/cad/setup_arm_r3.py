from pathlib import Path
import sys
sys.dont_write_bytecode=True
base=Path(__file__).resolve().parent
dest=base/'revO24E_LArm_Stock_R3'
dest.mkdir(exist_ok=True)
names=['build_stock.py','export_stock.py','check_stock.py','check_modules.py','validate_stock.py','load_stock.py','print_stock.py','render_stock.py','section_stock.py','deliver_stock.py','electronics_review.py']
for n in names:
 s=(base/'revO24E_LArm_Stock_R2'/n).read_text('utf8').replace('revO24E_LArm_Stock_R2','revO24E_LArm_Stock_R3').replace('O24E_LArm_Stock_R2','O24E_LArm_Stock_R3').replace('O24E_left_arm_stock_R2','O24E_left_arm_stock_R3').replace('S2-','S3-')
 (dest/n).write_text(s,encoding='utf8')
# Reuse the verified numeric helpers, but source unchanged geometry from frozen R2 STL round-trip bodies.
p=dest/'build_stock.py';s=p.read_text('utf8');start=s.index('def build():');end=s.index('\ndef save():',start)
s=s[:start]+'''R2=H/'bench/revO24E_LArm_Stock_R2'
def build():
 assert sha(R2/'production_meshes.npz')=='9bf25e08e41c3faf6107d6e558f7b25f61aa82ec839a56e2c8c25f8fdcbc965e'
 a=load(R2/'production_assembly.json')['parts'];z=np.load(R2/'production_meshes.npz');d=Design();ints=load(R2/'interfaces.json');d.rolls=ints['rolls'];d.hinges=ints['hinges']
 removed={'KEEP_E-P017','KEEP_E-H1171','KEEP_E-H1172','KEEP_E-H1173','KEEP_E-H1174'}
 for old in a:
  if old['name'] in removed:continue
  i=str(old['i']);solid=md.Manifold(md.Mesh64(np.array(z[i+'v'],copy=True),np.array(z[i+'f'],dtype=np.uint64,copy=True)))
  p={key:old[key] for key in ['name','frame','role','sku','note','source']};p['s']=solid;p['pn']=old['part_number'].replace('S2-','S3-');p['source_r2_print']=old['part_number'] if old['role']=='structure' else None
  if old['name']=='KEEP_E-P018':
   # Preserve the R2 wrist ears, strengthened stems and magnet seat exactly.
   # Recreate the visible palm, with a continuous neck instead of socket, key gap and M2 capture.
   palm=box([-9,-3.5,-42],[10,3.5,-28])+beam([-5.5,0,-42],[6.5,0,-42],3.5)+beam([-6,0,-31],[-13,0,-35],4)
   palm-=beam([-5,3.9,-35],[6,3.9,-36],1.2)
   palm+=beam([1,-3.6,-33],[1,-3.6,-40],1.1)
   palm+=oval_loft([(-31.5,6,6),(-27,6.5,5),(-21,8,4),(-20.5,8,4)])
   p['s']+=palm;p['pn']='S3-P010';p['source_r2_print']=None;p['source']='S2-P010 + S2-P011'
   p['note']='R3一体腕输出叉与手掌；填实旧方键/横孔连接，保留掌纹、拇指轮廓、双轴腕摩擦面与磁铁入口；无需掌部M2紧固组。'
  d.parts.append(p)
 return d
''' +s[end:]
s=s.replace('pn=f\'S3-{"P" if p["role"]=="structure" else "H"}{(len(prints)+1 if p["role"]=="structure" else len(hardware)+1):03d}\'','pn=p["pn"]')
s=s.replace("r['components']=", "r['source_r2_print']=p['source_r2_print'];r['components']=")
p.write_text(s,encoding='utf8')
# Exact byte reuse of all ten unaffected print files; only the unified hand is remeshed.
p=dest/'export_stock.py';s=p.read_text('utf8').replace("load(SRC/'kit.json')['structural_parts']","load(R2/'kit.json')['structural_parts']")
s=s.replace("reused=p['source'] in ['E-P019']","reused=bool(r.get('source_r2_print'))")
s=s.replace("o=old[p['source']];shutil.copyfile(SRC/o['stl']","o=old[r['source_r2_print']];shutil.copyfile(R2/o['stl']")
s=s.replace("byte_identical_source_stl=p['source'] if reused else None","byte_identical_source_stl=r.get('source_r2_print') if reused else None")
s=s.replace("'KEEP_E-P018':'双轴腕输出叉（原 E-P018）'","'KEEP_E-P018':'一体腕输出叉与手掌（替代R2 P010＋P011）'")
s=s.replace("SRC/'production_meshes.npz',SRC/'O24E_left_arm_mechanical.zip'","R2/'production_meshes.npz',R2/'O24E_left_arm_stock_R2.zip',H/'bench/revO24E_LArm_Stock_R2_AssemblyGuide/data.js'")
p.write_text(s,encoding='utf8')
# No removable palm interface or its four fasteners remains in R3.
p=dest/'validate_stock.py';s=p.read_text('utf8');start=s.index(" prepared=test('palm_on_square_key'");end=s.index(" put(OUT/'verification/hinge_wrist_paths.json'",start);s=s[:start]+s[end:];p.write_text(s,encoding='utf8')
p=dest/'deliver_stock.py';s=p.read_text('utf8');start=s.index(" step(m,'KEEP_E-P017'");end=s.index(" allids={",start);s=s[:start]+s[end:];s=s.replace("'合上第二轴输出叉'","'装入一体腕叉与手掌'").replace("'从掌部一端装入，两个叉耳与X轴摩擦面同轴。'","'整件从掌部一端装入，两个叉耳与X轴摩擦面同轴；手掌已连为一体，不再单独装掌部螺钉。'");s=s.replace('printed_bodies=12','printed_bodies=11');p.write_text(s,encoding='utf8')
# Renderer keeps no obsolete R1 comparison object, shows the new unified hand.
p=dest/'render_stock.py';s=p.read_text('utf8');start=s.index("shot('P007_R2.png'");end=s.index("sc.frame_set(1+24",start);s=s[:start]+"shot('unified_hand.png',(3,3,1),lambda p:p['name']=='KEEP_E-P018')\n"+s[end:];s=s.replace('no electronics or magnets','mechanical trial; electronics reservations provided separately');p.write_text(s,encoding='utf8')
# Electronics study refers to the unified part; geometry and angle bindings are unchanged.
p=dest/'electronics_review.py';s=p.read_text('utf8').replace('S3-P011','S3-P010');p.write_text(s,encoding='utf8')
print('R3 source prepared',dest)
