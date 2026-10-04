"""O15 raw-angle composition. Independent of legacy PDG5/41 transport.
Four physical measurements are composed into a three-rotation joint; no raw
channel is dropped. Hardware calibration and a qualified transport remain gates.
"""
from dataclasses import dataclass
import math
import numpy as np

@dataclass(frozen=True)
class RawAngle:
    angle_deg: float | None
    status: str
    capture_id: int
    boot_id: str
    age_ms: float

def rotation(axis,deg):
    x,y,z=axis;c=math.cos(math.radians(deg));s=math.sin(math.radians(deg));K=np.array([[0,-z,y],[z,0,-x],[-y,x,0]],float)
    return np.eye(3)+s*K+(1-c)*(K@K)

def wrap(a):return (a+180)%360-180

def compose_matrix(kind,q):
    if kind in ('tut','wide_tut'):order=[(0,0,1),(1,0,0),(0,1,0),(0,0,1)]
    elif kind=='three_axis':order=[(0,0,1),(1,0,0),(0,1,0)]
    else:raise ValueError('unsupported compound joint')
    if len(q)!=len(order):raise ValueError('raw channel count')
    R=np.eye(3)
    for axis,a in zip(order,q):R=R@rotation(axis,a)
    return R

def semantic_matrix(axes,angles):
    M=np.eye(3)
    for axis,a in zip(axes,angles):M=M@rotation(axis,a)
    return M

def decode_rotation(M,axes,limits,previous=None):
    """Return a valid bounded Euler branch, preserving previous branch at gimbal lock."""
    M=np.asarray(M,float)
    if M.shape!=(3,3) or not np.isfinite(M).all() or np.max(np.abs(M.T@M-np.eye(3)))>1e-7 or abs(np.linalg.det(M)-1)>1e-7:raise ValueError('not a proper rotation')
    axes=np.asarray(axes,float);ids=np.argmax(np.abs(axes),axis=1).tolist();signs=np.array([axes[i,ax] for i,ax in enumerate(ids)])
    if any(abs(abs(s)-1)>1e-9 for s in signs):raise ValueError('axis not a signed coordinate axis')
    rows=[]
    if ids==[2,1,0]:
        b=math.asin(np.clip(-M[2,0],-1,1));c=math.cos(b)
        if abs(c)>1e-7:rows.append([math.atan2(M[1,0],M[0,0]),b,math.atan2(M[2,1],M[2,2])])
    elif ids==[1,0,2]:
        b=math.asin(np.clip(-M[1,2],-1,1));c=math.cos(b)
        if abs(c)>1e-7:
            a=math.atan2(M[0,2],M[2,2]);d=math.atan2(M[1,0],M[1,1]);rows.extend([[a,b,d],[a+math.pi,math.pi-b,d+math.pi]])
    else:raise ValueError('unsupported semantic axis order')
    choices=[]
    for row in rows:
        q=np.array([wrap(math.degrees(a)) for a in row])/signs
        if all(lo-1e-7<=a<=hi+1e-7 for a,(lo,hi) in zip(q,limits)) and np.max(np.abs(semantic_matrix(axes,q)-M))<1e-7:choices.append(q)
    if not choices and ids==[1,0,2] and abs(abs(M[1,2])-1)<1e-7:
        # At +/-90 degrees the first and third angles are not independently
        # observable from a rotation. Keep the prior first angle when available.
        b=math.degrees(math.asin(np.clip(-M[1,2],-1,1)))
        aa=[previous[0]] if previous is not None else []
        aa+=list(np.linspace(limits[0][0],limits[0][1],101))
        for a in aa:
            tail=rotation(axes[1],b/signs[1]).T@rotation(axes[0],a).T@M
            d=wrap(math.degrees(math.atan2(tail[1,0],tail[0,0])))/signs[2];q=np.array([a,b/signs[1],d])
            if all(lo-1e-7<=v<=hi+1e-7 for v,(lo,hi) in zip(q,limits)) and np.max(np.abs(semantic_matrix(axes,q)-M))<1e-7:choices.append(q)
    if not choices:raise ValueError('rotation outside semantic range')
    ref=np.zeros(3) if previous is None else np.asarray(previous,float)
    return min(choices,key=lambda q:float(np.sum((q-ref)**2))).tolist()

