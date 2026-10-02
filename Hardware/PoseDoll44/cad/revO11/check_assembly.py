"""Nominal insert/retention/tool checks and explicit catalogue-tolerance screen."""
from build_printed_core import *

def main():
 sources=[OUT/'printed_core/parts.npz',H/'bench/revO11/parts.npz',Path(__file__),Path(__file__).with_name('build_printed_core.py')]
 hashes={str(p.relative_to(H)):sha(p) for p in sources};raw={k:from_tri(t) for k,t in np.load(sources[0]).items()};ring=raw['C14']+raw['C15'];rows=[]
 for k,s in raw.items():
  if not (k.endswith('M3_nut') or k.endswith('M3_reaction_washer')):continue
  insertion=[{'offset_mm':float(d),'volume_mm3':(raw['C14']^s.translate([0,0,d])).volume()} for d in np.linspace(0,15,31)]
  axis=0 if k.startswith('C01') else 1;side=-1 if '_-1_' in k else 1;v=np.eye(3)[axis]*side
  fixed=ring+(raw[k.replace('M3_nut','M3_reaction_washer')] if k.endswith('M3_nut') else md.Manifold())
  retention=[{'outward_mm':d,'volume_mm3':(fixed^s.translate(v*d)).volume()} for d in (.6,1)]
  rows.append({'part':k,'insertion_from_open_split_plane':insertion,'outward_pull':retention})
 tools=[]
 # Full tool shank in its service position, which is alpha=beta=0.
 for axis in (0,1):
  for side in (-1,1):
   tool=hex_prism(1.95,HEAD0+1.55,HEAD0+31)
   if side<0:tool=pose(tool,rot(0,180))
   tool=along(tool,axis);hits=[]
   for k,s in raw.items():
    v=(tool^s).volume()
    if v>1e-4:hits.append({'part':k,'volume_mm3':v})
   tools.append({'axis':axis,'side':side,'hits':hits})
 # Compare shoulder length extremes and compressed spring heights; printed
 # dimensional scatter is not known, and is explicitly excluded here.
 variations=[]
 for length,height in itertools.product((8,8.25),(.8,.9,1.1)):
  head=HEAD0+height-.9;tip=head-length-7;neck=head-length
  bolt=cylinder(1.5,tip,neck)+cylinder(2,neck,head)+cylinder(3.5,head,head+3)
  parts={}
  for name,axis in [('C01',0),('C02',1)]:
   for side in (-1,1):parts[f'{name}_{side}']=along(bolt if side>0 else pose(bolt,rot(0,180)),axis)
  clashes=[]
  for a,b in itertools.product((-28,0,28),(-98,-75,0,75,98)):
   # Use the ring frame to keep all hardware fixed; forks rotate relative to it.
   forks={'C01':pose(raw['C01'],rot(0,-a)),'C02':pose(raw['C02'],rot(1,b))}
   for n,s in parts.items():
    for f,ss in forks.items():
     v=(s^ss).volume()
     if v>1e-4:clashes.append({'alpha':a,'beta':b,'bolt':n,'fork':f,'volume_mm3':v})
    v=(s^ring).volume()
    if v>1e-4:clashes.append({'bolt':n,'ring_volume_mm3':v})
  variations.append({'length_mm':length,'spring_stack_mm':height,'thread_tip_mm':tip,'neck_mm':neck,'shoulder_floor_margin_mm':neck-11.6,'nut_engagement_envelope_mm':max(0,min(neck,8.9)-max(tip,6.5)),'findings':clashes})
 bench={k:from_tri(t) for k,t in np.load(sources[1]).items()};base=bench['printed_base_minus'];br=[]
 for k in ('M3_nut','M3_reaction_washer'):
  br.append({'part':k,'insertion_positive_Y_max_volume_mm3':max((base^bench[k].translate([0,d,0])).volume() for d in np.linspace(0,15,31))})
 pressure={'reference_force_N':210,'fork_average_MPa':210/(np.pi*(6**2-2.15**2)),'reaction_land_average_MPa':210/(np.pi*(4.5**2-1.7**2)),'note':'Average nominal contact pressure only; no peak stress, layer strength or creep qualification.'}
 report={'inputs_sha256':hashes,'ring_inserts':rows,'straight_AF2_tool_shank':tools,'bench_insert_paths':br,'catalogue_tolerance_cases':variations,'pressure':pressure,'scope':'Sampled insertion paths (0.5 mm steps), solid axial obstruction, straight shaft envelope and six fastener-stack variants at 15 angle combinations each. No driver handle/finger model; no printed tolerance or screw loosening qualification.','physical_tested':False,'manufacturing_released':False}
 assert hashes=={str(p.relative_to(H)):sha(p) for p in sources}
 save('assembly_and_stack.json',report)
 print('insert_max',max(r['volume_mm3'] for row in rows for r in row['insertion_from_open_split_plane']),'tool_hits',sum(len(r['hits']) for r in tools),'variant_hits',sum(len(r['findings']) for r in variations),'bench',br)
 print('retention_min',min(r['volume_mm3'] for row in rows for r in row['outward_pull']),'pressure',pressure)
if __name__=='__main__':main()

