"""Publish verified O22 PLA support projects and actual G-code previews.

No slicing or printer access. Publication is refused unless all 12 final
projects have current, matching slice/roundtrip/clearance evidence. There is
no force/skip-checks option. Run after the build, native re-open, and clearance
checks are complete. Preview .bin files remain local and are not in the ZIP.
"""
from __future__ import annotations
import argparse
from collections import Counter
from datetime import datetime, timezone, timedelta
import hashlib
import html
import json
from pathlib import Path
import sys
import xml.etree.ElementTree as ET
import zipfile
from o22_support_gcode import export_preview

ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'Hardware/PoseDoll44/bench/revO22'
OUT=BASE/'a1mini_supports'
WORK=ROOT/'.local/o22-easy-support'
Q='{http://schemas.microsoft.com/3dmanufacturing/core/2015/02}'
EXPECTED_IDS=['S00']+[f'A{i:02d}' for i in range(1,11)]+['T01']
ZIP_NAME='PoseDoll_O22_A1mini_PLA_Support_Projects.zip'
LOCAL_URL='http://127.0.0.1:8770/bench/revO22/a1mini_supports/index.html'


def sha(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda:stream.read(1024*1024),b''):h.update(block)
    return h.hexdigest()


def load(path):return json.loads(Path(path).read_text(encoding='utf-8-sig'))
def dump(path,value):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    text=json.dumps(value,ensure_ascii=False,indent=2)+'\n'
    temp=path.with_name(path.name+'.publishing');temp.write_text(text,encoding='utf8');temp.replace(path)

def require(condition,message,errors):
    if not condition:errors.append(message)


def native_info(path):
    with zipfile.ZipFile(path) as z:
        if z.testzip():raise ValueError('3MF ZIP CRC failure')
        settings=json.loads(z.read('Metadata/project_settings.config'))
        met=ET.fromstring(z.read('Metadata/model_settings.config'))
        model=ET.fromstring(z.read('3D/3dmodel.model'))
        application=next((n.text for n in model.findall(Q+'metadata') if n.get('name')=='Application'),None)
        names=[];normal_count=0;subtypes=Counter()
        for o in met.findall('object'):
            names.append(next((n.get('value') for n in o.findall('metadata') if n.get('key')=='name'),None))
            for part in o.findall('part'):
                subtype=part.get('subtype');subtypes[subtype]+=1
                normal_count+=int(subtype=='normal_part')
        return {'settings':settings,'application':application,'object_names':names,'normal_parts':normal_count,'subtypes':dict(subtypes),'build_instances':len(model.findall(Q+'build/'+Q+'item'))}


