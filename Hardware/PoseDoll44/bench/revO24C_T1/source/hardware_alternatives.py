"""Verify the user's 0.5 mm M2 and 1.5 mm M6 washers with unchanged T1 prints.

This is an alternate assembled configuration, not a rewrite of the baseline CAD.
S1 already includes the pictured D2.5 shoulder and its two mandatory .5 washers.
This audit only substitutes the remaining six M2 and the two M6 washers.
"""
from kit import *
from validate import overlaps
import time


def alternative_build():
    k = build()
    p = {r['id']: r for r in k.parts}
    changed = []

    def replace(id, solid):
        p[id]['s'] = solid
        changed.append(id)

    def shift(id, vector):
        replace(id, p[id]['s'].translate(vector))

    # M2 liner washer's OUTER face remains on the existing tab at |Y|=12.2.
    # Thickening from .3 to .5 moves the screw/head inward by .2, not the tab.
    for sign in [-1, 1]:
        for xx in [-8.5, 8.5]:
            tail = str(sign) + '_' + str(xx)
            replace('Wliner_w_' + tail, washer([xx, sign*11.7, 0], sign*Y, 5, 2.2, .5))
            shift('Wliner_screw_' + tail, [0, -sign*.2, 0])
        replace('Wlever_w' + str(sign), washer([sign*6, 0, -27], sign*X, 5, 2.2, .5))
    shift('Wlever_screw', [.2, 0, 0])
    shift('Wlever_n', [-.2, 0, 0])

    # Fixed R04 pressure face is at Y=-6.6. Seat the thinner negative washer
    # there: the rotor moves -.1, and the floating R03 plate closes by .2.
    # R geometry is clocked about Y, so the same axial shifts apply directly.
    for r in k.parts:
        if r['station'] == 'R' and r['frame'] == 'rotor':
            shift(r['id'], [0, -.1, 0])
    for sign in [-1, 1]:
        replace('Rfriction_' + str(sign), washer([0, sign*5-.1, 0], sign*Y, 18, 6.4, 1.5))
    for id in ['R03', 'Rpreload_w1_-5', 'Rpreload_w1_5', 'Rpreload_n-5', 'Rpreload_n5']:
        shift(id, [0, -.2, 0])
    return k, changed


def protrusion(p, screw_id, nut_id, axis, pitch):
    # Measure the actual alternate screw tip and nut exit along the screw axis.
    tip = (mesh(p[screw_id]['s']).vertices @ axis).max()
    exit = (mesh(p[nut_id]['s']).vertices @ axis).max()
    value = float(tip-exit)
    return dict(screw=screw_id, nut=nut_id, protrusion_mm=value,
                minimum_two_threads_mm=2*pitch, passed=value >= 2*pitch-1e-6)


def audit(k):
    static = []; motion = {}; pose_counts = {}
    for station in ['R', 'W']:
        rows = [p for p in k.parts if p['station'] == station]
        for i, p in enumerate(rows):
            for r in rows[i+1:]:
                if overlaps(p['s'], r['s']):
                    vol = float((p['s'] ^ r['s']).volume())
                    if vol > .02:
                        static.append(dict(pair=[p['id'], r['id']], volume_mm3=vol))
        poses = [(q, 0) for q in range(-85, 81)] if station == 'R' else sorted(set(
            [(q, d) for q in range(-65, 71, 5) for d in range(-20, 31, 5)] +
            [(q, d) for q in range(-65, 71) for d in [-20, 30]] +
            [(q, d) for q in [-65, 70] for d in range(-20, 31)]))
        pose_counts[station] = len(poses)
        fixed = [p for p in rows if p['frame'] == 'fixed']
        moving = [p for p in rows if p['frame'] != 'fixed']
        for q, d in poses:
            F = frames(station, q, d)
            for p in moving:
                s = moved(p['s'], F[p['frame']])
                for r in fixed:
                    if not overlaps(s, r['s']): continue
                    vol = float((s ^ r['s']).volume())
                    if vol > .02:
                        key = p['id'] + ' / ' + r['id']
                        if vol > motion.get(key, {}).get('volume_mm3', 0):
                            motion[key] = dict(q=q, dev=d, volume_mm3=vol)
        print('ALTERNATE', station, len(poses), 'motion pairs', len(motion), flush=True)

    # Same additional .20 mm/side wrist preload keep-out check as base T1.
    closing = [p for p in k.parts if p['id'] in ['W06', 'W07'] or
               p['id'].startswith(('Wliner_screw', 'Wliner_w', 'Wliner_n'))]
    moving = [p for p in k.parts if p['station'] == 'W' and p['frame'] == 'ball']
    keepout = {}
    for q in [-65, -45, 0, 45, 70]:
        for d in [-20, 0, 30]:
            F = frames('W', q, d)['ball']
            for p in closing:
                sign = 1 if np.array(p['s'].bounding_box()).reshape(2, 3).mean(0)[1] > 0 else -1
                s = p['s'].translate([0, -sign*.2, 0])
                for r in moving:
                    t = moved(r['s'], F)
                    if overlaps(s, t):
                        vol = float((s ^ t).volume())
                        if vol > .02:
                            key = p['id'] + ' / ' + r['id']
                            keepout[key] = max(keepout.get(key, 0), vol)
    return dict(static_collisions=static, motion_collisions=motion,
                pose_counts=pose_counts, total_poses=sum(pose_counts.values()),
                wrist_additional_closing_mm_per_side=.2,
                preload_keepout_poses=15, preload_keepout_collisions=keepout)


