"""Read-only review of saved O24D/T6 meshes. Writes only this audit's outputs.
No build/export script is called; no old PASS or manufacturing file is changed.
The tests below detect rigid-path interference or escape, not assembly force,
friction, fatigue or the impossibility of every alternative assembly path.
"""
from pathlib import Path
import json,hashlib,collections
import numpy as np
import manifold3d as md
HERE=Path(__file__).resolve().parent
H=HERE.parents[1]
ROOT=H.parents[1]
P=H/'bench/revO24D'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
load=lambda p:json.loads(p.read_text('utf8'))
A=load(P/'assembly.json');Z=np.load(P/'assembly_meshes.npz')
rows={r['name']:r for r in A['parts']}
FA={n:np.array(m) for n,m in A['neutral_frames'].items()}
FN={n:np.array(m) for n,m in A['build_reference_N_frames'].items()}
cache={}
def solid(n):
 if n not in cache:
  r=rows[n];s=md.Manifold(md.Mesh64(Z[str(r['i'])+'v'].astype(np.float64),Z[str(r['i'])+'f'].astype(np.uint64)))
  assert s.status()==md.Error.NoError,n
  cache[n]=s.transform(FA[r['frame']][:3])
 return cache[n]
def center(s):return np.array(s.bounding_box()).reshape(2,3).mean(0)
def vol(a,b):return max(0.,float((a^b).volume()))
def union(items):return md.Manifold.batch_boolean(list(items),md.OpType.Add)

joints=load(P/'profiles/joint_interfaces.json')
cartridges=[j for j in joints if 'pressure_web_width_mm' not in j]
output_paths=[]
for j in cartridges:
 pre=j['id'];fr=j['axis_id'];name=pre+'_output_socket';moving=solid(name)
 axis=FA[fr][:3,:3]@FN[fr][:3,:3].T@np.array(j['axis_world'])
 if np.dot(center(moving)-center(solid(pre+'_compression_cartridge')),axis)<0:axis=-axis
 pin=solid(pre+'_torque_pin')
 localmetal=[n for n,r in rows.items() if n.startswith(pre+'_') and r['role'] in ['metal','magnet','bearing','friction']]
 metal=union(solid(n) for n in localmetal)
 metal_no_pin=union(solid(n) for n in localmetal if n!=pre+'_torque_pin')
 samples=[dict(offset_mm=round(float(d),3),pin_collision_mm3=vol(moving.translate(axis*d),pin),all_local_metal_collision_mm3=vol(moving.translate(axis*d),metal),collision_without_torque_pin_mm3=vol(moving.translate(axis*d),metal_no_pin)) for d in np.linspace(0,8,81)]
 hits=[r for r in samples if r['pin_collision_mm3']>.02]
 output_paths.append(dict(interface=pre,output_part=name,axis_outward_A=axis.tolist(),documented_sequence='torque pin first, then printed output socket',sample_interval_mm=.1,first_pin_interference=hits[0] if hits else None,maximum_pin_interference_mm3=max(r['pin_collision_mm3'] for r in samples),max_without_torque_pin_mm3=max(r['collision_without_torque_pin_mm3'] for r in samples),samples=samples))
 print('SOCKET',pre,'pin_max',round(max(r['pin_collision_mm3'] for r in samples),6),flush=True)

wrists=[]
for side in ['l','r']:
 for liner,cup,sg in [('W04','W06',-1),('W05','W07',1)]:
  other='W07' if cup=='W06' else 'W06'
  axis=center(solid(side+'_'+other))-center(solid(side+'_'+cup));axis/=np.linalg.norm(axis)
  ms=solid(side+'_'+liner);fs=solid(side+'_'+cup)
  samples=[dict(offset_toward_ball_mm=round(float(d),3),collision_mm3=vol(ms.translate(axis*d),fs)) for d in np.linspace(0,20,81)]
  hits=[r for r in samples if r['collision_mm3']>.02]
  wrists.append(dict(liner=side+'_'+liner,cup=side+'_'+cup,sample_interval_mm=.25,first_interference=hits[0] if hits else None,max_collision_mm3=max(r['collision_mm3'] for r in samples),samples=samples))

