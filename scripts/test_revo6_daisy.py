"""Independent fixed words, pipeline/order checks, injected faults and known blind spots."""
from pathlib import Path
import sys,json,hashlib,itertools
R=Path(__file__).resolve().parents[1];H=R/'Hardware/PoseDoll44'
sys.path.insert(0,str(R/'Firmware/PoseDollFullBody/revO6'))
from daisy_chain_trial import *
def pack(v):return v|(0x8000 if bin(v).count('1')%2 else 0)
def frame(angles):
 # Values are specified in physical near-to-far order, serialized far-to-near.
 n=len(angles)
 return [[0xABCD]*n,[0x8100]*n,[0x9000]*n,list(reversed([pack(v) for v in angles])),[0]*n,[0]*n]
def main():
 out=H/'verification/revO6/runs/o6_20260924_r1/daisy';out.mkdir(parents=True,exist_ok=True)
 assert [command(r) for r in REGISTERS]==[0x7FFD,0x7FFE,0xFFFF,0x4016,0xC017]
 positive=0;mutations=0;shape=0
 for n in (1,3,6,7,9):
  angles=[(7919*i+1234)&0x3FFF for i in range(n)];rx=frame(angles);s=decode_pipeline(rx,n);assert s.angles==tuple(angles) and s.mathematically_valid and not s.capture_eligible;positive+=1
  for burst,port,bit in itertools.product(range(1,6),range(n),range(16)):
   bad=[r.copy() for r in rx];bad[burst][port]^=1<<bit
   assert not decode_pipeline(bad,n).mathematically_valid;mutations+=1
  for bad in [rx[:-1],rx+[[0]*n],[r[:-1] for r in rx]]:
   try:decode_pipeline(bad,n)
   except ValueError:shape+=1
   else:raise AssertionError('accepted incomplete chain response')
  assert not decode_pipeline([[0]*n for _ in range(6)],n).mathematically_valid
  assert not decode_pipeline([[0xFFFF]*n for _ in range(6)],n).mathematically_valid
 # Explicitly demonstrate limitations instead of turning parser passes into
 # complete physical-count/liveness guarantees.
 nominal=frame([100+i for i in range(9)])
 replay=decode_pipeline(nominal,9)
 duplicated=[r.copy() for r in nominal]
 for r in duplicated:r[0]=r[1]
 duplicate=decode_pipeline(duplicated,9)
 two_bit=[r.copy() for r in nominal];two_bit[3][0]^=3
 undetected=decode_pipeline(two_bit,9)
 assert replay.mathematically_valid and duplicate.mathematically_valid and undetected.mathematically_valid
 assert all(not s.capture_eligible for s in (replay,duplicate,undetected))
 try:TrialScan((1,),(0,),True,True)
 except ValueError:shape+=1
 else:raise AssertionError('experimental capture enabled')
 timing=[]
 for hz in (25000,50000,100000,250000):
  # Five required register reads + final NOP; no stale-response reuse. Six CS
  # frames per region. 3us per burst is an assumption, no SDK/driver latency.
  for counts in [(3,6,9,9,7,7)]:
   region_ms=[6*16*n/hz*1000+6*.003 for n in counts]
   timing.append({'SPI_clock_Hz':hz,'region_lengths':list(counts),'ideal_plus_CS_fullscan_ms':sum(region_ms),'max_region_ms':max(region_ms),'fullscan_100ms_budget_met':sum(region_ms)<=100,'region_20ms_budget_met':max(region_ms)<=20,'electrical_or_driver_timing_qualified':False})
 # 4 communication signals + V/GND = six conductors. Not four total wires.
 result={'schema':'o6-DC1-digital-experiment-v1','valid_chain_length_cases':positive,'single_bit_faults_rejected':mutations,'bad_shape_or_capture_enable_rejected':shape,'all_zero_and_all_one_rejected':True,'known_undetectable_counterexamples':['Whole valid replay without independent sample age/binding','Duplicated valid physical response column; physical sensor count not proven','Even-bit angle mutation can retain valid parity'],'timing':timing,'hypothetical_harness_conductors_per_serial_segment_including_power':6,'source':'https://look.ams-osram.com/m/d6b55afbdfe4b3d0/original/AS5048_UG000223_1-00.pdf','source_access':'Official indexed section 4.3 read; direct document fetch returned 404. No mirrored source used.','pipeline_basis':'n x 16-bit read command, next n x 16-bit transfer returns previous register; physical near/far mapping is a declared fixture hypothesis requiring bench verification','register_policy_inherited_from':'Firmware/PoseDollFullBody/revO5/main/main.c','capture_eligible':False,'connected_to_production_firmware':False,'physical_tested':False,'new_central_PCB_exists':False,'decision':'Worth investigating for a smaller back controller and loom; retain current A baseline. Do not qualify six physical regions merely by decoding six logical records.','open':['Actual chain order/count and fault isolation','Clock/data integrity on flexing harness and return conductor','Power drop/inrush and branch protection','Connector/splice envelopes; no free volume credit from wire count','Native central PCB/RF/thermal/protection layout','Reboot, stale-frame and host transaction integration'],'input_sha256':{str(p.relative_to(R)).replace('\\','/'):hashlib.sha256(p.read_bytes()).hexdigest() for p in (Path(__file__),R/'Firmware/PoseDollFullBody/revO6/daisy_chain_trial.py',R/'Firmware/PoseDollFullBody/revO5/main/main.c')}}
 (out/'results.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
 print(json.dumps({k:result[k] for k in ('valid_chain_length_cases','single_bit_faults_rejected','bad_shape_or_capture_enable_rejected','capture_eligible','timing')},indent=2))
if __name__=='__main__':main()

