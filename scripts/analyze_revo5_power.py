"""Recompute the O5 conditional DC power sweep; no physical qualification."""
from pathlib import Path
import json,itertools,argparse,hashlib
ROOT=Path(__file__).resolve().parents[1]
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--out',type=Path,required=True);ap.add_argument('--arm',type=Path);a=ap.parse_args()
 path=ROOT/'Hardware/PoseDoll44/mechanical_manifest/connector_wire_contract_revO5.json';c=json.loads(path.read_text(encoding='utf-8'));w=c['selected_wire_candidate']
 assert w['AWG'] in c['terminal_allowed_AWG'] and .4<=w['insulation_OD_mm_range'][0]<=w['insulation_OD_mm_range'][1]<=.8
 rows=[];vmin=3.3*.95;ilim_min=25230/101**1.016;ilim_max=22980/99**.94;r20=w['nominal_conductor_DCR_ohm_per_m']
 for length,temp,current,rfactor in itertools.product((.15,.3,.45,.6),(20,60),(.1,.2,.25),(1.,1.1)):
  total=2*length*r20*(1+.00393*(temp-20))*rfactor+.04*4+.135+.05;v=vmin-current*total
  rows.append(dict(one_way_length_m_including_service_and_twist=length,temperature_C=temp,load_A=current,DCR_allowance_factor=rfactor,remote_V=v,minimum_device_V=3.,voltage_only_pass=v>=3.,reserve_50mV_pass=v>=3.05,below_minimum_current_limit=current*1000<ilim_min,total_resistance_ohm=total,distributed_I2R_W=current**2*total))
 limits=[]
 for current in (.1,.2,.25):
  per_m=2*r20*(1+.00393*40)*1.1
  limits.append(dict(load_A=current,max_one_way_length_for_3V_m=max(0,((vmin-3)/current-.345)/per_m),max_one_way_length_for_3V05_m=max(0,((vmin-3.05)/current-.345)/per_m),within_min_current_limit=current*1000<ilim_min))
 result=dict(schema='o5-power-sensitivity-v1',status='CONDITIONAL_NOT_SUPPLY_OR_THERMAL_QUALIFICATION',contract_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),source_min_V=vmin,required_remote_min_V=3.,engineering_reserve_target_V=.05,reserve_is_unqualified_design_allowance=True,R_on_TPS2553_DBV_max_ohm=.135,contact_after_environment_loop_ohm=.16,PCB_allowance_ohm=.05,separate_crimp_resistance_not_yet_known=True,current_limit_100k_1percent_mA=[ilim_min,ilim_max],cases=rows,failed_voltage_cases=sum(not x['voltage_only_pass'] for x in rows),failed_reserve_cases=sum(not x['reserve_50mV_pass'] for x in rows),conditional_length_limits=limits,static_retries_do_not_reduce_peak_current=True,RF_kept=True,physical_tested=False,unknowns=['Actual current/inrush','Actual longest route/service loop','Wire-lot DCR upper bound','Crimp resistance and process','Voltage/thermal/short-circuit waveforms'],decision='SH4/28 AWG candidate retained, manufacturing blocked. Independently keyed 5V/local regulation or qualified larger connector only if actual conditions require it; never apply 5V to current 3V3 interface.')
 if a.arm:
  arm=json.loads(a.arm.read_text(encoding='utf-8'));routes=[]
  for character in arm['characters']:
   variant=next(v for v in character['variants'] if v['variant']=='C');length=variant['max_J50_draft_length_mm']/1000
   for current in (.1,.2,.25):
    total=2*length*r20*(1+.00393*40)*1.1+.345;voltage=vmin-current*total
    routes.append(dict(character=character['character'],draft_one_way_length_m=length,temperature_C=60,load_A=current,DCR_allowance_factor=1.1,remote_V=voltage,voltage_only_pass=voltage>=3,reserve_50mV_pass=voltage>=3.05,below_minimum_current_limit=current*1000<ilim_min,route_qualified=False))
  result['shared_arm_draft']=dict(source_sha256=hashlib.sha256(a.arm.read_bytes()).hexdigest(),cases=routes,limitation='Polyline plus declared loop allowance only: no minimum-curvature/collision/flex certification; not the actual qualified longest wire')
 a.out.parent.mkdir(parents=True,exist_ok=True);a.out.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8');print('Conditional voltage failures:',result['failed_voltage_cases'],'/',len(rows))
if __name__=='__main__':main()
