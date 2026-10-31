from check_stock import *
a,ss=saved();S={p['name']:s for p,s in zip(a,ss)};P={p['name']:p for p in a}
for name in ['arms_wrist_flex','arms_wrist_extend']:
 f=frames(POSES[name]['angles'])
 for n in ['KEEP_E-H1154','KEEP_E-H1162']:
  hit=moved(S['FOREARM'],f[P['FOREARM']['frame']])^moved(S[n],f[P[n]['frame']])
  if hit.volume()>.02:print(name,n,hit.volume(),e.bounds(moved(hit,np.linalg.inv(f['l_wrist_flex']))).tolist())
print('wrist output',e.bounds(S['KEEP_E-P018']).tolist())
