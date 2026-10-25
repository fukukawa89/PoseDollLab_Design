from arm_kit import *

def along(path,t):
 v=np.array(path,float);lengths=np.linalg.norm(np.diff(v,axis=0),axis=1);distance=t*sum(lengths)
 for i,length in enumerate(lengths):
  if distance<=length or i==len(lengths)-1:return v[i]+(v[i+1]-v[i])*(distance/length if length else 1)
  distance-=length
 return v[-1]

def main():
 rawpath=ROOT/'output/playwright/o24ct5-tutorial-browser-raw.txt';raw=rawpath.read_text('utf-8-sig')
 assert '### Result\n' in raw,raw[:2000]
 result=json.JSONDecoder().raw_decode(raw.split('### Result\n',1)[1].lstrip())[0]
 data=json.loads((OUT/'tutorial/steps.json').read_text('utf8'));geo=sha(OUT/'assembly_meshes.npz');assert result['passed'] and result['geometry_sha256']==data['geometry_sha256']==geo
 err=0.;states=result['states']
 for q in states:
  s=data['lessons'][q['station']]['steps'][q['index']];t=q['t']
  for id,m in q['matrices'].items():
   off=along(s['paths'][id],t*t*(3-2*t)) if id in s['paths'] else s['before'].get(id,[0,0,0]);expected=a.T(off)
   err=max(err,float(np.max(np.abs(expected-np.array(m).reshape(4,4)))))
  if q['rom']:
   qangle,v=q['angles'];st=q['station']
   angle=along([[0],[145],[0]],t)[0] if st=='H' else along([[0],[-85],[80],[0]],t)[0] if st=='R' else along([[0],[-65],[70],[0]],t/.55)[0] if t<.55 else 0.
   dev=along([[0],[-20],[30],[0]],(t-.55)/.45)[0] if st=='W' and t>=.55 else 0.
   assert abs(qangle-angle)<1e-8 and abs(v-dev)<1e-8
   for id,m in q['rom'].items():
    f=data['catalog'][id]['frame'];expected=np.eye(4)
    if f=='rotor':expected=rot(Y if st=='H' else Z,-angle)
    if f=='flex':expected=rot(Y,angle)
    if f=='hand':expected=rot(Y,angle)@rot(X,dev)
    err=max(err,float(np.max(np.abs(expected-np.array(m).reshape(4,4)))))
 for r in result['orientationChecks']:
  expected=data['catalog'][r['id']]['orientation'];shown=r['before']['state']
  assert np.max(np.abs(np.array(expected['normal'])-shown['normal']))<1e-8
  assert np.max(np.abs(np.array(expected['face'])-shown['face']))<1e-8
 assert result['steps']==sum(len(l['steps']) for l in data['lessons'].values()) and result['additions']==len(data['catalog'])
 assert result['auto_stopped'] and result['pause_worked'] and not result['mobile']['overflow'] and result['offline']['ready']
 assert err<1e-8,err
 report=dict(passed=True,geometry_sha256=geo,steps=result['steps'],unique_additions=result['additions'],states_checked=len(states),max_matrix_error=err,edition=data['tutorial_edition'],orientation_checks=result['orientationChecks'],mobile=result['mobile'],offline=result['offline'],auto_stopped=result['auto_stopped'],pause_worked=result['pause_worked'],errors=result['errors'],raw_result_sha256=sha(rawpath),checked_assets={p.name:sha(p) for p in (OUT/'tutorial').iterdir() if p.suffix in ['.js','.html','.css','.json']})
 put(OUT/'verification/tutorial_browser.json',report);print(json.dumps({k:report[k] for k in ['passed','steps','unique_additions','states_checked','max_matrix_error']},ensure_ascii=False))

if __name__=='__main__':main()
