from common import *
import search_serial_clavicle as ss
old=ss.config
record=read(OUT/'shoulder_outward_directions.json')['candidates'][0]
F=np.array(record['F'])
def config(char):
 p,mm=old(char)
 for m in mm:
  if m['id'].startswith('upperarm_'):
   side=1 if m['id'].endswith('_l') else -1
   m['F']=(F if side==1 else np.diag([1,-1,1])@F).tolist();m['offset_parent_mm']=[0,side*8,0]
 return p,mm
if __name__=='__main__':
 src=OUT/'serial_clavicle_search.json'
 if src.exists():(OUT/'serial_clavicle_search_inward.json').write_bytes(src.read_bytes())
 ss.config=config;ss.main()
 r=read(src);r['shoulder_F_left']=F.tolist();r['shoulder_offset_mm']=8;save('serial_clavicle_outward_search.json',r)
