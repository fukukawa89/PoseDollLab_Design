"""Stock stack, insertion, retention, tools and inheritance of exact fork geometry."""
from build_printed_core import *
def main():
 source=OUT/'printed_core/parts.npz';raw={k:from_tri(t) for k,t in np.load(source).items()};ring=raw['C14']+raw['C15'];rows=[]
 for k,s in raw.items():
  if not k.endswith(('M3_nut','M3_reaction_washer')):continue
  axis=0 if k.startswith('C01') else 1;side=-1 if '_-1_' in k else 1
  fixed=ring+(raw[k.replace('M3_nut','M3_reaction_washer')] if k.endswith('M3_nut') else md.Manifold())
  rows.append({'part':k,'insertion_max_mm3':max((raw['C14']^s.translate([0,0,d])).volume() for d in np.linspace(0,15,31)),
  'axial_obstruction_mm3':[(fixed^s.translate(np.eye(3)[axis]*side*d)).volume() for d in (.6,1)]})
 tools=[]
 for axis in (0,1):
  for side in (-1,1):
   tool=hex_prism(2.95,HEAD0+1.55,HEAD0+31)
   tool=along(pose(tool,rot(0,180)) if side<0 else tool,axis)
   tools.append({'axis':axis,'side':side,'hits':[{'part':k,'volume_mm3':v} for k,s in raw.items() if (v:=(tool^s).volume())>1e-4]})
 cases=[]
 for length,height in itertools.product((8,8.25),(.9,1.,1.1,1.2)):
  head=HEAD0+height-.9;tip=head-length-6;neck=head-length
  bolt=cylinder(1.5,tip,neck)+cylinder(2,neck,head)+cylinder(3.5,head,head+3)
  hits=[]
  for a,b in itertools.product((-28,0,28),(-98,-75,0,75,98)):
   forks=[pose(raw['C01'],rot(0,-a)),pose(raw['C02'],rot(1,b)),ring]
   for axis,side in itertools.product((0,1),(-1,1)):
    s=along(pose(bolt,rot(0,180)) if side<0 else bolt,axis)
    for i,t in enumerate(forks):
     if (v:=(s^t).volume())>1e-4:hits.append({'a':a,'b':b,'axis':axis,'side':side,'target':i,'volume_mm3':v})
  cases.append({'shoulder_mm':length,'spring_pair_mm':height,'engagement_mm':max(0,min(neck,9.9)-max(tip,7.5)),'thread_tip_protrusion_mm':7.5-tip,'floor_margin_mm':neck-11.6,'hits':hits})
 old=H/'generated/revO11/runs/o11_20260926_r1/printed_core/parts.npz'
 orig=np.load(old);new=np.load(source)
 equal={k:bool(np.array_equal(orig[k],new[k])) for k in ('C01','C02')}
 cert=H/'generated/revO11/runs/o11_20260926_r1/printed_core/continuous_yokes.json'
 c=json.loads(cert.read_text());assert all(equal.values()) and c['status']=='CERTIFIED_NOMINAL_YOKE_PAIR_ONLY'
 assert max(r['insertion_max_mm3'] for r in rows)<1e-4
 assert min(v for r in rows for v in r['axial_obstruction_mm3'])>.01
 assert not any(r['hits'] for r in tools+cases)
 assert all(abs(r['engagement_mm']-2.4)<1e-6 for r in cases)
 save('stock_assembly.json',{'input_sha256':{p.relative_to(H).as_posix():sha(p) for p in (source,old,cert,Path(__file__))},'insertions':rows,'straight_AF3_tools':tools,'stack_sensitivity_cases':cases,'inherited_fork_certificate':{'byte_identical_triangles':equal,'source_sha256':sha(cert),'required_mm':c['required_mm'],'cells':len(c['certified_cells'])},'reaction_web_mm':2.8,'spring_force_N':None,'scope':'Sampled nominal insertion and bolt/fork/land stack checks; no handle, load, strength or creep proof.'})
 print('stock assembly checks passed',len(rows),len(tools),len(cases),'exact forks',equal,flush=True)
if __name__=='__main__':main()
