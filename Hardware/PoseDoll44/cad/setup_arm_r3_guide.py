from pathlib import Path
import hashlib
base=Path(__file__).resolve().parent;h=base.parent;dest=base/'revO24E_LArm_Stock_R3_AssemblyGuide';dest.mkdir(exist_ok=True);digest=hashlib.sha256((h/'bench/revO24E_LArm_Stock_R3/production_meshes.npz').read_bytes()).hexdigest()
for n in ['build_guide.py','verify_guide.py','docs_guide.py','package_guide.py','index.html','style.css','guide.js','enhance.js']:
 s=(base/'revO24E_LArm_Stock_R2_AssemblyGuide'/n).read_text('utf8')
 s=s.replace('revO24E_LArm_Stock_R2','revO24E_LArm_Stock_R3').replace('O24E_left_arm_stock_R2','O24E_left_arm_stock_R3').replace('S2-','S3-').replace('R2','R3')
 s=s.replace('161','156').replace('483','468').replace('146','141').replace('134','130').replace('12 个打印件','11 个打印件').replace('12个打印件','11个打印件').replace('12 prints','11 prints').replace('counts[None]==12','counts[None]==11')
 if n=='build_guide.py':
  s=s.replace("DEST=H/'bench/revO24E_LArm_Stock_R3_AssemblyGuide'","DEST=SOURCE/'assembly_guide'")
  s=s.replace("EXPECTED='9bf25e08e41c3faf6107d6e558f7b25f61aa82ec839a56e2c8c25f8fdcbc965e'",f"EXPECTED='{digest}'")
  s=s.replace(",SOURCE/'O24E_left_arm_stock_R3.zip'",'')
  s=s.replace('双叉耳开口朝腕中心件；方键端朝手掌。侧面磁铁座保留，本轮不装电子件。','一体件的双叉耳开口朝腕中心件，指端远离腕轴；掌部不再拆分。侧面磁铁入口保留，本轮不装电子件。').replace('手掌方键','一体掌部')
  s=s.replace("if mid=='W' and sn>=45:row['target']=N['KEEP_E-P017'];row['printed_direction']=orientation[row['target']]['orientation']",'')
 if n=='index.html':s=s.replace('<div class="top-right">','<div class="top-right"><a href="../PRINTING.html">只重打一件 ↗</a>')
 (dest/n).write_text(s,encoding='utf8')
print('R3 guide source',digest)
