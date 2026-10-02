"""Publish the actual final fitted parts, never library placeholders, to WebGL."""
from common import *
from fitted import build_fitted
from layout_fullbody import build,fk,G3
from carriers_swept import ASSEMBLY_POSE
PAGE=H/'tutorials/full-doll-o15'

def group(k,m):
 if any(x in k for x in ('clavicle_l','upperarm_l','elbow_l','forearm_l','hand_l')):return 'arm_l'
 if any(x in k for x in ('clavicle_r','upperarm_r','elbow_r','forearm_r','hand_r')):return 'arm_r'
 if any(x in k for x in ('thigh_l','calf_l','foot_l','ball_l')):return 'leg_l'
 if any(x in k for x in ('thigh_r','calf_r','foot_r','ball_r')):return 'leg_r'
 if 'head' in k:return 'head'
 return 'torso'

def main(char):
 p,m,st,f,pr,prov=build_fitted(char);assert not f;index=read(OUT/'print_export_index.json');ids={i['part']:r['id'] for r in index['parts'] for i in r['instances'] if i['character']==char};models={};meshkeys={};arrays=[];objects=[];count=0
 for k,s in p.items():
  A=m[k]['transform'];I=np.linalg.inv(A);local=pose(s,I[:3,:3],I[:3,3]);tt=tri(local.simplify(.03)).astype('<f4');digest=hashlib.sha256(tt.tobytes()).hexdigest()
  if digest not in meshkeys:
   alias=str(len(models));meshkeys[digest]=alias;n=np.cross(tt[:,1]-tt[:,0],tt[:,2]-tt[:,0]);n/=np.maximum(np.linalg.norm(n,axis=1)[:,None],1e-30);v=np.concatenate([tt,np.repeat(n[:,None,:],3,axis=1)],axis=2).reshape(-1,6);models[alias]={'first':count,'count':len(v)};count+=len(v);arrays.append(v)
  sku=m[k]['sku'];role='frame' if k.startswith('frame/') else 'tail' if k.startswith('tail/') else 'print' if sku is None else 'sensor' if sku in ('AS5048A_MINI_PCBA','PCBA_INCLUDED','C1_PCBA_INCLUDED','C1_CENTRAL_PCBA','XIAO_ESP32S3') else 'equipment' if k.startswith('accessory/') and not sku.startswith(('NUT_','SCREW_')) else 'metal';bb=np.array(s.bounding_box());center=(bb[:3]+bb[3:])/2;outward=center-A[:3,3]
  if np.linalg.norm(outward)<1:outward=np.array([0,0,1.])
  outward=outward/np.linalg.norm(outward);objects.append({'mesh':meshkeys[digest],'label':k,'role':role,'group':group(k,m[k]),'print_id':ids.get(k),'sku':sku,'matrix':A.ravel().tolist(),'center':center.tolist(),'explode':(outward*35).tolist(),'follows_part':m[k].get('follows_part',k),'body':m[k]['body']})
 manifest=read(H/'mechanical_manifest/revO_pose_cases.json')['cases'];wanted={'assembly':ASSEMBLY_POSE,**{k:manifest[k] for k in ('neutral','arms_forward','arms_overhead','arms_side','sitting','crouch','trunk_bend_twist','palms_turn')}};labels={'assembly':'张臂装配参考','neutral':'中立站姿','arms_forward':'双臂前举','arms_overhead':'双臂上举','arms_side':'双臂侧举','sitting':'坐姿','crouch':'下蹲','trunk_bend_twist':'弯腰转身','palms_turn':'翻转手掌'};reference=read(G3/f'layouts/{char}/anatomy_profile.json');scenes=[]
 for name,angles in wanted.items():
  _,meta,states,fail,profile=build(char,angles,geometry=False);T,_=fk(profile,angles);Tr,_=fk(reference,angles);rows=[]
  for ob in objects:
   k=ob['label'];M=T[ob['body']] if k.startswith(('frame/','accessory/')) else meta[ob['follows_part']]['transform'];D=M@np.linalg.inv(np.array(ob['matrix']).reshape(4,4));rows.append({**ob,'matrix':M.ravel().tolist(),'center':(D@np.r_[ob['center'],1])[:3].tolist(),'explode':(D[:3,:3]@ob['explode']).tolist()})
  bones=[{'a':Tr[n['parent']][:3,3].tolist(),'b':Tr[n['id']][:3,3].tolist()} for n in reference['nodes'] if n['parent'] and n['parent']!='device_base' and n['parent'] in Tr]
  scenes.append({'pose':name,'label':labels[name],'objects':rows,'reference_bones':bones,'caption':'实体姿势预览。相邻结构已做离散检查；非相邻肢体仍可能接触，摆姿时避让。分解动画仅帮助认件，不代表装配路径。','mapping_failures':fail})
 ref=read(OUT/'reference_deviations.json');charref=next(r for r in ref['characters'] if r['character']==char);load=next(r for r in read(OUT/'load_budget.json')['characters'] if r['character']==char)
 d={'character':char,'status':'整机数字样机 · 已形成统一打印/采购/测试资料；机械强度、摩擦、带线手感和电子实测等待同一批样机验证。','meshes':models,'scenes':scenes,'reference_deviations':charref,'mass_budget_kg':load['modeled_mass_kg'],'print_index':index['parts'],'coverage':['41个测量语义轴 + 3个固定骨盆轴；46块原始角度采集板。','两种体型各689个设备/短尾线离散检查工况，未发现未解释的相邻实体干涉；不是连续运动证明。','C1中央板与传感板原生ERC/DRC均通过；BODY/G0固件编译及UE桥接仿真通过。','动态导线仍需在实物上整理服务环，验证不卡线、不拉扯、不影响姿态；页面不伪造柔性线缆仿真。','约'+str(round(load['modeled_mass_kg'],3))+' kg为预算，不是称重；允许手托，不设1.2 kg硬门槛。'],'render_mesh_simplification_mm':.03}
 PAGE.mkdir(parents=True,exist_ok=True);(PAGE/f'geometry_{char}.bin').write_bytes(np.concatenate(arrays).astype('<f4').tobytes());(PAGE/f'scene_{char}.json').write_text(json.dumps(d,ensure_ascii=False,separators=(',',':')),encoding='utf8');save(f'viewer_{char}.json',{'input_sources':{str(x):sha(x) for x in [Path(__file__),Path(__file__).with_name('fitted.py'),OUT/f'harness/{char}_tails_final.json',OUT/'load_budget.json']},'models':len(models),'triangles':count//3,'bytes':(PAGE/f'geometry_{char}.bin').stat().st_size});print('FINAL VIEWER',char,len(models),count//3,flush=True)
if __name__=='__main__':
 for char in sys.argv[1:] or ['quinn','manny']:main(char)
