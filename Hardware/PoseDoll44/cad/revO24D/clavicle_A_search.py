"""Author search for the revised coaxial clavicle cassette and solid D8 bridge."""
from layout_A_search import *

def main():
    parts,z,ss=read_assembly();data=load(OUT/'verification/joint_local_grids.json')
    cases=[dict(NEUTRAL_ANGLES)]+[c['angles'] for g in data['groups'] for c in g['cases']]
    center=P['clavicle_l']+[0,0,-64.6]
    flip=T(center)@np.diag([1.,1,-1,1])@T(-center)
    for i,p in enumerate(parts):
        fr=p['frame'];tf=None
        if p['name'].startswith('l_clavicle_z_'):tf=flip
        elif p['name'].startswith('r_clavicle_z_'):tf=T([0,0,3])
        if tf is not None:ss[i]=moved(ss[i],np.linalg.inv(F0[fr])@tf@F0[fr])
        if p['name']=='thoracic_centered_tube':
            d=P['spine_05']-P['spine_04'];d/=np.linalg.norm(d)
            ss[i]=moved(tube(P['spine_04']+d*14,P['spine_04']+d*40,4.5,2),np.linalg.inv(F0[fr]))
    excluded=['l_clavicle_vertical_transfer','r_clavicle_vertical_transfer','left_clavicle_seat','right_clavicle_seat']
    fr='l_clavicle_protract';obs=obstacles(parts,ss,fr,cases,excluded);cache={};best=(1e30,None,None)
    socket=next(i for i,p in enumerate(parts) if p['name']=='l_clavicle_z_output_socket')
    bounds=np.array(ss[socket].bounding_box()).reshape(2,3);zc=float(bounds.mean(0)[2]);print('OUTPUT ROOT Z',zc,flush=True)
    for theta in [180,270,225,135,315,90,0]:
      root=[10.5*math.cos(math.radians(theta)),10.5*math.sin(math.radians(theta)),zc]
      for xx in [26,-42,-38,32,-32,38]:
       for yy in [-32,-34,-36,-38,-40,-42,-44]:
        for top in [-20,8,-14,18]:
         points=[root,[root[0],yy,zc],[xx,yy,zc],[xx,yy,top],[20,0,-7]]
         pieces=[beam(x,y,4.2) for x,y in zip(points[:-1],points[1:])]
         shape=union(pieces)-cyl([6,0,0],[23,0,0],4.6)
         hits=score(shape,obs,ss,parts,cache,[np.array(p.bounding_box()).reshape(2,3) for p in pieces]);total=sum(v for n,v in hits)
         if total<best[0]:best=(total,points,sorted({n for n,v in hits}));print('BRIDGE BEST',round(total,5),points,best[2][:10],flush=True)
         if not hits:
          put(OUT/'verification/A_clavicle_route_proposal.json',dict(radius_mm=4,search_radius_mm=4.2,points=points,left_flip_plane_relative_z_mm=-64.6,right_shift_z_mm=3,colliding_parts=[]));return
    put(OUT/'verification/A_clavicle_route_proposal.json',dict(unresolved_volume=best[0],points=best[1],colliding_parts=best[2]))

if __name__=='__main__':main()
