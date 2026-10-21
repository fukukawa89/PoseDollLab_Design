"""Static gravity demands of modeled printed material, not friction capacity.

Uniform density is an explicit comparison assumption. Infill, metal, electronics,
wires, print tolerances and a stand are not included; no holding-pose PASS follows.
"""
from package_revo23 import *

def material_points(parts,density):
    points=[]
    for key,part in parts.items():
        if part['role'] not in ('structure','print','frame'):continue
        v,f=vf(part['s']);mesh=trimesh.Trimesh(v,f,process=False)
        points.append(dict(key=key,token=part['token'],center_mm=mesh.center_mass,
                           mass_kg=part['s'].volume()/1e6*density))
    return points

def gravitational_demand(p,points,raw):
    # dU/dq gives required static torque about each generalized measured axis.
    # It automatically accounts for all descendant segments and joint order.
    def energy(q):
        ff=frames(p,q)
        return sum((ff[x['token']]@np.r_[x['center_mm'],1])[2]/1000*x['mass_kg']*9.80665 for x in points)
    eps=.001;torques={}
    for rid in p['raw_order']:
        a=dict(raw);b=dict(raw);a[rid]+=eps;b[rid]-=eps
        torques[rid]=(energy(a)-energy(b))/(2*np.deg2rad(eps))
    return torques

def main():
    parts=load_current();base,_,_=load_baseline();p=read(B/'profiles/device_profile.json')
    density=read(CFG)['material_density_g_cm3_for_solid_volume_only']
    new=material_points(parts,density);old=material_points(base,density)
    rows=[];report=[]
    for name,q in cases(p,'quick').items():
        a=gravitational_demand(kin.profile,old,q);b=gravitational_demand(p,new,q)
        for rid in p['raw_order']:
            rows.append({'姿态':name,'原始轴':rid,'O22打印材料力矩_Nm':round(a[rid],6),
                             TAG+'打印材料力矩_Nm':round(b[rid],6)})
        report.append(dict(pose=name,old_print_only_signed_Nm=a,new_print_only_signed_Nm=b))
    writecsv(B/'打印材料重力力矩对照.csv',list(rows[0]),rows)
    put(B/'verification/gravity_demand.json',dict(geometry_sha256=sha(B/'assembly.npz'),
        density_g_cm3=density,printed_geometry_solid_equivalent_g={
            'O22F7':sum(x['mass_kg']for x in old)*1000,TAG:sum(x['mass_kg']for x in new)*1000},
        rows=report,assumptions=[
            'All modeled printable solids use the same uniform density, with no slicer infill adjustment.',
            'Only printed geometry is included. Metal, magnets, PCBs, wiring, and the support stand are omitted.',
            'Static gravitational demand via central finite difference of potential energy; no dynamic loads.',
            'Numbers are not predicted actual mass, friction capacity, strength, or a holding-pose test.'],
        friction_capacity_verified=False,physical_tested=False))
    print('GRAVITY report saved',flush=True)

if __name__=='__main__':main()
