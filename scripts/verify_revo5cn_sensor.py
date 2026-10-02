"""Read the saved native PCB independently of the producer: pin map and via/land DFM."""
from pathlib import Path
import hashlib,json,math
import pcbnew as pcb
R=Path(__file__).resolve().parents[1];H=R/'Hardware/PoseDoll44';D=H/'electronics/sensor_revO5CN';F=D/'PoseDoll_MT6701_CJT_CN1.kicad_pcb'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 before=sha(F);b=pcb.LoadBoard(str(F));fps={f.GetReference():f for f in b.GetFootprints()}
 padnets=lambda ref:{p.GetNumber():p.GetNetname().lstrip('/') for p in fps[ref].Pads() if p.GetNumber()}
 assert padnets('J1')=={'1':'GND','2':'+3V3','3':'CLK','4':'DO','5':'CS_N'}
 expected={'6':'DO_IC','7':'CLK','8':'CS_N','13':'+3V3','14':'+3V3','16':'GND'}
 actual=padnets('U1')
 for pin,net in expected.items():assert actual[pin]==net,(pin,actual[pin])
 for pin in set(actual)-set(expected):assert actual[pin].startswith('unconnected-'),pin
 assert not any('MOSI' in n for f in fps for n in padnets(f).values())
 assert abs(pcb.ToMM(b.GetDesignSettings().GetBoardThickness())-1)<1e-8
 pads=[p for f in fps.values() for p in f.Pads() if p.GetAttribute()==pcb.PAD_ATTRIB_SMD]
 gaps=[];vias=[]
 for t in b.GetTracks():
  if not isinstance(t,pcb.PCB_VIA):continue
  x,y=map(pcb.ToMM,(t.GetPosition().x,t.GetPosition().y));rad=pcb.ToMM(t.GetWidth(pcb.F_Cu))/2
  for p in pads:
   assert abs(p.GetOrientationDegrees()%180)<1e-6
   px,py=map(pcb.ToMM,(p.GetPosition().x,p.GetPosition().y));w,h=map(pcb.ToMM,(p.GetSize().x,p.GetSize().y))
   dx=max(abs(x-px)-w/2,0);dy=max(abs(y-py)-h/2,0);gaps.append(math.hypot(dx,dy)-rad)
  vias.append({'xy_mm':[x,y],'drill_mm':pcb.ToMM(t.GetDrillValue()),'pad_mm':2*rad})
 assert vias and min(gaps)>=.2-1e-6
 assert all(v['drill_mm']>=.3 and (v['pad_mm']-v['drill_mm'])/2>=.15-1e-6 for v in vias)
 assert sha(F)==before
 result={'schema':'cn1-native-independent-check-v1','source_sha256':{F.relative_to(R).as_posix():before,Path(__file__).relative_to(R).as_posix():sha(Path(__file__))},'pin_map_matches_datasheet_and_CN1_contract':True,'unused_and_EP_pads_isolated':True,'MOSInet_absent':True,'via_count':len(vias),'minimum_via_copper_to_SMD_land_mm':min(gaps),'via_in_pad_count':0,'vias':vias,'status':'PASS_DECLARED_PIN_AND_DFM_SCREENS','physical_tested':False,'manufacturing_released':False,'limit':'Not solder assembly qualification; EP still unspecified; supplier mask/DFM and actual crimp unknown'}
 out=H/'verification/revO5CN/runs/cn_20260924_r1/native_board_check.json';out.parent.mkdir(parents=True,exist_ok=True);out.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8');print(json.dumps({k:v for k,v in result.items() if k not in ('source_sha256','vias')},indent=2))
if __name__=='__main__':main()
