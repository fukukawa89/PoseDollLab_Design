"""Freeze verified F5 types and pack all original instances into A1 mini plates."""
import sys,json,shutil,copy,random,hashlib,collections,numpy as np
from search_revo22_f5_orientation268 import R,B,O,OLD,put
from pack_revo22_a1mini import split_free
from verify_revo22_f5_geometry292 import run as geometry
S=O/'compact296';EDGE=4.;GAP=6.;LIMIT=178.
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def prepare():
 old=json.loads((OLD/'manifest.json').read_text());items=[i for p in old['plates']for i in p['items']];profiles={i['id']:i.get('source_profile',p['profile'])for p in old['plates']for i in p['items']};rows=json.loads((O/'inventory.json').read_text())['rows'];chosen={}
 for sub in ['parts','design','verification/types']:(S/sub).mkdir(parents=True,exist_ok=True)
 for row in rows:
  pid=row['id'];sf=O/'selections'/f'{pid}.json'
  if not row['has_fins'] and not sf.exists():
   q=O/'candidates'/pid/'unassisted_f4'
   for sub in ['parts','design','verification']:(q/sub).mkdir(parents=True,exist_ok=True)
   shutil.copy2(OLD/'parts'/f'{pid}.npz',q/'parts'/f'{pid}.npz');d=json.loads((OLD/'design'/f'{pid}.json').read_text());pr=profiles[pid];d.update(trial='unassisted_f4',f4_to_current_matrix=np.eye(3).tolist(),f4_to_current_translation_mm=[0,0,0],part_body_modified_from_F4=False,new_tooth_count=0,support_count=0,required_layer_height_mm=pr['layer'],required_initial_layer_height_mm=pr['initial'],required_wall_generator=pr['wall'],required_process_overrides=pr.get('overrides',{}),required_layer_ranges=pr.get('height_overrides',[]));put(q/'design'/f'{pid}.json',d);put(sf,dict(id=pid,label='unassisted_f4',native_pass=None,body_modified=False,support_volume_mm3=0,teeth=0,fins=0,whole_plate_native_audit_required=True))
  assert sf.exists(),(pid,'missing selection');sel=json.loads(sf.read_text());q=O/'candidates'/pid/sel['label'];npz=q/'parts'/f'{pid}.npz';g=geometry(pid);assert g['geometric_constraints_passed']and g['parts_npz_sha256']==sha(npz)
  if g['body_change_fit_and_pose_required']:
   f=json.loads((q/'verification/f5_fit_and_pose.json').read_text());assert f['fit_and_pose_geometry_passed']and f['parts_npz_sha256']==sha(npz),(pid,'body fit not passed')
  if row['has_fins']:
   native=json.loads((q/'verification/native_final.json').read_text());assert native['native_review_resolved'],pid
  for sub,ext in [('parts','npz'),('design','json')]:shutil.copy2(q/sub/f'{pid}.{ext}',S/sub/f'{pid}.{ext}')
  (S/'verification/types'/pid).mkdir(exist_ok=True)
  for name in ['f5_geometry.json','f5_fit_and_pose.json','native_final.json','construction.json','relief_geometry.json','f5_fin_groups.npz','guards.npz','strict_magnet_guards.npz']:
   if(q/'verification'/name).exists():shutil.copy2(q/'verification'/name,S/'verification/types'/pid/name)
  chosen[pid]=dict(sel,npz_sha256=sha(npz),geometric_proof=g)
 assert len(chosen)==150
 assert sha(S/'parts/X062.npz')=='4c83dc08a2fa297821dbfa4ec6f43e4a05763b8386736d3e919957c4e726c765'
 put(S/'frozen_selection.json',chosen);print('F5_FROZEN',len(chosen),flush=True)
 return old

def pack(items,seed):
 rng=random.Random(seed);mode=seed%6
 def order(i):
  w,h=i['size'][:2];v=[w*h,max(w,h)**2,min(w,h)**2,w*w,h*h,w+h][mode];return-v*(rng.uniform(.65,1.35)if seed>=6 else 1)
 plates=[]
 for it in sorted(items,key=lambda i:(i['source_profile']['layer'],order(i))):
  options=[0]if it['id']in ['X062','X038','X046','X054','P130','P035','W016','P117','P093','W017','P115','P049','P071','P130','X050']else[0,1];best=None
  for pi,p in enumerate(plates):
   src=it['source_profile'];same=src['layer']==p['layer'] and src['initial']==p['initial'];finer=p['layer']<src['layer'] and src['initial']==p['initial'] and it['id']in ['N004','X045','P013','P045','X081']
   if not(same or finer):continue
   for rot in options:
    iw,ih=(it['size'][1],it['size'][0])if rot else it['size'][:2];iw+=GAP;ih+=GAP
    for x,y,w,h in p['free']:
     if iw>w+1e-8 or ih>h+1e-8:continue
     sc=(pi,min(w-iw,h-ih),max(w-iw,h-ih),y,x,rot)if seed%3 else(pi,w*h-iw*ih,min(w-iw,h-ih),y,x,rot)
     if best is None or sc<best[0]:best=(sc,pi,x,y,rot,iw,ih)
  if best is None:
   rot=0;iw,ih=np.array(it['size'][:2])+GAP;assert max(iw,ih)<=LIMIT+1e-6,(it['id'],iw,ih);pi=len(plates);plates.append(dict(free=[(0.,0.,LIMIT,LIMIT)],items=[],layer=it['source_profile']['layer'],initial=it['source_profile']['initial']));best=((),pi,0.,0.,rot,iw,ih)
  _,pi,x,y,rot,iw,ih=best;p=plates[pi];p['free']=split_free(p['free'],(x,y,iw,ih));i=copy.deepcopy(it);Q=np.array([[0,-1,0],[1,0,0],[0,0,1.]])if rot else np.eye(3);lo=np.array(it['local_bounds_mm'][:3]);hi=np.array(it['local_bounds_mm'][3:]);corners=np.array([[a,b,c]for a in[lo[0],hi[0]]for b in[lo[1],hi[1]]for c in[lo[2],hi[2]]])@Q.T;delta=np.array([x+EDGE,y+EDGE,0.])-corners.min(0);b=np.r_[corners.min(0)+delta,corners.max(0)+delta];i.update(rotation_matrix=Q.tolist(),translation_mm=delta.tolist(),rotation_z_deg=90*rot,bounds_mm=b.tolist(),fins_bounds_mm=b.tolist(),w=iw-GAP,h=ih-GAP,x=x+EDGE,y=y+EDGE)
  if i['source_profile']['layer']!=p['layer']:
   i['single_part_validated_profile']=copy.deepcopy(i['source_profile']);i['source_profile']['layer']=p['layer'];i['finer_layer_for_compact_layout']=True
  p['items'].append(i)
 return plates

