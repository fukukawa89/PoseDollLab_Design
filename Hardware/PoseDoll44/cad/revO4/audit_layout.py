"""Derive O4 occupied volumes from actual KiCad exports and explicit connector frames.
Catalog mating envelopes, service corridors and RF keepouts are separate classes.
"""
from pathlib import Path
import sys,re
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'revO3'))
from compact_joint import *
from revo4_evidence import ArtifactReader,run_paths,save,sha,read
import numpy as np
CATALOG='https://www.jst-mfg.com/product/pdf/eng/eSH.pdf'

def bound_box(bb):return box(bb[3]-bb[0],bb[4]-bb[1],bb[5]-bb[2],tuple((bb[i]+bb[i+3])/2 for i in range(3)))

def main():
    v,o=run_paths();reader=ArtifactReader('electronics');er=reader.json(v/'electronics.json');reports=[]
    for board in er['boards']:
        kind=board['kind'];src=o/'electronics'/kind;folder=o/'pcba'/kind;folder.mkdir(parents=True)
        layout=reader.json(src/'layout.json');model=reader.path(src/layout['step_export']['file']);raw=cq.importers.importStep(str(model)).val();raw_bounds=bounds(raw);real=raw.translate((0,0,-layout['board_mm'][2]));b=bounds(real)
        log=reader.path(src/'step_export.log').read_text(errors='replace');missing=[line.split(' for ')[-1].rstrip('.') for line in log.splitlines() if 'Could not add 3D model for' in line]
        rows=[{'id':'populated_board_available_models','class':'physical_solid','shape':real,'basis':'Actual KiCad STEP, board frame X right Y reversed Z top=0','qualification':'EXPORTED_AVAILABLE_MODELS_ONLY'}]
        connectors=[];unknown=[]
        def add(pid,cls,shape,basis,status):rows.append({'id':pid,'class':cls,'shape':shape,'basis':basis,'qualification':status})
        for c in layout['components']:
            x,y=c['center_xy_mm'];angle=c['rotation_deg'];transform=lambda s:s.rotate((0,0,0),(0,0,1),angle).translate((x,-y,0))
            if c['ref'] in missing:
                # Library F.Fab is an actual body outline, unlike courtyard.
                fab=np.array(c['fab_lines_xy_mm']).reshape(-1,2) if c['fab_lines_xy_mm'] else np.empty((0,2))
                if len(fab):
                    lo=fab.min(axis=0);hi=fab.max(axis=0)
                    is_stm=c['value']=='STM32C011F6U6'
                    height=.6 if is_stm else (.8 if c['value'].startswith('SN74LVC125') else 5.0)
                    if is_stm:lo-=.05;hi+=.05 # ST DS13866 Rev5 table69: D/E<=3.1, A<=0.6 mm.
                    top=-layout['board_mm'][2] if c['back'] else height;bottom=top-height if c['back'] else 0
                    substitute=bound_box([lo[0],-hi[1],bottom,hi[0],-lo[1],top]);add(c['ref']+'_missing_model_envelope','physical_envelope_unqualified',substitute,'ST DS13866 Rev5 table69 max 3.1 x 3.1 x 0.6 mm, terminal/body reference envelope; solder/board tolerance pending' if is_stm else 'Actual footprint F.Fab XY; TI BQA 0.8 mm max height where identified, otherwise unresolved 5 mm sensitivity assumption','NOT_A_COMPLETE_QUALIFIED_COMPONENT_MODEL')
                unknown.append(c['ref'])
            if not c['ref'].startswith('J') or c['ref']=='JP1':continue
            if 'JST_SH_' not in c['footprint']:
                unknown.append(c['ref']+'_mating_model');continue
            n=int(re.search(r'_1x(\d+)',c['footprint']).group(1));side='_SM' in c['footprint'];width=n+1
            if side:
                shell=box(width,5,2.8,(0,-2.075,1.475));axis=(0,-1,0);wire_start=(0,-4.575,1.475)
            else:
                shell=box(width,2.8,5,(0,.45,3.8));axis=(0,0,1);wire_start=(0,.45,6.3)
            mate=transform(shell);pid=c['ref']+'_catalog_mating';add(pid,'physical_envelope_catalog',mate,'SHR-'+str(n).zfill(2)+'V-S envelope; assembled top 6.3 mm / side 6.25 mm x 2.95 mm; catalog pp1-3; KiCad F.Fab/PAD frame','CATALOG_REFERENCE_DIMENSIONS_NOT_TOLERANCE_CERTIFICATION')
            bb=bounds(shell);sweepbb=[min(bb[i],bb[i]+12*axis[i]) for i in range(3)]+[max(bb[i+3],bb[i+3]+12*axis[i]) for i in range(3)]
            add(c['ref']+'_unplug_corridor','service_sweep',transform(bound_box(sweepbb)),'12 mm proposed straight unmating stroke; exact latch/finger/tool clearance absent','UNQUALIFIED_SERVICE_REQUIREMENT')
            for radius in (4,12):
                # Bounds of a 90-degree bend after 3 mm straight neck; all n
                # wire exits remain spread at connector pitch, no magical bundle collapse.
                if side:env=[-width/2,-4.575-3-radius-.4,1.475-.4,width/2,-4.575+.4,1.475+radius+.4]
                else:env=[-width/2,.45-.4,6.3-.4,width/2,.45+radius+.4,6.3+3+radius+.4]
                add(c['ref']+'_bend_R'+str(radius),'wire_bend_sensitivity',transform(bound_box(env)),f'{n} exits, 0.8 mm OD, 3 mm straight neck and R={radius} mm; material and endurance unqualified','SENSITIVITY_NOT_ACCEPTANCE')
            connectors.append({'ref':c['ref'],'header':c['value'].split(' / ')[0],'housing':'SHR-'+str(n).zfill(2)+'V-S','housing_width_mm':width,'entry':'side' if side else 'top','frame_origin_xy_mm':[x,y],'frame_rotation_deg':angle,'frame_source':'Native KiCad origin + F.Fab and pad geometry, not courtyard centroid','catalog':CATALOG,'nominal_assembled_height_mm':2.95 if side else 6.3,'unqualified_tolerance_and_true_mating_features':True})
        if layout['antenna']:
            width=layout['antenna']['keepout_width_mm'];height=layout['antenna']['keepout_beyond_top_mm'];center=layout['board_mm'][0]/2
            add('antenna_manufacturer_air','functional_keepout',box(width,height,30,(center,height/2,0)),'Retained library air region plus proposed +/-15 mm Z exclusion; separate from physical module; RF enabled baseline unchanged','FUNCTIONAL_REQUIREMENT_NOT_PHYSICAL_PART')
        exported=[]
        for q in rows:
            path=folder/(q['id']+'.step');cq.exporters.export(q['shape'],str(path));bb=bounds(q['shape']);exported.append({k:v for k,v in q.items() if k!='shape'}|{'file':path.relative_to(o).as_posix(),'sha256':sha(path),'bounds_mm':bb,'volume_mm3':q['shape'].Volume()})
        physical=[q['shape'] for q in rows if q['class'].startswith('physical')];physicalbb=bounds(cq.Compound.makeCompound(physical));sensitivity={}
        for r in (4,12):
            allshapes=physical+[q['shape'] for q in rows if q['id'].endswith('_R'+str(r))];bb=bounds(cq.Compound.makeCompound(allshapes));sensitivity[str(r)]={'bounds_mm':bb,'dimensions_mm':[bb[i+3]-bb[i] for i in range(3)]}
        report={'kind':kind,'raw_KiCad_export_bounds_mm':raw_bounds,'normalization_z_mm':-layout['board_mm'][2],'board_datum_basis':'Nominal native board thickness shifts KiCad export into board-top Z=0 frame; small stackup/model datum residual requires supplier mating validation','actual_export_bounds_mm':b,'actual_export_solids':len(real.Solids()),'physical_with_declared_substitutes_bounds_mm':physicalbb,'missing_or_unqualified_components':sorted(set(unknown)),'connectors':connectors,'objects':exported,'bend_sensitivity':sensitivity,'status':'BLOCKED_UNQUALIFIED_COMPONENTS_MATING_DATUM_TOLERANCES_AND_HARNESS','full_PCBA_qualified':False}
        reports.append(report);save(folder/'geometry.json',report);print(kind,'physical',physicalbb,'R4',sensitivity['4']['dimensions_mm'],'R12',sensitivity['12']['dimensions_mm'],flush=True)
    save(v/'pcba_geometry.json',{'schema':'revo4-PCBA-geometry-v1','boards':reports,'consumed_inputs':reader.receipt(),'status':'PARTIAL_DERIVED_GEOMETRY','JST_CAD_download_status':'Official STEP request requires personal/company details and emailed delivery; not submitted. Catalog reference envelope used openly.','physical_tested':False})
if __name__=='__main__':main()
