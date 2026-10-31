"""S3 regression against preserved S2 geometry; no physical claims."""
from kit import *

def main():
    baseline=ROOT/'output/o24ct1-assembly-tutorial'
    hashes=json.loads((baseline/'mechanical_baseline.json').read_text('utf8'))
    oldrows={p['id']:p for p in json.loads((baseline/'assembly_S2.json').read_text('utf8'))['parts']}
    old=np.load(baseline/'assembly_meshes_S2.npz')
    k=build();parts={p['id']:p['s'] for p in k.parts};paths=[]
    for lin,cup,sign in [('W04','W06',1),('W05','W07',-1)]:
        i=oldrows[cup]['index'];s2=md.Manifold(md.Mesh(old['v'+str(i)].astype(np.float32),old['f'+str(i)].astype(np.uint32)))
        previous=current=0
        for d in np.linspace(0,15,121):
            moving=parts[lin].translate([0,sign*d,0]);previous=max(previous,float((moving^s2).volume()));current=max(current,float((moving^parts[cup]).volume()))
        paths.append(dict(liner=lin,cup=cup,travel_mm=15,samples=121,S2_max_intersection_mm3=previous,S3_max_intersection_mm3=current,passed=previous>20 and current<.02))
    stls={n:h for n,h in hashes.items() if n.endswith('.stl')}
    changed=[n for n,h in stls.items() if sha(OUT/n)!=h]
    changed_projects=[n for n,h in hashes.items() if n.endswith('.3mf') and sha(OUT/n)!=h]
    bom_same=sha(OUT/'BOM.json')==hashes['BOM.json']
    passed=all(r['passed'] for r in paths) and set(changed)=={'stl_print/W06.stl','stl_print/W07.stl'} and changed_projects==['printing/P3_wrist_1.3mf'] and bom_same
    report=dict(passed=passed,revision=REVISION,geometry_sha256=sha(OUT/'assembly_meshes.npz'),source_sha256=sha(Path(__file__)),changed_stls_from_S2=changed,unchanged_base_stls=24,unchanged_optional_stls=12,changed_existing_projects=changed_projects,new_project='printing/REPRINT_S3_1.3mf',hardware_bom_unchanged=bom_same,liner_insertion=paths,retainer_floor_nominal_mm=1.25,scope='Opens the cup retaining-pad pocket inward. Does not change the liner, ball, guide slots, nut seat, preload ears or hardware. Physical fit/stiffness/wear still require testing.')
    put(OUT/'verification/S2_baseline_hashes.json',hashes);put(OUT/'verification/S3_changes.json',report)
    print('S3',passed,'changed STL',changed,'projects',changed_projects,flush=True)
    if not passed:raise SystemExit(1)

if __name__=='__main__':main()
