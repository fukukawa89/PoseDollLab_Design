"""Find an initial positive-clearance rectangle; no inference between samples."""
import itertools
from common import *
from clearance import certify

def main():
 meshes=core();rows=[]
 for a,b in itertools.product((15,20,25,30),(90,96,100)):
  r=certify(meshes['C01'],meshes['C02']@pose_matrices(a,b)['C02'].T)
  row={'alpha_deg':a,'beta_deg':b,**r};rows.append(row);print(a,b,r,flush=True)
  save('clearance_rectangle_probe.json',{'cases':rows,'scope':'Initial positive-quadrant probes only; not an accepted rectangle or continuous-motion certificate.'})
if __name__=='__main__':main()
