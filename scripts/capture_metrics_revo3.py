"""Offline PD41 v1 metrics. USB G0 arrival envelopes and raw node sampling are distinct.
No live I/O. Explicit reconnect segments never silently change Decoder sessions.
"""
from revo3_evidence import *
import argparse, math
sys.path.insert(0,str(REPO/'Tools/PoseDollHardwareBridge'))
from pd41_protocol import Decoder, NODE_INDICES
PERIOD_US=1_000_000/60

def _rate(n,d):return n/d if d else None

def metrics(data,trace=None):
    decoder=Decoder();frames=decoder.feed(data);n=len(frames)
    elapsed=frames[-1]['sender_monotonic_us']-frames[0]['sender_monotonic_us'] if n>1 else 0
    expected_seq=frames[-1]['sequence']-frames[0]['sequence']+1 if n else 0
    expected_time=round(elapsed/PERIOD_US)+1 if n else 0
    denominator=max(expected_seq,expected_time,n)
    intervals=[b['sender_monotonic_us']-a['sender_monotonic_us'] for a,b in zip(frames,frames[1:])]
    presence=sum(f['node_presence_mask']==63 for f in frames)
    normal=sum(f['pose_valid'] for f in frames)
    # v1 timing contains G0 elapsed-to-END, not the node's delay/span.
    good=[f for f in frames if f['pose_valid'] and all(0<d+s<14000 for d,s in f['node_timing_us'])]
    nodes=[]
    for node,inds in NODE_INDICES.items():
        own=[f for f in frames if f['node_presence_mask']&(1<<(node-1)) and all(f['axes'][i]['status']=='valid' for i in inds) and 0<sum(f['node_timing_us'][node-1])<14000]
        stamps=[f['sender_monotonic_us'] for f in own]
        # Include missing data at both capture boundaries in the maximum gap.
        bounds=([frames[0]['sender_monotonic_us']]+stamps+[frames[-1]['sender_monotonic_us']]) if frames else []
        nodes.append({'node':node,'normal_fresh_frames':len(own),'rate_including_missing_fault_and_recovery':_rate(len(own),denominator),'max_no_update_gap_us':max((b-a for a,b in zip(bounds,bounds[1:])),default=None)})
    raw_status='NOT_OBSERVABLE';raw_report={'status':raw_status,'reason':'USB v1 does not carry original node delay/span; associated raw END/trace required.'}
    if trace is not None:
        raw_report=trace_metrics(frames,trace)
    hz=(n-1)*1_000_000/elapsed if elapsed>0 else None
    quality={'duration_at_least_30min':elapsed>=1800_000_000,'effective_rate_near_60Hz':hz is not None and 59.7<=hz<=60.3,'complete_fresh_rate_at_least_0999':bool(denominator) and len(good)/denominator>=.999,'no_decoder_rejections':decoder.errors==0 and not decoder.buffer,'raw_timing_complete':raw_report.get('status')=='PASS_ASSOCIATED_RAW_TRACE'}
    return {'schema':'revo3-capture-metrics-v1','status':'NO_VALID_CAPTURE' if not n else 'CAPTURE_ANALYZED_NOT_PHYSICAL_QUALIFICATION','session':list(decoder.identity) if decoder.identity else None,'accepted_frames':n,'expected_by_sequence':expected_seq,'expected_by_elapsed_60Hz':expected_time,'denominator_including_time_and_sequence_gaps':denominator,'capture_duration_s':elapsed/1_000_000,'effective_output_Hz':hz,'maximum_output_interval_us':max(intervals,default=None),'malformed_stale_or_changed_session_frames':decoder.errors,'unfinished_trailing_frame':bool(decoder.buffer),'presence_complete_frames':presence,'all_41_angles_normal_frames':normal,'normal_and_G0_envelope_frames':len(good),'presence_complete_rate':_rate(presence,denominator),'fresh_complete_normal_rate':_rate(len(good),denominator),'fresh_complete_by_sequence_only':_rate(len(good),expected_seq),'per_node':nodes,'node_8ms_and_G0_14ms_trace':raw_report,'maintenance_cohorts_from_USB_alone':'NOT_OBSERVABLE_USE_ASSOCIATED_GATEWAY_LOG','period_exclusions':None,'qualification_checks':quality,'hardware_30min_soak_pass':False,'note':'All loss, fault and recovery cohorts count. USB envelope <14 ms is a consistency check, not independent bus timing proof; 8 ms remains a separate limit.'}

