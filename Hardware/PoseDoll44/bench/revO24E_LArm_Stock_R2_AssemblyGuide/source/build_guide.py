"""Standalone R2 assembly animation, derived from immutable production meshes."""
from pathlib import Path
import sys
sys.dont_write_bytecode=True
HERE=Path(__file__).resolve().parent;H=HERE.parents[1]
sys.path.insert(0,str(H/'cad/revO24E_LArm_Stock_R2'))
from build_stock import *
import base64,shutil,re
HERE=Path(__file__).resolve().parent
SOURCE=H/'bench/revO24E_LArm_Stock_R2';DEST=H/'bench/revO24E_LArm_Stock_R2_AssemblyGuide'
EXPECTED='9bf25e08e41c3faf6107d6e558f7b25f61aa82ec839a56e2c8c25f8fdcbc965e'
load=lambda p:json.loads(p.read_text('utf8'))
def point(M,p):return (np.array(M)@np.r_[p,1])[:3]
def unit(v):v=np.asarray(v,float);return v/np.linalg.norm(v)

def build():
 assert sha(SOURCE/'production_meshes.npz')==EXPECTED
 DEST.mkdir(exist_ok=True);(DEST/'verification').mkdir(exist_ok=True);(DEST/'source').mkdir(exist_ok=True)
 kit=load(SOURCE/'kit.json');parts=load(SOURCE/'production_assembly.json')['parts'];z=np.load(SOURCE/'production_meshes.npz');old=load(SOURCE/'tutorial/steps.json');ints=load(SOURCE/'interfaces.json');P={p['part_number']:p for p in parts};N={p['name']:p['part_number'] for p in parts};K={p['part_number']:p for p in kit['structural_parts']+kit['hardware']}
 rolls={r['id']:r for r in ints['rolls']};hinges={r['id']:r for r in ints['hinges']};W={x:np.array(r['W']) for x,r in rolls.items()};M={x:np.array(r['M']) for x,r in hinges.items()};M['W']=F0['l_wrist_flex'];zero=frames({});worldV={}
 original_hw={r['part_number']:r['feature'] for r in load(SRC/'kit.json')['hardware']}
 for p in parts:
  vv=z[str(p['i'])+'v'];worldV[p['part_number']]=vv@zero[p['frame']][:3,:3].T+zero[p['frame']][:3,3]
 def centre(pn):return np.mean([worldV[pn].min(0),worldV[pn].max(0)],axis=0)
 def partmarker(label,pos):return dict(label=label,point=np.asarray(pos).tolist())
 def arrow(label,vector):return dict(label=label,direction=unit(vector).tolist())
 definitions={
 'RP_keeper':('压盖贴座的平面朝固定座；环唇对准大平垫外缘，两个六角锁母口朝操作侧。',[("贴座面",point(W['RP'],[0,0,0])),("锁母装入口",point(W['RP'],[16,0,-6]))]),
 'RU_keeper':('压盖贴座的平面朝固定座；环唇对准大平垫外缘，两个六角锁母口朝操作侧。',[("贴座面",point(W['RU'],[0,0,0])),("锁母装入口",point(W['RU'],[16,0,-6]))]),
 'RF_keeper':('前臂压盖使用宽孔距版本；贴座面朝固定座，六角锁母口朝操作侧。',[("贴座面",point(W['RF'],[0,0,0])),("宽孔距锁母口",point(W['RF'],[20,0,-6]))]),
 'ROOT':('大平垫圆座与中心六角窝朝操作侧；实心握持块用于固定，不要夹持压盖环唇。',[("握持块",[0,-4,0]),("RP固定座入口",point(W['RP'],[0,0,0]))]),
 'SHOULDER_PITCH':('圆盘转子耳朝RP固定座；横向双孔端是肩外展固定端。侧窗保持可达。',[("RP转子耳",point(W['RP'],[0,0,-2])),("肩外展固定端",point(M['HS'],[0,0,0]))]),
 'SHOULDER_ABDUCT':('U形叉口朝肩外展固定端；另一端带压盖的RU座朝上臂骨杆。',[("肩外展叉口",point(M['HS'],[0,0,0])),("RU固定座",point(W['RU'],[0,0,0]))]),
 'UPPER_ARM':('圆盘耳端朝肩侧的RU座；连续横桥端朝肘。侧窗用来侧向装入垫片与碟簧。',[("肩端：RU转子耳",point(W['RU'],[0,0,-2])),("肘端：横桥",point(M['HE'],[0,0,0]))]),
 'ELBOW_OUTPUT':('U形叉口朝肘固定端；宽压盖的RF座朝前臂。保持宽压盖两颗螺钉可操作。',[("肘叉口",point(M['HE'],[0,0,0])),("RF固定座",point(W['RF'],[0,0,0]))]),
 'FOREARM':('圆盘耳端朝RF固定座；双叉耳端朝腕中心件。腕根圆弧避空不得当作承压台阶。',[("肘端：RF转子耳",point(W['RF'],[0,0,-2])),("腕叉口",point(M['W'],[0,0,0]))]),
 'KEEP_E-P017':('方键入口朝腕输出叉；指端朝远离手腕的一端。负X为锁母侧，正X为螺钉头及两片垫片侧。',[("方键入口",point(F0['l_wrist_deviation'],[0,0,-22])),("两片垫片／螺钉头侧",point(F0['l_wrist_deviation'],[7,0,-27])),("锁母侧",point(F0['l_wrist_deviation'],[-9,0,-27]))]),
 'KEEP_E-P018':('双叉耳开口朝腕中心件；方键端朝手掌。侧面磁铁座保留，本轮不装电子件。',[("腕中心叉口",point(M['W'],[0,0,0])),("手掌方键",point(F0['l_wrist_deviation'],[0,0,-27]))]),
 'KEEP_E-P019':('先在台面上完成四侧内层五金。Y轴两侧对应前臂叉，X轴两侧对应腕输出叉；不要提前合叉。',[("Y轴：前臂叉",point(M['W'],[0,9,0])),("X轴：输出叉",point(M['W'],[9,0,0])),("朝肘 +Z",point(M['W'],[0,0,7]))]),
 }
 orientation={};spring_groups={}
 for p in parts:
  pn=p['part_number'];name=p['name'];c=centre(pn);spec=K[pn]['spec'];role='打印件' if p['role']=='structure' else '五金';mark=[];ar=[];note='';sku=p['sku']
  if role=='打印件':
   note,landmarks=definitions[name];mark=[partmarker(t,x) for t,x in landmarks]
  else:
   if name.startswith(('RP_','RU_','RF_')):
    pre=name[:2];out=-W[pre][:3,2];suffix=name[len(pre)+1:];joint=pre
    if '_lid_' in name:out=W[pre][:3,2] if sku!='NL3' else -W[pre][:3,2]
   elif name.startswith(('HS_','HE_')):
    pre=name[:2];side=-1 if '_HL_' in name else 1;out=M[pre][:3,1]*side;suffix=name.split('_')[-1];joint=pre+('_HL' if side==-1 else '_HR')
   else:
    f=original_hw[name.removeprefix('KEEP_')];suffix=f.split('_')[-1]
    if f.startswith('l_E_W'):
     channel=f.split('_')[2];side=-1 if channel.endswith('M') else 1;axis=0 if 'WX' in channel else 1;out=M['W'][:3,axis]*side;joint=channel
    else:out=F0['l_wrist_deviation'][:3,0]*( -1 if sku=='NL2' else 1);joint='PALM'
   out=unit(out)
   if sku in ['AX4','M3x16','M2x20']:
    note='螺纹尖端先进入，螺钉头留在外侧。'+('光杆Φ4×8进入转动孔；M3×6螺纹端穿入锁母；用3 mm内六角。' if sku=='AX4' else '整根使用，不切短；用2.5 mm内六角，锁紧压盖。' if sku=='M3x16' else '从正X侧穿入；两片W2都在头下；用1.5 mm内六角。')
    ar=[arrow('螺纹端先入',-out),arrow('螺钉头朝外',out)]
   elif sku in ['NL3','NL2']:
    nylon=out if '_lid_nut_' in name or sku=='NL2' else -out
    note=('尼龙端朝外，金属端贴承压台阶；先把六角外形对齐锁母窝。' if '_lid_nut_' in name or sku=='NL2' else '尼龙端先进入深处，金属端朝入口；后续反力垫贴金属端。')+' 普通螺母不能替代尼龙锁母。'
    ar=[arrow('尼龙端',nylon),arrow('金属端',-nylon)]
   elif sku=='A8':
    v=worldV[pn]-c;ax=v@out;rad=np.linalg.norm(v-ax[:,None]*out,axis=1);inner=ax[rad<2.3].mean();outer=ax[rad>3.8].mean();assert abs(inner-outer)>.04,(name,inner,outer);peak=out*np.sign(inner-outer)
    note='看内孔凸缘的高边朝向，按放大图放置；两组内孔凸缘相对。'+('同一组的两片同向套叠，组与组反向；RP共4片。' if name.startswith('RP_') else '本位置两片反向，不要同向套叠。')+' 动画使用装后名义高度；先轻贴合，再调预紧，不压平。'
    ar=[arrow('内孔凸缘高边',peak),arrow('外圆低边方向',-peak)];spring_groups.setdefault(joint,[]).append(dict(pn=pn,feature=name,direction=peak.tolist()))
   elif sku=='FW4':
    face=out if suffix=='F1' else -out;note='12×4.3×1 mm摩擦平垫；选平整光滑的一面贴打印转子耳。图中箭头标的是贴耳方向；孔与肩钉同轴。';ar=[arrow('这一面贴打印耳',face),arrow('垫片孔轴线',-face)]
   elif sku=='W6L':
    note='18×6.4×1.5 mm大平垫，两面等效；外圆放进浅圆座，之后由压盖捕获。不可省略或用1.6 mm厚度替代。';ar=[arrow('放入固定浅座',-out),arrow('压盖所在侧',out)]
   else:
    note=('7×3.2×0.5薄W3，两面等效；不要换成O22的9×3.2×0.8。' if sku=='W3' else '9×4.3×0.8 W4，两面等效；注意这是4.3 mm孔。' if sku=='W4' else '5×2.2×0.5 W2，两面等效；两片都在掌部螺钉头下。')+' 平面垂直于孔轴，按箭头方向送入。';ar=[arrow('孔轴／朝装入侧',-out),arrow('外侧',out)]
  orientation[pn]=dict(part_number=pn,label=K[pn].get('kit_label') or f'{sku} · {name}',feature=name,kind=role,sku=sku,spec=spec,orientation=note,markers=mark,arrows=ar,centre=c.tolist(),spring_group=joint if sku=='A8' else None,outward_axis=out.tolist() if sku=='A8' else None)
 # Assembly semantics: individual modules on the bench, then join without reopening R.
 allsteps=[];chapters=[];complete={};global_seen=set();last_joint='RP'
 for om in old['modules']:
  mid=om['id'];r=rolls.get(mid);oldsteps=om['steps'];chapter=dict(id=mid,label=om['label'],step_indices=[]);chapters.append(chapter)
  if mid in rolls:installed=set()
  elif mid=='HS':installed=set(complete['RP'])
  elif mid=='HE':installed=set(complete['HS'])
  else:installed=set(complete['HE'])
  offsets={};hold_print={'RP':'ROOT','RU':'SHOULDER_ABDUCT','RF':'ELBOW_OUTPUT','HS':'SHOULDER_PITCH','HE':'UPPER_ARM','W':'FOREARM'}[mid];jointM=W.get(mid,M.get(mid));fixed_key=N[hold_print]
  def add(ids,title,note,path=None,base=None,kind='insert',primary=None,source_step=None):
   nonlocal installed,offsets
   ids=list(ids);path=path or [[0.,0.,0.]];base=np.asarray(base if base is not None else [0,0,0],float);before=sorted(installed);moves=bool(len(path)>1 and np.linalg.norm(np.array(path[0])-np.array(path[-1]))>1e-6)
   target=fixed_key
   if mid=='W' and (title.startswith('腕中心') or title=='准备腕中心件（台面）'):target=N['KEEP_E-P019']
   current_print=[x for x in ids if P[x]['role']=='structure'];current_metal=[x for x in ids if P[x]['role']!='structure']
   primary=primary or (current_print[0] if current_print else ids[0]);fresh=[x for x in ids if x not in global_seen];global_seen.update(ids);installed.update(ids)
   end_offsets=dict(offsets)
   for x in ids:
    if np.linalg.norm(base)>.001:end_offsets[x]=base.tolist()
    else:end_offsets.pop(x,None)
   row=dict(index=len(allsteps),number=len(allsteps)+1,chapter=mid,chapter_step=len(chapter['step_indices'])+1,title=title,note=note,kind=kind,parts=ids,new_parts=fresh,printed_parts=current_print,metal_parts=current_metal,primary=primary,target=target,visible=sorted(installed),before=before,base_offset=base.tolist(),offsets=end_offsets,path=path,animated=moves,frame_matrix=jointM.tolist(),source_step=source_step,printed_direction=orientation[target]['orientation'],metal_direction='逐件点击当前五金，放大图会显示尼龙端、螺纹端或碟簧凸缘；平垫明确标为两面等效。' if current_metal else '本步不新增五金；已有五金保持在已组装总成内。',expect='到位后核对本步方向与操作说明，再进入下一步。')
   offsets=end_offsets;allsteps.append(row);chapter['step_indices'].append(row['index']);return row
  for sn,s in enumerate(oldsteps,1):
   ids=s['part_numbers'];name=s['feature'];note=s['note'].replace('尖端名义露出3.5 mm','尖端名义露出2.5 mm');v=np.asarray(s['entry_world_A'],float);travel=float(s['animation_travel_mm']);path=s['animation_waypoints_world_A'] or [(v*travel).tolist(),[0,0,0]];base=[0,0,0]
   if mid in rolls and s['title'].startswith('准备压盖'):
    lid=N[r['keeper']];nuts=[N[mid+f'_lid_nut_{x}'] for x in [-r['lug_x_mm'],r['lug_x_mm']]];bench=-W[mid][:3,2]*24
    add([lid],'取防脱压盖，先在台面放好','压盖暂不合到固定座。平贴面朝固定座，六角装入口朝操作侧；下一步先装两颗锁母。',base=bench,kind='prepare',source_step=sn)
    for j,n in enumerate(nuts):
     row=add([n],f'压盖锁母 {j+1} / 2：先对六角','托住独立压盖，把NL3从六角口装入。尼龙朝操作侧，金属端朝压盖内的承压台阶；不要反装。',path=[(-W[mid][:3,2]*25).tolist(),[0,0,0]],base=bench,source_step=sn);row['target']=lid;row['printed_direction']=orientation[lid]['orientation']
    add([lid]+nuts,'将带锁母的压盖合到固定座','两颗锁母留在压盖里。整组沿箭头移到固定座，环唇捕获18 mm大平垫；保持贴合，下一步装头下平垫与M3×16。',path=[bench.tolist(),[0,0,0]],source_step=sn)
    continue
   if mid=='W' and sn==2:
    add(ids,'准备腕中心件（台面）','腕中心件先放在前臂叉外。按Y−、Y+、X−、X+逐侧装齐内五金，再将整个中心件放入前臂叉。',base=-M['W'][:3,2]*50,kind='prepare',source_step=sn);continue
   if mid=='W' and 3<=sn<=22:base=-M['W'][:3,2]*50
   if mid in ['HS','HE'] and len(ids)>3 and travel>0:path=[(-M[mid][:3,2]*60).tolist(),[0,0,0]]
   kind='prepare' if travel==0 and sn==1 else 'check' if travel==0 else 'insert'
   row=add(ids,s['title'],note,path=path if travel else None,base=base,kind=kind,source_step=sn)
   if mid=='W' and (24<=sn<=44):
    # Wrist centre is fixed at the Y axis after insertion; X fork surrounds its X faces.
    row['target']=N['KEEP_E-P019'];row['printed_direction']=orientation[row['target']]['orientation']
   if mid=='W' and sn>=45:row['target']=N['KEEP_E-P017'];row['printed_direction']=orientation[row['target']]['orientation']
  complete[mid]=set(installed)
 # Choose a view from the actual entry side, not from the back of a blind seat.
 for st in allsteps:
  mid=st['chapter'];mat=np.array(st['frame_matrix']);q=st['parts'][0];feature=P[q]['name'];sku=P[q]['sku'];out=-mat[:3,2] if mid in rolls else -mat[:3,1]
  if st['animated']:out=unit(np.array(st['path'][0])-np.array(st['path'][-1]))
  candidates=[unit(mat[:3,:3]@np.array([sx*2.6,sy*3.2,sz*2.8])) for sx in [-1,1] for sy in [-1,1] for sz in [-1,1]]
  st['camera_direction']=max(candidates,key=lambda d:-abs(np.dot(d,out)-.65)+.13*d[2]+.01*d[0]).tolist()
  st['auto_section']=bool(sku in ['A8','FW4'] or (sku in ['NL3','W3','W4'] and '_lid_' not in feature and mid not in rolls))
  if mid in rolls and st['source_step']:
   oi=next(i+1 for i,s in enumerate(next(m for m in old['modules'] if m['id']==mid)['steps']) if s['feature'] in ['SHOULDER_PITCH','UPPER_ARM','FOREARM'])
   if st['source_step']>oi:st['target']=N[{'RP':'SHOULDER_PITCH','RU':'UPPER_ARM','RF':'FOREARM'}[mid]]
  if mid in ['HS','HE'] and st['source_step'] and 13<=st['source_step']<=22:st['target']=N['SHOULDER_ABDUCT' if mid=='HS' else 'ELBOW_OUTPUT']
  if mid=='W' and st['source_step'] and 25<=st['source_step']<=44:
   f=original_hw[feature.removeprefix('KEEP_')];st['target']=N['FOREARM' if '_WY' in f else 'KEEP_E-P018']
  if mid=='W' and st['source_step']==45:st['target']=N['KEEP_E-P018']
  st['printed_direction']=orientation[st['target']]['orientation']
 # The final pose is an actual kinematic change, not a straight-line part translation.
 last=allsteps[-1];end=dict(last);end.update(index=len(allsteps),number=len(allsteps)+1,chapter_step=len(chapters[-1]['step_indices'])+1,title='装配完成：回到A字参考姿态',note='托住固定输入座，将肩外展从0°缓慢移到45°。确认三只防脱盖均锁住，各肩钉穿过尼龙段；七轴先低预紧活动，再按试装记录调整保持力。本动画不代表实测强度或保持力。',kind='pose',parts=sorted(complete['W']),new_parts=[],primary=N['UPPER_ARM'],target=N['ROOT'],printed_parts=[p['part_number'] for p in parts if p['role']=='structure'],metal_parts=[],base_offset=[0,0,0],offsets={},visible=sorted(complete['W']),before=sorted(complete['W']),path=[[0,0,0]],animated=True,auto_section=False,camera_direction=unit([2.5,3.5,1]).tolist(),pose_from={a['id']:0 for a in PROFILE['axes']},pose_to=POSES['neutral']['angles'],printed_direction='固定S2-P004输入握持座，肩外展45°；前臂固有−90°钟向已计入，不再重复旋转。',metal_direction='本步不新增五金；保留已装的预紧、锁固与防脱件。');allsteps.append(end);chapters[-1]['step_indices'].append(end['index'])
 allsteps[-1]['metal_parts']=[p['part_number'] for p in parts if p['role']!='structure']
 assert global_seen==set(P),(set(P)-global_seen)
 # Pack exact immutable production triangles. No remeshing, no generated proxy parts.
 packed=[];cursor=0;data_parts=[]
 for p in parts:
  i=str(p['i']);v=z[i+'v'];f=z[i+'f'];mesh=trimesh.Trimesh(v,f,process=False);ar=np.concatenate([v[f],np.repeat(mesh.face_normals[:,None,:],3,axis=1)],axis=2).reshape(-1,6).astype('<f4');packed.append(ar)
  row=dict(id=p['part_number'],frame=p['frame'],role=p['role'],bounds=p['bounds_mm'],first=cursor,count=len(ar),**orientation[p['part_number']]);cursor+=len(ar);data_parts.append(row)
 data=dict(revision='O24E R2',geometry_sha256=EXPECTED,parts=data_parts,profile=PROFILE,steps=allsteps,chapters=chapters,geometry=base64.b64encode(np.vstack(packed).tobytes()).decode(),initial_angles={a['id']:0 for a in PROFILE['axes']},spring_groups=spring_groups,physical_tested=False,mechanical_only=True)
 put(DEST/'steps.json',{k:v for k,v in data.items() if k!='geometry'});(DEST/'data.js').write_text('window.ARM_GUIDE='+json.dumps(data,ensure_ascii=False,separators=(',',':'))+';',encoding='utf8')
 for f in ['index.html','style.css','guide.js','enhance.js']:shutil.copyfile(HERE/f,DEST/f)
 p=DEST/'index.html';s=p.read_text('utf8').replace('<script src="guide.js"></script>','<script src="guide.js"></script><script src="enhance.js"></script>');p.write_text(s,encoding='utf8')
 put(DEST/'source_fingerprints.json',{str(p.relative_to(H)):sha(p) for p in [SOURCE/'production_meshes.npz',SOURCE/'production_assembly.json',SOURCE/'kit.json',SOURCE/'tutorial/steps.json',SOURCE/'verification/capture_assembly.json',SOURCE/'verification/hinge_wrist_paths.json',SOURCE/'verification/module_joining.json',SOURCE/'O24E_left_arm_stock_R2.zip']})
 print('GUIDE',len(allsteps),'steps',len(parts),'parts',len(chapters),'chapters',flush=True)
 return data
if __name__=='__main__':build()
