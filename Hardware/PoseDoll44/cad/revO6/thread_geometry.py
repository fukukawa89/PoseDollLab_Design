"""Reference threads with independent material-volume guards; still not production threads."""
import math
import cadquery as cq
RECEIPTS=[]
def thread_sweep(points,z0=-14.,height=9.,pitch=.75):
 # A Frenet pipe keeps the section on the moving radial plane. The older ruled
 # wire-face helper can return isValid=True and still give negative intersections.
 r=sum(p[0] for p in points)/len(points)
 path=cq.Wire.makeHelix(pitch,height,r,center=(0,0,z0))
 tool=cq.Workplane('XZ').polyline([(x,z0+z) for x,z in points]).close().sweep(path,isFrenet=True).val()
 cross=[points[i][0]*points[(i+1)%len(points)][1]-points[(i+1)%len(points)][0]*points[i][1] for i in range(len(points))]
 area=abs(sum(cross))/2
 centroid=sum((points[i][0]+points[(i+1)%len(points)][0])*cross[i] for i in range(len(points)))/(3*sum(cross))
 expected=2*math.pi*centroid*area*height/pitch
 assert tool.isValid() and len(tool.Solids())==1 and abs(tool.Volume()/expected-1)<.02,(tool.Volume(),expected)
 RECEIPTS.append({'operation':'thread_tool','volume_mm3':tool.Volume(),'pappus_reference_mm3':expected,'relative_difference':tool.Volume()/expected-1,'allowed_relative_difference':.02})
 return tool
def checked(base,tool,operation,label):
 vb,vt=base.Volume(),tool.Volume();inter=base.intersect(tool,tol=1e-5).Volume()
 out=base.cut(tool,tol=1e-5) if operation=='cut' else base.fuse(tool,tol=1e-5)
 vo=out.Volume();expected=vb-inter if operation=='cut' else vb+vt-inter
 tol=max(.005,1e-5*(vb+vt))
 report={'operation':operation,'label':label,'base_mm3':vb,'tool_mm3':vt,'intersection_mm3':inter,'result_mm3':vo,'conservation_error_mm3':vo-expected,'tolerance_mm3':tol}
 ok=out.isValid() and len(out.Solids())==1 and -tol<=inter<=min(vb,vt)+tol and abs(vo-expected)<=tol
 if operation=='cut':ok=ok and vo<=vb+tol
 else:ok=ok and max(vb,vt)-tol<=vo<=vb+vt+tol
 report['pass']=bool(ok);RECEIPTS.append(report);assert ok,report
 return out


def overlap_volume(a,b):
 x,y=a.BoundingBox(),b.BoundingBox()
 if not (min(x.xmax,y.xmax)>max(x.xmin,y.xmin)+1e-6 and min(x.ymax,y.ymax)>max(x.ymin,y.ymin)+1e-6 and min(x.zmax,y.zmax)>max(x.zmin,y.zmin)+1e-6):return 0.
 v=a.intersect(b,tol=1e-5).Volume();limit=min(a.Volume(),b.Volume());tol=max(.001,1e-5*limit)
 assert -tol<=v<=limit+tol,('Invalid intersection volume',v,limit)
 return max(0.,v)
