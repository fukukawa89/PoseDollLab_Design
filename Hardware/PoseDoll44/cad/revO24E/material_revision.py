"""Material-only correction following E full-body calculations; mesh unchanged."""
from build import *
def main():
    a=load(OUT/'assembly.json');j=load(OUT/'profiles/joint_interfaces.json');by={p['name']:p for p in a['parts']};rows=[]
    for it in j:
        pre=it['id']
        if pre not in ['lumbar_shoulder_pitch','l_hip_pitch','r_hip_pitch']:continue
        it['front_cap_min_yield_MPa']=940;p=by[pre+'_keyed_output_cap'];p.update(material='42CrMo4 QT; certified Rp0.2 >=940 MPa after machining',sku=f'E_CAP_D{it["bearing_diameter_mm"]}_QT940_{pre}',revision_change=True);rows.append(dict(part=p['name'],min_yield_MPa=940))
        if pre.startswith(('l_hip','r_hip')):
            it['cap_min_yield_MPa']=940;p=by[pre+'_rear_thrust_cap'];p.update(material='42CrMo4 QT; certified Rp0.2 >=940 MPa after machining',sku='E_REAR_CAP_QT940_'+pre,revision_change=True)
            if 'E whole-body load:' not in p['notes']:p['notes']+=' E whole-body load: new certified QT940 rear cap required; ordinary 304 original rear cap not equivalent.'
            rows.append(dict(part=p['name'],min_yield_MPa=940))
    put(OUT/'assembly.json',a);put(OUT/'profiles/joint_interfaces.json',j);put(OUT/'reference/material_revision.json',dict(geometry_sha256=sha(OUT/'assembly_meshes.npz'),rows=rows,reason='Full-body load/cross-hole ligament screen requires SF >=2. Same material density, no geometric changes; explicitly requires new certified parts.'))
if __name__=='__main__':main()