def trace_metrics(frames,trace):
    """Trace records require an explicit USB sequence/session association.
    Raw CAN sequence alone is insufficient across an epoch reset.
    """
    index={};errors=[]
    for q in trace:
        try:
            key=(str(q['device_id']),str(q['boot_id']),int(q['usb_sequence']),int(q['node']))
            if key in index:raise ValueError('duplicate trace key')
            if not q.get('association_verified') or not q.get('shared_clock_verified'):raise ValueError('unverified association or clock')
            if not 1<=key[3]<=6:raise ValueError('node range')
            d,s,t=q['node_delay_us'],q['node_span_us'],q['g0_end_elapsed_us']
            if not all(isinstance(v,int) and v>=0 for v in (d,s,t)) or not s or d+s>8000 or not 0<t<14000:raise ValueError('8 ms sampling or strict 14 ms END violation')
            index[key]=q
        except (KeyError,TypeError,ValueError) as e:errors.append(str(e))
    needed={(f['device_id'],f['boot_id'],f['sequence'],node) for f in frames for node in range(1,7) if f['node_presence_mask']&(1<<(node-1))}
    missing=needed-set(index);extra=set(index)-needed
    for f in frames:
        for node in range(1,7):
            k=(f['device_id'],f['boot_id'],f['sequence'],node)
            if k in index and abs(sum(f['node_timing_us'][node-1])-index[k]['g0_end_elapsed_us'])>1:errors.append('USB/trace envelope mismatch')
    return {'status':'PASS_ASSOCIATED_RAW_TRACE' if needed and not missing and not extra and not errors else 'FAIL_OR_INCOMPLETE_TRACE','needed_records':len(needed),'accepted_records':len(index),'missing':len(missing),'unmatched':len(extra),'errors':errors,'node_window_limit_us':8000,'G0_deadline_strictly_less_than_us':14000}

def analyze_segments(spec,root):
    reports=[]
    for i,seg in enumerate(spec['segments']):
        if i and not seg.get('explicit_reconnect_reason'):raise ValueError('Each new decoder session requires explicit reconnect reason')
        path=(root/seg['path']).resolve();raw=path.read_bytes()
        trace=read(root/seg['trace_path']) if seg.get('trace_path') else None
        q=metrics(raw,trace);q.update(path=str(path),capture_sha256=sha(path),explicit_reconnect_reason=seg.get('explicit_reconnect_reason'))
        reports.append(q)
    return {'schema':'revo3-segmented-capture-v1','segments':reports,'reconnect_count':max(0,len(reports)-1),'hardware_30min_soak_pass':False,'continuous_30min_session_verified':False,'note':'Session rates remain separate. Unknown disconnect wall time is not removed to manufacture a combined 60 Hz or 30-minute pass.'}

def main():
    ap=argparse.ArgumentParser();g=ap.add_mutually_exclusive_group(required=True);g.add_argument('--input',type=Path);g.add_argument('--segments',type=Path);ap.add_argument('--trace',type=Path);ap.add_argument('--output',type=Path,required=True);a=ap.parse_args()
    if a.segments:result=analyze_segments(read(a.segments),a.segments.parent)
    else:
        result=metrics(a.input.read_bytes(),read(a.trace) if a.trace else None);result['capture_sha256']=sha(a.input)
    save(a.output,result);print(json.dumps(result,ensure_ascii=False))
if __name__=='__main__':main()
