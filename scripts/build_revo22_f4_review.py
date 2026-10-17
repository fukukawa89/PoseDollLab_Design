"""Inspect every original part; do not publish unqualified candidates."""
from pathlib import Path
import sys,json,hashlib,csv,gzip,base64,shutil,collections,numpy as np
R=Path(__file__).resolve().parents[1];B=R/'Hardware/PoseDoll44/bench/revO22';O=B/'a1mini_fins_v4';F3=B/'O22F3_Release';D=O/'review'
for d in [D,D/'geometry',D/'records',D/'evidence']:d.mkdir(parents=True,exist_ok=True)
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def dump(p,d):p.write_text(json.dumps(d,ensure_ascii=False,separators=(',',':')),encoding='utf8')
def mesh_export(pid,source,mode):
 n=np.load(source/'parts'/f'{pid}.npz');meshes={}
 for name,vk,fk in [('part','v','f'),('fin','fin_v','fin_f'),('teeth','teeth_v','teeth_f')]:
  if len(n[fk]):meshes[name]={'v':base64.b64encode(gzip.compress(np.array(n[vk],dtype='<f4').tobytes())).decode(),'f':base64.b64encode(gzip.compress(np.array(n[fk],dtype='<u4').tobytes())).decode()}
 vv=np.concatenate([n[k] for k in ['v','fin_v','teeth_v'] if len(n[k])]);data={'meshes':meshes,'bounds':np.r_[vv.min(0),vv.max(0)].tolist()}
 (D/'geometry'/f'{pid}_{mode}.js').write_text('window.AUDIT_MESHES["'+pid+'_'+mode+'"]='+json.dumps(data,separators=(',',':'))+';',encoding='utf8')
manifest=read(F3/'manifest.json');base={p['id']:p for p in read(O/'audit/baseline/all_parts.json')['parts']};gg={p['id']:p for p in read(F3/'verification/geometry_final.json')['parts']};assert len(base)==len(gg)==150
inventory=collections.defaultdict(list)
for p in manifest['plates']:
 for i in p['items']:inventory[i['id']].append({'plate':p['id'],'optional':p['optional'],'name':i['object_name'],'old_name':i.get('original_object_name',''),'item':i})
assert sum(not i['optional'] for items in inventory.values() for i in items)==186
ids=sorted(base);details={pid:{'id':pid,'part':base[pid]['part'],'geometry':base[pid],'baseline_support_geometry':gg[pid],'instances':[{k:v for k,v in x.items() if k!='item'} for x in inventory[pid]],'issues':{'Orca':[],'Bambu':[]},'candidate':None} for pid in ids}
for pid in ids:assert hashlib.sha256((F3/'reference/parts'/f'{pid}.npz').read_bytes()).hexdigest()==gg[pid]['npz_sha256'],pid
completed=[];unmapped=[]
def local_record(q,it,plate,kind,engine):
 bb=q['bounds_mm'];M=np.array(it['rotation_matrix']);t=np.array(it['translation_mm']);pts=(np.array([[x,y,q['z_mm']] for x in [bb[0],bb[2]] for y in [bb[1],bb[3]]])-t)@M
 out=dict(q);out.update(kind=kind,engine=engine,plate=plate,object_name=it['object_name'],bounds_mm=[float(pts[:,0].min()),float(pts[:,1].min()),float(pts[:,0].max()),float(pts[:,1].max())],z_mm=float(pts[:,2].mean()),plate_z_mm=q['z_mm']);return out
for engine in ['Orca','Bambu']:
 for p in manifest['plates']:
  fn=O/'audit/native_baseline'/engine/f"{p['id']}_O22F3_PLA_fins.json"
  if not fn.exists():continue
  native=read(fn);assert native.get('audit_schema')=='local-extrusion-v2-preserve-nested-islands';completed.append(engine+'/'+p['id'])
  for kind,arr in [('island',native['detached_bead_regions']),('span',native['unresolved_spans'])]:
   for q in arr:
    bb=q['bounds_mm'];cx=(bb[0]+bb[2])/2;cy=(bb[1]+bb[3])/2
    matches=[i for i in p['items'] if i['bounds_mm'][0]-.5<=cx<=i['bounds_mm'][3]+.5 and i['bounds_mm'][1]-.5<=cy<=i['bounds_mm'][4]+.5]
    if len(matches)!=1:unmapped.append({'engine':engine,'plate':p['id'],'kind':kind,'region':q,'matches':[i['id'] for i in matches]});continue
    it=matches[0];out=local_record(q,it,p['id'],kind,engine);out['optional']=p['optional'];details[it['id']]['issues'][engine].append(out)
