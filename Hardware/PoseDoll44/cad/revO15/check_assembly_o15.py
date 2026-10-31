"""Order-sensitive nominal assembly checks with deliberately blocked old-cup control."""
from common import *
import importlib

def path_check(label,moving,fixed,points,step=.5):
 bb={k:np.array(v.bounding_box()) for k,v in fixed.items()};rr=[];peak=0.;samples=0
 for a,b in zip(points,points[1:]):
  a=np.array(a,float);b=np.array(b,float)
  for u in np.linspace(0,1,max(2,int(np.ceil(np.linalg.norm(b-a)/step))+1)):
   delta=a+(b-a)*u;samples+=1
   for k,v in moving.items():
    vb=np.array(v.bounding_box())+np.tile(delta,2);q=None
    for j,w in fixed.items():
     if np.any(np.minimum(vb[3:],bb[j][3:])<=np.maximum(vb[:3],bb[j][:3])+1e-6):continue
     if q is None:q=v.translate(delta)
     vol=float((q^w).volume());peak=max(peak,vol)
     if vol>1e-4 and len(rr)<12:rr.append({'moving':k,'obstacle':j,'translation_mm':delta.tolist(),'volume_mm3':vol})
 return {'label':label,'samples':samples,'step_mm':step,'maximum_overlap_mm3':peak,'findings':rr,'path_mm':[list(map(float,p)) for p in points]}

def main():
 rows=[];source=read(OUT/'ring_assembly_without_obsolete_pin.json')['path'];# compress only collinear path nodes
 path=[source[0]]
 for i in range(1,len(source)-1):
  if not np.array_equal(np.array(source[i])-source[i-1],np.array(source[i+1])-source[i]):path.append(source[i])
 path.append(source[-1])
 for name in ('hinge','tut','wide_tut','three_axis','clavicle_core','ankle_core'):
  p,o,sku=importlib.import_module(name).make();local=[]
  if name=='hinge':
   rotor={k:v for k,v in p.items() if o[k]=='child' or k in ('M3_nut','M3_reaction_washer','shoulder_D4_L8_M3_thread6','inner_M4_wide','outer_M4_wide','spring_1','spring_2','front_M4_washer')}
   fixed={k:v for k,v in p.items() if k not in rotor and not k.startswith('case_') and k!='base_service_half'}
   local.append(path_check('rotor_stock_radial_service',rotor,fixed,[[0,0,0],[0,45,0]]))
   prefixes=[''];Mlist=[np.eye(3)];origins=[np.zeros(3)]
  else:
   local.append(path_check('C14_to_lower_fork_before_other_fork_or_stock',{'C14':p['C14']},{'C01':p['C01']},read(OUT/'simple_assembly_path_ankle_core.json')['path'] if name=='ankle_core' else path,.25))
   local.append(path_check('C02_from_above_before_stock',{'C02':p['C02']},{k:p[k] for k in ('C01','C14')},[[0,0,0],[0,0,80]]))
   retained={k:v for k,v in p.items() if k in ('C01','C02','C14') or k.endswith(('M3_nut','M3_reaction_washer'))}
   local.append(path_check('C15_upper_close',{'C15':p['C15']},retained,[[0,0,0],[0,0,8],[-70,0,8]]))
   prefixes=['C01_','C02_'];Mlist=[np.c_[[0,0,-1],[0,1,0],[1,0,0]],np.c_[[0,0,1],[1,0,0],[0,1,0]]];origins=[np.array([16,0,0]),np.array([0,16,0])]
  for prefix,M,O in zip(prefixes,Mlist,origins):
   key='lever_cup' if not prefix else prefix[:-1];cup=p[key];normal=M[:,2]
   exclude=[k for k in p if 'pcb_' in k or 'sensor_' in k or 'passive_' in k or 'magnet' in k or k.startswith(('P_','D_'))]
   fixed={k:v for k,v in p.items() if k not in exclude}
   # Outer stack and shoulder bolt enter before small cap nuts obstruct the bore.
   stacknames=['outer_M4_wide','spring_1','spring_2','front_M4_washer','shoulder_D4_L8_M3_thread6']
   assembled={k:v for k,v in fixed.items() if not any(k.endswith(x) for x in stacknames)}
   for label in stacknames:
    k=label if not prefix else prefix+'+1_'+label
    local.append(path_check(prefix+label+'_axial', {k:p[k]},assembled,[np.zeros(3),normal*45]))
    assembled[k]=p[k]
   for suffix in ('magnet_seat','magnet','magnet_cap'):
    k=prefix+suffix
    fixed2={key:cup}
    if suffix!='magnet_seat':fixed2[prefix+'magnet_seat']=p[prefix+'magnet_seat']
    if suffix=='magnet_cap':fixed2[prefix+'magnet']=p[prefix+'magnet']
    local.append(path_check(k+'_insert', {k:p[k]},fixed2,[np.zeros(3),normal*35]))
   # Removed cradle/PCB/clip can lift along board normal before cup service.
   ckey=prefix+'sensor_cradle';selected={k:v for k,v in p.items() if k.startswith(prefix) and (k==ckey or k.startswith(prefix+'pcb_clip') and not k.endswith('_nut') or k.startswith(prefix+'sensor_') or k.startswith(prefix+'passive_'))}
   fixed3={k:v for k,v in p.items() if k not in selected and not k.startswith(('P_','D_'))}
   # Clip screw is removed first, so do not count its retained shaft in the lift.
   selected.pop(prefix+'pcb_clip_screw',None);fixed3.pop(prefix+'pcb_clip_screw',None)
   # Cradle local board normal can differ from cup frame by only axial phase.
   local.append(path_check(ckey+'_service_lift',selected,fixed3,[np.zeros(3),normal*40]))
  bad=[x for x in local if x['findings']];rows.append({'family':name,'checks':local,'failed_checks':len(bad)});print('ASSEMBLY',name,'failed',[(x['label'],x['findings'][0]) for x in bad],flush=True);save('assembly_order_checks.json',{'families':rows,'scope':'Nominal sampled rigid paths, staged order explicitly recorded. Thread tightening, compliance, printed tolerances and full-body tools are not simulated.','physical_tested':False})
 # Old closed cup must block the large washer: catches accidental removal of obstacles.
 old={k:from_tri_exact(v) for k,v in np.load(OUT/'assembly_witness/pre_repair_hinge_parts.npz').items()}
 negative=path_check('old_closed_cup_expected_block',{'washer':old['outer_M4_wide']},{'cup':old['lever_cup']},[[0,0,0],[0,0,35]])
 if not negative['findings']:raise RuntimeError('negative control did not detect old closed cup')
 d=read(OUT/'assembly_order_checks.json');d['old_geometry_negative_control']=negative;d['source_sha256']={p.name:sha(p) for p in Path(__file__).parent.glob('*.py')};save('assembly_order_checks.json',d)
if __name__=='__main__':main()
