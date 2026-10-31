"""O22 periodic or mounted bounded-range measured INL correction, preserving original raw data and provenance."""
from copy import deepcopy
from device import capture_window as base_capture, digest, number
def correct_sensor(angle, lut):
    if not number(angle) or not 0<=angle<360:raise ValueError('sensor angle')
    if lut is None:return angle
    if not isinstance(lut,dict):raise ValueError('LUT type')
    if lut.get('kind')=='bounded_delta_deg':
        anchor=lut.get('anchor_sensor_deg');knots=lut.get('knots',[])
        if not number(anchor) or not 0<=anchor<360:raise ValueError('bounded LUT anchor')
        if not isinstance(knots,list) or len(knots)<5:raise ValueError('bounded LUT needs >=5 measured knots')
        if any(not isinstance(p,list) or len(p)!=2 or not all(number(x) for x in p) for p in knots):
            raise ValueError('bounded LUT finite pairs')
        xs=[p[0] for p in knots]
        if xs[0]!=0 or not 0<xs[-1]<355 or any(b<=a for a,b in zip(xs,xs[1:])):
            raise ValueError('bounded LUT order/range')
        if any(b[0]-a[0]>15+1e-9 for a,b in zip(knots,knots[1:])):
            raise ValueError('bounded LUT unmeasured gap >15deg')
        if any(b[0]+b[1]<=a[0]+a[1] for a,b in zip(knots,knots[1:])):
            raise ValueError('LUT folds angle')
        u=(angle-anchor)%360
        if u>xs[-1]+1e-9:raise ValueError('outside measured bounded calibration interval')
        for a,b in zip(knots,knots[1:]):
            if a[0]<=u<=b[0]+1e-9:
                delta=a[1]+(b[1]-a[1])*(u-a[0])/(b[0]-a[0])
                return (angle+delta)%360
        raise ValueError('bounded LUT interval')
    if lut.get('kind')!='periodic_delta_deg':raise ValueError('LUT type')
    knots=lut.get('knots',[])
    if not isinstance(knots,list) or len(knots)<12:raise ValueError('LUT needs at least 12 measured knots')
    if any(not isinstance(p,list) or len(p)!=2 or not all(number(x) for x in p) for p in knots):raise ValueError('LUT finite pairs')
    xs=[p[0] for p in knots]
    if xs[0]!=0 or xs[-1]>=360 or any(b<=a for a,b in zip(xs,xs[1:])):raise ValueError('LUT order/range')
    cyclic=knots+[[360,knots[0][1]]]
    if any(b[0]+b[1]<=a[0]+a[1] for a,b in zip(cyclic,cyclic[1:])):raise ValueError('LUT folds angle')
    for a,b in zip(cyclic,cyclic[1:]):
        if a[0]<=angle<b[0]:
            delta=a[1]+(b[1]-a[1])*(angle-a[0])/(b[0]-a[0])
            return (angle+delta)%360
    raise ValueError('LUT interval')
def capture_window(profile,calibration,scans,**kw):
    original=deepcopy(scans);cal=deepcopy(calibration);rows=deepcopy(scans)
    try:
        axes=cal['axes']
        for k in profile['raw_order']:
            a=axes[k];lut=a.get('linearization')
            a['sensor_zero_deg']=correct_sensor(a['sensor_zero_deg'],lut)
            for row in rows:
                s=row['channels'][k];s['sensor_deg']=correct_sensor(s['sensor_deg'],lut)
    except (ValueError,KeyError,TypeError) as e:
        return {'status':'REJECTED','reason':'calibration or sensor: '+str(e),'hardware_capture_eligible':False}
    result=base_capture(profile,cal,rows,**kw)
    if result['status']=='VALID_MEASUREMENT':
        result['raw_scans']=original;result['corrected_sensor_scans']=rows
        result['calibration']=deepcopy(calibration);result['calibration_sha256']=digest(calibration)
        if any(a.get('linearization',{}).get('source')!='MEASURED_FIXTURE' for a in axes.values() if a.get('linearization')):
            result['hardware_capture_eligible']=False
    return result
