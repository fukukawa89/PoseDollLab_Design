"""O3 reference-surface packaging, driven only by sealed generated PCBA bounds.
This remains a sampled containment screen; unbuilt mechanisms cannot become passes.
"""
from revo3_evidence import *
from study_revo2 import measure_character
from study_revo import anatomy
from packaging_revo2 import inside_surface
from model import fk,rotation
import numpy as np,itertools

def box_points(bb,steps=2):return np.array(list(itertools.product(*[np.linspace(bb[i],bb[i+3],steps) for i in range(3)])))

def main():
    v,o=run_paths();pr=ArtifactReader('pcba_geometry');jr=ArtifactReader('joint');pcba=pr.json(v/'pcba_geometry.json');joint=jr.json(v/'joint.json');boards={q['kind']:q for q in pcba['boards']};chars=[];scenes={}
    basis=np.array([[0,0,1],[1,0,0],[0,1,0]],float) # Board X->body Y, Y->body Z, Z->body X.
    for char in ('manny','quinn'):
        c=measure_character(char);verts=c['vertices_mm'];faces=np.array(c['geometry']['triangles']);p=anatomy(char,480);T,A=fk(p,{});placements=[]
        for side in ('l','r'):
            start=T['upperarm_'+side][:3,3];end=T['elbow_'+side][:3,3];axis=(end-start)/np.linalg.norm(end-start);length=float(np.linalg.norm(end-start))
            reserved=joint['dimensions_mm'][2]/2+max(joint['dimensions_mm'][:2])/2
            for variant,radius in itertools.product(('distal4','distal4_narrow','distal4_side'),('4','12')):
                bb=boards[variant]['bend_sensitivity'][radius]['bounds_mm'];center=(np.array(bb[:3])+bb[3:])/2;local=box_points(bb,3)-center;corners=box_points(bb)-center;trials=[]
                for angle in (0,30,60,90,120,150):
                    R=rotation(axis,angle)@basis
                    for dx,dy in itertools.product((-3,0,3),repeat=2):
                        at=(start+end)/2+[dx,dy,0];pts=local@R.T+at;inside=inside_surface(pts,verts,faces);trials.append({'angle_deg':angle,'center_mm':at.tolist(),'inside_samples':int(inside.sum()),'sample_count':len(inside),'corners_mm':(corners@R.T+at).tolist(),'inside_corners':int(inside_surface(corners@R.T+at,verts,faces).sum())})
                best=max(trials,key=lambda q:q['inside_samples']);margin=length-reserved-(bb[4]-bb[1]);fail=best['inside_samples']<best['sample_count'] or margin<0
                placements.append({'node':'N3' if side=='l' else 'N4','variant':variant,'bend_radius_mm':int(radius),'rigid_owner':'upperarm_'+side,'envelope_source':'Sealed actual PCBA + identified catalog mating envelopes + explicit wire-bend sensitivity','envelope_dimensions_mm':[bb[5]-bb[2],bb[3]-bb[0],bb[4]-bb[1]],'segment_length_mm':length,'provisional_joint_reservation_mm':reserved,'reservation_basis':'Half the actual L6 axial length at shoulder twist plus half its transverse envelope at elbow; actual nested joint frames not yet frozen','guarded_envelope_axial_margin_mm':margin,'best_surface_trial':best,'candidates_tested':len(trials),'fit_status':'FAIL_CURRENT_DERIVED_ENVELOPE_SCREEN' if fail else 'PARTIAL_SAMPLED_ENVELOPE_ONLY','complete_arm_fit':'BLOCKED_MULTIXIS_STRUCTURE_MATING_TOLERANCES_AND_ROUTED_HARNESS'})
        # Proximal top vs side share a data-driven torso placement. N2 is an
        # explicit missing dependency, never replaced by a fabricated passing box.
        torso=[]
        for variant,radius in itertools.product(('proximal5','proximal5_side'),('4','12')):
            for node,sign in (('N3_prox',1),('N4_prox',-1)):
                bb=boards[variant]['bend_sensitivity'][radius]['bounds_mm'];center=(np.array(bb[:3])+bb[3:])/2;at=T['chest'][:3,3]+[0,sign*20,5];pts=(box_points(bb,3)-center)@basis.T+at;inside=inside_surface(pts,verts,faces);corners=(box_points(bb)-center)@basis.T+at
                q={'node':node,'variant':variant,'bend_radius_mm':int(radius),'rigid_owner':'chest','inside_samples':int(inside.sum()),'sample_count':len(inside),'inside_corners':int(inside_surface(corners,verts,faces).sum()),'corners_mm':corners.tolist(),'center_mm':at.tolist(),'fit_status':'FAIL_CURRENT_DERIVED_ENVELOPE_SCREEN' if not inside.all() else 'PARTIAL_SAMPLED_ENVELOPE_ONLY','complete_torso_fit':'BLOCKED_N2_AND_NESTED_SHOULDER_CHEST_AND_RF_KEEP_OUT'};placements.append(q);torso.append(q)
        overlaps=[]
        for a,b in itertools.combinations(torso,2):
            if a['variant']!=b['variant'] or a['bend_radius_mm']!=b['bend_radius_mm']:continue
            pa=np.array(a['corners_mm']);pb=np.array(b['corners_mm']);overlap=np.minimum(pa.max(0),pb.max(0))-np.maximum(pa.min(0),pb.min(0))
            if np.all(overlap>0):overlaps.append({'variant':a['variant'],'bend_radius_mm':a['bend_radius_mm'],'a':a['node'],'b':b['node'],'axis_aligned_envelope_overlap_mm3':float(np.prod(overlap)),'method':'Conservative occupied-envelope overlap, not component BRep collision'})
        chars.append({'character':char,'reference_height_mm':480,'placements':placements,'torso_envelope_overlaps':overlaps,'status':'PARTIAL_WITH_FAILED_CANDIDATES','N2_joint_chest_simultaneous_assembly':'NOT_BUILT','complete_arm_with_all_nine_axes':'NOT_BUILT','full_body_height_verified':False})
        scenes[char]={'surface_vertices':verts.tolist(),'surface_triangles':faces.tolist(),'placements':placements,'reference_height_mm':480}
        print(char,'trials',sum(q.get('candidates_tested',1) for q in placements),'failed',sum(q['fit_status'].startswith('FAIL') for q in placements),flush=True)
    save(v/'packaging.json',{'schema':'revo3-derived-packaging-v1','characters':chars,'status':'BLOCKED_FULL_MULTIXIS_PCBA_AND_HARNESS','bend_radii_mm':[4,12],'radii_are_not_qualified':True,'RF_keepout_retained':True,'mass_override_does_not_remove_size_checks':True,'consumed_inputs':[pr.receipt(),jr.receipt()]})
    save(o/'packaging_scene.json',scenes)
if __name__=='__main__':main()
