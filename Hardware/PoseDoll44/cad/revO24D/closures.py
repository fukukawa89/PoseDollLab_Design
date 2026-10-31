"""O24D independent metal preload cartridges. All coordinates in mm.

The fixed hexagonal compression sleeve and two face pads carry clamp force.
Recessed bearings carry radial reactions only. A headed, cross-drilled shaft,
keyed steel output cap and metal locknut close and retain each stack.
Turned/drilled parts are explicitly custom, never advertised as catalogue stock.
"""
from fullbody import *

def paired(D):
    specs=[]
    for side in ['l','r']:
        specs += [(side+'_clavicle_z',side+'_clavicle_z_housing',side+'_clavicle_protract'),(side+'_clavicle_x',side+'_clavicle_elevation_housing',side+'_clavicle_elevate'),(side+'_shoulder_pitch',side+'_shoulder_pitch_housing',side+'_shoulder_flex'),(side+'_humeral',side+'_humeral_housing',side+'_upperarm_roll'),(side+'_forearm',side+'_forearm_housing',side+'_forearm_roll')]
    for pre,ax in [('lumbar_shoulder_pitch','lumbar_flex'),('lumbar_humeral','lumbar_yaw'),('thorax_shoulder_pitch','thorax_side'),('neck_shoulder_pitch','neck_side'),('neck_humeral','neck_yaw'),('l_ankle_shoulder_pitch','l_ankle_roll'),('r_ankle_shoulder_pitch','r_ankle_roll'),('l_hip_pitch','l_hip_flex'),('r_hip_pitch','r_hip_flex'),('neck_shoulder_swing','neck_flex')]:specs.append((pre,pre+'_housing',ax))
    for pre,hn,child in specs:
        print('CARTRIDGE',pre,flush=True)
        housing=next(p for p in D.parts if p['name']==hn);parent=housing['frame']
        bearings=[p for p in D.parts if p['name'].startswith(pre+'_bearing_')]
        assert len(bearings)==2,(pre,len(bearings))
        def worldcentre(p):
            b=np.array(p['s'].bounding_box()).reshape(2,3).mean(0);return (F0[p['frame']]@np.r_[b,1])[:3]
        o=np.mean([worldcentre(p) for p in bearings],axis=0);axis=worldcentre(bearings[1])-worldcentre(bearings[0]);axis/=np.linalg.norm(axis)
        magnet=next(p for p in D.parts if p['name']==pre+'_magnet')
        flange=next(p for p in D.parts if p['name'] in [pre+'_rotor_flange',pre+'_flange'])
        if np.dot(worldcentre(flange)-o,axis)<0:axis=-axis
        xx=np.cross(axis,[0,0,1] if abs(axis[2])<.8 else [0,1,0]);xx/=np.linalg.norm(xx);yy=np.cross(axis,xx);W=T(o,np.c_[xx,yy,axis]);inv=np.linalg.inv(W)
        sh=moved(housing['s'],inv@F0[parent]);lo,hi=np.array(sh.bounding_box()).reshape(2,3)[:,2]
        if pre in ['l_humeral','r_humeral']:lo+=10
        if pre.endswith('forearm'):hi-=10
        if pre=='lumbar_humeral':lo+=.8
        if pre=='neck_humeral':lo+=1.5;hi+=1.5
        ankle_first='ankle_shoulder_pitch' in pre
        heavy_first=pre in ['lumbar_shoulder_pitch','thorax_shoulder_pitch'] or ankle_first
        hip_pitch=pre.endswith('hip_pitch')
        large=pre.endswith(('humeral','forearm')) or heavy_first or hip_pitch;diam=6 if large else 4;bro=6 if large else 4.5;hexr=8.4 if large else 6.4;print_r=10.5 if large else 8.5;wd=1.5 if large else 1.;frro=9 if large else 6.;headr=6 if large else 4.5;headt=3 if large else 2.5;af=10 if large else 7;nut_h=6 if large else 5;pitch=1 if large else .7
        if pre.endswith('forearm'):print_r=10
        thread=4 if heavy_first or hip_pitch else diam
        if heavy_first:lo=hi-16.8;af=7;nut_h=5;pitch=.7
        else:lo=min(lo,hi-10.8)
        rear_cap_th=3 if pre=='lumbar_shoulder_pitch' else (2.2 if hip_pitch else 1.5)
        if hip_pitch:af=7;nut_h=2.2;pitch=.7;headt=2.5
        if pre=='lumbar_humeral':headr=5;headt=2.5
        station_shift=-(6 if heavy_first and not ankle_first else .6) if pre.endswith('shoulder_pitch') else (-3 if pre.endswith('clavicle_x') else 0)
        if ankle_first:station_shift-=3  # Coaxial retreat clears the orthogonal D15 hub; UE axis intersection is unchanged.
        W=W@T([0,0,station_shift]);inv=np.linalg.inv(W)
        canonical=lambda p:moved(p['s'],inv@F0[p['frame']])
        # Existing fixed supports remain in their original frames. Their bearing
        # housing becomes a thick keyed FDM socket around a steel load cartridge.
        pinx=(hexr+diam/2+.3)/2;pinz_fixed=(lo+hi)/2;pinhalf=math.sqrt(print_r**2-pinx**2)-.4
        capture_hole=cyl([pinx,-pinhalf-2,pinz_fixed],[pinx,pinhalf+2,pinz_fixed],.75)
        printed_slot=union(cyl([pinx+dx,-pinhalf-2,pinz_fixed],[pinx+dx,pinhalf+2,pinz_fixed],.8) for dx in [-.15,.15])
        socket=cyl([0,0,lo+.35],[0,0,hi-.35],print_r)-md.Manifold.cylinder(hi-lo+2,hexr+.05,hexr+.05,6).translate([0,0,lo-1])-printed_slot
        housing['s']=moved(socket,np.linalg.inv(F0[parent])@W);housing['notes']=f'Keyed FDM socket, minimum radial corner ligament {print_r-hexr-.05:.2f} mm. Steel sleeve takes preload; 0.35 mm printed face recess and separate D1.5 axial capture pin.'
        def add(suffix,s,fr,role='metal',note='',sku=None):return D.local(pre+'_'+suffix,fr,s,W,role=role,note=note,sku=sku,group=pre)
        cage=md.Manifold.cylinder(hi-lo,hexr,hexr,6).translate([0,0,lo])-cyl([0,0,lo-1],[0,0,hi+1],bro+.01)
        cage+=tube([0,0,lo+4.4],[0,0,hi-4.4],bro+.01,diam/2+.3)
        cage-=capture_hole
        add('compression_cartridge',cage,parent,note='Custom steel hex sleeve with >=2 mm central bearing-stop shoulder. Bearing outer races bonded in precision metal seats with retaining compound; conditioned design shear allowable 2 MPa. No axial clamp force through plastic or bearing end faces.',sku='CUSTOM_STEEL_HEX_CARTRIDGE')
        add('fixed_capture_pin',tube([pinx,-pinhalf,pinz_fixed],[pinx,pinhalf,pinz_fixed],.75,.4),parent,sku='ROLL_PIN_1.5_CUT',note='D1.5 spring pin through the steel central shoulder positively retains the printed socket axially. Printed 1.6 mm slot is widened tangentially to let the hex faces take torque. Both ends remain inside the original housing envelope. Insert before the bearings.')
        # Move each bearing inward on its existing axis; no centre-line offset.
        for bi,p in enumerate(sorted(bearings,key=lambda p:np.dot(worldcentre(p)-o,axis))):
            b=canonical(p);z0=np.array(b.bounding_box()).reshape(2,3).mean(0)[2];shift=(lo+2.4 if bi==0 else hi-2.4)-z0
            b=ring([0,0,1],z0+shift-2,z0+shift+2,bro,diam/2)
            p['s']=moved(b,np.linalg.inv(F0[p['frame']])@W)
            p['sku']='MR126ZZ' if diam==6 else '684ZZ'
        removed={pre+'_shaft',pre+'_rotor_flange',pre+'_flange',pre+'_brake',pre+'_friction'}
        D.parts[:]=[p for p in D.parts if p['name'] not in removed]
        for sg in [-1,1]:
            end=lo if sg<0 else hi
            add('face_pad_'+str(sg),tube([0,0,end],[0,0,end+sg*wd],frro,diam/2+.15 if diam==4 else 3.2),parent,'friction',sku='FR12x4.3x1' if diam==4 else 'FR18x6.4x1.5',note='Stock-sized face pad; loaded annulus lies outside the recessed bearing outer diameter.')
        rear=lo-wd-rear_cap_th;front=hi+wd
        rear_key=5 if diam==6 else 3.5
        rear_cap=cyl([0,0,rear],[0,0,lo-wd],frro)-md.Manifold.cylinder(rear_cap_th+2,rear_key+.05,rear_key+.05,6).translate([0,0,rear-1])
        add('rear_thrust_cap',rear_cap,child,sku=f'CUSTOM_HEX_THRUST_{rear_cap_th:g}',note='Rear cap positively keyed to the integral shaft hex; both brake faces transmit holding torque without relying on washer/head friction.')
        capt=4 if large else 3
        cap=md.Manifold.cylinder(capt,hexr,hexr,6).translate([0,0,front])-cyl([0,0,front-1],[0,0,front+capt+1],diam/2+.025)
        pinr=1 if diam==4 else 1.5;pinz=front+capt/2
        cap-=cyl([-hexr-1,0,pinz],[hexr+1,0,pinz],pinr+.025)
        add('keyed_output_cap',cap,child,note='Cross-pinned steel cap; external hex transfers torque to printed output socket.',sku='CUSTOM_STEEL_HEX_OUTPUT')
        collar_extra=.5 if pre=='neck_shoulder_swing' else (1 if heavy_first else 2)
        collar=cyl([0,0,front],[0,0,front+capt+collar_extra],print_r)-md.Manifold.cylinder(capt+4,hexr+.05,hexr+.05,6).translate([0,0,front-1])
        add('output_socket',collar,child,'rotor',note=f'Continuous {print_r-hexr-.05:.2f} mm corner ligament; {capt-.35:.2f} mm axial hex engagement after 0.35 mm face relief. Locknut remains tool-accessible through the bore.')
        # The pin is inserted before the printed socket is fitted. The socket
        # captures its ends; the pin cannot walk out radially after assembly.
        add('torque_pin',tube([-hexr+.25,0,pinz],[hexr-.25,0,pinz],pinr,pinr*.55),child,sku=f'ROLL_PIN_{2*pinr:g}_CUT')
        front_sensor=pre in ['lumbar_humeral','neck_humeral'] or hip_pitch
        if pre=='lumbar_humeral':nut_h=3.2
        nut_z=front+capt+.8;tip=nut_z+nut_h+2*pitch+(1 if hip_pitch else 0)
        shaft=cyl([0,0,rear-headt],[0,0,tip if thread==diam else front+capt-.5],diam/2-.01)+cyl([0,0,rear-headt],[0,0,rear],headr)
        shaft+=md.Manifold.cylinder(rear_cap_th-.1,rear_key,rear_key,6).translate([0,0,rear])
        if thread!=diam:shaft+=cyl([0,0,front+capt-1],[0,0,tip],thread/2)
        shaft-=cyl([-diam,0,pinz],[diam,0,pinz],pinr+.025)
        add('shaft',shaft,child,sku=f'CUSTOM_HEADED_D{diam}_M{thread}',note='42CrMo4 +QT shaft, certified yield >=750 MPa after machining. Precision journal, threaded tip and cross hole. D6/M4 shoulders stop 0.5 mm behind the thrust washer so they cannot bypass preload.')
        add('nut_washer',k.washer([0,0,front+capt],[0,0,1],2*headr,thread+.3,.8),child,sku=f'W{thread}_{2*headr:g}x{thread+.3:g}x0.8')
        add('locknut',k.nut([0,0,nut_z],[0,0,1],thread,af,nut_h),child,sku=f'M{thread}_DIN439_THREADLOCK' if hip_pitch or pre=='lumbar_humeral' else f'M{thread}_NYLOC',note='All preload threads in metal. Hip pitch and lumbar yaw use DIN439 thin nuts, removable metal thread-lock and positive end pins; other cartridges use nylon locknuts.')
        # Keep the complete encoder outline; place the magnet on the new head
        # and translate the existing PCB/holder as one axial cassette.
        mg=canonical(magnet);mgb=np.array(mg.bounding_box()).reshape(2,3);already_front=mgb.mean(0)[2]>(lo+hi)/2
        sensor_flip=np.diag([1.,-1,-1,1]) if front_sensor and not already_front else np.eye(4)
        newmg=moved(mg,sensor_flip);mgb=np.array(newmg.bounding_box()).reshape(2,3)
        delta=(tip-mgb[0,2]) if front_sensor else (rear-headt-mgb[1,2])
        for p in D.parts:
            if p['name'].startswith(pre+'_') and any(t in p['name'] for t in ['magnet','pcb','connector','sensor_holder']):
                p['s']=moved(moved(canonical(p),sensor_flip).translate([0,0,delta]),np.linalg.inv(F0[p['frame']])@W)
        if pre=='lumbar_humeral' or hip_pitch:
            retention_z=nut_z+nut_h+1.1
            shaft_part=next(p for p in D.parts if p['name']==pre+'_shaft')
            shaft_part['s']-=moved(cyl([-4,0,retention_z],[4,0,retention_z],.75),np.linalg.inv(F0[child])@W)
            add('end_safety_pin',tube([-4,0,retention_z],[4,0,retention_z],.75,.4),child,sku='ROLL_PIN_1.5x8',note='Positive stop behind the thin metal nut; low-strength thread-lock separately preserves preload.')
        # Trim only the old printed interface at the new stationary pad plane.
        # A full radial recess remains valid through arbitrary rotation.
        clearance=cyl([0,0,hi-.1],[0,0,hi+wd+.2],frro+.25)+cyl([0,0,lo-.1],[0,0,hi+.05],print_r+.2)
        cb=np.array(clearance.bounding_box()).reshape(2,3)
        for p in D.parts:
            if p['frame']==child and p['role'] in ['structure','rotor','shell'] and p['name']!=pre+'_output_socket':
                s0=canonical(p);sb=np.array(s0.bounding_box()).reshape(2,3)
                if not (np.all(sb[1]>cb[0]) and np.all(cb[1]>sb[0])):continue
                trimmed=s0-clearance
                _=trimmed.volume()
                p['s']=moved(trimmed,np.linalg.inv(F0[child])@W)
        if pre.endswith(('humeral','forearm')):
            for p in D.parts:
                if not p['name'].startswith(pre+'_stem_'):continue
                old=canonical(p);rad=np.array(old.bounding_box()).reshape(2,3).mean(0);rad[2]=0;rad/=np.linalg.norm(rad)
                joint=F0[child][:3,3]
                if pre.endswith('forearm'):joint=P['lowerarm_'+pre[0]]
                jz=float((inv@np.r_[joint,1])[2]);root=1 if pre.startswith('neck') or pre.endswith('forearm') else 3.5
                if pre.endswith('forearm'):pts=[rad+[0,0,jz+5.5],rad+[0,0,jz+14],rad*10.5+[0,0,jz+19],rad*10.5+[0,0,lo+4]];rr=2.25
                elif pre.startswith('neck'):pts=[rad+[0,0,jz+5.5],rad+[0,0,jz+12],rad*12+[0,0,lo-4],rad*12+[0,0,lo+4]];rr=2.6
                else:pts=[rad*root+[0,0,jz+5.5],rad*6+[0,0,jz+12],rad*6+[0,0,jz+16],rad*12+[0,0,lo+1],rad*12+[0,0,lo+4]];rr=2.6
                p['s']=moved(union(beam(x,y,rr) for x,y in zip(pts[:-1],pts[1:])),np.linalg.inv(F0[p['frame']])@W)
                if pre=='lumbar_humeral':
                    sg=-1 if p['name'].endswith('-1') else 1
                    pts=[P['spine_02']+[sg*3,-5,3],P['spine_02']+[sg*3,-12,10],P['spine_02']+[sg*3,-12,16.8]]
                    p['s']=moved(union(beam(x,y,2.6) for x,y in zip(pts[:-1],pts[1:])),np.linalg.inv(F0[p['frame']]))
                if pre=='neck_humeral':
                    sg=-1 if p['name'].endswith('-1') else 1
                    pts=[P['neck_01']+[-7,-8.5,sg*3],P['neck_01']+[-14,-13+sg*3,13],P['neck_01']+[-12,sg*5,25],P['neck_01']+[-10,sg*5,29]]
                    p['s']=moved(union(beam(x,y,3) for x,y in zip(pts[:-1],pts[1:])),np.linalg.inv(F0[p['frame']]))
            # Two solid D3.2 struts go outside the rotating cap. Reusing the old
            # short sensor legs would leave them either cut through or rubbing.
            pcb=next(p for p in D.parts if p['name']==pre+'_pcb');holder=next(p for p in D.parts if p['name']==pre+'_sensor_holder')
            pb=np.array(canonical(pcb).bounding_box()).reshape(2,3);z0=pb[0,2]-.5;z1=pb[1,2]+.5
            outer0=pb[0]+[-1.8,-1.8,-.5];outer1=pb[1]+[1.8,1.8,.5]
            s=box(outer0,outer1)-box(pb[0]+[-.15,-.15,-1],pb[1]+[.15,.15,1])
            bz=hi-2 if front_sensor else lo+2;ez=(z0+z1)/2
            for sg in [-1,1]:
                leg_radius=12 if pre.endswith('forearm') else 13
                pts=[[sg*9.5,0,bz],[sg*leg_radius,0,bz],[sg*leg_radius,0,ez],[sg*(pb[1,0]+1),0,ez]]
                if pre=='lumbar_humeral':pts=[[-9.5,sg*4,bz],[-13,sg*4,bz],[-13,sg*4,ez],[-(pb[1,0]+1),sg*4,ez]]
                if pre in ['l_humeral','r_humeral']:
                    d=-1 if pre.startswith('l_') else 1
                    pts=[[sg*4,d*9.5,bz],[sg*4,d*13,bz],[sg*4,d*13,ez],[sg*4,d*(pb[1,1]+1),ez]]
                if pre=='neck_humeral':pts=[[0,sg*9.5,bz],[0,sg*13,bz],[0,sg*13,ez],[0,sg*(pb[1,1]+1),ez]]
                s+=union(beam(x,y,1.6) for x,y in zip(pts[:-1],pts[1:]))
            holder['s']=moved(s,np.linalg.inv(F0[parent])@W)
            holder['notes']='Continuous D3.2 sensor support struts around rotating hardware; full PCB outline retained. PCB routing and measured magnetic accuracy remain unqualified.'
        if pre in ['l_humeral','r_humeral','l_forearm','r_forearm']:
            isfore=pre.endswith('forearm');suffix='forearm_centered_tube' if isfore else 'upperarm_centered_tube'
            rod=next(p for p in D.parts if p['name']==pre[:2]+suffix)
            joint=P[('lowerarm_' if isfore else 'upperarm_')+pre[0]];jz=float((inv@np.r_[joint,1])[2])
            if isfore:
                length=float(np.linalg.norm(P['hand_'+pre[0]]-joint));end=jz+length-24
                merge=min(tip+5,end+1)
                shape=union(beam([0,sg*9.5,front+capt-.5],[0,sg*9.5,tip+1],2.6)+beam([0,sg*9.5,tip+1],[0,0,merge],3.2) for sg in [-1,1])
                shape+=tube([0,0,tip+1],[0,0,end+3],6,3)
            else:
                length=float(np.linalg.norm(P['lowerarm_'+pre[0]]-joint));end=jz+length-20
                shape=union(beam([0,sg*9.5,front+capt-.5],[0,sg*9.5,tip+2],2.6)+beam([0,sg*9.5,tip+2],[0,0,tip+8],3.2) for sg in [-1,1])
                shape+=tube([0,0,tip+6],[0,0,end],6,2.5)
            bore_start=tip+1 if isfore else tip+6;bore_end=end+3 if isfore else end
            shape-=cyl([0,0,bore_start],[0,0,bore_end],3 if isfore else 2.5)
            rod['s']=moved(shape,np.linalg.inv(F0[child])@W)
            rod['notes']='Actual coaxial bone tube with short symmetric fork roots around the metal locknut. Tube centreline is measured from exported cross-sections; no average-of-offset-rails substitution. Full D6.4 fork roots avoid the 0.2 mm bridge mode.'
            start=tip+1 if isfore else tip+6;finish=end+3 if isfore else end
            if finish-start<2:raise ValueError('Insufficient bone tube gauge length '+pre)
            rod['bone_link']=dict(bones=[('lowerarm_' if isfore else 'upperarm_')+pre[0],('hand_' if isfore else 'lowerarm_')+pre[0]],
                gauge_world_mm=[(W@np.array([0,0,start+(finish-start)*f,1]))[:3].tolist() for f in [.3,.5,.7]],outer_radius_mm=6,inner_radius_mm=3 if isfore else 2.5)
        if pre.endswith('clavicle_x'):
            side=pre[0];sg=1 if side=='l' else -1;part=next(p for p in D.parts if p['name']==pre+'_output')
            socket=next(p for p in D.parts if p['name']==pre+'_output_socket');root=worldcentre(socket)
            pts=[root+[0,sg*7.5,0],P['clavicle_'+side]+[0,sg*9,-1],P['clavicle_'+side]+[0,sg*7,-1]]
            part['s']=moved(union(beam(x,y,2.6) for x,y in zip(pts[:-1],pts[1:])),np.linalg.inv(F0[child]))
            part['notes']='D5.2 torque bridge joined to the keyed output socket, passing outside the locknut into the original clavicle links.'
        # Stator relief around rotating thrust caps and their heads. This makes
        # true assembly clearance; subsequent core checks reject weakened roots.
        relief=cyl([0,0,rear-.2],[0,0,lo+.05],frro+.25)+cyl([0,0,rear-headt-.2],[0,0,rear],headr+.25)
        relief+=cyl([0,0,front-.05],[0,0,front+capt+2.1],print_r+.25)
        relief+=cyl([0,0,lo-wd-.2],[0,0,lo+.35],frro+.25)+cyl([0,0,hi-.35],[0,0,hi+wd+.2],frro+.25)
        rb=np.array(relief.bounding_box()).reshape(2,3)
        for p in D.parts:
            if p['frame']==parent and p['role'] in ['structure','shell'] and p['name']!=hn:
                oldshape=canonical(p);sb=np.array(oldshape.bounding_box()).reshape(2,3)
                if not (np.all(sb[1]>rb[0]) and np.all(rb[1]>sb[0])):continue
                relieved=oldshape-relief
                _=relieved.volume()  # Evaluate the local Boolean before composing another transform.
                p['s']=moved(relieved,np.linalg.inv(F0[parent])@W)
        if heavy_first:
            holder=next(p for p in D.parts if p['name']==pre+'_sensor_holder');hb=np.array(canonical(holder).bounding_box()).reshape(2,3);ez=float(hb.mean(0)[2])
            for sg in [-1,1]:
                pts=[[0,sg*9.6,lo+2],[0,sg*13,lo+2],[0,sg*13,ez],[0,sg*7,ez]]
                holder['s']+=moved(union(beam(x,y,1.8) for x,y in zip(pts[:-1],pts[1:])),np.linalg.inv(F0[parent])@W)
            holder['notes']+=' Two continuous D3.6 supports join the fixed housing outside the rotating thrust cap.'
        if pre=='lumbar_humeral' or hip_pitch or pre in ['l_humeral','r_humeral']:
            # Radial TMAG5170 angle acquisition: full board and connector
            # envelope, same shaft and magnet centre. Ideal model is validated
            # separately; populated-board accuracy remains a bench item.
            zc=tip+1.25-(15 if pre=='lumbar_humeral' else 0);pcb=next(p for p in D.parts if p['name']==pre+'_pcb')
            if pre in ['l_humeral','r_humeral']:zc=lo+4
            pcb['s']=moved(box([17,-6,zc-5],[19,6,zc+5]),np.linalg.inv(F0[parent])@W)
            con=next(p for p in D.parts if p['name']==pre+'_connector')
            con['s']=moved(box([17,6,zc-2],[20,10,zc+2]),np.linalg.inv(F0[parent])@W)
            holder=next(p for p in D.parts if p['name']==pre+'_sensor_holder')
            shell=box([16.2,-7.8,zc-6.8],[19.8,7.8,zc+6.8])-box([16,-6.15,zc-5.15],[20,6.15,zc+5.15])
            for sg in [-1,1]:
                pts=[[9,sg*6,hi-2],[18,sg*7,hi-2],[18,sg*7,zc-6]]
                shell+=union(beam(x,y,1.8) for x,y in zip(pts[:-1],pts[1:]))
            holder['s']=moved(shell,np.linalg.inv(F0[parent])@W)
            holder['notes']='Radial TMAG5170 on 12 x 10 mm full board; 18 mm ideal magnetic radius. D3.6 continuous supports. Gain/offset calibration and interference verification required.'
            if pre=='lumbar_humeral':
                for p in [pcb,con,holder]:p['s']=moved(moved(canonical(p),rot([0,0,1],90)),np.linalg.inv(F0[parent])@W)
        if pre=='neck_shoulder_swing':
            old=next(p for p in D.parts if p['name']=='neck_shoulder_open_yoke')
            socket=next(p for p in D.parts if p['name']=='neck_shoulder_pitch_output_socket');c0=worldcentre(socket)
            shape=union(beam(c0+[0,0,sg*7],P['neck_01']+[7,0,sg*4],3.2) for sg in [-1,1])
            old['s']=moved(shape,np.linalg.inv(F0[parent]))
            pad=next(p for p in D.parts if p['name']=='neck_shoulder_pitch_face_pad_1')
            vv,_=a.mesh_data(moved(pad['s'],F0[pad['frame']]));cc=vv.mean(0);aa=np.array([1,0,0]);span=(vv-cc)@aa
            old['s']-=moved(cyl(cc+aa*(span.min()-.2),cc+aa*(span.max()+.2),6.2),np.linalg.inv(F0[parent]))
        D.stacks.append(dict(id=pre+'_M'+str(diam),underhead_to_tip_mm=tip-(rear-headt),underhead_to_nut_exit_mm=nut_z+nut_h-(rear-headt),protrusion_mm=2*pitch,minimum_two_threads_mm=2*pitch))
        D.joints.append(dict(id=pre,axis_id=child,axis_world=axis,center_mm=F0[child][:3,3],bearing_diameter_mm=diam,bearing_outer_mm=bro*2,bearing_span_mm=abs(float(np.dot(worldcentre(bearings[1])-worldcentre(bearings[0]),axis))),friction_od_mm=frro*2,friction_inner_loaded_radius_mm=bro+.01,friction_faces=2,preload_path='Head / rear cap / pad / keyed steel cartridge / pad / cross-pinned output cap / washer / metal locknut. Bearings recessed 0.40 mm, central shoulder and metal retaining compound maintain position.',bearing_axial_relief_mm=.4,output_hex_engagement_mm=capt,minimum_printed_corner_ligament_mm=print_r-hexr-.05,cap_thickness_mm=rear_cap_th,cap_supported_radius_mm=headr,cartridge_length_mm=float(hi-lo),cartridge_hex_radius_mm=hexr,thread_diameter_mm=thread,thread_pitch_mm=pitch,retention='Head plus metal locknut; captive transverse spring pin; hex keyed rotor',bearing_outer_bond_allowable_MPa=2))
        D.joints[-1]['shaft_min_yield_MPa']=940 if child=='lumbar_flex' or child.endswith('ankle_roll') else 750
        D.joints[-1]['output_hex_engagement_mm']=capt-.35
        metal_y=math.sqrt(3)*(hexr-pinx);fdm_y=math.sqrt(print_r**2-pinx**2)
        D.joints[-1].update(printed_preload_face_recess_mm=.35,fixed_capture_pin_diameter_mm=1.5,fixed_capture_pin_length_mm=2*pinhalf,fixed_capture_slot_width_mm=1.6,fixed_capture_slot_tangent_width_mm=1.9,fixed_capture_printed_engagement_per_end_mm=fdm_y-metal_y-.4)
        if child=='lumbar_flex' or child.endswith('ankle_roll'):
            next(p for p in D.parts if p['name']==pre+'_shaft')['notes']='Custom precision shaft machined from certified Ovako 6115 / 42CrMnMo4-4 +QT stock with yield >=940 MPa retained after processing. Source bar specification 25–60 mm; ordinary annealed rod is not equivalent. Qualification remains conditional on material certificate.'

