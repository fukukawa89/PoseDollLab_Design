from verify import *
parts=read_saved();by={p['name']:p for p in parts}
bad={r['interface'] for r in load(OUT/'verification/capture_and_paths.json')['rows'] if r['status']=='FAIL'}
for it in load(OUT/'profiles/capture_interfaces.json'):
    if it['id'] not in bad:continue
    W=np.array(it['W']);inv=np.linalg.inv(W);pre=it['id']
    cs=lambda p:moved(p['s'],inv@F0[p['frame']])
    pp=[p for p in parts if p['frame']==it['output_frame'] and p['role'] in ['structure','rotor','shell']]
    hw=[p for p in parts if p['name'].startswith(pre+'_') and p['role'] not in ['structure','rotor','shell','pcb','connector','magnet'] and not any(t in p['name'] for t in ['capture_','spring_','locknut','nut_washer','end_safety','lock_tab'])]
    for p in pp:
        for h in hw:
            maxv=0;at=0
            for dist in np.arange(0,8.01,.2):
                vv=(cs(p).translate([0,0,dist])^cs(h)).volume()
                if vv>maxv:maxv=vv;at=dist
            if maxv>.01:print(pre,p['name'],h['name'],maxv,at,flush=True)
