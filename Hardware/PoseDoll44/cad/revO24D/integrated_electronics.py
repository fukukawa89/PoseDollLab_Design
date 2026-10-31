"""O23-size native PCB, symmetric thoracic backplate and real fixing hardware."""
from fullbody import *
def apply(D):
    fr='thorax_flex';base=float(INTEGRATION.get('backboard_bottom_mm',385));px=float(INTEGRATION.get('backboard_x_mm',-61));plate_x=px+11.5
    W=np.eye(4);folder=OUT/'electronics/carrier';layout=load(folder/'placement.json')
    holes=[(sg*29,base+z) for sg in [-1,1] for z in [3,57]]
    # Open centre gives the inward-facing O23 connector bank service access.
    plate=box([plate_x-2.5,-35,base-3],[plate_x,35,base+63])-box([plate_x-3,-23,base+8],[plate_x+1,23,base+52])
    # Symmetric upper lip recess clears both clavicle sensor sweep corridors.
    plate-=box([plate_x-3,-23,base+58],[plate_x+1,23,base+64])
    for y,z in holes:
        plate+=tube([px+1.6,y,z],[plate_x,y,z],2.5,1.15)
        plate-=cyl([px-4,y,z],[plate_x+1,y,z],1.15)
        # M2 steel nut in a hex pocket; a shoulder around it retains the plate.
        nut=k.nut([plate_x-1.7,y,z],[1,0,0],2,4,1.6)
        plate-=nut
        D.local('backboard_nut_'+str(y)+'_'+str(z),fr,nut,W,role='metal',sku='M2_DIN439')
        D.local('backboard_screw_'+str(y)+'_'+str(z),fr,k.screw([px-.5,y,z],[1,0,0],2,14),W,role='metal',sku='M2x14',note='Four through fasteners into captured metal nuts; board is supported by four D5 standoffs.')
        D.local('backboard_washer_'+str(y)+'_'+str(z),fr,k.washer([px-.5,y,z],[1,0,0],5,2.2,.5),W,role='metal',sku='M2_WASHER')
    for y in [-22,22]:
        for z in [420,438]:
            plate+=beam([plate_x-1,y,z],[-40,y,z],3.5)
    # Circular wire pass-throughs behind every inward port; leave the side rails intact.
    for row in layout['footprints']:
        if row['side']=='B' and row['reference'].startswith('J'):
            u,v=row['x_mm'],row['y_mm'];yy=32-u;zz=base+60-v
            plate-=cyl([plate_x-3,yy,zz],[plate_x+1,yy,zz],2.5)
    D.local('electronics_backplate',fr,plate,W,role='structure',note='Symmetric open 70 x 66 x 2.5 mm backplate. Four continuous D7 roots join only the thoracic rigid frame; four D5 standoffs, M2 screws and captive steel nuts. Open centre for inward connector leads. No pelvis fixture.')
    pcb=box([px,-32,base],[px+1.6,32,base+60])
    for y,z in holes:pcb-=cyl([px-1,y,z],[px+2.5,y,z],1.1)
    D.local('electronics_carrier_FR4',fr,pcb,W,role='pcb',note='Native O24D 64 x 60 x 1.6 mm four-layer PCB, derived from O23. Four mounting holes at 58 x 54 mm pitch; 38 keyed six-way SPI harness ports.',sku='O24D_SPI_CARRIER')
    envelopes=[]
    for row in layout['footprints']:
        ref=row['reference']
        if ref.startswith(('H','TP')):continue
        u0,v0,u1,v1=row['bbox_mm'];front=row['side']=='F'
        if ref.startswith('J'):
            height=7 if ref in ['J1','J2'] else (7.5 if ref=='J3' else 5)
        elif ref.startswith('U'):height=1.3
        elif ref.startswith('L'):height=3.0
        elif ref.startswith(('D','F')):height=2.2
        else:height=1.1
        x0,x1=(px-height,px) if front else (px+1.6,px+1.6+height)
        shape=box([x0,32-u1,base+60-v1],[x1,32-u0,base+60-v0])
        D.local('electronics_'+ref,fr,shape,W,role='connector',note='Conservative component/mated connector envelope from the native footprint bounding box; height is a design allowance, not an exact package mesh.')
        envelopes.append(dict(reference=ref,side=row['side'],bounds_world_mm=[[x0,32-u1,base+60-v1],[x1,32-u0,base+60-v0]],height_allowance_mm=height))
    mcu=box([px-8.6,9.3,base+34.5],[px-7,30.3,base+52.3])
    D.local('electronics_XIAO_module',fr,mcu,W,role='pcb',note='21 x 17.8 mm XIAO ESP32-S3 module above two 2.54 mm headers; USB cable exits the top of the carrier.')
    D.local('electronics_XIAO_USB',fr,box([px-11.7,14.7,base+49],[px-8.6,23.7,base+57]),W,role='metal',note='USB-C receptacle envelope; external cable not a mechanical support.')
    D.electronics=dict(board_mm=[64,60,1.6],frame=fr,board_origin_world_mm=[px,32,base+60],board_u_world=[0,-1,0],board_v_world=[0,0,-1],mount_holes_world_mm=[[px,y,z] for y,z in holes],standoff_outer_mm=5,standoff_bore_mm=2.3,backplate_mm=[2.5,70,66],envelopes=envelopes,fastener='4 x M2x14 through screws, washers and captured steel nuts',routing_access='Open-centre backplate; no solid wall behind the inward bank',sensor_interface='Six factory-soldered wires at each sensor; keyed 6P JST SH only at carrier')
    put(OUT/'electronics/mechanical_integration.json',D.electronics)
