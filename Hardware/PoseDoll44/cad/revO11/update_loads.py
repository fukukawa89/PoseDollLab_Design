"""O11 component mass/gravity demand with printed-body density and current layout.
Solid-volume masses deliberately do not claim to predict slicer infill or real weight.
"""
from solid_ops import *
sys.path.append(str(H/'cad'))
from model import fk,rotation

def props(t):
 v=np.einsum('ij,ij->i',t[:,0],np.cross(t[:,1],t[:,2]))/6
 return v.sum(),(v[:,None]*(t[:,0]+t[:,1]+t[:,2])/4).sum(0)/v.sum()
def main():
 observed={}
 def remember(p):
  key=str(p.relative_to(H));value=sha(p)
  if key in observed:assert observed[key]==value,'Input changed before read'
  observed[key]=value
 states=[];sources=[Path(__file__),G9/'bounded_mapping.json']
 for p in sources:remember(p)
 for char in ('manny','quinn'):
  p=OUT/f'clavicle_trial/{char}_states.json';sources.append(p);remember(p);states+=json.loads(p.read_text())['states']
 oldp=H/'generated/revO6/runs/o6_20260924_r1/joint_M4_validated/manifest.json';sources.append(oldp);remember(oldp);old=json.loads(oldp.read_text());reports=[]
 for group in json.loads((G9/'bounded_mapping.json').read_text())['characters']:
  char,side=group['character'],group['side'];key=char+'_'+side
  pp=OUT/f'clavicle_trial/{key}_profile.json';sources.append(pp);remember(pp);p=json.loads(pp.read_text());file=OUT/'braked_module'/f'{key}.npz';sources.append(file);remember(file);meta=[]
  raw=dict(np.load(file));fast=G8/'fastened_core/fasteners.npz';sources.append(fast);remember(fast);raw.update({'retainer_'+k:t for k,t in np.load(fast).items()})
  for name,t in raw.items():
   v,c=props(t)
   metal=any(w in name for w in ('screw','nut','shoulder_SBSM','spring','_M4_','_M3_','retainer_'))
   density=.00785 if metal else .0014 if 'washer' in name else .00122
   role='P' if name.startswith('P_') else 'D' if name.startswith('D_') else name if name in ('C01','C02') else 'ring'
   meta.append({'name':name,'role':role,'mass_g':float(v*density),'local_com_mm':c.tolist(),'density_g_mm3':density})
  stages={'P':0,'C01':1,'ring':2,'C02':3,'D':4};names=['phi','alpha','beta','psi'];maximum={n:{'gravity_Nm':0} for n in names};cases=[]
  for i,state in enumerate(s for s in states if s['character']==char):
   T,A=fk(p,state['requested_angles_deg']);F={o['id']:np.array(o['frame']) for o in state['objects']};origin=A[f'upperarm_{side}.flex']['origin'];B=T[f'clavicle_{side}'][:3,:3]@np.array(group['mount_matrix']);q=np.array(group['paths'][i]['angles_deg'][-1])+group['paths'][i]['zero_offsets_deg'];P=rotation([0,0,1],q[0]);RA=P@rotation([1,0,0],q[1]);RB=RA@rotation([0,1,0],q[2]);directions=[B[:,2],(B@P)[:,0],(B@RA)[:,1],(B@RB)[:,2]];masses=[]
   for row in meta:
    f=F[f'TUT_{side}/'+row['role']];masses.append((stages[row['role']],row['mass_g'],f[:3,:3]@row['local_com_mm']+f[:3,3]))
   for ob in state['objects']:
    if not any(ob['id'].startswith(s+'_'+side) for s in ('elbow','forearm','hand')):continue
    owner=ob['library'].split('_')[1];f=np.array(ob['frame'])
    for row in old['parts']:
     if row['owner']==owner:masses.append((4,row['mass_g'],f[:3,:3]@row['local_com_mm']+f[:3,3]))
   for node,g,local in [(f'upperarm_{side}',24,[0,0,0]),(f'elbow_{side}',8,[0,0,0]),(f'forearm_{side}',8,[0,0,0]),(f'hand_{side}.flex_frame',8,[0,0,0]),(f'hand_{side}',8,[0,0,0]),(f'upperarm_{side}',20,[0,0,-20]),(f'forearm_{side}',20,[0,0,-20]),(f'hand_{side}',40,[0,0,-20])]:masses.append((4,g,T[node][:3,:3]@local+T[node][:3,3]))
   f=F[f'TUT_{side}/C02'];masses.append((3,8,f[:3,:3]@np.array([0,0,12])+f[:3,3]));values={}
   for j,n in enumerate(names,1):
    moment=sum((np.cross((c-origin)/1000,[0,0,-g*9.80665/1000]) for stage,g,c in masses if stage>=j),start=np.zeros(3));val=abs(float(moment@directions[j-1]));values[n]=val
    if val>maximum[n]['gravity_Nm']:maximum[n]={'gravity_Nm':val,'pose':state['pose']}
   cases.append({'pose':state['pose'],'gravity_Nm':values})
  reff=2/3*(6**3-2.15**3)/(6**2-2.15**2)/1000
  for n,row in maximum.items():
   row['required_hold_Nm']=1.5*row['gravity_Nm']+.02
   if n in ('alpha','beta'):row['mu_needed_if_210N_each']=row['required_hold_Nm']/(2*210*reff)
  reports.append({'id':key,'modeled_module_solid_mass_g':sum(r['mass_g'] for r in meta),'parts':meta,'physical_axes':maximum,'cases':cases,'unmodeled_downstream_allowance_g':144})
 before={str(p.relative_to(H)):sha(p) for p in set(sources)};assert before==observed,'Input changed during load calculation'
 out={'inputs_sha256':before,'characters':reports,'material_source':'https://us.store.bambulab.com/products/pla-cf','assumptions':{'printed_density_g_cm3':1.22,'stock_steel_density_g_cm3':7.85,'outer_thrust_washer_density_g_cm3':1.4,'holding_factor':1.5,'wire_allowance_Nm':.02},'scope':'Solid-volume mass budget and unsupported-arm gravity demand; no material strength/creep, contact support or whole-body mass qualification. Infill reduces real mass but is not used to reduce this demand. Outer twist parts are packaging concepts.','physical_tested':False,'manufacturing_released':False}
 save('loads.json',out);print([(c['id'],round(c['modeled_module_solid_mass_g'],2),{n:round(v['required_hold_Nm'],4) for n,v in c['physical_axes'].items()}) for c in reports])
if __name__=='__main__':main()

