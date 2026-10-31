from spherical_wrist import *
import shutil

def main():
    V=OUT/'preview';V.mkdir(exist_ok=True);vertices=[];offset=0
    def encode(meta,z):
        nonlocal offset
        result=[]
        for part in meta:
            i=str(part['i']);tri=z[i+'v'][z[i+'f']];n=np.cross(tri[:,1]-tri[:,0],tri[:,2]-tri[:,0]);n/=np.maximum(1e-10,np.linalg.norm(n,axis=1))[:,None]
            arr=np.concatenate([tri,np.repeat(n[:,None,:],3,axis=1)],axis=2).reshape(-1,6)
            vertices.append(arr);result.append({**part,'first':offset,'count':len(arr)});offset+=len(arr)
        return result
    new=encode(load(OUT/'assembly.json')['parts'],np.load(OUT/'assembly_meshes.npz'))
    old=encode(load(OLD/'assembly.json')['parts'][94:],np.load(OLD/'assembly_meshes.npz'))
    data=dict(profile=load(OUT/'profiles/arm_profile.json'),config=CONFIG,parts=new,oldParts=old,
        comparison=load(OUT/'verification/comparison.json'),kinematics=load(OUT/'verification/kinematics.json'),
        collision={k:v for k,v in load(OUT/'verification/motion_grid.json').items() if k!='cases'},magnetic=load(OUT/'verification/magnetic_feasibility.json'),
        interference=load(OUT/'verification/magnetic_interference_budget.json'),
        geometry_sha256=sha(OUT/'assembly_meshes.npz'),geometry=base64.b64encode(np.concatenate(vertices).astype('<f4').tobytes()).decode())
    (V/'data.js').write_text('window.O24B='+json.dumps(data,ensure_ascii=False,separators=(',',':'))+';\n',encoding='utf8')
    for name in ['index.html','viewer.js','style.css']:shutil.copy2(HERE/name,V/name)
    poses={'neutral':{},'flex':{'wrist_flex':70},'extend':{'wrist_flex':-65},'deviate':{'wrist_deviation':30},'combined':{'wrist_flex':45,'wrist_deviation':20},'elbow_bent':{'elbow_flex':90},'raised':{'shoulder_flex':120,'elbow_flex':45,'wrist_flex':25,'wrist_deviation':10}}
    put(OUT/'profiles/presentation_poses.json',{name:dict(angles=q,frames=frames(data['profile'],q)) for name,q in poses.items()})
    print('preview',V)

if __name__=='__main__':main()
