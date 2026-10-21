"""O9 imports immutable O8 geometry while keeping every new result in O9."""
from pathlib import Path
import sys,json,hashlib
import numpy as np
H=Path(__file__).resolve().parents[2];R=H.parents[1]
sys.path.insert(0,str(H/'cad/revO8'))
from reference_assembly import rot
G8=H/'generated/revO8/runs/o8_20260925_r1'
OUT=H/'generated/revO9/runs/o9_20260926_r1';OUT.mkdir(parents=True,exist_ok=True)
def save(name,data):
 (OUT/name).write_text(json.dumps(data,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def core(length=2):return dict(np.load(G8/f'fork_extension_{length}mm/core_meshes.npz'))
def pose_matrices(alpha,beta):
 A=rot([1,0,0],alpha);B=A@rot([0,1,0],beta)
 return {'C01':np.eye(3),'C02':B,'C14':A,'C15':A,'fasteners':A}