# Reproduce the T6 R failure independently of the old fixed-frame metadata.
p=H/'bench/revO24C_T6';data=load(p/'assembly.json');tz=np.load(p/'assembly_meshes.npz')
rr={r['id']:r for r in data['parts'] if r['station']=='R'}
rs={n:md.Manifold(md.Mesh(tz['v'+str(r['index'])].astype(np.float32),tz['f'+str(r['index'])].astype(np.uint32))) for n,r in rr.items()}
s=load(p/'tutorial/steps.json')['lessons']['R']['steps'][18];assert s['n']==19
rt=[]
for label,names in [('step19',set(s['after'])-{'R6-01'}),('final',set(rr)-{'R6-01'})]:
 moving=union(rs[n] for n in names)
 scan=[dict(offset_mm=round(float(d),3),collision_mm3=vol(moving.translate([0,0,-d]),rs['R6-01'])) for d in np.linspace(0,8,81)]
 rt.append(dict(state=label,geometry_sha256=sha(p/'assembly_meshes.npz'),moving_ids=sorted(names),screw_nut_relative_motion=False,escape_path_max_overlap_mm3=max(r['collision_mm3'] for r in scan),end_gap_mm=float(rs['R6-01'].bounding_box()[2]-moving.translate([0,0,-8]).bounding_box()[5]),samples=scan))

old=load(P/'verification/closure_faults_and_tolerances.json')
loads=load(P/'verification/preload_retention_loads.json')
report=dict(date='2026-10-26',geometry_sha256=sha(P/'assembly_meshes.npz'),source_sha256={n:sha(H/'cad/revO24D'/n) for n in ['fullbody.py','closures.py','closure_checks.py','strength.py','s1_geometry_input.py']},assembly_features=len(rows),joint_count=len(joints),cartridge_count=len(cartridges),H2_count=len(joints)-len(cartridges),no_A8_in_current_O24D=not any(r.get('sku')=='A8' or 'belleville' in r['name'].lower() for r in rows.values()),socket_path_interference_count=sum(r['first_pin_interference'] is not None for r in output_paths),socket_paths=output_paths,old_cartridge_stop_test_coverage=[dict(axis=r['axis'],fixed_stop_parts=r['fixed_stop_parts'],moving_stop_parts=r['moving_stop_parts'],fixed_socket_capture=r['fixed_socket_capture']) for r in old['joints'] if r['interface'] in {j['id'] for j in cartridges}],wrist_liner_paths=wrists,T6_R_escape=rt,selected_loads=[{k:r.get(k) for k in ['axis','hold_target_Nm','required_clamp_N','assumed_min_mu','shaft_procurement_min_yield_MPa','axial_handling_pull_N']} for r in loads['rows'] if r['axis'] in ['l_elbow_flex','l_forearm_roll','l_wrist_flex','lumbar_flex','l_hip_flex','l_knee_flex']],scope='Targeted saved-mesh audit at A neutral. Output socket tested on documented coaxial path with torque pin installed; the reverse path checks the same nominal obstruction. Not a proof that alternative tilted or deformable assembly is impossible, and not a pull-force test. Friction and STL frame assignment are not counted as attachments. No original manufacturing data changed.')
(HERE/'findings.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8')
print(json.dumps(dict(socket_path_interference_count=report['socket_path_interference_count'],cartridges=len(cartridges),wrist_max=[(r['liner'],r['max_collision_mm3']) for r in wrists],T6_R=[(r['state'],r['escape_path_max_overlap_mm3'],r['end_gap_mm']) for r in rt]),ensure_ascii=False),flush=True)
