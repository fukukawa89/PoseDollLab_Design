"""Read-only publication of current O15 mesh instances for local visual review.
This page never claims a manufacturing or hardware test pass.
"""
from common import *
from layout_fullbody import *
from connected import carrier_inputs
from carriers import ASSEMBLY_POSE
PAGE=H/'tutorials/full-doll-o15'

def owner_frames(m):
 q=m['angles_deg'];kind=m['kind']
 if kind in ('tut','wide_tut'):return tut.frames(q)
 if kind=='three_axis':return three_axis.frames(q)
 if kind in ('core','ankle_core','clavicle_core'):
  a,b=q;return {'C02':np.eye(3),'ring':rot(1,-b),'C01':rot(1,-b)@rot(0,a)}
 return {'parent':np.eye(3),'child':rot(2,q[0])}

def main(char='quinn',variant='carriers_swept'):
 rr,frames,frame_hash=carrier_inputs(char,variant)
 if rr.get('status')!='ROUTING_GENERATED':raise RuntimeError('routing is still being generated')
 models={};meshes={};arrays=[];count=0;digests={}
 def model(key,s):
  nonlocal count
  display=s.simplify(.025);t=tri(display).astype(np.float32);digest=hashlib.sha256(t.tobytes()).hexdigest()
  if digest in digests:models[key]=digests[digest];return
  n=np.cross(t[:,1]-t[:,0],t[:,2]-t[:,0]);length=np.linalg.norm(n,axis=1);n/=np.maximum(length[:,None],1e-30);v=np.concatenate([t,np.repeat(n[:,None,:],3,axis=1)],axis=2).reshape(-1,6);alias=str(len(meshes));models[key]=alias;meshes[alias]={'first':count,'count':len(v)};count+=len(v);arrays.append(v);digests[digest]=alias
 libs=libraries()
 for kind,(p,owners,sku) in libs.items():
  if kind not in {m['kind'] for m in config(char)[1]}:continue
  for k,s in p.items():
   if kind=='hinge' and k=='lever_cup':s=s^box([-50,-50,-50],[14,50,50])
   model(kind+'/'+k,s)
 for body,s in frames.items():model('frame/'+body,s)
 replaced={k for r in rr['frames'] for k in r['replaces']};poses=read(H/'mechanical_manifest/revO_pose_cases.json')['cases'];wanted={'assembly':ASSEMBLY_POSE,**{k:poses[k] for k in ('neutral','arms_forward','arms_overhead','arms_side','sitting','crouch','trunk_bend_twist','palms_turn')}};labels={'assembly':'张臂装配参考','neutral':'中立站姿','arms_forward':'双臂前举','arms_overhead':'双臂上举','arms_side':'双臂侧举','sitting':'坐姿','crouch':'下蹲','trunk_bend_twist':'弯腰转身','palms_turn':'翻转手掌'};scenes=[]
 ref=read(G3/f'layouts/{char}/anatomy_profile.json');refT,refA=fk(ref,{})
 for name,ang in wanted.items():
  _,meta,states,fail,pr=build(char,ang,geometry=False);T,A=fk(pr,ang);TR,_=fk(ref,ang);objects=[]
  for m in states:
   fs=owner_frames(m);pp,owners,sku=libs[m['kind']]
   for k in pp:
    pid=m['id']+'/'+k
    if pid in replaced:continue
    B=meta[pid]['transform'];role='print' if sku[k] is None else 'sensor' if sku[k] in ('AS5048A_MINI_PCBA','PCBA_INCLUDED','MAGNET_D6_T2P5_DIAMETRIC') else 'metal';objects.append({'mesh':models[m['kind']+'/'+k],'matrix':B.flatten().tolist(),'label':pid,'role':role})
  for body in frames:objects.append({'mesh':models['frame/'+body],'matrix':T[body].flatten().tolist(),'label':'frame/'+body,'role':'frame'})
  bones=[]
  for n in ref['nodes']:
   if n['parent'] and n['parent']!='device_base':
    a,b=TR[n['parent']][:3,3],TR[n['id']][:3,3]
    if np.linalg.norm(a-b)>1:bones.append({'a':a.tolist(),'b':b.tolist()})
  scenes.append({'pose':name,'label':labels[name],'objects':objects,'reference_bones':bones,'caption':'拖动旋转 · 滚轮缩放 · 当前是完整实体布局的离散姿势，连接架和带线运动尚在检查。','mapping_failures':fail})
 _,_,st,_,_=build(char,{});deviations=[]
 for m in st:
  delta=np.array(m['origin_mm'])-refA[m['axis_ids'][0]]['origin'];deviations.append({'label':m['id'],'delta':delta.tolist(),'distance':float(np.linalg.norm(delta))})
 result={'character':char,'status':'工作中的整机数字候选：已建立全身关节与连接架。线束、末端握持外形及完整运动复核仍在推进，暂不用于下单打印。','coverage':['全身 41 个测量语义轴已有实体关节；3 个骨盆轴保持固定输出。','四角度机构共需 46 路原始测量。角度合成已做参考姿态与故障注入检查，未接入实际电子采集。','连接架使用离散运动包络寻路，仍需检查整机组合动作；显示实体不等于运动范围已经通过。','新设计均未新增实物测试。最终打印包、金属采购单与统一测试顺序仍在整理。'],'meshes':meshes,'scenes':scenes,'deviations':deviations,'frame_inputs_sha256':frame_hash,'render_mesh_simplification_mm':.025}
 PAGE.mkdir(parents=True,exist_ok=True);(PAGE/'geometry.bin').write_bytes(np.concatenate(arrays).astype('<f4').tobytes());(PAGE/'scene.json').write_text(json.dumps(result,ensure_ascii=False,separators=(',',':')),encoding='utf-8');save('viewer_publication.json',{'frame_inputs_sha256':frame_hash,'mesh_count':len(meshes),'triangles':count//3,'scenes':len(scenes),'geometry_bytes':(PAGE/'geometry.bin').stat().st_size,'status':'IN_PROGRESS_NOT_RELEASED'});print('PAGE',len(meshes),count//3,'triangles',(PAGE/'geometry.bin').stat().st_size,'bytes',flush=True)
if __name__=='__main__':main(sys.argv[1] if len(sys.argv)>1 else 'quinn',sys.argv[2] if len(sys.argv)>2 else 'carriers_swept')
