"""Route shallow, swept FFC clearance channels in printed frames; preserve witnesses."""
from common import *
from equipped import build_full
from sensor_tails import pigtail,local_ports
from tail_fit import guarded_tail
from connected import adjacent_pairs
from layout_fullbody import build,fk
from carriers_swept import ASSEMBLY_POSE,motion_bank
from raw_paths import paths

def main(char):
 pp,mm,st,f,pr,_=build_full(char);assert not f;ports=local_ports(char);adj=adjacent_pairs(char);inv={k:np.linalg.inv(m['transform']) for k,m in mm.items()};baseline=OUT/f'harness/{char}_tails_motion.json';data=read(baseline);failed=[r['sensor'] for r in data['rows'] if r['selected'] is None];bank=motion_bank(char)+[(n,m,T) for n,m,T,d in paths(char)];changed={};records=[];hard=[];corners={}
 for k,s in pp.items():
  bb=np.array(s.bounding_box());corners[k]=np.c_[list(itertools.product(*zip(bb[:3],bb[3:]))),np.ones(8)]
 def matrix(k,m,T):return T[mm[k]['body']] if k.startswith(('frame/','accessory/')) else m[k]['transform']
 for key in failed:
  port=ports[key];F=port['basis'];c=port['board_top_center'];ribbon,patch,end=pigtail(2,15);s=pose(ribbon+patch,F,c);guard=pose(guarded_tail(2,15,.3),F,c);bb=np.array(guard.bounding_box());mod=port['module'];obstacles=[k for k in pp if mod in mm[k].get('modules',[mm[k]['module']]) or any(frozenset((mod,x)) in adj for x in mm[k].get('modules',[mm[k]['module']]))];seen=set();ncut=0
  for label,m,T in bank:
   I=np.linalg.inv(m[key]['transform'])
   for k in obstacles:
    M=I@matrix(k,m,T)@inv[k];stamp=(k,tuple(np.round(M,7).ravel()))
    if stamp in seen:continue
    seen.add(stamp);v=(corners[k]@M.T)[:,:3]
    if np.any(np.minimum(bb[3:],v.max(0))<=np.maximum(bb[:3],v.min(0))+1e-8):continue
    obs=pose(pp[k],M[:3,:3],M[:3,3]);overlap=float((s^obs).volume());guardhit=float((guard^obs).volume())
    if guardhit<1e-4:continue
    if k.startswith('frame/'):
     B=np.linalg.inv(M);cut=pose(guard,B[:3,:3],B[:3,3]);before=changed.get(k,pp[k]);after=before-cut;removed=before.volume()-after.volume()
     if removed>1e-6:changed[k]=after;records.append({'sensor':key,'frame':k,'pose':label,'actual_overlap_mm3':overlap,'clearance_removed_mm3':removed});ncut+=1
    elif overlap>1e-4:hard.append({'sensor':key,'part':k,'pose':label,'overlap_mm3':overlap})
  for row in data['rows']:
   if row['sensor']==key:row['selected']={'pcb_rotation_deg':0,'length_mm':15.,'radius_mm':2.,'basis':F.tolist(),'board_top_center':c.tolist(),'end_local_mm':(F@end+c).tolist(),'printed_frame_clearance':True}
  print('ROUTE TAIL',char,key,'cuts',ncut,'hard',len(hard),flush=True)
 reports=[];dest={}
 for k,s in changed.items():
  frac=(pp[k].volume()-s.volume())/pp[k].volume();components=solid_count(s);reports.append({'frame':k,'removed_mm3':pp[k].volume()-s.volume(),'removed_fraction':frac,'components':components,'strength_tested':False})
  if components!=1 or frac>.015:hard.append({'frame':k,'cause':'EXCESSIVE_REMOVAL_OR_DISCONNECT','fraction':frac,'components':components})
  I=inv[k];dest[k]=tri(pose(s,I[:3,:3],I[:3,3]))
 path=OUT/f'harness/{char}_frame_reliefs.npz';np.savez_compressed(path,**dest);inputs={str(p):sha(p) for p in [Path(__file__),baseline,Path(__file__).with_name('sensor_tails.py'),Path(__file__).with_name('tail_fit.py'),OUT/f'carriers_equipped/{char}_parts.npz',OUT/f'carriers_equipped/{char}_routing.json',path]}
 save(f'harness/{char}_frame_reliefs.json',{'status':'CLEARANCE_CHANNELS_CREATED' if not hard else 'FAILED','frames':reports,'witnesses':records,'hard_findings':hard,'sample_count':len(bank),'input_sha256':inputs,'scope':'Only printed material removed. Connected shell and bounded volume are geometric checks, not strength or wall-thickness qualification.'})
 data.update(status='SAMPLED_TAILS_CLEAR' if not hard else 'TAIL_COLLISIONS',source_sha256=inputs,frame_relief_report=str(OUT/f'harness/{char}_frame_reliefs.json'),scope='Original clear tails inherited unchanged. Failed tails retain orientation and gain shallow channels in printed frames. Complete-tail audit still required.');save(f'harness/{char}_tails_final.json',data);print('TAIL ROUTING',char,reports,'HARD',hard,flush=True)
if __name__=='__main__':main(sys.argv[1] if len(sys.argv)>1 else 'quinn')
