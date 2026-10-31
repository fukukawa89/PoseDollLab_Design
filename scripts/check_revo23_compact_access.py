"""Screwdriver and PCB removal path samples for the actual O23C assembly."""
from verify_revo23 import *
from deepen_revo23_backpack import screw_frame


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--candidate',action='store_true')
    args=ap.parse_args()
    root=B
    if args.candidate:
        from build_revo23_wire_seats import load_e,EROOT
        parts,p,_=load_e();root=EROOT
    else:
        parts=load_current();p=read(B/'profiles/device_profile.json')
    cfg=read(B/'design/compact_revision.json')
    C=np.array(cfg['controller_frame_neutral_mm']);N=frames(p,p['neutral_raw_deg'])['f:chest'];I=np.linalg.inv(N)
    tools=[]
    for i,head in enumerate(cfg['mount_heads_world_mm']):
        tools.append(dict(id='case_M3_'+str(i),key='o22/backpack_screw_'+str(i),matrix=screw_frame(head),z0=3.05,removed=[]))
    lid_keys=['o22/controller_lid']+['o22/lid_screw_'+str(i) for i in range(4)]
    for group,points,z0,removed in [('lid',[(-2,-2),(66,-2),(-2,62),(66,62)],34.2,[]),
                                  ('PCB',[(3,3),(61,3),(3,57),(61,57)],15.6,lid_keys)]:
        for i,(u,v) in enumerate(points):
            T=C.copy();T[:3,3]=(C@np.array([u,v,z0,1]))[:3]
            tools.append(dict(id=group+'_M2_'+str(i),key='o22/'+('lid' if group=='lid' else 'carrier')+'_screw_'+str(i),matrix=T,z0=1.55,removed=removed))
    # Keep the original diameter-6 failure visible. A separate, explicitly
    # specified slim-tool alternative is checked for the screw beside XIAO.
    slim=dict(next(t for t in tools if t['id']=='PCB_M2_0'))
    slim.update(id='PCB_M2_0_slim_D3',diameter_mm=3);tools.append(slim)
    rows=[]
    for name,q in cases(p,'quick').items():
        F=frames(p,q);world={k:move(v['s'],F[v['token']]) for k,v in parts.items()}
        bounds={k:np.array(s.bounding_box()) for k,s in world.items()}
        for t in tools:
            diameter=t.get('diameter_mm',6)
            tool=move(kin.b.b.cyl(diameter/2,t['z0'],t['z0']+80),F['f:chest']@I@t['matrix']);bb=np.array(tool.bounding_box());hits=[]
            for k,s in world.items():
                if k==t['key'] or k in t['removed']:continue
                b=bounds[k]
                if np.any(np.minimum(bb[3:],b[3:])-np.maximum(bb[:3],b[:3])<=0):continue
                volume=float((tool^s).volume())
                if volume>.001:hits.append(dict(key=k,overlap_mm3=volume))
            rows.append(dict(pose=name,screw=t['id'],shaft_diameter_mm=diameter,removed_for_service=t['removed'],hits=hits))
    # Remove lid and all 4 PCB screws first. Carrier, populated parts and the
    # XIAO lift together normal to the board; harness must be unplugged first.
    moving=[k for k in parts if k.startswith('o22/') and (k=='o22/carrier_pcb' or k.split('/')[-1].startswith(('J','U','C','R','F','D','L','Q','TP','xiao')))]
    fixed=[k for k in parts if k not in moving and k not in lid_keys and not k.startswith('o22/carrier_screw_')]
    body=union([parts[k]['s']for k in moving]);direction=I[:3,:3]@C[:3,2];removal=[]
    F=frames(p,cases(p,'quick')['A_STAND_35']);stationary={}
    for k in fixed:
        relative=np.linalg.inv(F['f:chest'])@F[parts[k]['token']]
        s=move(parts[k]['s'],relative);stationary[k]=(s,np.array(s.bounding_box()))
    for shift in np.linspace(0,42,22):
        moved=body.translate(direction*shift);bb=np.array(moved.bounding_box());hits=[]
        for k,(s,b) in stationary.items():
            # Relative to chest at the A pose; other body parts are included.
            if np.any(np.minimum(bb[3:],b[3:])-np.maximum(bb[:3],b[:3])<=0):continue
            v=float((moved^s).volume())
            if v>.03:hits.append(dict(key=k,overlap_mm3=v))
        removal.append(dict(translation_mm=float(shift),hits=hits))
    report=dict(geometry_sha256=sha(root/'assembly.npz'),rows=rows,passed=not any(r['hits'] for r in rows),
        slim_tool_plan_passed=not any(r['hits'] for r in rows if r['screw']!='PCB_M2_0'),
        scope='12 screw axes x 5 poses at diameter 6 mm, plus a separate diameter 3 mm alternative at PCB screw 0. Length 80 mm. Lid removed for PCB screws. No handle, human hand or wires. Match the actual purchased screw drive.',
        pcb_removal=dict(samples=removal,passed=not any(r['hits'] for r in removal),scope='22 discrete steps of populated board, A pose, lid/screws removed and harness disconnected; not continuous path proof.'),
        continuous_clearance_proven=False,physical_assembly_verified=False)
    put(root/'verification/backpack_tool_access.json',report)
    print('TOOLS',report['passed'],'PCB REMOVAL',report['pcb_removal']['passed'],flush=True)


if __name__=='__main__':main()
