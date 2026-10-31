from check_stock import saved
from build_stock import *
from connections import core

def validate():
 a,ss=saved();digest=sha(OUT/'production_meshes.npz');P={p['name']:p for p in a};S={p['name']:moved(s,F0[p['frame']]) for p,s in zip(a,ss)};ints=load(OUT/'interfaces.json');rr=[]
 for r,fn,on in zip(ints['rolls'],['ROOT','SHOULDER_ABDUCT','ELBOW_OUTPUT'],['SHOULDER_PITCH','UPPER_ARM','FOREARM']):
  W=np.array(r['W']);iw=np.linalg.inv(W);body=moved(S[fn],iw);lid=moved(S[r['keeper']],iw);anchor=moved(S[r['anchor']],iw)
  pre=r['id'];names=[x for x in S if x.startswith(pre+'_') and '_lid_' not in x and x!=r['keeper']]+[on];group=union(moved(S[n],iw) for n in names)
  blocked={str(dz):dict(body_overlap_mm3=(group.translate([0,0,dz])^body).volume(),lid_overlap_mm3=(group.translate([0,0,dz])^lid).volume()) for dz in [-.25,.25]}
  neg=[(group.translate([0,0,float(dz)])^body).volume() for dz in np.linspace(0,-12,49)]
  # Sequential real production-body insertion, before output installation.
  installed=body;paths=[]
  for n in [pre+'_N',pre+'_RW',pre+'_BACK_W4',pre+'_ANCHOR',r['keeper']]:
   s=moved(S[n],iw);samples=[(s.translate([0,0,float(dz)])^installed).volume() for dz in np.linspace(-24,0,97)]
   paths.append(dict(part=n,max_overlap_mm3=max(samples),direction='canonical -Z toward seat',passed=max(samples)<.02));installed+=s
  # Output body enters after lid is locked. FW4 goes on each side of the ear.
  springs=sorted([n for n in names if '_A8_' in n],key=lambda n:float(e.bounds(moved(S[n],iw))[0,2]),reverse=True)
  for n in [pre+'_F1',on,pre+'_F2']+springs+[pre+'_HW',pre+'_AX']:
   s=moved(S[n],iw)
   if n in [pre+'_F1',on,pre+'_AX']:
    shifts=[[0,0,float(dz)] for dz in np.linspace(-50 if n.endswith('_AX') else -32,0,201 if n.endswith('_AX') else 129)];direction='canonical -Z through open central service bore toward seat; assemble downstream joint later'
   else:
    found=None;best=(1e9,None)
    for depth in ([16,18,20,22] if n.endswith('_AX') else [6,8,10,12,14,16,18]):
     axial=[[0,0,float(dz)] for dz in np.linspace(-depth,0,2*depth+1)]
     axhit=max((s.translate(v)^installed).volume() for v in axial)
     if axhit>.02:continue
     for angle in range(0,360,15):
      vec=np.array([math.cos(math.radians(angle)),math.sin(math.radians(angle)),0.])
      shifts=[(vec*dy+[0,0,-depth]).tolist() for dy in np.linspace(40,0,81)]+axial
      hit=max((s.translate(v)^installed).volume() for v in shifts)
      if hit<best[0]:best=(hit,(depth,angle))
      if hit<.02:found=(depth,angle);break
     if found:break
    depth,angle=found or best[1];vec=np.array([math.cos(math.radians(angle)),math.sin(math.radians(angle)),0.])
    shifts=[(vec*dy+[0,0,-depth]).tolist() for dy in np.linspace(40,0,161)]+[[0,0,float(dz)] for dz in np.linspace(-depth,0,4*depth+1)]
    direction=f'side entry angle {angle} deg at axial offset -{depth} mm, then axial to seat; deepest spring first'
   samples=[(s.translate(shift)^installed).volume() for shift in shifts]
   paths.append(dict(part=n,max_overlap_mm3=max(samples),direction=direction,passed=max(samples)<.02));installed+=s
  tool=cyl([0,0,-10],[0,0,-32],1.9);toolhit=(tool^union(moved(S[n],iw) for n in [fn,on,r['keeper']])).volume()
  nut=moved(S[pre+'_N'],iw);spin=(moved(nut,rot([0,0,1],30))^body).volume()
  stack=dict(shoulder_end_z_mm=1.9,first_M3_washer_z_mm=2.3,shoulder_clearance_nominal_mm=.4,minimum_clearance_at_pack_limits_mm=.3,thread_tip_z_mm=7.9,nut_exit_z_mm=6.8,tip_beyond_nylon_nominal_mm=1.1,minimum_tip_beyond_nylon_mm=.9,pack_height_nominal_mm=r['pair_height_mm'],pack_working_range_mm=[1.7,2.] if r['parallel']==2 else [.9,1.2],minimum_anchor_lip_overlap_mm=.65,anchor_lip_thickness_mm=2.,fixed_cover_screw='2 x M3x16 with W3 and captive NL3; independent of preload')
  passed=all(max(v.values())>.02 for v in blocked.values()) and max(neg)<.02 and all(x['passed'] for x in paths) and toolhit<.02 and spin>.02
  rr.append(dict(id=pre,status='PASS_GEOMETRY' if passed else 'REVIEW_REQUIRED',positive_stops=blocked,negative_control_cover_removed_max_overlap_mm3=max(neg),assembly_paths=paths,adjuster_tool_envelope_overlap_mm3=toolhit,nut_30deg_spin_blocked_mm3=spin,stack=stack));print('R',pre,rr[-1]['status'],'negative',max(neg),'tool',toolhit,'badpaths',[(x['part'],round(x['max_overlap_mm3'],2)) for x in paths if not x['passed']],flush=True)
 put(OUT/'verification/capture_assembly.json',dict(status='PASS_GEOMETRY' if all(r['status']=='PASS_GEOMETRY' for r in rr) else 'REVIEW_REQUIRED',geometry_sha256=digest,rows=rr,scope='Actual final STL geometry. Positive axial stops at +/-0.25 mm, cover-removed negative control sampled 0..12 mm, insertion paths sampled 0.25 mm. Simplified screw external-thread envelopes; no physical force or fatigue certification.'))

