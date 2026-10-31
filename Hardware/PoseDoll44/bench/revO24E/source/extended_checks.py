"""Reuse frozen inspection algorithms with all output/kinematics bound to E."""
from verify import *
import importlib

def run(mode):
    context()
    module=importlib.import_module(dict(rom='rom_cases',grids='joint_grids',paths='plan_paths')[mode])
    for k,val in dict(OUT=OUT,PROFILE=PROFILE,NODES=NODES,F0=F0,FA=FA,frames=frames,poses=lambda:load(OUT/'profiles/poses.json')).items():
        if hasattr(module,k):setattr(module,k,val)
    if mode=='rom':sys.argv.append('--dense')
    module.main()

def ue():
    source=(H/'cad/revO24D/ue_mapping.py').read_text('utf8')
    source=source.replace("('hand','wrist_flex')","('hand','wrist_deviation')")
    source=source.replace("[s+'_wrist_deviation',s+'_wrist_flex']","[s+'_wrist_flex',s+'_wrist_deviation']")
    source=source.replace('POSEDOLL_O24D_40_A_2','POSEDOLL_O24E_40_A_1')
    ns={'__name__':'e_ue_mapping'};exec(compile(source,'E_adapted_ue_mapping','exec'),ns)
    ns.update(OUT=OUT,PROFILE=PROFILE,NODES=NODES,F0=F0,FA=FA,frames=frames,poses=lambda:load(OUT/'profiles/poses.json'))
    ns['main']()
    ch=load(OUT/'profiles/channel_map.json');ch.update(revision='O24E',wrist_order=PROFILE['wrist_order'],calibration_valid=False)
    for c in ch['channels']:
        if c.get('kind')=='Bx_By_Bz':c['model']='Ry(flex) @ Rx(deviation), bounded E-specific LUT; old D calibration rejected'
    put(OUT/'profiles/channel_map.json',ch)
    r=load(OUT/'verification/ue_mapping.json');r['geometry_sha256']=sha(OUT/'assembly_meshes.npz');put(OUT/'verification/ue_mapping.json',r)

if __name__=='__main__':
    if sys.argv[1]=='ue':ue()
    else:run(sys.argv[1])
