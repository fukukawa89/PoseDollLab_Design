"""Build physical internal stop sectors and retain both old and new meshes.
This probe is intentionally not a strength, printing, or manufacture release.
"""
from solid_ops import *
def build():
 original=dict(np.load(CORE));shapes={k:from_tri(t) for k,t in original.items()};adds={};cuts={};cases=[]
 for name,ax,limit in [('C01',0,28),('C02',1,98)]:
  for side in (-1,1):
   # The wide lug root limits nominal bending stress; two opposed journals share
   # the stop only under a future verified tolerance/load-sharing condition.
   lo,hi=sorted((side*6.05,side*8.45));pl,ph=lo-.18,hi+.18
   lug=along(sector(1.2,3.05,-40,40,lo,hi),ax)
   # Bosses become integral with the ring. Their axial bore retains running
   # clearance and the pre-existing inner/outer axial retention shoulders.
   bl,bh=lo-.4,hi+.4
   boss=along(cylinder(4.15,bl,bh)-cylinder(2.12,bl-.1,bh+.1),ax)
   pocket=along(sector(1.35,3.23,-limit-40,limit+40,pl,ph),ax)
   key=f'{name}_{side:+d}';adds[key]=lug;cuts[key]=pocket
   shapes[name]=shapes[name]+lug
   for ring,z0,z1 in [('C14',-20,0),('C15',0,20)]:
    half=box([-30,-30,z0],[30,30,z1])
    shapes[ring]=(shapes[ring]+(boss^half))-pocket
   cases.append({'part':name,'journal_axis':ax,'journal_side':side,'stop_deg':[-limit,limit],'lug_radius_mm':[1.2,3.05],'lug_half_angle_deg':40,'lug_axial_mm':[lo,hi],'pocket_axial_mm':[pl,ph],'outer_boss_radius_mm':4.15,'pocket_radius_mm':3.23})
 folder=OUT/'internal_stops';folder.mkdir(exist_ok=True)
 meshes={k:tri(s) for k,s in shapes.items()};np.savez_compressed(folder/'parts.npz',**meshes)
 np.savez_compressed(folder/'features.npz',**{f'lug_{k}':tri(v) for k,v in adds.items()},**{f'pocket_{k}':tri(v) for k,v in cuts.items()})
 for k,t in meshes.items():export_stl(folder/(k+'.stl'),t)
 save('internal_stops/build.json',{'candidate':'integral journal lugs and split annular stop pockets','source_sha256':sha(CORE),'generator_sha256':sha(__file__),'mesh_weld_grid_mm':.00001,'cases':cases,'parts':{k:record(s) for k,s in shapes.items()},'physical_tested':False,'manufacturing_released':False,'open_issues':['stop reaction and load sharing','weakened bearing/ring sections','assembly order','tolerance and elastic stop overtravel']})
 print(json.dumps({k:record(s) for k,s in shapes.items()},indent=2))
if __name__=='__main__':build()


