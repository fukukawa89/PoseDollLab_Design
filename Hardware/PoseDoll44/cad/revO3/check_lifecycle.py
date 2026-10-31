"""O3 life-state CAD: independent wear/compression and discrete cap indexing.
Reference clearances are not supplier tolerance or endurance qualification.
"""
from compact_joint import *
from export_joint import hits
from revo3_evidence import ArtifactReader
import itertools

def constraint_graph(manifest, shapes):
    edges=[]
    def edge(a,b,kind,feature,status='DESIGN_DECLARATION_NOT_STRENGTH_PROOF'):
        edges.append(dict(a=a,b=b,kind=kind,feature=feature,status=status))
    ids={p['part_id'] for p in manifest['parts']}
    for n in sorted(ids-{'one_piece_brake_cup'}):
        if n.startswith('housing_'):
            edge(n,'one_piece_brake_cup','fixed','Registered flange and four axial M2 fasteners; tower is continuous material')
        elif n.startswith(('rear_bush','front_bush')):
            edge(n,'housing_'+n[-1],'fixed_intended','Split bearing fit and axial restraint require supplier definition','UNRESOLVED_FIT_AND_RETENTION')
        elif n.startswith('thrust_'):
            edge(n,'housing_'+n[-1],'captured_axial_locator','Split thrust washer in housing recess; independent of brake preload')
        elif n=='measurement_shaft':
            edge(n,'housing_L','revolute','Two journal bands and collar/thrust washers; nominal 0.05 mm endplay')
            edge(n,'housing_R','revolute','Matched second half of the same journal/locator')
        elif n=='floating_brake_disc':
            edge(n,'measurement_shaft','axial_slide_torque_key','Two integral axial ribs; slip under torque remains unmeasured')
        elif n in ('front_lining_backing','rear_lining_backing','keyed_pressure_plate'):
            edge(n,'one_piece_brake_cup','keyed_axial_slide','Two outside ears in open-ended cup tracks; captured by preload stack')
        elif n.endswith('friction_lining'):
            edge(n,n.replace('friction_lining','lining_backing'),'bonded_fixed_intended','Steel-backed lining adhesive/shear/peel/temperature qualification missing','UNQUALIFIED_BOND_NO_STRENGTH_CREDIT')
            edge(n,'floating_brake_disc','friction_contact','Two compressed faces; no measured coefficient, creep or torque claim')
        elif n=='threaded_adjuster_cap':
            edge(n,'one_piece_brake_cup','helical_then_locked','0.75 mm pitch reference thread and 12-position positive dog')
        elif n.startswith(('disc_spring','spring_')):
            edge(n,'keyed_pressure_plate','preloaded_contact','Coaxial spring/washer stack between pressure plate and threaded cap')
        elif n.startswith('sensor_pcba_'):
            edge(n,'sensor_pcba_6' if n!='sensor_pcba_6' else 'housing_L','fixed_intended','Imported PCBA solder/board assembly; edge clamps on integral shelves')
            if n=='sensor_pcba_6':edge(n,'housing_R','fixed_intended','Second integral shelf and screw clamp')
        elif n.startswith(('pcb_edge_clamp','pcb_clamp_screw')):
            edge(n,'housing_L' if '-7.7' in n else 'housing_R','threaded_clamp','M1.6 reference root core with nominal 1.39 mm tower engagement')
        elif n.startswith(('diametric_magnet','magnet_keeper','keeper_screw')):
            edge(n,'measurement_shaft','fixed_intended','Magnet pocket, keeper and two small screws; thread production details pending')
        else:
            edge(n,'one_piece_brake_cup' if n.startswith(('cup_mount','cap_lock')) else 'housing_L','threaded_fastener','Modeled shank/root and head, production thread fits pending')
    reached={'one_piece_brake_cup'}
    while True:
        new={x for e in edges if e['a'] in reached or e['b'] in reached for x in (e['a'],e['b'])}|reached
        if new==reached:break
        reached=new
    towers=[]
    for side,sgn in [('L',-1),('R',1)]:
        shape=shapes['housing_'+side]
        bridge=shape.intersect(box(3.0,2.0,.1,(sgn*7.7,0,19.95)))
        towers.append({'housing':'housing_'+side,'solid_count':len(shape.Solids()),'base_connection_section_volume_mm3':bridge.Volume(),'status':'PASS_INTEGRAL_BASE_GEOMETRY' if len(shape.Solids())==1 and bridge.Volume()>.1 else 'FAIL'})
    return {'parts':sorted(ids),'edges':edges,'unconnected_part_ids':sorted(ids-reached),'sensor_towers':towers,'part_coverage_complete':ids<=reached,'status':'PARTIAL_INTEGRAL_TOWER_FIXED_OTHER_FITS_AND_BONDS_UNQUALIFIED','physical_constraint_rank_or_stiffness':'NOT_RUN','declaration_is_not_a_gate_pass':True}