def search(items,n=1500):
 best=None
 for seed in range(n):
  ps=pack(items,seed);score=(len(ps),sum(bool(i.get('finer_layer_for_compact_layout'))for p in ps for i in p['items']),sum(len(p['items'])==1 for p in ps),-len(ps[-1]['items']))
  if best is None or score<best[0]:best=(score,ps,seed);print('F5_PACK_BEST',len(items),seed,score,flush=True)
 return best[1:]

def main():
 old=prepare();main=[];samples=[]
 for p in old['plates']:
  for i in p['items']:
   it=copy.deepcopy(i);pid=i['id'];n=np.load(S/'parts'/f'{pid}.npz');v=np.r_[n['v'],n['fin_v'],n['teeth_v']];assert v[:,2].min()>=-1e-6,(pid,'mesh below bed',v[:,2].min());d=json.loads((S/'design'/f'{pid}.json').read_text());profile=dict(layer=d.get('required_layer_height_mm',.2),initial=d.get('required_initial_layer_height_mm',.2),wall=d.get('required_wall_generator','arachne'),overrides=d.get('required_process_overrides',{}),height_overrides=d.get('required_layer_ranges',[]),fuse=True);it.update(optional_sample=bool(p['optional']),previous_f4_address=i['object_name'].split()[0],previous_f4_plate=p['id'],source_profile=profile,has_fins=bool(len(n['fin_f'])),local_bounds_mm=np.r_[v.min(0),v.max(0)].tolist(),size=np.ptp(v,axis=0).tolist());(samples if p['optional']else main).append(it)
 def grouped(items,attempts):
  pp,seed=search(items,attempts);return pp,dict(mixed=seed)
 ps,seed=grouped(main+samples,1500);qs=[];ss={};plates=[]
 for optional,group,prefix in[(False,ps,'D'),(True,qs,'Q')]:
  for j,p in enumerate(group,1):
   pid=f'{prefix}{j:02}'
   for k,it in enumerate(p['items'],1):it.update(number=k,object_name=f'{pid}-{k:02} '+it['id']+' '+it['part']+(' [可选小样]'if it['optional_sample']else''),native_internal_object_name=f'{pid}-{k:02} '+it['id']+' '+it['part']+(' [可选小样]'if it['optional_sample']else''))
   plates.append(dict(id=pid,title='O22-F5 稀疏支撑合盘'+('额外小样'if optional else'主套'),optional=optional,items=p['items'],profile=dict(layer=p['layer'],initial=p['initial'],wall='arachne',overrides={},fuse=True)))
 gaps=[];edges=[]
 for p in plates:
  for idx,i in enumerate(p['items']):
   b=np.array(i['bounds_mm']);assert min(b[:2])>=EDGE-1e-6 and max(b[3:5])<=180-EDGE+1e-6 and abs(b[2])<1e-6 and b[5]<180;edges.append(min(*b[:2],*(180-b[3:5])))
   for j in p['items'][idx+1:]:
    c=np.array(j['bounds_mm']);gap=float(np.linalg.norm(np.maximum(np.maximum(b[:2]-c[3:5],c[:2]-b[3:5]),0)));assert gap>=GAP-1e-6;gaps.append(gap)
 expected=collections.Counter((i['id'],i['original_object_name'],p['optional'])for p in old['plates']for i in p['items']);actual=collections.Counter((i['id'],i['original_object_name'],i['optional_sample'])for p in plates for i in p['items']);assert expected==actual and len(main)==186 and len(samples)==7;assert len(plates)<len(old['plates']),('No reduction',len(plates))
 out=dict(version='O22-F5-Compact',status='layout frozen; whole-plate native checks pending',source_release=str(OLD),main_instances=186,sample_instances=7,samples_embedded_in_main_plates=True,type_count=150,before_main_plates=14,after_main_plates=len(ps),before_optional_plates=1,after_optional_plates=len(qs),minimum_model_edge_margin_mm=float(min(edges)),minimum_combined_body_fin_teeth_bbox_gap_mm=float(min(gaps)),packing='Multi-start MaxRects; specified sensitive types keep their in-plane orientation. Small or unassisted objects may fill finer-layer plates, subject to fresh native whole-plate checks. Global optimum not claimed',bed_mm=[180,180,180],seed=seed,sample_seed=ss,plates=plates);put(S/'stage_manifest.json',out);print('F5_PACK_DONE',len(ps),len(qs),[(p['id'],len(p['items']))for p in plates],flush=True)
if __name__=='__main__':main()
