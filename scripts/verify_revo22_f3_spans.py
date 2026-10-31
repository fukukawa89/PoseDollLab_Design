"""Conservative span diagnostics on native G-code, with analytic controls.
Geometric bead coverage only; no melt, cooling, adhesion or strength model.
"""
import json,sys
from pathlib import Path
import numpy as np,shapely
from shapely.geometry import LineString,Point,box as box2
from o22_f3_gcode import extract_detailed
from build_revo22_fins_v3 import md,polygon

def spans(line,covered,minimum=2.):
    diff=line.difference(covered)
    pieces=list(diff.geoms) if hasattr(diff,'geoms') else [diff]
    out=[]
    for g in pieces:
        if g.geom_type!='LineString' or g.length<=minimum:continue
        q=np.asarray(g.coords);chord=float(np.linalg.norm(q[-1]-q[0]));anchors=sum(covered.distance(Point(p))<.002 for p in (q[0],q[-1]))
        out.append({'length_mm':float(g.length),'chord_mm':chord,'end_anchors_in_previous_layer':int(anchors),'straightness':chord/max(g.length,1e-9),'bounds_mm':list(g.bounds)})
    return out

def controls():
    two=box2(-1,-1,0,1).union(box2(5,-1,6,1))
    a=spans(LineString([[-.5,0],[5.5,0]]),two)
    b=spans(LineString([[-.5,0],[5,0]]),box2(-1,-1,0,1))
    c=spans(LineString([[1,0],[5,0]]),box2(-1,-1,0,1))
    d=spans(LineString([[-.5,0],[.5,0]]),box2(-1,-1,1,1))
    assert [a[0]['end_anchors_in_previous_layer'],b[0]['end_anchors_in_previous_layer'],c[0]['end_anchors_in_previous_layer']]==[2,1,0] and not d
    return {'two_ended_bridge':a,'cantilever':b,'detached_path':c,'fully_backed':d,'passed':True}

def check(path,out):
    rep,raw,fi,names=extract_detailed(path,arc_tolerance_mm=.015,max_arc_segment_mm=.6)
    a=np.asarray(raw).reshape(-1,9);fi=np.asarray(fi);mask=a[:,7]==0;a=a[mask];fi=fi[mask]
    previous=None;records=[]
    for lid in np.unique(a[:,6]):
        mask=a[:,6]==lid;ar=a[mask];features=fi[mask];z=float(np.median(ar[:,5]))
        xy=np.stack([ar[:,:2],ar[:,3:5]],axis=1);buffers=shapely.buffer(shapely.linestrings(xy),np.maximum(ar[:,8]/2,.001),quad_segs=3)
        contours=[np.round(np.asarray(g.exterior.coords)[:-1][::-1],4) for g in buffers if not g.is_empty]
        # normalize orientation before Clipper union
        contours=[p if np.sum(p[:,0]*np.roll(p[:,1],-1)-p[:,1]*np.roll(p[:,0],-1))>0 else p[::-1] for p in contours]
        current=polygon(md.CrossSection(contours))
        if previous is not None:
            start=0;cache={}
            for end in range(1,len(ar)+1):
                boundary=end==len(ar) or features[end]!=features[start] or abs(ar[end,8]-ar[start,8])>.025 or np.linalg.norm(ar[end,:2]-ar[end-1,3:5])>.005
                if not boundary:continue
                feature=names[int(features[start])]
                if feature not in ['Sparse infill','Internal sparse infill','Gap infill']:
                    pts=np.vstack([ar[start,:2],ar[start:end,3:5]])
                    if len(pts)>1:
                        width=round(float(ar[start,8]),2)
                        if width not in cache:cache[width]=previous.buffer(width/2+.025,quad_segs=4)
                        for row in spans(LineString(pts),cache[width]):
                            row.update(z_mm=z,feature=feature);records.append(row)
                start=end
        previous=current
    result={'method':'Native extrusion centerline portions with no previous-layer bead overlap, allowing current half-width plus 0.025 mm. Only spans longer than 2 mm. Sparse/gap infill excluded. End anchors use previous layer only; curved paths and same-layer support need review. Not a strength or melt-flow simulation.',
        'gcode_sha256':rep['gcode_sha256'],'project':str(path),'controls':controls(),'features':rep['features'],'span_count':len(records),
        'max_span_mm':max([r['length_mm'] for r in records],default=0),'zero_anchor_spans':sum(r['end_anchors_in_previous_layer']==0 for r in records),'one_anchor_spans':sum(r['end_anchors_in_previous_layer']==1 for r in records),'spans':records}
    Path(out).write_text(json.dumps(result,indent=2),encoding='utf8')
    print(Path(path).parent.parent.name,'SPANS',len(records),'max',result['max_span_mm'],'zero',result['zero_anchor_spans'],'one',result['one_anchor_spans'],flush=True)
    return result

if __name__=='__main__':
    if len(sys.argv)>1:check(Path(sys.argv[1]),Path(sys.argv[2]))
    else:
        from explore_revo22_f3 import O
        for candidate in (O/'spring_candidates').iterdir():
            if not candidate.is_dir():continue
            projects=list((candidate/'projects').glob('*.3mf'))
            if projects:check(projects[0],candidate/'verification/bridge_spans.json')