def open_axis_brakes(D):
    spec=[]
    for side,sg in [('l',1),('r',-1)]:
        spec.extend([(side+'_shoulder_swing',side+'_shoulder_flex',side+'_shoulder_abduct',P['upperarm_'+side],[1,0,0],[0,sg,0],14.5,side+'_shoulder_cross_head'),(side+'_ankle_shoulder_swing',side+'_ankle_roll',side+'_ankle_flex',P['foot_'+side],[0,-1,0],[1,0,0],14.5,side+'_ankle_shoulder_cross_head'),(side+'_elbow',side+'_upperarm_roll',side+'_elbow_flex',P['lowerarm_'+side],[0,1,0],[1,0,0],10.5,None)])
    spec += [('lumbar_shoulder_swing','lumbar_flex','lumbar_side',P['spine_02'],[1,0,0],[0,-1,0],15.2,'lumbar_shoulder_cross_head'),('thorax_shoulder_swing','thorax_side','thorax_flex',P['spine_04'],[0,1,0],[-1,0,0],14.5,'thorax_shoulder_cross_head')]
    for pre,parent,child,origin,axis,orient,ear,headname in spec:
        D.parts[:]=[p for p in D.parts if not (p['name']==headname or (p['name'].startswith(pre+'_') and not any(x in p['name'] for x in ['magnet','pcb','connector','sensor_holder','fork_'])))]
        big=pre in ['lumbar_shoulder_swing','thorax_shoulder_swing']
        hinge(D,pre,parent,child,origin,axis,orient=orient,half=ear-6,ear=ear,bore=6 if big else 4,od=12 if big else 9,friction_od=18 if big else 12,include_sensor=False)
        magnet=next(p for p in D.parts if p['name']==pre+'_magnet');shaft=next(p for p in D.parts if p['name']==pre+'_shaft');ax=np.array(axis,float)
        mv,_=a.mesh_data(moved(magnet['s'],F0[magnet['frame']]));sv,_=a.mesh_data(moved(shaft['s'],F0[shaft['frame']]));sg=np.sign(np.dot(mv.mean(0)-origin,ax));mp=(mv-origin)@(ax*sg);sp=(sv-origin)@(ax*sg);shift=max(0,sp.max()+.2-mp.min())
        if shift>1e-6:
            for p in D.parts:
                if p['name'].startswith(pre+'_') and any(n in p['name'] for n in ['magnet','pcb','connector','sensor_holder']):p['s']=p['s'].translate(F0[p['frame']][:3,:3].T@(ax*sg*shift))
        if pre.endswith('elbow'):
            for p in D.parts:
                if p['name'] in [pre+'_fork_-14',pre+'_fork_14']:
                    sg=-1 if p['name'].endswith('-14') else 1
                    s=beam([0,0,22],[6,sg*18,22],2.8)+beam([6,sg*18,22],[6,sg*18,0],2.8)+beam([6,sg*18,0],[6,sg*12,0],2.8)
                    s-=cyl([0,-20,0],[0,20,0],4.6)
                    p['s']=moved(s,np.linalg.inv(F0[parent])@T(origin))
    pre='neck_shoulder_swing';parent='neck_side';child='neck_flex';W=T(P['neck_01'],np.c_[[1,0,0],[0,0,1],[0,-1,0]])
    D.parts[:]=[p for p in D.parts if not p['name'].startswith(pre+'_') and p['name']!='neck_shoulder_cross_head']
    D.local(pre+'_housing',parent,ring([0,0,1],-5.4,5.4,8.5,4.6),W)
    for zz in [-3,3]:D.local(pre+'_bearing_'+str(zz),parent,ring([0,0,1],zz-2,zz+2,4.5,2.03),W,role='bearing',sku='684ZZ')
    D.local(pre+'_rotor_flange',child,ring([0,0,1],6.4,9.4,6,2.05),W,role='rotor')
    sensor=a.Assembly();sensor.sensor(pre,parent,child,[0,0,-1],13)
    for p in sensor.parts:D.local(p['name'],p['frame'],p['s'],W,role=p['role'])

