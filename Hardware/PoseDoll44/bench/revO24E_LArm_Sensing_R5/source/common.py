from pathlib import Path
import sys, json, math, hashlib, shutil, copy, csv
sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
H = HERE.parents[1]
sys.path.insert(0, str(H/'cad/revO24E_LArm_Stock_R4'))
import build_stock as r4
from build_stock import T, rot, moved, box, cyl, tube, beam, union, k, e, md, np, trimesh, F0, FA, frames, PROFILE, POSES, ROOT
BASE = H/'bench/revO24E_LArm_Stock_R4'
OUT = H/'bench/revO24E_LArm_Sensing_R5'
load = r4.load
put = r4.put
sha = r4.sha

def baseline():
    assert sha(BASE/'production_meshes.npz') == 'de73b1fb747faa73d77f735215eed157c6503b94efe380b91477f848450ccdfa'
    a=load(BASE/'production_assembly.json')['parts']; z=np.load(BASE/'production_meshes.npz')
    ss=[md.Manifold(md.Mesh64(np.array(z[str(p['i'])+'v'],copy=True),np.array(z[str(p['i'])+'f'],dtype=np.uint64,copy=True))) for p in a]
    return a,ss

def basis(axis):
    z=np.asarray(axis,dtype=float);z/=np.linalg.norm(z)
    x=np.eye(3)[np.argmin(abs(z))];x-=z*np.dot(x,z);x/=np.linalg.norm(x)
    return np.column_stack([x,np.cross(z,x),z])

def world_solids():
    a,ss=baseline()
    return a,{p['name']:moved(s,F0[p['frame']]) for p,s in zip(a,ss)}

if __name__=='__main__':
    a,S=world_solids();ints=load(BASE/'interfaces.json')
    for r in ints['rolls']:
        W=np.array(r['W']);inv=np.linalg.inv(W)
        names=[p['name'] for p in a if p['name'].startswith(r['id']+'_') and '_lid_' not in p['name']]
        names+=['ROOT','SHOULDER_PITCH','SHOULDER_ABDUCT','UPPER_ARM','ELBOW_OUTPUT','FOREARM']
        print(r['id'])
        for name in names:
            b=e.bounds(moved(S[name],inv))
            print(name,np.round(b,2).tolist())
