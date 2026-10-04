"""Rev O port-count-specific native KiCad studies using actual pinned footprints.
No assumed tiny blank boards: every retained component has a net/pad identity.
These unrouted placements do not constitute a released PCB.
"""
from pathlib import Path
import sys, json, math, copy, subprocess, xml.etree.ElementTree as ET
REPO=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(REPO/'Hardware/PoseDoll44/tools'))
sys.path.insert(0,str(REPO/'scripts'))
import build_regional_revM as legacy
import pcbnew as pcb
from revo_common import HW, VERIFY, save, sha
CLI='D:/ProgramFiles/KiCad/10.0/bin/kicad-cli.exe'

def main():
    original=copy.deepcopy(legacy.components())
    reports=[]
    for ports in (0,3,6,7,9):
        name='PoseDoll_RevO_G0_placement' if ports==0 else f'PoseDoll_RevO_N{ports}_placement'
        out=HW/('electronics/revO/g0_gateway' if ports==0 else f'electronics/revO/node_{ports}port');out.mkdir(parents=True,exist_ok=True)
        legacy.OUT=out;legacy.NAME=name
        components=[]
        for raw in original:
            c=copy.deepcopy(raw);ref=c['ref'];section=c['section']
            if ref in ('SW1','SW2') or (ports!=0 and (section=='usb' or ref=='#FLG04')):continue
            if section.startswith('port') and int(section[4:])>ports:continue
            if ref=='U1':
                for pin,net in list(c['nets'].items()):
                    if (ports!=0 and net in ('USB_DM_IC','USB_DP_IC')) or (net and net.startswith('CS') and int(net[2:net.index('_')])>ports):
                        c['nets'][pin]=None
            if ref=='J1':c['pcb']=(85.8,95);c['back']=True;c['value']='Fused 5V branch; NOT 12V qualified'
            if ref=='JP1':c['pcb']=(115.5,93);c['fp']='Jumper:SolderJumper-2_P1.3mm_Open_Pad1.0x1.5mm'
            if ref=='R5':c['pcb']=(115.5,90)
            components.append(c)
        # Supplier pogo access instead of everyday on-body USB/buttons.
        for i,(net,xy) in enumerate([('EN',(115,94)),('BOOT_N',(115,97))],5):
            components.append(dict(ref=f'TP{i}',lib='Connector',sym='TestPoint',value=net,fp='TestPoint:TestPoint_Pad_D1.0mm',nets={'1':net},pcb=xy,angle=0,back=False,section='control'))
        legacy.comps=components
        if ports==0 and not (out/'PoseDoll.pretty/USB_C_Data_Port.kicad_mod').exists():
            subprocess.run([sys.executable,__file__,'--prepare-g0-footprints'],check=True)
        rootid=legacy.schematic();legacy.board(rootid)
        board=pcb.LoadBoard(str(out/'placement.kicad_pcb'))
        for d in list(board.GetDrawings()):
            if d.GetLayer()==pcb.Edge_Cuts:board.Remove(d)
        bottom=166 if ports==0 else 124+11*(math.ceil(ports/3)-1)
        corners=[(80,80),(120,80),(120,bottom),(80,bottom)]
        for a,b in zip(corners,corners[1:]+corners[:1]):
            line=pcb.PCB_SHAPE();line.SetShape(pcb.SHAPE_T_SEGMENT);line.SetStart(pcb.VECTOR2I(*[pcb.FromMM(v) for v in a]));line.SetEnd(pcb.VECTOR2I(*[pcb.FromMM(v) for v in b]));line.SetLayer(pcb.Edge_Cuts);line.SetWidth(pcb.FromMM(.05));board.Add(line)
        target=out/(name+'.kicad_pcb');pcb.SaveBoard(str(target),board)
        parts=[]; connectors=[]
        for f in board.GetFootprints():
            boxes=[x.GetBoundingBox() for x in f.GraphicalItems() if x.GetLayer() in (pcb.F_CrtYd,pcb.B_CrtYd)]
            if not boxes:boxes=[f.GetBoundingBox(False,False)]
            b=[min(bb.GetLeft() for bb in boxes),min(bb.GetTop() for bb in boxes),max(bb.GetRight() for bb in boxes),max(bb.GetBottom() for bb in boxes)]
            b=[pcb.ToMM(v)-80 for v in b]
            ref=f.GetReference();is_back=f.GetLayer()==pcb.B_Cu
            # Package heights are conservative study bounds, not claimed vendor STEP.
            ht=3.2 if ref=='U1' else 4.8 if ref.startswith('J') else 2.2 if ref=='L1' else 1.8 if ref=='U3' else 1.3
            item=dict(ref=ref,value=f.GetValue(),footprint=str(f.GetFPID().GetLibNickname())+':'+str(f.GetFPID().GetLibItemName()),courtyard_xy_mm=b,back=is_back,height_max_assumed_mm=ht,
                      pads=[dict(number=p.GetNumber(),net=p.GetNetname(),x_mm=pcb.ToMM(p.GetPosition().x)-80,y_mm=pcb.ToMM(p.GetPosition().y)-80) for p in f.Pads()])
            parts.append(item)
            if ref.startswith('J') and ref!='JP1':
                connectors.append(dict(ref=ref,position_xy_mm=[(b[0]+b[2])/2,(b[1]+b[3])/2],side='back' if is_back else 'front',plug_envelope_mm=[b[2]-b[0],b[3]-b[1],6.0],unplug_travel_mm=12,wire_bend_radius_mm=12,source='PCB courtyard exact; mating plug/strain-relief preliminary conservative reservations require part-specific supplier confirmation'))
        layout=dict(name=name,ports=ports,board_mm=[40,bottom-80,1.2],components=parts,connectors=connectors,
                    status='NATIVE_KICAD_UNROUTED_COMPONENT_PLACEMENT',hardware_voltage_V=5,actual_mating_step_status='NOT_RUN',height_scope='assumed maximum study envelopes',source_legacy_generator_sha256=sha(HW/'tools/build_regional_revM.py'))
        save(out/'layout.json',layout)
        commands=[('erc',['sch','erc','--format','json','--severity-error','-o',str(out/'erc.json'),str(out/(name+'.kicad_sch'))]),
                  ('drc',['pcb','drc','--format','json','--severity-error','-o',str(out/'drc.json'),str(target)])]
        checks={}
        for kind,args in commands:
            result=subprocess.run([CLI,*args],stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
            (out/(kind+'.log')).write_bytes(result.stdout)
            data=json.loads((out/(kind+'.json')).read_text(encoding='utf-8')) if (out/(kind+'.json')).exists() else {}
            violations=data.get('violations',[])+[v for sheet in data.get('sheets',[]) for v in sheet.get('violations',[])]
            checks[kind]=dict(exit_code=result.returncode,status='PASS' if result.returncode==0 and not violations and not data.get('unconnected_items',[]) else 'FAIL',violations=len(violations),unconnected_items=len(data.get('unconnected_items',[])))
        save(out/'checks.json',checks)
        reports.append(dict(ports=ports,board_mm=layout['board_mm'],components=len(parts),directory=str(out.relative_to(REPO)),checks=checks))
        print(ports,'ports',layout['board_mm'],checks,flush=True)
    save(VERIFY/'electronics_placement.json',dict(boards=reports,routing='NOT_RUN',physical_tested=False,manufacturing_released=False))

if __name__=='__main__':
    if '--prepare-g0-footprints' in sys.argv:
        legacy.OUT=HW/'electronics/revO/g0_gateway';legacy.prepare_footprints()
    else:main()
