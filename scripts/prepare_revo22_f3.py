"""Prepare isolated F3 work area and verify slicer; no printer access."""
from pathlib import Path
import json, sys, subprocess, zipfile, time, importlib.metadata, hashlib
import numpy as np
from build_revo22_fins import solid, box, vf
import package_revo22_fins_v2 as pack
R=Path(__file__).resolve().parents[1]
B=R/'Hardware/PoseDoll44/bench/revO22'
O=B/'a1mini_fins_v3'
for d in ['parts','design','verification','orientation','projects','candidates','blender']:
    (O/d).mkdir(parents=True,exist_ok=True)
ORCA=Path('D:/ProgramFiles/OrcaSlicer/orca-slicer.exe')
def slicer(source,dest,work,engine=ORCA,timeout=360):
    source=Path(source).resolve();dest=Path(dest).resolve();work=Path(work).resolve()
    work.mkdir(parents=True,exist_ok=True)
    command=[str(engine),'--allow-newer-file','--arrange','0','--slice','0','--debug','3','--export-3mf',str(dest),str(source)]
    started=time.time()
    with (work/'console.log').open('wb') as log:
        p=subprocess.Popen(command,cwd=work,stdout=log,stderr=log,creationflags=subprocess.CREATE_NO_WINDOW)
        while p.poll() is None and time.time()-started<timeout:time.sleep(.25)
        if p.poll() is None:p.terminate();p.wait(timeout=15)
    report={'command':command,'returncode':p.returncode,'elapsed_s':time.time()-started,'output_exists':dest.exists()}
    if dest.exists():
        with zipfile.ZipFile(dest) as z:
            codes=[n for n in z.namelist() if n.endswith('.gcode')]
            report['gcode_members']=codes
            if codes:
                code=z.read(codes[0]).decode('utf8','replace')
                report.update(gcode_header=code[:250],gcode_bytes=len(code),gcode_sha256=hashlib.sha256(code.encode()).hexdigest())
            settings=json.loads(z.read('Metadata/project_settings.config'))
            keys=['printer_model','printer_settings_id','filament_type','nozzle_diameter','layer_height','initial_layer_print_height','enable_support','wall_loops','sparse_infill_density','print_sequence']
            report['settings']={k:settings.get(k) for k in keys}
    report['complete']=bool(report.get('gcode_members')) and report['returncode']==0
    (work/'invocation.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8')
    return report
if __name__=='__main__':
    packages={n:importlib.metadata.version(n) for n in ['numpy','trimesh','shapely','manifold3d','scipy','rtree']}
    v,f=vf(box([0,0,0],[12,12,8]))
    np.savez_compressed(O/'parts/TOOLCHECK.npz',v=v,f=f,source_v=v,fin_v=np.empty((0,3)),fin_f=np.empty((0,3),int),teeth_v=np.empty((0,3)),teeth_f=np.empty((0,3),int))
    pack.O=O;pack.WORK=R/'.local/o22-fins-v3';pack.WORK.mkdir(exist_ok=True)
    p={'id':'TOOLCHECK','items':[{'id':'TOOLCHECK','object_name':'TOOLCHECK_cube','rotation_matrix':np.eye(3).tolist(),'translation_mm':[20,20,0]}]}
    source,work=pack.build(p)
    result=slicer(source,work/'orca_cube.3mf',work/'orca')
    result.update(python_executable=sys.executable,packages=packages)
    (O/'verification/toolchain.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf8')
    print(json.dumps(result,ensure_ascii=False,indent=2),flush=True)


