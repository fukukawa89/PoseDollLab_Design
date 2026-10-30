from production import *
parts=read_saved();fr='l_clavicle_elevate';members=[moved(p['s'],np.linalg.inv(F0[fr])@F0[p['frame']]) for p in parts if physical_frame(p['frame'])==fr and p['role'] in ['structure','rotor','shell']];s=physical_components(union(members))[0]
for orig in [False,True]:
 for tol in [.001,.01,.02,.04,.05]:
  t=(s.as_original() if orig else s).simplify(tol);v,f=base.a.mesh_data(t);R,size=orientation(t);m=trimesh.Trimesh(v,f,process=False);m.apply_transform(R)
  rt=trimesh.load(io.BytesIO(m.export(file_type='stl')),file_type='stl',process=True)
  mesh=md.Mesh64(np.array(rt.vertices,dtype=np.float64,copy=True),np.array(rt.faces,dtype=np.uint64,copy=True),tolerance=.0001);mesh.merge();ms=md.Manifold(mesh)
  vv,ff=base.a.mesh_data(ms);mm=trimesh.Trimesh(vv,ff,process=True);rt2=trimesh.load(io.BytesIO(mm.export(file_type='stl')),file_type='stl',process=True)
  rt3=rt.copy();rt3.update_faces(rt3.nondegenerate_faces());rt3.update_faces(rt3.unique_faces());rt3.remove_unreferenced_vertices();trimesh.repair.fill_holes(rt3)
  rt4=trimesh.Trimesh(rt.vertices,rt.faces,process=True,validate=True);trimesh.repair.fill_holes(rt4)
  _,inv,count=np.unique(np.sort(rt.faces,axis=1),axis=0,return_inverse=True,return_counts=True);rt5=rt.copy();rt5.update_faces((count[inv]==1)&rt5.nondegenerate_faces());trimesh.repair.fill_holes(rt5)
  ec=np.bincount(rt.edges_unique_inverse);bad=rt.edges_unique[ec!=2];lens=np.linalg.norm(rt.vertices[bad[:,0]]-rt.vertices[bad[:,1]],axis=1)
  print(orig,tol,rt.is_watertight,ms.status(),mm.is_watertight,rt2.is_watertight,rt3.is_watertight,rt4.is_watertight,rt5.is_watertight,len(rt.faces),t.volume()-s.volume(),'bad',len(bad),max(lens,default=0),flush=True)
  if orig and tol==.02:
   for e in bad:
    pts=(rt.vertices[e]-R[:3,3])@R[:3,:3];mid=pts.mean(0);test=md.Manifold.sphere(.1,12).translate(mid);near=[]
    for p in parts:
     if physical_frame(p['frame'])!=fr:continue
     shape=moved(p['s'],np.linalg.inv(F0[fr])@F0[p['frame']])
     if (shape^test).volume()>1e-8:near.append(p['name'])
    print('EDGE',pts.tolist(),'near',near,flush=True)
