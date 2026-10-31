"""Author search: both Z modules, steel output wall and all actual local grids."""
from layout_A_search import *

def main():
    parts,z,ss=read_assembly();data=load(OUT/'verification/joint_local_grids.json');cases=[dict(NEUTRAL_ANGLES)]+[c['angles'] for g in data['groups'] for c in g['cases']]
    ids={side:[i for i,p in enumerate(parts) if p['name'].startswith(side+'_clavicle_z_')] for side in ['l','r']}
    excluded=[parts[i]['name'] for side in ids for i in ids[side]]+['left_clavicle_seat','right_clavicle_seat','l_clavicle_vertical_transfer','r_clavicle_vertical_transfer','thorax_shell']
    candidates={}
    for side in ids:
        frameset=dict.fromkeys(parts[i]['frame'] for i in ids[side]);obs={fr:obstacles(parts,ss,fr,cases,excluded) for fr in frameset};cache={fr:{} for fr in frameset};valid=[]
        opts=[(False,d) for d in [7,8,9,10,11,12]] if side=='l' else [(f,d) for f in [False,True] for d in [-8,-6,-4,-3,-2,0,2,4,6,8,10]]
        for flip,dz in opts:
            c=P['clavicle_'+side]+[0,0,-27.4];W=T([0,0,dz])@(T(c)@np.diag([1.,1,-1,1])@T(-c) if flip else np.eye(4));items=[];hits=[]
            for i in ids[side]:
                fr=parts[i]['frame'];shape=ss[i]
                if side=='l' and parts[i]['name'].endswith('output_socket'):
                    shape=shape^cyl([0,0,-100],[0,0,20],7.5)
                shape=moved(shape,np.linalg.inv(F0[fr])@W@F0[fr]);items.append((i,shape));hits.extend((parts[i]['name'],n,v) for n,v in score(shape,obs[fr],ss,parts,cache[fr]))
            print('MODULE',side,flip,dz,round(sum(v for a,b,v in hits),3),sorted({b for a,b,v in hits}),flush=True)
            if not hits:valid.append(dict(flip=flip,dz=dz,items=items))
        candidates[side]=valid
    for l in candidates['l']:
      for r in candidates['r']:
        hits=[]
        for i,si in l['items']:
          a=moved(si,FA[parts[i]['frame']]);ab=np.array(a.bounding_box()).reshape(2,3)
          for j,sj in r['items']:
            b=moved(sj,FA[parts[j]['frame']]);bb=np.array(b.bounding_box()).reshape(2,3)
            if not(np.all(ab[1]>bb[0]) and np.all(bb[1]>ab[0])):continue
            v=(a^b).volume()
            if v>.02:hits.append((parts[i]['name'],parts[j]['name'],v))
        print('PAIR',l['dz'],r['flip'],r['dz'],round(sum(v for a,b,v in hits),3),flush=True)
        if not hits:
          put(OUT/'verification/A_pair_proposal.json',dict(source_geometry_sha256=sha(OUT/'assembly_meshes.npz'),left_delta=l['dz'],left_output_radius_mm=7.5,right_flip=r['flip'],right_delta=r['dz'],right_flip_relative_z_mm=-27.4));return
    print('NO PAIR',flush=True)

if __name__=='__main__':main()
