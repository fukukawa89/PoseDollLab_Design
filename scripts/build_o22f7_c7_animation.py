"""Full assembly sequence with the checked C7 split and bare-chest preassembly."""
import o22f7_animation as a
from o22f7_animation import *
C=WORK/'structure_revision';N=B/'O22F7_PLA_AssemblyRevision';NG=N/'assembly/tutorials/assembly-o22';a.G=NG;a.OUT=NG/'animation';a.REV='O22F7-animation-r4-C7-20261016'
stock=['M3_nut','M3_reaction_washer','inner_M4_wide','outer_M4_wide','spring_1','spring_2','front_M4_washer','shoulder_D4_L8_M3_thread6'];root='revision/clavicle_l.root';nut='revision/clavicle_l.join_nut';bolt='revision/clavicle_l.join_screw';left='frame/clavicle_l.protract_frame';right='frame/clavicle_r.protract_frame';prekeys=[root,left,right,nut,bolt]+[side+'/'+s for side in ['clavicle_l.protract','clavicle_r.protract'] for s in stock]
g=read(NG/'guide-data.json');original=read(G/'guide-data.json');g['steps'][1]['objects']=list(dict.fromkeys(original['steps'][1]['objects']+prekeys));put(NG/'guide-data.json',g)
class Revised(a.Build):
 def __init__(self):
  super().__init__(metadata=read(NG/'assembly_metadata_c7.json'));self.preparing=False;self.preassembled=False;self.early_raw={};self.precap_keys=[];self.precheck={r['name']:r for r in read(C/'W005_C7_preassembly_review.json')['checks']};self.stockcheck={r['name']:r for r in read(C/'W005_C7_stock_review.json')['checks']}
 def rigid(self,k,rec,frame,station,title,cue,new=True,reverse=True):
  path=rec['path'][::-1] if reverse else rec['path'];M=frame@np.array(rec['motion_frame']);receiver=['frame/chest'];detail='spring' if k.endswith(('spring_1','spring_2')) else 'part'
  return self.action('install' if new else 'transfer',title,cue,'看清转动和侧移的先后；零件落座后再继续。',new=[k] if new else [],moving=[k],path=[arr(station),arr(station)],focus=[k,*receiver],pose_path=path,motion_frame=arr(M.flatten()),motion_frame_inverse=arr(np.linalg.inv(M).flatten()),station=arr(station),duration=20 if len(path)>10 else 9,detail=detail,verified_path=rec['name'],path_sampling_mm=rec['sample_displacement_upper_bound_mm'])
 def install(self,k,*args,**kw):
  if k=='frame/chest' and self.chapter=='S02' and not self.preparing:
   off=np.array(kw['end']);self.preassembly(off);return self.transfer(['frame/chest',*prekeys],self.pre_station,off,'把预装胸架放入胸部核心','托住胸架和两侧锁骨，先移到核心上方，再沿轴线落座。',path=[arr(self.pre_station),arr(off+self.direction([0,0,260])),arr(off+self.direction([0,0,48])),arr(off)])
  return super().install(k,*args,**kw)
 def twist_preload(self,endname,frame,offset):
  start=len(self.actions);keys=super().twist_preload(endname,frame,offset)
  if self.chapter in ['S02','S03'] and endname=='P':
   delta=self.direction([0,175,0]);targets={self.mod+'/P_'+x for x in ['case_plus','adjust_nut','radial_pad']}
   for act in self.actions[start:]:
    if any(self.idx[k] in act['moving'] for k in targets):act['path']=arr(np.array(act['path'])+delta)
   for k in targets:self.offset[k]=self.offset[k]+delta
  return keys
 def preassembly(self,off):
  self.preparing=True;self.pre_station=off+self.direction([350,350,200]);station=self.pre_station;st=self.st;group=self.group
  jm=next(j for j in self.profile['joints'] if j['id']=='clavicle_l.protract');frame=self.frames['chest']@np.array(jm['parent_to_mount_mm']);self.group='胸架先在手边预装 · 左锁骨'
  super().install('frame/chest',dir=self.direction([0,0,1]),end=station,title='先拿出胸架 · 预装左右锁骨',cue='胸架还没有接到躯干。先在手边安装两侧连接件，留出绕入空间。',station=True)
  for k in stock[:3]:self.rigid('clavicle_l.protract/'+k,self.stockcheck['left_'+k],frame,station,'放入左侧 · '+self.name('clavicle_l.protract/'+k),'从敞开的背面放入，按特写核对内外顺序。')
  self.rigid(root,self.precheck['left_root_into_bare_chest'],frame,station,'绕入左锁骨根部 · W005A','先倾斜小根部进入胸架开口，再边转边回正，最后对准轴孔。')
  for k in stock[3:]:self.rigid('clavicle_l.protract/'+k,self.precheck['left_'+k],frame,station,'左侧摩擦组 · '+self.name('clavicle_l.protract/'+k),'沿折线绕开胸架后套到轴上。两片碟簧相向，轴肩螺钉调到能保持姿势。')
  self.rigid(root,self.precheck['park_left_root'],frame,station,'把左侧小根部暂时转开 20°','只轻转已装好的左侧根部，给右锁骨留出通道。',new=False,reverse=False)
  self.group='胸架先在手边预装 · 右锁骨'
  for k in stock[:3]:self.rigid('clavicle_r.protract/'+k,self.stockcheck['right_'+k],frame,station,'放入右侧 · '+self.name('clavicle_r.protract/'+k),'按内侧顺序放入，保持左侧小根部处于转开的位置。')
  self.rigid(right,self.precheck['right_frame_with_left_root_parked'],frame,station,'绕入右锁骨 · H008','按动画先斜着侧入，再转动、回收，最后对准轴孔。左侧长杆此时尚未安装。')
  for k in stock[3:]:self.rigid('clavicle_r.protract/'+k,self.stockcheck['right_'+k],frame,station,'右侧摩擦组 · '+self.name('clavicle_r.protract/'+k),'沿动画绕开骨架再落座；两片碟簧相向，最后调节轴肩螺钉。')
  self.rigid(root,self.stockcheck['left_root_return_after_right_stock'],frame,station,'把左锁骨根部转回','右侧固定后，把左侧根部转回动画显示的方向。',new=False,reverse=False)
  self.group='接上左锁骨长杆 · 新增一组 M2 紧固件'
  self.rigid(nut,self.precheck['nut_0'],frame,station,'放入接合螺母 · M2','先从侧面绕到接合座上方，再把六角螺母放进槽底。')
  self.rigid(left,self.precheck['left_distal_after_right'],frame,station,'接上左锁骨长杆 · W005B','沿定位键落入，把两块接合面贴合。不要把定位凸台压在槽外。')
  self.rigid(bolt,self.precheck['screw_0_entry'],frame,station,'拧入接合螺钉 · M2×6','从圆柱沉孔一侧穿入 M2×6 机螺钉，旋入刚放好的螺母。贴合后停止，不压坏 PLA。')
  self.check('检查左右锁骨预装','接合面没有缝，定位键已入槽；轻转两侧关节，确认平稳、不松脱。',focus=['frame/chest',*prekeys]);self.preparing=False;self.preassembled=True;self.group=group
 def action(self,*args,**kw):
  if self.chapter=='S02' and self.early_raw:kw.setdefault('raw_overrides',dict(self.early_raw))
  return super().action(*args,**kw)
 def set_raw(self,overrides):
  self.raw.update(overrides);ff,oo=kin.owners(self.raw);self.frames=ff;self.owners=oo
  for k in self.obs:
   mm=self.meta['meta'][k];M=ff[mm['body']] if mm['owner']=='rigid_frame' else oo[mm['module'],mm['owner']];self.mats[k]=M@np.array(self.bind[self.idx[k]]['local']).reshape(4,4)
 def preload_cap(self,off):
  route=next(r for r in self.g['routes'] if r['connector']=='A04');start=len(self.actions);seen=self.seen.copy();offset={k:v.copy() for k,v in self.offset.items()};group=self.group;super().magnetic_sensor(route);generated=self.actions[start:];self.actions=self.actions[:start];self.seen=seen;self.offset=offset
  for act in generated:
   if act['group'].endswith(' · 传感板'):break
   act['path']=arr(np.array(act['path'])+off);act['cue']='核心还在手边：'+act['cue'];self.actions.append(act)
   for i in act['new']:self.seen.add(list(self.obs)[i]);self.precap_keys.append(list(self.obs)[i])
   for i in act['moving']:self.offset[list(self.obs)[i]]=np.array(act['path'][-1])
  self.group=group
 def transfer(self,keys,start,end,title,cue='',path=None):
  if self.chapter=='S02' and title=='把核心放进近端半壳':
   self.preload_cap(np.array(start));keys=list(keys)+self.precap_keys
   self.action('pose','先把胸架转到安装角度','托住核心，让胸架连同左右锁骨缓慢转到图示角度，为接入腰架留出空间。','只转动胸部交叉轴；内部垫片保持落座。',focus=['frame/chest',*prekeys],duration=10,raw_transition={'chest/r2':[0,self.target['chest/r2']]})
   self.early_raw={'chest/r2':self.target['chest/r2']};self.set_raw(self.early_raw)
   path=read(C/'C7_chest_core_transfer_path.json')['entry_path'];cue='先绕到腰架螺钉外侧，再侧移回正，最后把转轴放入敞开的半壳。按动画的折线顺序移动。'
  return super().transfer(keys,start,end,title,cue,path)
 def magnetic_sensor(self,r):
  if r['connector']!='A04' or not self.precap_keys:return super().magnetic_sensor(r)
  start=len(self.actions);self.seen.difference_update(self.precap_keys);super().magnetic_sensor(r);generated=self.actions[start:];self.actions=self.actions[:start];sensor_start=next(i for i,act in enumerate(generated) if act['group'].endswith(' · 传感板'));self.actions.extend(generated[sensor_start:])
 def mechanical(self,s):
  if s['step'] not in ['S04','S11']:return super().mechanical(s)
  self.begin(s);parent='frame/'+s['parent'];child='frame/'+s['child'];self.group='已预装的锁骨 · 装传感器';self.check('确认胸架上的连接已完成','这处机械连接已经在 S02 预装；现在安装磁铁、传感板并整理软线。',focus=[parent,child]+([root] if s['step']=='S04' else []))
  for r in [r for r in self.g['routes'] if r['step']==s['step']]:self.magnetic_sensor(r)
  self.group='本节完成';self.action('pose','调整到图示姿态','托住两侧骨架，轻轻转到画面姿态，方便接着安装。','导线保留余量。',focus=[parent,child],duration=8,pose=True);self.check(s['title']+' · 本节检查','关节平稳，磁铁不松动，板边被固定，导线不拉紧。',focus=[parent,child],pose_final=True,overlay='complete');assert not(set(s['objects'])-self.seen)
 def run(self):
  super().run();p=a.OUT/'sequence.json';d=read(p);
  for i,act in enumerate(d['actions'],1):act['id']=f'A{i:04}'
  d['coverage']['unverified_insertion_steps']=[];d['status']='ASSEMBLY_REVISION_PENDING_FINAL_QA';d['scope']='186 件装机打印件、960 件五金及磁铁、46 块传感板逐件覆盖。锁骨采用 C7 分体预装与采样校核路线；轨迹演示不代替打印公差、强度、胶固化和实测电气验收。';d['actions'][-1].update(title='全部零件已装入 · 最后检查',cue='逐关节检查保持力和活动余量，逐路核对传感器读数，再确认背盒没有夹线。',check='只有你检查过实物的项目才勾选；观看动画不会自动通过验收。');put(p,d);v=read(a.OUT/'coverage.json');v.update(status=d['status'],coverage=d['coverage'],unresolved_steps=[],sequence_sha256=sha(p),scope=d['scope'],release_ready=False);put(a.OUT/'coverage.json',v)
if __name__=='__main__':Revised().run()