def apply(D):
    open_axis_brakes(D)
    materialize(D)
    paired(D)
    materialize(D)
    # Clear the stationary H2 brake faces from adjoining printed rotor roots.
    # The annular relief is rotationally invariant about each physical shaft.
    for j in D.joints:
        if 'pressure_web_width_mm' not in j:continue
        axis=np.array(j['axis_world']);origin=np.array(j['center_mm']);child=j['axis_id'];pre=j['id']
        pads=[p for p in D.parts if p['name'].startswith(pre+'_friction_')]
        for pad in pads:
            world=moved(pad['s'],F0[pad['frame']]);v,f=a.mesh_data(world);proj=(v-origin)@axis
            rel=tube(origin+axis*(proj.min()-.15),origin+axis*(proj.max()+.15),j['friction_od_mm']/2+.25,j['bearing_diameter_mm']/2+.05)
            for p in D.parts:
                if p['frame']==child and p['role'] in ['structure','rotor','shell'] and p['name']!=pre+'_hub':p['s']-=moved(rel,np.linalg.inv(F0[child]))
    # Explicit keyed outlets from the remotely supported hip X and Z journals.
    # These replace previously unconnected tube/shaft ends.
    for side in ['l','r']:
        hip=P['thigh_'+side]
        for pre,child,axis,start,end,collar0,collar1,pinpos,d,ro in [
            (side+'_hip_abduction',side+'_hip_abduct',np.array([1,0,0]),-HIP_BACK+14,-HIP_BACK+32,-HIP_BACK+23,-HIP_BACK+29,-HIP_BACK+26,6,7),
            (side+'_hip_twist',side+'_hip_roll',np.array([0,0,-1]),84,92,85,90,88,6,7)]:
            p=next(p for p in D.parts if p['name']==pre+'_shaft');trans=np.linalg.inv(F0[child]);pinaxis=np.array([0,0,1]) if pre.endswith('abduction') else np.array([1,0,0]);pr=1 if d==4 else 1.5
            hole=cyl(hip+axis*pinpos-pinaxis*(ro+1),hip+axis*pinpos+pinaxis*(ro+1),pr+.025)
            p['s']+=moved(cyl(hip+axis*start,hip+axis*end,d/2)-hole,trans)
            for pin in D.parts:
                if pin['name']==pre+'_retention_pin_1':
                    vv,_=a.mesh_data(moved(pin['s'],F0[child]));pc=vv.mean(0);_,V=np.linalg.eigh(np.cov(vv.T));pa=V[:,-1]
                    p['s']-=moved(cyl(pc-pa*6,pc+pa*6,.75),trans)
            socket=tube(hip+axis*collar0,hip+axis*collar1,ro,d/2+.025)-hole
            D.local(pre+'_keyed_outlet',child,socket,np.eye(4),role='rotor',note='Full-thickness socket around the extended steel journal; transverse spring pin transfers torque and prevents separation.')
            D.local(pre+'_outlet_pin',child,tube(hip+axis*pinpos-pinaxis*(ro-.2),hip+axis*pinpos+pinaxis*(ro-.2),pr,pr*.55),np.eye(4),role='metal',sku=f'ROLL_PIN_{2*pr:g}_CUT')
    for pre,angle in load(HERE/'sensor_layout.json').items():
        j=next(j for j in D.joints if j['id']==pre);o=np.array(j['center_mm']);W=T(o)@rot(j['axis_world'],angle)@T(-o)
        for p in D.parts:
            if p['name'].startswith(pre+'_') and any(n in p['name'] for n in ['pcb','connector','sensor_holder']):
                p['s']=moved(p['s'],np.linalg.inv(F0[p['frame']])@W@F0[p['frame']])
        j['sensor_clocking_delta_deg']=angle
    for p in D.parts:
        if p['name'].startswith('l_shoulder_pitch_') and any(n in p['name'] for n in ['pcb','connector','sensor_holder']):
            p['s']=p['s'].translate(F0[p['frame']][:3,:3].T@np.array([2.,0,0]))
            p['notes']+=' Board shifted 2 mm forward; sensing IC remains on axis at a 2 mm offset from board centre.'
    pre='l_shoulder_pitch';holder=next(p for p in D.parts if p['name']==pre+'_sensor_holder');cap=next(p for p in D.parts if p['name']==pre+'_rear_thrust_cap');j=next(j for j in D.joints if j['id']==pre);axis=np.array(j['axis_world']);origin=np.array(j['center_mm'])
    vv,_=a.mesh_data(moved(cap['s'],F0[cap['frame']]));proj=(vv-origin)@axis
    relief=cyl(origin+axis*(proj.min()-.25),origin+axis*(proj.max()+.25),j['friction_od_mm']/2+.25)
    cut=holder['s']-moved(relief,np.linalg.inv(F0[holder['frame']]));_=cut.volume();holder['s']=cut
    materialize(D)
    continuous_forks(D)
    # Local elbow relief: move the sensing cluster to the opposite end of
    # the same E axis, and keep the proximal fork on a continuous D5.2 route.
    e=P['lowerarm_l'];mirror=T(e)@np.diag([1.,-1,1,1])@T(-e)
    forkpoints=[[0,0,22],[-3,0,22],[-3,-10.5,22],[-3,-10.5,7],[0,-10.5,7],[0,-10.5,0]]
    fork_relief=union(beam(x,y,2.8) for x,y in zip(forkpoints[:-1],forkpoints[1:]))
    for p in D.parts:
        fr=p['frame']
        if p['name'].startswith('l_elbow_') and any(t in p['name'] for t in ['magnet','pcb','connector','sensor_holder']):
            p['s']=moved(p['s'],np.linalg.inv(F0[fr])@mirror@F0[fr])
            p['notes']+=' Encoder mounted on opposite end of unchanged elbow axis; calibration sign is determined at assembly.'
        if p['name']=='l_elbow_fork_-14':
            shape=union(beam(x,y,2.6) for x,y in zip(forkpoints[:-1],forkpoints[1:]))-cyl([0,-20,0],[0,20,0],4.58)
            p['s']=moved(shape,np.linalg.inv(F0[fr])@T(e));p['notes']='Continuous D5.2 local fork routed 3 mm rearward. Coaxial main upperarm tube and E axis unchanged.'
        if p['name'].startswith('l_elbow_pressure_'):
            p['s']-=moved(fork_relief,np.linalg.inv(F0[fr])@T(e))
            p['notes']+=' 25 mm web, 9 mm screw arm and 10 mm screw pitch. Negative-side plate omits the upper return flange to clear the adjacent clavicle cap. D5.6 relief retains the continuous proximal fork; strength counts only one full return and deducts the full slot width.'
        if p['name'].startswith('r_shoulder_pitch_') and any(t in p['name'] for t in ['pcb','connector','sensor_holder']):
            p['s']=p['s'].translate(F0[fr][:3,:3].T@np.array([0.,0,3.]))
            p['notes']+=' Full board and holder shifted 3 mm in its plane; IC footprint 3 mm off board centre remains on the shaft sensing axis.'
    j=next(j for j in D.joints if j['id']=='l_elbow');j.update(structural_link_clearance_width_mm=5.6,pressure_return_count_at_relief=1)
    materialize(D)
    # Turn the left Z cassette end-for-end about its unchanged axis, and move
    # the right one 3 mm along Z. All parts in each cassette move together;
    # neither effective C centre nor any bone length changes.
    center=P['clavicle_l']+[0,0,-64.6]
    flip=T(center)@np.diag([1.,1,-1,1])@T(-center)
    for p in D.parts:
        tf=flip if p['name'].startswith('l_clavicle_z_') else (T([0,0,3]) if p['name'].startswith('r_clavicle_z_') else None)
        if tf is not None:
            p['s']=moved(p['s'],np.linalg.inv(F0[p['frame']])@tf@F0[p['frame']])
            p['notes']+=' A update: cassette reversed/shifted only along the original C axis; physical centre retained.'
    for j in D.joints:
        if j['id']=='l_clavicle_z':j['axial_end_for_end_plane_relative_z_mm']=-64.6
        if j['id']=='r_clavicle_z':j['axial_station_shift_mm']=3
    materialize(D)
    preload_face_relief(D)
    materialize(D)
    # A local clearance pocket for the actual neighbouring thorax pressure
    # channel, swept over its full configured flex range. The thick saddle
    # is rechecked using sections of the resulting mesh, never the stock D13.5.
    pressure=next(p for p in D.parts if p['name']=='thorax_shoulder_swing_pressure_1')
    seat=next(p for p in D.parts if p['name']=='left_clavicle_seat')
    shape=moved(pressure['s'],F0[pressure['frame']]);origin=P['spine_04'];lim=next(a['limits_deg'] for a in PROFILE['axes'] if a['id']=='thorax_flex')
    envelope=[]
    for angle in np.arange(lim[0],lim[1]+.5,1):
        w=moved(shape,T(origin)@rot([0,1,0],-angle)@T(-origin))
        envelope.extend(w.translate(d) for d in [[0,0,0],[.3,0,0],[-.3,0,0],[0,.3,0],[0,-.3,0],[0,0,.3],[0,0,-.3]])
    before=seat['s'].volume();seat['s']-=moved(union(envelope),np.linalg.inv(F0[seat['frame']]));after=seat['s'].volume()
    seat['notes']+=f' Actual thorax pressure-channel swept pocket, 1 degree samples with 0.30 mm Cartesian relief; removed {before-after:.3f} mm3. Section and core checks apply after machining.'
    materialize(D)
    machine_static_interfaces(D)
    materialize(D)
    remove_isolated_cutoffs(D)
    materialize(D)