choices=read(O/'native_review_choices.json');cand_geometry={q['id']:q for q in read(O/'candidate_geometry.json')};native_choices=[]
for choice in choices:
 pid=choice['id'];label=choice['label'];folder=O/'candidates'/pid/label;a=read(folder/f'{pid}.json');design=read(folder/'design'/f'{pid}.json');q={'label':label,'geometry':a,'constraints':cand_geometry[pid],'design':{'support_count':design['support_count'],'teeth_count':len(design['teeth']),'height_mm':design['new_height_mm'],'orientation':design['orientation']},'issues':[],'native_complete':False,'print_release_approved':False}
 fn=folder/'verification/local_extrusion.json'
 if fn.exists() and read(fn).get('audit_schema')=='local-extrusion-v2-preserve-nested-islands':
  native=read(fn);plate=read(folder/'verification/plate_manifest.json');it=plate['items'][0];q['native_complete']=True;native_choices.append(pid);q['native_sha256']=native['project_sha256']
  for kind,arr in [('island',native['detached_bead_regions']),('span',native['unresolved_spans'])]:q['issues'] += [local_record(x,it,plate['id'],kind,'Orca') for x in arr]
 details[pid]['candidate']=q
rows=[]
for pid in ids:
 d=details[pid];g=d['geometry'];d['geometry']={k:v for k,v in g.items() if k!='layers'}
 for engine in d['issues']:d['issues'][engine].sort(key=lambda q:-(q.get('area_mm2',0)*10+q.get('unsupported_footprint_diagonal_mm',0)))
 if d['candidate']:d['candidate']['issues'].sort(key=lambda q:-(q.get('area_mm2',0)*10+q.get('unsupported_footprint_diagonal_mm',0)))
 rr={'id':pid,'part':d['part'],'instances':sum(not i['optional'] for i in d['instances']),'plates':', '.join(x['name'].split(' ')[0] for x in d['instances'] if not x['optional']),'geometry_layers':g['flagged_layer_count'],'print_height_mm':g['height_mm'],'max_excess_mm2':g['max_local_excess_area_mm2'],'bed_occluded_area_mm2':g['critical_area_blocked_from_bed_mm2'],'roots_pass':g['all_fin_components_reach_bed'],'body_collision_mm3':g['fin_part_overlap_mm3']}
 for engine in ['Orca','Bambu']:
  issues=[x for x in d['issues'][engine] if not x['optional']];rr[engine+'_islands']=sum(x['kind']=='island' for x in issues);rr[engine+'_spans']=sum(x['kind']=='span' for x in issues);rr[engine+'_max_extent_mm']=max([x.get('unsupported_footprint_diagonal_mm',0) for x in issues],default=0)
 rr['review_required']=bool(g['flagged_layer_count'] or rr['Orca_spans']+rr['Bambu_spans']+rr['Orca_islands']+rr['Bambu_islands']);rr['priority']=2 if max(rr['Orca_max_extent_mm'],rr['Bambu_max_extent_mm'])>5 or rr['max_excess_mm2']>5 else 1 if rr['review_required'] else 0
 c=d['candidate'];rr.update(candidate_height_mm=c['geometry']['height_mm'] if c else None,candidate_label=c['label'] if c else None,candidate_native_complete=bool(c and c['native_complete']),candidate_max_excess_mm2=c['geometry']['max_local_excess_area_mm2'] if c else None,candidate_islands=sum(x['kind']=='island' for x in c['issues']) if c and c['native_complete'] else None,candidate_spans=sum(x['kind']=='span' for x in c['issues']) if c and c['native_complete'] else None)
 rr['disposition']='优先复核长跨空或大面积区域' if rr['priority']==2 else '需核对局部出丝和接触齿' if rr['priority']==1 else '本次检查未检出所列问题；尚未实物验证'
 if pid=='X046':rr['disposition']='已确认原内顶壁缺支撑；需调整'
 rows.append(rr);d['summary']=rr
 (D/'records'/f'{pid}.js').write_text('window.AUDIT_DETAILS["'+pid+'"]='+json.dumps(d,ensure_ascii=False,separators=(',',':'))+';',encoding='utf8');dump(D/'records'/f'{pid}.json',d)
 if not (D/'geometry'/f'{pid}_baseline.js').exists():mesh_export(pid,F3/'reference','baseline')
 if c and not (D/'geometry'/f'{pid}_candidate.js').exists():mesh_export(pid,O/'candidates'/pid/c['label'],'candidate')
