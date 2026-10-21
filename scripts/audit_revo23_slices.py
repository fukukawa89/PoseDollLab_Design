"""Check slicer-saved geometry and actual toolpath height coverage, not just exit code."""
from slice_revo23_exports import *
from verify_revo22_f3_native_mesh import read_project

def audit(row):
    rid=row['id'];work=ROOT/rid;before,_,_=read_project(work/'input.3mf');after,settings,repairs=read_project(B/row['project'])
    assert before.keys()==after.keys()=={rid}
    v,f=before[rid];w,g=after[rid]
    same_faces=np.array_equal(f,g);delta=float(np.max(abs(v-w))) if v.shape==w.shape else 1e9
    mesh=trimesh.Trimesh(w,g,process=False)
    with zipfile.ZipFile(B/row['project']) as z:code=z.read(row['gcode_members'][0]).decode('utf8','replace')
    feature='';z=0.;model_layers=[];support_moves=object_moves=0;xy=[];layers={}
    for line in code.splitlines():
        if line.startswith('; Z_HEIGHT:'):z=float(line.split(':',1)[1])
        elif line.startswith('; FEATURE:'):feature=line.split(':',1)[1].strip()
        elif re.match(r'G[123] ',line) and re.search(r'\bE(?:\d*\.\d+|\d+)',line) and re.search(r'\b[XY]-?(?:\d*\.\d+|\d+)',line):
            if feature in ('Support','Support interface'):support_moves+=1
            elif feature and feature not in ('Brim','Skirt','Custom'):
                object_moves+=1;model_layers.append(z);layers[z]=layers.get(z,0)+1
    lo=float(w[:,2].min());hi=float(w[:,2].max());top=max(model_layers) if model_layers else None;bottom=min(model_layers) if model_layers else None
    repair_count=sum(sum(x.values()) for x in repairs)
    result=dict(id=rid,key=row['key'],stl_sha256=row['stl_sha256'],project_sha256=sha(B/row['project']),
        slicer_faces_identical_to_STL=True if same_faces else False,slicer_maximum_vertex_shift_mm=delta,
        slicer_saved_mesh_watertight=bool(mesh.is_watertight),slicer_saved_mesh_winding=bool(mesh.is_winding_consistent),
        slicer_saved_components=len(mesh.split(only_watertight=False)),slicer_repair_count=repair_count,
        object_extrusion_moves=object_moves,support_extrusion_moves=support_moves,object_layers=len(layers),
        object_bottom_extrusion_z_mm=bottom,object_top_extrusion_z_mm=top,geometry_bottom_z_mm=lo,geometry_top_z_mm=hi,
        mesh_fits_A1mini=bool(w[:,:2].min()>=-1e-4 and w[:,:2].max()<=180.0001 and lo>=-.0001 and hi<=180.0001),
        layer_profile_mm=float(settings['layer_height']),automatic_supports=settings['enable_support']=='1',
        physical_print_tested=False)
    result['passed']=bool(row['passed'] and same_faces and delta<.0002 and mesh.is_watertight and mesh.is_winding_consistent
        and result['slicer_saved_components']==1 and repair_count==0 and object_moves>10 and len(layers)>2
        and bottom is not None and bottom-lo<=.21 and abs(top-hi)<=.2 and result['mesh_fits_A1mini'])
    put(work/'native_audit.json',result)
    print('NATIVE',rid,result['passed'],'shift',round(delta,9),'top error',round(hi-top,4) if top else None,flush=True)
    return result

if __name__=='__main__':
    rows=read(ROOT/'results.json')['rows'];results=[audit(r) for r in rows]
    put(ROOT/'native_audit.json',dict(geometry_sha256=sha(B/'assembly.npz'),rows=results,passed=all(r['passed'] for r in results)))
