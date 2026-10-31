"""Prepare real candidate meshes/frames for visual QA without publishing them."""
from build_revo23_continuous import *


def main():
    z=np.load(B/'preview/render_meshes.npz');out={k:z[k] for k in z.files}
    doc=read(C_HISTORY/'assembly.json');parts={v['key']:v for v in doc['items']}
    source=load_c()
    p=read(DROOT/'source/device_profile.json') if (DROOT/'source/device_profile.json').exists() else read(B/'profiles/device_profile.json')
    q=read(B/'profiles/default_pose.json')['raw_deg'];F=frames(p,q)
    scene=read(B/'preview/render_scene.json')
    for obj in scene['items']:
        item=parts[obj['key']];obj['matrix']=F[item['token']].flatten().tolist()
        i=str(item['index']);out[i+'v'],out[i+'f']=vf(source[item['key']]['s'])
        path=DROOT/(item['key'].replace('/','__')+'.npz')
        if path.exists():
            trial=np.load(path);i=str(item['index']);out[i+'v']=trial['v'];out[i+'f']=trial['f']
            print('TRIAL',item['key'],flush=True)
    np.savez_compressed(B/'preview/trial_meshes.npz',**out)
    put(B/'preview/trial_scene.json',scene)


if __name__=='__main__':main()
