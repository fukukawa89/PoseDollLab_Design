"""O22F7 part-by-part animation generator. Manufacturing files remain read-only."""
from pathlib import Path
from collections import Counter
import hashlib,json,math,sys,shutil
import numpy as np
import build_revo22_assembly as kin
R=Path(__file__).resolve().parents[1]
B=R/'Hardware/PoseDoll44/bench/revO22';F=B/'O22F7_PLA_Final';G=F/'assembly/tutorials/assembly-o22';OUT=G/'animation';WORK=B/'diagnostics/O22F7_20261016/animation_update'
REV='O22F7-animation-r3-20261016'
read=lambda p:json.loads(p.read_text('utf-8-sig'))
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,s):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(s,encoding='utf8')
def put(p,d):write(p,json.dumps(d,ensure_ascii=False,separators=(',',':'),allow_nan=False))
def unit(v):v=np.array(v,float);return v/max(np.linalg.norm(v),1e-12)
def arr(v):return np.round(v,8).tolist()

class Build:
 def __init__(self):
  self.g=read(G/'guide-data.json');self.scene=read(G/'scene.json');self.meta=read(B/'mechanical/assembly_metadata.json');self.profile=read(B/'profiles/device_profile.json');self.target=read(B/'profiles/default_pose.json')['raw_deg']
  self.obs={o['label']:o for o in self.scene['objects']};self.idx={k:i for i,k in enumerate(self.obs)};self.verts=np.fromfile(G/self.scene['geometry_url'],dtype='<f4').reshape(-1,6)
  self.actions=[];self.chapters=[];self.seen=set();self.offset={};self.axis={};self.bind=[]
  ff,oo=kin.owners(self.target)
  for k,o in self.obs.items():
   m=self.meta['meta'][k];owner='frame:'+m['body'] if m['owner']=='rigid_frame' else m['module']+':'+m['owner'];M=ff[m['body']] if m['owner']=='rigid_frame' else oo[m['module'],m['owner']]
   local=np.linalg.inv(M)@np.array(o['matrix']).reshape(4,4);mesh=self.scene['meshes'][o['mesh']];v=self.verts[mesh['first']:mesh['first']+mesh['count'],:3].astype(float);lo,hi=v.min(0),v.max(0);c=(lo+hi)/2
   _,U=np.linalg.eigh(np.cov(np.unique(v,axis=0).T));bolt='SCREW' in (o.get('sku') or '') or 'SHOULDER' in (o.get('sku') or '');a=U[:,2] if bolt else U[:,0];z=(v-c)@a;rad=np.linalg.norm(v-c-z[:,None]*a,axis=1);extent=z.max()-z.min()
   if bolt and np.percentile(rad[z<z.min()+extent*.2],90)>np.percentile(rad[z>z.max()-extent*.2],90):a=-a
   self.axis[k]=a;self.bind.append({'owner':owner,'local':arr(local.flatten()),'center':arr(c),'lo':arr(lo),'hi':arr(hi)})
  self.pose_error=max(np.abs((ff[self.meta['meta'][k]['body']] if self.meta['meta'][k]['owner']=='rigid_frame' else oo[self.meta['meta'][k]['module'],self.meta['meta'][k]['owner']])@np.array(self.bind[self.idx[k]]['local']).reshape(4,4)-np.array(o['matrix']).reshape(4,4)).max() for k,o in self.obs.items())
 def begin(self,s):
  self.st=s;self.mod=s['id'];self.chapter=s['step'];self.group='准备';self.chapter_keys=set(s.get('objects',[]));self.raw=dict(self.target)
  for r in s.get('raw_ids',[]):self.raw[r]=0
  ff,oo=kin.owners(self.raw);self.frames=ff;self.owners=oo;self.mats={}
  for k in self.obs:
   mm=self.meta['meta'][k];M=ff[mm['body']] if mm['owner']=='rigid_frame' else oo[mm['module'],mm['owner']];self.mats[k]=M@np.array(self.bind[self.idx[k]]['local']).reshape(4,4)
  self.mount=ff[s['parent']]@np.array(s['parent_to_mount_mm']) if s.get('parent') else np.array(self.obs['o22/carrier_pcb']['matrix']).reshape(4,4)
  self.chapters.append({'id':self.chapter,'title':s['title'],'start':len(self.actions),'kind':s['kind'],'objects':[self.idx[k] for k in dict.fromkeys(s.get('objects',[])) if k in self.idx],'raw_ids':s.get('raw_ids',[])})
 def center(self,k):return (self.mats[k]@np.r_[self.bind[self.idx[k]]['center'],1])[:3]
 def direction(self,v):return self.mount[:3,:3]@np.array(v,float)
 def axis_world(self,k):return unit(self.mats[k][:3,:3]@self.axis[k])
 def name(self,k):
  o=self.obs[k]
  if o.get('address'):return o['name_zh']
  if o['role']=='sensor':return 'MT6701 预焊传感板'
  brief={'A8_SS':'碟簧 A8 · Ø8 × Ø4.2 × 0.4 mm','W_M4_D12_T1':'M4 大垫圈 · Ø12 × 1 mm','W_M4_D9_T0P8':'M4 平垫圈 · Ø9 × 0.8 mm','W_M3_D9_T0P8':'M3 反力垫圈 · Ø9 × 0.8 mm','SHOULDER_D4_L8_M3_L6':'轴肩螺钉 · Ø4×8 / M3×6','SELF_TAP_M2_L6':'M2×6 塑料自攻螺钉'}
  if o.get('sku') in brief:return brief[o['sku']]
  return self.g['hardware'].get(o.get('sku'),{}).get('name_zh',o.get('sku') or k).split('；')[0].split('（')[0]
 def action(self,kind,title,cue='',check='',new=(),moving=(),path=None,focus=(),**kw):
  new=list(new);moving=list(moving or new);focus=list(focus or moving)
  assert not (set(new)&self.seen),(title,set(new)&self.seen)
  assert set(new)<=self.obs.keys() and set(moving)<=self.obs.keys(),title
  self.seen.update(new);p=np.array(path if path is not None else [[0,0,0],[0,0,0]],float)
  a={'id':f'A{len(self.actions)+1:04}','chapter':self.chapter,'group':self.group,'kind':kind,'title':title,'cue':cue,'check':check,'new':[self.idx[k] for k in new],'moving':[self.idx[k] for k in moving],'focus':[self.idx[k] for k in focus if k in self.idx],'path':arr(p),'duration':7 if kind in ['install','transfer'] else 9,'gate':kind in ['check','power','glue','finished']};a.update(kw)
  for k in moving:self.offset[k]=p[-1]
  self.actions.append(a);return a
 def install(self,k,dir=None,end=None,receiver=(),title=None,cue=None,check=None,path=None,**kw):
  end=np.zeros(3) if end is None else np.array(end,float);d=unit(self.axis_world(k) if dir is None else dir);o=self.obs[k];sku=o.get('sku') or '';length=32 if o['role']=='metal' else 48;path=[end+d*length,end] if path is None else path;bolt='SCREW' in sku or 'SHOULDER' in sku
  return self.action('install',title or ('拧入' if bolt else '放入')+' · '+self.name(k),cue if cue is not None else ('对准孔，先用手带入螺纹，再用工具拧入。' if bolt else '先对准方向，再沿箭头放到高亮位置。'),check if check is not None else ('贴合后停下；不要把 PLA 压变形。' if bolt else '完全落座，不歪斜。'),new=[k],path=path,focus=[k,*receiver],receiver=[self.idx[x] for x in receiver if x in self.idx],axis=arr(d),spin=bolt,detail='spring' if sku=='A8_SS' else 'washer' if sku.startswith('W_') else 'screw' if bolt else 'nut' if sku.startswith('NUT') else 'part',**kw)
 def check(self,title,cue,focus=(),**kw):return self.action('check',title,cue,focus=focus,**kw)
 def transfer(self,keys,start,end,title,cue='',path=None):return self.action('transfer',title,cue,'对准后贴合，保持已装小件的位置。',moving=keys,path=path or [arr(start),arr(end)],focus=keys)
 def inside(self,prefix,receiver,end=None):
  d=self.direction([0,1,0]) if self.st['kind']=='hinge' else self.direction([0,0,1])
  for tail in ['M3_nut','M3_reaction_washer','inner_M4_wide']:self.install(prefix+tail,dir=d,end=end,receiver=receiver,cue='从敞开的检修口放入；平面贴住座底。' if tail=='M3_nut' else '对准轴孔，放在动画标出的内侧位置。',check='先装这些内侧小件，再装转动件。')
 def outside(self,prefix,receiver,end=None):
  d=self.axis_world(prefix+'shoulder_D4_L8_M3_thread6')
  for tail in ['outer_M4_wide','spring_1','spring_2','front_M4_washer','shoulder_D4_L8_M3_thread6']:
   ex={}
   if tail=='spring_1':ex=dict(cue='第一片碟簧按特写方向放入。',check='下一片要翻面，与这一片相向成对。')
   if tail=='spring_2':ex=dict(cue='第二片翻面放入，形成相向的一对。',check='确认像特写中的“()”组合，不是同向套叠。')
   if tail.startswith('shoulder'):ex=dict(cue='穿过垫圈中心，旋入已放好的 M3 螺母。',check='调到关节能保持姿势、又可平稳转动；不要锁死。')
   self.install(prefix+tail,dir=d,end=end,receiver=receiver,**ex)
 def twist_preload(self,endname,frame,offset):
  prefix=self.mod+'/'+endname+'_';self.group=('近端' if endname=='P' else '远端')+'转轴 · 预装半壳';d=self.direction([0,1,0]);keys=[];stage=np.array(offset)+self.direction([0,65,60]);plus=prefix+'case_plus'
  self.install(plus,dir=d,end=stage,title='先准备另一半壳 · '+self.name(plus),cue='在手边预装调节螺母和摩擦垫，暂时不合壳。',station=True)
  self.install(prefix+'adjust_nut',dir=self.direction([0,0,1 if endname=='P' else -1]),end=stage,receiver=[plus],cue='从半壳敞开的轴向槽口放入 M3 调节螺母。',check='六角边贴合槽壁，保持螺母在槽内。')
  self.install(prefix+'radial_pad',dir=-d,end=stage,receiver=[plus],cue='从半壳内侧把摩擦垫放入槽，弧面朝向转轴。',check='托住摩擦垫；合壳前不要让它掉出。')
  for i in range(4):
   k=prefix+'case_nut_'+str(i);self.install(k,dir=-d,end=offset,receiver=[frame],cue='把 M2 六角螺母压入骨架半壳外侧的六角槽。');keys.append(k)
  return keys
 def twist_close(self,endname,frame):
  prefix=self.mod+'/'+endname+'_';self.group=('近端' if endname=='P' else '远端')+'转轴 · 合半壳';plus=prefix+'case_plus';stage=self.offset[plus];d=self.direction([0,1,0])
  self.transfer([plus,prefix+'adjust_nut',prefix+'radial_pad'],stage,[0,0,0],'合上预装好的半壳','托住摩擦垫与螺母，先移到轴的侧面，再合上半壳。',path=[arr(stage),arr(d*65),[0,0,0]])
  for i in [0,3,1,2]:self.install(prefix+'case_screw_'+str(i),receiver=[plus],cue='逐个拧入 M2×20，交替收紧。')
  self.install(prefix+'adjust_screw',receiver=[plus],cue='旋入 M3×8 调节螺钉，使其顶住摩擦垫。',check='转轴能平稳旋转；不能让螺钉直接磨轴。')
 def magnetic_sensor(self,r):
  prefix=r['sensor_part_O20'].replace('sensor_PCB','');mag=prefix+'magnet';cap=r['magnet_mount'];mounts=r['mounts'];pcb=[k for k in self.obs if k.startswith(r['sensor_part_O20']+'/')];assert len(pcb)==7
  pcba=r['sensor_part_O20']+'/pcb';PM=self.mats[pcba];normal=unit(PM[:3,2]);slide=unit(PM[:3,1]);endaxis=cap.endswith('magnet_cap');sensorname=r['connector']+' · '+r['raw_id'];out=normal*55;self.group=sensorname+' · 磁铁'
  relevant=[k for k in self.chapter_keys if k.startswith(prefix) and self.obs.get(k,{}).get('role')=='metal'];nuts=sorted(k for k in relevant if 'magnet' in k and 'nut' in k);screws=sorted(k for k in relevant if 'magnet' in k and 'screw' in k)
  for k in nuts:
   d=unit(self.center(k)-self.center(mag));d=d-normal*np.dot(d,normal);self.install(k,dir=d,cue='从侧面的窗口放入 M2 螺母，再安装磁铁座。')
  self.install(cap,dir=slide,end=out,title='在手边准备 · '+self.name(cap),cue='磁铁座暂时放在关节外，先装磁铁。',check='此时还没有装到转轴上。',station=True)
  if endaxis:md=-normal
  else:
   mm=self.meta['meta'][mag];A=np.array(mm['transform'],float)
   if '/C01_' in mag or '/C02_' in mag:
    i=0 if '/C01_' in mag else 1;Z=np.eye(3)[i];X=np.array([0,0,-1 if i==0 else 1]);Y=np.cross(Z,X);A[:3,:3]=A[:3,:3]@np.c_[X,Y,Z]
   if np.linalg.det(A[:3,:3])<0:A[:3,1]*=-1
   delta=self.mats[mag]@np.linalg.inv(np.array(mm['transform']));spacing=6.1 if '/C0' in mag else 8.;theta=math.asin(4/spacing);md=unit((delta@A)[:3,:3]@np.array([math.cos(theta),math.sin(theta),0]))
  self.install(mag,dir=md,end=out,receiver=[cap],title='放入径向磁铁 · '+r['connector'],cue='从磁铁盖背面的大开口放入；正面小挡边朝传感板。' if endaxis else '从侧向开口滑入 Φ6×2.5 径向充磁磁铁。',check='磁铁平整落座，不能用轴向充磁磁铁替代。',detail_override='magnet')
  self.action('glue','少量防转胶 · 等待固化','只在磁铁与座接触处少量点胶。按胶说明等到完全固化后继续。','磁铁不能在座内转动；胶不要流进活动间隙。',focus=[cap,mag],overlay='glue',route=r['connector'])
  self.transfer([cap,mag],out,[0,0,0],'装上磁铁座 · '+r['connector'],'把已固化的磁铁座对准转轴端面。')
  for k in screws:self.install(k,receiver=[cap],cue='端轴用 M2×4；关节磁铁座用 M2×5。按当前规格拧入。',check='两个螺钉都固定到位；磁铁保持在座内。')
  self.group=sensorname+' · 传感板'
  if endaxis:
   for k in sorted(k for k in relevant if 'pcb_nut' in k):self.install(k,dir=-normal,cue='先放入固定传感板夹块的 M2 螺母。')
   self.action('install','放上传感板 · '+r['connector'],'手持板边，芯片一面朝向磁铁。','导线从留出的出口向外，不压在夹块下。',new=pcb,path=[arr(normal*40),[0,0,0]],focus=[mag,*pcb],axis=arr(normal),detail='sensor',route=r['connector'])
   for k in mounts:self.install(k,dir=normal,receiver=[pcba],cue='两侧夹块分别装入，夹住板边。',check='夹块不能压到芯片和焊点。')
   for k in sorted(k for k in relevant if 'pcb_screw' in k):self.install(k,receiver=mounts,cue='旋入 M2×8，把两侧夹块轻轻收紧。')
  else:
   cas=mounts[0]
   for k in sorted(k for k in relevant if 'pcb_clip_nut' in k):self.install(k,dir=-slide,cue='先从检修窗口放入 M3 六角螺母。')
   self.install(cas,dir=slide,end=out,title='在手边准备 · '+self.name(cas),cue='先在关节外把板装入卡座，再整体安装。',station=True)
   self.action('install','滑入传感板 · '+r['connector'],'轻放开弹舌，手持板边，沿导槽平行滑入。','芯片朝磁铁；板边入槽后让弹舌回位。',new=pcb,path=[arr(out+slide*26),arr(out)],focus=[cas,*pcb],axis=arr(slide),detail='sensor',route=r['connector'],overlay='latch')
   self.check('检查卡座锁住板边','轻拨板边确认不会滑出；不要按芯片或焊点。',focus=[cas,*pcb],route=r['connector'],overlay='sensor')
   self.transfer([cas,*pcb],out,[0,0,0],'装上传感板卡座 · '+r['connector'],'对准固定柱与定位键，芯片面朝向磁铁。')
   for k in sorted(k for k in relevant if 'pcb_clip_screw' in k):self.install(k,receiver=[cas],cue='旋入 M3×8 固定卡座，不压弯电路板。')
  self.action('check','留出软线圈 · '+r['connector'],'先在板端固定线束，再在活动关节处留 U 形余量。','轻动关节，线不能拉紧或卷进夹缝；本步仍断电。',focus=[mag,*pcb,*mounts],overlay='slack',route=r['connector'])
 def mechanical(self,s):
  self.begin(s);parent='frame/'+s['parent'];child='frame/'+s['child'];mod=s['id'];self.group='基座与方向'
  if parent not in self.seen:self.install(parent,dir=self.direction([0,0,1]),title='从第一件开始 · '+self.name(parent),cue='在软垫上托住基座。按画面确认前后与左右。',check='左右以人偶自身为准。')
  if s['kind']=='hinge':
   prefix=mod+'/';self.group='轴孔内侧 · 先放螺母与垫片';self.inside(prefix,[parent]);self.group='连接骨架';self.install(child,dir=self.direction({'S05':[0,0,1],'S07':[1,0,0],'S09':[1,0,0],'S12':[1,0,0],'S21':[0,0,1],'S23':[1,0,0],'S25':[0,0,1]}.get(s['step'],[0,1,0])),receiver=[parent],cue='保持图示方向，沿箭头把转动件放进支座。',check='两侧轴孔同心；内侧垫片仍在原位。');self.group='摩擦组 · 从里向外';self.outside(prefix,[child]);self.check('先检查摩擦，再封磁铁座','轻转关节：可以平稳转动，松手能保持位置。',focus=[parent,child],overlay='friction')
  else:
   endP=s['kind'] in ['tut','wide_tut','three_axis'];endD=s['kind'] in ['tut','wide_tut'];ankle=s['kind']=='ankle_core';off=self.direction([0,90,0]) if endP else self.direction([0,0,-90]);c01=mod+'/C01' if not ankle else child;c02=mod+'/C02' if endD else child if not ankle else parent
   if endP:self.twist_preload('P',parent,np.zeros(3))
   self.group='转动核心 · 在手边组装';self.install(c01,dir=self.direction([0,0,-1]),end=off,title='准备下叉 · '+self.name(c01),cue='先在半壳外组装核心，给下环留出绕入空间。',station=True)
   ring=mod+'/C14';pathdir=R/'Hardware/PoseDoll44/generated/revO15/runs/o15_20260929_r1';file='simple_assembly_path_ankle_core.json' if ankle else 'ring_assembly_without_obsolete_pin.json';p=([[0,0,0],[0,0,-1],[0,-3,-1],[0,-3,16],[0,70,16]] if ankle else read(pathdir/file)['path']);p=[p[0]]+[p[i] for i in range(1,len(p)-1) if not np.array_equal(np.array(p[i])-p[i-1],np.array(p[i+1])-p[i])]+[p[-1]];path=[arr(off+self.direction(v)) for v in reversed(p)]
   self.install(ring,end=off,path=path,receiver=[c01],title='绕入下环 · '+self.name(ring),cue='沿动画侧移、下移和回正；不能直接穿过下叉。',check='先绕入下环，再安装上叉和小五金。',duration=14)
   self.group='核心内侧 · 四组螺母与垫片'
   for axis in ['C01','C02']:
    for side in ['-1','+1']:self.inside(mod+'/'+axis+'_'+side+'_',[ring],end=off)
   self.group='交叉轴 · 放入上叉'
   if not ankle:self.install(c02,dir=self.direction([0,0,1]),end=off,receiver=[ring,c01],cue='从上方落入，与下叉成直角，保持内侧垫片在位。')
   corekeys=[k for k in self.obs if k in self.seen and k in self.chapter_keys and np.linalg.norm(self.offset.get(k,np.zeros(3))-off)<1e-5]
   if ankle:self.transfer(corekeys,off,[0,0,0],'将足部核心接到小腿','托住小腿，移动已装好的足部与下环，对准上叉。');off=np.zeros(3)
   self.group='合上环 · 保持螺母在位';self.install(mod+'/C15',end=off,path=([arr(off+self.direction(v)) for v in [[-18,-70,8],[-18,0,8],[0,0,8],[0,0,0]]] if ankle else [arr(off+self.direction([-70,0,8])),arr(off+self.direction([0,0,8])),arr(off)]),receiver=[ring],cue='按折线路径先绕过脚掌与小腿，再落到下环。' if ankle else '先侧移到上方，再平移落到下环。')
   for n in [1,4,2,3]:
    nut=mod+f'/ring_nut_{n}';bolt=mod+f'/ring_screw_{n}';d=self.axis_world(bolt);self.install(nut,dir=-d,end=off,receiver=[ring,mod+'/C15'],cue='按动画放入 M1.6 螺母；相邻孔的朝向相反。');self.install(bolt,dir=d,end=off,receiver=[ring,mod+'/C15'],cue='从螺母对面拧入 M1.6×6，按对角顺序收紧。')
   self.group='摩擦组 · 四个轴端逐片安装'
   for axis in ['C01','C02']:
    for side in ['-1','+1']:self.outside(mod+'/'+axis+'_'+side+'_',[ring,c01,c02],end=off)
   self.check('检查核心转动','轻转两个方向，检查碟簧相向、垫片平整；能动且能保持姿势。',focus=[ring,c01,c02],overlay='friction')
   if endP:
    corekeys=[k for k in self.obs if k in self.seen and k in self.chapter_keys and np.linalg.norm(self.offset.get(k,np.zeros(3))-off)<1e-5];self.transfer(corekeys,off,[0,0,0],'把核心放进近端半壳','保持摩擦垫在槽内，从敞开的一侧放入转轴。');self.twist_close('P',parent)
   if endD:
    stage=self.direction([0,90,0]);self.group='远端骨架 · 先放内部件';self.install(child,dir=self.direction([0,0,1]),end=stage,cue='先在手边准备远端骨架，暂时留出半壳开口。',station=True);pre=self.twist_preload('D',child,stage);self.transfer([child,*pre],stage,[0,0,0],'把远端半壳接到转轴','托住骨架，保持预装螺母和摩擦垫不脱位。');self.twist_close('D',child)
  if s['step'] in ['S04','S11']:
   # Do not demonstrate a known obstructed translation as an assembly instruction.
   a=next(a for a in self.actions if self.idx[child] in a['new'])
   a.update(kind='fit-review',gate=True,needs_path_review=True,path=[[0,0,0],[0,0,0]],title='待确认 · '+s['title']+'装入路径',cue='这里显示最终安装位置。装入动作尚未验证，请先不要按直线硬推。',check='直线进入会碰到胸部骨架；绕入方法需进一步核对，当前画面不能作为已验证的装入示范。')
  for r in [r for r in self.g['routes'] if r['step']==s['step']]:self.magnetic_sensor(r)
  self.group='本节完成';self.action('pose','调整到图示姿态','托住两侧骨架，轻轻转到画面姿态，方便接着安装。','导线保留余量；遇到卡住先检查，不要强扭。',focus=[parent,child],duration=8,pose=True);self.check(s['title']+' · 本节检查','小件全部落座，转动顺畅，磁铁不松动，板边被固定。',focus=[parent,child],pose_final=True,overlay='complete')
  assert not (set(s['objects'])-self.seen),(s['step'],'UNPLANNED',set(s['objects'])-self.seen)
 def electronics(self):
  self.begin(self.g['steps'][-1]);self.group='中央板 · 断电准备';self.check('断开 USB 与外接电源','本章插接线束时保持断电；先确认成品板已经焊接并检查。',focus=['o22/carrier_pcb'],overlay='off');equipment=[k for k,o in self.obs.items() if o['role']=='equipment'];normal=unit(self.mats['o22/carrier_pcb'][:3,2]);pcb='o22/carrier_pcb'
  self.action('install','放入中央成品板','拿板边，将四个安装孔对准背盒里的四根柱。','XIAO、插座和芯片是工厂预焊的成品板组件。',new=equipment,path=[arr(normal*65),[0,0,0]],focus=[pcb,'frame/chest'],axis=arr(normal),detail='carrier',duration=10)
  for i in [0,3,1,2]:self.install('o22/carrier_screw_'+str(i),dir=normal,receiver=[pcb],cue='用塑料自攻 M2×6 按对角顺序固定。',check='板子不翘曲；螺钉贴合即停。')
  self.check('认识供电与插座','看清 USB、外接 5V 的 J3、A/B/C 三组传感器插座。',focus=[pcb],overlay='power-map');self.check('确认五针顺序','按 Pin 1 标记与端子编号核对；示意颜色不代表实际线色。',focus=[pcb],overlay='pinout')
  for n,r in enumerate(self.g['routes']):
   self.group='逐路接线 · '+r['connector'][0]+' 组';conn='o22/'+r['carrier_reference'];pk=r['sensor_part_O20']+'/pcb'
   self.action('wire','布线 · '+r['connector'],'从这块传感板沿路线走到背盒，在活动处留 U 形松弛圈。','路线用于定位；实际线长先试走、再检查活动余量。',focus=[pk,conn],route=r['connector'],overlay='route',duration=12)
   self.action('plug','插接 · '+r['connector']+' → '+r['carrier_reference'],'抓住插头外壳，对准卡扣方向，插入高亮的五针插座。','核对线束标签和插座编号；不能只按线色判断。',focus=[conn],route=r['connector'],overlay='pinout',duration=9)
   self.check('检查这一条线 · '+r['connector'],'轻拉插头外壳确认扣住，轻动关节确认不拉线、不夹线。',focus=[pk,conn],route=r['connector'],overlay='slack')
   if n==0 or n in [13,29,45]:
    self.group='分段通电检查';self.action('power',('首路' if n==0 else r['connector'][0]+' 组')+' · 通电检查','确认针序与绝缘后按供电图接电，读取已接通道，缓慢转动关节观察角度。','需要你确认实物电压、温升和读数正常，再断电继续。',focus=[pcb],overlay='test',route=r['connector'],bank_end=n,duration=12);self.check('再次断电','拔掉 USB 和外接电源，再继续插接或合盖。',focus=[pcb],overlay='off')
  self.group='理线与合盖';self.check('检查 46 路与活动余量','逐路检查标签、读数和关节活动；背盒收好线，盖沿不能夹住导线。',focus=[pcb],overlay='all-routes');self.install('o22/controller_lid',dir=normal,receiver=['frame/chest'],cue='先收好线束，再把背盖沿箭头合上。',check='盖边没有导线，通风孔保持通畅。',duration=10)
  for i in [0,1]:self.action('tie',f'穿入并收紧第 {i+1} 根扎带','沿高亮槽穿入扎带，绕过背盒后扣紧，剪去多余尾端。','盖子不松动；扎带不压线、不压电路板。',focus=['o22/controller_lid','frame/chest'],overlay='tie',tie=i,duration=12)
  self.action('finished','完整位置预览 · 最后检查','S04/S11 的装入方法仍待确认。本画面展示全部零件的最终位置，可查看其余步骤与电路。','本页记住观看位置；完成动画不等于实物验收通过。',focus=[k for k,o in self.obs.items() if o['role']=='frame'],overlay='finished',duration=12)
 def run(self):
  for s in self.g['steps'][:-1]:self.mechanical(s)
  self.electronics();assert self.seen==set(self.obs),set(self.obs)-self.seen
  for i,c in enumerate(self.chapters):c['end']=self.chapters[i+1]['start'] if i+1<len(self.chapters) else len(self.actions)
  tally=Counter(self.obs[k]['role'] for k in self.seen);metal=Counter(self.obs[k]['sku'] for k in self.seen if self.obs[k]['role']=='metal');assert all(metal[k]==v['net_quantity'] for k,v in self.g['hardware'].items())
  excluded=[{'address':q['address'],'id':q['id'],'name':q['name_zh'],'reason':'可选小样，不重复装机' if q['optional'] else '工厂焊接用的 4 mm 间距量规，安装成品板不需要它'} for q in self.g['instances'] if q['optional'] or q['part']=='fixture/xiao_spacing_gauge']
  data={'schema':'O22F7-PART-BY-PART-ANIMATION/1','revision':REV,'scene_url':'../scene.json','geometry_url':'../'+self.scene['geometry_url'],'source_geometry_sha256':sha(G/self.scene['geometry_url']),'source_guide_sha256':sha(G/'guide-data.json'),'bind':self.bind,'profile':{k:self.profile[k] for k in ['root_transform_mm','joints','raw_order']},'target_raw':self.target,'chapters':self.chapters,'actions':self.actions,'routes':self.g['routes'],'hardware':self.g['hardware'],'excluded':excluded,'coverage':{'print_instances':tally['print']+tally['frame'],'hardware_instances':tally['metal'],'sensor_boards':46,'factory_board_meshes':tally['sensor']+tally['equipment'],'scene_objects':len(self.obs),'actions':len(self.actions),'wiring_routes':46,'unverified_insertion_steps':['S04','S11'],'print_gauge':1,'optional_samples':7},'status':'PREVIEW_TWO_INSERTION_PATHS_UNVERIFIED','scope':'动画校核预览。S04/S11 锁骨装入路径仍待确认；实体取自 O22F7；轨迹为操作演示，不代替打印公差、弹舌变形、胶固化、线束活动和实测电气验收。'}
  
  for name in ['index.html','style.css','app.js']:
   if (R/'scripts/o22f7_animation_web'/name).is_file():shutil.copy2(R/'scripts/o22f7_animation_web'/name,OUT/name)
  put(OUT/'sequence.json',data);proof={'passed':True,'release_ready':False,'unresolved_steps':['S04','S11'],'revision':REV,'coverage':data['coverage'],'unique_introduction_count':len(self.seen),'hardware_counts':dict(metal),'unplanned_objects':[],'bind_roundtrip_max_abs':self.pose_error,'sequence_sha256':sha(OUT/'sequence.json'),'source_geometry_sha256':data['source_geometry_sha256'],'physical_assembly_tested':False,'collision_free_swept_volume_certified':False,'scope':data['scope']};put(OUT/'coverage.json',proof);print(json.dumps(proof,ensure_ascii=False),flush=True)
if __name__=='__main__':Build().run()
