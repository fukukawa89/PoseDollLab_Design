"""T6 closed sockets, metal load path, reuse and thread allowance."""
from audit import *

def main():
 d=build();P={p['id']:p for p in d.parts};ports=list(PORTS);geo=sha(OUT/'assembly_meshes.npz')
 tests=[]
 for port in ports:
  M=np.array(port['M']);C=M@rot(Y,port['clock_deg']);body=P[port['body']]['s']
  # Entire closed six-flat shell around minimum 2.15 mm metal hex section.
  shell=moved(hexagon([0,-4.2,0],Y,8.,1.8)-hexagon([0,-4.21,0],Y,HEX_AF+.02,1.82),C)
  missing=(shell-body).volume()
  minimum=moved(nyloc(5.32,3.7,2.15),C);largest=moved(nyloc(),C)
  fits=[(n^body).volume() for n in [minimum,largest]]
  spin=[(moved(minimum,M@rot(Y,q)@np.linalg.inv(M))^body).volume() for q in [-30,-10,10,30]]
  tests.append(dict(body=port['body'],prefix=port['prefix'],six_flat_shell_missing_mm3=missing,aligned_min_max_nut_collision_mm3=fits,minimum_nut_spin_collision_mm3=spin,metal_hex_capture_mm=1.9,passed=missing<.001 and max(fits)<.001 and min(spin)>.02))
 z=np.load(OUT/'assembly_meshes.npz');D={r['id']:r for r in json.loads((OUT/'assembly.json').read_text('utf8'))['parts']}
 def circle(id,axes):
  vs=z['v'+str(D[id]['index'])];v=vs[abs(np.linalg.norm(vs[:,axes],axis=1)-2.125)<.00002][:,axes]
  c=np.linalg.lstsq(np.c_[2*v,np.ones(len(v))],np.sum(v*v,axis=1),rcond=None)[0]
  return dict(center_mm=c[:2].tolist(),radius_mm=float(np.sqrt(c[2]+sum(c[:2]**2))),vertices=len(v))
 fits={k:circle(*args) for k,args in {'H':('H3-03',[0,2]),'R':('R3-03',[0,1]),'W_Y':('W4-01',[0,2]),'W_X':('W4-04',[1,2])}.items()}
 ref=a.reference()[0];E=np.array(ref['points_mm']['lowerarm_l']);W=np.array(ref['points_mm']['hand_l']);er=float(np.linalg.norm(E+[0,0,-FORE]-W));fe=max(np.linalg.norm(c['center_mm']) for c in fits.values())
 put(OUT/'verification/ue_alignment.json',dict(passed=max(er,fe)<1e-5,geometry_sha256=geo,fitted_bores=fits,wrist_reference_error_mm=er,forearm_mm=FORE,wrist_axis_order='Ry(flex) @ Rx(deviation)',reference_asset=ref['asset'],scope='Nominal exported bore centres; full body and physical tolerances not certified.'))
 heights=[]
 for h in [.9,1.,1.1,1.2]:
  dh=build(h);heights.append(dict(pair_height_mm=h,collisions=collisions(scene_parts(dh)),stack_rows=dh.stacks))
 tools=[]
 for port in ports:
  M=np.array(port['M']);pre=port['prefix'];st=P[pre+'AX']['station']
  tool=moved(cyl([0,9.81,0],[0,50,0],1.85),M);hits=[]
  for p in d.parts:
   if p['bench_only'] or p['station']!=st or p['id']==pre+'AX':continue
   if overlap(bounds(tool),bounds(p['s'])) and (tool^p['s']).volume()>.02:hits.append(p['id'])
  tools.append(dict(screw=pre+'AX',diameter_mm=3.7,passed=not hits,obstructions=hits,condition='R: remove detachable wrist/fixture and crossbolt first'))
 prior=H/'bench/revO24C_T5';oldP={p['id']:p for p in json.loads((prior/'assembly.json').read_text('utf8'))['parts']};oldz=np.load(prior/'assembly_meshes.npz');reuse={};hardware={}
 changed_ids={port['prefix']+suffix for port in ports for suffix in ['N','RW']}
 for id,p in D.items():
  if id not in oldP:continue
  old=oldP[id]
  if p['printable']:reuse[id]=sha(OUT/p['stl'])==sha(prior/old['stl'])
  elif id not in changed_ids:hardware[id]=all(np.array_equal(z[k+str(p['index'])],oldz[k+str(old['index'])]) for k in ['v','f'])
 frozen=json.loads((prior/'manifest.json').read_text('utf8'))['files'];changed=[r['path'] for r in frozen if sha(prior/r['path'])!=r['sha256']]
 bounds_same={new:bool(np.allclose(P[new]['s'].bounding_box(),oldP[old]['bounds_mm'][0]+oldP[old]['bounds_mm'][1])) for new,old in [('H6-01','H5-01'),('R6-01','R5-01'),('W6-01','W5-01')]}
 put(OUT/'verification/reuse.json',dict(passed=len(reuse)==10 and all(reuse.values()) and all(hardware.values()) and not changed and all(bounds_same.values()),geometry_sha256=geo,identical_STLs=reuse,identical_retained_hardware=hardware,unchanged_housing_bounds=bounds_same,T5_files_checked=len(frozen),T5_changes=changed))
 single={id:len(P[id]['s'].decompose())==1 for id in ['H6-01','R6-01','W6-01','C6-01']}
 rows=[r for item in heights for r in item['stack_rows']]
 clearance=min(r['shoulder_to_reaction_washer_gap_mm'] for r in rows);protrusion=min(r['tip_past_nylon_mm'] for r in rows)
 report=dict(passed=all(x['passed'] for x in tests) and all(x['passed'] for x in tools) and all(not x['collisions'] for x in heights) and all(single.values()) and clearance>.299 and protrusion>.899,geometry_sha256=geo,closed_hex_capture=tests,one_connected_solid=single,preload_envelopes=heights,tools=tools,minimum_shoulder_gap_mm=clearance,minimum_tip_past_nylon_mm=protrusion,physical_tests_passed=False,notes=['No torque, printed socket strength, nyloc performance or 100-cycle test has been certified.','Nyloc CAD shows assembled major-diameter bore, no nylon deformation or helix.','Actual screw lengths, washer thicknesses and tip chamfer must be measured; require shoulder clearance and complete nylon engagement. Nominal worst dimensions are not an all-tolerance guarantee.','Two .8 mm spacers and .5 mm reaction washer create a metal load path. Do not use old .8 mm small-hole washer.','Full six-flat pocket limits rotation; clearance take-up is possible, slot rounding or continuing nut rotation is a failure.'])
 put(OUT/'verification/mechanics.json',report)
 print(json.dumps(dict(passed=report['passed'],capture=tests,clearance=clearance,protrusion=protrusion,collisions=[r['collisions'] for r in heights],reuse=len(reuse)),ensure_ascii=False),flush=True)
 if not report['passed']:raise SystemExit(1)
if __name__=='__main__':main()

