import zipfile,json,numpy as np
from search_revo22_f5_orientation268 import O
from optimize_revo22_f5_276 import candidates
for pid in ['P001','P017','P033','P049','P051','P071','P073','P093','P095','P115','P117','P130','W006','W016','W017','X038','X046','X054','X058','X066','X073','X080']:
 p=O/'selections'/f'{pid}.json'
 if p.exists():print('SELECT',pid,json.loads(p.read_text()).get('label'),flush=True)
 else:
  cc=candidates(pid);print('MISSING',pid,[(c[2],c[0])for c in cc[:2]],flush=True)
a=O/'candidates/P033/access307_3';p=next((a/'projects').glob('*.3mf'))
with zipfile.ZipFile(p)as z:
 st=json.loads(z.read('Metadata/project_settings.config'));print('OTHERSET',{k:v for k,v in st.items()if any(w in k for w in ['gap','filter','tiny','small','remove','threshold','min_'])})
 lines=z.read(next(n for n in z.namelist()if n.endswith('.gcode'))).decode().splitlines();start=next(i for i,l in enumerate(lines)if l=='; Z_HEIGHT: 20.4');end=next(i for i in range(start+1,len(lines))if lines[i].startswith('; Z_HEIGHT:'))
 print('RAWMATCH');
 for i in range(start,end):
  l=lines[i]
  if ('X53.'in l or'X54.'in l)and('Y41.'in l or'Y42.'in l):print(i,lines[max(i-2,start):i+3])
