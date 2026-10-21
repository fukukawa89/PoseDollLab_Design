from o22f7_animation import *
from build_revo22_assembly import b
x=Build();x.begin(x.g['steps'][3]);lm=x.mount.copy();x.begin(x.g['steps'][10]);rm=x.mount.copy();path=read(WORK/'clavicle_right_parked_left_goal_0_1_path.json')['path'];path[-1]=arr(np.array(path[-2])+(np.array(path[-1])-path[-2])*min(1,45/max(np.linalg.norm(np.array(path[-1])[:3]-path[-2][:3]),1)));path=np.array(path[::-1]);lens=np.linalg.norm(np.diff(path,axis=0)*[1,1,1,1.7,1.7,1.7],axis=1)
def mat(q):
 M=np.eye(4);M[:3,:3]=b.b.rot(0,q[3])@b.b.rot(1,q[4])@b.b.rot(2,q[5]);M[:3,3]=q[:3];return M
def smooth(t):
 t=np.clip(t,0,1);return t*t*(3-2*t)
def sample(t):
 distance=lens.sum()*t
 for i,length in enumerate(lens):
  if distance<=length:return path[i]+(path[i+1]-path[i])*(distance/max(length,1e-12))
  distance-=length
 return path[-1]
expected=[]
for t in [0,.15,.52,.85,1]:
 angle=-20*smooth(t/.15) if t<.15 else -20*(1-smooth((t-.85)/.15)) if t>.85 else -20;raw=dict(x.raw);raw['clavicle_l.protract/r0']=float(angle);ff,oo=kin.owners(raw);values={}
 for k in ['frame/clavicle_l.protract_frame','frame/clavicle_r.protract_frame']:
  if k.endswith('_l.protract_frame'):M=ff['clavicle_l.protract_frame']@np.array(x.bind[x.idx[k]]['local']).reshape(4,4)
  else:M=rm@mat(sample(smooth((t-.15)/.7)))@np.linalg.inv(rm)@x.mats[k]
  values[k]=arr(M.flatten())
 expected.append({'t':t,'matrices':values})
put(WORK/'fit_review_expected_matrices.json',expected)
def shape(k):
 o=x.obs[k];m=x.scene['meshes'][o['mesh']];return b.g.move(b.b.from_tri_exact(x.verts[m['first']:m['first']+m['count'],:3].reshape(-1,3,3)),x.mats[k])
l=shape('frame/clavicle_l.protract_frame');r=b.g.move(shape('frame/clavicle_r.protract_frame'),rm@mat(path[0])@np.linalg.inv(rm));peak=0
for a in np.linspace(0,-20,81):peak=max(peak,float((b.g.move(l,lm@mat([0,0,0,0,0,a])@np.linalg.inv(lm))^r).volume()))
put(WORK/'fit_review_start_phase_check.json',{'passed':peak<=.02,'samples':81,'max_pair_overlap_mm3':peak,'scope':'left opening rotation versus right frame at trimmed outside start pose'})
print('start-phase peak',peak)
js=(R/'scripts/check_o22f7_clavicle_review_browser.js').read_text('utf-8-sig');js=js.replace('let end=await page.evaluate', 'let numerical=await page.evaluate(expected=>{O22_FIT_REVIEW.select("right");let maximum=0;for(const sample of expected){O22_FIT_REVIEW.seek(sample.t);for(const [key,M] of Object.entries(sample.matrices)){let i=O22_FIT_REVIEW.data.parts.findIndex(o=>o.key===key),actual=O22_FIT_REVIEW.getMatrices()[i];maximum=Math.max(maximum,...actual.map((v,j)=>Math.abs(v-M[j])));}}return maximum},'+json.dumps(expected,separators=(',',':'))+');let end=await page.evaluate');js=js.replace('return {left,middle,end,played,mobile,errors}', 'return {left,middle,end,played,mobile,numerical,errors}');write(R/'scripts/check_o22f7_clavicle_review_browser_verified.js',js)
