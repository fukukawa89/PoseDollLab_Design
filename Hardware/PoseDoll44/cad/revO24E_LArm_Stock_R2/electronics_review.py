"""Mechanical reservation study. Deliberately not an electronics manufacturing release.
The trial BOM stays mechanical. Envelopes must never be confused with printable holders.
"""
from check_stock import saved
from build_stock import *
import shutil

def main():
 folder=OUT/'electronics';folder.mkdir(exist_ok=True);a,ss=saved();P={p['name']:p for p in a};ints=load(OUT/'interfaces.json');parts=[];bindings=[];cases=load(OUT/'verification/motion_dense.json')['cases']
 # Same finite pose set as the mechanical checker, reconstructed deterministically.
 poses=[('neutral',POSES['neutral']['angles'])]
 for axis in PROFILE['axes']:
  lo,hi=axis['limits_deg']
  for no,val in enumerate(np.linspace(lo,hi,math.ceil((hi-lo)/2)+1)):
   q=dict(POSES['neutral']['angles']);q[axis['id']]=float(val);poses.append((f'{axis["id"]}/{no}',q))
 for name,p in POSES.items():
  if name.startswith('ROM/') or name=='neutral':continue
  for no,t in enumerate(np.linspace(0,1,21)):poses.append((f'path/{name}/{no}',{ax['id']:(1-t)*POSES['neutral']['angles'].get(ax['id'],0)+t*p['angles'].get(ax['id'],0) for ax in PROFILE['axes']}))
 world=[]
 for name,q in poses:
  f=frames(q);sol=[moved(s,f[p['frame']]) for p,s in zip(a,ss)];world.append((name,f,sol,np.array([e.bounds(s) for s in sol])))
 variants={v['variant']:v for v in load(H/'bench/revO24E/electronics/inherited_D/sensors/manifest.json')['variants']}
 def clear(s,fr,skip=()):
  worst=0.;bad=[]
  for name,f,sol,bb in world:
   v=moved(s,f[fr]);lo,hi=e.bounds(v);active=np.flatnonzero(np.all(bb[:,1]>=lo,axis=1)&np.all(bb[:,0]<=hi,axis=1))
   for i in active:
    if a[i]['name'] in skip:continue
    ov=(v^sol[i]).volume();worst=max(worst,ov)
    if ov>.02:bad.append(dict(pose=name,part=a[i]['name'],overlap_mm3=ov));return False,worst,bad
  return True,worst,bad
 def add(n,s,fr,role,W):
  local=moved(s,np.linalg.inv(F0[fr])@W);parts.append(dict(name=n,frame=fr,role=role,s=local));return local
 def board(variant):
  v=variants[variant];w,h,t=v['board_mm'];du,dv=v['ic_offset_uv_mm']
  # Origin is sensor die, not PCB centre. Include populated inward face and a potted tail.
  return box([-w/2-du,-h/2-dv,-2.5],[w/2-du,h/2-dv,t])+box([-2-du,h/2-dv,-1.5],[2-du,h/2-dv+4,2.0])
 for r,variant,axis in zip(ints['rolls'],['S2','S3','S1'],['l_shoulder_flex','l_upperarm_roll','l_forearm_roll']):
  W=np.array(r['W']);fr=r['fixed_frame'];out=r['output_frame'];chosen=None
  for radius in [22,25,28]:
   for angle in [45,135,225,315,90,270,0,180]:
    rad=math.radians(angle);normal=np.array([math.cos(rad),math.sin(rad),0]);u=np.array([-normal[1],normal[0],0]);v=np.array([0,0,1]);B=W@T(normal*radius+[0,0,-15],np.column_stack([u,v,normal]));local=moved(board(variant),np.linalg.inv(F0[fr])@B);ok,hit,bad=clear(local,fr)
    if ok:chosen=(B,radius,angle,hit);break
   if chosen:break
  assert chosen,(r['id'],'PCB reservation');B,radius,angle,hit=chosen;add(r['id']+'_PCB_RESERVED',board(variant),fr,'pcb',B)
  M=W@T([0,0,-15]);mag=cyl([0,0,-1.25],[0,0,1.25],3);local=add(r['id']+'_MAGNET_RESERVED',mag,out,'magnet',M);ok,vol,bad=clear(local,out);assert ok,bad
  bindings.append(dict(id=r['id'],axes=[axis],variant=variant,fixed_frame=fr,moving_frame=out,board_die_matrix_local=(np.linalg.inv(F0[fr])@B).tolist(),magnet_matrix_local=(np.linalg.inv(F0[out])@M).tolist(),magnet_mm=[6,2.5],sensor_layout='radial 3D magnetic measurement; new calibration required',radial_die_offset_mm=radius,clock_deg=angle,board_check_max_overlap_mm3=hit,magnet_check_max_overlap_mm3=vol,fixed_mount_interface='existing pair of R cover M3 bolt axes; detachable bridge on rear face; added bracket thickness requires correspondingly longer stock screws and renewed engagement check',moving_mount_interface='keyed two-piece saddle on noncircular moving shaft below service window; detachable central magnet bridge, independent of preload screw head',carrier_fabrication_released=False))
 for r,axis in zip(ints['hinges'],['l_shoulder_abduct','l_elbow_flex']):
  M=np.array(r['M']);fr=r['fixed_frame'];out=r['output_frame'];chosen=None
  for side in [1,-1]:
   for distance in [28,31,34]:
    B=M@T([0,side*distance,0],np.column_stack([[1,0,0],[0,0,-side],[0,side,0]]));local=moved(board('S1'),np.linalg.inv(F0[fr])@B);ok,hit,bad=clear(local,fr)
    if ok:chosen=(B,side,distance,hit);break
   if chosen:break
  assert chosen,(r['id'],'PCB reservation');B,side,distance,hit=chosen;add(r['id']+'_PCB_RESERVED',board('S1'),fr,'pcb',B)
  G=M@T([0,side*23.5,0],np.column_stack([[1,0,0],[0,0,-side],[0,side,0]]));local=add(r['id']+'_MAGNET_RESERVED',cyl([0,0,-1.25],[0,0,1.25],3),out,'magnet',G);ok,vol,bad=clear(local,out);assert ok,bad
  bindings.append(dict(id=r['id'],axes=[axis],variant='S1',fixed_frame=fr,moving_frame=out,board_die_matrix_local=(np.linalg.inv(F0[fr])@B).tolist(),magnet_matrix_local=(np.linalg.inv(F0[out])@G).tolist(),magnet_mm=[6,2.5],board_check_max_overlap_mm3=hit,magnet_check_max_overlap_mm3=vol,fixed_mount_interface='split saddle on continuous fixed backbone; route removable bracket in positive H-X / positive H-Z quadrant, outside ear sweep; no hole through force bridge',moving_mount_interface='keyed removable cap around moving fork ear; magnet follows printed output, never the adjustable shoulder screw',carrier_fabrication_released=False))
 fr='l_forearm_roll';out='l_wrist_deviation';MW=F0['l_wrist_flex'];B=MW@T([0,24.5,0],np.column_stack([[1,0,0],[0,0,-1],[0,1,0]]));local=add('W_PCB_RESERVED',board('S1'),fr,'pcb',B);ok,hit,bad=clear(local,fr);assert ok,bad
 G=F0[out]@T([-12.5,0,-16],np.column_stack([[1,0,0],[0,0,-1],[0,1,0]]));local=add('W_MAGNET_RESERVED',cyl([0,0,-1.5],[0,0,1.5],3),out,'magnet',G);ok,vol,bad=clear(local,out);assert ok,bad
 bindings.append(dict(id='W',axes=['l_wrist_flex','l_wrist_deviation'],variant='S1',fixed_frame=fr,moving_frame=out,board_die_matrix_local=(np.linalg.inv(F0[fr])@B).tolist(),magnet_matrix_local=(np.linalg.inv(F0[out])@G).tolist(),magnet_mm=[6,3],board_check_max_overlap_mm3=hit,magnet_check_max_overlap_mm3=vol,fixed_mount_interface='removable saddle on reinforced forearm; fixed PCB centre retained at wrist [0,24.5,0]',moving_mount_interface='existing D6.2 blind pocket and keeper boss on S2-P011 retained; keeper and sensor carrier are future electronic accessories',carrier_fabrication_released=False,angle_chain='Ry(wrist_flex) @ Rx(wrist_deviation); 3-field-vector constrained two-angle LUT must be recalibrated'))
 # PCB rigid insertion envelopes; bracket installation is not silently included in this check.
 for bind in bindings:
  p=next(p for p in parts if p['name']==bind['id']+'_PCB_RESERVED');normal=np.array(bind['board_die_matrix_local'])[:3,2];others=union(moved(s,F0[x['frame']]) for x,s in zip(a,ss));worst=0.
  for travel in np.linspace(0,30,61):worst=max(worst,(moved(p['s'].translate(normal*travel),F0[p['frame']])^others).volume())
  bind['board_outward_entry_max_overlap_mm3']=worst
 mutual=[]
 for name,f,_,_ in world:
  sol=[moved(p['s'],f[p['frame']]) for p in parts];bb=[e.bounds(s) for s in sol]
  for i in range(len(sol)):
   for j in range(i):
    if np.any(bb[i][1]<bb[j][0]) or np.any(bb[j][1]<bb[i][0]):continue
    ov=(sol[i]^sol[j]).volume()
    if ov>.02:mutual.append(dict(pose=name,a=parts[i]['name'],b=parts[j]['name'],volume_mm3=ov))
 assert not mutual,mutual[:5]
 scene=trimesh.Scene();zz={};meta=[]
 for i,p in enumerate(parts):
  v,f=e.base.a.mesh_data(p['s']);zz[str(i)+'v']=v;zz[str(i)+'f']=f;meta.append({k:v for k,v in p.items() if k!='s'}|dict(i=i,quantity=1,physical_trial_item=False));m=trimesh.Trimesh(v,f,process=False);m.visual.vertex_colors=([40,170,110,255] if p['role']=='pcb' else [230,85,65,255]);m.apply_transform(FA[p['frame']]);m.apply_scale(.001);scene.add_geometry(m,node_name=p['name'])
 for p,s in zip(a,ss):
  v,f=e.base.a.mesh_data(s);m=trimesh.Trimesh(v,f,process=False);m.apply_transform(FA[p['frame']]);m.visual.vertex_colors=[170,185,185,100];m.apply_scale(.001);scene.add_geometry(m,node_name=p['part_number'])
 scene.export(folder/'reserved_layout.glb');np.savez_compressed(folder/'reserved_meshes.npz',**zz);put(folder/'reserved_parts.json',meta)
 oldroutes=load(H/'bench/revO24E/harness/routes.json');ids=['l_shoulder_pitch','l_shoulder_swing','l_humeral','l_elbow','l_forearm','l_wrist'];inherited=[x for x in oldroutes['cables'] if x['sensor'] in ids]
 put(folder/'inherited_pinmap_reference.json',dict(source_sha256=sha(H/'bench/revO24E/harness/routes.json'),cables=inherited,warning='Pin mapping only. Old cut lengths, clips and routes are NOT applicable to this arm.'))
 wire=dict(conductors=6,wire='AWG30 finely stranded; insulation OD <=0.7 mm',reserved_bundle_diameter_mm=3.5,minimum_dynamic_bend_radius_mm=10,pins='retain per-instance inherited pin map, never interchange SDO channel labels',routing='outside the continuous backbone; no wire through A8/FW4/NL3 stacks, R capture lip, fork pinch zone or central adjuster bore',strain_relief='fixed-side PCB potted tail first, then a removable saddle/clip; reserve service loops at RP, HS, RU, HE and RF; fixed wrist PCB avoids wires across both wrist axes',minimum_loop_budgets_mm={x['id']:round(2*math.pi*10+10*math.radians(x['limits_deg'][1]-x['limits_deg'][0]),1) for x in PROFILE['axes'] if x['id'] not in ['l_wrist_flex','l_wrist_deviation']},loop_budget_scope='preliminary arc-length allowance only, not wire cut length or collision/fatigue validation',routing_release=False)
 put(folder/'interface_reservations.json',dict(status='PASS_RIGID_ENVELOPE_RESERVATION',geometry_sha256=sha(OUT/'production_meshes.npz'),sampled_poses=len(poses),bindings=bindings,wire=wire,variant_definitions={k:variants[k] for k in ['S1','S2','S3']},mechanical_trial_electronics_required=False,carrier_fabrication_released=False,electrical_accuracy_verified=False,scope='Twelve rigid board/component/tail and magnet envelopes checked against all mechanical bodies in 850 finite poses. No sensor holder STL, moving cable collision check, magnetic field qualification or electronic manufacturing release is implied. Future detachable carriers use external saddles/existing fastener interfaces; no unreviewed notch is cut into the new force bridge.'))
 print('ELECTRONICS',len(bindings),'bindings',len(parts),'rigid reservations',len(poses),'poses; electronics accessories not released',flush=True)
if __name__=='__main__':main()
