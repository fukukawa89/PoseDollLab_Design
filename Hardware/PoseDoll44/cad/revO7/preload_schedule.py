"""Nominal preload schedule bounded by catalog deflection; not a force guarantee."""
from decimal import Decimal,ROUND_FLOOR

def advance(wear,compression,pitch_mm,work_height_mm,free_height_mm,series=4,stops=12):
 if any(v<0 for v in [*wear,*compression]) or min(pitch_mm,work_height_mm,free_height_mm,series,stops)<=0:raise ValueError('Invalid preload dimensions')
 if free_height_mm<=work_height_mm:raise ValueError('Spring working height must be below free height')
 d=sum((Decimal(str(x)) for x in (*wear,*compression)),Decimal(0));pitch=Decimal(str(pitch_mm))
 index=int((Decimal(stops)*d/pitch).to_integral_value(rounding=ROUND_FLOOR));dz=pitch*index/Decimal(stops)
 h=Decimal(str(work_height_mm))+(d-dz)/Decimal(series)
 if h>=Decimal(str(free_height_mm)):raise ValueError('Preload would be lost')
 return {'index':index,'cap_advance_mm':float(dz),'cap_rotation_deg':index*360/stops,'spring_height_mm':float(h),'total_wear_compression_mm':float(d),'uncompensated_axial_mm':float(d-dz),'nominal_catalog_deflection_not_exceeded':h>=Decimal(str(work_height_mm))}
