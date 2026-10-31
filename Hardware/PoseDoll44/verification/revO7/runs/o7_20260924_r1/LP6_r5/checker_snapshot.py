"""LP6 sampled assembly, single-axis motion, nominal wear and retention checks.
Every installed part is covered. No stiffness, force balance or manufacturing rating.
"""
from pathlib import Path
import argparse,hashlib,itertools,json,math,sys
import cadquery as cq
import numpy as np
R=Path(__file__).resolve().parents[4];H=R/'Hardware/PoseDoll44'
sys.path.insert(0,str(H/'cad/revO3'));from compact_joint import ring,box,cyl,bounds
sys.path.insert(0,str(H/'cad/revO6'));from thread_geometry import overlap_volume
from small_joint import spring
from pancake_joint import at,lining
from preload_schedule import advance

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,d):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(d,indent=2)+'\n',encoding='utf-8')
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--joint',type=Path,required=True);ap.add_argument('--out',type=Path,required=True);ap.add_argument('--phase',choices=['assembly','life','retention'],required=True);a=ap.parse_args();a.joint=a.joint.resolve()
 m=json.loads((a.joint/'manifest.json').read_text());assert not m['nominal_intersections'];s={};paths=[Path(__file__),a.joint/'manifest.json',Path(__file__).with_name('pancake_joint.py'),Path(__file__).with_name('preload_schedule.py'),H/'cad/revO6/thread_geometry.py',H/'cad/revO6/small_joint.py',H/'cad/revO3/compact_joint.py']
 for row in m['parts']:
  p=a.joint/row['step_file'];assert sha(p)==row['step_sha256'];paths.append(p);s[row['part_id']]=cq.importers.importStep(str(p)).val()
 inputs={p.relative_to(R).as_posix():sha(p) for p in paths};g=m['geometry'];r=g['spring_radius_mm'];angles=g['spring_angles_deg'];hw=g['spring_work_height_mm'];hf=g['spring_free_height_mm'];pitch=g['preload_thread_pitch_mm'];relax=2*(hf-hw)
 def helical(i,dz):
  theta=math.radians(angles[i]);c=(r*math.cos(theta),r*math.sin(theta),0)
  return s['M6p5_preload_plug_'+str(i)].rotate(c,(c[0],c[1],1),dz/pitch*360).translate((0,0,dz))
 def checkpairs(group,other):
  hits=[];seen=set()
  for n,v in group.items():
   for j,w in other.items():
    if n==j:continue
    key=tuple(sorted([n,j]))
    if key in seen:continue
    seen.add(key);q=overlap_volume(v,w)
    if q>1e-4:hits.append({'a':n,'b':j,'volume_mm3':q})
  return hits
 if a.phase=='assembly':
  installed={};covered=set();steps=[]
  def step(label,samples,method):
   names=set(samples[-1][1]);fixed={n:v for n,v in installed.items() if n not in names};hits=[]
   for pos,group in samples:
    hits.extend({'position':pos,**x} for x in checkpairs(group,{**fixed,**group}))
   installed.update(samples[-1][1]);covered.update(names)
   steps.append({'step':label,'parts':sorted(names),'samples':len(samples),'method':method,'hits':hits,'status':'FAIL' if hits else 'PASS_SAMPLED_NOMINAL'})
   print(label,steps[-1]['status'],len(hits),flush=True);save(a.out/'assembly_progress.json',{'status':'RUNNING_INCOMPLETE','steps':steps})
  def linear(label,names,vec,dist=25,shapes=None):
   q=shapes or {n:s[n] for n in names};ds=sorted(set([0,.05,.1,.25,.5,1,2,4,8,12,20,dist]),reverse=True) if dist else [0]
   step(label,[(d,{n:v.translate(tuple(d*x for x in vec)) for n,v in q.items()}) for d in ds],{'direction':vec,'continuous_proof':False})
  linear('01 shaft',['integral_output_measurement_shaft'],(0,0,1),0)
  for base in ['front_thrust','front_bush']:
   for side,sgn in [('L',-1),('R',1)]:linear('02 '+base+side,[base+'_'+side],(sgn,0,0),12)
  for side,sgn in [('L',-1),('R',1)]:linear('03 front plate '+side,['front_reaction_and_bearing_'+side],(sgn,0,0),30)
  for n in s:
   if n.startswith('front_split_bolt_'):linear('04 '+n,[n],(-1,0,0))
  for n in ['front_lining','floating_rotor','rear_lining','floating_pressure_carrier']:linear('05 '+n,[n],(0,0,1),30)
  for i in range(3):linear('06 guide '+str(i),['guide_sleeve_'+str(i)],(0,0,1))
  for side,sgn in [('L',-1),('R',1)]:linear('07 rear shaft collar '+side,['rear_shaft_collar_'+side],(sgn,0,0),12)
  for i,theta in enumerate(angles):
   n='spring_lower_seat_'+str(i);linear('08 '+n,[n],(0,0,1))
   for j in range(2):
    n=f'B8_spring_{i}_{j}';free=at(spring(4,2.1,.3,4.45+j*hf,hf,j%2==1),r,theta);linear('09 '+n,[n],(0,0,1),25,{n:free})
   n='spring_upper_seat_'+str(i);linear('10 '+n,[n],(0,0,1),25,{n:s[n].translate((0,0,relax))})
  linear('11 monolithic rear plate over bare shaft/collar',['rear_reaction_and_bearing'],(0,0,1),30)
  for i in range(3):
   linear('12 cage bolt '+str(i),['cage_M2x15_'+str(i)],(0,0,1));linear('13 cage nut '+str(i),['cage_nut_M2_'+str(i)],(0,0,-1))
  # A direct axial approach is obstructed by the integrated board ledges. Move
  # the bush/washer past the ledges at Y=7, recenter above the seat, then lower.
  for base,lo in [('rear_thrust',6.5),('rear_bush',6.9)]:
   names=[base+'_L',base+'_R'];poses=[];level=10.15-lo
   poses += [(f'offset_descent_{dz}',{n:s[n].translate((0,7,dz)) for n in names}) for dz in np.linspace(24,level,16)]
   poses += [(f'recenter_{dy}',{n:s[n].translate((0,float(dy),level)) for n in names}) for dy in np.linspace(7,0,29)]
   poses += [(f'seat_{dz}',{n:s[n].translate((0,0,float(dz))) for n in names}) for dz in np.linspace(level,0,22)]
   step('14 dogleg '+base,poses,{'radial_offset_mm':7,'recenter_lower_face_z_mm':10.15})
  for sign in (-1,1):linear('15 bearing keeper '+str(sign),['rear_bearing_keeper_'+str(sign)],(0,sign,0),20)
  for i in range(4):linear('16 keeper screw '+str(i),['rear_keeper_M1p6x3_'+str(i)],(0,0,1))
  for i in range(3):
   n='M6p5_preload_plug_'+str(i)
   step('17 helical plug '+str(i),[(float(d),{n:helical(i,float(d))}) for d in np.linspace(4.375,relax,33)],{'pitch_mm':pitch,'unloaded_stack_height_mm':2*hf})
  samples=[]
  for dz in np.linspace(relax,0,19):
   group={};h=hw+float(dz)/2
   for i,theta in enumerate(angles):
    group['M6p5_preload_plug_'+str(i)]=helical(i,float(dz));group['spring_upper_seat_'+str(i)]=s['spring_upper_seat_'+str(i)].translate((0,0,float(dz)))
    for j in range(2):group[f'B8_spring_{i}_{j}']=at(spring(4,2.1,.3,4.45+j*h,h,j%2==1),r,theta)
   samples.append((float(dz),group))
  step('18 synchronized fixture compression',samples,{'free_to_working_height_mm':[hf,hw],'note':'Fixture keeps pressure carrier parallel. This geometric path does not demonstrate force balance during sequential adjustment.'})
  for i,theta in enumerate(angles):linear('19 locking dog '+str(i),['preload_lock_dog_'+str(i)],(math.cos(math.radians(theta)),math.sin(math.radians(theta)),0),15)
  linear('20 sensor cup',['removable_sensor_cup'],(0,0,1))
  th=math.radians(g['sensor_cup_access_angle_deg']);linear('21 cup radial screw',['sensor_cup_radial_screw'],(math.cos(th),math.sin(th),0),22)
  for n in ['diametric_magnet','magnet_keeper','keeper_screw_-4.25','keeper_screw_4.25']:linear('22 '+n,[n],(0,0,1))
  linear('23 PCBA',[n for n in s if n.startswith('sensor_pcba_')],(0,0,1))
  for n in ['pcb_edge_clamp_-7.7','pcb_edge_clamp_7.7','pcb_clamp_screw_-7.7','pcb_clamp_screw_7.7']:linear('24 '+n,[n],(0,0,1))
  linear('25 output mate',['output_yoke_interface'],(0,0,-1))
  for i in range(4):linear('26 output screw '+str(i),['output_M2x5_'+str(i)],(0,0,-1))
  rotating=[p['part_id'] for p in m['parts'] if p['owner']=='child'];fixed={n:v for n,v in s.items() if n not in rotating};motion=[]
  for degree in range(0,361,5):
   group={n:s[n].rotate((0,0,0),(0,0,1),degree) for n in rotating};motion.append({'deg':degree,'hits':checkpairs(group,fixed)})
  allpass=covered==set(s) and not any(x['hits'] for x in steps+motion)
  save(a.out/'assembly.json',{'status':'PASS_SAMPLED_NOMINAL' if allpass else 'FAIL','part_coverage_complete':covered==set(s),'uncovered':sorted(set(s)-covered),'part_count':len(s),'steps':steps,'rotation':motion,'input_sha256':inputs,'continuous_proof':False,'force_balance_or_fastener_strength_proof':False,'physical_tested':False,'manufacturing_released':False})
  (a.out/'assembly_progress.json').unlink()
 if a.phase=='life':
  cache={};cases=[]
  specs=[(w,c,None) for w in [(0,0),(.1,0),(0,.1),(.1,.1),(.2,0),(0,.2),(.2,.2)] for c in [(0,0),(.04,0),(0,.04),(.04,.04)]]
  specs += [(w,(0,0),i) for w in [(0,0),(.1,.1),(.2,.2)] for i in range(3)]
  for wear,comp,mismatch in specs:
   p=advance(wear,comp,pitch,hw,hf,series=2);total=p['total_wear_compression_mm'];df=wear[0]+comp[0];nom=p['cap_advance_mm'];cur=dict(s);sig={n:() for n in s}
   cur['front_lining']=lining(0,.6-df);cur['rear_lining']=lining(2.1-df,2.7-total);cur['floating_rotor']=s['floating_rotor'].translate((0,0,-df));cur['floating_pressure_carrier']=s['floating_pressure_carrier'].translate((0,0,-total))
   sig['front_lining']=(df,);sig['rear_lining']=(df,total);sig['floating_rotor']=(df,);sig['floating_pressure_carrier']=(total,);heights=[]
   for i,theta in enumerate(angles):
    adv=nom-(pitch/12 if i==mismatch else 0);h=hw+(total-adv)/2;heights.append(h);assert hw-1e-9<=h<=hf
    for n,dz in [('spring_lower_seat_'+str(i),-total),('spring_upper_seat_'+str(i),-adv)]:cur[n]=s[n].translate((0,0,dz));sig[n]=(round(dz,8),)
    n='M6p5_preload_plug_'+str(i);cur[n]=helical(i,-adv);sig[n]=(round(adv,8),)
    for j in range(2):
     n=f'B8_spring_{i}_{j}';cur[n]=at(spring(4,2.1,.3,4.45-total+j*h,h,j%2==1),r,theta);sig[n]=(total,round(adv,8),round(h,8))
   changed={n for n in s if cur[n] is not s[n]};hits=[]
   for n,j in itertools.combinations(cur,2):
    if n not in changed and j not in changed:continue
    key=(n,sig[n],j,sig[j])
    if key not in cache:cache[key]=overlap_volume(cur[n],cur[j])
    if cache[key]>1e-4:hits.append({'a':n,'b':j,'volume_mm3':cache[key]})
   cases.append({'wear_mm':wear,'compression_mm':comp,'one_detent_less_compressed_station':mismatch,'nominal_advance_mm':nom,'spring_height_by_station_mm':heights,'hits':hits});print('life',wear,comp,mismatch,len(hits),flush=True)
   save(a.out/'life_progress.json',{'status':'RUNNING_INCOMPLETE','states':cases})
  save(a.out/'lifecycle.json',{'status':'FAIL' if any(c['hits'] for c in cases) else 'PASS_SCOPED_NOMINAL_GEOMETRY','states':cases,'force_balance_verified':False,'nominal_catalog_deflection_not_exceeded':True,'force_not_guaranteed_by_height':True,'input_sha256':inputs,'unique_pairs':len(cache),'physical_tested':False,'manufacturing_released':False});(a.out/'life_progress.json').unlink()
 if a.phase=='retention':
  reversals=[]
  for name,fixed in [('floating_rotor',['integral_output_measurement_shaft']),('floating_pressure_carrier',['guide_sleeve_'+str(i) for i in range(3)]),('front_lining',['front_reaction_and_bearing_L','front_reaction_and_bearing_R']),('rear_lining',['floating_pressure_carrier'])]:
   brackets=[]
   for sign in (-1,1):
    lo,hi=0.,1.
    assert sum(overlap_volume(s[name].rotate((0,0,0),(0,0,1),sign*hi),s[n]) for n in fixed)>1e-6
    for _ in range(13):
     mid=(lo+hi)/2;v=sum(overlap_volume(s[name].rotate((0,0,0),(0,0,1),sign*mid),s[n]) for n in fixed)
     if v>1e-6:hi=mid
     else:lo=mid
    brackets.append({'sign':sign,'clear_deg':lo,'hit_deg':hi})
   reversals.append({'part':name,'brackets':brackets,'full_free_interval_deg':[sum(x['clear_deg'] for x in brackets),sum(x['hit_deg'] for x in brackets)]})
  retention=[]
  for name in ['rear_shaft_collar_L','rear_shaft_collar_R','removable_sensor_cup','front_lining','rear_lining']:
   fixed={n:v for n,v in s.items() if n!=name}
   for axis in range(3):
    for sign in (-1,1):
     d=[0,0,0];d[axis]=sign*.2;hits=checkpairs({name:s[name].translate(tuple(d))},fixed)
     retention.append({'part':name,'translation_mm':d,'blocking_parts':hits,'blocked':bool(hits)})
  save(a.out/'retention_reverse.json',{'nominal_reverse_clearance':reversals,'six_direction_retention_at_0p2mm':retention,'all_translation_attempts_blocked':all(x['blocked'] for x in retention),'scope':'Geometric stops only, not pullout strength, arbitrary escape paths, whole-joint backlash or encoder accuracy. Other installed parts held rigid.','input_sha256':inputs,'physical_tested':False,'manufacturing_released':False})
 assert all(sha(R/k)==v for k,v in inputs.items()),'Input changed during verification'
if __name__=='__main__':main()