def preflight(base=BASE,out=OUT,work=WORK):
    errors=[];watched={};rows=[]
    def read(path):
        path=Path(path)
        if not path.is_file():errors.append('Missing '+str(path));return None
        watched[str(path.resolve())]=sha(path)
        try:return load(path)
        except Exception as exc:errors.append(f'{path}: {exc}');return None
    original_path=base/'a1mini/manifest.json';original=read(original_path)
    sample_path=work/'S00/manifest.json';sample=read(sample_path)
    protected_path=out/'design/all_protected_volumes.json';protected=read(protected_path)
    if original is None or sample is None or protected is None:return {'status':'FAIL','errors':errors},[],watched
    mapping={p['id']:p for p in original['plates']};mapping['S00']=sample
    require(set(mapping)==set(EXPECTED_IDS),'Plate set must be S00,A01..A10,T01',errors)
    require(sample.get('count')==7 and len(sample.get('items',[]))==7,'S00 must contain the final 7 actual trial pieces',errors)
    main_items=[i for p in original['plates'] if p['id'].startswith('A') for i in p['items']]
    main_parts=[i['part'] for i in main_items]
    require(len(main_items)==186 and len(set(main_parts))==186,'Main plates must contain exactly 186 unique assembly parts (185 doll + 1 gauge)',errors)
    by_part={x['part']:x for x in protected.get('objects',[])}
    observed_main=[]
    for pid in EXPECTED_IDS:
        p=mapping.get(pid)
        if p is None:continue
        project=out/'projects'/f"{pid}_{p['slug']}_PLA_supports.3mf"
        if not project.is_file():errors.append('Missing '+str(project));continue
        actual_sha=sha(project);watched[str(project.resolve())]=actual_sha
        validation_path=out/'verification'/f'{pid}.json';roundtrip_path=out/'verification'/f'{pid}_roundtrip.json';clearance_path=out/'verification'/f'{pid}_clearance.json';decisions_path=out/'verification'/f'{pid}_decisions.json'
        v=read(validation_path);rt=read(roundtrip_path);clearance=read(clearance_path);decisions=read(decisions_path)
        if any(x is None for x in (v,rt,clearance,decisions)):continue
        require(v.get('sha256')==actual_sha,f'{pid}: slice verification is stale',errors)
        nr=v.get('native_roundtrip',{})
        require(nr.get('status')=='PASS' and nr.get('actual_sha256')==actual_sha,f'{pid}: input-to-native preservation must PASS with current project SHA',errors)
        reopened=rt.get('native_roundtrip',{})
        require(reopened.get('status')=='PASS' and reopened.get('reference_sha256')==actual_sha,f'{pid}: saved-project re-open evidence is absent/stale/not PASS',errors)
        require(reopened.get('actual_sha256')==rt.get('sha256'),f'{pid}: roundtrip result hash does not match preservation evidence',errors)
        reopened_path=work/pid/'roundtrip/reopened.3mf'
        if reopened_path.is_file():
            watched[str(reopened_path.resolve())]=sha(reopened_path)
            require(watched[str(reopened_path.resolve())]==rt.get('sha256'),f'{pid}: reopened project bytes differ from evidence',errors)
        else:errors.append(f'{pid}: missing actual reopened.3mf for verification')
        for doc,label in [(v,'initial'),(rt,'reopened')]:
            sr=doc.get('slice_result',{})
            require(sr.get('return_code')==0,f'{pid}: {label} slicer did not succeed',errors)
            require(not any(doc.get('mesh_repairs',{}).values()),f'{pid}: {label} mesh repairs occurred',errors)
            require(doc.get('objects')==p['count'],f'{pid}: {label} object count differs from placement manifest',errors)
            require(len(sr.get('sliced_plates',[]))==1,f'{pid}: expected exactly one sliced plate',errors)
            for sp in sr.get('sliced_plates',[]):require(not sp.get('warning_message','').strip(),f'{pid}: {label} slicer warning: '+sp.get('warning_message',''),errors)
        require(clearance.get('source_sha256')==actual_sha,f'{pid}: clearance report is stale',errors)
        require(clearance.get('protected_volumes_sha256')==watched[str(protected_path.resolve())],f'{pid}: protection-core definitions changed after clearance audit',errors)
        expected_cores=sum(len(by_part[i['part']].get('volumes',[])) for i in p['items'] if i['part'] in by_part)
        require(clearance.get('checked_feature_volumes')==expected_cores,f'{pid}: clearance audit did not cover all declared cores',errors)
        expected_status='CLEAR_FOR_DECLARED_CORES' if expected_cores else 'NO_PROTECTED_FEATURES_DECLARED'
        require(clearance.get('status')==expected_status,f'{pid}: clearance status {clearance.get("status")}',errors)
        require(clearance.get('bead_midline_core_segment_count')==0 and clearance.get('conservative_bead_envelope_segment_count')==0 and clearance.get('finding_count')==0,f'{pid}: support/brim enters a protected core',errors)
        require(set(clearance.get('roles_checked',[]))=={1,2,3,4},f'{pid}: clearance audit must include support/interface/transition AND brim',errors)
        if pid=='S00':require(clearance.get('placement_manifest_sha256')==watched[str(sample_path.resolve())],'S00: clearance placement manifest mismatch',errors)
        try:info=native_info(project)
        except Exception as exc:errors.append(f'{pid}: invalid native archive: {exc}');continue
        names=[i['object_name'] for i in p['items']]
        require(Counter(info['object_names'])==Counter(names),f'{pid}: native object names/instances differ from expected parts',errors)
        require(info['normal_parts']==p['count'] and info['build_instances']==p['count'],f'{pid}: normal-part/build-instance count mismatch',errors)
        require(info['application']=='BambuStudio-02.08.02.61',f'{pid}: unexpected generator version',errors)
        setting=info['settings']
        for key,want in {'printer_model':'Bambu Lab A1 mini','nozzle_diameter':['0.4'],'filament_settings_id':['Generic PLA @BBL A1M'],'support_type':'normal(auto)','support_style':'snug','raft_first_layer_expansion':'0','support_object_first_layer_gap':'0.45','print_sequence':'by layer'}.items():require(setting.get(key)==want,f'{pid}: native {key} is not {want}',errors)
        require(Counter(i['object_name'] for i in decisions)==Counter(names),f'{pid}: support decisions do not cover each object exactly once',errors)
        decisions_by_name={i['object_name']:i for i in decisions}
        for item in p['items']:
            src=base/item['source_3mf'];key=str(src.resolve())
            if not src.is_file():errors.append(f'{pid}: missing source {src}');continue
            watched.setdefault(key,sha(src))
            require(watched[key]==item['source_sha256'],f'{pid}: source geometry SHA changed for {item["id"]}',errors)
            decision=decisions_by_name.get(item['object_name'],{})
            require(decision.get('source_sha256')==item['source_sha256'] and decision.get('part')==item['part'],f'{pid}: decision source mismatch for {item["object_name"]}',errors)
            require(decision.get('painted_enforcer_faces')==0,f'{pid}: forced support paint remains',errors)
        if pid.startswith('A'):observed_main.extend(i['part'] for i in decisions)
        rows.append({'plate':p,'project':project,'project_sha256':actual_sha,'validation':v,'roundtrip':rt,'clearance':clearance,'info':info,'evidence_files':[validation_path,roundtrip_path,clearance_path,decisions_path]})
    require(Counter(observed_main)==Counter(main_parts),'Main native/decision coverage must match all 186 original unique parts exactly',errors)
    require((out/'README.zh-CN.md').is_file(),'Printing/removal README is missing',errors)
    report={'schema':'POSEDOLL-O22-SUPPORT-PUBLISH-PREFLIGHT/1','status':'PASS' if not errors else 'FAIL','errors':errors,'expected_projects':12,'verified_projects':len(rows),'main_normal_part_count':len(observed_main),'main_unique_parts':len(set(observed_main)),'declared_clearance_policy':'No midline or conservative bead-envelope hits for every declared core; brim included; no waived findings.'}
    return report,rows,watched


