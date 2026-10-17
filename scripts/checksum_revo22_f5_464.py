from pathlib import Path
p=Path(__file__).parent/'package_revo22_f5_delivery375.py';s=p.read_text(encoding='utf-8-sig');a=s.index(" files=sorted(p for p in D.rglob('*')if p.is_file()and p.name!='SHA256SUMS.txt')");b=s.index('\n zpath=',a);block=s[a:b];s=s[:a]+s[b:];idx=s.index(' failures=[]');s=s[:idx]+block+'\n'+s[idx:];p.write_text(s,encoding='utf-8')
from publish_revo22_f5_compact302 import D,write
p=D/'assembly/tutorials/assembly-o22/index.html';s=p.read_text();s=s.replace('<title>O22 · 按打印盘拼装人偶</title>','<title>O22-F5 · 按打印盘拼装人偶</title>');write(p,s)
