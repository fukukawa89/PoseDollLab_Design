from common import *
from design import channels,named_poses,GAP_SHIFT

def run():
    nodes={n['id']:n for n in PROFILE['nodes']};cs=channels();byaxis={c['axis']:c for c in cs};routes=[];rows=[];loops={}
    for c in cs:
        pf=c['pcb_frame'];A=c['A'];start=(A@np.r_[[0,8,1.2] if c['id']=='WD' else [0,10,6.4+GAP_SHIFT],1])[:3]
        chain=[];f=pf
        while f!=ROOT and f in nodes:
            if nodes[f]['axis'] is not None:chain.append(f)
            f=nodes[f]['parent']
        branch=[];last=start;lastfr=pf;neutral_length=0
        for axis in chain:
            joint=byaxis[axis];J=np.array(joint['A']);child=axis;parent=nodes[axis]['parent'];arc=[]
            for t in np.linspace(0,1,33):
                ang=np.deg2rad(30+300*t);p=(J@np.array([15*np.cos(ang),15*np.sin(ang),14,1]))[:3];arc.append(p)
            # Free service turn stays outside the encoder and follows both endpoint frames.
            a0=arc[0];a1=arc[-1]
            if np.linalg.norm(last-a0)>.1:
                mid1=last+A[:3,2]*6;mid2=a0+J[:3,2]*6;pts=[last,mid1,mid2,a0]
                routes.append(dict(id=c['id']+'/'+axis+'/lead',bank='B',end=c['id'],start_frame=lastfr,end_frame=child,points=[dict(a=(np.linalg.inv(F0[lastfr])@np.r_[p,1])[:3].tolist(),b=(np.linalg.inv(F0[child])@np.r_[p,1])[:3].tolist(),t=i/3) for i,p in enumerate(pts)]))
                neutral_length+=sum(np.linalg.norm(b-a) for a,b in zip(pts,pts[1:]))
            pa=(np.linalg.inv(F0[child])@np.r_[a0,1])[:3];pb=(np.linalg.inv(F0[parent])@np.r_[a1,1])[:3]
            maximum=0
            for _,q in named_poses():
                ff=frames(q);maximum=max(maximum,np.linalg.norm((ff[child]@np.r_[pa,1])[:3]-(ff[parent]@np.r_[pb,1])[:3]))
            loose=max(90,math.ceil((maximum+30)/10)*10)
            loops[axis]=dict(axis=axis,child_frame=child,parent_frame=parent,nominal_bend_radius_mm=15,service_length_mm=loose,maximum_sampled_anchor_separation_mm=maximum,remaining_length_mm=loose-maximum,child_anchor_mm=pa.tolist(),parent_anchor_mm=pb.tolist(),mount='软线系于两侧各自固定的打印骨杆/夹壳外缘；不要系在磁铁座、肩钉头、摩擦面或防脱压盖活动间隙。')
            routes.append(dict(id=c['id']+'/'+axis+'/loop',bank='A' if c['id']=='WD' else 'B',end=c['id'],start_frame=child,end_frame=parent,points=[dict(a=(np.linalg.inv(F0[child])@np.r_[p,1])[:3].tolist(),b=(np.linalg.inv(F0[parent])@np.r_[p,1])[:3].tolist(),t=i/(len(arc)-1)) for i,p in enumerate(arc)]))
            neutral_length+=loose;last=a1;lastfr=parent
        exitpt=F0[ROOT][:3,3]+np.array([45,20,20]);neutral_length+=np.linalg.norm(last-exitpt);cut=math.ceil((neutral_length+120)/10)*10
        rows.append(dict(channel=c['id'],pcb_frame=pf,conductor_count=6 if c['id']=='WD' else 5,wire='32 AWG stranded flexible insulated wire, each OD <=0.65 mm; separate small bundles through joints',crossed_axes=chain,estimated_pre_cut_length_mm=cut,service_tail_mm=120,method='Conservative prototype allowance; route and sweep the real arm before final connector crimp, then trim only the controller tail.',sensor_exit_world_mm=start.tolist(),controller_port='A01 + GPIO3' if c['id']=='WD' else {'RP':'B01','HS':'B02','RU':'B03','HE':'B05','RF':'B06','WF':'B07'}[c['id']]))
    put(OUT/'harness/viewer_routes.json',routes);put(OUT/'harness/routing_plan.json',dict(rows=rows,service_loops=list(loops.values()),no_wire_crosses_wrist_deviation=True,branch_strain_relief='MT: soft lacing through two 1.3 mm holes in the rear cover, immobilize potted tail. WD: soft lacing to integral bracket cross brace; never pull solder pads.',validation=dict(anchor_length_check=all(r['remaining_length_mm']>=30 for r in loops.values()),nominal_loop_bend_radius_mm=15,posed_flexible_collision_simulation=False,physical_bend_strain_and_slip_test=False,scope='Reference centerlines and sampled anchor travel only; route actual slack outside all joints and complete the manual sweep test.')))
    print('HARNESS',[(r['channel'],r['estimated_pre_cut_length_mm'],len(r['crossed_axes'])) for r in rows],flush=True)

if __name__=='__main__':run()
