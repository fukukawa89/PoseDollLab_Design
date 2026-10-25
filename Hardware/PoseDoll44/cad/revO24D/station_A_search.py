"""Author-only search relative to the currently saved cassette geometry."""
from layout_A_search import *

def main():
    parts,z,ss=read_assembly();data=load(OUT/'verification/joint_local_grids.json')
    cases=[dict(NEUTRAL_ANGLES)]+[c['angles'] for g in data['groups'] for c in g['cases']]
    excluded=[p['name'] for p in parts if p['name'].startswith('l_clavicle_z_')]+['left_clavicle_seat','l_clavicle_vertical_transfer']
    ids=[i for i,p in enumerate(parts) if p['name'].startswith('l_clavicle_z_')]
    obs={fr:obstacles(parts,ss,fr,cases,excluded) for fr in dict.fromkeys(parts[i]['frame'] for i in ids)};cache={fr:{} for fr in obs}
    best=(1e30,None,None)
    for dz in [.25,.5,.75,1,1.25,1.5,1.75,2]:
        hits=[]
        for i in ids:
            fr=parts[i]['frame'];shape=ss[i].translate(F0[fr][:3,:3].T@np.array([0,0,dz]));h=score(shape,obs[fr],ss,parts,cache[fr]);hits.extend([(parts[i]['name'],n,v) for n,v in h])
        total=sum(v for a,b,v in hits)
        print('STATION',dz,round(total,4),sorted({b for a,b,v in hits}),flush=True)
        if total<best[0]:best=(total,dz,hits)
        if not hits:break
    put(OUT/'verification/A_station_proposal.json',dict(current_geometry_sha256=sha(OUT/'assembly_meshes.npz'),volume=best[0],delta_z_mm=best[1],hits=best[2]))

if __name__=='__main__':main()
