"""Analyze a saved PD41 capture. No serial ports, firmware flashing, or live capture."""
from revo2_evidence import *
import argparse
sys.path.insert(0,str(REPO/'Tools/PoseDollHardwareBridge'))
from pd41_protocol import Decoder

def metrics(data):
 decoder=Decoder();frames=decoder.feed(data);n=len(frames)
 expected=max((frames[-1]['sequence']-frames[0]['sequence']+1),n) if n else 0
 presence=sum(f['node_presence_mask']==63 for f in frames)
 normal=sum(f['pose_valid'] for f in frames)
 in_window=sum(f['pose_valid'] and all(delay+span<=8000 and span>0 for delay,span in f['node_timing_us']) for f in frames)
 return {'accepted_frames':n,'expected_by_sequence':expected,'malformed_stale_or_changed_session_frames':decoder.errors,'unfinished_trailing_frame':bool(decoder.buffer),'presence_complete_frames':presence,'all_41_angles_normal_frames':normal,'normal_and_node_window_frames':in_window,'presence_complete_rate':presence/expected if expected else None,'fresh_complete_normal_rate':in_window/expected if expected else None,'status':'NO_VALID_CAPTURE' if not n else 'CAPTURE_ANALYZED_NOT_END_TO_END_TIMING_PROOF','period_exclusions':None,'physical_CAN_END_14ms_deadline_verified':False,'hardware_30min_soak_pass':False,'note':'Every captured recovery/fault cohort is included. The 14 ms CAN completion deadline requires a synchronized bus trace; presence alone never proves valid angles.'}

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--input',type=Path,required=True);ap.add_argument('--output',type=Path,required=True);a=ap.parse_args();result=metrics(a.input.read_bytes());result['capture_sha256']=sha(a.input);save(a.output,result);print(json.dumps(result,ensure_ascii=False))
if __name__=='__main__':main()
