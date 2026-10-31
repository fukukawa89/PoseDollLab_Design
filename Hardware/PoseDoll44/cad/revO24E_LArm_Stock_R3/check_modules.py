from validate_stock import *
a,ss=saved();S={p['name']:moved(s,F0[p['frame']]) for p,s in zip(a,ss)};rows=[]
def group(pre,other):return union([v for n,v in S.items() if n.startswith(pre+'_') or n in other])
rp=group('RP',['ROOT','SHOULDER_PITCH']);ru=group('RU',['SHOULDER_ABDUCT','UPPER_ARM']);rf=group('RF',['ELBOW_OUTPUT','FOREARM'])
for pre,fix,moving in [('HS',rp,ru),('HE',rp+ru+union(s for n,s in S.items() if n.startswith('HS_')),rf)]:
 r=next(x for x in load(OUT/'interfaces.json')['hinges'] if x['id']==pre);M=np.array(r['M']);inner=union(s for n,s in S.items() if n.startswith(pre+'_') and n.endswith(('_N','_RW','_K1','_K2','_F1')));fixed=fix+inner;v=[(moving.translate(-M[:3,2]*float(d))^fixed).volume() for d in np.linspace(60,0,241)];rows.append(dict(join=pre,max_overlap_mm3=max(v),passed=max(v)<.02))
for r,on in zip(load(OUT/'interfaces.json')['rolls'],['SHOULDER_PITCH','UPPER_ARM','FOREARM']):
 iw=np.linalg.inv(r['W']);rotor=moved(S[on],iw);metals=union(moved(s,iw) for n,s in S.items() if n.startswith(r['id']+'_') and n!=r['keeper']);vs=[(rotor.translate([0,0,d])^metals).volume() for d in [-.25,.25]];rows.append(dict(rotor=r['id'],output_ear_axial_stop_overlap_mm3=vs,passed=min(vs)>.02))
put(OUT/'verification/module_joining.json',dict(status='PASS_GEOMETRY' if all(r['passed'] for r in rows) else 'FAIL',geometry_sha256=sha(OUT/'production_meshes.npz'),rows=rows,scope='Joining complete RP/RU/RF subassemblies after their individual hardware is installed, at zero adjustable angles; output-ear independent stops also checked.'))
print(rows)
