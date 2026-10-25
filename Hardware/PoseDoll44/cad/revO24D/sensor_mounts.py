"""Validate saved PCB envelopes against native-board orientation datums."""
from validate import *

def main():
    parts,z,ss=read_assembly();rows=load(HERE/'sensor_mount_layout.json')['rows']
    variants=load(OUT/'electronics/sensors/manifest.json')['variants'];checks=[]
    for row in rows:
        p=next(p for p in parts if p['name']==row['pcb_part']);f=F0[p['frame']]
        w=z[str(p['i'])+'v']@f[:3,:3].T+f[:3,3];center=(w.min(0)+w.max(0))/2
        u=np.array(row['u_world']);v=np.array(row['v_to_pigtail_world']);n=np.array(row['normal_to_magnet'])
        variant=next(x for x in variants if row['sensor'] in x['instances'])
        dims=np.array([np.ptp(w@u),np.ptp(w@v)]);ce=float(np.linalg.norm(center-row['board_center_N_mm']))
        good=ce<1e-5 and np.max(abs(dims-row['board_uv_mm']))<1e-5 and np.max(abs(np.array(variant['ic_offset_uv_mm'])-row['ic_offset_uv_mm']))<1e-5 and np.max(abs(np.array(variant['board_mm'][:2])-dims))<1e-5
        checks.append(dict(sensor=row['sensor'],variant=variant['variant'],center_error_mm=ce,board_uv_mm=dims,status='PASS' if good else 'FAIL'))
        if not good:raise ValueError(checks[-1])
    digest=sha(OUT/'assembly_meshes.npz')
    put(OUT/'electronics/sensor_mounts.json',dict(geometry_sha256=digest,rows=rows,orientation_source='Frozen native PCB axes, not the sign of the pigtail exit; negative-V tails retain the original native board orientation.'))
    put(OUT/'verification/sensor_board_binding.json',dict(status='PASS',geometry_sha256=digest,rows=checks,scope='Actual saved PCB outlines, centres and native IC offsets. Does not qualify magnetic amplitude or calibration.'))
    print('SENSOR BOARD BINDING',len(checks),'PASS',flush=True)
if __name__=='__main__':main()