def materialize(D):
    """Resolve CSG expressions before composing new local/world transforms.
    Mesh roundtrip prevents deferred native Boolean evaluation from depending on
    the order in which later diagnostics happen to request a volume or bounds.
    """
    for p in D.parts:
        expected=p['s'].volume();vv,ff=a.mesh_data(p['s'])
        solid=md.Manifold(md.Mesh64(np.array(vv,dtype=np.float64,copy=True,order='C'),np.array(ff,dtype=np.uint64,copy=True,order='C')))
        if abs(solid.volume()-expected)>max(1e-5,abs(expected)*1e-8):raise ValueError('CSG materialization volume mismatch '+p['name'])
        p['s']=solid


def preload_face_relief(D):
    """Extend the axial preload clearance to ALL linked printed features, not
    only the named socket/hub. This operation removes material only."""
    for j in D.joints:
        pre=j['id'];axis=np.array(j['axis_world']);o=np.array(j['center_mm']);h2='pressure_web_width_mm' in j
        pads=[p for p in D.parts if p['name'].startswith(pre+('_friction_' if h2 else '_face_pad_'))]
        for p0 in pads:
            vv,_=a.mesh_data(moved(p0['s'],F0[p0['frame']]));proj=(vv-o)@axis
            clearance=cyl(o+axis*(proj.min()-.35),o+axis*(proj.max()+.35),j['friction_od_mm']/2+.2)
            for p in D.parts:
                if p['role'] in ['structure','rotor','shell'] and p['frame'] in [p0['frame'],j['axis_id']]:
                    s=p['s']-moved(clearance,np.linalg.inv(F0[p['frame']]));_=s.volume();p['s']=s
        if h2:
            for cap in [p for p in D.parts if p['name'].startswith(pre+'_rotor_cap_')]:
                vv,_=a.mesh_data(moved(cap['s'],F0[cap['frame']]));proj=(vv-o)@axis
                clearance=cyl(o+axis*(proj.min()-.35),o+axis*(proj.max()+.35),j['friction_od_mm']/2+.6)
                for p in D.parts:
                    if p['frame']==j['axis_id'] and p['role'] in ['structure','rotor','shell']:
                        s=p['s']-moved(clearance,np.linalg.inv(F0[p['frame']]));_=s.volume();p['s']=s


