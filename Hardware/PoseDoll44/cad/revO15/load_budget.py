"""Conditional whole-assembly mass and gravity moments with pelvis supported.
Uses each retained solid exactly once. No invented floor reactions or friction.
"""
from common import *
from fitted import build_fitted as build_connected
from carriers_swept import ASSEMBLY_POSE
from layout_fullbody import build,fk


def declared_cases(char):
 cases={'assembly':ASSEMBLY_POSE,**read(H/'mechanical_manifest/revO_pose_cases.json')['cases']}
 for i,a in enumerate(read(OUT/'serial_clavicle_bilateral_search.json')['cases']):cases['bilateral_clavicle_'+str(i)]=a
 profile=build(char,{},geometry=False)[4]
 for a in profile['axes']:
  if a['id'].startswith('pelvis.'):continue
  for i,v in enumerate(a['limits_rad']):cases[a['id']+'.'+str(i)]={a['id']:float(np.rad2deg(v))}
 seen=set();out={}
 for k,a in cases.items():
  key=tuple(sorted(a.items()))
  if key not in seen:seen.add(key);out[k]=a
 return out


def density(sku):
 if sku is None:return 1.27e-6,'solid PETG proxy; kg/mm3'
 if sku in ('AS5048A_MINI_PCBA','C1_CENTRAL_PCBA'):return 1.85e-6,'bare FR4 proxy; packages separate'
 if sku in ('PCBA_INCLUDED','C1_PCBA_INCLUDED'):return 2.0e-6,'component-envelope proxy, not measured package mass'
 if sku.startswith(('JST_','HEADER_','FFC_','SEEED_','USB_')):return 1.4e-6,'connector/cable polymer+metal envelope proxy'
 if sku.startswith('MAGNET_'):return 7.4e-6,'NdFeB nominal density assumption'
 return 7.9e-6,'steel nominal density assumption'


def raw_axes(m):
 W=np.array(m['world_mount']);q=m['angles_deg'];O=np.array(m['origin_mm']);kind=m['kind']
 if kind in ('tut','wide_tut','three_axis'):
  p,a,b=q[:3];directions=[W[:,2],W@rot(2,p)[:,0],W@rot(2,p)@rot(0,a)[:,1]];sets=[{'C01','ring','C02','D'},{'ring','C02','D'},{'C02','D'}]
  if len(q)==4:directions.append(W@rot(2,p)@rot(0,a)@rot(1,b)[:,2]);sets.append({'D'})
 elif kind in ('core','clavicle_core','ankle_core'):
  a,b=q;directions=[W@rot(1,-b)[:,0],-W[:,1]];sets=[{'C01'},{'ring','C01'}]
 else:directions=[W[:,2]];sets=[{'child'}]
 return [(O,float(np.linalg.det(W))*u,owners) for u,owners in zip(directions,sets)]


