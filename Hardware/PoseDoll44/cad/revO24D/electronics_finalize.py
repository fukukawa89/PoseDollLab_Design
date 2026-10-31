"""Freeze routed native electrical files, tighter divider, native rule evidence."""
from electronics_carrier import *

def main():
    changes={'R50':('316k 0.1%','31.6k 0.1%'),'R51':('66.5k 0.1%','6.65k 0.1%'),'C10':('22p C0G starting value','220p C0G starting value')}
    b=p.LoadBoard(str(D/(NAME+'.kicad_pcb')));pro=json.loads((D/(NAME+'.kicad_pro')).read_text('utf8'));sch=D/(NAME+'.kicad_sch');text=sch.read_text('utf8')
    for f in b.GetFootprints():
        if f.GetReference() in changes:
            old,new=changes[f.GetReference()];f.SetValue(new);text=text.replace('"'+old+'"','"'+new+'"')
    sch.write_text(text,'utf8');p.SaveBoard(str(D/(NAME+'.kicad_pcb')),b);put(D/(NAME+'.kicad_pro'),pro)
    comps=json.loads((D/'components.json').read_text('utf8'));lay=json.loads((D/'placement.json').read_text('utf8'))
    for c in comps:
        if c['ref'] in changes:c['value']=changes[c['ref']][1]
    for c in lay['footprints']:
        if c['reference'] in changes:c['value']=changes[c['reference']][1]
    put(D/'components.json',comps);lay['checks']={n:check(n) for n in ['erc','drc']};d=json.loads((D/'drc.json').read_text('utf8'));lay['checks']['drc']['parity']=len(d['schematic_parity']);lay['pcb_sha256']=hashlib.sha256((D/(NAME+'.kicad_pcb')).read_bytes()).hexdigest();put(D/'placement.json',lay)
    trace={}
    for t in b.GetTracks():
        net=t.GetNetname();r=trace.setdefault(net,dict(length_mm=0,resistance_sum_ohm=0,minimum_width_mm=100,vias=0))
        if isinstance(t,p.PCB_VIA):r['resistance_sum_ohm']+=.005;r['vias']+=1
        else:
            length=p.ToMM(t.GetLength());width=p.ToMM(t.GetWidth());r['length_mm']+=length;r['resistance_sum_ohm']+=.01724*(length/1000)/(width*.035);r['minimum_width_mm']=min(r['minimum_width_mm'],width)
    put(D/'trace_metrics.json',dict(copper_thickness_mm=.035,copper_resistivity_ohm_mm2_per_m=.01724,via_resistance_bound_ohm=.005,nets=trace,scope='Sum of every copper branch resistance is a conservative upper bound on any source-to-load path, not an inferred exact power-integrity solution.'))
    copper_layers=[p.F_Cu,p.In1_Cu,p.In2_Cu,p.B_Cu]
    geom=dict(tracks=[],vias=[],pads=[],copper_layers=copper_layers)
    xy=lambda q:[p.ToMM(q.x),p.ToMM(q.y)]
    for t in b.GetTracks():
        if isinstance(t,p.PCB_VIA):geom['vias'].append(dict(net=t.GetNetname(),point=xy(t.GetPosition())))
        else:geom['tracks'].append(dict(net=t.GetNetname(),layer=t.GetLayer(),a=xy(t.GetStart()),b=xy(t.GetEnd()),width=p.ToMM(t.GetWidth())))
    for f in b.GetFootprints():
        for q in f.Pads():
            bb=q.GetBoundingBox();geom['pads'].append(dict(ref=f.GetReference(),num=q.GetNumber(),net=q.GetNetname(),point=xy(q.GetPosition()),layers=[l for l in copper_layers if q.IsOnLayer(l)],box=[p.ToMM(bb.GetLeft()),p.ToMM(bb.GetTop()),p.ToMM(bb.GetRight()),p.ToMM(bb.GetBottom())]))
    put(D/'power_network_input.json',geom)
    print('ELECTRICAL FINAL',lay['checks'],flush=True)
if __name__=='__main__':main()