def continuous_forks(D):
    """Printed links pass through deliberate unloaded-edge reliefs in the metal
    calipers. These reliefs replace the old accidental cuts THROUGH the links.
    Channel strength calculation subtracts their full width conservatively.
    """
    for j in D.joints:
        pre=j['id']
        if pre not in ['l_shoulder_swing','r_shoulder_swing','lumbar_shoulder_swing','thorax_shoulder_swing','l_ankle_shoulder_swing','r_ankle_shoulder_swing','l_knee','r_knee']:continue
        plate=next(p for p in D.parts if p['name']==pre+'_pressure_1');fr=plate['frame'];axis=np.array(j['axis_world']);o=np.array(j['center_mm'])
        vv,_=a.mesh_data(moved(plate['s'],F0[fr]));cent=vv.mean(0)-o;xx=-(cent-axis*np.dot(cent,axis));xx/=np.linalg.norm(xx);W=T(o,np.c_[xx,axis,np.cross(xx,axis)])
        if pre.endswith('knee'):
            links=[p for p in D.parts if p['name'].startswith(pre+'_fork_link_')]
            brace=union(moved(p['s'],F0[p['frame']]) for p in links)
            # Cylindrical clearance around the explicitly defined load links.
            rel=union(beam(o+[0,0,23],o+[16,sg*12,0],3.4) for sg in [-1,1])
        else:
            socket=next(p for p in D.parts if p['name']==pre.replace('swing','pitch')+'_output_socket')
            sb=np.array(moved(socket['s'],np.linalg.inv(W)@F0[socket['frame']]).bounding_box()).reshape(2,3);c0=sb.mean(0);rootr=max(sb[1,1]-c0[1],sb[1,2]-c0[2])-.7
            ear=j['bearing_span_mm']/2;ro=j['friction_od_mm']/2
            points=[(c0+[.6,sg*rootr,0],np.array([-ro-9,sg*ear,0])) for sg in [-1,1]]
            brace=moved(union(beam(x,y,3.2) for x,y in points),W);rel=moved(union(beam(x,y,3.4) for x,y in points),W)
            D.local(pre+'_continuous_fork_links',fr,brace,np.eye(4),note='Two D6.4 solid load links. Metal pressure-plate edge reliefs leave 0.2 mm clearance; preload does not clamp these printed links.')
        for p in D.parts:
            if p['name'].startswith(pre+'_pressure_'):
                p['s']-=moved(rel,np.linalg.inv(F0[fr]));_=p['s'].volume()
                p['notes']+=' Edge clearance for continuous D6.4 load links; 6.8 mm full-width deduction included in channel calculation.'
        j['structural_link_clearance_width_mm']=6.8


