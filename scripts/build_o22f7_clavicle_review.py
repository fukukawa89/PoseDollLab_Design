"""Create an honest, standalone fit-review viewer from unchanged O22F7 geometry."""
from o22f7_animation import *
from build_revo22_assembly import b
import base64
x=Build();x.begin(x.g['steps'][3]);leftmount=x.mount.copy();x.begin(x.g['steps'][10]);rightmount=x.mount.copy();stock=['M3_nut','M3_reaction_washer','inner_M4_wide','outer_M4_wide','spring_1','spring_2','front_M4_washer','shoulder_D4_L8_M3_thread6'];keys=['frame/chest','frame/clavicle_l.protract_frame','frame/clavicle_r.protract_frame']+['clavicle_l.protract/'+k for k in stock]+['clavicle_r.protract/'+k for k in stock[:3]];pack=[];parts=[];first=0
for k in keys:
 o=x.obs[k];m=x.scene['meshes'][o['mesh']];v=x.verts[m['first']:m['first']+m['count']];pack.append(v);parts.append({'key':k,'left_moves':(k=='frame/clavicle_l.protract_frame' or (x.meta['meta'][k].get('module')=='clavicle_l.protract' and x.meta['meta'][k]['owner']=='child')),'matrix':arr(x.mats[k].flatten()),'first':first,'count':len(v),'lo':arr(v[:,:3].min(0)),'hi':arr(v[:,:3].max(0)),'address':o.get('address'),'id':o.get('print_id')});first+=len(v)
def shape(k):
 o=x.obs[k];m=x.scene['meshes'][o['mesh']];return b.g.move(b.b.from_tri_exact(x.verts[m['first']:m['first']+m['count'],:3].reshape(-1,3,3)),x.mats[k])
l=shape(keys[1]);chest=shape(keys[0]);bad=None
for mm in range(1,36):
 M=np.eye(4);M[1,3]=mm;delta=leftmount@M@np.linalg.inv(leftmount);overlap=b.g.move(l,delta)^chest
 if overlap.volume()>3:bad=(mm,delta,overlap);break
assert bad is not None
tri=b.g.tri(bad[2]);norm=np.cross(tri[:,1]-tri[:,0],tri[:,2]-tri[:,0]);norm/=np.maximum(np.linalg.norm(norm,axis=1)[:,None],1e-12);verts=np.concatenate([tri,np.repeat(norm[:,None,:],3,axis=1)],axis=2).reshape(-1,6).astype('<f4');pack.append(verts);parts.append({'key':'interference','matrix':arr(np.eye(4).flatten()),'first':first,'count':len(verts),'lo':arr(verts[:,:3].min(0)),'hi':arr(verts[:,:3].max(0))})
path=read(WORK/'clavicle_right_parked_left_goal_0_1_path.json')['path'];path[-1]=arr(np.array(path[-2])+(np.array(path[-1])-path[-2])*min(1,45/max(np.linalg.norm(np.array(path[-1])[:3]-path[-2][:3]),1)))
report={'status':'PREVIEW_NOT_RELEASE_READY','user_has_not_assembled_clavicles':True,'left_step':'S04','left_part':'D05-01 / W005','left_complete_path_verified':False,'left_straight_demo_mm':bad[0],'left_interference_mm3':float(bad[2].volume()),'right_step':'S11','right_part':'D07-02 / H008','right_conditional_path_passed':True,'right_conditions':['bare chest','left frame installed and rotated -20 degrees','left hinge hardware installed','right inner nut and two washers installed','head, chest core and sensor boards not present'],'right_sampled_review':read(WORK/'right_parked_left_dense_review.json'),'left_return_review':read(WORK/'clavicle_preassembly_interfaces_review.json')['checks'][-1],'head_transfer_review':read(WORK/'head_after_clavicles_review.json')['checks'][0],'manufacturing_changed':False,'physical_assembly_tested':False,'source_geometry_sha256':sha(G/x.scene['geometry_url']),'candidate_path_sha256':sha(WORK/'clavicle_right_parked_left_goal_0_1_path.json')}
data={'parts':parts,'left_mount':arr(leftmount.flatten()),'left_inverse':arr(np.linalg.inv(leftmount).flatten()),'right_mount':arr(rightmount.flatten()),'right_inverse':arr(np.linalg.inv(rightmount).flatten()),'bad_delta':arr(bad[1].flatten()),'right_path':path[::-1],'report':report,'binary':base64.b64encode(np.concatenate(pack).astype('<f4').tobytes()).decode()}
put(WORK/'clavicle_fit_review.json',report);template=(R/'scripts/o22f7_clavicle_review_template.html').read_text('utf8');html=template.replace('/*DATA*/',json.dumps(data,ensure_ascii=False,separators=(',',':')));write(WORK/'锁骨装配路径复核.html',html);print(json.dumps({'html':str(WORK/'锁骨装配路径复核.html'),'bytes':len(html.encode()),'interference_mm3':report['left_interference_mm3'],'right_samples':report['right_sampled_review']['samples']},ensure_ascii=False))

