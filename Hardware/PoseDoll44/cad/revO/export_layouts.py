"""Export 10 skeleton/component STEP studies. Never labels them a complete assembly."""
from pathlib import Path
import sys
import numpy as np
import cadquery as cq
from compact_joint import box, bounds, ROOT, save
sys.path.insert(0,str(ROOT.parents[1]/'scripts'))
from revo_common import read, sha
OUT=ROOT/'generated/revO'

def rod(a,b,r):
    a=np.array(a);v=np.array(b)-a;length=np.linalg.norm(v)
    return cq.Solid.makeCylinder(r,float(length),cq.Vector(*a),cq.Vector(*(v/length)))

def main():
    summary={}
    for key,scene in read(OUT/'layout_data.json').items():
        ass=cq.Assembly(name=key+'_LAYOUT_NOT_COMPLETE_ASSEMBLY');shapes=[]
        def add(name,sh,color):
            assert sh.isValid(),name
            ass.add(sh,name=name,color=cq.Color(*color));shapes.append(sh)
        for i,line in enumerate(scene['links']):add(f'ANATOMY_LINK_{i}',rod(line['a'],line['b'],1.1),(.6,.67,.75))
        for i,axis in enumerate(scene['axes']):
            add(f'AXIS_ORIGIN_MARKER_{i}',cq.Solid.makeSphere(2.4,cq.Vector(*axis['position'])),(.3,.57,.85))
        for node,placement in scene['boards'].items():
            pcb=read(ROOT/f'electronics/revO/node_{placement["ports"]}port/layout.json')
            w,h,thick=pcb['board_mm'];cx,cy,cz=placement['center']
            add(node+'_board',box(thick,w,h,(cx,cy,cz)),(.15,.54,.42))
            for comp in pcb['components']:
                x0,y0,x1,y1=comp['courtyard_xy_mm'];ht=comp['height_max_assumed_mm'];sgn=-1 if comp['back'] else 1
                loc=(cx+sgn*(thick/2+ht/2),cy+(x0+x1)/2-w/2,cz-(y0+y1)/2+h/2)
                # Actual XY courtyard / assumed maximum package Z, labelled accordingly.
                add(node+'_'+comp['ref'].replace('#','flag'),box(ht,x1-x0,y1-y0,loc),(.25,.35,.37))
        folder=OUT/'layouts'/key
        ass.save(str(folder/(key+'_component_layout.step')))
        bb=bounds(cq.Compound.makeCompound(shapes))
        summary[key]=dict(status='SKELETON_AND_PCBA_COMPONENT_ENVELOPES_ONLY',layout_bbox_mm=bb,
                          full_body_height_mm=None,full_body_mass_g=None,full_assembly_delivered=False,
                          pcba_component_height_source='conservative engineering assumptions; exact footprints, not vendor package models',
                          STEP=str((folder/(key+'_component_layout.step')).relative_to(ROOT)),
                          source_scene_sha256=sha(folder/'layout_scene.json'))
        print(key,'component STEP exported',flush=True)
    save(ROOT/'verification/revO/layout_cad.json',summary)

if __name__=='__main__':main()
