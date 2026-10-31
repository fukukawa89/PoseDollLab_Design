"""Skin the frozen UE Quinn asset using exported A component transforms.
This is an offline reconstruction, never an Unreal runtime test claim.
"""
from fullbody import *
from scipy.spatial.transform import Rotation

def main():
    ref,ch,scale=a.reference();geo=ch['geometry'];vertices=np.array(geo['positions_cm']);triangles=np.array(geo['triangles'])
    examples=load(OUT/'profiles/UE_component_pose_examples.json')['poses'];bybone=[[] for _ in ch['names']]
    for vi,ws in enumerate(geo['skin_weights']):
        for bi,w in ws:bybone[bi].append((vi,w))
    result={};max_weight_error=0
    for label in ['neutral','reference_N']:
        skinned=np.zeros_like(vertices);weights=np.zeros(len(vertices))
        for bi,ws in enumerate(bybone):
            if not ws:continue
            row=examples[label]['bones_component_space'][ch['names'][bi]]
            target=T(row['translation_cm'],Rotation.from_quat(row['rotation_xyzw']).as_matrix());delta=target@np.linalg.inv(ch['reference'][bi])
            ids=np.array([x[0] for x in ws]);w=np.array([x[1] for x in ws])
            skinned[ids]+=(vertices[ids]@delta[:3,:3].T+delta[:3,3])*w[:,None];weights[ids]+=w
        max_weight_error=max(max_weight_error,float(np.max(abs(weights-1))))
        result[label]=(skinned/weights[:,None])@a.ue.SWAP.T*(10*ref['uniform_scale'])+ref['floor_shift_mm']
    error=float(np.max(abs(result['reference_N']-ch['vertices_mm']*scale)))
    np.savez_compressed(OUT/'reference/UE_A_surface.npz',vertices_mm=result['neutral'],triangles=triangles[:,::-1])
    mesh=trimesh.Trimesh(result['neutral']/1000,triangles[:,::-1],process=False);mesh.visual.vertex_colors=[224,227,229,255];mesh.export(OUT/'reference/UE_Quinn_A.glb')
    put(OUT/'verification/ue_A_surface.json',dict(status='PASS_OFFLINE_RECONSTRUCTION' if error<1e-6 and max_weight_error<2e-4 else 'FAIL',geometry_sha256=sha(OUT/'assembly_meshes.npz'),source_asset=ref['asset'],source_files=ref['source_files'],skin_vertices=len(vertices),triangles=len(triangles),bones=len(ch['names']),A_angles_deg=NEUTRAL_ANGLES,reference_N_reconstruction_error_mm=error,max_weight_sum_error=max_weight_error,runtime_UE_tested=False,scope='Actual frozen UE mesh and per-vertex skin weights driven by exported A component transforms; compare N reconstruction independently with original neutralization. Visual alignment reference only, not a skin self-intersection or runtime acceptance test.'))
    print('UE A SKIN',len(vertices),'N cross-check mm',error,flush=True)

if __name__=='__main__':main()
