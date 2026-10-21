from optimize_revo23_print import *
import copy
from scipy.spatial.transform import Rotation

if __name__=='__main__':
    choices={'S02':'pose1_tree_clear_snug','S04':'pose1_tree_clear_snug','S05':'pose1_tree_clear_snug','S06':'pose1_clear_m2',
        'S07':'pose1_tree_clear_snug','S08':'pose1_clear_m2','S09':'pose1_tree_clear_snug','S10':'pose1_tree_clear_snug',
        'S12':'pose3_tree_clear_snug','S13':'pose1_tree_clear_snug','S14':'pose1_tree_clear_snug','S15':'flat1_clear',
        'S16':'flat1_clear','S17':'pose1_tree_clear_snug','S18':'pose1_tree_clear_snug','S20':'pose2_tree_clear_snug',
        'S21':'flat1_clear','S22':'flat1_clear','S23':'pose1_tree_clear_snug','W01':'flat2_clear'}
    for rid,source in choices.items():
        p=OUT/'candidates'/('O23G-'+rid+'.json');s=read(p);m=trimesh.load(B/s['source']['staged_stl'],process=True)
        original=next(c for c in s['candidates'] if c['name']==source)
        for name,axis,degrees in [('v3_upright','x',0),('v3_tilt_x','x',35),('v3_tilt_y','y',-35)]:
            c=copy.deepcopy(original);F=Rotation.from_euler(axis,degrees,degrees=True).as_matrix()@np.array(c['matrix'])[:3,:3]
            M,size=placement(m.vertices,F)
            if max(size[:2])>168 or size[2]>177:continue
            c.update(name=name,matrix=M,size_mm=size,metrics=metrics(m,M,s['rod_lines']),guard_revision=3,blocker_margin_mm=.65,
                settings=dict(support_threshold_angle='55',bridge_no_support='0',support_expansion='0',support_object_xy_distance='0.4',brim_width='6'))
            s['candidates']=[x for x in s['candidates'] if x['name']!=name]+[c]
        put(p,s)
