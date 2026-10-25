"""Retain functional hand targets while using B/C wrist rotation order."""
from compact_arm import *
from scipy.optimize import least_squares

p=load(OLD/'profiles/arm_profile.json');ref=load(OLD/'reference/target_quinn.json');rows={}
ids=['shoulder_flex','shoulder_abduct','upperarm_roll','elbow_flex','forearm_roll','wrist_flex','wrist_deviation']
limits={x['id']:x['limits_deg'] for x in p['axes']}
for name,offset in [('drink',[25,12,10]),('head',[5,34,20])]:
    initial=a.poses()[name][1];goal=np.array(ref['points_mm']['head'])+offset;x0=np.array([initial[k] for k in ids])
    def q(x):return {**initial,**dict(zip(ids,x))}
    def residual(x):
        point=(frames(p,q(x))['hand_ball']@np.array([0,0,-28,1]))[:3]
        return np.r_[point-goal,(x-x0)*1e-5]
    sol=least_squares(residual,x0,bounds=([limits[k][0] for k in ids],[limits[k][1] for k in ids]),xtol=1e-12,ftol=1e-12,gtol=1e-12,max_nfev=1000)
    assert np.linalg.norm(residual(sol.x)[:3])<.001
    rows[name]=q(np.round(sol.x,6))
put(HERE/'reach_poses.json',rows)
print('Two reach poses solved without changing UE centres or bone lengths.')
