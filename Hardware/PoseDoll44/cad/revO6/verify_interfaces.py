"""Sampled assembly, life states, guide retention and reverse clearance for O6."""
from pathlib import Path
import argparse,hashlib,itertools,json,math,sys
import cadquery as cq
import numpy as np
R=Path(__file__).resolve().parents[4];H=R/'Hardware/PoseDoll44'
sys.path.insert(0,str(H/'cad/revO3'))
from compact_joint import bounds,ring,disc_spring,THREAD_PITCH,STACK_SHIFT
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def overlap(a,b):
 x,y=bounds(a),bounds(b)
 if not all(min(x[k+3],y[k+3])-max(x[k],y[k])>1e-6 for k in range(3)):return 0.
 return a.intersect(b).Volume()
def save(p,d):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--joint',type=Path,required=True);ap.add_argument('--out',type=Path,required=True);a=ap.parse_args();a.joint=a.joint.resolve();a.out=a.out.resolve()
 m=json.loads((a.joint/'manifest.json').read_text());inputs={(a.joint/'manifest.json').relative_to(R).as_posix():sha(a.joint/'manifest.json'),Path(__file__).relative_to(R).as_posix():sha(Path(__file__))}
 s={}
 for row in m['parts']:
  p=a.joint/row['step_file'];assert sha(p)==row['step_sha256'];inputs[p.relative_to(R).as_posix()]=sha(p);s[row['part_id']]=cq.importers.importStep(str(p)).val()
 assert not m['nominal_intersections']
 installed={};steps=[];covered=set()
 def step(label,names,samples,method):
  found=[];pairs=0
  for position,group in samples:
   for n,shape in group.items():
    for j,other in installed.items():
     if j in names:continue
     v=overlap(shape,other);pairs+=1
     if v>1e-4:found.append(dict(position=position,moving=n,fixed=j,volume_mm3=v))
   for n,j in itertools.combinations(group,2):
    v=overlap(group[n],group[j]);pairs+=1
    if v>1e-4:found.append(dict(position=position,moving=n,within_group=j,volume_mm3=v))
  steps.append(dict(step=label,parts=names,samples=len(samples),pairs_screened=pairs,method=method,intersections=found,status='FAIL' if found else 'PASS_SAMPLED_NOMINAL'))
  installed.update({n:s[n] for n in names});covered.update(names)
  print(label,steps[-1]['status'],len(found),flush=True)
 def linear(label,names,vec,dist=25):
  ds=sorted(set([0,.05,.1,.25,.5,1,2,4,8,12,20,dist]),reverse=True) if dist else [0]
  step(label,names,[(d,{n:s[n].translate(tuple(d*v for v in vec)) for n in names}) for d in ds],{'linear_direction':vec,'continuous_proof':False})
 linear('01 shaft',['short_taper_measurement_shaft'],(0,0,-1),0)
 for n in ('diametric_magnet','magnet_keeper','keeper_screw_-4.25','keeper_screw_4.25'):linear('03 magnet '+n,[n],(0,0,1))
 for base in ('rear_bush','front_bush','thrust_rear','thrust_front'):
  for side,sign in (('L',-1),('R',1)):linear('04 split '+base+side,[base+'_'+side],(sign,0,0),12)
 for side,sign in (('L',-1),('R',1)):linear('05 housing '+side,['housing_'+side],(sign,0,0),32)
 for n in ('bearing_clamp_-6','bearing_clamp_6'):linear('06 clamp '+n,[n],(-1,0,0))
 linear('06b front plate from bare tail after radial bearing closure',['integral_steel_front_backing'],(0,0,-1),35)
 for n in ('front_friction_lining','floating_brake_disc'):linear('07 brake '+n,[n],(0,0,-1),35)
 cup_names=['brake_cup_front_loading','integral_rear_sliding_carrier','rear_friction_lining',*[n for n in s if n.startswith('guide_shim_')]]
 # Separate bench insertion checked before moving the completed subassembly.
 bench=[]
 for n in cup_names[1:]:
  for dz in (15,8,4,2,1,.5,.1,0):
   v=overlap(s[n].translate((0,0,dz)),s['brake_cup_front_loading'])
   bench.append({'part':n,'approach_mm':dz,'cup_intersection_mm3':v})
 linear('08 front-loaded cup subassembly from rear',cup_names,(0,0,-1),35)
 for i in range(4):linear('09 cup bolt '+str(i),['cup_mount_'+str(i)],(0,0,1))
 linear('10 spring seat',['spring_front_washer'],(0,0,-1),35)
 springs=['disc_spring_'+str(i+1) for i in range(4)]
 for i in range(3,-1,-1):
  n=springs[i];free=disc_spring(-10+i*.85,.85,i%2==1)
  step('11 free spring '+str(i+1),[n],[(d,{n:free.translate((0,0,-d))}) for d in (25,15,8,4,1,.1,0)],{'free_height_mm':.85})
  installed[n]=free
 rear=s['spring_rear_washer'].translate((0,0,-1.05))
 step('12 free rear seat',['spring_rear_washer'],[(d,{'spring_rear_washer':rear.translate((0,0,-d))}) for d in (25,15,8,4,1,.1,0)],{'free_stack_mm':3.4})
 installed['spring_rear_washer']=rear
 samples=[(float(d),{'threaded_adjuster_cap':s['threaded_adjuster_cap'].rotate((0,0,0),(0,0,1),float(d/THREAD_PITCH*360)).translate((0,0,float(d)))}) for d in np.linspace(-10.05,-1.05,37)]
 step('13 helical cap',['threaded_adjuster_cap'],samples,{'pitch_mm':.75,'increment_mm':.25})
 samples=[]
 for dz in np.linspace(-1.05,0,22):
  h=(2.35-dz)/4
  group={'threaded_adjuster_cap':s['threaded_adjuster_cap'].rotate((0,0,0),(0,0,1),float(dz/.75*360)).translate((0,0,float(dz))),'spring_rear_washer':s['spring_rear_washer'].translate((0,0,float(dz)))}
  group.update({n:disc_spring(-6.6-4*h+i*h,h,i%2==1) for i,n in enumerate(springs)});samples.append((float(dz),group))
 step('14 compression',['threaded_adjuster_cap','spring_rear_washer',*springs],samples,{'free_to_working_height_mm':[.85,.5875]})
 linear('15 cap dog',['cap_lock_dog_screw'],(1,0,0),15)
 linear('16 sensor board',[n for n in s if n.startswith('sensor_pcba_')],(0,0,1))
 for n in ('pcb_edge_clamp_-7.7','pcb_edge_clamp_7.7','pcb_clamp_screw_-7.7','pcb_clamp_screw_7.7'):linear('17 sensor fastener '+n,[n],(0,0,1))
 for n in ('taper_output_hub','output_retention_washer','output_retention_screw','output_yoke_interface'):
  linear('18 output '+n,[n],(0,0,-1))
 for i in range(4):linear('19 output bolt '+str(i),['output_yoke_screw_'+str(i)],(0,0,-1))
 rotating=[p['part_id'] for p in m['parts'] if p['owner']=='child']
 step('20 single-axis rotation',rotating,[(d,{n:s[n].rotate((0,0,0),(0,0,1),d) for n in rotating}) for d in range(0,361,5)],{'step_deg':5,'continuous_proof':False})
 save(a.out/'assembly.json',{'steps':steps,'bench_front_insertion':bench,'part_coverage_complete':covered==set(s),'physical_tested':False,'manufacturing_released':False,'status':'FAIL' if any(t['intersections'] for t in steps) or any(r['cup_intersection_mm3']>1e-4 for r in bench) else 'PASS_SAMPLED_NOMINAL','input_sha256':inputs})
 # Six attempted translations of each shim after front closure. This establishes
 # gross translation stops only; it does not prove no arbitrary escape path.
 retention=[]
 for n in s:
  if not n.startswith('guide_shim_'):continue
  for axis in range(3):
   for sign in (-1,1):
    d=[0.,0.,0.];d[axis]=sign*.2
    v=sum(overlap(s[n].translate(tuple(d)),s[j]) for j in ('brake_cup_front_loading','integral_steel_front_backing'))
    full=[]
    for dz in (0,.64,.9):
     full.append(v+overlap(s[n].translate(tuple(d)),s['integral_rear_sliding_carrier'].translate((0,0,dz))))
    retention.append({'shim':n,'attempt_mm':d,'fixed_parts_only_blocking_volume_mm3':v,'assembled_blocking_volume_mm3_at_carrier_shifts_0_064_09':full,'blocking_volume_mm3':min(full)})
 guide=[s['brake_cup_front_loading'],*[v for n,v in s.items() if n.startswith('guide_shim_')]]
 carrier=s['integral_rear_sliding_carrier'];threshold=[]
 for sign in (-1,1):
  lo,hi=0.,.5
  for _ in range(12):
   mid=(lo+hi)/2;shape=carrier.rotate((0,0,0),(0,0,1),sign*mid)
   v=sum(overlap(shape,x) for x in guide)
   if v>1e-6:hi=mid
   else:lo=mid
  threshold.append({'sign':sign,'last_clear_deg':lo,'first_collision_deg':hi})
 save(a.out/'retention_reverse.json',{'shim_translation_stops':retention,'retention_basis':'Cup/endplate constrain axial/radial/outward motion; installed sliding carrier constrains inward tangential motion. Tested at three wear positions; arbitrary escape path and flex are not proven.','all_24_attempts_blocked':all(r['blocking_volume_mm3']>1e-5 for r in retention),'rear_guide_reverse_thresholds':threshold,'total_reverse_free_angle_interval_deg':[sum(x['last_clear_deg'] for x in threshold),sum(x['first_collision_deg'] for x in threshold)],'not_equivalent_to':'Measured joint backlash or encoder error','physical_tested':False,'input_sha256':inputs})
 configpath=H/'mechanical_manifest/lifecycle_states_revO3.json';inputs[configpath.relative_to(R).as_posix()]=sha(configpath);config=json.loads(configpath.read_text())
 states=[];cache={}
 for wf,wr in config['wear_pairs_mm']:
  for cf,cr in config['compression_pairs_mm']:
   df=wf+cf;dr=wf+wr+cf+cr;capdz=math.ceil((dr-1e-9)/(.75/12))*(.75/12) if dr else 0;h=(2.35+dr-capdz)/4
   current=dict(s)
   current['front_friction_lining']=ring(12,4.2,-1.4+df,-.8)
   current['rear_friction_lining']=ring(12,4.2,-3.5+dr,-2.9+df)
   current['floating_brake_disc']=s['floating_brake_disc'].translate((0,0,df))
   for n in ('integral_rear_sliding_carrier','spring_front_washer'):current[n]=s[n].translate((0,0,dr))
   for n in ('threaded_adjuster_cap','spring_rear_washer'):current[n]=s[n].translate((0,0,capdz))
   current['threaded_adjuster_cap']=current['threaded_adjuster_cap'].rotate((0,0,0),(0,0,1),capdz/.75*360)
   for i in range(4):current[springs[i]]=disc_spring(-8.95+capdz+i*h,h,i%2==1)
   changed={n for n in current if current[n] is not s[n]};sig={n:() for n in current}
   for n in ('front_friction_lining','floating_brake_disc'):sig[n]=(round(df,6),)
   sig['rear_friction_lining']=(round(df,6),round(dr,6))
   for n in ('integral_rear_sliding_carrier','spring_front_washer'):sig[n]=(round(dr,6),)
   for n in ('threaded_adjuster_cap','spring_rear_washer'):sig[n]=(round(capdz,6),)
   for n in springs:sig[n]=(round(capdz,6),round(h,6))
   hits=[]
   for n,j in itertools.combinations(current,2):
    if n not in changed and j not in changed:continue
    key=(n,sig[n],j,sig[j])
    if key not in cache:cache[key]=overlap(current[n],current[j])
    if cache[key]>1e-4:hits.append({'a':n,'b':j,'volume_mm3':cache[key]})
   states.append({'wear_mm':[wf,wr],'compression_mm':[cf,cr],'cap_advance_mm':capdz,'spring_height_mm':h,'intersections':hits})
   print('life',wf,wr,cf,cr,len(hits),flush=True)
 save(a.out/'lifecycle.json',{'states':states,'status':'FAIL' if any(t['intersections'] for t in states) else 'PASS_SCOPED_LIFE_GEOMETRY','unique_pair_evaluations':len(cache),'input_sha256':inputs,'physical_tested':False,'manufacturing_released':False})
 assert all(sha(R/k)==v for k,v in inputs.items()),'Input changed during verification'
if __name__=='__main__':main()