complete=len(completed)==26 and len(native_choices)==102 and not unmapped
if '--complete' in sys.argv:assert complete,{'native_baseline':len(completed),'native_candidates':len(native_choices),'unmapped':len(unmapped)}
summary={'audit_schema':'local-extrusion-v2-preserve-nested-islands','inspection_complete':complete,'type_count':150,'main_instance_count':186,'optional_sample_instance_count':sum(i['optional'] for a in inventory.values() for i in a),'geometry_review_types':102,'native_review_types':sum(r['review_required'] for r in rows),'no_flags_types':sum(not r['review_required'] for r in rows),'completed_native_projects':len(completed),'expected_native_projects':26,'candidate_directions_built':408,'candidate_native_checked':len(native_choices),'source_bodies_changed':0,'source_geometry_hashes_verified':150,'unmapped_native_regions':unmapped,'F4_print_release_approved':False,'physical_print_tested':False,'physical_strength_simulation_performed':False,'rows':rows}
dump(D/'all_parts.json',summary);(D/'audit-data.js').write_text('window.AUDIT='+json.dumps(summary,ensure_ascii=False,separators=(',',':'))+';window.AUDIT_DETAILS={};window.AUDIT_MESHES={};',encoding='utf8')
with (D/'all_parts.csv').open('w',encoding='utf-8-sig',newline='') as f:
 w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
for name in ['index.html','review.js']:shutil.copy2(R/'.local/o22_f4_review_template'/name,D/name)
for name in ['F01_unsupported_ceiling.png','F01_ceiling_Z110.svg']:shutil.copy2(B/'F01_F3_audit'/name,D/'evidence'/name)
(D/'METHOD.txt').write_text("""O22 全零件检查说明
范围：F3 原文件 150 类零件、186 个主套实例、7 个额外样件；Orca、Bambu 各 13 个原生 3MF。
本体截面：0.20 mm 层高，与前层本体、鳍、齿的完整截面比较；前层仅外扩 0.20 mm；记录大于 0.02 mm² 的局部缺覆盖区。与侧壁相连的区域、被低层本体遮挡的支撑目标均保留。
实际 G-code：读取正向挤出、线宽和圆弧；圆弧弦误差不超过 0.025 mm。构造出丝宽度覆盖，独立检出大于 0.05 mm² 的孤立区域。连续路径不因切片特征标签改变而断开。非纯稀疏/间隙填充路径与前层出丝覆盖（仅外扩 0.025 mm）求差；记录长度大于 0.25 mm 的未覆盖段。
两端有前层锚点、包围框对角线不超过 3 mm 的小范围跨空，及单端长度不超过 0.5 mm 的边缘延伸，另行保留在原始报告，未当作实物合格。其余在页面显示为待处理。路径长度不等于直线桥跨度。
检查程序第二版修复了前层覆盖转换时漏掉嵌套空腔内独立实体的问题，已保留旧结果供审计，旧统计作废。控制样例覆盖单侧悬臂、两侧相连屋顶、孤立路径、标签连续性、45°逐层偏移，以及空腔内独立出丝覆盖。F01 Z110 mm 已知内顶壁缺支撑在新检查中仍被检出。
几何约束：主体不穿模，齿同时连接两侧实体，每个鳍从热盘起，高薄板需要横向加强。F3 原几何报告与 150 个当前模型 SHA256 逐一对应；候选另做约束检查。
本轮本体没有改形，装配几何和姿势范围保持原设计状态；这不代表重新认证了原设计全部机械性能。后续本体改动仍须检查配合保护区、其它装配件和姿势极限。
页面显示实际网格：蓝色本体、橙色鳍主体、黄色齿；红框为待处理出丝区域的包围盒，不是形变模拟。候选是实验结果，不是打印交付件。
未实物试打，未做热变形、熔融桥接或鳍板受力仿真。切片成功不等于可靠打印。
参考：Prusa 官方建模与桥接指南：
https://help.prusa3d.com/article/modeling-with-3d-printing-in-mind_164135
https://help.prusa3d.com/article/poor-bridging_1802
""",encoding='utf8')
print(json.dumps({k:v for k,v in summary.items() if k not in ['rows','unmapped_native_regions']},ensure_ascii=False));print('UNMAPPED',len(unmapped))

