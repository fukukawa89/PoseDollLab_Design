"""O11: printed split ring, retained catalogue nuts and stock washers/shoulder bolts.
Thread envelopes provide clearance/engagement geometry, not a strength proof.
All coordinates in mm. Source core is immutable O9 mesh, welded at 1e-5 mm.
"""
from solid_ops import *
import itertools
EXTRA=7.0
EXTENSIONS={'C01':1.5,'C02':7.0}
FACE=13.5
FORK0=FACE+1
FORK1=FORK0+3
SPRING0=FORK1+1
HEAD0=SPRING0+.9+.8

def hex_prism(af,z0,z1):
 a=np.arange(6)*np.pi/3
 return md.CrossSection([np.c_[np.cos(a),np.sin(a)]*af/np.sqrt(3)]).extrude(z1-z0).translate([0,0,z0])
def washer(ro,ri,z0,t):return cylinder(ro,z0,z0+t)-cylinder(ri,z0-.1,z0+t+.1)
def disc(z0,flip=False):
 p=np.array([[2.1,z0+.05],[4,z0],[4,z0+.4],[2.1,z0+.45]])
 if flip:p[:,1]=2*z0+.45-p[:,1];p=p[::-1].copy()
 return md.CrossSection([p]).revolve(circular_segments=144)
def stock_stack(face=FACE):
 d=face-FACE
 bolt=cylinder(1.5,HEAD0-15,HEAD0-8)+cylinder(2,HEAD0-8,HEAD0)+cylinder(3.5,HEAD0,HEAD0+3)
 bolt-=hex_prism(2,HEAD0+1.5,HEAD0+3.1)
 parts={'inner_M4_wide':washer(6,2.15,FACE,1),'outer_M4_wide':washer(6,2.15,FORK1,1),
 'spring_1':disc(SPRING0),'spring_2':disc(SPRING0+.45,True),'front_M4_washer':washer(4.5,2.15,SPRING0+.9,.8),
 'shoulder_SBSM_M3_4_8':bolt,'M3_nut':hex_prism(5.5,6.5,8.9)-cylinder(1.55,6.4,9),
 'M3_reaction_washer':washer(4.5,1.6,8.9,.8)}
 return {k:s.translate([0,0,d]) for k,s in parts.items()}
def pocket(face=FACE):
 d=face-FACE
 # Captured through-nut and washer are inserted normal to the ring split plane.
 return (hex_prism(5.8,6.35,8.95)+cylinder(4.65,8.85,9.7)+cylinder(1.7,3.5,12.5)+cylinder(2.125,11.6,14)).translate([0,0,d])
def move_legs(t,axis):
 t=t.copy();x=t[:,:,axis];t[:,:,axis]+=np.sign(x)*5.3*np.clip((np.abs(x)-4)/4,0,1);return t

def main():
 raw=dict(np.load(CORE));ring=from_tri(raw['C14'])+from_tri(raw['C15']);parts={}
 for name,ax,limit in [('C01',0,28),('C02',1,98)]:
  extra=EXTENSIONS[name];t=tri(from_tri(raw[name]));sign=-1 if name=='C01' else 1;t[:,:,2]+=sign*extra*np.clip((sign*t[:,:,2]-6)/3,0,1);s=from_tri(t)
  for side in (-1,1):
   lo,hi=sorted((side*4.99,side*9.27));s-=along(cylinder(2.6,lo,hi),ax)
  s=from_tri(move_legs(tri(s),ax))
  for side in (-1,1):
   def orient(x):return along(pose(x,rot(0,180)) if side<0 else x,ax)
   s-=orient(cylinder(4.25,4.7,FORK0-.01))
   ring+=orient(cylinder(4.5,5,9)+cylinder(8,8.8,FACE))
   ring-=orient(pocket())
   ring-=orient(sector(6.4,7.8,-limit-6,limit+6,FACE-2.1,FACE+.1))
   boss=(cylinder(8,FORK0,FORK0+1)+cylinder(6,FORK0+1,FORK1))-cylinder(2.125,FORK0-.1,FORK1+.1)
   ear=sector(6.6,7.6,-6,6,FACE-2, FORK0+.1)
   s+=orient(boss+ear);s-=orient(cylinder(2.125,3.6,FORK1+.1))
   for lab,ss in stock_stack().items():parts[f'{name}_{side:+d}_{lab}']=orient(ss)
  if name=='C01':s+=cylinder(1.2,-17.2-extra,-2.4)+box([-6,-1,-18.3-extra],[6,1,-16.8-extra])
  parts[name]=s
 # Keep original four ring bolts and nut seats; new nuts lie inside their pattern.
 fast={k:from_tri(t) for k,t in np.load(G8/'fastened_core/fasteners.npz').items()}
 for k,s in fast.items():
  if 'nut' in k:
   b=np.array(s.bounding_box());c=(b[:3]+b[3:])/2;ring-=s.translate(-c).scale([1.07,1.07,1]).translate(c)
 parts.update(C14=ring^box([-50,-50,-40],[50,50,0]),C15=ring^box([-50,-50,0],[50,50,40]))
 dest=OUT/'printed_core';dest.mkdir(parents=True,exist_ok=True)
 np.savez_compressed(dest/'parts.npz',**{k:tri(s) for k,s in parts.items()})
 for k in ('C01','C02','C14','C15'):export_stl(dest/(k+'.stl'),tri(parts[k]))
 hits=[];allparts={**parts,**{'ring_fastener_'+k:s for k,s in fast.items()}}
 for a,b in itertools.combinations(allparts,2):
  v=(allparts[a]^allparts[b]).volume()
  if v>1e-4:hits.append({'pair':[a,b],'volume_mm3':v})
 report={'source_sha256':sha(CORE),'generator_sha256':sha(__file__),'parts':{k:record(s) for k,s in parts.items()},'extra_fork_extension_each_mm':EXTRA,'extensions_mm':EXTENSIONS,'assembled_findings':hits,
 'materials':{'printed_bodies':'FDM PLA-CF candidate; process and creep validation pending','stock_washers':'SUS304 catalogue standard dimensions; finish must be recorded','axle':'NBK SBSM-M3-4-8, catalogue steel'},
 'axial_stack_mm':{'ring_face':FACE,'fork_start':FORK0,'fork_end':FORK1,'spring_start':SPRING0,'head_start':HEAD0,'head_end':HEAD0+3,'shoulder_start':HEAD0-8,'thread_tip':HEAD0-15,'nut':[6.5,8.9],'reaction_washer':[8.9,9.7]},
 'custom_metal_in_new_core':0,'scope':'Two-axis core only. External twist housings retained solely for envelope checks; their bearing/wire/holding design is not released.',
 'thread_model':'Nominal major-diameter bolt and relieved nut bore. Catalogue nut provides real thread; envelope check does not prove thread strength.',
 'physical_tested':False,'manufacturing_released':False}
 save('printed_core/build.json',report);print('parts',len(parts),'printed',[(k,record(parts[k])) for k in ('C01','C02','C14','C15')]);print('hits',hits,flush=True)
if __name__=='__main__':main()