def publish(*,base=BASE,out=OUT,work=WORK,check_only=False):
    pre,rows,watched=preflight(base,out,work)
    dump(out/'verification/publish_preflight.json',pre)
    if pre['status']!='PASS':
        raise RuntimeError('Publication refused:\n'+'\n'.join(pre['errors']))
    if check_only:return pre
    created=datetime.now(timezone(timedelta(hours=8))).isoformat(timespec='seconds')
    manifest={'schema':'POSEDOLL-O22-A1MINI-SUPPORT-PROJECTS/1','title':'O22 · A1 mini 单材料 PLA 支撑工程','status':'DIGITAL_CHECKS_PASS_PHYSICAL_TRIAL_REQUIRED','generated_at':created,'printer':'Bambu Lab A1 mini','nozzle_mm':.4,'material':'Generic PLA','single_material':True,'main_pieces':186,'on_doll_pieces':185,'assembly_gauge_pieces':1,'trial_pieces':7,'optional_coupon_pieces':2,'physical_print_tested':False,'local_preview_url':LOCAL_URL,'package':'../'+ZIP_NAME,'readme':'README.zh-CN.md','notes':['先打印 S00 七件试盘，检查支撑拆除、悬空底面与五金配合，再打印 A01–A10。','所有工程均保存了机器、PLA 和逐零件支撑设置；请作为项目打开。','路径检查针对已经建模的孔槽保护核心，不等于所有空腔或实物拆除力已经验证。'],'plates':[]}
    verification={'schema':'POSEDOLL-O22-SUPPORT-RELEASE-VERIFICATION/1','status':'PASS','generated_at':created,'preflight':pre,'physical_print_tested':False,'plates':[]}
    for row in rows:
        p=row['plate'];pid=p['id'];print(f'Preview {pid} from verified final native project',flush=True)
        dst=out/'previews'/f'{pid}.json';preview=export_preview(row['project'],dst)
        if preview['out_of_bed_segment_count']!=0:raise RuntimeError(f'{pid}: exported print paths exceed bed; publication stopped')
        if any('estimated_mass_g' not in c for c in preview['classes']):raise RuntimeError(f'{pid}: G-code lacks filament diameter/density for class mass estimates')
        sr=row['validation']['slice_result']['sliced_plates'][0]
        grams=sum(x['total_used_g'] for x in sr['filaments'])
        sec=float(sr['total_predication']);support_g=sum(c.get('estimated_mass_g',0) for c in preview['classes'][1:4]);model_g=preview['classes'][0].get('estimated_mass_g',0);brim_g=preview['classes'][4].get('estimated_mass_g',0)
        plate={'id':pid,'title':p['title'],'slug':p['slug'],'file':row['project'].relative_to(out).as_posix(),'project_sha256':row['project_sha256'],'project_bytes':row['project'].stat().st_size,'preview':dst.relative_to(out).as_posix(),'preview_json_sha256':sha(dst),'preview_binary_sha256':preview['binary']['sha256'],'count':p['count'],'normal_part_count':row['info']['normal_parts'],'optional':bool(p.get('optional')),'trial':pid=='S00','slicer_estimated_print_seconds':round(sec,3),'slicer_estimated_filament_g':round(grams,4),'path_estimated_support_g':round(support_g,4),'path_estimated_model_g':round(model_g,4),'path_estimated_brim_g':round(brim_g,4),'layers':len(preview['layers']),'gcode_sha256':preview['gcode_sha256'],'clearance_cores_checked':row['clearance']['checked_feature_volumes'],'items':[{'id':i['id'],'part':i['part'],'number':i['number'],'object_name':i['object_name'],'source_3mf':i['source_3mf'],'source_sha256':i['source_sha256']} for i in p['items']]}
        manifest['plates'].append(plate)
        verification['plates'].append({'id':pid,'project_sha256':row['project_sha256'],'normal_parts':p['count'],'source_hashes_match':True,'native_initial_preservation':'PASS','native_saved_project_reopen':'PASS','clearance_status':row['clearance']['status'],'clearance_cores_checked':row['clearance']['checked_feature_volumes'],'clearance_midline_hits':0,'clearance_envelope_hits':0,'brim_included':True,'out_of_bed_path_segments':0,'preview_segments':preview['segment_count'],'evidence':{x.name:sha(x) for x in row['evidence_files']}})
    # Catch races: no project, geometry, protection definition or evidence may
    # change between preflight and publication of its derived previews.
    changed=[p for p,h in watched.items() if not Path(p).is_file() or sha(p)!=h]
    if changed:raise RuntimeError('Inputs changed during preview export; rerun after builds finish:\n'+'\n'.join(changed))
    main=[p for p in manifest['plates'] if p['id'].startswith('A')]
    data_hashes={p['id']:{'project':p['project_sha256'],'gcode':p['gcode_sha256'],'preview_json':p['preview_json_sha256'],'preview_binary':p['preview_binary_sha256']} for p in manifest['plates']}
    summary={'schema':'POSEDOLL-O22-SUPPORT-RELEASE-SUMMARY/1','status':'PASS','generated_at':created,'projects':12,'main_plates':10,'main_normal_part_instances':sum(p['normal_part_count'] for p in main),'main_unique_assembly_parts':186,'on_doll_parts':185,'gauge_parts':1,'trial_parts':7,'optional_coupon_parts':2,'main_estimated_print_seconds':round(sum(p['slicer_estimated_print_seconds'] for p in main),3),'main_slicer_estimated_filament_g':round(sum(p['slicer_estimated_filament_g'] for p in main),4),'main_path_estimated_model_g':round(sum(p['path_estimated_model_g'] for p in main),4),'main_path_estimated_support_g':round(sum(p['path_estimated_support_g'] for p in main),4),'main_path_estimated_brim_g':round(sum(p['path_estimated_brim_g'] for p in main),4),'estimates_scope':'Printer time and total filament from native slicer; model/support/brim mass from extrusion paths with slicer filament diameter/density. Startup cleaning is excluded from path classes.','physical_print_tested':False,'data_hashes':data_hashes,'data_sha256':hashlib.sha256(json.dumps(data_hashes,sort_keys=True,separators=(',',':')).encode()).hexdigest()}
    verification['watched_input_hashes']={str(Path(k).relative_to(ROOT)) if Path(k).is_relative_to(ROOT) else k:v for k,v in watched.items()}
    dump(out/'manifest.json',manifest);dump(out/'summary.json',summary);dump(out/'verification/release.json',verification)
    table=['| 打印盘 | 内容 | 件数 | 预计用时 | 切片估算耗材 | 工程 |','|---|---|---:|---:|---:|---|']
    for p in manifest['plates']:
        minutes=round(p['slicer_estimated_print_seconds']/60);table.append(f"| {p['id']} | {p['title']} | {p['count']} | {minutes//60}时{minutes%60:02d}分 | {p['slicer_estimated_filament_g']:.1f} g | [{Path(p['file']).name}]({p['file']}) |")
    package_readme='# O22 A1 mini PLA 支撑工程包\n\n请先阅读 [打印与拆除说明](README.zh-CN.md)，先试印 S00。主盘 A01–A10 共 186 件（185 件整机零件 + 1 件量规）；S00 七件试印件和 T01 两件可选小样单独计算。\n\n'+'\n'.join(table)+'\n\n时间和耗材为切片估算，未做实物打印。所有工程包含原生打印配置和实际切片，可直接在 Bambu Studio 中预览。\n\n包内不附大体积的网页路径二进制。原工作区的本地交互预览入口：['+LOCAL_URL+']('+LOCAL_URL+')。本地服务运行时可访问；这个地址不是公网网站。离线打开 .3mf 工程仍可在 Bambu Studio 内看全部支撑与路径。manifest.json 中 preview 字段供完整本地工作区使用。\n\nverification/ 保存原生往返、实际路径与孔槽保护核心检查；design/ 包含保护区域定义。检查范围仅限声明的保护核心，不证明实物一定易拆。\n'
    (out/'PACKAGE_README.zh-CN.md').write_text(package_readme,encoding='utf8')
    table_html='<div class="table-wrap"><table><thead><tr><th>打印盘</th><th>内容</th><th>件数</th><th>预计用时</th><th>估算耗材</th><th>工程</th></tr></thead><tbody>'
    for p in manifest['plates']:
        minutes=round(p['slicer_estimated_print_seconds']/60);table_html+=f'<tr><td><a href="?plate={p["id"]}">{p["id"]}</a></td><td>{html.escape(p["title"])}</td><td>{p["count"]}</td><td>{minutes//60}时{minutes%60:02d}分</td><td>{p["slicer_estimated_filament_g"]:.1f} g</td><td><a href="{html.escape(p["file"])}" download>下载</a></td></tr>'
    table_html+='</tbody></table></div>'
    index=out/'index.html';text=index.read_text(encoding='utf-8-sig');start='<!-- SUPPORT_PROJECT_INDEX_START -->';end='<!-- SUPPORT_PROJECT_INDEX_END -->'
    block=start+'\n<section class="notes"><p><a class="button" href="?plate=S00">先查看 S00 七件试盘</a>　<a href="README.zh-CN.md">打印与拆除说明</a>　<a href="../'+ZIP_NAME+'" download>下载完整工程包</a></p><details><summary>展开全部 12 个工程的用时与耗材</summary>'+table_html+'</details></section>\n'+end
    if start in text:
        before,rest=text.split(start,1);_,after=rest.split(end,1);text=before+block+after
    else:text=text.replace('<main>',block+'\n<main>',1)
    index.write_text(text,encoding='utf8')
    files=[out/'README.zh-CN.md',out/'PACKAGE_README.zh-CN.md',out/'manifest.json',out/'summary.json']
    files.extend(row['project'] for row in rows)
    files.extend(x for row in rows for x in row['evidence_files'])
    files.extend([out/'verification/publish_preflight.json',out/'verification/release.json'])
    files.extend(x for x in (out/'verification').glob('*.json') if x.name.endswith('_roundtrip_clearance.json') or x.name in {'A02_local_model_continuity.json','original_packages_unchanged.json'})
    files.extend(x for x in (out/'design').rglob('*') if x.is_file() and x.suffix.lower() in {'.json','.md','.svg'})
    files.extend(x for x in out.rglob('*.svg') if 'design' not in x.relative_to(out).parts)
    archive=base/ZIP_NAME;temp=archive.with_suffix('.zip.publishing');seen=set();prefix='PoseDoll_O22_A1mini_PLA_Support_Projects/'
    with zipfile.ZipFile(temp,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
        for file in sorted(files):
            member=prefix+file.relative_to(out).as_posix()
            if member not in seen:z.write(file,member);seen.add(member)
    with zipfile.ZipFile(temp) as z:
        if z.testzip():raise RuntimeError('Package CRC check failed')
        if any(n.endswith('.bin') for n in z.namelist()):raise RuntimeError('Preview binary unexpectedly included')
        if len([n for n in z.namelist() if '/projects/' in n and n.endswith('.3mf')])!=12:raise RuntimeError('Package must contain exactly 12 native projects')
    temp.replace(archive)
    package={'file':archive.name,'sha256':sha(archive),'bytes':archive.stat().st_size,'members':len(seen),'preview_binary_included':False,'data_sha256':summary['data_sha256']}
    dump(out/'package.json',package)
    print(json.dumps({'status':'PASS','summary':summary,'package':package},ensure_ascii=False,indent=2),flush=True)
    return summary


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--check-only',action='store_true',help='Validate all final evidence without exporting previews or packaging');a=p.parse_args()
    try:publish(check_only=a.check_only)
    except (ValueError,RuntimeError,KeyError,OSError) as exc:print(str(exc),file=sys.stderr);raise SystemExit(1)

if __name__=='__main__':main()
