"""Finite outer twist modules with retained rotors and explicit split housings.
The shape reuse ends at each original fork's main flange. Obsolete slip-ring
stems are removed by a plane cut; journal/cup features remain as the O10 core.
Thread major/minor envelopes model assembly only, not strength or preload.
"""
from solid_ops import *
D=rot(0,180)
def housing(lo,hi):
 # Lug sweep clearance stops at actual end faces. The housing is assembled
 # radially around the rotor and axial shoulders, rather than sliding over them.
 body=cylinder(12.5,-35.5,-18.8)
 for x in (-9.5,9.5):
  for z in (-32,-21.5):body+=box([x-1.9,-10,z-2.0],[x+1.9,10,z+2.0])
 body-=cylinder(6.12,-36,-18)
 body-=cylinder(9.82,-28.1,-24.5)
 body-=sector(9.0,11.48,lo-6,hi+6,-28.1,-24.5)
 screws={};nuts={};washers={};n=0
 for x in (-9.5,9.5):
  for z in (-32,-21.5):
   n+=1
   # local Z fasteners rotated along +Y; head bears on flat Y=10 land.
   M=rot(0,-90)
   bore=pose(cylinder(1.1,-12,13),M,[x,0,z]);body-=bore
   head=pose(cylinder(1.9,10,12),M,[x,0,z]);shank=pose(cylinder(1,-12,10),M,[x,0,z]);screws[f'screw{n}']=head+shank
   a=np.linspace(0,2*np.pi,7)[:-1];r=4/np.sqrt(3);poly=np.c_[r*np.cos(a),r*np.sin(a)]
   nut=md.CrossSection([poly]).extrude(1.6).translate([0,0,-11.6])-cylinder(1.01,-12,-9)
   nuts[f'nut{n}']=pose(nut,M,[x,0,z])
 for nm,z0,z1 in [('rear',-28.05,-27.85),('front',-24.75,-24.55)]:washers[nm]=cylinder(9.65,z0,z1)-cylinder(6.2,z0-.1,z1+.1)
 halves={'case_minus':body^box([-30,-30,-40],[30,0,-10]),'case_plus':body^box([-30,0,-40],[30,30,-10])}
 return {**halves,**screws,**nuts,**{f'washer_{k}':v for k,v in washers.items()}}
def rotor_stub():
 return (cylinder(6,-33,-18.3)-cylinder(4.4,-34,-18))+(cylinder(9.6,-27.8,-24.8)-cylinder(4.4,-28,-24)) +sector(9.4,11.3,-6,6,-27.8,-24.8)
def build():
 inp=OUT/'internal_stops/parts.npz';core={k:from_tri(t) for k,t in dict(np.load(inp)).items()};stub=rotor_stub()
 core['C01']=(core['C01']^box([-30,-30,-18.6],[30,30,30]))+stub
 core['C02']=(core['C02']^box([-30,-30,-30],[30,30,18.6]))+pose(stub,D)
 # Absolute angle zero offsets are inherited for each character/side below.
 paths=json.loads((G9/'bounded_mapping.json').read_text());spec=[];mesh={k:tri(s) for k,s in core.items()}
 folder=OUT/'finite_twist';folder.mkdir(exist_ok=True)
 for c in paths['characters']:
  side=c['side'];zero=c['paths'][0]['zero_offsets_deg'];plo,phi=(-170,50) if side=='l' else (-55,170);slo,shi=-95,105
  proximal=housing(plo+zero[0],phi+zero[0]);distal=housing(slo+zero[3],shi+zero[3]);key=c['character']+'_'+side
  np.savez_compressed(folder/(key+'.npz'),**mesh,**{f'P_{k}':tri(s) for k,s in proximal.items()},**{f'D_{k}':tri(s) for k,s in distal.items()})
  spec.append({'id':key,'zero_offsets_deg':zero,'proximal_absolute_stop_deg':[plo+zero[0],phi+zero[0]],'distal_canonical_stop_deg':[slo+zero[3],shi+zero[3]],'proximal':{k:record(s) for k,s in proximal.items()},'distal':{k:record(s) for k,s in distal.items()}})
 for k,t in mesh.items():export_stl(folder/(k+'.stl'),t)
 for k,s in housing(-260,-40).items():export_stl(folder/('proximal_example_'+k+'.stl'),tri(s))
 save('finite_twist/build.json',{'source_sha256':{str(inp.relative_to(H)):sha(inp),'bounded_mapping':sha(G9/'bounded_mapping.json')},'core_parts':{k:record(s) for k,s in core.items()},'characters':spec,'rotor_bore_diameter_mm':8.8,'nominal_journal_diameter_mm':12,'housing_journal_diameter_mm':12.24,'thrust_washers_mm':.2,'total_nominal_axial_free_travel_mm':.2,'fasteners':'4 M2 x 22 per twist, 2 mm head height; thread envelopes only','physical_tested':False,'manufacturing_released':False,'scope':'Explicit finite-angle retention and motion candidate. Bearing/friction/strength/wire qualification remain required.'})
 print('built finite twist',[(r['id'],sum(x['volume_mm3'] for x in r['proximal'].values())) for r in spec],flush=True)
if __name__=='__main__':build()
