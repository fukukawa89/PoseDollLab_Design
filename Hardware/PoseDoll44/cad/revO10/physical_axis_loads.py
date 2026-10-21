"""Per-physical-axis gravity of finite TUT with explicit inherited allowances.
No friction coefficient is treated as measured. No manufactured capacity rating.
"""
from assemble_shoulders import *

def props(t):
 v=np.einsum('ij,ij->i',t[:,0],np.cross(t[:,1],t[:,2]))/6;volume=v.sum();return float(volume),((v[:,None]*(t[:,0]+t[:,1]+t[:,2])/4).sum(0)/volume)
def main():
 states=json.loads((OUT/'shoulder_assembly/states.json').read_text())['states'];mapping=json.loads((G9/'bounded_mapping.json').read_text());oldman={f:json.loads(p.read_text()) for f,p in [('M4',H/'generated/revO6/runs/o6_20260924_r1/joint_M4_validated/manifest.json'),('LP6',H/'generated/revO7/runs/o7_20260924_r1/LP6_current/manifest.json')]};reports=[]
 for group in mapping['characters']:
  char,side=group['character'],group['side'];key=char+'_'+side;p=profile(char,side);raw=dict(np.load(OUT/'finite_twist'/f'{key}.npz'));metadata=[]
  for name,t in raw.items():
   v,c=props(t);density=.00785 if 'screw' in name or 'nut' in name else .0014 if 'washer' in name else .00114
   role='P' if name.startswith('P_') else 'D' if name.startswith('D_') else 'ring' if name in ('C14','C15') else name
   metadata.append({'name':name,'role':role,'mass_g':v*density,'com_mm':c.tolist(),'density_g_mm3':density})
  fp=np.load(H/'generated/revO8/runs/o8_20260925_r1/fastened_core/fasteners.npz')
  for name,t in fp.items():
   v,c=props(t);metadata.append({'name':name,'role':'ring','mass_g':v*.00785,'com_mm':c.tolist(),'density_g_mm3':.00785})
  stages={'P':0,'C01':1,'ring':2,'C02':3,'D':4};names=['phi','alpha','beta','psi'];maxima={n:{'gravity_Nm':0} for n in names};caseout=[]
  for k,state in enumerate([s for s in states if s['character']==char]):
   T,A=fk(p,state['requested_angles_deg']);frames={o['id']:np.array(o['frame']) for o in state['objects']};origin=A[f'upperarm_{side}.flex']['origin'];B=T[f'clavicle_{side}'][:3,:3]@np.array(group['mount_matrix']);pp,aa,bb,ss=np.array(group['paths'][k]['angles_deg'][-1])+group['paths'][k]['zero_offsets_deg'];P=rotation([0,0,1],pp);RA=P@rotation([1,0,0],aa);RB=RA@rotation([0,1,0],bb);directions=[B[:,2],(B@P)[:,0],(B@RA)[:,1],(B@RB)[:,2]];masses=[]
   for row in metadata:
    F=frames[f'TUT_{side}/'+row['role']];masses.append((stages[row['role']],row['mass_g'],F[:3,:3]@row['com_mm']+F[:3,3]))
   for ob in state['objects']:
    if not any(ob['module'].startswith(s+'_'+side) for s in ('elbow','forearm','hand')):continue
    fam,owner=ob['library'].split('_');F=np.array(ob['frame'])
    for row in oldman[fam]['parts']:
     if row['owner']==owner:masses.append((4,row['mass_g'],F[:3,:3]@row['local_com_mm']+F[:3,3]))
   # Preserve all former carrier allocations for the 7 affected axes (56 g)
   # plus cover/hand allowances. Add 8 g for unmodeled TUT sensors/magnets.
   alloc=[(f'upperarm_{side}',24,[0,0,0]),(f'elbow_{side}',8,[0,0,0]),(f'forearm_{side}',8,[0,0,0]),(f'hand_{side}.flex_frame',8,[0,0,0]),(f'hand_{side}',8,[0,0,0]),(f'upperarm_{side}',20,[0,0,-20]),(f'forearm_{side}',20,[0,0,-20]),(f'hand_{side}',40,[0,0,-20])]
   for node,g,local in alloc:masses.append((4,g,T[node][:3,:3]@local+T[node][:3,3]))
   F=frames[f'TUT_{side}/C02'];masses.append((3,8,F[:3,:3]@np.array([0,0,12])+F[:3,3]))
   values={}
   for j,n in enumerate(names,1):
    moment=sum((np.cross((c-origin)/1000,[0,0,-g*9.80665/1000]) for stage,g,c in masses if stage>=j),start=np.zeros(3));val=abs(float(moment@directions[j-1]));values[n]=val
    if val>maxima[n]['gravity_Nm']:maxima[n]={'gravity_Nm':val,'pose':state['pose']}
   caseout.append({'pose':state['pose'],'gravity_Nm':values})
  for n,row in maxima.items():
   need=1.5*row['gravity_Nm']+.02;row['required_hold_Nm']=need;row['friction_only_hand_force_at_60mm_N']=need/.06
   if n in ('alpha','beta'):
    row['journal_clamp_force_each_at_assumed_mu_N']={str(mu):need/(2*mu*.0015) for mu in (.08,.15,.22,.30)}
    row['two_equal_solid_3mm_shafts_torsion_shear_MPa']=16*(need/2)*1000/(np.pi*3**3)
    row['one_shaft_taking_all_torque_shear_MPa']=16*need*1000/(np.pi*3**3)
    row['comparison_4p5mm_two_shafts_shear_MPa']=16*(need/2)*1000/(np.pi*4.5**3)
    row['scope']='Ideal solid round sections, no notch factor, no bending, no creep, no strength allowance. Geometry has thin/stepped printed journals; sharing is unverified. These are load demands, not capacities.'
  reports.append({'id':key,'new_TUT_modeled_mass_g':sum(r['mass_g'] for r in metadata),'parts':metadata,'physical_axes':maxima,'cases':caseout,'allowance_g_downstream':144,'static_support':'unsupported arm with torso held; no body-weight support on hands'})
  print(key,round(reports[-1]['new_TUT_modeled_mass_g'],2),[(n,round(x['required_hold_Nm'],4)) for n,x in maxima.items()],flush=True)
 (OUT/'physical_axis_loads.json').write_text(json.dumps({'characters':reports,'holding_margin_factor':1.5,'cable_torque_assumption_Nm':.02,'measured_friction':False,'manufacturing_released':False,'scope':'Mass and gravity demands for stopped finite-twist candidate at original targets, including missing-part allowances. Not a fit or force-balance approval.'},indent=2)+'\n')
if __name__=='__main__':main()
