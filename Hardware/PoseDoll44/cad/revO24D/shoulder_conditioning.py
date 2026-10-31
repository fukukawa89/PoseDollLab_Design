"""Record the retained shoulder gimbal singularity; do not label it solved."""
from fullbody import *


def main():
    rows=[]
    for side in ['l','r']:
        keys=[side+'_'+n for n in ['shoulder_flex','shoulder_abduct','upperarm_roll']]
        for angle in [45,85,89,90,91,95]:
            q={**NEUTRAL_ANGLES,keys[1]:angle};f=frames(q)
            jac=np.column_stack([f[k][:3,:3]@np.array(NODES[k]['axis']) for k in keys])
            values=np.linalg.svd(jac,compute_uv=False);rank=int(np.linalg.matrix_rank(jac,tol=1e-10))
            rows.append(dict(side=side,abduction_deg=angle,instantaneous_axes=jac.tolist(),singular_values=values.tolist(),rank=rank,condition_number=float(values[0]/values[-1]) if rank==3 else None))
    reproduced=all(r['rank']==(2 if r['abduction_deg']==90 else 3) for r in rows)
    put(OUT/'verification/shoulder_conditioning.json',dict(status='KNOWN_MECHANICAL_SINGULARITY',geometry_sha256=sha(OUT/'assembly_meshes.npz'),boundary_check='PASS_REPRODUCED' if reproduced else 'FAIL',rows=rows,
        scope='World-axis Jacobian of the actual three-stage shoulder. Abduction 90 degrees aligns the first and third axes; A45 is full-rank. Side raise remains available but independent small-angle adjustment degenerates near 90 degrees. Joint encoders and quaternion output do not remove this mechanical condition. It is documented, not counted as a collision failure or a solved singularity.'))
    print('SHOULDER BOUNDARY',reproduced,flush=True)


if __name__=='__main__':main()
