"""Re-route with explicit DSN classes and inductor keep-outs (KiCad exporter omits classes)."""
from pathlib import Path
import json,re
import pcbnew as p
R=Path(__file__).resolve().parents[1];D=R/'Hardware/PoseDoll44/bench/revO22/electronics/carrier'
b=p.LoadBoard(str(D/'placement.kicad_pcb'))
for f in b.GetFootprints():
 if f.GetReference()=='L1':f.SetOrientationDegrees(180)
# Keep routed conductors away from the unshielded gap and body, except terminal pads.
for layer in (p.F_Cu,p.B_Cu):
 for x0,y0,x1,y1 in [(121.73,83.75,122.27,88.25),(119.75,83.75,124.25,84.8),(119.75,87.2,124.25,88.25)]:
  z=p.ZONE(b);z.SetIsRuleArea(True);z.SetLayer(layer);z.SetDoNotAllowTracks(True);z.SetDoNotAllowVias(True);z.SetDoNotAllowZoneFills(True);z.SetDoNotAllowPads(False);z.SetDoNotAllowFootprints(False)
  poly=z.Outline();poly.NewOutline()
  for x,y in [(x0,y0),(x1,y0),(x1,y1),(x0,y1)]:poly.Append(p.FromMM(x),p.FromMM(y))
  b.Add(z)
p.SaveBoard(str(D/'route_input.kicad_pcb'),b)
assert p.ExportSpecctraDSN(b,str(D/'route_input.dsn'))
s=(D/'route_input.dsn').read_text();start=s.index('    (class kicad_default');end=s.index('  (wiring',start)
# Rewrite this class only: preserve all net membership, separate power widths.
chunk=s[start:end];head=chunk[:chunk.index('      (circuit')]
power=['/EXT5V','/FUSED5V','/VIN','/LX','/REG_3V45'];rail=['/GND','/SENSOR_3V45']
for n in power+rail:head=re.sub(r'(?<!\S)'+re.escape(n)+r'(?!\S)','',head)
def klass(name,nets,width):
 return '    (class '+name+' '+' '.join(nets)+' (circuit (use_via "Via[0-1]_600:300_um")) (rule (width '+str(width)+') (clearance 150)))\n'
new=head+'      (circuit (use_via "Via[0-1]_600:300_um")) (rule (width 200) (clearance 150)))\n'+klass('Power',power,600)+klass('Distribution',rail,400)+'  )\n'
s=s[:start]+new+s[end:];(D/'route_input.dsn').write_text(s)
print('Explicit power classes and inductor exclusions exported.')
