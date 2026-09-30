"""Inextensible spiral-path feasibility study for four separate twist conductors.
This is a kinematic candidate family, NOT a predicted elastic equilibrium or
fatigue qualification. Raw conductor OD and bend screen are inherited.
"""
from pathlib import Path
import json,hashlib
import numpy as np
H=Path(__file__).resolve().parents[2];OUT=H/'generated/revO10/runs/o10_20260926_r1';OUT.mkdir(exist_ok=True)
OD=.7366;RMIN=7.366;TURNS=4

def curve(q,c,outer=18,n=2049):
 u=np.linspace(0,1,n);T=2*TURNS*np.pi-np.deg2rad(q);ri=8;dr=outer-ri;r=ri+dr*(u+c*np.sin(np.pi*u));rp=dr*(1+c*np.pi*np.cos(np.pi*u));rpp=-dr*c*np.pi**2*np.sin(np.pi*u);theta=np.deg2rad(q)+T*u
 xyz=np.c_[r*np.cos(theta),r*np.sin(theta),np.zeros(n)];speed=np.sqrt(rp*rp+(r*T)**2);curvature=np.abs(T*(2*rp*rp-r*rpp+r*r*T*T))/(rp*rp+(r*T)**2)**1.5
 length=float(np.trapezoid(speed,u));return xyz,length,float((1/curvature).min()),u,T

def solve(q,L,outer):
 lo,hi=-1/np.pi,1/np.pi
 for _ in range(42):
  c=(lo+hi)/2;length=curve(q,c,outer)[1]
  if length<L:lo=c
  else:hi=c
 p,length,r,u,T=curve(q,(lo+hi)/2,outer);return (lo+hi)/2,p,length,r,T

def turn_distance(p,T):
 # All nonadjacent point pairs, with a conservative chord endpoint cover.
 # Exclude only neighboring <4 mm of arc; these neighborhoods are separately
 # smooth with radius >7 mm and cannot fold back in the sampled geometry.
 ds=np.linalg.norm(np.diff(p,axis=0),axis=1);arc=np.r_[0,np.cumsum(ds)];best=np.inf;witness=None
 for start in range(0,len(p),128):
  ids=np.arange(start,min(start+128,len(p)));d=np.linalg.norm(p[ids,None,:]-p[None,:,:],axis=2);local=np.abs(arc[ids,None]-arc[None,:])<4;d[local]=np.inf
  idx=np.unravel_index(np.argmin(d),d.shape)
  if d[idx]<best:best=float(d[idx]);witness=[int(ids[idx[0]]),int(idx[1])]
 # Every polyline point lies within max segment/2 of a sampled endpoint;
 # this guard bounds the distance of the represented polylines, not the wire
 # solution under force or the unsampled analytic curve.
 return {'sample_min_centerline_mm':best,'polyline_endpoint_cover_lower_mm':best-float(ds.max()),'max_segment_mm':float(ds.max()),'witness_indices':witness}

def main():
 rows=[];examples={}
 for outer in (12,14,16,18,20):
  angles=np.linspace(-112.5,112.5,25);ranges=[sorted([curve(q,c,outer)[1] for c in (-1/np.pi,1/np.pi)]) for q in angles];low=max(x[0] for x in ranges);high=min(x[1] for x in ranges)
  if low>high:rows.append({'outer_radius_mm':outer,'status':'NO_COMMON_LENGTH_IN_THIS_SPIRAL_FAMILY','lower_mm':low,'upper_mm':high});continue
  L=(low+high)/2;cases=[]
  for q in angles:
   c,p,l,r,T=solve(float(q),L,outer);clear=turn_distance(p[::2],T);fine=curve(q,c,outer,4097);
   if clear['sample_min_centerline_mm']>=OD+.2 and clear['polyline_endpoint_cover_lower_mm']<OD+.2:clear=turn_distance(fine[0],T)
   case={'twist_relative_mid_deg':float(q),'coefficient':c,'length_mm':l,'length_integration_delta_mm':abs(l-fine[1]),'min_sampled_bend_radius_mm':r,'bend_radius_refinement_delta_mm':abs(r-fine[2]),**clear};cases.append(case)
   if outer==18 and q in (-112.5,0,112.5):examples[str(q)]=p[::8].round(5).tolist()
  best=min(x['polyline_endpoint_cover_lower_mm'] for x in cases);bend=min(x['min_sampled_bend_radius_mm'] for x in cases);status='KINEMATIC_PATH_FAMILY_CANDIDATE' if best>=OD+.2 and bend>=RMIN else 'FAIL_SELF_CLEARANCE_OR_BEND_SCREEN'
  rows.append({'outer_radius_mm':outer,'status':status,'constant_free_length_mm':L,'self_centerline_lower_mm':best,'surface_gap_lower_mm':best-OD,'minimum_sampled_bend_radius_mm':bend,'cases':cases});print(outer,status,L,best,bend,flush=True)
 out={'wire_od_max_mm':OD,'inherited_bend_screen_mm':RMIN,'neutral_turns':TURNS,'relative_twist_range_deg':[-112.5,112.5],'required_surface_gap_mm':.2,'lane_pitch_mm':1.6,'lane_separator_thickness_mm':.4,'candidate_case_outer_radius_mm':19.5,'candidate_case_axial_depth_mm':9,'studies':rows,'example_centerlines_mm':examples,'scope':'Separate conductor spiral, constant arc length, smooth radius and finite sampled geometry only. Not a qualified cable assembly: elastic shape, clamped-end transitions, wire-to-wire drift, insulation wear, fatigue and signal integrity require hardware. Bend-axis harness is not covered.','physical_tested':False,'manufacturing_released':False}
 (OUT/'twist_wire_study.json').write_text(json.dumps(out,indent=2)+'\n')
if __name__=='__main__':main()


