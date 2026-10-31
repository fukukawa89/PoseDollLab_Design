"""Check tutorial face directions against unmodified CAD contact surfaces.

Bolt head/tip radii identify thread travel independently of orientation metadata.
Thin annular probes test which washer/nut face actually touches its named mate.
These checks concern directions, not thread friction or physical holding force.
"""
from kit import *


def main():
    data=json.loads((OUT/'tutorial/steps.json').read_text('utf8'))
    parts={p['id']:p for p in build().parts};checks=[]
    for id,p in data['catalog'].items():
        o=p.get('orientation')
        if not o:continue
        direction=np.array(o['normal']);face=np.array(o['face']);c=np.array(o['center'])
        assert np.isclose(np.linalg.norm(direction),1),id
        if o['kind']=='nylon':
            v=mesh(parts[o['bolt']]['s']).vertices
            axial=(v-c)@direction;radial=np.linalg.norm(v-c-axial[:,None]*direction,axis=1)
            near=float(radial[axial<axial.min()+.05].max())
            far=float(radial[axial>axial.max()-.05].max())
            # The socket head must be on the metal-entry side, the narrow tip
            # on the marked nylon side, including R's rotated radial clamps.
            passed=near>1.4*far and o['radius']>o['bore']
            checks.append(dict(id=id,test='nylon face follows head-to-tip direction',head_radius=near,tip_radius=far,passed=passed))
        else:
            inner=o['bore']+.03;outer=o['radius']-.03
            target=parts[o['target_id']]['s']
            into=tube(face+direction*.01,face+direction*.04,outer,inner)
            away=tube(face-direction*.01,face-direction*.04,outer,inner)
            positive=float((into^target).volume());negative=float((away^target).volume())
            # Wrist preload ears include a rounded brace tip just beyond the
            # flat bearing face. Require >1000:1 directional contact, allowing
            # that tiny edge remnant without misclassifying the bearing face.
            checks.append(dict(id=id,test='marked face contacts named mate',mate=o['target_id'],toward_mm3=positive,away_mm3=negative,passed=positive>1e-4 and negative<max(1e-5,positive*.001)))
    assert len(checks)==73
    failed=[r for r in checks if not r['passed']]
    # Manufacturing and user observation files must be byte-for-byte unchanged.
    baseline=json.loads((OUT/'verification/tutorial_orientation_baseline.json').read_text('utf8'))
    changed=[name for name,digest in baseline.items() if sha(OUT/name)!=digest]
    assert not changed,changed
    report=dict(passed=not failed,geometry_sha256=sha(OUT/'assembly_meshes.npz'),steps_sha256=sha(OUT/'tutorial/steps.json'),
                checked_hardware=len(checks),nylon_nuts=sum(c['test'].startswith('nylon') for c in checks),
                unchanged_manufacturing_and_observation_files=len(baseline),checks=checks)
    put(OUT/'verification/tutorial_orientation.json',report)
    assert not failed,failed
    print('ORIENTATION PASS',len(checks),'hardware faces;',len(baseline),'unchanged manufacturing / record files',flush=True)


if __name__=='__main__':main()
