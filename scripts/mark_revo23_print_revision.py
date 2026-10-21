"""Prevent using a superseded print package while connection review is ongoing."""
from revo23_endfaces import *

initialize()
path=B/'DELIVERY.json';data=read(path)
data['connection_end_face_review']={'status':'under_revision','candidate_revision':HREV,
    'reason':'G verification omitted full native-end seating; H is under repair and not released.',
    'printing':'Pause new prints from G until the repaired package is released.'}
data['manufacturing_release']=False;put(path,data)
backup=GHISTORY/'print_notice_original';backup.mkdir(exist_ok=True)
for name in ('index.html','README.zh-CN.md'):
    path=B/'a1mini_pla_optimized'/name
    if not path.exists():continue
    if not (backup/name).exists():shutil.copy2(path,backup/name)
    content=path.read_text(encoding='utf-8')
    message='结构复查进行中：G 版有部分连接端面未坐实，暂缓使用此包开始新的打印。正在修订连接及对应打印文件。'
    if name.endswith('.html'):
        if 'O23H_CONNECTION_REVIEW' not in content:
            content=content.replace('<body>','<body><!-- O23H_CONNECTION_REVIEW --><div style="padding:20px;background:#fff1b8;color:#432d00;font-weight:bold">'+message+'</div>',1)
    elif not content.startswith('> 结构复查进行中'):
        content='> '+message+'\n\n'+content
    path.write_text(content,encoding='utf-8')
put(HROOT/'WORK_IN_PROGRESS.json',dict(status='working_not_released',baseline_revision=GREV,candidate_revision=HREV,
    remaining=['native end repair','functional apertures','full regression','export and print package'],
    original_rods=44,candidate_rods=42))
print('G print package marked under revision; geometry and print files preserved.')