def main(variant='fitted'):
 rows=[]
 for char in ('quinn','manny'):
  pp,mm,st,f,pr,_=build_connected(char,ASSEMBLY_POSE);_,m0,_,_,_=build(char,ASSEMBLY_POSE,geometry=False);T0,_=fk(pr,ASSEMBLY_POSE)
  if f:raise RuntimeError(f)
  def M(k,m,T):return T[mm[k]['body']] if k.startswith(('frame/','accessory/')) else m[mm[k].get('follows_part',k)]['transform']
  parts=[]
  for k,s in pp.items():
   d,assumption=density(mm[k]['sku']);rec=mesh_record(s);mass=d*rec['volume_mm3'];basis=assumption
   if mm[k]['sku'] in ('NITECORE_CARBON_6K','XIAO_ESP32S3','POLOLU_D24V22F3'):
    mass={'NITECORE_CARBON_6K':.088,'XIAO_ESP32S3':.004,'POLOLU_D24V22F3':.006}[mm[k]['sku']];basis='Nitecore published88g; XIAO4g/buck6g provisional allowance, not weighed'
   c=np.r_[rec['COM_mm'],1];local=np.linalg.inv(M(k,m0,T0))@c
   parts.append({'id':k,'body':mm[k]['body'],'module':mm[k]['module'],'owner':mm[k].get('owner'),'sku':mm[k]['sku'],'mass_kg':mass,'volume_mm3':rec['volume_mm3'],'density_kg_mm3':d,'basis':basis,'local_COM_mm':local[:3].tolist()})
  harness=next(r for r in read(OUT/'harness/cut_and_binding_plan.json')['characters'] if r['character']==char)
  for chain in harness['chains']:
   for seg in chain['segments']:
    mass=seg['cut_length_each_conductor_mm']/1000*(2*.00380+4*.00110)+.0012 # insulated copper + splice/strain-relief allowance
    for end,key in enumerate((seg['from_part'],seg['to_part'])):
     basekey='frame/chest' if key is None else key;pid='wire_mass/'+seg['segment']+'/'+str(end);mm[pid]={**mm[basekey]};mm[pid]['follows_part']=basekey
     if basekey.startswith('frame/'):mm[pid]['mass_body_frame']=True
     A=M(basekey,m0,T0);point=np.array(seg['assembly_endpoints_mm'][end]);local=np.linalg.inv(A)@np.r_[point,1]
     parts.append({'id':pid,'body':mm[basekey]['body'],'module':mm[basekey]['module'],'owner':mm[basekey].get('owner'),'sku':'WIRE_MASS_ALLOWANCE','mass_kg':mass/2,'local_COM_mm':local[:3].tolist(),'basis':'Cut-length wire model, split to endpoints. Actual loop COM differs.'})
  originalM=M
  def M(k,m,T):return T[mm[k]['body']] if mm[k].get('mass_body_frame') else originalM(k,m,T)
  # Common USB/internal-buck wires/coax/local 46 tails, insulation and removable ties.
  k='accessory/chest/wire_allowance';mm[k]={**mm['frame/chest']};parts.append({'id':k,'body':'chest','module':'frame/chest','owner':'rigid_frame','sku':'WIRE_AND_TIES_ALLOWANCE','mass_kg':.030,'local_COM_mm':[0,0,0],'basis':'30g common wiring+46local tap+soft tie allowance, not weighed'})
  total=sum(p['mass_kg'] for p in parts);samples=[];maxima={};module_parent={m['id']:m['parent'] for m in st}
  children={n['id']:set() for n in pr['nodes']}
  for n in pr['nodes']:
   if n['parent'] in children:children[n['parent']].add(n['id'])
  def subtree(root):
   found={root};todo=[root]
   while todo:
    for c in children.get(todo.pop(),set()):
     if c not in found:found.add(c);todo.append(c)
   return found
  for label,angles in declared_cases(char).items():
   _,meta,states,fail,profile=build(char,angles,geometry=False);T,_=fk(profile,angles);coms={p['id']:(M(p['id'],meta,T)@np.r_[p['local_COM_mm'],1])[:3] for p in parts};bodycom=sum(p['mass_kg']*coms[p['id']] for p in parts)/total;torques=[]
   for m in states:
    downstream=subtree(m['child'])
    for j,(origin,axis,owners) in enumerate(raw_axes(m)):
     subset=[p for p in parts if p['body'] in downstream or p['module']!=m['id'] and module_parent.get(p['module']) in downstream or p['module']==m['id'] and p['owner'] in owners]
     moment=sum((p['mass_kg']*(coms[p['id']]-origin) for p in subset),np.zeros(3))*.00980665;tau=float(-axis[0]*moment[1]+axis[1]*moment[0]);rid=m['id']+'/r'+str(j)
     item={'raw_axis':rid,'gravity_torque_Nm':tau,'supported_mass_kg':sum(p['mass_kg'] for p in subset),'axis_origin_mm':origin.tolist(),'axis_world':axis.tolist()};torques.append(item)
     if rid not in maxima or abs(tau)>abs(maxima[rid]['gravity_torque_Nm']):maxima[rid]={**item,'pose':label,'reference_self_hold_preference_Nm':abs(tau)*1.5+.02}
   samples.append({'pose':label,'COM_mm':bodycom.tolist(),'torques':torques,'mapping_failures':fail})
  rows.append({'character':char,'modeled_mass_kg':total,'parts':parts,'samples':samples,'worst_sample_per_raw_axis':list(maxima.values()),'manual_pelvis_support_force_N':total*9.80665,'mass_limit_gate':False,'unmodeled_mass_items':['actual wire loop/splice/strain-relief mass and COM use allowances','print supports removed; actual infill/voids/process differ from solid PETG proxy'],'physical_holding_torque_measured':False});print('MASS',char,total,'max gravity',max(abs(v['gravity_torque_Nm']) for v in maxima.values()),flush=True)
 save('load_budget.json',{'characters':rows,'gravity_m_s2':9.80665,'load_case':'pelvis rigidly supported by hand or fixture; no credited floor contacts; gravity only','mass_budget_is_not_weighed_mass':True,'dynamic_loads_or_drop_qualified':False,'FDM_strength_qualified':False,'input_sha256':{str(p):sha(p) for p in [Path(__file__),Path(__file__).with_name('layout_fullbody.py'),OUT/'harness/cut_and_binding_plan.json',*[OUT/f'harness/{c}_tails_final.json' for c in ('quinn','manny')],*[OUT/f'carriers_equipped/{c}_parts.npz' for c in ('quinn','manny')]]}})
if __name__=='__main__':main(sys.argv[1] if len(sys.argv)>1 else 'fitted')
