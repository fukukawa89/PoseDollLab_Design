"""O22 actual CAD preview. Render simplification never enters manufacturing files."""
import json,copy,hashlib,shutil,numpy as np
import build_revo22_assembly as a
b=a.b;g=a.g;B=a.B;H=a.H;PAGE=H/'tutorials/full-doll-o22';PAGE.mkdir(exist_ok=True)
p,m,base,changed,services,C=a.model();ids=g.read(a.D/'print_ids.json');w=g.read(B/'harness/routing_plan.json');arrays={};meshes={};mids={};centers={};scenes=[]
def mesh(key,s):
 tt=g.tri(s.simplify(.012)).astype(np.float32);nn=np.cross(tt[:,1]-tt[:,0],tt[:,2]-tt[:,0]);nn/=np.maximum(np.linalg.norm(nn,axis=1)[:,None],1e-30);arr=np.concatenate([tt,np.repeat(nn[:,None,:],3,axis=1)],axis=2).reshape(-1,6);stamp=hashlib.sha256(arr.tobytes()).hexdigest()[:18]
 arrays.setdefault(stamp,arr);mids[key]=stamp;centers[key]=np.mean(np.array(s.bounding_box()).reshape(2,3),axis=0)
for i,(k,s) in enumerate(p.items()):
 mesh(k,g.move(s,np.linalg.inv(np.array(m[k]['transform']))))
 if i%300==0:print('RENDER MESH',i,flush=True)
def group(k):
 if any(x in k for x in ['thigh_l','calf_l','foot_l','ball_l']):return 'leg_l'
 if any(x in k for x in ['thigh_r','calf_r','foot_r','ball_r']):return 'leg_r'
 if any(x in k for x in ['clavicle_l','upperarm_l','elbow_l','forearm_l','hand_l']):return 'arm_l'
 if any(x in k for x in ['clavicle_r','upperarm_r','elbow_r','forearm_r','hand_r']):return 'arm_r'
 return 'head' if 'head' in k else 'torso'
for name,label in [('a_stand','A 站姿 · 默认'),('left_elbow','左肘弯曲'),('asymmetric','非对称摆姿'),('right_forearm','右前臂扭转')]:
 q=g.read(B/'ue'/f'{name}.payload.json')['joint_angles_deg'];posed,mat,f=a.pose_parts(p,m,base,q);objects=[]
 for k in p:
  M=mat[k];center=(M@np.r_[centers[k],1])[:3];sku=m[k].get('sku');role='frame' if k.startswith('frame/') else 'print' if not sku else 'sensor' if 'sensor_PCB/' in k else 'equipment' if k.startswith('o22/') and not 'screw' in k else 'metal'
  body=m[k]['body'];root=f.get(body,f.get(body.split('/')[0],f['chest']));explode=center-root[:3,3];ln=np.linalg.norm(explode);explode=explode*25/max(ln,1)
  objects.append({'mesh':mids[k],'label':k,'role':role,'group':group(k),'print_id':ids.get(k),'sku':sku,'matrix':M.ravel().tolist(),'center':center.tolist(),'explode':explode.tolist(),'body':m[k]['body']})
 bones=[{'a':f[j['parent']][:3,3].tolist(),'b':f[j['child']][:3,3].tolist(),'group':group(j['id'])} for j in a.profile['joints']]
 lines=[]
 if name=='a_stand':
  for r in w['rows']:
   points=r['A_centerline_mm']
   lines += [{'a':x,'b':y,'group':group(r['raw_id'])} for x,y in zip(points,points[1:])]
 scenes.append({'pose':name,'label':label,'objects':objects,'reference_bones':[],'physical_bones':bones,'harness_lines':lines,'caption':'O22 实际 CAD；铜板、芯片与插头为最大安装包络。橙线为实体关节链。绿色线仅为待首件验证的线束路径，折点须弯成 ≥7mm 半径，不能按直折角装配。'})
# Backboard detail with lid hidden, same actual assembly transform.
sc=copy.deepcopy(scenes[0]);sc.update(pose='detail_carrier',label='中央板与背盒 · 去盖',objects=[o for o in sc['objects'] if (o['label'].startswith('o22/') and o['label']!='o22/controller_lid') or o['label']=='frame/chest'],view_center=(C@np.array([40,47,12,1]))[:3].tolist(),view_radius=80,view_yaw=np.pi/2,view_pitch=-np.pi/2,caption='80×94×1.6mm 四层载板，46个 SH5P 插座；86×100×27mm 背盒。四颗 M2×6 塑料自攻螺钉固定载板；盒盖用两条扎带固定。USB 和线束从相对侧出口进入。',physical_bones=[],harness_lines=[]);scenes.append(sc)
# Mounted sensor true cross-section; use the real elbow service coordinate system.
key='elbow_l.flex/sensor_cassette';A=services['elbow_l.flex/sensor_PCB'][0];section=[];cut=b.b.box([-100,-100,-100],[0,100,100]);shapes={'holder':g.move(p[key],np.linalg.inv(A))}
shapes.update(b.electronics());shapes['magnet']=b.b.cyl(3,10.4,12.9)
for name,s in shapes.items():
 s=s^cut
 if s.volume()<1e-7:continue
 mid='section/'+name;mesh(mid,s);section.append({'mesh':mids[mid],'label':mid,'role':'print' if name=='holder' else 'equipment','group':'all','print_id':None,'sku':None,'matrix':np.eye(4).ravel().tolist(),'center':centers[mid].tolist(),'explode':[0,0,0],'body':'detail','color':[.3,.48,.65] if name=='holder' else [.85,.58,.21] if name=='magnet' else [.28,.5,.3]})
