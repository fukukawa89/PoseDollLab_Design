"""Assembly insertion directions, preload travel and actual extrusion evidence."""
from kit import *
from validate import overlaps
import zipfile,re

def main():
    k=build();P={p['id']:p for p in k.parts};fail=[];checks=[]
    # Bearing and washer insertion occurs before the removable cheek is installed.
    # Cup insertion is checked without guide pins; pins are screwed in afterwards.
    paths=[]
    for st in ['H','R']:
        for sign in [-1,1]:paths.append((st+'bearing_'+str(sign),[st+'01',st+'02'],sign*Y,6))
    for id,targets,direction,distance in [('W01',['W02'], -X,15),('W09',['W01','W02'], -Z,20),('W04',['W01','W02'], -Y,15),('W05',['W01','W02'],Y,15)]:paths.append((id,targets,direction,distance))
    # S3 closes the missed insertion check: each liner must enter its own cup,
    # not merely fit around the ball after being placed at its final location.
    paths.extend([('W04',['W06'],Y,15),('W05',['W07'],-Y,15)])
    for moving,targets,direction,distance in paths:
        worst=0
        for dist in np.linspace(0,distance,31):
            s=P[moving]['s'].translate(direction*dist)
            for target in targets:
                if overlaps(s,P[target]['s']):worst=max(worst,(s^P[target]['s']).volume())
        checks.append(dict(id=moving,against=targets,travel_mm=distance,steps=31,max_intersection_mm3=worst,passed=worst<.02))
    # Rigid closing motion is a keep-out check only. The intended liner/ball
    # compression is excluded by exact pair identity, not by a whole assembly.
    moving=[p for p in k.parts if p['station']=='W' and p['frame']=='ball']
    closing=[p for p in k.parts if p['id'] in ['W06','W07'] or p['id'].startswith(('Wliner_screw','Wliner_w','Wliner_n'))]
    worst={}
    for q in [-65,-45,0,45,70]:
        for d in [-20,0,30]:
            F=frames('W',q,d)['ball']
            for p in closing:
                sign=1 if np.array(p['s'].bounding_box()).reshape(2,3).mean(0)[1]>0 else -1
                s=p['s'].translate([0,-sign*.20,0])
                for r in moving:
                    t=moved(r['s'],F)
                    if overlaps(s,t):
                        v=(s^t).volume()
                        if v>.02:worst[p['id']+' / '+r['id']]=max(worst.get(p['id']+' / '+r['id'],0),v)
    # Critical local dimensions are explicit acceptance gates for actual metrology.
    dims=[dict(name='Bearing face to braking plane',nominal_mm=.4,physical_gate='Measure >=0.20 mm on both assembled rotor halves before tightening brake; no washer contact with bearing faces.'),
          dict(name='S1 guide metal clamp stack',nominal_mm=2.1,physical_gate='0.5 mm steel washer directly on 1.6 mm plain M2 nut; no PLA between them. Captured stack has nominal 0.20 mm total axial clearance. Do not substitute a 3 mm nyloc nut.'),
          dict(name='Liner retainer pocket floor',nominal_mm=1.25,physical_gate='No broken layers or white stress marks when lightly seated.'),
          dict(name='W cup-to-bridge adjustment gap each side',nominal_mm=2.5,physical_gate='Limit inward travel to <=0.20 mm per side measured from loose assembled position; match both sides within 0.10 mm.'),
          dict(name='Guide slot minus pin diameter',nominal_mm=.44,physical_gate='Must move freely without filing the metal shoulder or forcing the slot; record cross-axis play.'),
          dict(name='Shaft end float',nominal_mm=.6,physical_gate='Blind bores retain the 45 mm rod even before radial clamps engage; ends deburred.'),
          dict(name='Ball magnet chamber axial allowance',nominal_mm=.2,physical_gate='D8x3 dummy/magnet seats wholly inside; split faces must close without clamping on the magnet.')]
    put(OUT/'verification/assembly_checks.json',dict(passed=all(r['passed'] for r in checks) and not worst,insertion_paths=checks,preload_closing_keepout=dict(each_cup_travel_mm=.2,poses=15,collisions=worst),dimensions=dims,
        scope='Named part insertion paths and geometric keep-outs. Nut insertion into open split ball is provided by the open X=0 face. Does not replace actual tool access, elastic contact, fit or force tests.'))
    print('ASSEMBLY',all(r['passed'] for r in checks),worst,flush=True)

    # Every object must have actual positive model extrusion, not just a mesh name.
    plans=json.loads((OUT/'printing/plates.json').read_text())['plates'];rows=[]
    for plan in plans:
        path=ROOT/'output/o24ct1-slicing'/plan['id']/'sliced.3mf'
        with zipfile.ZipFile(path) as z:g=z.read('Metadata/plate_1.gcode').decode('utf8','replace')
        counts={item['id']:0 for item in plan['items']};obj=None;feature='Custom';lengths={n:0. for n in counts}
        for line in g.splitlines():
            m=re.match(r'; printing object (.+) id:',line)
            if m:obj=m.group(1)
            if line.startswith('; stop printing object '):obj=None
            if line.startswith('; FEATURE: '):feature=line[11:]
            if obj in counts and feature not in ['Custom','Support','Support interface','Skirt','Brim'] and re.match(r'G[123] .*\b[XY]',line):
                e=re.search(r'\bE((?:[0-9]*\.)?[0-9]+)',line)
                if e and float(e.group(1))>0:counts[obj]+=1;lengths[obj]+=float(e.group(1))
        rows.append(dict(plate=plan['id'],positive_model_extrusions=counts,extruded_filament_mm=lengths,passed=all(x>100 for x in counts.values()),time_header=next((x for x in g.splitlines() if x.startswith('; model printing time:')),None),
            material_header=[x for x in g.splitlines() if x.startswith(('; filament used [g]','; total filament used [g]'))]))
    put(OUT/'verification/extrusion_by_part.json',dict(passed=all(r['passed'] for r in rows),plates=rows))
    print('EXTRUSION',all(r['passed'] for r in rows),flush=True)

if __name__=='__main__':main()
