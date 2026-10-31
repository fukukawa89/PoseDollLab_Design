"""Finalize labels and evidence without changing verified geometry or motion."""
from o22f7_animation import *
from build_revo22_assembly import b
import o22f7_native as h, copy, collections
C=WORK/'structure_revision';N=B/'O22F7_PLA_AssemblyRevision';NG=N/'assembly/tutorials/assembly-o22';A=NG/'animation';V=N/'verification/C7';H=N/'verification/prior_release'
def canonical(d):return hashlib.sha256(json.dumps(d,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()).hexdigest()
def payload(d):return {k:v for k,v in d.items() if k not in ['status','source_guide_sha256']}
def preserve(p):
 dst=H/p.relative_to(N);dst.parent.mkdir(parents=True,exist_ok=True)
 if not dst.exists():shutil.copy2(p,dst)
seq=read(A/'sequence.json');oldseq=sha(A/'sequence.json');motion=canonical(payload(seq));g=read(NG/'guide-data.json');oldguide=sha(NG/'guide-data.json');m=read(N/'manifest.json');sc=read(NG/'scene.json');obs=sc['objects']
assert read(C/'C7_package_verification.json')['passed'] and read(C/'C7_browser_review.json')['passed']
assert sha(C/'W005_C7.npz')=='996d9c94822f946556d336e1119ffb3783e31fbf1206f6b61eaf46d00047e2f1'
for p in [A/'sequence.json',NG/'guide-data.json',N/'manifest.json']:preserve(p)
newinfo={}
for pid in ['W005A','W005B']:
 n=np.load(N/f'parts/{pid}.npz');q=copy.deepcopy(next(q for q in g['instances'] if q['id']==pid));verts=np.concatenate([n[k] for k in ['v','fin_v','teeth_v']]);placed=verts@np.array(q['rotation_matrix']).T+q['translation_mm'];body=h.solid(n['v'],n['f']);r=next(r for r in m['rows'] if r['id']==pid)
 q['prior_to_split_source']={k:q.pop(k) for k in ['source_sha256','source_volume_mm3','placed_volume_mm3','triangles'] if k in q}
 q.update(source_npz_sha256=sha(N/f'parts/{pid}.npz'),body_volume_mm3=float(body.volume()),body_triangles=len(n['f']),bounds_mm=np.r_[placed.min(0),placed.max(0)].tolist(),fins_bounds_mm=np.r_[placed.min(0),placed.max(0)].tolist(),local_bounds_mm=np.r_[verts.min(0),verts.max(0)].tolist(),size=(verts.max(0)-verts.min(0)).tolist(),previous_f4_address='C03-02（拆分来源）',original_address='A04-02（拆分来源）');newinfo[pid]=q
 r.pop('removed_mm3',None);r.pop('added_mm3',None);r['body_comparison_scope']='W005 replaced by two individually identified split pieces; whole-parent zero volume deltas are not applicable.'
 dp=N/f'design/{pid}.json';preserve(dp);d=read(dp)
 if 'f7_verification' in d:d['historical_parent_W005_verification']=d.pop('f7_verification')
 d.update(structural_revision='C7',native_pending=False,fit_and_pose_pending=False,support_count=r['fin_count'],support_volume_mm3=r['support_volume_mm3'],npz_sha256=r['npz_sha256'],current_verification='verification/C7/C7_print_geometry_and_removal.json',current_native_verification='verification/plates/'+q['plate']+'/support_paths.json',physical_print_tested=False,physical_assembly_tested=False,strength_or_fatigue_tested=False);put(dp,d)
first={};bychapter={}
for ch in seq['chapters']:
 introduced=[i for a in seq['actions'][ch['start']:ch['end']] for i in a['new']];bychapter[ch['id']]=introduced
 for i in introduced:
  if obs[i].get('print_id'):first[obs[i]['label']]=ch['id']
def refresh(obj):
 if isinstance(obj,dict):
  if obj.get('id') in newinfo and 'address' in obj:
   for k in ['source_sha256','source_volume_mm3','placed_volume_mm3','triangles']:obj.pop(k,None)
   obj.update(copy.deepcopy(newinfo[obj['id']]))
  if obj.get('part') in first and 'first_use' in obj:obj['first_use']=first[obj['part']]
  for v in list(obj.values()):refresh(v)
 elif isinstance(obj,list):
  for v in obj:refresh(v)
refresh(g);refresh(m);g['first_use'].update(first)
for step in g['steps']:
 ii=bychapter[step['step']];prints=[obs[i]['label'] for i in ii if obs[i].get('print_id')];step['new_parts']=prints;step['parts']=list(dict.fromkeys(step['parts']+prints));step['objects']=[obs[i]['label'] for i in ii];step['stock']=dict(collections.Counter(obs[i]['sku'] for i in ii if obs[i]['role']=='metal'));step['plates']=sorted({g['parts'][label]['plate'] for label in prints})
g['original_plate_manifest_sha256']=g.pop('source_plate_manifest_sha256',None);g['native_project_sha256']={p['project']:sha(N/p['project']) for p in m['plates']};g['inventory_source']='Current projects listed in this document; original manifest hash is provenance only.'
g['main_instances']=187;g['on_doll_instances']=186;g['revision']=seq['revision'];put(NG/'guide-data.json',g)
seq['source_guide_sha256']=sha(NG/'guide-data.json');seq['status']='RELEASED_DIGITAL_CHECKS_PASSED';assert canonical(payload(seq))==motion;put(A/'sequence.json',seq);newseq=sha(A/'sequence.json')
remap={'verified_sequence_sha256_before_metadata_update':oldseq,'sequence_sha256':newseq,'mechanical_action_payload_sha256':motion,'metadata_only_changes':['status','source_guide_sha256'],'mechanical_action_payload_unchanged':True}
for name in ['W005_C7_sequence_interfaces.json','C7_chest_rotation_review.json']:
 p=C/name;d=read(p);assert d['sequence_sha256']==oldseq;d.update(remap);put(p,d);shutil.copy2(p,V/name)
put(C/'C7_release_metadata_transition.json',dict(remap,old_guide_sha256=oldguide,new_guide_sha256=sha(NG/'guide-data.json'),guide_changes='Current plate hashes, split-piece descriptive measurements, and chapter inventory derived from unchanged animation actions. No geometry, trajectories, object transforms, electrical routes or BOM changed.'))
cv=read(A/'coverage.json');assert cv['passed'] and not cv['unresolved_steps'];cv.update(sequence_sha256=newseq,status=seq['status'],release_ready=True);put(A/'coverage.json',cv)
m.update(complete=True,status='RELEASED_DIGITAL_CHECKS_PASSED');put(N/'manifest.json',m)
for row in m['rows']:
 rp=N/f"records/{row['id']}.json";d=read(rp);d['summary']=row;put(rp,d);write(N/f"records/{row['id']}.js",'window.AUDIT_DETAILS['+json.dumps(row['id'])+']='+json.dumps(row,ensure_ascii=False,separators=(',',':'))+';')
write(N/'audit-data.js','window.AUDIT='+json.dumps(m,ensure_ascii=False,separators=(',',':'))+';window.AUDIT_DETAILS={};window.AUDIT_MESHES={};')
s=(N/'index.html').read_text('utf8').replace('</style>','[hidden]{display:none!important}</style>',1).replace('26 步取件清单','26 章取件清单');write(N/'index.html',s)
s=(N/'viewer.js').read_text('utf8').replace('O22F7 PLA 最终版：15 盘','O22F7 PLA 装配修订版 r4：15 盘').replace('17 类保留孔内可拆承托；','17 类保留孔内可拆承托（含 W005B 新接合孔的一根细齿）；');write(N/'viewer.js',s)
for rel in ['ASSEMBLY.zh-CN.md','verification.json','animation/verification.json','animation/browser-review.json','animation/path-review.json','animation/预览说明.txt']:
 p=NG/rel
 if p.exists():preserve(p)
for rel in ['summary.json','assembly_animation.json','assembly_guide.json','asset_links.json']:
 p=N/'verification'/rel
 if p.exists():preserve(p)
write(NG/'ASSEMBLY.zh-CN.md','''# O22F7 PLA 装配修订版 r4

从 [逐件拼装动画](animation/index.html) 开始，默认每个动作播放后暂停。支持慢放、重播、查看内部、按零件编号搜索和查看所在打印盘。

本版共 26 章、1658 个动作，覆盖 186 件装机打印件、960 件五金与磁铁、46 块传感板及接线。支撑清理完成后开始，不包含拆支撑动画；电路板以工厂预焊并检查好的状态开始。

[当前 D01–D15 取件清单](index.html#plates) 与本包打印文件对应。A01–A14、B01–B16、C01–C16 是电路端口，与打印盘编号不同。

原 W005 拆为 D15-01 / W005A 根部和 D05-01 / W005B 长杆；D07-02 / H008 保持原件。额外准备 1 枚 M2×6 内六角圆柱头机螺钉及 1 枚 M2 六角螺母。按 S02 先预装左右锁骨，S04 / S11 再装传感器。W005B 接合沉孔边缘的细齿需清理后再装螺钉。

按动画完成传感器、线束、中央板、分段通电检查，最后合上背盒。7 件可选小样和 1 件工厂焊接量规不装到人偶上。

数字检查已完成；装配路径检查采用列明的采样范围，尚未实物试打、试装或验证强度疲劳。观看动画不会替代或自动勾选实物验收。

[当前检查记录](verification.json) · [电路生产资料](engineering-files.html)
''')
write(A/'预览说明.txt','本目录为 O22F7 PLA 装配修订版 r4 的完整逐件动画。26 章、1658 动作；186 件装机打印件、960 件五金与磁铁、46 路电路。左右锁骨关键安装路径已按记录完成数字采样检查，无遗留的未完成动作。\n请双击包根目录“打开逐件拼装动画.cmd”。尚未实物试打、试装、强度或疲劳验证。\n')
p=NG/'engineering-files.html';s=p.read_text('utf8').replace('D01–D14','D01–D15').replace('index.html#electronics','animation/index.html?step=S26');write(p,s)
pathreview={'status':'LISTED_SAMPLED_PATH_CHECKS_PASSED','revision':seq['revision'],'sequence_sha256':newseq,'unresolved_steps':[],'critical_interface_path_checks':14,'sampling_mm':.25,'chest_rotation_samples':85,'chest_rotation_sampling_deg':.5,'whole_device_pose_comparisons':414,'full_swept_volume_verified':False,'physical_assembly_tested':False,'scope':'Current C7 clavicle preassembly, chest/head interfaces, early chest rotation and added-interference pose comparisons are checked over listed samples. Flexible cable routes, print tolerance, strength and all continuous assembly sweeps are not certified.','current_evidence':'../../../../verification/C7/'};put(A/'path-review.json',pathreview)
print('FINAL_METADATA',newseq,'motion_unchanged',motion,flush=True)
