"""Small, explicit channel in the removable printed PCB clip for a reversed FFC."""
from common import *
from sensor_tails import pigtail

def guarded_tail(radius,length,margin=.18):
 ribbon,patch,end=pigtail(radius,length);Q=np.c_[[0,1,0],[0,0,1],[1,0,0]]
 cs=pose(ribbon,Q.T).slice(0).offset(margin,md.JoinType.Round,circular_segments=16)
 guard=pose(cs.extrude(3.5+2*margin),Q,[-1.75-margin,0,0]);bb=np.array(patch.bounding_box())
 return guard+box(bb[:3]-margin,bb[3:]+margin)

def relieve_clip(clip,F,center,radius,length):
 guard=pose(guarded_tail(radius,length),F,center);out=clip-guard
 removed=clip.volume()-out.volume();fraction=removed/clip.volume()
 if solid_count(out)!=1 or fraction>.04:raise ValueError(('Clip channel breaks retention',fraction,solid_count(out)))
 return out,{'removed_mm3':float(removed),'removed_fraction':float(fraction),'components':solid_count(out),'channel_margin_mm':.18,'strength_tested':False}
