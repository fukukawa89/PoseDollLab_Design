"""Regression checks of interval bounds, including endpoint-clear collision."""
import numpy as np
from common import *
from continuous_clearance import Certificate
from rigid_collision import Body,Pair

def box(center,half):
 c=np.array(center);h=np.broadcast_to(half,(3,));v=np.array([[x,y,z] for x in (-1,1) for y in (-1,1) for z in (-1,1)])*h+c
 quads=[(0,1,3,2),(4,6,7,5),(0,4,5,1),(2,3,7,6),(0,2,6,4),(1,5,7,3)]
 return np.array([v[list(ids)] for q in quads for ids in ((q[0],q[1],q[2]),(q[0],q[2],q[3]))])

def main():
 rows=[];rng=np.random.default_rng(904)
 worst=0.
 for _ in range(5000):
  p=rng.uniform(-30,30,3);a0,b0=rng.uniform(-100,100,2);ha,hb=rng.uniform(0,100,2);da=rng.uniform(-ha,ha);db=rng.uniform(-hb,hb);A=rot([1,0,0],a0);B=rot([0,1,0],b0);pA=p@A
  chord=2*np.hypot(p[1],p[2])*np.sin(np.deg2rad(ha)/2)+2*np.hypot(pA[0],pA[2])*np.sin(np.deg2rad(hb)/2)
  actual=np.linalg.norm(p@rot([1,0,0],a0+da)@rot([0,1,0],b0+db)-pA@B);assert actual<=chord+1e-10;worst=max(worst,float(actual/(chord or 1)))
 rows.append({'case':'5000_rotated_point_chord_bounds','pass':True,'max_actual_to_bound_ratio':worst})
 a=box([0,0,5],.5);b=box([0,0,-5],.5);c=Certificate(a,b);r=c.cell((-5,5),(-5,5),.6);assert r['status']=='CERTIFIED_CONTINUOUS_NOMINAL_CLEARANCE';rows.append({'case':'separated_boxes_over_interval',**r})
 b=box([5,0,0],.5);c=Certificate(a,b)
 for beta in (-180,0):assert c.pair.check(B=rot([0,1,0],beta))['status'].startswith('CLEAR')
 r=c.cell((0,0),(-180,0),.05);assert r['status']!='CERTIFIED_CONTINUOUS_NOMINAL_CLEARANCE';rows.append({'case':'clear_endpoints_but_middle_collision',**r})
 c=Certificate(box([0,0,0],4),box([0,0,0],1));r=c.pair.check();assert r['status']=='PENETRATION';rows.append({'case':'containment_rejected_by_mandatory_initial_check',**r})
 m=core();c=Certificate(m['C01'],m['C02']);r=c.cell((15,15),(0,0),.6);assert r['status']!='CERTIFIED_CONTINUOUS_NOMINAL_CLEARANCE';r['independent_signed_witness_mm']=float(c.target.distance.EvaluateFunction(np.array([1.811018464081826e-7,-3.987763448537642,-2.327254729849317])@rot([1,0,0],15)));assert r['independent_signed_witness_mm']<.6;rows.append({'case':'existing_cup_gap_counterexample',**r})
 m=dict(np.load(OUT/'cup_relief_L3_R0p35/core_meshes.npz'));c=Certificate(m['C01'],m['C02']);r=c.cell((0,0),(0,0),.6);assert r['status']=='CERTIFIED_CONTINUOUS_NOMINAL_CLEARANCE';rows.append({'case':'new_mesh_neutral',**r})
 r=Certificate(box([0,0,0],.5),box([0,0,5],.5)).cell((-90,90),(-100,100),.6);assert r['status']=='CERTIFIED_CONTINUOUS_NOMINAL_CLEARANCE';rows.append({'case':'origin_exclusion_sphere_under_large_rotations',**r})
 save('continuous_method_regression.json',{'status':'PASS','cases':rows,'scope':'Mathematical bounds and selected independent analytic counterexamples. Not physical validation.'});print('PASS',len(rows),'groups')
if __name__=='__main__':main()
