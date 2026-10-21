"""Update the first O23C lid bosses to allow populated PCB withdrawal.

Use once after the initial compact build/refinement; the main builder now emits
this corrected geometry directly. Every untouched indexed mesh is preserved.
"""
from build_revo23_compact import *


def main():
    parts=load_current();p=read(B/'profiles/device_profile.json');config=read(B/'design/compact_revision.json')
    if config.get('lid_boss_version')==2:raise RuntimeError('Corrected lid bosses already applied.')
    before=sha(B/'assembly.npz');C=np.array(config['controller_frame_neutral_mm']);N=frames(p,p['neutral_raw_deg'])['f:chest'];A=np.linalg.inv(C)@N
    housing=move(parts['o22/controller_housing']['s'],A)
    oldpoints=[(-1,-1),(65,-1),(-1,61),(65,61)];newpoints=[(-2,-2),(66,-2),(-2,62),(66,62)]
    oldboss=union([(kin.b.b.cyl(2.5,1.5,32)-kin.b.b.cyl(.85,25,33)).translate([u,v,0])for u,v in oldpoints])-box([-.3,-.3,12],[64.3,60.3,18])
    newboss=union([(kin.b.b.cyl(2.5,1.5,32)-kin.b.b.cyl(.85,25,33)).translate([u,v,0])for u,v in newpoints])-box([-.3,-.3,12],[64.3,60.3,33])
    floor=box([-5,-5,0],[69,65,2]);wall=box([-5,-5,1],[69,65,32])-box([-3,-3,.9],[67,63,32.1])
    for u in (-6,66):wall=wall-box([u,10,4],[u+4,50,29])
    wall=wall-box([2,-6,21],[23,-2,32.1])-box([25,62,16],[40,66,32.1])
    housing=housing-oldboss+floor+wall+newboss
    lid=box([-5,-5,32.2],[69,65,34.2])
    for u,v in newpoints:lid=lid-kin.b.b.cyl(1.15,32,35).translate([u,v,0])
    for u in range(7,59,10):
        for v in (5,55):lid=lid-box([u,v,32],[u+5,v+1.5,35])
    local=np.linalg.inv(N)@C;changed={'o22/controller_housing','o22/controller_lid'}
    parts['o22/controller_housing']['s']=move(housing,local);parts['o22/controller_lid']['s']=move(lid,local)
    for i,(u,v) in enumerate(newpoints):
        key='o22/lid_screw_'+str(i);changed.add(key)
        parts[key]['s']=move(kin.b.b.screw(2,6,3.8,1.5,34.2).translate([u,v,0]),local)
    old=np.load(B/'assembly.npz');out={k:old[k] for k in old.files}
    for key in changed:
        item=parts[key];i=str(item['index']);out[i+'v'],out[i+'f']=vf(item['s'])
    np.savez_compressed(B/'assembly.npz',**out)
    config.update(lid_boss_version=2,lid_boss_revision_input_sha256=before,lid_boss_revision_output_sha256=sha(B/'assembly.npz'))
    put(B/'design/compact_revision.json',config)
    print('CASE WITHDRAWAL CLEARANCE',before,sha(B/'assembly.npz'),flush=True)


if __name__=='__main__':main()
