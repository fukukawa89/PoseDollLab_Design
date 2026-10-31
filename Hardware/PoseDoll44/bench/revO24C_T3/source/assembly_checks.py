from audit import *

def main():
 d=build();P={p['id']:p for p in d.parts};steps=[];fail=[];samples=0
 def path(label,ids,installed,delta):
  nonlocal samples
  delta=np.array(delta,float);n=int(np.linalg.norm(delta)/.5)+1;worst=[]
  for t in np.linspace(1,0,n):
   for id in ids:
    s=P[id]['s'].translate(delta*t);b=bounds(s)
    for other in installed:
     s2=P[other]['s']
     if not overlap(b,bounds(s2)):continue
     vol=(s^s2).volume()
     if vol>.02:
      worst.append(dict(a=id,b=other,volume=round(vol,5),fraction=float(t)));break
   samples+=1
  steps.append(dict(label=label,ids=ids,offset_mm=delta.tolist(),samples=n,passed=not worst))
  if worst:fail.append(dict(label=label,examples=worst[:8]))
  installed.extend(ids)
 def addmany(label,ids,inst,delta):
  for id in ids:path(label+' '+id,[id],inst,delta)
 # H split reaction seat and compact fork.
 inst=['H3-01']
 addmany('H 合模面装金属反力组件',['HL_N','HR_N','HL_RW','HR_RW'],inst,[20,0,0])
 path('H 合拢固定叉',['H3-02'],inst,[20,0,0])
 for z in [28,36]:
  path('H 装普通合模螺母',['HC'+str(z)+'N'],inst,[20,0,0])
  addmany('H 合模紧固',['HC'+str(z)+'W','HC'+str(z)+'B'],inst,[-25,0,0])
 for side,prefix in [(-1,'HL_'),(1,'HR_')]:path('H 内侧摩擦垫',[prefix+'F1'],inst,[0,side*25,0])
 path('H 转动叉从远端套入',['H3-03'],inst,[0,0,-40])
 for side,prefix in [(-1,'HL_'),(1,'HR_')]:addmany('H 外侧预紧堆叠',[prefix+x for x in ['F2','S1','S2','HW','AX']],inst,[0,side*25,0])
 # R: first captive M2 nuts in the free rotor; then insert that subassembly.
 inst=['R3-01'];addmany('R 合模面反力组件',['R_N','R_RW'],inst,[20,0,0]);path('R 合拢固定芯',['R3-02'],inst,[20,0,0])
 for y in [-7.4,7.4]:
  path('R 普通合模螺母',['RC'+str(y)+'N'],inst,[-20,0,0]);addmany('R 合模紧固',['RC'+str(y)+'W','RC'+str(y)+'B'],inst,[20,0,0])
 sub=['R3-03'];addmany('R 先在转盘背面放壳体螺母',['RO-8.5N','RO8.5N'],sub,[0,0,20])
 path('R 固定芯端面摩擦垫',['R_F1'],inst,[0,0,-25]);path('R 带预装螺母的转盘',sub,inst,[0,0,-30])
 addmany('R 预紧堆叠',['R_F2','R_S1','R_S2','R_HW','R_AX'],inst,[0,0,-25]);path('R 输出壳罩住碟簧',['R3-04'],inst,[0,0,-30])
 for y in [-8.5,8.5]:addmany('R 壳体紧固',['RO'+str(y)+'W','RO'+str(y)+'B'],inst,[0,0,-25])
 # W spherical components: cups close BEFORE inserting shoulder guide pins.
 inst=['W3-01'];addmany('W 球合模面金属件',['Wguide_nut_-1','Wguide_nut_1','Wguide_w_-1','Wguide_w_1','W3-03'],inst,[20,0,0]);path('W 合拢球体',['W3-02'],inst,[20,0,0])
 for z in [-5.5,5.5]:
  path('W 球合模尼龙锁紧螺母',['Wball_nut_'+str(z)],inst,[-20,0,0]);path('W 球合模螺钉',['Wball_bolt_'+str(z)],inst,[20,0,0])
 for side,cu,li in [(-1,'W3-08','W3-04'),(1,'W3-07','W3-05')]:
  sub=[cu];path('W 衬片从朝球心入口装入',[li],sub,[0,-side*15,0])
  for x in [-8.5,8.5]:
   pre='WL'+str(side)+'_'+str(x)
   path('W 衬片普通螺母',[pre+'N'],sub,[0,side*20,0])
   addmany('W 从球心侧装衬片垫圈和螺钉',[pre+'W',pre+'B'],sub,[0,-side*20,0])
  path('W 带衬片的球窝合拢（尚不装导向肩钉）',sub,inst,[0,side*30,0])
 for side in [-1,1]:path('W 最后旋入导向轴肩钉',['Wguide_'+str(side)],inst,[0,side*25,0])
 for x in [-8,8]:
  pre='WP'+str(x);path('W 预紧普通M4螺母',[pre+'N'],inst,[0,-25,0]);addmany('W 碟簧预紧堆叠',[pre+s for s in ['W0','S1','S2','W1','B']],inst,[0,25,0])
 path('W 掌柄套入球颈',['W3-09'],inst,[0,0,-30]);path('W 掌柄普通螺母',['WPALM_N'],inst,[-20,0,0]);addmany('W 掌柄紧固',['WPALM_W','WPALM_B'],inst,[20,0,0])
 put(OUT/'verification/assembly_paths.json',dict(passed=not fail,geometry_sha256=sha(OUT/'assembly_meshes.npz'),samples=samples,step_mm=.5,steps=steps,failures=fail,scope='Rigid straight insertion paths at neutral pose; no thread helix, elastic snap, printer error, hand size or actual tool torque simulation. Captured nuts and staged subassemblies are installed before enclosing parts.'))
 print('ASSEMBLY',len(steps),samples,'failures',json.dumps(fail,ensure_ascii=False),flush=True)

 # Fitted physical axes from exported meshes, independent of frame labels.
 z=np.load(OUT/'assembly_meshes.npz');rows=json.loads((OUT/'assembly.json').read_text('utf8'))['parts'];D={r['id']:r for r in rows}
 def circle(id,axes,radius):
  v=z['v'+str(D[id]['index'])];v=v[abs(np.linalg.norm(v[:,axes],axis=1)-radius)<.00002][:,axes]
  c=np.linalg.lstsq(np.c_[2*v,np.ones(len(v))],np.sum(v*v,axis=1),rcond=None)[0]
  return dict(center_mm=c[:2].tolist(),radius_mm=float(np.sqrt(c[2]+sum(c[:2]**2))),vertices=len(v))
 hc=circle('H3-03',[0,2],2.125);rc=circle('R3-03',[0,1],2.125)
 verts=np.vstack([z['v'+str(D[id]['index'])] for id in ['W3-01','W3-02']]);v=verts[abs(np.linalg.norm(verts,axis=1)-11)<.00005]
 fit=np.linalg.lstsq(np.c_[2*v,np.ones(len(v))],np.sum(v*v,axis=1),rcond=None)[0];wc=fit[:3]
 ref=json.loads((H/'bench/revO24/reference.json').read_text('utf8')) if (H/'bench/revO24/reference.json').exists() else a.reference()[0]
 E=np.array(ref['points_mm']['lowerarm_l']);W=np.array(ref['points_mm']['hand_l']);werr=float(np.linalg.norm(E+np.array([0,0,-FORE])+wc-W))
 put(OUT/'verification/ue_alignment.json',dict(passed=max(np.linalg.norm(hc['center_mm']),np.linalg.norm(rc['center_mm']),werr)<1e-5,H_bore=hc,R_bore=rc,W_ball_center_local_mm=wc.tolist(),W_reference_error_mm=werr,forearm_mm=FORE,reference=ref['asset'],scope='Mesh-fitted H axis through E, R axis collinear E-W, spherical W at original UE W; no physical calibration or fullbody height measurement.'))

 # Every shoulder stack stays away from its blind shoulder floor; actual force unmeasured.
 heights=[]
 for h in [.9,1.,1.1,1.2]:
  dh=build(h);bad=collisions(scene_parts(dh));heights.append(dict(pair_height_mm=h,collisions=bad,stack_rows=dh.stacks))
 # Exclude designed contact surfaces: these selected packaging gaps are unrelated to friction.
 geom={p['id']:s for p,s,b in scene_parts(d,q=145)}
 gaps=[]
 for aa,bb in [('H3-01','H3-03'),('H3-02','H3-03'),('H3-02','H_R_B'),('R3-04','W3-08')]:gaps.append(dict(a=aa,b=bb,gap_mm=geom[aa].min_gap(geom[bb],5),at_elbow_deg=145))
 area=[]
 for wid,rid,direction in [('HR_F1','H3-03',[0,.02,0]),('HL_F1','H3-03',[0,-.02,0]),('R_F1','R3-03',[0,0,-.02])]:
  area.append(dict(washer=wid,rotor=rid,area_mm2=(P[wid]['s'].translate(direction)^P[rid]['s']).volume()/.02))
 fasteners=[('H合模',1.5,.5),('H-R方键',1.1,.5),('R合模',1.5,.4),('R壳盖',.8,.4),('W球体尼龙锁紧',1.,.4),('W导向肩钉',1.9,.4),('W衬片',1.3,.4),('R-W方键',3.1,.5),('W掌柄',3.5,.4),('F3-R',3.1,.5),('F3-W',5.4,.4)]
 toolchecks=[]
 for bid,start,end,exclude_station in [('HL_AX',[0,-19.81,0],[0,-50,0],None),('HR_AX',[0,19.81,0],[0,50,0],None),('R_AX',[0,0,-9.81],[0,0,-55],'R'),('WP-8B',[-8,20.11,19],[-8,55,19],'W'),('WP8B',[8,20.11,19],[8,55,19],'W')]:
  tool=cyl(start,end,1.85);hits=[]
  for p in d.parts:
   if p['bench_only'] or p['id']==bid or p['station']!=(exclude_station or 'H'):continue
   if overlap(bounds(tool),bounds(p['s'])) and (tool^p['s']).volume()>.02:hits.append(p['id'])
  toolchecks.append(dict(screw=bid,passed=not hits,obstructions=hits,tool_diameter_mm=3.7,condition='R test with W and interface crossbolt removed' if bid=='R_AX' else 'neutral joint'))
 put(OUT/'verification/mechanics.json',dict(passed=all(not r['collisions'] for r in heights) and all(x[1]>=2*x[2]-.00001 for x in fasteners) and all(t['passed'] for t in toolchecks),geometry_sha256=sha(OUT/'assembly_meshes.npz'),preload_envelopes=heights,selected_gaps=gaps,friction_face_probe=area,fastener_exit=[dict(name=n,exit_mm=g,pitch_mm=p) for n,g,p in fasteners],tools=toolchecks,physical_force_verified=False,notes=['A8 force curve and coefficient of friction are unknown.','Free steel washers can slip; do not assume twice the friction torque per ear.','Negative W cup is integral with bone bridge; positive cup alone moves to close spherical clearance. Small seating movement from .05mm radial fit gap is distinct from an unlocated socket.','Test negative W ear nut wall 3.7mm; H/R reaction wall2.8mm. No strength/creep qualification claimed.']))
 print('MECHANICS',json.dumps(dict(heights=[len(x['collisions']) for x in heights],gaps=gaps,areas=area,tools=toolchecks),ensure_ascii=False),flush=True)
if __name__=='__main__':main()
