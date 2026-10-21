"""O23C 64 x 60 mm double-sided SSI carrier *placement*, not a routed PCB.

Run with KiCad's Python. Start from the final O22 native board, preserve UUIDs
and every pad/net assignment. No new circuit, pin ordering or voltage is inferred.
All O22 input files remain read-only. Native ERC/DRC reports are retained, and
unrouted nets are deliberately not suppressed or described as a DRC pass.
"""
from pathlib import Path
import json, shutil, hashlib, subprocess, csv
import pcbnew as p

R=Path(__file__).resolve().parents[1]
H=R/'Hardware/PoseDoll44'
SRC=H/'bench/revO22/electronics/carrier'
D=H/'bench/revO23/electronics/carrier'
OLD='PoseDoll_O22_SSI_Carrier';NAME='PoseDoll_O23C_SSI_Carrier'
CLI=Path('D:/ProgramFiles/KiCad/10.0/bin/kicad-cli.exe')

def v(x,y):return p.VECTOR2I(p.FromMM(x),p.FromMM(y))
def put(path,data):path.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def nets(board):return sorted((f.GetReference(),a.GetNumber(),a.GetNetname()) for f in board.GetFootprints() for a in f.Pads())


def main():
    D.mkdir(parents=True,exist_ok=True)
    src=SRC/(OLD+'.kicad_pcb');original_hash=sha(src);b=p.LoadBoard(str(src));original_nets=nets(b)
    for q in list(b.GetTracks()):b.Delete(q)
    for q in list(b.Zones()):b.Delete(q)
    for q in list(b.GetDrawings()):b.Delete(q)
    print('CLEARED routing and drawings',flush=True)
    for ext in ('.kicad_sch','.kicad_pro'):
        shutil.copy2(SRC/(OLD+ext),D/(NAME+ext))
    for filename in ('sym-lib-table','fp-lib-table'):
        if (SRC/filename).exists():shutil.copy2(SRC/filename,D/filename)
    for dirname in ('symbols',):
        if (SRC/dirname).exists():shutil.copytree(SRC/dirname,D/dirname,dirs_exist_ok=True)
    # Explicit positions are native footprint anchors, not guessed body centres.
    positions={
      'J1':(5,7.38),'J2':(20.24,22.62),'J3':(32,54),
      'U1':(31,9),'U2':(31,22),'U3':(30,36),'U6':(10,32),
      'U4':(12,31),'U5':(12,45),'U7':(16,48),
      'C1':(37,9),'C2':(37,22),'C3':(36,35),'C6':(10,37),
      'C4':(18,29),'C5':(18,43),
      'Q1':(5,27),'R1':(10,27),'R2':(15,27),
      'R30':(25,29),'R31':(30,29),'R40':(36,39),
      'R32':(8,23),'R33':(13,23),'R41':(18,34),
      'R34':(8,38),'R35':(13,38),'R42':(18,48),
      'F4':(35,46),'D1':(28,46),'L1':(9,48),
      'C7':(22,48),'C8':(7,54),'C9':(12,54),'F5':(8,42),
      'R50':(17,55),'R51':(21,55),'C10':(17,52),
      'TP1':(39,54),'TP2':(22,42),'TP3':(38,29),'TP4':(39,48),
      'H1':(3,3),'H2':(61,3),'H3':(3,57),'H4':(61,57)}
    for i in range(6):positions['R'+str(10+i)]=(26+5*(i%3),14.5+2.4*(i//3))
    back={'U4','U5','C4','C5','R32','R33','R34','R35','R41','R42'}
    # A01-A14 on the front; the B and C banks on the back. Each port keeps
    # its exact O22 reference and pad nets, including 1 GND / 2 3V45.
    for i in range(14):positions['J'+str(10+i)]=(47+10*(i%2),9+6.2*(i//2))
    for bank,first in enumerate((26,42)):
        for i in range(16):
            ref='J'+str(first+i);positions[ref]=(27+10*(i%4),8.5+6*(i//4+4*bank));back.add(ref)
    rows=[]
    for f in b.GetFootprints():
        ref=f.GetReference();assert ref in positions,ref
        if ref in back and f.GetLayer()!=p.B_Cu:f.Flip(f.GetPosition(),True)
        f.SetOrientationDegrees(180 if ref=='J2' else 0)
        f.SetPosition(v(*positions[ref]))
        f.Reference().SetVisible(False);f.Value().SetVisible(False)
        # Small bank labels are placed between connector rows, on their own side.
        if ref.startswith('J') and ref not in ('J1','J2','J3'):
            label=p.PCB_TEXT(b);label.SetText(f.GetValue().split()[0])
            x,y=positions[ref];label.SetPosition(v(x,y+2.7));label.SetTextSize(v(.8,.8));label.SetTextThickness(p.FromMM(.1))
            label.SetLayer(p.B_SilkS if ref in back else p.F_SilkS);label.SetMirrored(ref in back);b.Add(label)
        bb=f.GetBoundingBox(False,False)
        libid=f.GetFPID()
        footprint_id=str(libid.GetLibNickname())+':'+str(libid.GetLibItemName())
        rows.append(dict(reference=ref,value=f.GetValue(),footprint=footprint_id,
            side='B' if ref in back else 'F',x_mm=positions[ref][0],y_mm=positions[ref][1],angle_deg=f.GetOrientationDegrees(),
            bbox_mm=[p.ToMM(bb.GetLeft()),p.ToMM(bb.GetTop()),p.ToMM(bb.GetRight()),p.ToMM(bb.GetBottom())],
            pads={a.GetNumber():a.GetNetname() for a in f.Pads()}))
    points=[(0,0),(64,0),(64,60),(0,60)]
    for a,z in zip(points,points[1:]+points[:1]):
        q=p.PCB_SHAPE();q.SetShape(p.SHAPE_T_SEGMENT);q.SetStart(v(*a));q.SetEnd(v(*z));q.SetLayer(p.Edge_Cuts);q.SetWidth(p.FromMM(.05));b.Add(q)
    b.SetCopperLayerCount(4);b.GetDesignSettings().SetBoardThickness(p.FromMM(1.6))
    assert nets(b)==original_nets,'Pad-to-net identity must survive placement.'
    out=D/(NAME+'.kicad_pcb');p.SaveBoard(str(out),b)
    checks={}
    for kind,args in [('erc',['sch','erc']),('drc',['pcb','drc','--schematic-parity','--all-track-errors'])]:
        suffix='.kicad_sch' if kind=='erc' else '.kicad_pcb'
        proc=subprocess.run([str(CLI),*args,'--format','json','--severity-all','-o',str(D/(kind+'.json')),str(D/(NAME+suffix))],capture_output=True)
        (D/(kind+'.log')).write_bytes(proc.stdout+proc.stderr)
        data=json.loads((D/(kind+'.json')).read_text('utf8'))
        issues=data.get('violations',[])+[x for s in data.get('sheets',[]) for x in s.get('violations',[])]
        checks[kind]=dict(exit_code=proc.returncode,violations=len(issues),unconnected=len(data.get('unconnected_items',[])),
            categories={typ:sum(x['type']==typ for x in issues) for typ in sorted({x['type'] for x in issues})})
    for side,layers in [('front','F.Cu,F.SilkS,F.Fab,Edge.Cuts'),('back','B.Cu,B.SilkS,B.Fab,Edge.Cuts')]:
        dest=D/'svg'/side;dest.mkdir(parents=True,exist_ok=True)
        proc=subprocess.run([str(CLI),'pcb','export','svg','--mode-single','--exclude-drawing-sheet','--page-size-mode','2','--layers',layers,*(['--mirror'] if side=='back' else []),'--output',str(dest/(side+'.svg')),str(out)],capture_output=True)
        (dest/'export.log').write_bytes(proc.stdout+proc.stderr)
    assert sha(src)==original_hash,'O22 source PCB changed during the layout operation.'
    put(D/'placement.json',dict(revision='O23C-double-sided-64x60',source_pcb_sha256=original_hash,pcb_sha256=sha(out),
        source_board_mm=[80,94,1.6],board_mm=[64,60,1.6],copper_layers=4,components_on_both_sides=True,
        identical_pad_nets=nets(p.LoadBoard(str(out)))==original_nets,pad_net_count=len(original_nets),
        old_pcb_unmodified=sha(src)==original_hash,sensor_ports=46,
        footprints=rows,checks=checks,tracks=0,routing_complete=False,manufacturing_release=False,
        mechanical_component_height_status='Conservative design envelopes; mate and wire bend dimensions need assembly qualification.',
        power_note='O22 circuit unchanged. J2.7 XIAO 5V remains NC; J3 external 5V input is not tied to USB VBUS.'))
    print(json.dumps(checks),flush=True)


if __name__=='__main__':main()
