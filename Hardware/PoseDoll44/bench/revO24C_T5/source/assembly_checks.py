"""New load wall, nut capture, access, shaft datum and retained-part checks."""
from audit import *

def main():
 d=build();P={p['id']:p for p in d.parts};ports=list(PORTS);geo=sha(OUT/'assembly_meshes.npz');tests=[]
 for port in ports:
  M=np.array(port['M']);pre=port['prefix'];body=P[port['body']]['s'];n=P[pre+'N']['s']
  # This annulus lies entirely in the retained continuous reaction wall.
  ring=moved(cyl([0,-2.7,0],[0,-2,0],6)-cyl([0,-2.71,0],[0,-1.99,0],2.2),M)
  missing=(ring-body).volume();spin=[]
  for angle in [-10,10]:
   turned=moved(n,M@rot(Y,angle)@np.linalg.inv(M));spin.append((turned^body).volume())
  tests.append(dict(body=port['body'],prefix=pre,continuous_annulus_missing_mm3=missing,antirotation_overlap_at_10deg_mm3=spin,passed=missing<.001 and min(spin)>.02))
 z=np.load(OUT/'assembly_meshes.npz');D={r['id']:r for r in json.loads((OUT/'assembly.json').read_text('utf8'))['parts']}
 def circle(id,axes):
  vs=z['v'+str(D[id]['index'])];v=vs[abs(np.linalg.norm(vs[:,axes],axis=1)-2.125)<.00002][:,axes]
  c=np.linalg.lstsq(np.c_[2*v,np.ones(len(v))],np.sum(v*v,axis=1),rcond=None)[0]
  return dict(center_mm=c[:2].tolist(),radius_mm=float(np.sqrt(c[2]+sum(c[:2]**2))),vertices=len(v))
 fits={k:circle(*args) for k,args in {'H':('H3-03',[0,2]),'R':('R3-03',[0,1]),'W_Y':('W4-01',[0,2]),'W_X':('W4-04',[1,2])}.items()}
 ref=a.reference()[0];E=np.array(ref['points_mm']['lowerarm_l']);W=np.array(ref['points_mm']['hand_l']);er=float(np.linalg.norm(E+[0,0,-FORE]-W));fe=max(np.linalg.norm(c['center_mm']) for c in fits.values())
 put(OUT/'verification/ue_alignment.json',dict(passed=max(er,fe)<1e-5,geometry_sha256=geo,fitted_bores=fits,wrist_reference_error_mm=er,forearm_mm=FORE,wrist_axis_order='Ry(flex) @ Rx(deviation)',reference_asset=ref['asset'],scope='Nominal exported-mesh bore fit; unchanged actual arm datums. No full-body height or physical tolerance certification.'))
 heights=[]
 for h in [.9,1.,1.1,1.2]:
  dh=build(h);heights.append(dict(pair_height_mm=h,collisions=collisions(scene_parts(dh)),stack_rows=dh.stacks))
 tools=[]
 for port in ports:
  M=np.array(port['M']);pre=port['prefix'];st=P[pre+'AX']['station']
  # Start just outside head. R access excludes detachable wrist / bench arm.
  tool=moved(cyl([0,9.81,0],[0,50,0],1.85),M);hits=[]
  for p in d.parts:
   if p['bench_only'] or p['station']!=st or p['id']==pre+'AX':continue
   if overlap(bounds(tool),bounds(p['s'])) and (tool^p['s']).volume()>.02:hits.append(p['id'])
  tools.append(dict(screw=pre+'AX',diameter_mm=3.7,passed=not hits,obstructions=hits,condition='neutral joint; R needs detachable wrist/fixture and transverse bolt removed'))
 prior=H/'bench/revO24C_T4';was=json.loads((prior/'assembly.json').read_text('utf8'))['parts'];oldP={p['id']:p for p in was};oldz=np.load(prior/'assembly_meshes.npz');reuse={};hardware={}
 for id,p in D.items():
  if id not in oldP:continue
  old=oldP[id]
  if p['printable']:reuse[id]=sha(OUT/p['stl'])==sha(prior/old['stl'])
  elif id not in ['HL_N','HR_N']:
   hardware[id]=all(np.array_equal(z[k+str(p['index'])],oldz[k+str(old['index'])]) for k in ['v','f'])
 frozen=json.loads((prior/'manifest.json').read_text('utf8'))['files'];changed=[r['path'] for r in frozen if sha(prior/r['path'])!=r['sha256']]
 put(OUT/'verification/reuse.json',dict(passed=len(reuse)==11 and all(reuse.values()) and all(hardware.values()) and not changed,geometry_sha256=geo,identical_STLs=reuse,identical_retained_hardware=hardware,nut_orientation_change='HL_N and HR_N rotated 30 degrees, same M3 nut, to align flats with sliding guide',T4_files_checked=len(frozen),T4_changes=changed))
 single={id:len(P[id]['s'].decompose())==1 for id in ['H5-01','R5-01','W5-01']}
 report=dict(passed=all(x['passed'] for x in tests) and all(x['passed'] for x in tools) and all(not x['collisions'] for x in heights) and all(single.values()),geometry_sha256=geo,reaction_wall_and_capture=tests,one_connected_solid=single,preload_envelopes=heights,tools=tools,R_sidewall_mm=dict(T4=.35,T5=1.85),physical_tests_passed=False,notes=['User approved old H friction qualitatively. T5 is untested.','Continuous nominal annulus and captive flats do not certify printed strength or creep.','A8 force curve and friction coefficient unknown. Pair heights are geometry envelopes, not preload settings.','Ordinary captured nuts prevent rotation only; use witness marks and appropriate removable locking of metal threads.','Washer slot 1.1 for .8 washer; hex guide AF5.8 / depth2.8 for AF5.5 / h2.4 nut. Printed fit must be checked.'])
 put(OUT/'verification/mechanics.json',report)
 print(json.dumps(dict(passed=report['passed'],wall_capture=tests,tools=tools,reuse=len(reuse),old_changes=changed),ensure_ascii=False),flush=True)
 if not report['passed']:raise SystemExit(1)

if __name__=='__main__':main()
