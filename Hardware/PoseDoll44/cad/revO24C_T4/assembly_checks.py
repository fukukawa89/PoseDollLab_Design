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
     if overlap(b,bounds(s2)):
      vol=(s^s2).volume()
      if vol>.02:worst.append(dict(a=id,b=other,volume=round(vol,5),fraction=float(t)));break
   samples+=1
  steps.append(dict(label=label,ids=ids,offset_mm=delta.tolist(),samples=n,passed=not worst))
  if worst:fail.append(dict(label=label,examples=worst[:6]))
  installed.extend(ids)
 def addmany(label,ids,inst,delta):
  for id in ids:path(label+' '+id,[id],inst,delta)
 inst=['W4-02']
 for axis in ['Y','X']:
  for sign in [-1,1]:
   pre='W'+axis+('M_' if sign<0 else 'P_')
   addmany('从合模面放入普通螺母及反力垫',[pre+'N',pre+'RW'],inst,[0,0,20])
 path('合上十字芯',['W4-03'],inst,[0,0,25])
 for x in [-5,5]:
  for y in [-5,5]:
   pre=f'WC{x}_{y}'
   path('从底面深槽装普通M2',[pre+'N'],inst,[0,0,-25])
   addmany('合模垫圈及M2x16',[pre+'W',pre+'B'],inst,[0,0,25])
 for axis,piece,offset in [('Y','W4-01',[0,0,40]),('X','W4-04',[0,0,-40])]:
  for sign in [-1,1]:
   pre='W'+axis+('M_' if sign<0 else 'P_');delta=sign*(Y if axis=='Y' else X)*25
   path('内侧摩擦垫',[pre+'F1'],inst,delta)
  path('转动叉从开口侧套入',[piece],inst,offset)
  for sign in [-1,1]:
   pre='W'+axis+('M_' if sign<0 else 'P_');delta=sign*(Y if axis=='Y' else X)*25
   addmany('外侧摩擦垫／碟簧／头下垫／肩钉',[pre+s for s in ['F2','S1','S2','HW','AX']],inst,delta)
 path('原掌柄从远端装入',['W3-09'],inst,[0,0,-35]);path('掌柄普通M2',['WPALM_N'],inst,[-20,0,0]);addmany('掌柄紧固',['WPALM_W','WPALM_B'],inst,[20,0,0])
 # Alternate removable fixtures use the same joint, rather than a larger coupon.
 fixture_inst=[i for i in inst if not i.startswith('WPALM_') and i!='W3-09']
 path('原100mm加载杆',['F3-W'],fixture_inst,[0,0,-35])
 addmany('测试杆负侧垫圈与普通M2',['FW_W2','FW_N'],fixture_inst,[-25,0,0]);addmany('测试杆正侧垫圈与M2x20',['FW_W1','FW_B'],fixture_inst,[25,0,0])
 path('原测试夹持柄',['F3-M'],fixture_inst,[0,0,35]);path('夹持柄普通M3',['W_R_N'],fixture_inst,[-25,0,0]);addmany('夹持柄垫圈与M3x20',['W_R_W','W_R_B'],fixture_inst,[25,0,0])
 put(OUT/'verification/assembly_paths.json',dict(passed=not fail,geometry_sha256=sha(OUT/'assembly_meshes.npz'),samples=samples,step_mm=.5,steps=steps,failures=fail,scope='Wrist and removable fixtures, neutral straight insertion, complete hardware; thread helices, hands and elastic effects not simulated. Unchanged H/R paths are covered by T3 with exact mesh reuse verification.'))
 print('ASSEMBLY',len(steps),samples,'failures',json.dumps(fail,ensure_ascii=False),flush=True)
 # Independently fit the actual exported bores, not just named frame origins.
 z=np.load(OUT/'assembly_meshes.npz');D={r['id']:r for r in json.loads((OUT/'assembly.json').read_text('utf8'))['parts']}
 def circle(id,axes,radius):
  vs=z['v'+str(D[id]['index'])];v=vs[abs(np.linalg.norm(vs[:,axes],axis=1)-radius)<.00002][:,axes]
  c=np.linalg.lstsq(np.c_[2*v,np.ones(len(v))],np.sum(v*v,axis=1),rcond=None)[0]
  return dict(center_mm=c[:2].tolist(),radius_mm=float(np.sqrt(c[2]+sum(c[:2]**2))),vertices=len(v))
 fits={k:circle(*args) for k,args in {'H':('H3-03',[0,2],2.125),'R':('R3-03',[0,1],2.125),'W_Y':('W4-01',[0,2],2.125),'W_X':('W4-04',[1,2],2.125)}.items()}
 ref=a.reference()[0];E=np.array(ref['points_mm']['lowerarm_l']);W=np.array(ref['points_mm']['hand_l'])
 er=float(np.linalg.norm(E+[0,0,-FORE]-W));fe=max(np.linalg.norm(c['center_mm']) for c in fits.values())
 put(OUT/'verification/ue_alignment.json',dict(passed=max(er,fe)<1e-5,fitted_bores=fits,wrist_reference_error_mm=er,forearm_mm=FORE,wrist_axis_order='Ry(flex) @ Rx(deviation)',reference_asset=ref['asset'],scope='Nominal exported-mesh axis fits. Both wrist axes intersect UE W; X axis follows Y flex. Not physical tolerance or measured fullbody height.'))
 heights=[]
 for h in [.9,1.,1.1,1.2]:
  dh=build(h);bad=collisions(scene_parts(dh));heights.append(dict(pair_height_mm=h,collisions=bad,stack_rows=dh.stacks))
 tools=[]
 for axis in ['Y','X']:
  for sign in [-1,1]:
   vec=sign*(Y if axis=='Y' else X);pre='W'+axis+('M_' if sign<0 else 'P_')
   tool=cyl(vec*19.81,vec*60,1.85);hits=[]
   for p in d.parts:
    if p['bench_only'] or p['station']!='W' or p['id']==pre+'AX':continue
    if overlap(bounds(tool),bounds(p['s'])) and (tool^p['s']).volume()>.02:hits.append(p['id'])
   tools.append(dict(screw=pre+'AX',diameter_mm=3.7,passed=not hits,obstructions=hits,condition='neutral wrist; straight 3mm hex tool'))
 areas=[]
 for axis,piece in [('Y','W4-01'),('X','W4-04')]:
  for sign in [-1,1]:
   pre='W'+axis+('M_' if sign<0 else 'P_');delta=sign*(Y if axis=='Y' else X)*.02
   areas.append(dict(washer=pre+'F1',rotor=piece,area_mm2=(P[pre+'F1']['s'].translate(delta)^P[piece]['s']).volume()/.02))
 # Check smallest external packaging gap for each selected moving pair.
 gaps=[]
 for w,v in [(-65,-20),(-65,30),(70,-20),(70,30),(0,0)]:
  solids={p['id']:s for p,s,b in scene_parts(d,w=w,v=v)}
  for aa,bb in [('W4-01','W4-04'),('W4-01','W4-02'),('W4-01','WXP_AX'),('R3-04','W4-01')]:
   gaps.append(dict(a=aa,b=bb,angles=[w,v],gap_mm=solids[aa].min_gap(solids[bb],5)))
 exits=[dict(name='cross-core M2x16',exit_mm=1.1,pitch_mm=.4),dict(name='palm M2x14',exit_mm=3.5,pitch_mm=.4),dict(name='R-W M3x20',exit_mm=3.1,pitch_mm=.5)]
 # Four axes' shoulder tips never reach W: minimum radius 2.7mm, with 3mm threads.
 put(OUT/'verification/mechanics.json',dict(passed=all(not x['collisions'] for x in heights) and all(x['passed'] for x in tools) and all(x['exit_mm']>=2*x['pitch_mm'] for x in exits),geometry_sha256=sha(OUT/'assembly_meshes.npz'),preload_envelopes=heights,tools=tools,friction_face_probes=areas,selected_gaps=gaps,fastener_exit=exits,physical_tests_passed=False,notes=['A8 force curve and friction coefficient unknown; geometry does not certify holding force.','Each wrist axis has two independently accessible opposed A8 pairs. Alternate adjustments on opposite sides.','Captured ordinary nuts prevent nut rotation only; screw loosening still needs marks and a suitable metal-thread locking method.','3mm solid friction ears; fixed reaction wall 2.8mm; no strength or creep qualification.','Pair heights .9 to 1.2mm are CAD sweep positions, not force or tightening specifications. Never flatten the .8mm pair.']))
 print('MECHANICS',json.dumps(dict(heights=[len(x['collisions']) for x in heights],tools=tools,areas=areas),ensure_ascii=False),flush=True)

if __name__=='__main__':main()
