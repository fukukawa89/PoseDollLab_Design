"""Compact rigid palm direction indicator; no UE finger geometry constraint."""
from fullbody import *

def hand(side):
    sg=1 if side=='l' else -1
    palm=box([-9,-3.5,-42],[10,3.5,-28])
    palm+=beam([-5.5,0,-42],[6.5,0,-42],3.5)
    palm+=beam([-6,0,-31],[-13,0,-35],4)
    palm+=box([-6,-6,-31.5],[6,6,-21.8])
    palm-=beam([-5,sg*3.9,-35],[6,sg*3.9,-36],1.2)
    palm+=beam([1,-sg*3.6,-33],[1,-sg*3.6,-40],1.1)
    palm-=box([-3.2,-3.2,-31.2],[3.2,3.2,-21.7])
    palm-=cyl([-18,0,-27],[18,0,-27],1.15)
    return palm,dict(side=side,frame=side+'_wrist_flex',fingers=[],
        design='One-piece compact mitten direction indicator; UE finger positions are not design constraints',
        palm_normal_local=[0,sg,0],dorsal_normal_local=[0,-sg,0],
        palm_cues='One broad recessed groove',dorsal_cues='One raised longitudinal ridge',
        thumb_side='Negative local X',finger_motion='None; no additional physical DOF',
        root_connection='Continuous 7 mm thick palm into 12 mm square-key boss; original M2 capture unchanged')
