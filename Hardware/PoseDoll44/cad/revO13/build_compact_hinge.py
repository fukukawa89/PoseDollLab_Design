"""Compact single-axis friction candidate reuses the physically assembled O12 stack.
Only the three printed mechanical bodies are exportable prototype parts.
Sensor/cap/connector solids are explicit reservations, not fixed PCBA designs.
"""
from solid_ops import *
from parts_library import Parts,library
from clavicle_trial import frames,bounds
from check_full_motion import check
import itertools
def make():
 src=H/'bench/revO12/parts.npz';raw={k:from_tri(t) for k,t in np.load(src).items()}
 for k in ('printed_base_minus','printed_base_plus'):raw[k]=raw[k]^box([-14,-30,-1],[14,30,30])
 raw['printed_lever']=raw['printed_lever']^box([-20,-20,0],[22,20,25])
 raw['printed_lever']-=cylinder(1.7,8,16).translate([17,0,0])
 raw={k:s.translate([0,0,-10.5]) for k,s in raw.items()}
 # Provisional sensor-side reserved geometry around, rather than through,
 # the current stock bolt/spring stack. No attachment acceptance is inferred.
 annulus=(cylinder(11.5,1.5,10)-cylinder(6.3,1.4,10.1))
 cap=cylinder(11.5,10,13)-cylinder(3.1,10.5,13.1)
 magnet=cylinder(3,10.5,13)
 board=box([-6,-5,16.495],[6,5,17.495])
 package=box([-3.25,-3.25,14.5],[3.25,3.25,16.495])
 connector=box([-3,2,17.495],[3,5,22.5])
 # Holder routing volume accounts for a support post and bridge above the cap.
 post=cylinder(2.5,-2.5,16.495).translate([-11.5,-12,0])
 bridge=box([-14,-14,15],[-5,-5,16.495])
 plate=box([-7,-6,15],[7,6,16.495])-box([-4,-4,14.9],[4,4,16.6])
 reservations={'rotor_cup':annulus,'rotor_cap':cap,'magnet':magnet,'sensor_PCB':board,'sensor_package':package,'connector':connector,'holder_route':post+bridge+plate}
 groups={'parent':Parts([s for k,s in raw.items() if k!='printed_lever']),
         'child':Parts([raw['printed_lever']])}
 packed={'parent':Parts(groups['parent'].parts+[board,package,connector,post+bridge+plate]),
         'child':Parts(groups['child'].parts+[annulus,cap,magnet])}
 return raw,reservations,groups,packed
def main():
 raw,reserved,bare,packed=make();dest=OUT/'compact_hinge';dest.mkdir(exist_ok=True)
 np.savez_compressed(dest/'parts.npz',**{k:tri(s) for k,s in raw.items()})
 np.savez_compressed(dest/'reservations.npz',**{k:tri(s) for k,s in reserved.items()})
 pairs=[]
 for a,b in itertools.combinations(raw,2):
  if (v:=(raw[a]^raw[b]).volume())>1e-4:pairs.append({'pair':[a,b],'volume_mm3':v})
 motion=[]
 for d in range(-90,141,5):
  v=(bare['parent']^pose(bare['child'],rot(2,d))).volume()
  w=(packed['parent']^pose(packed['child'],rot(2,d))).volume()
  motion.append({'angle_deg':d,'bare_overlap_mm3':v,'including_reserved_overlap_mm3':w})
 save('compact_hinge/build.json',{'source_sha256':sha(H/'bench/revO12/parts.npz'),'generator_sha256':sha(__file__),'parts':{k:record(s) for k,s in raw.items()},'nominal_findings':pairs,'sampled_motion':motion,
 'friction_interface_same_as_O12':True,'reaction_web_mm':2.8,'smaller_base_xy_mm':[28,30],
 'sensor_reservations':{'diametric_magnet_mm':[6,2.5],'PCB_mm':[12,10,1],'airgap_mm':1.5,'mounting_and_wiring_not_detail_designed':True},
 'manufacturing_released':False,'status':'GEOMETRY_CANDIDATE_REQUIRES_MOUNTING_AND_PHYSICAL_TESTS'})
 lib=library()
 # Replace the same four retained single-axis modules per arm, without
 # altering joint origins or target angles. This is a packaging experiment.
 c=json.loads((OUT/'clavicle_trial/motion.json').read_text())['candidate'];rows=[]
 for mode,groups in [('bare_mechanics',bare),('including_sensor_reservations',packed)]:
  trial={**lib,**{'M4_'+k:v for k,v in groups.items()}};bb={k:bounds(v) for k,v in trial.items()}
  # Pair cache is shared by imported checker; geometry identity must be part
  # of key, so reset it whenever the geometry library is substituted.
  import check_full_motion
  check_full_motion.PAIR_CACHE.clear()
  for char in ('manny','quinn'):
   states,_=frames(char,c['x_mm'],c['lateral_mm'],c['z_shift_mm'])
   for state in states:
    hits=check(state,trial,bb,True)
    rows.append({'mode':mode,'character':char,'pose':state['pose'],'findings':hits})
  save('compact_hinge/packing_comparison.json',{'complete':False,'cases':rows})
 save('compact_hinge/packing_comparison.json',{'complete':True,'cases':rows,'scope':'Endpoint packaging comparison using same origins/angles. Bare result alone is not full-joint acceptance. Reserved PCBA/cap has no qualified attachment, cable or magnetic test. No material/force transfer from qualitative coupon feedback.'})
 print('compact hinge',len(raw),'nominal hits',len(pairs),'motion max',max(r['including_reserved_overlap_mm3'] for r in motion),flush=True)
 print('endpoint failures', {m:sum(bool(r['findings']) for r in rows if r['mode']==m) for m in ('bare_mechanics','including_sensor_reservations')},flush=True)
if __name__=='__main__':main()
