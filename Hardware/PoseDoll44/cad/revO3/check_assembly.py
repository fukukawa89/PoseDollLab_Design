"""Sample explicit assembly paths against already installed BReps. No collision whitelist."""
from compact_joint import *
from export_joint import hits
import numpy as np,os,itertools
from revo3_evidence import ArtifactReader

def main():
 verify,out=run_paths();folder=out/'joint';source=ArtifactReader('joint');manifest=source.json(verify/'joint.json')
 shapes={p['part_id']:cq.importers.importStep(str(source.path(folder/(p['part_id']+'.step')))).val() for p in manifest['parts']}
 installed={};steps=[];assembled=set();assembly_order=[]
 def evaluate(name,moving,samples,detail):
  found=[];count=0
  for label,group in samples:
   if name.startswith(('09','10')):print('sample',name,round(float(label),5),flush=True)
   for a,s in group.items():
    ba=bounds(s)
    for b,t in installed.items():
     if b in moving:continue
     bb=bounds(t)
     if not all(min(ba[k+3],bb[k+3])-max(ba[k],bb[k])>1e-6 for k in range(3)):continue
     v=s.intersect(t).Volume();count+=1
     if v>1e-4:found.append({'sample':label,'moving':a,'installed':b,'volume_mm3':v})
   for a,b in itertools.combinations(group,2):
    ba,bb=bounds(group[a]),bounds(group[b])
    if not all(min(ba[k+3],bb[k+3])-max(ba[k],bb[k])>1e-6 for k in range(3)):continue
    vol=group[a].intersect(group[b]).Volume();count+=1
    if vol>1e-4:found.append({'sample':label,'moving':a,'within_moving_group':b,'volume_mm3':vol})
   if len(found)>30:break
  steps.append({'step':name,'parts':moving,'samples':len(samples),'exact_BRep_pairs_checked':count,'status':'FAIL' if found else 'PASS_SAMPLED_NOMINAL_ONLY','intersections':found,'method':detail})
  print(name,steps[-1]['status'],len(found),flush=True)
  for n in moving:
   installed[n]=shapes[n]
   if n in {p['part_id'] for p in manifest['parts']} and n not in assembled: assembled.add(n);assembly_order.append(n)
 def translate(name,names,vec,dist=30):
  offsets=sorted(set([0,.05,.1,.25,.5,1,2,3,4,5,*range(6,int(dist)+1,2),dist]),reverse=True)
  evaluate(name,names,[(float(d),{n:shapes[n].translate(tuple(d*v for v in vec)) for n in names}) for d in offsets],{'motion':'linear','direction':vec,'start_distance_mm':dist,'minimum_end_step_mm':.05})
 translate('01 shaft datum',['measurement_shaft'],(0,0,-1),0)
 # Install keeper hardware on the accessible bare shaft before the integral
 # PCB shelves close radially around it. Post-closure axial insertion is blocked.
 for n in ('diametric_magnet','magnet_keeper','keeper_screw_-4.25','keeper_screw_4.25'):translate('02 bench sensor subassembly '+n,[n],(0,0,1),20)
 for base in ('rear_bush','front_bush','thrust_rear','thrust_front'):
  for side,sign in [('L',-1),('R',1)]:translate('03 radial '+base+' '+side,[base+'_'+side],(sign,0,0),10)
 for side,sign in [('L',-1),('R',1)]:translate('04 split housing '+side,['housing_'+side],(sign,0,0),32)
 translate('04b rear cup registered to cartridge',['one_piece_brake_cup'],(0,0,-1),35)
 for i in range(4):translate('04c axial cup screw '+str(i),['cup_mount_'+str(i)],(0,0,1),20)
 for n in ('bearing_clamp_-6','bearing_clamp_6'):translate('05 case fastening '+n,[n],(-1,0,0),20)
 for n in ('front_lining_backing','front_friction_lining','floating_brake_disc','rear_friction_lining','rear_lining_backing','keyed_pressure_plate','spring_front_washer'):translate('06 rear loading '+n,[n],(0,0,-1),35)
 # Springs are loaded in their free geometry, from the front seat toward the cap.
 spring_names=['disc_spring_'+str(i+1) for i in range(4)]
 for i in range(3,-1,-1):
  n=spring_names[i];free=disc_spring(-8.6+STACK_SHIFT+i*.85,.85,i%2==1)
  samples=[(d,{n:free.translate((0,0,-d))}) for d in (30,20,10,5,2,1,.5,.1,0)]
  evaluate('07 free spring '+str(i+1),[n],samples,{'free_height_mm':.85});installed[n]=free
 free_rear=shapes['spring_rear_washer'].translate((0,0,-1.05))
 evaluate('08 rear free washer',['spring_rear_washer'],[(d,{'spring_rear_washer':free_rear.translate((0,0,-d))}) for d in (30,20,10,5,2,1,.5,.1,0)],{'free_stack_plus_washers_mm':4.4});installed['spring_rear_washer']=free_rear
 samples=[]
 for dz in np.linspace(-10.05,-1.05,37):
  cap=shapes['threaded_adjuster_cap'].rotate((0,0,0),(0,0,1),float(dz/THREAD_PITCH*360)).translate((0,0,float(dz)))
  samples.append((float(dz),{'threaded_adjuster_cap':cap}))
 evaluate('09 helical cap insertion',['threaded_adjuster_cap'],samples,{'pitch_mm':THREAD_PITCH,'sample_increment_turns':.25/THREAD_PITCH,'thread_tolerance':'reference geometry only'})
 group=['threaded_adjuster_cap','spring_rear_washer',*spring_names];samples=[]
 for dz in np.linspace(-1.05,0,22):
  h=(2.35-dz)/4
  moving={'threaded_adjuster_cap':shapes['threaded_adjuster_cap'].rotate((0,0,0),(0,0,1),float(dz/THREAD_PITCH*360)).translate((0,0,float(dz))), 'spring_rear_washer':shapes['spring_rear_washer'].translate((0,0,float(dz)))}
  moving.update({n:disc_spring(-5.2+STACK_SHIFT-4*h+i*h,h,i%2==1) for i,n in enumerate(spring_names)});samples.append((float(dz),moving))
 evaluate('10 coordinated spring compression',group,samples,{'spring_height_free_mm':.85,'spring_height_working_mm':.5875,'compression_increment_mm':.05,'intragroup_contacts':'Nominal conical geometry remains tangent; friction/deformation not simulated'})
 translate('11 positive cap lock',['cap_lock_dog_screw'],(1,0,0),15)
 translate('13 unscaled sensor PCBA',[n for n in shapes if n.startswith('sensor_pcba_')],(0,0,1),25)
 for n in ('pcb_edge_clamp_-7.7','pcb_edge_clamp_7.7','pcb_clamp_screw_-7.7','pcb_clamp_screw_7.7'):translate('14 PCBA retention '+n,[n],(0,0,1),20)
 # The tool is inserted only with the lock dog removed. It may not pass the shaft by deleting it.
 del installed['cap_lock_dog_screw']
 shapes['hollow_pin_spanner']=cq.importers.importStep(str(source.path(folder/'hollow_pin_spanner.step'))).val()
 translate('15 hollow tool insertion',['hollow_pin_spanner'],(0,0,-1),25)
 del installed['hollow_pin_spanner']
 translate('15b reinstall positive cap lock',['cap_lock_dog_screw'],(1,0,0),15)
 rotating=[p['part_id'] for p in manifest['parts'] if p['owner']=='child']
 samples=[(int(a),{n:shapes[n].rotate((0,0,0),(0,0,1),a) for n in rotating}) for a in range(0,361,5)]
 evaluate('16 single-axis rotation',rotating,samples,{'angle_step_deg':5,'continuous_collision_proof':False,'full_body_motion':False})
 save(verify/'assembly.json',{'schema':'revo3-assembly-v1','run_id':os.environ['REVO3_RUN_ID'],'steps':steps,'status':'FAIL' if any(x['status']=='FAIL' for x in steps) else 'PASS_SAMPLED_NOMINAL_ONLY','reverse_path':'Reverse of these nominal sampled transforms in reverse assembly order; bonded/pressed fits and actual thread tools not simulated','coverage':{'expected_part_ids':sorted(p['part_id'] for p in manifest['parts']),'assembled_part_ids':sorted(assembled),'final_installed_part_ids':sorted(installed),'final_identity_set':set(installed)==set(p['part_id'] for p in manifest['parts']),'missing':sorted(set(p['part_id'] for p in manifest['parts'])-assembled),'extra':sorted(assembled-set(p['part_id'] for p in manifest['parts'])),'exact_identity_set':assembled==set(p['part_id'] for p in manifest['parts']),'assembly_DAG':{'ordered_first_install':assembly_order,'edges':[[a,b] for a,b in zip(assembly_order,assembly_order[1:])],'scope':'One feasible sequential assembly order; retention requires separate constraint graph'}},'consumed_inputs':source.receipt(),'not_proven':['Continuous path/tolerance extrema','Small-fastener helical trajectories and screwdriver access','Output coupler/mating sensor plug and wires','Preload deformation, shaft key sliding friction, split bore clamping distortion','Physical hand assembly and endurance'],'physical_tested':False})
if __name__=='__main__':main()