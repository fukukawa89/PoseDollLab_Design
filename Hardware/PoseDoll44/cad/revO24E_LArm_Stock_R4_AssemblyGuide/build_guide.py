"""Standalone R3 assembly animation, derived from immutable production meshes."""
from pathlib import Path
import sys
sys.dont_write_bytecode=True
HERE=Path(__file__).resolve().parent;H=HERE.parents[1]
sys.path.insert(0,str(H/'cad/revO24E_LArm_Stock_R4'))
from build_stock import *
from assembly_plan import make_plan,tools_for_guide
import base64,shutil,re
HERE=Path(__file__).resolve().parent
SOURCE=H/'bench/revO24E_LArm_Stock_R4';DEST=SOURCE/'assembly_guide'
EXPECTED='131f5773614d53e33adcd16ac34a69802cda4ff049abefa3ada9da397af0b0d9'
load=lambda p:json.loads(p.read_text('utf8'))
def point(M,p):return (np.array(M)@np.r_[p,1])[:3]
def unit(v):v=np.asarray(v,float);return v/np.linalg.norm(v)

def build():
 global EXPECTED
 EXPECTED=sha(SOURCE/'production_meshes.npz')
 DEST.mkdir(exist_ok=True);(DEST/'verification').mkdir(exist_ok=True);(DEST/'source').mkdir(exist_ok=True)
 kit=load(SOURCE/'kit.json');parts=load(SOURCE/'production_assembly.json')['parts'];z=dict(np.load(SOURCE/'production_meshes.npz'));ints=load(SOURCE/'interfaces.json');P={p['part_number']:p for p in parts};N={p['name']:p['part_number'] for p in parts};K={p['part_number']:p for p in kit['structural_parts']+kit['hardware']}
 for t in tools_for_guide():
  vv,ff=e.base.a.mesh_data(t['s']);i=len(parts);m=trimesh.Trimesh(vv,ff,process=False);z[str(i)+'v']=vv;z[str(i)+'f']=ff
  q={k:v for k,v in t.items() if k!='s'};q.update(i=i,bounds_mm=m.bounds.tolist());parts.append(q);P[q['part_number']]=q;N[q['name']]=q['part_number'];K[q['part_number']]=dict(spec='重复使用的临时打印工装；不留在人偶内。',kit_label=q['label'])
 rolls={r['id']:r for r in ints['rolls']};hinges={r['id']:r for r in ints['hinges']};W={x:np.array(r['W']) for x,r in rolls.items()};M={x:np.array(r['M']) for x,r in hinges.items()};M['W']=F0['l_wrist_flex'];zero=frames({});worldV={}
 original_hw={r['part_number']:r['feature'] for r in load(SRC/'kit.json')['hardware']}
 for p in parts:
  vv=z[str(p['i'])+'v'];worldV[p['part_number']]=vv@zero[p['frame']][:3,:3].T+zero[p['frame']][:3,3]
 def centre(pn):return np.mean([worldV[pn].min(0),worldV[pn].max(0)],axis=0)
 def partmarker(label,pos):return dict(label=label,point=np.asarray(pos).tolist())
 def arrow(label,vector):return dict(label=label,direction=unit(vector).tolist())
 definitions={
 'RP_keeper':('压盖贴座的平面朝固定座；环唇对准大平垫外缘，两个六角螺钉头口朝操作侧。',[("贴座面",point(W['RP'],[0,0,0])),("螺钉头装入口",point(W['RP'],[16,0,-6]))]),
 'RU_keeper':('压盖贴座的平面朝固定座；环唇对准大平垫外缘，两个六角螺钉头口朝操作侧。',[("贴座面",point(W['RU'],[0,0,0])),("螺钉头装入口",point(W['RU'],[16,0,-6]))]),
 'RF_keeper':('前臂压盖使用宽孔距版本；贴座面朝固定座，六角螺钉头口朝操作侧。',[("贴座面",point(W['RF'],[0,0,0])),("宽孔距螺钉头口",point(W['RF'],[20,0,-6]))]),
 'ROOT':('大平垫圆座与中心六角窝朝操作侧；实心握持块用于固定，不要夹持压盖环唇。',[("握持块",[0,-4,0]),("RP固定座入口",point(W['RP'],[0,0,0]))]),
 'SHOULDER_PITCH':('圆盘转子耳朝RP固定座；横向双孔端是肩外展固定端。侧窗保持可达。',[("RP转子耳",point(W['RP'],[0,0,-2])),("肩外展固定端",point(M['HS'],[0,0,0]))]),
 'SHOULDER_ABDUCT':('U形叉口朝肩外展固定端；另一端带压盖的RU座朝上臂骨杆。',[("肩外展叉口",point(M['HS'],[0,0,0])),("RU固定座",point(W['RU'],[0,0,0]))]),
 'UPPER_ARM':('圆盘耳端朝肩侧的RU座；连续横桥端朝肘。侧窗用于送入由托叉承托并由导向针定位的整组五金。',[("肩端：RU转子耳",point(W['RU'],[0,0,-2])),("肘端：横桥",point(M['HE'],[0,0,0]))]),
 'ELBOW_OUTPUT':('U形叉口朝肘固定端；宽压盖的RF座朝前臂。保持宽压盖两颗螺钉可操作。',[("肘叉口",point(M['HE'],[0,0,0])),("RF固定座",point(W['RF'],[0,0,0]))]),
 'FOREARM':('圆盘耳端朝RF固定座；双叉耳端朝腕中心件。腕根圆弧避空不得当作承压台阶。',[("肘端：RF转子耳",point(W['RF'],[0,0,-2])),("腕叉口",point(M['W'],[0,0,0]))]),
 'KEEP_E-P017':('方键入口朝腕输出叉；指端朝远离手腕的一端。负X为锁母侧，正X为螺钉头及两片垫片侧。',[("方键入口",point(F0['l_wrist_deviation'],[0,0,-22])),("两片垫片／螺钉头侧",point(F0['l_wrist_deviation'],[7,0,-27])),("锁母侧",point(F0['l_wrist_deviation'],[-9,0,-27]))]),
 'KEEP_E-P018':('一体件的双叉耳开口朝腕中心件，指端远离腕轴；掌部不再拆分。侧面磁铁入口保留，本轮不装电子件。',[("腕中心叉口",point(M['W'],[0,0,0])),("一体掌部",point(F0['l_wrist_deviation'],[0,0,-27]))]),
 'KEEP_E-P019':('先在台面上完成四侧内层五金，并逐侧检查定位筋留住FW4。Y轴两侧对应前臂叉，X轴两侧对应腕输出叉；不要提前合叉。',[("Y轴：前臂叉",point(M['W'],[0,9,0])),("X轴：输出叉",point(M['W'],[9,0,0])),("朝肘 +Z",point(M['W'],[0,0,7]))]),
 }
 orientation={};spring_groups={}
 for p in parts:
  pn=p['part_number'];name=p['name'];c=centre(pn);spec=K[pn]['spec'];role='打印件' if p['role']=='structure' else '五金';mark=[];ar=[];note='';sku=p['sku']
  if p['role']=='tool':
   role='临时工装';note=p['label']+'；两种实物各打印1件，在三个旋转模块重复使用。';mark=[partmarker('握持端（外部）',c),partmarker('作业端',worldV[pn].max(0))]
  elif role=='打印件':
   note,landmarks=definitions[name];mark=[partmarker(t,x) for t,x in landmarks]
  else:
   if name.startswith(('RP_','RU_','RF_')):
    pre=name[:2];out=-W[pre][:3,2];suffix=name[len(pre)+1:];joint=pre
    if '_lid_' in name:out=-W[pre][:3,2] if sku=='M3x16' else W[pre][:3,2]
   elif name.startswith(('HS_','HE_')):
    pre=name[:2];side=-1 if '_HL_' in name else 1;out=M[pre][:3,1]*side;suffix=name.split('_')[-1];joint=pre+('_HL' if side==-1 else '_HR')
   else:
    f=original_hw[name.removeprefix('KEEP_')];suffix=f.split('_')[-1]
    if f.startswith('l_E_W'):
     channel=f.split('_')[2];side=-1 if channel.endswith('M') else 1;axis=0 if 'WX' in channel else 1;out=M['W'][:3,axis]*side;joint=channel
    else:out=F0['l_wrist_deviation'][:3,0]*( -1 if sku=='NL2' else 1);joint='PALM'
   out=unit(out)
   if sku in ['AX4','M3x16','M2x20']:
    note='螺纹尖端先进入，螺钉头留在外侧。'+('光杆Φ4×8进入转动孔；M3×6螺纹端穿入锁母；用3 mm内六角。' if sku=='AX4' else '整根使用，不切短；本版反向安装，头留在压盖六角窝，背面用两颗普通M3对顶。' if sku=='M3x16' else '从正X侧穿入；两片W2都在头下；用1.5 mm内六角。')
    ar=[arrow('螺纹端先入',-out),arrow('螺钉头朝外',out)]
   elif sku=='N3':
    note='普通M3正常高度2.4 mm，位于固定座背面；每支压盖螺钉两颗对顶。先轻贴合内侧一颗，再保持其不转，锁住外侧一颗。';ar=[arrow('背面外侧',out),arrow('固定座与W3侧',-out)]
   elif sku in ['NL3','NL2']:
    nylon=out if '_lid_nut_' in name or sku=='NL2' else -out
    note=('尼龙端朝外，金属端贴承压台阶；先把六角外形对齐锁母窝。' if '_lid_nut_' in name or sku=='NL2' else '尼龙端先进入深处，金属端朝入口；后续反力垫贴金属端。')+' 本处为关节预紧锁母，仍保留NL3；压盖固定组另用两颗普通M3。'
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
 allsteps,chapters=make_plan(parts,orientation)
 # Pack exact immutable production triangles. No remeshing, no generated proxy parts.
 packed=[];cursor=0;data_parts=[]
 for p in parts:
  i=str(p['i']);v=z[i+'v'];f=z[i+'f'];mesh=trimesh.Trimesh(v,f,process=False);ar=np.concatenate([v[f],np.repeat(mesh.face_normals[:,None,:],3,axis=1)],axis=2).reshape(-1,6).astype('<f4');packed.append(ar)
  row=dict(id=p['part_number'],frame=p['frame'],role=p['role'],bounds=p['bounds_mm'],first=cursor,count=len(ar),**orientation[p['part_number']]);cursor+=len(ar);data_parts.append(row)
 data=dict(revision='O24E R4',geometry_sha256=EXPECTED,parts=data_parts,profile=PROFILE,steps=allsteps,chapters=chapters,geometry=base64.b64encode(np.vstack(packed).tobytes()).decode(),initial_angles={a['id']:0 for a in PROFILE['axes']},spring_groups=spring_groups,physical_tested=False,mechanical_only=True)
 put(DEST/'steps.json',{k:v for k,v in data.items() if k!='geometry'});(DEST/'data.js').write_text('window.ARM_GUIDE='+json.dumps(data,ensure_ascii=False,separators=(',',':'))+';',encoding='utf8')
 for f in ['index.html','style.css','guide.js','enhance.js']:shutil.copyfile(HERE/f,DEST/f)
 p=DEST/'index.html';s=p.read_text('utf8').replace('<script src="guide.js"></script>','<script src="guide.js"></script><script src="enhance.js"></script>');p.write_text(s,encoding='utf8')
 put(DEST/'source_fingerprints.json',{str(p.relative_to(H)):sha(p) for p in [SOURCE/'production_meshes.npz',SOURCE/'production_assembly.json',SOURCE/'kit.json',SOURCE/'tooling/kit.json']})
 print('GUIDE',len(allsteps),'steps',len(parts),'parts',len(chapters),'chapters',flush=True)
 return data
if __name__=='__main__':build()