def compose_group(group,samples,*,capture_id,boot_id,max_age_ms,previous=None):
    ids=group['raw_ids'];raw=[samples.get(k) for k in ids];n=len(group['axis_ids']);bad='valid';reason=None
    for s in raw:
        if s is None or s.status=='missing':bad='missing';reason='missing raw member';continue
        if s.status!='valid' or s.angle_deg is None or not math.isfinite(s.angle_deg) or s.capture_id!=capture_id or s.boot_id!=boot_id or not math.isfinite(s.age_ms) or not 0<=s.age_ms<=max_age_ms:
            bad='fault';reason='invalid, stale or mixed capture raw member';break
    if bad!='valid':return {'status':bad,'axis_ids':group['axis_ids'],'angles_deg':[None]*n,'reason':reason}
    q=[s.angle_deg for s in raw]
    if len(q)!=len(group['raw_limits_deg']) or any(not lo-1e-7<=v<=hi+1e-7 for v,(lo,hi) in zip(q,group['raw_limits_deg'])):return {'status':'fault','axis_ids':group['axis_ids'],'angles_deg':[None]*n,'reason':'raw mechanical range'}
    try:
        if group['kind'] in ('tut','wide_tut','three_axis'):
            M=np.asarray(group['F'])@compose_matrix(group['kind'],q)@np.asarray(group['V']).T
            values=decode_rotation(M,group['semantic_axes'],group['semantic_limits_deg'],previous)
        elif group['kind'] in ('core','clavicle_core','ankle_core'):
            a,b=q;values=[group['beta0']-b,a/group['alpha_sign']]
        else:values=[q[0]/group['hinge_sign']]
        if any(not lo-1e-7<=v<=hi+1e-7 for v,(lo,hi) in zip(values,group['semantic_limits_deg'])):raise ValueError('semantic range')
    except ValueError as e:return {'status':'fault','axis_ids':group['axis_ids'],'angles_deg':[None]*n,'reason':str(e)}
    return {'status':'valid','axis_ids':group['axis_ids'],'angles_deg':values,'raw_count':len(raw),'capture_id':capture_id,'boot_id':boot_id}


def compose_frame(mapping, samples, axis_order, *, capture_id, boot_id,
                  max_age_ms=1000, previous=None):
    """Validate the complete 46-to-44 mapping before composing one snapshot.

    A diagnostic frame can be mathematically valid without being eligible for
    hardware capture. Qualification belongs to the acquisition/calibration gate.
    The pelvis values are explicit fixed channels, never invented measurements.
    """
    groups=mapping['groups'];fixed=mapping['fixed_axes']
    raw_ids=[rid for g in groups for rid in g['raw_ids']]
    measured=[aid for g in groups for aid in g['axis_ids']]
    if (len(axis_order)!=44 or len(set(axis_order))!=44 or
        len(raw_ids)!=46 or len(set(raw_ids))!=46 or
        len(measured)!=41 or len(set(measured))!=41 or
        set(fixed)!={'pelvis.yaw','pelvis.pitch','pelvis.roll'} or
        len(fixed)!=3 or set(fixed)&set(measured) or
        set(measured+fixed)!=set(axis_order)):
        raise ValueError('invalid or duplicate full-body channel layout')
    if set(samples)-set(raw_ids):raise ValueError('unknown physical channel')
    if (not isinstance(capture_id,int) or isinstance(capture_id,bool) or capture_id<0 or
        not isinstance(boot_id,str) or not boot_id or
        not math.isfinite(max_age_ms) or max_age_ms<0):
        raise ValueError('invalid capture identity or age budget')
    previous={} if previous is None else previous
    channels={aid:{'status':'fixed','angle_deg':0.} for aid in fixed};details=[]
    for group in groups:
        result=compose_group(group,samples,capture_id=capture_id,boot_id=boot_id,
                             max_age_ms=max_age_ms,previous=previous.get(group['id']))
        details.append({'group':group['id'],**result})
        for aid,value in zip(group['axis_ids'],result['angles_deg']):
            channels[aid]={'status':result['status'],'angle_deg':value}
    status='fault' if any(v['status']=='fault' for v in channels.values()) else 'missing' if any(v['status']=='missing' for v in channels.values()) else 'valid'
    return {'schema':'O15-SEMANTIC-SNAPSHOT/1','capture_id':capture_id,
            'boot_id':boot_id,'status':status,'axis_order':list(axis_order),
            'channels':[channels[a] for a in axis_order], 'groups':details,
            'capture_eligible':False,
            'qualification':'Diagnostic composition only; calibrated hardware acquisition is required.'}
