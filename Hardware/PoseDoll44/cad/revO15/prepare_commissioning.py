"""Create honest incomplete commissioning forms; never invent measured calibration."""
from common import *
from layout_fullbody import build
import re,argparse

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--body-mac');ap.add_argument('--gateway-mac');ap.add_argument('--out',type=Path,default=BENCH/'commissioning');a=ap.parse_args();a.out.mkdir(parents=True,exist_ok=True)
 mapping=OUT/'raw46_mapping_candidate.json';wiring=OUT/'raw46_wiring_candidate.json';w=read(wiring)
 if bool(a.body_mac)!=bool(a.gateway_mac):raise ValueError('Provide both MAC addresses together')
 device=None
 if a.body_mac:
  mac=lambda s:bool(re.fullmatch(r'(?:[0-9A-Fa-f]{2}:){5}[0-9A-Fa-f]{2}',s)) and s!='00:00:00:00:00:00' and not int(s[:2],16)&1
  if not mac(a.body_mac) or not mac(a.gateway_mac) or a.body_mac.lower()==a.gateway_mac.lower():raise ValueError('Distinct real unicast factory MACs required')
  # Firmware device_id shifts the 6 MAC bytes in network order into uint64_t.
  device=str(int.from_bytes(bytes.fromhex(a.body_mac.replace(':','')),'big'))
  for role,peer in [('BODY',a.gateway_mac),('G0',a.body_mac)]:
   src=R/'Firmware/PoseDollFullBody/revO15'/('sdkconfig.'+role+'.defaults');text='\n'.join(line for line in src.read_text().splitlines() if not line.startswith('CONFIG_P15_PEER_MAC='));text+='\nCONFIG_P15_PEER_MAC="'+peer.upper()+'"\n';(a.out/('sdkconfig.'+role+'.paired.defaults')).write_text(text)
 cal={'schema':'O15-RAW-CALIBRATION/1','body_device':device,'source_kind':'hardware','mapping_sha256':sha(mapping),'wiring_sha256':sha(wiring),'physical_tests':{k:False for k in ['individual_chain_binding','magnet_and_raw_calibration','disconnect_and_brownout','far_end_voltage_and_spi','complete_wired_motion']},'raw':{rid:{'zero_deg':None,'sign':None,'measurement_evidence':None} for rid in w['raw_order']},'status':'INCOMPLETE_TEMPLATE_DO_NOT_USE_FOR_CAPTURE'}
 (a.out/'raw_calibration_INCOMPLETE.json').write_text(json.dumps(cal,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
 rows=[]
 for char in ('quinn','manny'):
  _,_,states,f,_=build(char,{},geometry=False);assert not f
  rows.append({'character':char,'neutral_reference_raw_axes':[{'module':m['id'],'expected_degrees':m['angles_deg'],'world_mount':m['world_mount'],'origin_mm':m['origin_mm']} for m in states]})
 (a.out/'neutral_raw_reference.json').write_text(json.dumps({'scope':'CAD angular references only, not measured encoder zeros. Read real raw counts at mechanically verified reference and a known positive offset.','characters':rows},ensure_ascii=False,indent=2)+'\n',encoding='utf8')
 print('Commissioning templates saved. Hardware capture stays disabled until real evidence is entered.')
if __name__=='__main__':main()
