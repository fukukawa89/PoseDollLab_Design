"""Assemble the two finite twist modules and stopped core in their actual frames."""
from pathlib import Path
import sys,json,numpy as np
H=Path(__file__).resolve().parents[2];G9=H/'generated/revO9/runs/o9_20260926_r1';OUT=H/'generated/revO13/runs/o13_20260929_r1'
sys.path.insert(0,str(H/'cad/revO9'));from common import rot
D=rot([1,0,0],180)
def matrices(q,zero):
 p,a,b,s=np.asarray(q)+zero;P=rot([0,0,1],p);A=P@rot([1,0,0],a);B=A@rot([0,1,0],b)
 return {'P':np.eye(3),'C01':P,'ring':A,'C02':B,'D':B@rot([0,0,1],s)@D}
def meshes(key):
 raw=dict(np.load(OUT/'braked_module'/f'{key}.npz'));fast=np.load(H/'generated/revO8/runs/o8_20260925_r1/fastened_core/fasteners.npz')
 return {'P':np.concatenate([v for k,v in raw.items() if k.startswith('P_')]),'C01':raw['C01'],'ring':np.concatenate([raw['C14'],raw['C15'],*fast.values()]),'C02':raw['C02'],'D':np.concatenate([v for k,v in raw.items() if k.startswith('D_')])}

