"""Reseal the O22F7 package after a documentation-only assembly update."""
from pathlib import Path
import hashlib,json,re,shutil,zipfile
from urllib.parse import unquote,urlsplit
import o22f7_assembly_guide as g
from verify_o22f7_assembly_guide import verify


def release():
    report=verify();F=g.F;G=g.G
    before=g.read(g.WORK/'before.json')
    backup=g.WORK/'original_package.zip';assert g.sha(backup)==before['archive_sha256']
    release=g.read(F/'RELEASED.json');release.update(assembly_tutorial_revision=g.REV,assembly_tutorial='assembly/tutorials/assembly-o22/index.html',assembly_verification='verification/assembly_guide.json',manufacturing_files_unchanged_in_tutorial_update=True)
    g.put(F/'RELEASED.json',release)
    notes='''O22F7 拼装教程更新 · r2 · 2026-10-16

本次更新教程，14 个 PLA 3MF、150 类零件本体和支撑设计均保持原文件。
1. 当前 D01–D14 的实际盘图、193 件位置、26 步取件表已统一。
2. 7 件可选小样独立标识；185 件装机件与 1 件焊接量规各分配一次。
3. 三维查看器使用 185 个装机件的 O22F7 永久本体；26 张装配图同步更新。
4. P095 / P073 / P051 拆撑提示与当前修订对应，转角圆接头保留。
5. 电路 A01 等端口编号保持，与 D 系列打印盘明确区分。

打开 assembly/tutorials/assembly-o22/index.html，或从根目录 index.html 进入安装图解。
页面顶部应显示“O22F7 / ASSEMBLY r2”，正文标注“教程修订：2026-10-16 · r2”。
如果仍显示旧盘图，请刷新页面或从本包重新打开。

校核：193 个原生工程对象、186 个首次领用位置、958 件五金/磁铁分配、46 路电路映射、185 个当前本体网格及 26 张装配图。桌面、手机和三维交互检查通过。
'''
    g.write(F/'教程更新说明.txt',notes)
    p=F/'先读我.txt';s=p.read_text('utf-8-sig');line='教程已更新至 r2（2026-10-16）：当前 D01–D14 盘图、取件清单及三维装配图同步；详见 教程更新说明.txt。\n'
    if line not in s:s=s.replace('2026-10-16\n','2026-10-16\n'+line,1)
    g.write(p,s)
    for name in ['o22f7_assembly_guide.py','verify_o22f7_assembly_guide.py','o22f7_assembly_release.py','build_revo22_assembly_guide.py','check_o22f7_assembly_browser.js','check_o22f7_assembly_mobile.js','o22f7_viewer.py','o22f7_release.py']:
        shutil.copy2(g.R/'scripts'/name,F/'verification'/name)
    # Assembly-only inventory is replaced as well, so it cannot still certify the predecessor assets.
    files={p.relative_to(F/'assembly').as_posix():g.sha(p) for p in sorted((F/'assembly').rglob('*')) if p.is_file() and p.name!='archive_manifest.json' and '__pycache__' not in p.parts}
    g.put(F/'assembly/archive_manifest.json',{'schema':'POSEDOLL-O22F7-ASSEMBLY-ARCHIVE/2','revision':g.REV,'files':files,'current_native_projects':'../projects','hardware_access_during_packaging':False})
    bad=[];count=0
    for p in F.rglob('*.html'):
        for target in re.findall(r'(?:href|src)=[\"\']([^\"\']+)',p.read_text('utf-8-sig')):
            u=urlsplit(target)
            if u.scheme or '${' in target or not u.path:continue
            count+=1
            if not(p.parent/unquote(u.path)).is_file():bad.append((p.relative_to(F).as_posix(),target))
    assert not bad,bad
    g.put(F/'verification/asset_links.json',{'passed':True,'local_links_checked':count,'assembly_revision':g.REV})
    files=sorted(p for p in F.rglob('*') if p.is_file() and p.name!='SHA256SUMS.txt' and '__pycache__' not in p.parts)
    checks={p.relative_to(F).as_posix():g.sha(p) for p in files}
    g.write(F/'SHA256SUMS.txt',''.join(h+'  '+k+'\n' for k,h in checks.items()))
    target=g.B/'O22F7_PLA_完整打印包_20261016.zip';staged=g.WORK/'updated_package.zip'
    with zipfile.ZipFile(staged,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
        for p in files+[F/'SHA256SUMS.txt']:z.write(p,p.relative_to(F).as_posix())
    with zipfile.ZipFile(staged) as z:
        assert z.testzip() is None
        assert set(z.namelist())==set(checks)|{'SHA256SUMS.txt'}
        for k,h in checks.items():assert hashlib.sha256(z.read(k)).hexdigest()==h,k
    # Replace only the named release archive, after full verification; original stays recoverable.
    assert target.resolve().parent==g.B.resolve() and staged.resolve().is_relative_to(g.WORK.resolve())
    shutil.copy2(staged,target)
    h=g.sha(target);g.write(target.with_suffix('.zip.sha256'),h+'  '+target.name+'\n')
    result={'archive':str(target),'bytes':target.stat().st_size,'sha256':h,'files':len(checks)+1,'verified_every_archived_file':True,'complete':True,'assembly_revision':g.REV,'manufacturing_files_unchanged':len(before['mechanical_files']),'previous_archive_sha256':before['archive_sha256'],'previous_archive_backup':str(backup)}
    g.put(g.WORK/'delivery.json',result);g.put(g.WORK.parent/'delivery.json',result)
    print('DELIVERED',json.dumps(result,ensure_ascii=False),flush=True)

if __name__=='__main__':release()
