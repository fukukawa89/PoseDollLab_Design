"""A-pose wire routing guide geometry, separate from rigid-motion solids."""
from fullbody import *
def main():
    h=load(OUT/'harness/routes.json');assert h['geometry_sha256']==sha(OUT/'assembly_meshes.npz')
    scene=trimesh.load(OUT/'O24D_full_body.glb',force='scene',process=False)
    wire=trimesh.Scene();colors={'A':[.1,.5,.3],'B':[.1,.35,.82],'C':[.85,.4,.12]}
    for r in h['spans']:
        pts=np.array(r['guide_A_mm']);s=union(beam(a,b,r['diameter_mm']/2) for a,b in zip(pts,pts[1:]));v,f=a.mesh_data(s);m=trimesh.Trimesh(v*.001,f,process=False);m.visual.vertex_colors=np.array([*colors[r['cables'][0][0]],1])*255
        name='wire_guide_'+r['id'];scene.add_geometry(m,node_name=name);wire.add_geometry(m,node_name=name)
    scene.metadata.update(review_only=True,wire_geometry='A pose routing centreline guides with nominal bundled diameter; dress reserved loops during assembly; not flexible-cable simulation')
    scene.export(OUT/'O24D_system_A.glb');wire.export(OUT/'harness/O24D_wire_guides_A.glb')
    saved=trimesh.load(OUT/'O24D_system_A.glb',force='scene',process=False);bounds=saved.bounds*1000
    wire_names=[n for n in saved.graph.nodes_geometry if n.startswith('wire_guide_')]
    passed=len(wire_names)==len(h['spans']) and bounds[1,2]-bounds[0,2]<600
    put(OUT/'verification/wire_scene.json',dict(status='PASS_REFERENCE_EXPORT' if passed else 'FAIL',geometry_sha256=h['geometry_sha256'],harness_sha256=sha(OUT/'harness/routes.json'),system_glb_sha256=sha(OUT/'O24D_system_A.glb'),spans=len(h['spans']),saved_wire_nodes=len(wire_names),system_bounds_mm=bounds,system_A_height_mm=bounds[1,2]-bounds[0,2],scope=scene.metadata['wire_geometry']))
    if not passed:raise RuntimeError('Saved system model envelope or wire inventory mismatch')
if __name__=='__main__':main()
