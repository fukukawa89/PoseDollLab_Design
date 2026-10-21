"""Traceable 6-chain harness cutting/binding plan; no cable compliance simulation."""
from common import *
from layout_fullbody import build,fk
from carriers_swept import ASSEMBLY_POSE,motion_bank
from raw_paths import paths
from fitted import fit_inputs

def main():
 wiring=read(OUT/'raw46_wiring_candidate.json');allrows=[]
 for char in ('quinn','manny'):
  ports,digest=fit_inputs(char);_,m0,_,_,pr=build(char,ASSEMBLY_POSE,geometry=False);T0,_=fk(pr,ASSEMBLY_POSE);entry=next(x for x in read(OUT/f'equipment/{char}_search.json')['entries'] if x['kind']=='controller');F=np.c_[[0,1,0],[0,0,-1],[-1,0,0]];o=np.array(entry['front_center_world_mm'])-F@np.array([35,30,0]);bank=motion_bank(char)+[(n,m,T) for n,m,T,d in paths(char)];rows=[];branch_results=[]
  for chain in wiring['chains']:
   ci=chain['chain'];nodes=chain['nodes'];socket=np.array([-10 if ci<=3 else 80,[10,29,48][(ci-1)%3],9.5]);jlocal=np.linalg.inv(T0['chest'])@np.r_[F@socket+o,1];keys=[None]+[r['part'] for r in nodes];segments=[]
   for j,(a,b) in enumerate(zip(keys,keys[1:])):
    maximum=0.;witness=None;minspan=float('inf');initial=None
    for label,m,T in bank:
     A=(T['chest']@jlocal)[:3] if a is None else (m[a]['transform']@np.r_[ports[a]['end_local_mm'],1])[:3];B=(m[b]['transform']@np.r_[ports[b]['end_local_mm'],1])[:3];distance=float(np.linalg.norm(B-A));minspan=min(minspan,distance)
     if label=='assembly':initial=[A.tolist(),B.tolist()]
     if distance>maximum:maximum=distance;witness=label
    # Reserve one full external service loop plus detour/termination room.
    # This is a cut-length basis, not a solved cable route or proof of no snags.
    reserve=2*math.pi*12+35;cut=math.ceil((maximum+reserve)/10)*10
    segments.append({'segment':f'J{ci}-S{j:02}','from':'controller/J'+str(ci) if a is None else nodes[j-1]['label'],'to':nodes[j]['label'],'from_part':a,'to_part':b,'span_max_mm':maximum,'span_min_mm':minspan,'witness_pose':witness,'loop_radius_target_mm':12,'detour_and_termination_reserve_mm':35,'cut_length_each_conductor_mm':cut,'assembly_endpoints_mm':initial,'conductors':['GND 24AWG black','VCC3V3 24AWG red','SCK 30AWG blue','CS_N 30AWG yellow','FORWARD 30AWG white','RETURN 30AWG green']})
   # Worst rated wire resistance at elevated temperature: AWG24 .0842 ohm/m at20C.
   # Use 25% increase, 15mA per board and .10ohm total supply+return per splice. Continuous rails use <=.01ohm pair tap/splice allowance; only one GH connector pair .08ohm.
   n=len(nodes);cumulative=.015*n*(.10+2*.134*1.25*.04+.01) # one GH supply/return contact pair at controller
   for j,s in enumerate(segments):
    remaining=n-j;current=.015*remaining;Rpair=2*.0842*1.25*s['cut_length_each_conductor_mm']/1000;cumulative+=current*(Rpair+.01);s['downstream_design_current_A']=current;s['supply_return_drop_V']=current*(Rpair+.01)
   trace=read(H/'electronics/revO15/central_c1/power_trace_resistance.json');rr=trace['branches'] if 'branches' in trace else trace
   # Explicit independently exported routed minimum-path values; checked against report below.
   assert trace['board_sha256']==sha(H/'electronics/revO15/central_c1/PoseDoll_O15_Central_C1.kicad_pcb');copper=next(r['copper_path_ohm_at_60C_bound'] for r in trace['branches'] if r['branch']==ci);switch_drop=.015*n*.135;board_drop=.015*n*copper
   tail_drop=.015*(2*.539*1.25*.04+.35);extra_common_drop=.03;voltage=3.3*.96-switch_drop-board_drop-cumulative-tail_drop-extra_common_drop
   branch_results.append({'chain':ci,'boards':n,'allocated_current_A':.015*n,'wire_and_splice_drop_V':cumulative,'switch_max_drop_V':switch_drop,'actual_copper_drop_V':board_drop,'local_tail_drop_V':tail_drop,'common_rail_allowance_V':extra_common_drop,'controller_GH_pigtail':'40mm AWG26, insulation OD.76..1.0mm, SSHL-002T-P0.2 terminals; splice to continuous24AWG rails outside connector; contact pair .10ohm after-test budget','conditional_far_end_min_V':voltage,'AS5048A_min_V':3.,'conditional_margin_V':voltage-3.,'conditional_budget_ok':voltage>=3.})
   rows.append({'chain':ci,'sensor_nodes':nodes,'segments':segments,'power_result':branch_results[-1]})
  allrows.append({'character':char,'chains':rows,'power_results':branch_results,'tail_report_sha256':digest})
 report={'status':'CUT_LENGTH_AND_PIN_BINDING_PLAN','characters':allrows,'scope':'689 discrete poses bound terminal straight-line separation. External loose service loops add reserve. No computed elastic cable shape, bend force, fatigue or moving-wire collision proof. Adjust loop placement on complete assembled prototype.','no_automatic_hardware_pass':True,'wire_specs':{'power':'24 AWG multi-strand silicone, conductor DC resistance <=0.0842 ohm/m at20C; OD<=1.6mm','signal':'30 AWG multi-strand flexible insulated, OD<=.9mm','local_pigtail':'6x32 AWG, OD<=.55mm, <=40mm from FFC transition to splice; no moving bend at solder','static_FFC':'6P pitch.5mm width3.5mm thickness.2mm, nominal15mm; 2.15mm insertion, terminal stiffeners>=3.5mm; formed once radius2mm, supplier must accept bend geometry','controller_connector':'GHR-06V-S with SSHL-002T-P0.2, AWG26 power/30signal, insulation OD.76..1.0mm; 40mm power leads adapt to24AWG outside housing, never crimp24AWG in GH. PH PHR-2/3 uses SPH-002T-P0.5S, AWG24, insulation OD.8..1.5mm.', 'sources':['https://www.jst-mfg.com/product/pdf/eng/eGH.pdf','https://www.jst-mfg.com/product/pdf/eng/ePH.pdf'], 'termination':'Continuous 24AWG supply and ground rails with soldered taps, not a series of removable connectors. Main GH contact pair after-test budget .10ohm; each through tap pair <=.01ohm at elevated temperature. Factory assemble and electrically test labeled harness. Individual heatshrink insulation; no exposed splices. Route RETURN bypass past intermediate boards; do not short pin4 to pin5.'},'inputs_sha256':{str(p):sha(p) for p in [Path(__file__),OUT/'raw46_wiring_candidate.json',H/'electronics/revO15/central_c1/power_trace_resistance.json']}}
 save('harness/cut_and_binding_plan.json',report);BENCH.joinpath('harness').mkdir(exist_ok=True);BENCH.joinpath('harness/cut_and_binding_plan.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf8');print([(r['character'],[round(v['conditional_far_end_min_V'],3) for v in r['power_results']]) for r in allrows])
if __name__=='__main__':main()
