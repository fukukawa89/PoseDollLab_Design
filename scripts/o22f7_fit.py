"""Sampled whole-assembly and conservative continuous same-joint elbow checks."""
import json,shutil,itertools,sys,time,hashlib
import numpy as np
import o22f7 as r
h=r.h

def main():
 r.configure();import build_revo22_assembly as a
 scratch=r.WORK/'assembly';scratch.mkdir(parents=True,exist_ok=True)
 for name in ['sensor_fit.json','end_axis_fit.json','sensor_cassettes.npz','end_axis_parts.npz']:shutil.copy2(h.B/'mechanical'/name,scratch/name)
 a.D=scratch;a.b.D=scratch;parts,meta,base,*_=a.model();original=parts.copy()
 exports={x['id']:x for x in r.read(h.B/'print_batch/manifest.json')['rows']};audit=r.read(r.WORK/'whole_batch_audit.json');contexts=[]
 for pid in audit['affected_ids']:
  d=r.read(r.OUT/f'design/{pid}.json');n=np.load(r.OUT/f'parts/{pid}.npz');prefix='r1' if pid=='P095' else'f7';added=h.solid(n[prefix+'_added_body_v'],n[prefix+'_added_body_f']);before=r.solidfile(r.BASE/f'parts/{pid}.npz');bed=exports[pid]['bed']
  for ins in exports[pid]['instances']:
   key=ins['part'];A=np.array(meta[key]['transform']);A[:3,1]*=1 if np.linalg.det(A[:3,:3])>0 else -1
   T=h.H(d['orientation']['matrix'],d['orientation']['source_translation_mm'])@h.H(bed['rotation'],bed['translation_mm'])@np.linalg.inv(A);Ti=np.linalg.inv(T)
   align=(before^original[key].transform(T[:3])).volume()/before.volume();assert align>.97,(key,align)
   parts[key]=original[key]+added.transform(Ti[:3]);bb=np.array(added.bounding_box());worldcorners=np.array(list(itertools.product(*zip(bb[:3],bb[3:]))))@Ti[:3,:3].T+Ti[:3,3]
   contexts.append((pid,key,T,added,before,worldcorners,align))
 f0,o0=a.owners(base);profile=a.profile;inv_frames={k:np.linalg.inv(v)for k,v in f0.items()};inv_owners={k:np.linalg.inv(v)for k,v in o0.items()}
 keys=list(parts);bounds=np.array([list(itertools.product(*zip(s.bounding_box()[:3],s.bounding_box()[3:])))for s in parts.values()]);tokens=[];token_ix=[]
 for k in keys:
  m=meta[k];token=('f',m['body'])if m['owner']=='rigid_frame'else('o',m['module'],m['owner'])
  if token not in tokens:tokens.append(token)
  token_ix.append(tokens.index(token))
 all_reports=[]
 for pid,key,T,added,before,wcorners,align in contexts:
  out=r.WORK/'fit'/ (key.replace('/','__')+'.json')
  if out.exists():
   rep=r.read(out)
   if rep['npz_sha256']==h.sha(r.OUT/f'parts/{pid}.npz'):all_reports.append(rep);print('FIT_REUSED',key,flush=True);continue
  poses=[('base',base),('neutral',profile['neutral_raw_deg']),('default',r.read(h.B/'profiles/default_pose.json')['raw_deg'])]
  for rawkey,lim in profile['raw_limits_deg'].items():
   for label,val in zip(['min','max'],lim):
    pp=profile['neutral_raw_deg'].copy();pp[rawkey]=val;poses.append((rawkey+'/'+label,pp))
  local=next(j['raw_ids']for j in profile['joints']if j['id']==key.split('/')[0])
  for i,vals in enumerate(itertools.product(*[np.linspace(*profile['raw_limits_deg'][k],5)for k in local])):
   pp=profile['neutral_raw_deg'].copy();pp.update(dict(zip(local,vals)));poses.append(('local_grid_'+str(i),pp))
  rng=np.random.default_rng(20261016)
  for i in range(128):poses.append(('combined_'+str(i),{k:float(rng.uniform(*v))for k,v in profile['raw_limits_deg'].items()}))
  cache={};mins=[];flags=[];preexisting=[];rows=[];selfindex=keys.index(key);start=time.time()
  for ix,(name,raw)in enumerate(poses):
   f,o=a.owners(raw);mats=np.array([f[t[1]]@inv_frames[t[1]]if t[0]=='f'else o[t[1:]]@inv_owners[t[1:]]for t in tokens]);each=mats[token_ix];mine=each[selfindex];im=np.linalg.inv(mine);wc=wcorners@mine[:3,:3].T+mine[:3,3];lo=wc.min(0);hi=wc.max(0)
   v=np.einsum('nkj,nij->nki',bounds,each[:,:3,:3])+each[:,None,:3,3];sep=np.maximum(np.maximum(v.min(1)-hi,lo-v.max(1)),0);indices=np.flatnonzero(np.linalg.norm(sep,axis=1)<=.6);near=[]
   for ki in indices:
    k=keys[ki]
    if k==key:continue
    rel=im@each[ki];token=(k,tuple(np.round(rel,8).flat))
    if token not in cache:
     moved=parts[k].transform((T@rel)[:3]);overlap=max(0.,float((added^moved).volume()));gap=float(added.min_gap(moved,.6));old_overlap=max(0.,float((before^original[k].transform((T@rel)[:3])).volume()))if overlap>1e-6 or gap<.05 else 0
     cache[token]=dict(part=k,added_intersection_mm3=overlap,gap_capped_at_06_mm=gap,old_body_intersection_mm3=old_overlap)
    rec=dict(cache[token],pose=name);near.append(rec);mins.append(rec)
    if rec['added_intersection_mm3']>1e-6 or rec['gap_capped_at_06_mm']<.05:
     if rec['old_body_intersection_mm3']>.01:preexisting.append(rec)
     else:flags.append(rec)
   rows.append(dict(pose=name,nearby_checks=near))
   if ix%100==0:print('FIT',key,ix+1,'/',len(poses),'newflags',len(flags),flush=True)
  invalid={x['pose']for x in preexisting};excluded=[x for x in flags if x['pose']in invalid];flags=[x for x in flags if x['pose']not in invalid];valid=[x for x in mins if x['pose']not in invalid]
  rep=dict(id=pid,instance=key,npz_sha256=h.sha(r.OUT/f'parts/{pid}.npz'),body_sha256=hashlib.sha256(np.load(r.OUT/f'parts/{pid}.npz')['v'].tobytes()+np.load(r.OUT/f'parts/{pid}.npz')['f'].tobytes()).hexdigest(),source_alignment=align,pose_count=len(poses),valid_pose_count=len(poses)-len(invalid),excluded_poses=sorted(invalid),preexisting_collision_pairs=preexisting,new_contacts_in_infeasible_poses=excluded,new_interferences=flags,passed=not flags,minimum_clearance_mm=min([x['gap_capped_at_06_mm']for x in valid],default=.6),closest=sorted(valid,key=lambda x:x['gap_capped_at_06_mm'])[:20],unique_checks=len(cache),local_axes=local,local_grid_steps=5,global_random_count=128,elapsed_s=time.time()-start,pose_records=rows,scope='All modeled other parts including every revised elbow, hardware and electronics. 0.05 mm clearance threshold in sampled feasible poses. A pose with demonstrated pre-existing penetration >0.01 mm3 is excluded with evidence. Not continuous combined-motion or physical strength proof.')
  h.put(out,rep);all_reports.append(rep);print('FIT_DONE',key,rep['passed'],rep['minimum_clearance_mm'],'flags',len(flags),'seconds',round(rep['elapsed_s']),flush=True)
 h.put(r.WORK/'fit_summary.json',dict(passed=all(x['passed']for x in all_reports),instances=len(all_reports),total_pose_checks=sum(x['pose_count']for x in all_reports),rows=[{k:v for k,v in x.items()if k not in['pose_records','preexisting_collision_pairs','new_contacts_in_infeasible_poses']}for x in all_reports]))
if __name__=='__main__':main()
