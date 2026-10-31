"""Measured layout/codec evidence plus openly parameterized engineering estimates."""
from revo4_evidence import *
import math,struct,zlib
def dims(b):return [b[i+3]-b[i] for i in range(3)]
def main():
 v,o=run_paths();er=ArtifactReader('electronics');pr=ArtifactReader('pcba_geometry');lr=ArtifactReader('remote_link');kr=ArtifactReader('packaging')
 e=er.json(v/'electronics.json');p=pr.json(v/'pcba_geometry.json');pack=kr.json(v/'packaging.json');native=lr.path(o/'remote_link/pdr4_golden.bin').read_bytes()
 assert len(native)==80 and native[:4]==b'PDR4'
 assert zlib.crc32(native[:-4])&0xffffffff==struct.unpack_from('<I',native,76)[0]
 duration,*words=struct.unpack_from('<I4H',native,64);assert duration==300000 and words==[0,0x8000,0xc000,16383]
 geometry={q['kind']:q for q in p['boards']};boards=[]
 for q in e['boards']:
  g=geometry[q['kind']];j50=next(c for c in g['connectors'] if c['ref']=='J50');physical=dims(g['physical_with_declared_substitutes_bounds_mm'])
  service=[r['bounds_mm'] for r in g['objects'] if r['class'].startswith('physical') or r['class']=='service_sweep']
  sbb=[min(b[i] for b in service) for i in range(3)]+[max(b[i+3] for b in service) for i in range(3)]
  boards.append({'kind':q['kind'],'pcb_mm':q['board_mm'],'pcb_area_mm2':q['board_mm'][0]*q['board_mm'][1],'components':len(q['components']),'placement':q['placement_status'],'checks':q['checks'],'physical_dimensions_mm':physical,'physical_bbox_mm3':math.prod(physical),'R4_dimensions_mm':g['bend_sensitivity']['4']['dimensions_mm'],'R12_dimensions_mm':g['bend_sensitivity']['12']['dimensions_mm'],'with_service_dimensions_mm':dims(sbb),'J50_mating_width_mm':j50['housing_width_mm'],'unqualified_models':g['missing_or_unqualified_components']})
 # Five validated register reads per axis, 2 x 16 bits/read + 3 us GPIO gaps/word.
 # Match O3 diagnostic policy; slower scans do not permit silently dropping error checks.
 per_axis_us=10*(16/250000*1e6+3);serial_us=148*10/115200*1e6;remote_us=serial_us+4*per_axis_us+2000
 timing={'scope':'SERIALIZATION_AND_SCHEDULING_ASSUMPTION_NOT_MEASURED_FIRMWARE','request_bytes':68,'response_bytes':80,'baud':115200,'framing':'8N1','link_serial_us':serial_us,'per_axis_wire_and_CS_us':per_axis_us,'diagnostic_register_reads_per_axis':5,'remote_read_wire_CS_us':4*per_axis_us,'remote_attempt_with_assumed_2ms_turnaround_scheduler_us':remote_us,'one_arm_sequential_five_local_plus_remote_us':5*per_axis_us+remote_us,'all41_serial_SPI_base_us':41*per_axis_us,'two_remote_links_serial_extra_us':2*(serial_us+2000),'conservative_all41_plus_two_links_us':41*per_axis_us+2*(serial_us+2000),'two_retry_one_link_sensitivity_us':41*per_axis_us+2*(serial_us+2000)+2*remote_us,'CAN_gateway_USB_and_OS_us':'NOT_MEASURED_NOT_INCLUDED','max_extra_retries_per_node_per_transaction':2,'no_per_scan_retry_reset':True,'qualification':'No schedulability proof; retire incomplete scans, never reuse previous angles'}
 # Copper resistivity parameter, not a cable manufacturer's certified limit.
 wire_rows=[]
 for awg in (26,28,30):
  diameter=.127*92**((36-awg)/39);area=math.pi*diameter**2/4;r20=.017241/area
  for length in (.3,.6):
   for temp in (20,60):
    for current in (.1,.2,.25):
     loop=2*length*r20*(1+.00393*(temp-20));contacts=4*.02;switch=.135;other=.05
     remote=3.3*.95-current*(loop+contacts+switch+other)
     wire_rows.append({'AWG':awg,'one_way_length_m':length,'copper_C':temp,'load_A':current,'loop_ohm':loop,'remote_V':remote,'margin_to_3V_V':remote-3,'passes_voltage_only':remote>=3})
 ilim={'resistor_kohm':100,'tolerance_fraction':.01,'min_mA':25230/101**1.016,'typ_mA':23950/100**.977,'max_mA':22980/99**.94,'formula_source':'TI TPS2553 SLVS841F section 9.2.1 equations 1','warning':'Current-limit protection cannot compensate voltage drop; startup/inrush and thermal cycling untested'}
 power={'scope':'PARAMETRIC_DC_DROP_SENSITIVITY_NOT_SUPPLY_QUALIFICATION','source_min_V':3.3*.95,'AS5048_3V_min_V':3.0,'sensor_four_max_mA':4*15,'additional_load_budget':'MCU, transceiver, buffers, terminations, wiring and inrush unresolved; sweep 100/200/250mA','TPS2553_DBV_Ron_max_ohm':.135,'per_contact_ohm_assumed':.02,'four_series_mated_contacts':True,'PCB_path_ohm_assumed':.05,'wire_material':'copper, rho20=.017241 ohm mm2/m, alpha=.00393/K; actual stranded cable must be measured','current_limit':ilim,'cases':wire_rows,'failed_voltage_cases':sum(not q['passes_voltage_only'] for q in wire_rows),'recommendation':'Qualify short 26 AWG 3V3 path first. If transient/margin fails, study 5V plus local regulator as a separate sized/power-qualified variant; do not silently change J50 pinout'}
 # Equivalent packed area only; does not model cable jacket or torsional bending stiffness.
 bundle={'J50_A_conductors':14,'J50_C_conductors':4,'J50_reduction_percent':100*(14-4)/14,'other_shoulders_conductors':'UNCHANGED; actual multi-axis route is not yet frozen','same_OD_assumption_mm':.8,'packing_fraction_assumed':.7,'A_equivalent_bundle_mm':.8*math.sqrt(14/.7),'C_equivalent_bundle_mm':.8*math.sqrt(4/.7),'qualification':'AREA_PROXY_ONLY_NOT_MIN_BEND_RADIUS_OR_TORQUE','electrical_nodes':{'processors':9,'CAN_nodes':7,'logical_regions':6,'measured_axes':41}}
 result={'schema':'o4-hardware-comparison-v1','boards':boards,'timing':timing,'power':power,'harness':bundle,'C_host_codec_python_crosscheck':'PASS','native_duration_us':duration,'packaging_screen_failures':{c['character']:sum(q['fit_status'].startswith('FAIL') for q in c['placements']) for c in pack['characters']},'full_arm_assembled':False,'physical_tested':False,'manufacturing_released':False,'conclusion':'C reduces J50 and fits two remote placement candidates, but routing, net 3D packaging, power transient and loaded motion remain blockers. Retain A as fallback.','sources':{'STM32':'https://www.st.com/resource/en/datasheet/stm32c011f6.pdf','THVD1400':'https://www.ti.com/lit/ds/symlink/thvd1400.pdf','JST':'https://www.jst-mfg.com/product/pdf/eng/eSH.pdf','TPS2553':'https://www.ti.com/lit/ds/symlink/tps2553.pdf','AS5048':'https://look.ams-osram.com/m/287d7ad97d1ca22e/original/AS5048-DS000298.pdf'},'consumed_inputs':[er.receipt(),pr.receipt(),lr.receipt(),kr.receipt()]}
 save(v/'hardware_comparison.json',result)
 print('codec crosscheck PASS; boards',len(boards),'voltage failures',power['failed_voltage_cases'],'of',len(wire_rows))
if __name__=='__main__':main()
