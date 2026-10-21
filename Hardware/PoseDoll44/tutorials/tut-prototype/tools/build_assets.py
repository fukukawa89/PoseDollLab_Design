"""Offline WebGL assets derived directly from O8 triangle meshes (no remodelling)."""
from pathlib import Path
import json,sys,numpy as np,hashlib
H=Path(__file__).resolve().parents[3];sys.path.insert(0,str(H/'cad/revO8'));from reference_assembly import OUT
D=Path(__file__).resolve().parents[1]/'assets';models={};inputs=[]
for label,path in [('original',OUT.parent/'fork_extension_0mm/core_meshes.npz'),('extended',OUT.parent/'fork_extension_2mm/core_meshes.npz'),('fastener',OUT.parent/'fastened_core/fasteners.npz'),('gauge',H/'bench/revO8/fit_gauges/meshes.npz')]:
 data=np.load(path);inputs.append({'path':path.relative_to(H).as_posix(),'sha256':hashlib.sha256(path.read_bytes()).hexdigest()})
 for name,t in data.items():
  v,f=np.unique(np.round(t.reshape(-1,3),5),axis=0,return_inverse=True);models[label+'_'+name]={'v':v.tolist(),'f':f.reshape(-1,3).tolist()}
summary={}
for name in ('fork_search','fork_clearance','shoulder_mapping','assembly_path','sensor_observability'):
 p=OUT.parent/(name+'.json');inputs.append({'path':p.relative_to(H).as_posix(),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()})
(D/'models.js').write_text('window.TUT_MODELS='+json.dumps(models,separators=(',',':'))+';\n',encoding='utf-8')
(D/'provenance.json').write_text(json.dumps({'inputs':inputs,'render_precision_mm':1e-5,'scope':'Display geometry only. Collision reports use the original full precision meshes. Page animations do not perform online collision checking.','physical_tested':False},indent=2)+'\n',encoding='utf-8');print(len(models),'models', (D/'models.js').stat().st_size)
