"""Explicit links in the entire retention chain, independently of frame labels."""
from verify import *

def stop(s,ob,axis,limit=12):
    rows=[]
    for sg in [-1,1]:
        hit=None
        for d in np.arange(.1,limit+.001,.1):
            vol=(s.translate(np.array(axis)*sg*d)^ob).volume()
            if vol>.02:hit=dict(direction=sg,travel_mm=float(d),overlap_mm3=float(vol));break
        rows.append(hit)
    return rows

def main(production=False):
    parts=read_saved();by={p['name']:p for p in parts};ws={p['name']:moved(p['s'],F0[p['frame']]) for p in parts}
    groups={}
    for p in parts:
        if p['role'] in ['structure','rotor','shell']:groups.setdefault(p['frame'],[]).append(ws[p['name']])
    groups={fr:union(s) for fr,s in groups.items()};rows=[];pins=[]
    if production:groups=production_groups()
    for j in load(OUT/'profiles/joint_interfaces.json'):
        pre=j['id'];axis=np.array(j['axis_world']);h='pressure_web_width_mm' in j
        fixed=[pre+'_pressure_-1',pre+'_pressure_1'] if h else [pre+'_compression_cartridge']
        caps=[pre+'_rotor_cap_-1',pre+'_rotor_cap_1'] if h else [pre+'_rear_thrust_cap',pre+'_keyed_output_cap']
        parent=by[fixed[0]]['frame'];child=j['axis_id'];rotor=groups[child]+union(ws[n] for n in caps+[pre+'_shaft'])
        metal=stop(rotor,union(ws[n] for n in fixed),axis)
        outpin=pre+'_drive_pin' if h else pre+'_capture_bolt'
        output=stop(groups[child],ws[outpin],axis)
        pin=pre+'_drive_pin' if h else pre+'_fixed_capture_pin'
        fixed_link=stop(ws[pre+'_compression_cartridge'],groups[parent],axis) if not h else []
        # The fixed pin is tested separately: cage can float 0.1 mm before pin bears.
        positive=stop(ws[pin],groups[child if h else parent],axis)
        # Frame label alone cannot supply any of these three explicit stops.
        r=dict(interface=pre,family='H16' if h else 'C20',metal_to_fixed_metal=metal,output_bone_to_capture=output,fixed_pin_to_input_structure=positive,
               status='PASS_GEOMETRY' if all(metal) and all(output) and all(positive) else 'FAIL')
        rows.append(r);print('CHAIN',pre,r['status'],flush=True)
        # Nominal straight insertion path, prior to bearing or preload assembly.
        s=ws[pin];vv,_=base.a.mesh_data(s);_,axes=np.linalg.eigh(np.cov(vv.T));a=axes[:,-1];ob=groups[child if h else parent]+(ws[pre+'_compression_sleeve'] if h else ws[pre+'_compression_cartridge'])
        directions=[]
        for sg in [-1,1]:
            worst=0.;first=None
            for d in np.arange(0,40.001,.5):
                vol=(s.translate(a*sg*d)^ob).volume();worst=max(worst,vol)
                if vol>.02 and first is None:first=float(d)
            directions.append(dict(sign=sg,first_block_mm=first,max_overlap_mm3=worst))
        pins.append(dict(pin=pin,axis_world=a.tolist(),paths=directions,status='PASS_GEOMETRY' if any(d['first_block_mm'] is None for d in directions) else 'FAIL'))
    nuts=[]
    for p in parts:
        if not (p['name'].endswith('_capture_nyloc') or '_preload_nut_' in p['name'] or p.get('sku')=='NL3' or '_E_pcb_nut_' in p['name'] or '_E_magnet_keeper_nut' in p['name']):continue
        s=ws[p['name']];v,_=base.a.mesh_data(s);c=centre(s);_,a=np.linalg.eigh(np.cov(v.T));ax=a[:,0];body=groups[p['frame']]
        aligned=(s^body).volume();spin=[]
        for angle in [-30,-10,10,30]:spin.append(float((moved(s,T(c)@rot(ax,angle)@T(-c))^body).volume()))
        nuts.append(dict(nut=p['name'],aligned_overlap_mm3=float(aligned),rotation_overlap_mm3=spin,status='PASS_GEOMETRY' if aligned<.02 and min(spin)>.02 else 'FAIL'))
    wrist=[]
    for side in ['l','r']:
        W=F0[side+'_wrist_flex'];M=np.diag([1.,-1,1.]) if side=='r' else np.eye(3)
        for a,outer,inner in [('Y','W4-01','W6-01'),('X','W4-04','W6-01')]:
            bolts=union(ws[side+'_E_W'+a+k+'_AX'] for k in ['M','P']);s=ws[side+'_E_'+outer]
            ax=W[:3,:3]@M@(np.array([0,1,0]) if a=='Y' else np.array([1,0,0]));hits=stop(s,bolts,ax)
            wrist.append(dict(side=side,axis=a,outer_fork_to_two_shoulders=hits,status='PASS_GEOMETRY' if all(hits) else 'FAIL'))
    report=dict(geometry_sha256=sha(OUT/'assembly_meshes.npz'),chains=rows,pin_insertion=pins,nut_capture=nuts,wrists=wrist,scope='Explicit nominal material stops. Full output body included. At least one straight pin access direction required. Thread helices/nylon compliance not modelled; thread dimensions checked separately. Does not establish force or fatigue.',status='PASS_GEOMETRY' if all(r['status']=='PASS_GEOMETRY' for r in rows+pins+nuts+wrist) else 'FAIL')
    if production:report['production_mesh_sha256']=sha(OUT/'production_meshes.npz')
    put(OUT/('verification/production_retention.json' if production else 'verification/retention_chain.json'),report)
    print('FAILED',[(r.get('interface') or r.get('pin') or r.get('nut') or r.get('side'),r) for r in rows+pins+nuts+wrist if r['status']=='FAIL'],flush=True)
if __name__=='__main__':main('--production' in sys.argv)
