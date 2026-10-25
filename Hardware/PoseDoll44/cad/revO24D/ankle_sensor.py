"""Compact outboard ankle encoder on the unchanged shaft/magnet axis."""
from fullbody import *

def apply(D):
    pre='l_ankle_shoulder_pitch';origin=P['foot_l'];fr='l_knee_flex'
    magnet=next(p for p in D.parts if p['name']==pre+'_magnet')
    bb=np.array(moved(magnet['s'],F0[magnet['frame']]).bounding_box()).reshape(2,3)
    axial=float(bb.mean(0)[0]-origin[0]);radius=11.
    W=T(origin+[axial,radius,0],np.c_[[1,0,0],[0,0,1],[0,-1,0]])
    pcb=next(p for p in D.parts if p['name']==pre+'_pcb')
    pcb['s']=moved(box([-6,-5,-1],[6,5,1]),np.linalg.inv(F0[fr])@W)
    pcb['notes']='Existing centred-IC 12 x 10 S1 native PCB, outboard radial layout at 11 mm from the unchanged shaft magnet. Ideal angle observability only; field amplitude and metal interference require calibration/bench qualification.'
    holder=next(p for p in D.parts if p['name']==pre+'_sensor_holder')
    shape=moved(box([-7.8,-6.8,-1.8],[7.8,6.8,1.8])-box([-6.15,-5.15,-2],[6.15,5.15,2]),W)
    for sg in [-1,1]:
        points=[origin+[axial+12,9,sg*3.5],origin+[axial+12,radius,sg*3.5],origin+[axial+7,radius,sg*6]]
        shape+=union(beam(x,y,1.8) for x,y in zip(points[:-1],points[1:]))
    _=shape.volume()  # Resolve CSG before further frame transforms / pigtail cuts.
    holder['s']=moved(shape,np.linalg.inv(F0[fr]))
    holder['notes']='Outboard full-board perimeter seat with two continuous D3.6 root struts. Keeps the original 140 degree knee target clear; no joint centre or axis line is translated.'
    for j in D.joints:
        if j['id']==pre:j.update(sensor_layout='radial',sensor_radial_distance_mm=radius)
