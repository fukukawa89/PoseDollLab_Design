from check_geometry import *
a,ss=saved();ch=next(c for c in channels() if c['id']=='RU');A=ch['mag_A'];pf=ch['pcb_frame']
mods=[(p,s) for p,s in zip(a,ss) if p['name'].startswith('RU_') and p.get('baseline_name') is None and 'MAG_' not in p['name'] and p['name']!='RU_MAGNET']
targets=[(p,s) for p,s in zip(a,ss) if p.get('baseline_name') and p['name'] not in ['UPPER_ARM']]
rows=[]
for clock in range(245,266):
    adjust=np.linalg.inv(F0[pf])@A@rot([0,0,1],clock-255)@np.linalg.inv(A)@F0[pf];worst=0;hits=[]
    for ang in [0,120,135,145]:
        ff=frames({'l_elbow_flex':ang});ob=[(p,moved(s,ff[p['frame']])) for p,s in targets]
        for p,s in mods:
            w=moved(s,ff[pf]@adjust);bb=e.bounds(w)
            for op,ow in ob:
                b=e.bounds(ow)
                if np.any(bb[1]<=b[0]) or np.any(bb[0]>=b[1]):continue
                v=(w^ow).volume()
                if v>.03:hits.append((p['name'],op['name'],round(v,3),ang));worst=max(worst,v)
    rows.append((clock,round(worst,3),hits))
print(sorted(rows,key=lambda x:x[1])[:8])
