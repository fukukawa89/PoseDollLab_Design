"""Load-bearing continuous fork bypasses, screened against actual moving solids."""
from validate import *
from rom_cases import examination_cases

def shape(points,radius):
    return union(beam(np.array(x),np.array(y),radius) for route in points for x,y in zip(route[:-1],route[1:]))

def main():
    parts,z,ss=read_assembly();joints=load(OUT/'profiles/joint_interfaces.json');byname={p['name']:i for i,p in enumerate(parts)};result={}
    cases=[{}]+[v['angles'] for v in examination_cases().values()]+[v['angles'] for v in poses().values()]
    for side in ['l','r']:
        for axis,values in [('shoulder_flex',range(-45,176,10)),('elbow_flex',range(0,146,10)),('knee_flex',range(0,146,10))]:
            for v in values:cases.append({side+'_'+axis:v,side+'_shoulder_abduct':15,side+'_hip_flex':45 if axis=='knee_flex' else 0})
    corners=[]
    for s in ss:
        lo,hi=np.array(s.bounding_box()).reshape(2,3);corners.append(np.array([[hi[k] if mask>>k&1 else lo[k] for k in range(3)] for mask in range(8)]))
    prefixes=['l_shoulder_swing','r_shoulder_swing','lumbar_shoulder_swing','thorax_shoulder_swing','l_ankle_shoulder_swing','r_ankle_shoulder_swing','l_knee','r_knee']
    for pre in prefixes:
        j=next(j for j in joints if j['id']==pre);axis=np.array(j['axis_world']);origin=np.array(j['center_mm']);pi=byname[pre+'_pressure_1'];fr=parts[pi]['frame']
        centroid=(F0[fr]@np.r_[parts[pi]['mass_centroid_mm'],1])[:3]-origin;xx=-(centroid-axis*np.dot(centroid,axis));xx/=np.linalg.norm(xx);W=T(origin,np.c_[xx,axis,np.cross(xx,axis)]);L=np.linalg.inv(F0[fr])@W
        knee=pre.endswith('knee');root=None
        if not knee:
            sn=pre.replace('swing','pitch')+'_output_socket';p=parts[byname[sn]];root=(np.linalg.inv(W)@F0[p['frame']]@np.r_[np.mean(p['bounds_mm'],axis=0),1])[:3]
        obs={}
        for q in cases:
            F=frames(q);back=np.linalg.inv(F[fr])
            for i,p in enumerate(parts):
                if family(fr)==family(p['frame']):continue
                rel=back@F[p['frame']];key=(i,np.round(rel,6).tobytes())
                if key in obs:continue
                vv=corners[i]@rel[:3,:3].T+rel[:3,3];obs[key]=(i,rel,vv.min(0),vv.max(0))
        arr=list(obs.values());mins=np.array([x[2] for x in arr]);maxs=np.array([x[3] for x in arr]);cache={};best=(1e30,None,None)
        for zg in [1,-1]:
          for outer in [24,27,30,33]:
           for height in [17,20,24]:
            ear=j['bearing_span_mm']/2;ro=j['friction_od_mm']/2;radius=3.2
            if knee:
                root=(np.linalg.inv(W)@np.r_[origin+[0,0,23],1])[:3]
                routes=[[root.tolist(),[-outer,0,zg*height],[-outer,sg*ear,zg*height],[-outer,sg*ear,0],[-ro-9,sg*ear,0]] for sg in [-1,1]]
            else:
                cr=np.array(root)+[0,0,zg*(ro+.8)]
                routes=[[cr.tolist(),[root[0],0,zg*height],[-outer,0,zg*height],[-outer,sg*ear,zg*height],[-outer,sg*ear,0],[-ro-9,sg*ear,0]] for sg in [-1,1]]
            candidate=moved(shape(routes,radius),L);bb=np.array(candidate.bounding_box()).reshape(2,3);coll=[];vol=0
            for idx in np.where(np.all(maxs>bb[0],1)&np.all(mins<bb[1],1))[0]:
                i,rel,_,_=arr[idx]
                if idx not in cache:cache[idx]=moved(ss[i],rel)
                v=(candidate^cache[idx]).volume()
                if v>.02:coll.append(parts[i]['name']);vol+=v
            if vol<best[0]:best=(vol,routes,sorted(set(coll)));print(pre,'BEST',zg,outer,height,round(vol,3),best[2][:6],flush=True)
            if not coll:break
           if best[0]==0:break
          if best[0]==0:break
        if best[0]==0:
            worldroutes=[[(W@np.r_[p,1])[:3].tolist() for p in route] for route in best[1]]
            result[pre]=dict(frame=fr,radius_mm=3.2,world_routes_mm=worldroutes)
        else:print('UNRESOLVED',pre,best,flush=True)
    put(HERE/'bridge_layout.json',result)
if __name__=='__main__':main()
