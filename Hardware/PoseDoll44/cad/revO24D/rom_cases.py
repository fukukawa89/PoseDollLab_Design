"""Explicit full-body ROM examination postures; retain every existing axis target.

A joint range is examined in an appropriate posture, not by requiring every other
joint to be zero. No zero-context failure is classified as non-human automatically.
"""
from fullbody import *

def examination_cases():
    result={}
    for axis in PROFILE['axes']:
        name=axis['id'];q=dict(NEUTRAL_ANGLES)
        reason='A-pose baseline; retain original anatomical angle endpoint. Required collision scope is same/adjacent anatomical segments, including all intermediate joint stages. Non-adjacent body contact is advisory by user instruction.'
        for value in axis['limits_deg']:
            goal={**q,name:value}
            result[f'ROM/{name}/{value}']=dict(angles=goal,axis=name,value_deg=value,reason=reason,classification='RETAIN_NORMAL_TARGET')
    return result

def main():
    from validate import read_assembly,Collision
    digest=sha(OUT/'assembly_meshes.npz');parts,z,solids=read_assembly();engine=Collision(parts,solids);rows=[]
    cases=examination_cases();dense='--dense' in sys.argv
    if dense:
        for name,v in list(cases.items()):
            steps=max(1,math.ceil(abs(v['value_deg'])/2))
            for i in range(steps):
                angle=v['value_deg']*i/steps
                cases[name+f'/step/{i}']=dict(v,angles={**v['angles'],v['axis']:angle},value_deg=angle)
    for name,v in cases.items():
        hits=engine.check(v['angles']);rows.append(dict(case=name,**v,count=len(hits),collisions=hits))
        if hits:print(name,len(hits),[(h['a'],h['b'],h['volume_mm3']) for h in hits[:5]],flush=True)
        if len(rows)%100==0:print('ROM SAMPLES',len(rows),'/',len(cases),flush=True)
    if sha(OUT/'assembly_meshes.npz')!=digest:raise RuntimeError('Geometry changed during ROM scan; no current report written')
    put(OUT/('verification/rom_examination_dense.json' if dense else 'verification/rom_examination.json'),dict(status='PASS' if all(r['count']==0 for r in rows) else 'FAIL',geometry_sha256=digest,targets=len(rows),max_axis_step_deg=2 if dense else None,excluded_targets=[],cases=rows,scope='All original angular endpoints retained; A neutral baseline. All moving parts within same/adjacent anatomical segments required. Non-adjacent body contact is advisory per user instruction 2026-10-23. Finite samples; multi-axis local grids tested separately.'))
    print('ROM FAILS',sum(r['count']>0 for r in rows),'/',len(rows),flush=True)
if __name__=='__main__':main()
