"""Mass/COM accounting for the combined O13 arm candidate, not whole body.
Real CAD solids + explicit unmodeled allowance; sensor reservation volumes are
not treated as known populated-board masses. Manual support remains permitted.
"""
from update_loads import props
from solid_ops import *
from model import fk,rotation

def density(name):
 return .00785 if any(w in name for w in ('screw','nut','shoulder_D4','spring','_M4_','_M3_','retainer_')) else .00122

def main():
 watched={}
 def read(p):
  p=Path(p);before=sha(p);data=p.read_bytes();assert sha(p)==before;watched[p.relative_to(H).as_posix()]=before;return data
 def npz(p):
  import io
  return dict(np.load(io.BytesIO(read(p))))
 states=json.loads(read(OUT/'integrated_arm_states.json'))['states'];maps=json.loads(read(G9/'bounded_mapping.json'))['characters']
 core=npz(OUT/'printed_core/parts.npz');fast=npz(G8/'fastened_core/fasteners.npz');compact=npz(OUT/'compact_hinge/parts.npz');carriers=npz(OUT/'carriers/parts.npz')
 old=json.loads(read(H/'generated/revO6/runs/o6_20260924_r1/joint_M4_validated/manifest.json'));groups=[]
 read(Path(__file__));read(Path(__file__).with_name('update_loads.py'));read(Path(__file__).with_name('solid_ops.py'))
 for g in maps:
  ch,side=g['character'],g['side'];key=ch+'_'+side;p=json.loads(read(OUT/f'clavicle_trial/{key}_profile.json'));raw=npz(OUT/f'braked_module/{key}.npz');rows=[]
  def add(name,t,body,stage,rho=None):
   v,c=props(t);rows.append({'name':name,'body':body,'downstream_stage':stage,'mass_g':float(v*(density(name) if rho is None else rho)),'local_com_mm':c.tolist(),'mass_basis':'solid volume times assumed density'})
  add('clav_input',core['C01'],f'{side}/clav_input',0)
  for k,t in core.items():
   if k not in ('C01','C02'):add('clav_'+k,t,f'{side}/clav_ring',1)
  for k,t in fast.items():add('clav_retainer_'+k,t,f'{side}/clav_ring',1,.00785)
  add('integrated_clav_output_and_P_case_plus',carriers[key+'_integrated'],f'{side}/clav_output',2,.00122)
  for k,t in raw.items():
   if k=='P_case_plus':continue
   role='P' if k.startswith('P_') else 'D' if k.startswith('D_') else k if k in ('C01','C02') else 'ring';stage={'P':2,'C01':3,'ring':4,'C02':5,'D':6}[role]
   add(k,t,f'TUT_{side}/'+role,stage)
  for k,t in fast.items():add('shoulder_retainer_'+k,t,f'TUT_{side}/ring',4,.00785)
  for axis in (f'elbow_{side}.flex',f'forearm_{side}.twist'):
   for r in old['parts']:rows.append({'name':axis+'/'+r['part_id'],'body':axis+'/'+r['owner'],'downstream_stage':6,'mass_g':r['mass_g'],'local_com_mm':r['local_com_mm'],'mass_basis':'retained M4 manifest'})
  for axis in (f'hand_{side}.flex',f'hand_{side}.deviate'):
   for name,t in compact.items():add(axis+'/'+name,t,axis+('/child' if name=='printed_lever' else '/parent'),6,.00122 if name.startswith('printed_') else .00785)
  names=['clavicle_protract','clavicle_elevate','phi','alpha','beta','psi'];maxima={n:{'gravity_Nm':0} for n in names};cases=[]
  for i,st in enumerate(s for s in states if s['character']==ch):
   T,A=fk(p,st['requested_angles_deg']);F={o['id']:np.array(o['frame']) for o in st['objects']};origin=A[f'upperarm_{side}.flex']['origin'];base=T[f'clavicle_{side}'][:3,:3]@np.array(g['mount_matrix']);q=np.array(g['paths'][i]['angles_deg'][-1])+g['paths'][i]['zero_offsets_deg'];P=rotation([0,0,1],q[0]);RA=P@rotation([1,0,0],q[1]);RB=RA@rotation([0,1,0],q[2])
   origins=[A[f'clavicle_{side}.protract']['origin'],A[f'clavicle_{side}.elevate']['origin']]+[origin]*4
   directions=[A[f'clavicle_{side}.protract']['direction'],A[f'clavicle_{side}.elevate']['direction'],base[:,2],(base@P)[:,0],(base@RA)[:,1],(base@RB)[:,2]]
   masses=[]
   for row in rows:
    f=F[row['body']];masses.append((row['downstream_stage'],row['mass_g'],f[:3,:3]@row['local_com_mm']+f[:3,3]))
   # Explicit 136 g downstream allowance, including unmodeled sensor/PCB,
   # skeleton and hand components; reservation meshes are not added again.
   for node,m,local in [(f'upperarm_{side}',24,[0,0,0]),(f'elbow_{side}',8,[0,0,0]),(f'forearm_{side}',8,[0,0,0]),(f'hand_{side}.flex_frame',8,[0,0,0]),(f'hand_{side}',8,[0,0,0]),(f'upperarm_{side}',20,[0,0,-20]),(f'forearm_{side}',20,[0,0,-20]),(f'hand_{side}',40,[0,0,-20])]:masses.append((6,m,T[node][:3,:3]@local+T[node][:3,3]))
   f=F[f'TUT_{side}/C02'];masses.append((5,8,f[:3,:3]@np.array([0,0,12])+f[:3,3]));vals={}
   for j,n in enumerate(names,1):
    moment=sum((np.cross((c-origins[j-1])/1000,[0,0,-m*9.80665/1000]) for stage,m,c in masses if stage>=j),start=np.zeros(3));v=abs(float(moment@directions[j-1]));vals[n]=v
    if v>maxima[n]['gravity_Nm']:maxima[n]={'gravity_Nm':v,'pose':st['pose']}
   cases.append({'pose':st['pose'],'gravity_Nm':vals})
  for r in maxima.values():r.update(preferred_hold_Nm=1.5*r['gravity_Nm']+.02,measured_hold_Nm=None,self_holding_is_hard_gate=False,hand_force_at_100mm_if_zero_friction_N=r['gravity_Nm']/.1)
  groups.append({'id':key,'modeled_arm_solids_g':sum(r['mass_g'] for r in rows),'parts':rows,'unmodeled_downstream_allowance_g':144,'sensor_reservation_mass_added_separately':False,'physical_axes':maxima,'cases':cases})
 assert all(sha(H/k)==v for k,v in watched.items())
 save('integrated_loads.json',{'complete':True,'inputs_sha256':watched,'characters':groups,'assumptions':{'plastic_solid_density_g_cm3':1.22,'stock_metal_g_cm3':7.85,'density_not_user_material_measurement':True,'self_hold_multiplier':1.5,'wire_allowance_Nm':.02},'scope':'Current arm candidate only. Integrated union replaces both original printed solids, avoiding double counting. 144 g allowance covers missing downstream parts and sensor reservations; it is a budget, not final design weight. Missing external supports, full body, strength, material/creep validation. No numerical friction inferred from user hand-feel report.','full_body_mass_g':None,'manufacturing_released':False})
 print([(g['id'],round(g['modeled_arm_solids_g'],1),{k:round(v['preferred_hold_Nm'],3) for k,v in g['physical_axes'].items()}) for g in groups],flush=True)
if __name__=='__main__':main()