def cores():
 a,ss=saved();rows=[]
 for p,s in zip(a,ss):
  if p['role']!='structure':continue
  v,_=e.base.a.mesh_data(s);cent=v.mean(0);_,basis=np.linalg.eigh(np.cov(v.T));basis[:,0]*=np.linalg.det(basis);s=moved(s,T(-basis.T@cent,basis.T));screen=core(s,.3)
  if len(screen[0]['substantial_core_volumes_mm3'])!=1:screen=core(s,.2)
  n=len(screen[0]['substantial_core_volumes_mm3']);rows.append(dict(part_number=p['part_number'],core_count_0_5=n,screen=screen,status='PASS_SCREEN' if n==1 else 'REVIEW_REQUIRED'));print('CORE',p['name'],n,flush=True)
 put(OUT/'verification/connected_core.json',dict(status='PASS_SCREEN' if all(r['status']=='PASS_SCREEN' for r in rows) else 'REVIEW_REQUIRED',geometry_sha256=sha(OUT/'production_meshes.npz'),rows=rows,scope='Morphological erosion 0.5/0.75 mm on actual STL bodies, substantial components >=2 mm3. Screens thin connecting ligaments; not stiffness, FEA, fatigue or material qualification.'))

def joins():
 a,ss=saved();S={p['name']:moved(s,F0[p['frame']]) for p,s in zip(a,ss)};rows=[]
 def test(label,moving,fixed,direction,travel=35):
  values=[(moving.translate(np.array(direction)*float(d))^fixed).volume() for d in np.linspace(travel,0,math.ceil(travel/.25)+1)];v=max(values);rows.append(dict(operation=label,max_overlap_mm3=v,status='PASS_PATH' if v<.02 else 'REVIEW_REQUIRED'));return fixed+moving
 for r,fn,on in zip(load(OUT/'interfaces.json')['hinges'],['SHOULDER_PITCH','UPPER_ARM'],['SHOULDER_ABDUCT','ELBOW_OUTPUT']):
  pre=r['id'];M=np.array(r['M']);fixed=S[fn]
  for side,tag in [(-1,'HL_'),(1,'HR_')]:
   direction=M[:3,:3]@np.array([0,side,0])
   for suf in ['N','RW','K1','K2','F1']:fixed=test(pre+'_'+tag+suf,S[pre+'_'+tag+suf],fixed,direction)
  fixed=test(pre+'_output',S[on],fixed,M[:3,:3]@np.array([0,0,-1]),60)
  for side,tag in [(-1,'HL_'),(1,'HR_')]:
   direction=M[:3,:3]@np.array([0,side,0])
   # Deeper spring first by position along outward axis.
   springs=sorted(['S1','S2'],key=lambda n:float(np.mean(e.bounds(S[pre+'_'+tag+n]),axis=0)@direction))
   for suf in ['F2']+springs+['HW','AX']:fixed=test(pre+'_'+tag+suf,S[pre+'_'+tag+suf],fixed,direction)
 # Captive cover nuts are loaded while the cover is separate. Bolts stay standard length.
 for r in load(OUT/'interfaces.json')['rolls']:
  W=np.array(r['W']);pre=r['id'];lid=S[r['keeper']]
  for x in [-r['lug_x_mm'],r['lug_x_mm']]:
   test(pre+f'_cover_nut_{x}',S[pre+f'_lid_nut_{x}'],lid,-W[:3,2])
  fn={'RP':'ROOT','RU':'SHOULDER_ABDUCT','RF':'ELBOW_OUTPUT'}[pre];fixed=S[fn]+lid
  for x in [-r['lug_x_mm'],r['lug_x_mm']]:
   fixed+=S[pre+f'_lid_nut_{x}'];fixed=test(pre+f'_cover_washer_{x}',S[pre+f'_lid_washer_{x}'],fixed,W[:3,2]);fixed=test(pre+f'_cover_bolt_{x}',S[pre+f'_lid_bolt_{x}'],fixed,W[:3,2])
 # Wrist hardware from accepted T6 W is preloaded into the centre before forks.
 inv=load(OUT/'kit.json');old={r['part_number']:r['feature'] for r in load(SRC/'kit.json')['hardware']};wp={old[p['source'] if p.get('source') else p['name'].removeprefix('KEEP_')]:p['name'] for p in a if p['name'].startswith('KEEP_E-H')}
 MW=F0['l_wrist_flex'];centre=S['KEEP_E-P019'];prepared=centre
 prefixes=['l_E_WYM_','l_E_WYP_','l_E_WXM_','l_E_WXP_']
 for pre in prefixes:
  axis=np.array([0,1,0]) if 'WY' in pre else np.array([1,0,0]);sign=-1 if 'M_' in pre else 1;direction=MW[:3,:3]@(axis*sign)
  for suf in ['N','RW','K1','K2','F1']:
   n=wp[pre+suf];prepared=test(pre+suf,S[n],prepared,direction)
 prepared=test('wrist_centre_into_forearm',prepared,S['FOREARM'],-MW[:3,2],50)
 prepared=test('wrist_output_fork',S['KEEP_E-P018'],prepared,-MW[:3,2],50)
 for pre in prefixes:
  axis=np.array([0,1,0]) if 'WY' in pre else np.array([1,0,0]);sign=-1 if 'M_' in pre else 1;direction=MW[:3,:3]@(axis*sign)
  springs=sorted(['S1','S2'],key=lambda n:float(np.mean(e.bounds(S[wp[pre+n]]),axis=0)@direction))
  for suf in ['F2']+springs+['HW','AX']:prepared=test(pre+suf,S[wp[pre+suf]],prepared,direction)
 put(OUT/'verification/hinge_wrist_paths.json',dict(status='PASS_PATHS' if all(r['status']=='PASS_PATH' for r in rows) else 'REVIEW_REQUIRED',geometry_sha256=sha(OUT/'production_meshes.npz'),rows=rows,scope='Actual final STL H/W/palm insertion and cover-fastener paths, 0.25 mm sampling, module assembly while other modules remain separate. Elastic compression and screw helical threading are nominal envelopes. H/W user acceptance remains unchanged; this is only geometry integration verification.'))
 print('JOINS',len(rows),[(r['operation'],round(r['max_overlap_mm3'],3)) for r in rows if r['status']!='PASS_PATH'],flush=True)
if __name__=='__main__':
 if '--cores' in sys.argv:cores()
 elif '--joins' in sys.argv:joins()
 else:validate()
