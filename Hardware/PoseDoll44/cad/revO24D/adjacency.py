"""User-defined acceptance: all moving parts within/touching adjacent bone segments.

Gimbal stages are NOT excluded merely because an intermediate frame separates
them. Non-adjacent body contacts are advisory, per user direction 2026-10-23.
"""
def segment(frame):
    if frame == 'pelvis': return 'pelvis'
    for pre in ['lumbar', 'thorax', 'neck']:
        if frame.startswith(pre): return pre
    if frame == 'head': return 'neck'
    side, name = frame.split('_', 1)
    if name == 'chest': return 'thorax'
    for tokens, label in [(['clavicle'], 'clavicle'), (['shoulder','upperarm'], 'upperarm'),
                          (['elbow','forearm'], 'forearm'), (['wrist'], 'hand'),
                          (['hip'], 'thigh'), (['knee'], 'shin'), (['ankle'], 'foot'), (['toe'], 'toe')]:
        if any(name.startswith(t) for t in tokens): return side+'_'+label
    raise ValueError('Unclassified frame '+frame)

EDGES=[('pelvis','lumbar'),('lumbar','thorax'),('thorax','neck')]
for side in ['l','r']:
    for chain in [['thorax',side+'_clavicle',side+'_upperarm',side+'_forearm',side+'_hand'],
                  ['pelvis',side+'_thigh',side+'_shin',side+'_foot',side+'_toe']]:
        EDGES.extend(zip(chain[:-1],chain[1:]))

def required(a,b):
    x,y=segment(a),segment(b)
    return x==y or (x,y) in EDGES or (y,x) in EDGES