def remove_isolated_cutoffs(D):
    """Remove individually identified machining remnants, never bridge a gap by
    treating spatially separate printed islands as one printable part."""
    from groups import physical_components
    allowed=['thoracic_root_neck','right_clavicle_seat','r_clavicle_vertical_transfer','l_hip_L_yoke_a','r_hip_L_yoke_a','l_hip_L_yoke_b','r_hip_L_yoke_b','l_shin_key_neck','r_shin_key_neck','l_ankle_input_leg_-7','l_ankle_input_leg_7','r_ankle_input_leg_-7','r_ankle_input_leg_7','l_heel_stem','r_heel_stem','l_toe_pad','r_toe_pad','neck_humeral_sensor_holder']
    allowed+=['pelvis_lumbar_brace_29','pelvis_lumbar_brace_33']
    # D13 saddle: inspected isolated 0.8 mm machining sheet (3.379 mm3)
    # and a 0.231 mm3 bore chip; the connected 3632.89 mm3 body is retained.
    allowed+=['left_clavicle_seat']
    def family(fr):
        while NODES[fr]['axis'] is None and NODES[fr]['parent']:fr=NODES[fr]['parent']
        return fr
    removed=[]
    for fr in dict.fromkeys(family(p['frame']) for p in D.parts):
        printed=[p for p in D.parts if family(p['frame'])==fr and p['role'] in ['structure','rotor','shell']]
        if not printed:continue
        shapes=[moved(p['s'],np.linalg.inv(F0[fr])@F0[p['frame']]) for p in printed];bodies=physical_components(union(shapes));cuts=[]
        for s in bodies:
            if s.volume()>=30:continue
            names=[p['name'] for p,t in zip(printed,shapes) if (s^t).volume()>.001]
            if all(n in allowed for n in names) or (names==['l_clavicle_vertical_transfer'] and s.volume()<.01):cuts.append(s);removed.append(dict(frame=fr,features=names,volume_mm3=s.volume(),bounds_in_rigid_frame_mm=s.bounding_box()))
            else:raise ValueError('Unreviewed detached small body: '+str((fr,names,s.volume())))
        if cuts:
            cut=union(cuts)
            for p,t in zip(printed,shapes):
                removed_volume=(t^cut).volume()
                if removed_volume<1e-8:continue
                clipped=t-cut;v=clipped.volume()
                if abs(t.volume()-v-removed_volume)>1e-5:raise ValueError('Cutoff volume mismatch '+p['name'])
                p['s']=moved(clipped,np.linalg.inv(F0[p['frame']])@F0[fr])
    D.cutoffs=removed
    D.parts[:]=[p for p in D.parts if p['s'].volume()>1e-7]

