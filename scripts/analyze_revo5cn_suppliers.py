"""Reproducible conditional supplier comparison; no inferred prices or physical passes."""
from pathlib import Path
import json,hashlib,itertools,math
R=Path(__file__).resolve().parents[1];HW=R/'Hardware/PoseDoll44';OUT=HW/'verification/revO5CN/runs/cn_20260924_r1'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def save(p,d):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def main():
 paths=[Path(__file__),HW/'references/revO5CN/supplier_comparison.json',HW/'mechanical_manifest/requirements_revO5CN.json',HW/'mechanical_manifest/connector_wire_contract_revO5.json',HW/'generated/revO5/runs/o5_20260924_r1/arm/shared_arm_screen.json',HW/'electronics/sensor_revO5CN/result.json',HW/'generated/revO5CN/runs/cn_20260924_r1/cad_screen.json']
 hashes={p.relative_to(R).as_posix():sha(p) for p in paths};sources,contract,wire,arm,pcb,cad=map(read,paths[1:]);w=wire['selected_wire_candidate']
 rows=[]
 for supplier in sources['records']:
  f=supplier.get('facts',{});od=f.get('OD_nominal_mm');limit=f.get('insulation_OD_max_mm')
  if od is not None:
   upper=od+f['OD_tolerance_mm'] if 'OD_tolerance_mm' in f else None
   state='REJECT' if od>.8 or (upper is not None and upper>.8) else 'UNKNOWN_MAX_OD'
   rows.append({'candidate':supplier['id'],'nominal_OD_mm':od,'upper_OD_mm':upper,'terminal_max_OD_mm':.8,'result':state,'no_flex_qualification':True})
  elif limit is not None:
   rows.append({'candidate':supplier['id'],'wire_upper_OD_mm':w['insulation_OD_mm_range'][1],'terminal_max_OD_mm':limit,'OD_only_result':'PASS_CATALOG_ONLY' if w['insulation_OD_mm_range'][1]<=limit else 'REJECT'})
 # Freeze the wire/current/route conditions when comparing connector brands.
 # CJT additionally publishes <=10mOhm per crimp. Count four crimps in the loop.
 power=[];source=3.135
 for c in arm['characters']:
  length=next(v['max_J50_draft_length_mm'] for v in c['variants'] if v['variant']=='C')/1000
  for current,contact,crimp in itertools.product((.1,.2,.25),(.02,.04),(0.,.01)):
   rw=2*length*w['nominal_conductor_DCR_ohm_per_m']*1.1*(1+.00393*40)
   total=rw+4*contact+4*crimp+.135+.05;voltage=source-current*total
   power.append({'character':c['character'],'one_way_draft_m':length,'load_A':current,'temperature_C':60,'DCR_factor':1.1,'each_contact_ohm':contact,'each_crimp_ohm':crimp,'remote_V':voltage,'meets_3V_minimum':voltage>=3,'meets_3V05_reserve':voltage>=3.05,'current_limit_guaranteed_by_O5_min':current*1000<25230/101**1.016,'scope':'Hypothetical CJT J50 pair; J50 has NOT been replaced or routed. 0 crimp case is optimistic only.'})
 sensor={'axis_ports':41,'per_port_before':6,'per_port_after':5,'conductor_segments_before':246,'conductor_segments_after':205,'conductor_segments_saved':41,'cross_section_sum_reduction_fraction':1-5/6,'assumes_equal_wire_OD_and_equal_route':True,'does_not_count_shared_bus_or_CAN_trunks':True,'J50_before':4,'J50_after':4,'wire_only_bits_per_axis_before':160,'wire_only_bits_per_axis_after':24,'clock_only_scan_41_at_250k_us_before':41*160/250000*1e6,'clock_only_scan_41_at_250k_us_after':41*24/250000*1e6,'not_actual_scan_latency':True,'SSI_resolution_deg_per_count':360/16384,'resolution_is_not_accuracy':True,'new_INL_typ_max_deg':[1,1.5],'board_area_changed':False,'must_not_claim_smaller_joint':True}
 result={'schema':'cn1-supplier-analysis-v1','input_sha256':hashes,'supplier_count':len(sources['records']),'wire_terminal_screens':rows,'sensor_change':sensor,'power_sensitivity':power,'CJT_28AWG_crimp_reference':{'strip_mm':[1.2,1.7],'height_mm':[.46,.54],'pull_min_N':9.80665,'qualification':'Reference only; requires exact wire/process validation'},'spring_substitute':cad['spring_direct_swap'],'PCB_checks':pcb['checks'],'physical_tested':False,'manufacturing_released':False,'decisions':{'MT6701':'Worth independent five-wire trial; production replacement not justified yet','CJT':'Worth domestic matched-pair sourcing trial; no power/size/cost superiority claimed','wire':'Keep Alpha comparison baseline; tested Chinese catalog wires fail OD or lack tolerance/flex evidence','spring':'Keep original reference; tested 12.5 mm domestic row interferes with guide','manufacturing':'Prepare domestic RFQ/DFM route; no quotations sent or supplier capability approved'},'unknown_commercial':['Unit prices at prototype/41-axis quantity','Available lot/leadtime/MOQ','Matched crimp tooling/setup cost','Yield and lifetime']}
 for name,h in hashes.items():assert sha(R/name)==h,name
 save(OUT/'supplier_analysis.json',result);print(json.dumps({'supplier_count':result['supplier_count'],'saved_conductor_segments':sensor['conductor_segments_saved'],'PCB_checks':pcb['checks'],'spring':cad['spring_direct_swap']['status']},indent=2))
if __name__=='__main__':main()
