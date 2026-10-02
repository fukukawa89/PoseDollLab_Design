"""Run with KiCad Python to refresh final-board pad snapshots for the guide."""
from pathlib import Path
import hashlib,json
import pcbnew
ROOT=Path(__file__).resolve().parents[1];H=ROOT/'Hardware/PoseDoll44'
for name,filename in [('carrier','PoseDoll_O22_SSI_Carrier'),('sensor','PoseDoll_O22_MT6701CT')]:
    path=H/f'bench/revO22/electronics/{name}/{filename}.kicad_pcb';board=pcbnew.LoadBoard(str(path));rows=[]
    point=lambda p:[pcbnew.ToMM(p.x),pcbnew.ToMM(p.y)]
    for f in sorted(board.GetFootprints(),key=lambda x:x.GetReference()):
        rows.append({'ref':f.GetReference(),'value':f.GetValue(),'footprint':str(f.GetFPID().GetLibItemName()),'at_mm':point(f.GetPosition()),'rotation_deg':f.GetOrientationDegrees(),'pads':[{'pin':p.GetNumber(),'net':p.GetNetname().removeprefix('/'),'at_mm':point(p.GetPosition())} for p in f.Pads()]})
    target=H/f'tutorials/assembly-o22/evidence/{name}_native_pads.json'
    target.write_text(json.dumps({'source':str(path.relative_to(ROOT)).replace('\\','/'),'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'components':rows},ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    print(name,len(rows),'footprints')