def machine_static_interfaces(D):
    """Make real sockets/bores where joined printed features meet metal.

    This is restricted to the SAME rigid body. It cannot erase moving-body
    collisions or move a joint. Subsequent material/core/connection tests apply.
    """
    def family(fr):
        while NODES[fr]['axis'] is None and NODES[fr]['parent']:fr=NODES[fr]['parent']
        return fr
    hard={}
    for p in D.parts:
        if p['role'] not in ['metal','bearing','magnet','pcb','connector','friction']:continue
        fr=family(p['frame']);s=moved(p['s'],np.linalg.inv(F0[fr])@F0[p['frame']]);hard.setdefault(fr,[]).append((p['name'],s,np.array(s.bounding_box()).reshape(2,3)))
    audit=[]
    for p in list(D.parts):
        if p['role'] not in ['structure','rotor','shell']:continue
        fr=family(p['frame']);w=np.linalg.inv(F0[fr])@F0[p['frame']];s=moved(p['s'],w);b=np.array(s.bounding_box()).reshape(2,3);cuts=[];names=[]
        for name,t,tb in hard.get(fr,[]):
            if np.all(b[1]>tb[0]+1e-7) and np.all(tb[1]>b[0]+1e-7) and (s^t).volume()>.001:cuts.append(t);names.append(name)
        if cuts:
            before=s.volume();s-=union(cuts);after=s.volume();audit.append(dict(part=p['name'],mating_hardware=names,removed_mm3=before-after,remaining_mm3=after))
            if after<.001:D.parts.remove(p)
            else:p['s']=moved(s,np.linalg.inv(w))
    D.interface_machining=audit
