"""O10 reference threaded insertion and straight tool sweep at a service pose.
Nominal solids only; no driver handle, fingers, thread class or friction model.
"""
from solid_ops import *
from module_frames import matrices

def main():
 source=OUT/'face_brake/parts.npz';raw={k:from_tri(t) for k,t in np.load(source).items()};ring=raw['C14']+raw['C15'];rows=[]
 for name,s in raw.items():
  if not name.endswith('shoulder_axle'):continue
  axis=0 if name.startswith('C01') else 1;sign=-1 if '_-1_' in name else 1;direction=np.eye(3)[axis]*sign
  axial=[{'shift_mm':d,'ring_intersection_mm3':(ring^s.translate(direction*d)).volume()} for d in (-.15,.15)]
  assert all(r['ring_intersection_mm3']>.01 for r in axial)
  path=[]
  for d in np.linspace(0,5,21):
   moved=pose(s,rot(direction,d*720),direction*d);v=(ring^moved).volume();path.append({'outward_mm':float(d),'rotation_deg':float(d*720),'ring_intersection_mm3':v})
  rows.append({'axle':name,'axial_pull_without_rotation':axial,'helical_withdrawal':path})
 c=json.loads((G9/'bounded_mapping.json').read_text())['characters'][0];q=[0,0,0,0];M=matrices(q,c['paths'][0]['zero_offsets_deg']);full={}
 for name,t in np.load(OUT/'braked_module/manny_l.npz').items():
  role='P' if name.startswith('P_') else 'D' if name.startswith('D_') else name if name in ('C01','C02') else 'ring';full[name]=pose(from_tri(t),M[role])
 tools=[];angles=np.arange(6)*np.pi/3;hexagon=md.CrossSection([np.c_[np.cos(angles),np.sin(angles)]*(2.5/np.sqrt(3))]);rod=hexagon.extrude(24.2).translate([0,0,17.8])
 for axis in (0,1):
  for sign in (-1,1):
   local=along(rod if sign==1 else pose(rod,rot(0,180)),axis);world=pose(local,M['ring']);hits=[]
   for name,s in full.items():
    v=(world^s).volume()
    if v>1e-4:hits.append({'part':name,'volume_mm3':v})
   tools.append({'axis':axis,'side':sign,'findings':hits})
 out={'input_sha256':{str(p.relative_to(H)):sha(p) for p in [source,OUT/'braked_module/manny_l.npz',Path(__file__)]},'service_q_relative_deg':q,'service_description':'Straight universal joint alpha=beta=0, not the anatomical neutral beta around 76.7 degrees. Both outer twists stay at their common zero offsets.','threaded_axles':rows,'straight_2p5mm_AF_tool_sweeps':tools,'scope':'21 reference helical positions per axle against the ring; four complete straight tool-shaft sweeps against the modeled full module. No printed tolerance, driver handle, fingers, loaded insertion or anti-loosening qualification.','manufacturing_released':False}
 save('face_brake/assembly_tools.json',out);print('thread max',max(r['ring_intersection_mm3'] for a in rows for r in a['helical_withdrawal']),'tool findings',tools)
if __name__=='__main__':main()
