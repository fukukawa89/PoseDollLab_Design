from electronics_carrier import *
def main():
 b=p.LoadBoard(str(D/(NAME+'.kicad_pcb')));layers=[p.F_Cu,p.In1_Cu,p.In2_Cu,p.B_Cu];xy=lambda q:[p.ToMM(q.x),p.ToMM(q.y)];obs=[]
 for f in b.GetFootprints():
  for a in f.Pads():
   bb=a.GetBoundingBox();obs.append(dict(kind='pad',net=a.GetNetname(),ref=f.GetReference(),num=a.GetNumber(),center=xy(a.GetPosition()),box=[p.ToMM(bb.GetLeft()),p.ToMM(bb.GetTop()),p.ToMM(bb.GetRight()),p.ToMM(bb.GetBottom())],layers=[i for i,L in enumerate(layers) if a.IsOnLayer(L)],smd=a.GetAttribute()==p.PAD_ATTRIB_SMD))
 for t in b.GetTracks():
  if isinstance(t,p.PCB_VIA):obs.append(dict(kind='via',net=t.GetNetname(),center=xy(t.GetPosition()),radius=p.ToMM(t.GetWidth(p.F_Cu))/2,layers=[0,1,2,3]))
  else:obs.append(dict(kind='track',net=t.GetNetname(),start=xy(t.GetStart()),end=xy(t.GetEnd()),radius=p.ToMM(t.GetWidth())/2,layers=[layers.index(t.GetLayer())]))
 put(D/'routing_obstacles.json',obs)
if __name__=='__main__':main()