def main():
    started = time.time()
    k, changed = alternative_build()
    p = {r['id']: r for r in k.parts}
    baseline = build()
    # Compare local printable meshes after removing rigid placement: no reprint.
    shape_checks = []
    original = {r['id']: r for r in baseline.parts}
    for r in k.parts:
        if not r['printable']: continue
        v = mesh(r['s']).vertices; b = mesh(original[r['id']]['s']).vertices
        local_error = float(np.max(np.abs((v-v.mean(0))-(b-b.mean(0)))))
        # Manifold mesh vertices are float32; rigid translations can round them
        # by sub-micrometre amounts. This tolerance is 0.01 micrometre.
        shape_checks.append(dict(part=r['id'], max_local_vertex_delta_mm=local_error,
                                 tolerance_mm=1e-5, passed=local_error < 1e-5))
    stacks = []
    for sign in [-1, 1]:
        for xx in [-8.5, 8.5]:
            tail = str(sign)+'_'+str(xx)
            stacks.append(protrusion(p, 'Wliner_screw_'+tail, 'Wliner_n_'+tail, sign*Y, .4))
    stacks.append(protrusion(p, 'Wlever_screw', 'Wlever_n', -X, .4))
    for z in [-5, 5]:
        stacks.append(protrusion(p, 'Rpreload_'+str(z), 'Rpreload_n'+str(z), Y, .5))
    result = audit(k)
    old_area = math.pi*(3**2-2.3**2)/4
    new_area = math.pi*(2.5**2-2.3**2)/4
    result.update(
        baseline_geometry_sha256=sha(OUT/'assembly_meshes.npz'),
        verification_source_sha256=sha(Path(__file__)),
        alternate_washers_mm=dict(W2=[5, 2.2, .5], FR6=[18, 6.4, 1.5]),
        changed_assembly_placements_or_hardware=changed,
        unchanged_print_shapes=shape_checks, fastener_stacks=stacks,
        r_rotor_axial_shift_mm=-.1, r_floating_plate_axial_shift_mm=-.2,
        pictured_screw=dict(approved_as_direct_substitute_for_original_T1=False,
            adapted_revision='O24C-T1-S1', supported_by='stock_guide_checks.json',
            source='User-supplied 肩轴螺钉.png; labelled nominal dimensions, not measured product.',
            shoulder_d_mm=2.5, shoulder_length_mm=6, thread='M2x0.4',
            thread_length_mm=4, head_d_mm=4.8, head_height_mm=2.4, hex_key_mm=2,
            baseline_slot_width_mm=3.44, baseline_diametral_clearance_mm=.44,
            substituted_diametral_clearance_mm=.94,
            screw_clearance_hole_d_mm=2.3,
            baseline_seat_radial_width_mm=.35, substituted_seat_radial_width_mm=.1,
            baseline_ideal_annular_area_mm2=old_area,
            substituted_ideal_annular_area_mm2=new_area,
            area_ratio=new_area/old_area,
            note='Historical comparison against original D3 T1 only. S1 replaces both ball halves, liners and cups, and captures a steel washer directly backed by a plain nut. Not a direct substitution in original prints.'),
        scope='Nominal alternate hardware/rigid placement, baseline printed geometry. Not physical torque, wear, material strength or supplier tolerance qualification.',
        elapsed_s=time.time()-started)
    result['passed'] = (not result['static_collisions'] and not result['motion_collisions']
                        and not result['preload_keepout_collisions']
                        and all(r['passed'] for r in shape_checks+stacks))
    put(OUT/'verification/hardware_alternatives.json', result)
    print(json.dumps(dict(passed=result['passed'], static=result['static_collisions'],
          motion=result['motion_collisions'], keepout=result['preload_keepout_collisions'],
          protrusions=[r['protrusion_mm'] for r in stacks],
          printed_shapes_unchanged=all(r['passed'] for r in shape_checks),
          seconds=result['elapsed_s'])), flush=True)
    if not result['passed']: raise SystemExit(1)


if __name__ == '__main__': main()
