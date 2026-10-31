"""Generate nominal L6-R2 CAD and evaluate physical solid intersections separately from gates."""
from compact_joint import *
import itertools,json,os

def hits(rows):
    found=[];boxes={q['name']:bounds(q['shape']) for q in rows}
    for a,b in itertools.combinations(rows,2):
        ba,bb=boxes[a['name']],boxes[b['name']]
        if not all(min(ba[k+3],bb[k+3])-max(ba[k],bb[k])>1e-6 for k in range(3)):continue
        v=a['shape'].intersect(b['shape']).Volume()
        if v>1e-4:found.append({'a':a['name'],'b':b['name'],'volume_mm3':v})
    return found

def main():
    verify,out=run_paths();folder=out/'joint';folder.mkdir(parents=True,exist_ok=True)
    rows,tools=module();print('Generated',len(rows),'solids, checking intersections',flush=True)
    baseline_rows,_=module(lighten=False)
    baseline_mass={q['name']:q['shape'].Volume()*DENSITY[q['material']] for q in baseline_rows}
    reduction=[{'part_id':q['name'],'before_volume_mm3':next(b['shape'].Volume() for b in baseline_rows if b['name']==q['name']),'after_volume_mm3':q['shape'].Volume(),'before_mass_g':baseline_mass[q['name']],'after_mass_g':q['shape'].Volume()*DENSITY[q['material']]} for q in rows if abs(baseline_mass[q['name']]-q['shape'].Volume()*DENSITY[q['material']])>.001]
    collisions=hits(rows);print('INTERSECTIONS',json.dumps(collisions),flush=True)
    mass=[];meshes=[];ass=cq.Assembly(name='L6_R2_NOT_MANUFACTURING_RELEASE')
    for q in rows:
        s=q['shape'];center=s.Center();g=s.Volume()*DENSITY[q['material']]
        mass.append({'part_id':q['name'],'owner':q['owner'],'material':q['material'],'density_g_mm3':DENSITY[q['material']],'mass_g':g,'local_com_mm':[center.x,center.y,center.z],'volume_mm3':s.Volume(),'bounds_mm':bounds(s),'mass_source':'CAD volume times material-class density estimate','uncertainty_fraction':.25 if q['material'] in ('package','connector','ceramic','lining') else .05,'group':q['group'],'note':q['note']})
        ass.add(s,name=q['name'],color=cq.Color(COLORS[q['material']]))
        cq.exporters.export(s,str(folder/(q['name']+'.step')))
        verts,tri=s.tessellate(.18,.25)
        meshes.append({'name':q['name'],'owner':q['owner'],'color':COLORS[q['material']],'vertices':[[round(v.x,4),round(v.y,4),round(v.z,4)] for v in verts],'triangles':tri})
    ass.save(str(folder/'L6_R2_assembly.step'));save(folder/'mesh.json',meshes)
    for name,shape in tools.items():cq.exporters.export(shape,str(folder/(name+'.step')))
    tool_hits=hits([{'name':'hollow_pin_spanner','shape':tools['hollow_pin_spanner']},*rows]);tool_hits=[q for q in tool_hits if 'hollow_pin_spanner' in (q['a'],q['b'])]
    shape=cq.Compound.makeCompound([q['shape'] for q in rows]);bb=bounds(shape)
    report={'schema':'revo2-joint-v1','run_id':os.environ['REVO2_RUN_ID'],'name':'L6-R2','cad_valid':all(q['shape'].isValid() for q in rows),'part_count':len(rows),'solid_intersections':collisions,'nominal_solid_status':'FAIL' if collisions else 'PASS_NOMINAL_GEOMETRY_ONLY','tool_solid_intersections':tool_hits,'lightening':{'baseline_same_parts_mass_g':sum(baseline_mass.values()),'changed_parts':reduction,'added_parts':[],'net_mass_saved_g':sum(baseline_mass.values())-sum(q['mass_g'] for q in mass),'scope':'13 mm cartridge OD and four-rib rear-cap pockets; no thread-root, stop or bearing-seat removal; FEA/physical qualification pending'},'modeled_mass_g':sum(q['mass_g'] for q in mass),'bounds_mm':bb,'dimensions_mm':[bb[k+3]-bb[k] for k in range(3)],'parts':mass,'single_connected_solid_per_part':all(len(q['shape'].Solids())==1 for q in rows),'bearing_span_mm':14,'nominal_diametral_clearance_mm':.02,'study_worst_diametral_clearance_mm':.03,'clearance_tilt_scale_deg':math.degrees(math.atan(.03/14)),'nominal_shaft_endplay_mm':.05,'sensor_magnet_face_gap_mm':1.5,'thread':{'pitch_mm':THREAD_PITCH,'major_diameter_nominal_mm':28,'modeled_cap_engagement_length_mm':4.0,'helical_length_mm':3.5,'female_axial_range_mm':[-13.4,-4.7],'cap_working_range_mm':[-12.05,-8.05],'cap_free_range_mm':[-13.1,-9.1],'radial_root_wall_mm':.97,'geometry':'Matched explicit 60-degree reference helices with radial/flank clearances, not production thread gauging'},'brake_faces':2,'spring':{'candidate':'SCHNORR 002100','count':4,'arrangement':'series','catalog_force_N':326,'free_stack_mm':3.4,'catalog_stack_mm':2.35,'washer_total_mm':1.0,'free_cavity_required_mm':4.4,'catalog_point_not_qualification':True},'nominal_force_path':['one_piece_brake_cup','front_friction_lining','floating_brake_disc','rear_friction_lining','wear_sheet','keyed_pressure_plate','spring_front_washer','disc_spring_4..1','spring_rear_washer','threaded_adjuster_cap','one_piece_brake_cup'],'shaft_axial_locator_path':['housing_R/L','thrust_rear_L/R or thrust_front_L/R','measurement_shaft integral collar'],'physical_tested':False,'manufacturing_released':False,'unresolved':['Supplier production tolerances, split-seat distortion and matched-bore finishing','Lining coefficient/pressure/wear and full spring curve/tolerance','Shaft-key backlash, sliding under torque and parasitic axial forces','Dynamic assembly and tool sweeps follow in separate report','Exact mating plug/wire interface and complete multi-axis embedding']}
    save(verify/'joint.json',report);save(folder/'manifest.json',report)
    print('L6-R2',report['nominal_solid_status'],'mass_g',report['modeled_mass_g'],'tool_hits',len(tool_hits),flush=True)
if __name__=='__main__':main()
