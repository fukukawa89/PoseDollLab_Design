"""Deterministic binding of every modeled PCBA to one physical chain position."""
from common import *
from layout_fullbody import build


def make():
 _,parts,states,fail,_=build('quinn',{},geometry=False);assert not fail
 modules={m['id']:m for m in states}
 chains=[['waist','chest'],['head'],['clavicle_l.protract','clavicle_l.elevate','upperarm_l','elbow_l.flex','forearm_l.twist','hand_l.flex','hand_l.deviate'],['clavicle_r.protract','clavicle_r.elevate','upperarm_r','elbow_r.flex','forearm_r.twist','hand_r.flex','hand_r.deviate'],['thigh_l','calf_l.flex','foot_l','ball_l.flex'],['thigh_r','calf_r.flex','foot_r','ball_r.flex']]
 rows=[];flat=[]
 for ci,seq in enumerate(chains):
  nodes=[]
  for name in seq:
   m=modules[name];kind=m['kind'];keys=['P_sensor_PCB','C01_sensor_PCB','C02_sensor_PCB','D_sensor_PCB'] if kind in ('tut','wide_tut') else ['P_sensor_PCB','C01_sensor_PCB','C02_sensor_PCB'] if kind=='three_axis' else ['C01_sensor_PCB','C02_sensor_PCB'] if kind in ('core','ankle_core','clavicle_core') else ['sensor_PCB']
   for j,k in enumerate(keys):
    part=name+'/'+k;assert parts[part]['sku']=='AS5048A_MINI_PCBA'
    row={'raw_index':len(flat),'raw_id':name+'/r'+str(j),'chain':ci+1,'position_nearest_controller_zero_based':len(nodes),'part':part,'label':f'J{ci+1}.{len(nodes)+1:02}'};flat.append(row);nodes.append(row)
  rows.append({'chain':ci+1,'count':len(nodes),'nodes':nodes})
 assert [r['count'] for r in rows]==[6,4,10,10,8,8]
 assert len(flat)==46 and len({x['part'] for x in flat})==46
 assert {x['part'] for x in flat}=={k for k,m in parts.items() if m['sku']=='AS5048A_MINI_PCBA'}
 d={'schema':'O15-RAW-WIRING/1','status':'CENTRAL_DAISY_CANDIDATE_NOT_PHYSICALLY_BOUND','chains':rows,'raw_order':[r['raw_id'] for r in flat],'counts':[r['count'] for r in rows],'sensor_connector_pinout':{'1':'GND','2':'3.3V branch','3':'SCK','4':'previous MISO / MCU MOSI for first','5':'next MOSI / RETURN for last','6':'CS_N'},'trunk_six_conductors':['GND','3.3V','SCK','CS_N','forward data between adjacent sensors','last-MISO RETURN bypassing intermediate sensors'],'sequential_read_bursts':6,'on_fault_only_error_clear_bursts':2,'worst_wire_time_including_clear_ms':46*16*8/100000*1000,'spi_hz_candidate':100000,'nominal_wire_bits':46*16*6,'nominal_wire_time_ms':46*16*6/100000*1000,'physical_tests_required':['rotate one joint at a time to identify every actual chain position','verify board direction, magnet polarity, raw zero and sign','disconnect each chain segment and each sensor power tap','oscilloscope SPI and far-end supply at maximum load','cold start, brownout, body/gateway reboot and replay faults'],'source_sha256':{str(p):sha(p) for p in [Path(__file__),Path(__file__).with_name('layout_fullbody.py')]}}
 save('raw46_wiring_candidate.json',d);return d
if __name__=='__main__':d=make();print('RAW WIRING',d['counts'],len(d['raw_order']),d['nominal_wire_time_ms'])
