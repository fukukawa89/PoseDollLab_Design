"""Static low duty cycle does not reduce peak supply current; conditional O6 screen."""
from pathlib import Path
import itertools,json,hashlib,argparse
R=Path(__file__).resolve().parents[1];H=R/'Hardware/PoseDoll44'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--out',type=Path,required=True);a=ap.parse_args()
 p=H/'mechanical_manifest/connector_wire_contract_revO5.json';c=json.loads(p.read_text());r20=c['selected_wire_candidate']['nominal_conductor_DCR_ohm_per_m']
 allocations={'AS5048_4x15mA':.060,'STM32C011_MCU_allocation_NOT_datasheet_max':.010,'THVD_quiescent_allocation':.003,'driver_resistive_54ohm_upper_at_3V6':3.6/54,'pullups_buffers_allocation':.005}
 budget=sum(allocations.values());rows=[]
 for L,T,I in itertools.product((.15,.305,.45,.6),(20,60),(.1,.15,.2,.25)):
  rw=2*L*r20*(1+.00393*(T-20))*1.1;fixed=.16+.135+.05+.04;v=3.135-I*(rw+fixed)
  rows.append({'one_way_length_m':L,'temperature_C':T,'peak_current_A':I,'remote_V':v,'R_loop_ohm':rw+fixed,'voltage_3V_met':v>=3.,'engineering_3V05_met':v>=3.05})
 out={'schema':'o6-peak-power-budget-v1','allocations_A':allocations,'sum_A':budget,'proposed_engineering_peak_allocation_A':.15,'allocation_is_verified_peak':False,'cases':rows,'separate_crimp_4x10mohm_is_sensitivity_NOT_JST_guarantee':True,'CJT_terminal_data_does_not_qualify_JST_crimps':True,'driver_load_basis':'3.6 V divided by 54 ohm is a resistor-path ceiling in the declared healthy termination case; excludes shorts/inrush/transients','device_current_basis':[{'part':'AS5048','fact':'15 mA maximum operating supply, four sensors 60 mA','url':'https://look.ams-osram.com/m/287d7ad97d1ca22e/original/AS5048-DS000298.pdf','document_download':'Restricted at official asset endpoint; primary indexed excerpt read, no bypass.'},{'part':'STM32C011','fact':'Rev5 table27 48MHz flash max4.9mA characterized with peripherals disabled; not a whole-board current ceiling','url':'https://www.st.com/resource/en/datasheet/stm32c011f6.pdf'},{'part':'THVD1400','fact':'No-load quiescent current is not terminated driving current. Load included separately.','url':'https://www.ti.com/lit/ds/symlink/thvd1400.pdf'}],'decision':'Keep present 3V3 keyed interface and 200/250mA stress cases. 150mA is a conditional design budget, not a reason to mark longer wires qualified. No 5V applied to existing 3V3 connector.','static_sampling_reduces_average_not_peak':True,'physical_tested':False,'manufacturing_released':False,'input_sha256':{p.relative_to(R).as_posix():sha(p),Path(__file__).relative_to(R).as_posix():sha(Path(__file__))}}
 a.out.parent.mkdir(parents=True,exist_ok=True);a.out.write_text(json.dumps(out,indent=2)+'\n',encoding='utf-8');print('conditional budget',budget);print([x for x in rows if x['one_way_length_m']==.305 and x['temperature_C']==60])
if __name__=='__main__':main()

