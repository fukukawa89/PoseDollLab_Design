"""Select finite FFC folds against retained real geometry, then swept geometry."""
from common import *
from sensor_tails import pigtail,local_ports
from tail_fit import relieve_clip
from connected import build_connected,adjacent_pairs
from layout_fullbody import build,fk
from carriers_swept import ASSEMBLY_POSE,motion_bank
from raw_paths import paths

def main(char='quinn',mode='assembly'):
 pp,mm,st,f,pr,_=build_connected(char,ASSEMBLY_POSE,'carriers_refined');assert not f;_,m0,_,_,_=build(char,ASSEMBLY_POSE,geometry=False);T0,_=fk(pr,ASSEMBLY_POSE);ports=local_ports(char);adj=adjacent_pairs(char)
 def matrix(k,m,T):return T[mm[k]['body']] if k.startswith('frame/') else m[k]['transform']
 inv={k:np.linalg.inv(matrix(k,m0,T0)) for k in pp};bounds={}
 for k,s in pp.items():
  bb=np.array(s.bounding_box());bounds[k]=np.c_[list(itertools.product(*zip(bb[:3],bb[3:]))),np.ones(8)]
 bank=[('assembly',m0,T0)] if mode=='assembly' else motion_bank(char)+[(name,m,T) for name,m,T,d in paths(char)]
 baseline_path=OUT/f'harness/{char}_tails_motion.json';baseline=read(baseline_path);prior={r['sensor']:r for r in baseline['rows']};rows=[]
 for key,port in ports.items():
  if prior[key]['selected'] is not None:
   rows.append({**prior[key],'inherited_unmodified_tail':True});continue
  mod=port['module'];obstacles=[k for k in pp if mod in mm[k].get('modules',[mm[k]['module']]) or any(frozenset((mod,x)) in adj for x in mm[k].get('modules',[mm[k]['module']]))];selected=None;attempts=[]
  for orientation,length,radius in [(o,l,r) for o in (0,180) for l,r in [(15.,2.),(20.,3.),(20.,2.5),(20.,2.),(20.,3.5),(20.,4.)]]:
   ribbon,patch,end=pigtail(radius,length);F=port['basis']@rot(2,orientation);s=pose(ribbon+patch,F,port['board_top_center']);active=obstacles
   if orientation:
    prefix=key[:-len('sensor_PCB')];members=[k for k in pp if k.startswith(prefix) and mm[k]['sku'] in ('AS5048A_MINI_PCBA','PCBA_INCLUDED')];Q=F@port['basis'].T;B=np.eye(4);B[:3,:3]=Q;B[:3,3]=port['board_top_center']-Q@port['board_top_center'];I=np.linalg.inv(m0[key]['transform'])
    for k in members:
     M=B@I;s+=pose(pp[k],M[:3,:3],M[:3,3])
    active=[k for k in obstacles if k not in members]
   clipkey=key[:-len('sensor_PCB')]+'pcb_clip';custom={};relief=None
   if orientation and clipkey in pp:
    I=np.linalg.inv(m0[key]['transform']);clip=pose(pp[clipkey],I[:3,:3],I[:3,3]);cut,relief=relieve_clip(clip,F,port['board_top_center'],radius,length)
    P=m0[key]['transform'];custom[clipkey]=pose(cut,P[:3,:3],P[:3,3])
   bb=np.array(s.bounding_box());seen=set();fail=[]
   for label,m,T in bank:
    I=np.linalg.inv(m[key]['transform'])
    for k in active:
     M=I@matrix(k,m,T)@inv[k];stamp=(k,tuple(np.round(M,7).ravel()))
     if stamp in seen:continue
     seen.add(stamp);v=(bounds[k]@M.T)[:,:3]
     if np.any(np.minimum(bb[3:],v.max(0))<=np.maximum(bb[:3],v.min(0))+1e-8):continue
     overlap=float((s^pose(custom.get(k,pp[k]),M[:3,:3],M[:3,3])).volume())
     if overlap>1e-4:fail.append({'pose':label,'part':k,'overlap_mm3':overlap});break
    if fail:break
   attempts.append({'pcb_rotation_deg':orientation,'length_mm':length,'radius_mm':radius,'first_failure':fail})
   if not fail:selected={'clip_relief':relief,'pcb_rotation_deg':orientation,'length_mm':length,'radius_mm':radius,'end_local_mm':(F@end+port['board_top_center']).tolist(),'basis':F.tolist(),'board_top_center':port['board_top_center'].tolist()};break
  rows.append({'sensor':key,'selected':selected,'attempts':attempts});save('harness/'+char+'_tails_fitted_'+mode+'.json',{'status':'RUNNING','rows':rows});print('TAIL',char,mode,key,selected and (selected['length_mm'],selected['radius_mm']),flush=True)
 save('harness/'+char+'_tails_fitted_'+mode+'.json',{'status':'SAMPLED_TAILS_CLEAR' if all(r['selected'] for r in rows) else 'TAIL_COLLISIONS','rows':rows,'sample_count':len(bank),'source_sha256':{str(p):sha(p) for p in [Path(__file__),baseline_path,Path(__file__).with_name('sensor_tails.py'),Path(__file__).with_name('tail_fit.py'),OUT/f'carriers_refined/{char}_parts.npz',OUT/f'carriers_refined/{char}_routing.json']},'scope':'FFC formed once with >=3.5mm terminal straight allowance. Discrete geometry; no fatigue, supplier solder transition or moving wire qualification.'})
if __name__=='__main__':main(sys.argv[1] if len(sys.argv)>1 else 'quinn',sys.argv[2] if len(sys.argv)>2 else 'assembly')
