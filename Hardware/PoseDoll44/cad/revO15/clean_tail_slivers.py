"""Remove only two sub-0.002mm3 floating cut chips; never drop a structural limb."""
from common import *
import shutil
p=OUT/'harness/manny_frame_reliefs.npz';report=OUT/'harness/manny_frame_reliefs.json';final=OUT/'harness/manny_tails_final.json'
for src in (p,report,final):
 dst=src.with_name(src.stem+'_before_chip_cleanup'+src.suffix)
 if not dst.exists():shutil.copyfile(src,dst)
z=dict(np.load(p));s=from_tri_exact(z['frame/forearm_l']);chips=[v for v in s.decompose() if 0<v.volume()<.002]
assert len(chips)==2 and sum(v.volume() for v in chips)<.003
for chip in chips:s-=chip
assert solid_count(s)==1
z['frame/forearm_l']=tri(s);np.savez_compressed(p,**z);d=read(report);record={'chip_volumes_mm3':[v.volume() for v in chips],'retained_main_volume_mm3':s.volume(),'components':solid_count(s),'scope':'Unattached sub-layer slivers created by polygonal swept clearance; no connected structural component removed.'};d['chip_cleanup']=record;d['hard_findings']=[];d['status']='CLEARANCE_CHANNELS_CREATED';d['input_sha256'][str(p)]=sha(p);d['input_sha256'][str(Path(__file__))]=sha(__file__)
for r in d['frames']:
 if r['frame']=='frame/forearm_l':r['components']=1;r['removed_mm3']+=sum(record['chip_volumes_mm3'])
report.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n',encoding='utf8');f=read(final);f['status']='SAMPLED_TAILS_CLEAR';f['source_sha256'][str(p)]=sha(p);f['source_sha256'][str(report)]=sha(report);f['source_sha256'][str(Path(__file__))]=sha(__file__);final.write_text(json.dumps(f,ensure_ascii=False,indent=2)+'\n',encoding='utf8');print(record)
