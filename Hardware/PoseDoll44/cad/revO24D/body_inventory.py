"""Identify actual joined printed bodies and their same-body hardware contacts."""
from groups import *

def main():
    parts,z,ss=read_assembly();rows=[]
    for fr in dict.fromkeys(family(p['frame']) for p in parts):
        members=[(p,moved(s,np.linalg.inv(F0[fr])@F0[p['frame']])) for p,s in zip(parts,ss) if family(p['frame'])==fr]
        printed=[(p,s) for p,s in members if p['role'] in ['structure','rotor','shell']]
        if not printed:continue
        hard=[(p,s,np.array(s.bounding_box()).reshape(2,3)) for p,s in members if p['role'] not in ['structure','rotor','shell']]
        comp=physical_components(union(s for p,s in printed))
        for i,s in enumerate(comp):
            b=np.array(s.bounding_box()).reshape(2,3);names=[];contacts=[]
            for p,t in printed:
                tb=np.array(t.bounding_box()).reshape(2,3)
                if np.all(b[1]>=tb[0]) and np.all(tb[1]>=b[0]) and (s^t).volume()>.001:names.append(p['name'])
            for p,t,tb in hard:
                if np.all(b[1]+.26>=tb[0]) and np.all(tb[1]+.26>=b[0]):
                    gap=s.min_gap(t,.26)
                    if gap<.251:contacts.append(dict(part=p['name'],gap_mm=gap,role=p['role']))
            r=dict(frame=fr,index=i,volume_mm3=s.volume(),bounds_mm=b,features=names,materials=sorted({p.get('material','FDM process qualification required') for p,t in printed if p['name'] in names}),contacts=contacts)
            rows.append(r)
            if s.volume()>2 and (len(comp)>1 or not contacts):print(fr,i,round(s.volume(),2),names,'CONTACT',[c['part'] for c in contacts],flush=True)
    put(OUT/'verification/material_body_inventory.json',dict(geometry_sha256=sha(OUT/'assembly_meshes.npz'),rows=rows,note='Geometric contact inventory only; contact is not automatically a validated attachment. Enclosed cavity boundaries stay with their containing material.'))

if __name__=='__main__':main()
