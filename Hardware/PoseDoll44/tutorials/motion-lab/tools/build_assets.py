from pathlib import Path
import json,numpy as np,hashlib
H=Path(__file__).resolve().parents[3];G=H/'generated/revO9/runs/o9_20260926_r1';D=Path(__file__).resolve().parents[1]/'assets';models={};inputs=[]
for label,path in [('original',H/'generated/revO8/runs/o8_20260925_r1/fork_extension_2mm/core_meshes.npz'),('extended',G/'cup_relief_L3_R0p35/core_meshes.npz'),('fastener',H/'generated/revO8/runs/o8_20260925_r1/fastened_core/fasteners.npz')]:
 inputs.append({'path':path.relative_to(H).as_posix(),'sha256':hashlib.sha256(path.read_bytes()).hexdigest()})
 for name,t in np.load(path).items():
  v,f=np.unique(np.round(t.reshape(-1,3),5),axis=0,return_inverse=True);models[label+'_'+name]={'v':v.tolist(),'f':f.reshape(-1,3).tolist()}
reports={}
for name in ('bounded_mapping','path_audit','continuous_yoke_workspace','core_motion_grid','assembly_path','restricted_tool_access'):
 p=G/(name+'.json');reports[name]=json.loads(p.read_text());inputs.append({'path':p.relative_to(H).as_posix(),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()})
assert reports['continuous_yoke_workspace']['status']=='CERTIFIED_SCOPED_NOMINAL_YOKE_WORKSPACE'
(D/'data.js').write_text('window.TUT_MODELS='+json.dumps(models,separators=(',',':'))+';\nwindow.O9_REPORTS='+json.dumps(reports,separators=(',',':'))+';\n',encoding='utf-8')
(D/'provenance.json').write_text(json.dumps({'inputs':inputs,'scope':'Display rounds meshes to 0.00001 mm; validation uses original precision. Browser does not compute collisions.','physical_tested':False},indent=2)+'\n',encoding='utf-8')
print('models',len(models),'bytes',(D/'data.js').stat().st_size)