scenes.append({'pose':'detail_sensor','label':'SOP8 磁铁安装剖面','objects':section,'reference_bones':[],'physical_bones':[],'harness_lines':[],'view_center':[-3,-3,15],'view_radius':23,'view_yaw':-np.pi/2,'view_pitch':-np.pi/2,'caption':'实际托架与最大封装包络的剖面。元件面高度15.95mm；磁铁顶12.9mm；安装后封装高度1.50–1.85mm；座面与磁铁各±0.10mm时外壳间隙1.00–1.75mm。磁场强度和角度误差仍须实测。'})
# Complete representative limb, including all ten channels.
sc=copy.deepcopy(scenes[0]);sc.update(pose='detail_left_arm',label='完整左臂 · 10路布线',objects=[o for o in sc['objects'] if o['group']=='arm_l' or o['label'].startswith('o22/J')],harness_lines=[x for x in sc['harness_lines'] if x['group']=='arm_l'],physical_bones=[x for x in sc['physical_bones'] if x['group']=='arm_l'],view_center=[-30,82,330],view_radius=155,view_yaw=-1.05,view_pitch=-1.32,caption='2路锁骨＋4路肩＋肘/前臂/腕屈伸/腕侧摆，共10根五线束独立回中央板。扎带只固定在各自骨段；运动交界留U形余量。此图是安装路径模板，尚未证明运动中无夹线。');scenes.append(sc)

for sc in scenes:
 for o in sc['objects']:
  k=o['label']
  if k=='o22/carrier_pcb':o['color']=[.23,.47,.31]
  elif k.startswith('o22/J'):o['color']=[.88,.9,.84]
  elif k.startswith('o22/U'):o['color']=[.15,.17,.19]
  elif k=='o22/xiao':o['color']=[.18,.32,.43]
  elif k=='o22/xiao_usb':o['color']=[.7,.72,.74]
blocks=[];offset=0
for mid,arr in arrays.items():meshes[mid]={'first':offset,'count':len(arr)};offset+=len(arr);blocks.append(arr)
data={'character':'universal','status':'O22 数字验证版 · 实物与报价待验证','meshes':meshes,'scenes':scenes,'coverage':['一套 USB 人偶，46路实际轴、25个关节模块、41个语义自由度。','完整可打印文件186件：185件在人偶上，1件装配治具。O11已验证摩擦结构不变。','两个人物 P21R 数据→可编辑关键帧→保存→新进程重新打开验证通过；输入是明确标注的合成测试数据。','1500元为目标；当前分项预算1482.50元，正式供应商报价为0份。','相邻机构的旧有极限姿势碰撞仍列在校核报告中；没有连续全范围无碰撞证明。','首件必须补齐新传感板、完整左臂线束、16路长支路及46路整机实测。'],'render_mesh_simplification_mm':.012}
json.dumps(data,allow_nan=False);b.put(PAGE/'scene_universal.json',data);(PAGE/'geometry_universal.bin').write_bytes(np.concatenate(blocks).astype('<f4').tobytes())
app=(H/'tutorials/full-doll-o20/app.js').read_text(encoding='utf-8').replace('revO20','revO22').replace('O20','O22').replace("fetch('../../bench/revO22/harness/cut_and_binding_plan.json')","fetch('../../bench/revO22/harness/routing_plan.json')")
app=app.replace("['physical',scene.physical_bones||[],[.91,.35,.05]]", "['physical',scene.physical_bones||[],[.91,.35,.05]],['wires',scene.harness_lines||[],[.15,.58,.36]]")
app=app.replace("'electronics','reference','physical']","'electronics','reference','physical','wires']")
start=app.index("$('#chains').replaceChildren");end=app.index("$('#group').disabled=false;partOptions();",start)
app=app[:start]+"$('#chains').replaceChildren(...wiring.rows.map(r=>{const d=document.createElement('div');d.className='chain';d.textContent=r.connector+' · '+r.raw_id+' · '+r.proposed_cut_each_wire_mm+' mm ×5芯（首件后定长）';return d}));"+app[end:]
app=app.replace('PoseDoll_O22_Universal_Design.zip','PoseDoll_O22_Engineering_Package.zip').replace('下载 O22 单人偶设计包','下载 O22 工程设计包')
(PAGE/'app.js').write_text(app,encoding='utf-8');shutil.copy2(H/'tutorials/full-doll-o20/style.css',PAGE/'style.css')
print('VIEWER',len(scenes),'SCENES',len(meshes),'MESHES',offset,'VERTICES',flush=True)
