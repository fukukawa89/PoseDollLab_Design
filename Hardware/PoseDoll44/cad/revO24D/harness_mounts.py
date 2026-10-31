"""Integral strain-relief tabs and kinematic harness anchors, O24D only."""
from fullbody import *
def apply(D):
    anchors=[]
    def tab(name,frame,W,position_label,feed=1):
        # Two full 2.25 mm ligaments above/below a 2.5 mm slot, root 10 mm wide.
        reach=28 if '_pelvis_' in name else 14
        slot=box([-reach+3,-6,-1.25],[-reach+7,6,1.25])
        body=box([-reach,-5,-3.5],[-4,5,3.5])-slot
        # Cut the actual joined body too: a separate tab cut alone can be filled
        # by an overlapping parent tube. No mechanical hardware is cut.
        cutter=moved(slot,np.linalg.inv(F0[frame])@W)
        for p in D.parts:
            if p['frame']==frame and p['role'] in ['structure','rotor','shell']:p['s']-=cutter
        D.local(name,frame,body,W,role='structure',note='Integral 7 mm high / 10 mm wide cable tab; two 2.25 mm ligaments around a 2.5 mm tie slot. Root overlaps the parent wall over its full width; no thin butt seam. Use 2.0 mm rounded nylon tie with soft liner.')
        q=(np.linalg.inv(F0[frame])@W@np.array([-reach-8,0,0,1]))[:3]
        anchors.append(dict(id=name,frame=frame,local_mm=q,world_N_mm=(W@np.array([-reach-8,0,0,1]))[:3],label=position_label,root_local_mm=(np.linalg.inv(F0[frame])@W@np.array([-4,0,0,1]))[:3],slot_mm=[4,10,2.5],slot_world_from_local=W,slot_bounds_mm=[[-reach+3,-6,-1.25],[-reach+7,6,1.25]],root_lever_mm=reach+4,minimum_ligament_mm=2.25,strap_width_mm=2.0,design_bundle_pull_N=5,wire_clearance='Soft liner; tie grips insulation, never bare copper or the solder joint; 8 mm from tab face to bundle centre'))
    for p in list(D.parts):
        if 'bone_link' not in p or not p['name'].startswith(('l_','r_')):continue
        b=p['bone_link'];g=np.array(b['gauge_world_mm']);centre=g[1];fr=p['frame'];stem=p['name'].replace('_centered_tube','').replace('_tube','')
        # On the larger thigh tube, bring the root 1 mm deeper into the thick wall.
        if 'thigh' in stem:centre=centre+[-1,0,0]
        if 'shin' in stem:
            tab(stem+'_wire_tab',fr,T(centre),stem+' fixed cable guide')
        else:tab(stem+'_wire_tab',fr,T(centre),stem+' fixed cable guide')
    for side,sg in [('l',1),('r',-1)]:
        hip=P['thigh_'+side];ank=P['foot_'+side]
        tab(side+'_pelvis_wire_tab','pelvis',T(hip+[-32,0,17]),'Pelvis service-loop anchor')
        W=T(ank+[20,0,-25])@rot([0,0,1],-sg*90)
        tab(side+'_foot_wire_tab',side+'_ankle_flex',W,'Foot / toe sensor strain relief')
        px=INTEGRATION['backboard_x_mm']+11.5;base=INTEGRATION['backboard_bottom_mm']
        for i,z in enumerate([base+18,base+42]):tab(side+'_back_wire_tab_'+str(i),'thorax_flex',T([px-1.25,sg*27,z])@rot([0,0,1],-sg*90),'Backplate bank strain relief')
    D.harness_anchors=anchors
    put(OUT/'harness/anchors.json',dict(anchors=anchors,method='Integral tabs on actual bone tubes, pelvis crossbeam, foot soles and backplate; potted six-wire sensor tails provide local solder-joint strain relief.',H04_rule='Broad root overlaps, no 0.20 mm butt junction',wire='6 x AWG30 finely stranded, OD <=0.7 mm each, loose braid, no rigid heatshrink across any joint',minimum_free_bend_radius_mm=10,manufacturing_release=False))
