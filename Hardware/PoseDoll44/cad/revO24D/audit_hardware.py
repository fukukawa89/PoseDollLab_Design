"""Detect interpenetrating metal/bearing/electronics within a rigid body."""
from validate import *

def main():
    parts,z,ss=read_assembly();rows=[];families={}
    for p,s in zip(parts,ss):
        if p['role'] not in ['metal','bearing','pcb','connector','magnet','friction']:continue
        fr=family(p['frame']);s=moved(s,np.linalg.inv(F0[fr])@F0[p['frame']]);b=np.array(s.bounding_box()).reshape(2,3)
        for t,u,c in families.get(fr,[]):
            if np.all(b[1]>c[0]+1e-7) and np.all(c[1]>b[0]+1e-7):
                v=(s^u).volume()
                if v>.02:rows.append(dict(a=p['name'],b=t['name'],volume_mm3=v,frame=fr))
        families.setdefault(fr,[]).append((p,s,b))
    put(OUT/'verification/static_hardware_intersections.json',dict(status='PASS' if not rows else 'FAIL',geometry_sha256=sha(OUT/'assembly_meshes.npz'),rows=rows,threshold_mm3=.02))
    print('SAME BODY HARDWARE',len(rows))
    for r in sorted(rows,key=lambda r:-r['volume_mm3'])[:80]:print(r)

if __name__=='__main__':main()
