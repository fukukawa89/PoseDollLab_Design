"""Separate tiny embedded tooth tips from actual unsupported tooth-neck layers.
Keep the raw discrepancies and require a separately printed contact lower bound.
"""
import json,sys
import numpy as np
from pathlib import Path
from build_revo22_fins_v3 import O,solid,box,md

def qualify(report_path,plate):
    r=json.loads(report_path.read_text());byname={q['object_name']:q for q in plate['items']};cache={};tip_count=0;unresolved=[]
    for tooth in r['teeth']:
        if tooth['continuous_printed_stack']:continue
        it=byname[tooth['object_name']];pid=it['id']
        if tooth['object_name'] not in cache:
            n=np.load(O/'parts'/f'{pid}.npz');T=np.c_[it['rotation_matrix'],it['translation_mm']]
            cache[tooth['object_name']]=(solid(n['v'],n['f']).transform(T),solid(n['fin_v'],n['fin_f']).transform(T),solid(n['teeth_v'],n['teeth_f']).transform(T),json.loads((O/'design'/f'{pid}.json').read_text()),{})
        s,b,t,des,sections=cache[tooth['object_name']];rec=des['teeth'][tooth['tooth']-1];bb=rec['bounds_mm'];M=np.array(it['rotation_matrix']);tr=np.array(it['translation_mm']);corners=np.array([[x,y,z] for x in [bb[0],bb[3]] for y in [bb[1],bb[4]] for z in [bb[2],bb[5]]])@M.T+tr;lo=corners.min(0);hi=corners.max(0);window=md.CrossSection.square(hi[:2]-lo[:2]).translate(lo[:2]);part_lower=0.;root_lower=0.;bad=[];tiny=[]
        for q in tooth['layers']:
            z=round(q['z_mm'],3);mid=z-.1
            if z not in sections:sections[z]=(s.slice(mid),b.slice(mid),t.slice(mid))
            ss,bs,ts=sections[z];piece=ts^window;outside_part=(piece-ss).area();outside_root=(piece-bs).area();gap=(piece-ss-bs).area()
            q['free_gap_section_mm2']=float(max(0,gap));q['printed_part_contact_area_lower_bound_mm2']=max(0,q['printed_overlap_mm2']-outside_part);q['printed_fin_root_area_lower_bound_mm2']=max(0,q['printed_overlap_mm2']-outside_root)
            part_lower=max(part_lower,q['printed_part_contact_area_lower_bound_mm2']);root_lower=max(root_lower,q['printed_fin_root_area_lower_bound_mm2'])
            if q['printed_overlap_mm2']<q['minimum_required_overlap_mm2']:
                if q['tooth_section_mm2']<.02 and gap<1e-7:tiny.append(q)
                else:bad.append(q)
        tooth['raw_continuous_printed_stack']=False;tooth['embedded_tip_discretization_layers']=tiny;tooth['maximum_printed_part_contact_lower_bound_mm2']=part_lower;tooth['maximum_printed_root_lower_bound_mm2']=root_lower
        if not bad and tiny and part_lower>.005 and root_lower>.02:
            tooth['continuous_printed_stack']=True;tooth['qualification']='Raw failures are wholly embedded sub-0.02 mm2 tip slices, not the free-gap neck. Other layers give positive lower bounds for printed contact into both fin and part.';tip_count+=len(tiny)
        else:unresolved.append({'object_name':tooth['object_name'],'tooth':tooth['tooth'],'part_lower':part_lower,'root_lower':root_lower,'bad':bad,'tiny':tiny})
    r['raw_teeth_missing_printed_layer']=r['teeth_missing_printed_layer'];r['teeth_missing_printed_layer']=sum(not t['continuous_printed_stack'] for t in r['teeth']);r['embedded_tip_discretization_layer_count']=tip_count;r['qualification_scope']='Only wholly embedded tooth-tip sections <0.02 mm2 are exempted, and only when actual printed overlap in other layers proves both endpoint contacts by positive area lower bounds. Free-gap missing layers are never exempted. Layer height 0.2 mm.'
    report_path.write_text(json.dumps(r,ensure_ascii=False,indent=2),encoding='utf8');print(report_path.parent.name,plate['id'],'raw',r['raw_teeth_missing_printed_layer'],'unresolved',r['teeth_missing_printed_layer'],'tip_layers',tip_count,flush=True);return unresolved
if __name__=='__main__':
    manifest=json.loads((O/'manifest.json').read_text());out=[]
    for folder in [O/'verification',O/'verification/bambu']:
        for p in manifest['plates']:
            q=folder/f"{p['id']}_extrusion_contacts.json"
            if q.exists() and 'raw_teeth_missing_printed_layer' not in json.loads(q.read_text()):out+=qualify(q,p)
    (O/'verification/tooth_neck_unresolved.json').write_text(json.dumps(out,indent=2),encoding='utf8')
