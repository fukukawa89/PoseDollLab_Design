"""Traceability, thin-bridge controls, attachment inventory and diagnostic cases."""
from groups import *
import body_inventory

def main():
    body_inventory.main();parts,z,ss=read_assembly();digest=sha(OUT/'assembly_meshes.npz')
    base=box([0,0,0],[10,18,6])+box([20,0,0],[30,18,6]);weak=core(base+box([9,0,0],[21,18,.2]),.25);strong=core(base+box([9,0,0],[21,18,3.2]),.25)
    rows=[]
    for body in load(OUT/'verification/printed_body_connections.json')['rows']:
        names=body['source_primitives'];mechanism='Continuous joined printed material; parent/child connection uses the named keyed metal joint interface.'
        if body['frame']=='l_clavicle_protract':mechanism='One-piece custom machined 304 steel carrier, including both sockets and the sensor seat. No printed-to-metal bonded joint. Keyed caps and transverse capture retain it.'
        elif any(n.endswith(('W06','W07')) for n in names):mechanism='Independent S1 cup, captured and preloaded by the two M3 cross screws; ball guide heads are wider than the guide slots.'
        elif any(n.endswith(('W01','W02')) for n in names):mechanism='S1 split ball halves assembled by two M2 bolts; guide shoulders captured by metal washer and M2 nut. The review union retains the source-half IDs; split halves must be manufactured separately.'
        elif any(n.endswith('palm') for n in names):mechanism='Square palm key carries torque; transverse M2 bolt, washers and locking nut prevent withdrawal.'
        elif len(names)==1 and any(n.endswith(('hip_abduction_hub','hip_twist_hub')) for n in names):mechanism='Independent hex socket on the stepped metal core, captured axially by two keyed caps. D3 cross pin couples core/shaft; separate outlet is cross-pinned to the same shaft.'
        rows.append(dict(body=body['body'],frame=body['frame'],source_primitives=names,status=body['status'],mechanical_connection=mechanism))
    controls=dict(weak_edge_mm=[.2,18],weak_detected=len(weak[0]['substantial_core_volumes_mm3'])==2,strong_bridge_mm=[3.2,18],strong_single_core=len(strong[0]['substantial_core_volumes_mm3'])==1,weak=weak,strong=strong)
    loads=load(OUT/'verification/preload_retention_loads.json');head=next(x for x in loads['rows'] if x['axis']=='neck_yaw');force=head['downstream_solid_mass_g']/1000*9.80665*1.875
    stress=32*(force/2*31)/(math.pi*4.6**3);deflection=(force/2)*7.5**3/(3*1500*(math.pi*4.6**4/64))
    headcheck=dict(assumed_allowable_MPa=8,diameter_mm=4.6,branch_length_mm=7.5,downstream_mass_g=head['downstream_solid_mass_g'],load_factor=1.875,conservative_moment_arm_mm=31,bending_stress_MPa=stress,elastic_deflection_mm=deflection,status='PASS_CONDITIONAL' if stress<=8 else 'FAIL',scope='Two D4.6 head branches. Full neck-yaw downstream mass assigned to them conservatively; not a global chassis FEA.')
    good=all(r['status']=='PASS_SCREEN' for r in rows) and controls['weak_detected'] and controls['strong_single_core'] and stress<=8
    put(OUT/'verification/connection_review.json',dict(status='PASS_SCREEN_CONDITIONAL' if good else 'FAIL',geometry_sha256=digest,body_count=len(rows),controls=controls,attachments=rows,head_branch=headcheck,scope='Material-body connectivity at 0.5 mm erosion and named positive mechanical interfaces. This catches the reported 0.20 mm bridge mode but does not establish lifetime stiffness, FDM anisotropy or fatigue by itself. Single CSG feature counts are not equated to physical part counts.'))
    e=Collision(parts,ss);allhits=e.check(NEUTRAL_ANGLES,scope='all');hits=[h for h in allhits if h['required_adjacent']]
    put(OUT/'verification/A_pose_contacts.json',dict(status='PASS' if not hits else 'FAIL',geometry_sha256=digest,angles=NEUTRAL_ANGLES,required_adjacent_count=len(hits),nonadjacent_advisory_count=len(allhits)-len(hits),all_contacts=allhits,scope='A neutral. Adjacent anatomy is the acceptance requirement. Non-adjacent contacts remain visible as pose-adjustment advice under user instruction.'))
    a=load(OUT/'reference/engineering_sources.json');extra=[
      dict(id='shaft_yield',url='https://steelnavigator.ovako.com/steel-grades/42crmo4/',use='Custom shafts: certified yield >=750 MPa. Lumbar flexion: certified 6115 / 42CrMnMo4-4 +QT, minimum 940 MPa retained after machining; source stock 25–60 mm. Not a rating for generic annealed rods.'),
      dict(id='retaining_compound',url='https://next.henkel-adhesives.com/ca/en/products/industrial-adhesives/central-pdp.html/loctite-603/BP000000153475/variation/231099.html',use='Steel retaining compound reference. The design uses a separately qualified 2 MPa shear allowable, not the advertised typical strength as a guaranteed joint rating.'),
      dict(id='magnetic_sensor',url='https://www.ti.com/lit/ds/symlink/tmag5170.pdf',use='Three-axis sensing, angle calculation and gain/offset compensation. Only ideal observability is validated; no populated board or measured magnetic accuracy is claimed.')]
    a['sources']=[x for x in a['sources'] if x['id'] not in [v['id'] for v in extra]]+extra;a['design_assumptions_not_measurements']['shaft_min_yield_MPa']=dict(normal=750,lumbar_flex=940);put(OUT/'reference/engineering_sources.json',a)
    print('CONNECTION',good,'HEAD STRESS',stress,'A REQUIRED CONTACTS',len(hits),'A TOTAL CONTACTS',len(allhits),flush=True)

if __name__=='__main__':main()