def main():
    verify,out=run_paths();reader=ArtifactReader('joint');m=reader.json(verify/'joint.json');folder=out/'joint'
    shapes={p['part_id']:cq.importers.importStep(str(reader.path(folder/p['step_file']))).val() for p in m['parts']}
    config=read(ROOT/'mechanical_manifest/lifecycle_states_revO3.json')
    states=[];cache={};cache_hits=0
    for wf,wr in config['wear_pairs_mm']:
        assert wf+wr<=TOTAL_WEAR_BUDGET+1e-9 and max(wf,wr)<=MAX_SINGLE_FACE_WEAR+1e-9
        for cf,cr in config['compression_pairs_mm']:
            df=wf+cf;dr=wf+wr+cf+cr
            capdz=math.ceil((dr-1e-9)/(THREAD_PITCH/12))*(THREAD_PITCH/12) if dr else 0
            h=(2.35+dr-capdz)/4
            current=dict(shapes)
            current['front_friction_lining']=ring(12,4.2,-1.4+df,-.8)
            current['rear_friction_lining']=ring(12,4.2,-3.5+dr,-2.9+df)
            current['floating_brake_disc']=shapes['floating_brake_disc'].translate((0,0,df))
            for n in ('rear_lining_backing','keyed_pressure_plate','spring_front_washer'):current[n]=shapes[n].translate((0,0,dr))
            for n in ('threaded_adjuster_cap','spring_rear_washer'):current[n]=shapes[n].translate((0,0,capdz))
            current['threaded_adjuster_cap']=current['threaded_adjuster_cap'].rotate((0,0,0),(0,0,1),capdz/THREAD_PITCH*360)
            for i in range(4):current['disc_spring_'+str(i+1)]=disc_spring(-7.55+STACK_SHIFT+capdz+i*h,h,i%2==1)
            # Every pair involving a changed body is checked. Unchanged pairs
            # refer to the sealed all-pairs nominal CAD test, not a contact whitelist.
            moved={n for n in current if current[n] is not shapes[n]};collisions=[];pairs=0
            sig={n:() for n in current}
            for n in ('front_friction_lining','floating_brake_disc'):sig[n]=(round(df,6),)
            sig['rear_friction_lining']=(round(df,6),round(dr,6))
            for n in ('rear_lining_backing','keyed_pressure_plate','spring_front_washer'):sig[n]=(round(dr,6),)
            for n in ('threaded_adjuster_cap','spring_rear_washer'):sig[n]=(round(capdz,6),)
            for i in range(4):sig['disc_spring_'+str(i+1)]=(round(capdz,6),round(h,6))
            for a,b in itertools.combinations(current,2):
                if a not in moved and b not in moved:continue
                ba,bb=bounds(current[a]),bounds(current[b])
                if not all(min(ba[k+3],bb[k+3])-max(ba[k],bb[k])>1e-6 for k in range(3)):continue
                key=(a,sig[a],b,sig[b])
                if key not in cache:cache[key]=current[a].intersect(current[b]).Volume();pairs+=1
                else:cache_hits+=1
                vol=cache[key]
                if vol>1e-4:collisions.append({'a':a,'b':b,'volume_mm3':vol})
            q={'front_wear_mm':wf,'rear_wear_mm':wr,'front_compression_mm':cf,'rear_compression_mm':cr,'cap_advance_mm':capdz,'cap_turns':capdz/THREAD_PITCH,'cap_index_step_mm':THREAD_PITCH/12,'spring_working_height_mm':h,'extra_spring_compression_from_indexing_mm':capdz-dr,'remaining_lining_before_compression_mm':[.6-wf,.6-wr],'retention_metal_intersections':collisions,'BRep_pairs':pairs,'status':'FAIL' if collisions else 'PASS_SCOPED_LIFE_GEOMETRY'}
            states.append(q);print('LIFE',wf,wr,cf,cr,q['status'],len(collisions),flush=True)
    graph=constraint_graph(m,shapes)
    # Explicit worst-stack dimensional budget for metal-to-disc separation.
    # It does not simulate deformed friction contact or joint-wide tilt.
    clearance=.6-MAX_SINGLE_FACE_WEAR-max(max(x) for x in config['compression_pairs_mm'])-config['backing_face_error_mm']-config['rotor_face_runout_mm']
    report={'schema':'revo3-life-v1','cached_identical_pair_checks':cache_hits,'unique_BRep_pair_checks':len(cache),'states':states,'status':'FAIL' if any(q['status']=='FAIL' for q in states) else 'PASS_SCOPED_LIFE_GEOMETRY','nominal_dependency_status':m['nominal_solid_status'],'constraint_graph':graph,'tolerance_budget':{'status':'CONDITIONAL_DIMENSION_BUDGET_ONLY','minimum_metal_face_gap_mm':clearance,'assumptions':config,'joint_wide_tolerance_BRep_sweep':'NOT_RUN','minimum_gap_positive':clearance>0},'not_proven':['Bonded lining strength, compliance and wear distribution','Full torque-loaded sliding key path and parasitic axial force','Bore and fastener deformation, actual assembly tools','All tolerance extrema combined with rotor tilt and temperature'],'consumed_inputs':reader.receipt(),'physical_tested':False,'manufacturing_released':False}
    save(verify/'lifecycle.json',report);save(out/'joint_constraints.json',graph)
if __name__=='__main__':main()
