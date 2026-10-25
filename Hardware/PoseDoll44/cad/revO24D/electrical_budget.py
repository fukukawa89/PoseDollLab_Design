"""Native-board copper-network DC calculation and stated bus design budgets."""
from fullbody import *
from scipy.sparse import lil_matrix
from scipy.sparse.linalg import spsolve

def crc(word):
    r=15
    for i in range(31,-1,-1):
        inv=((word>>i)&1)^((r>>3)&1);r=((r<<1)&15)^(3 if inv else 0)
    return r

def main():
    root=OUT/'electronics';d=load(root/'carrier/power_network_input.json');nets=['/SENSOR_3V45','/REG_3V45','/GND'];pts=[];lookup={};par=[];edges=[]
    def node(net,layer,xy):
        key=(net,layer,*np.round(xy,6));i=lookup.get(key)
        if i is None:i=len(pts);lookup[key]=i;pts.append((net,layer,np.array(xy)));par.append(i)
        return i
    def find(i):
        while par[i]!=i:par[i]=par[par[i]];i=par[i]
        return i
    def join(a,b):par[find(a)]=find(b)
    tracks=[t for t in d['tracks'] if t['net'] in nets]
    for t in tracks:
        node(t['net'],t['layer'],t['a']);node(t['net'],t['layer'],t['b'])
    for v in d['vias']:
        if v['net'] not in nets:continue
        ids=[node(v['net'],l,v['point']) for l in d['copper_layers']]
        for i in ids[1:]:edges.append((ids[0],i,.005,'via'))
    pads={}
    for p in d['pads']:
        if p['net'] not in nets:continue
        ids=[node(p['net'],l,p['point']) for l in p['layers']];pads[p['ref'],p['num']]=ids[0]
        for i in ids[1:]:join(ids[0],i)
        x0,y0,x1,y1=p['box']
        for i,(net,l,xy) in enumerate(pts):
            if net==p['net'] and l in p['layers'] and x0-1e-5<=xy[0]<=x1+1e-5 and y0-1e-5<=xy[1]<=y1+1e-5:join(ids[0],i)
    for t in tracks:
        a=np.array(t['a']);b=np.array(t['b']);v=b-a;vv=v@v
        if vv<1e-12:continue
        on=[]
        for i,(net,l,q) in enumerate(pts):
            if net!=t['net'] or l!=t['layer']:continue
            f=((q-a)@v)/vv
            if -1e-5<=f<=1+1e-5 and np.linalg.norm(q-a-f*v)<2e-5:on.append((float(f),i))
        on.sort()
        for (f,i),(g,j) in zip(on,on[1:]):
            length=(g-f)*math.sqrt(vv)
            if length<1e-7:join(i,j)
            else:edges.append((i,j,.01724*1.25*(length/1000)/(t['width']*.035),'copper'))
    edges.append((pads['F5','1'],pads['F5','2'],.2,'fuse_bound'))
    roots=sorted({find(i) for i in range(len(pts))});ri={r:i for i,r in enumerate(roots)};ix=lambda i:ri[find(i)]
    N=len(roots);G=lil_matrix((N,N));loadI=np.zeros(N);connections=[]
    for a,b,R,tag in edges:
        i,j=ix(a),ix(b)
        if i==j:continue
        g=1/R;G[i,i]+=g;G[j,j]+=g;G[i,j]-=g;G[j,i]-=g;connections.append((i,j,R,tag))
    carrier=load(root/'carrier/placement.json');ports=[p['reference'] for p in carrier['footprints'] if p['reference'].startswith('J') and p['reference'] not in ['J1','J2','J3']]
    loads=[]
    for ref in ports:loads.append((ref,'2','1',.01))
    for ref,powpin,gndpin,current in [('U1','20','10',.008),('U2','20','10',.008),('U3','24','12',.002),('U4','24','12',.002),('U5','24','12',.002)]:loads.append((ref,powpin,gndpin,current))
    for ref,hi,lo,I in loads:loadI[ix(pads[ref,hi])]-=I;loadI[ix(pads[ref,lo])]+=I
    fixed={ix(pads['L1','2']):0.,ix(pads['U7','2']):0.}
    # Solve voltage deviations from ideal source/return. Both reference nodes
    # are zero because the two copper networks are disjoint except through
    # prescribed load currents; F5 links the two positive-rail net names.
    for i,val in fixed.items():G[i,:]=0;G[i,i]=1;loadI[i]=val
    voltage=spsolve(G.tocsr(),loadI)
    assert np.all(np.isfinite(voltage)),'Native extracted copper graph is disconnected'
    drops=[dict(reference=ref,current_A=I,supply_drop_V=-float(voltage[ix(pads[ref,hi])]),ground_rise_V=float(voltage[ix(pads[ref,lo])]),loop_drop_V=float(voltage[ix(pads[ref,lo])]-voltage[ix(pads[ref,hi])])) for ref,hi,lo,I in loads]
    rt=31600;rb=6650;low=.588*(1+rt*.999/(rb*1.001))-.2e-6*rt*1.001;high=.612*(1+rt*1.001/(rb*.999))+.2e-6*rt*1.001;ripple=.05
    h=load(OUT/'harness/routes.json');longest=max(c['cut_length_mm'] for c in h['cables'])/1000;wire_drop=2*.345*longest*1.25*.01;mindrop=max(r['loop_drop_V'] for r in drops if r['reference'] in ports);sensormin=low-ripple-mindrop-wire_drop
    # Each 6-core SCK branch uses a procurement-bound 100 pF/m, 10 pF input.
    bankC={b:sum(c['cut_length_mm']/1000*100+10 for c in h['cables'] if c['bank']==b) for b in 'ABC'};worstC=max(bankC.values());tau_ns=(50+33)*worstC/1000;settle_ns=5*tau_ns+100;clock_hz=100000;half_ns=1e9/(2*clock_hz)
    cycle_s=15*(4*32/clock_hz+10e-6);target_hz=40
    # Datasheet published CRC-disable command is an independent known answer.
    crc_ok=crc(0x0F000400)==7;single_bit_detected=all(crc((0x0F000400^(1<<bit))&0xFFFFFFF0)!=7 for bit in range(4,32))
    logic_output_min=low-ripple-max(r['loop_drop_V'] for r in drops if r['reference'] in ['U1','U2'])-.2
    logic_input_required=.75*(high+ripple);criteria=dict(native_carrier=all(r['violations']==0 and r['unconnected']==0 for r in carrier['checks'].values()),native_sensor_boards=all(v['routing_complete'] for v in load(root/'sensors/manifest.json')['variants']),rail_upper=high+ripple<3.6,sensor_minimum=sensormin>=2.3,logic_high=logic_output_min>=logic_input_required,settling=settle_ns<half_ns*.5,scan_rate=1/cycle_s>=target_hz,crc_known_answer=crc_ok,crc_single_bit_detection=single_bit_detected)
    result=dict(status='PASS_ELECTRICAL_BUDGET_CONDITIONAL' if all(criteria.values()) else 'FAIL',geometry_sha256=sha(OUT/'assembly_meshes.npz'),criteria=criteria,pcb_sha256=carrier['pcb_sha256'],power=dict(nominal_rail_V=.6*(1+rt/rb),regulated_DC_range_V=[low,high],allowed_ripple_peak_V=ripple,upper_with_ripple_V=high+ripple,total_budget_current_A=sum(x[3] for x in loads),sensor_budget_each_mA=10,maximum_copper_loop_drop_V=mindrop,maximum_wire_loop_drop_V=wire_drop,sensor_min_supply_V=sensormin,logic_output_min_V=logic_output_min,logic_input_required_V=logic_input_required,copper_temperature_factor=1.25,fuse_resistance_bound_ohm=.2,loads=drops),timing=dict(clock_hz=clock_hz,bank_capacitance_pF=bankC,assumed_driver_resistance_ohm=50,source_series_ohm=33,five_tau_and_extra_ns=settle_ns,half_period_ns=half_ns,frames_per_address=4,addresses=15,scan_cycle_ms=cycle_s*1000,target_frame_hz=target_hz,maximum_budget_frame_hz=1/cycle_s),CRC=dict(known_word='0x0F000407',known_answer_pass=crc_ok,single_bit_negative_controls=28,single_bit_detected=single_bit_detected),sources=['https://www.diodes.com/datasheet/download/AP3429.pdf','https://www.ti.com/lit/ds/symlink/tmag5170.pdf','https://www.ti.com/lit/ds/symlink/sn74lvc244a.pdf'],scope='Native ERC/DRC/connectivity plus extracted DC copper resistor network, explicit current/cable/capacitance bounds, conservative 100 kHz broadcast SPI budget. 10 mA per sensor, 50 mV ripple, 100 pF/m and 50 ohm effective driver resistance are design limits to verify, not measured values. MCU has three sampled MISO pins, host calibration, CRC/status rejection. Board thermal, signal ringing, magnetic EMC, power sequencing and physical calibration still require hardware tests. No production release.')
    put(OUT/'verification/electrical_system.json',result);put(root/'electrical_budget.json',result);print('ELECTRICAL',result['status'],criteria,'sensor min',sensormin,'logic margin',logic_output_min-logic_input_required,flush=True)
if __name__=='__main__':main()
