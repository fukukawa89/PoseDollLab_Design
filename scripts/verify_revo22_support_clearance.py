"""Check sliced support sweeps against CAD-derived O22 precision clearances.

Read-only: no slicing, printer access, or model edits. A CLEAR result applies
only to the declared, conservatively inset clearance cores. It does not prove
that every cavity is open or that a real PLA support will release easily.
"""
from __future__ import annotations
import argparse
import copy
import hashlib
import json
import re
import zipfile
from pathlib import Path
import numpy as np
from o22_support_gcode import extract_paths

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_VOLUMES = ROOT / 'Hardware/PoseDoll44/bench/revO22/a1mini_supports/design/all_protected_volumes.json'


def segment_box(a, b, lower, upper):
    """Vectorized closed segment / axis-aligned box interval, including points."""
    delta = b - a
    lower = np.broadcast_to(np.asarray(lower), a.shape)
    upper = np.broadcast_to(np.asarray(upper), a.shape)
    enter = np.zeros(len(a)); leave = np.ones(len(a)); valid = np.ones(len(a), dtype=bool)
    for axis in range(3):
        parallel = np.abs(delta[:, axis]) < 1e-12
        valid &= ~parallel | ((a[:, axis] >= lower[:, axis]) & (a[:, axis] <= upper[:, axis]))
        denominator = np.where(parallel, 1., delta[:, axis])
        u = (lower[:, axis] - a[:, axis]) / denominator
        v = (upper[:, axis] - a[:, axis]) / denominator
        enter = np.maximum(enter, np.where(parallel, -np.inf, np.minimum(u, v)))
        leave = np.minimum(leave, np.where(parallel, np.inf, np.maximum(u, v)))
    return valid & (enter <= leave), enter, leave


def segment_cylinder(a, b, radius, zmin, zmax):
    """Finite cylinder aligned to local Z; intersect radial and axial intervals."""
    delta = b - a
    radius = np.broadcast_to(np.asarray(radius), (len(a),))
    zmin = np.broadcast_to(np.asarray(zmin), (len(a),)); zmax = np.broadcast_to(np.asarray(zmax), (len(a),))
    qa = np.sum(delta[:, :2] ** 2, axis=1)
    qb = 2 * np.sum(a[:, :2] * delta[:, :2], axis=1)
    qc = np.sum(a[:, :2] ** 2, axis=1) - radius ** 2
    parallel = qa < 1e-20
    discr = qb * qb - 4 * qa * qc
    valid = np.where(parallel, qc <= 1e-12, discr >= -1e-12)
    root = np.sqrt(np.maximum(discr, 0.)); denom = np.where(parallel, 1., 2 * qa)
    enter = np.maximum(0., np.where(parallel, -np.inf, (-qb - root) / denom))
    leave = np.minimum(1., np.where(parallel, np.inf, (-qb + root) / denom))
    zp = np.abs(delta[:, 2]) < 1e-12
    valid &= ~zp | ((a[:, 2] >= zmin) & (a[:, 2] <= zmax))
    zd = np.where(zp, 1., delta[:, 2]); u = (zmin - a[:, 2]) / zd; v = (zmax - a[:, 2]) / zd
    enter = np.maximum(enter, np.where(zp, -np.inf, np.minimum(u, v)))
    leave = np.minimum(leave, np.where(zp, np.inf, np.maximum(u, v)))
    return valid & (enter <= leave), enter, leave


def _hash(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def _transformed_bounds(volume, matrix):
    if volume['shape'] == 'box':
        low, high = np.array(volume['min_mm']), np.array(volume['max_mm'])
    else:
        radius = volume['radius_mm']; low = np.array([-radius, -radius, volume['z_mm'][0]]); high = np.array([radius, radius, volume['z_mm'][1]])
    points = np.array([[x, y, z] for x in (low[0], high[0]) for y in (low[1], high[1]) for z in (low[2], high[2])])
    points = points @ matrix[:3, :3].T + matrix[:3, 3]
    return points.min(0), points.max(0)


def select_objects(document, plate_id, placement=None):
    if placement is None:
        return [copy.deepcopy(x) for x in document['objects'] if x['plate'] == plate_id]
    entries = {x['object_name']: x for x in document['objects']}
    by_part = {x['part']: x for x in document['objects']}
    objects = []
    for item in placement['items']:
        old = entries.get(item.get('strategy_original_object_name')) or by_part.get(item['part'])
        if old is None: continue
        row = copy.deepcopy(old); row.update(plate=plate_id, number=item['number'], object_name=item['object_name'])
        matrix = np.eye(4); matrix[:3, :3] = item['rotation_matrix']; matrix[:3, 3] = item['translation_mm']
        for volume in row['volumes']:
            volume['local_to_plate_matrix'] = (matrix @ np.array(volume['local_to_source_print_matrix'])).tolist()
        objects.append(row)
    return objects


def declared_role_widths(source, plate=1, include_brim=False):
    """Read emitted LINE_WIDTH annotations only where selected roles move with E.

    Width ranges are process declarations, not a physical filament measurement.
    Using the widest declared support/brim width for every audited segment is
    deliberately conservative; model-only variable line widths are excluded.
    """
    source = Path(source)
    if zipfile.is_zipfile(source):
        with zipfile.ZipFile(source) as archive:
            text = archive.read(f'Metadata/plate_{plate}.gcode').decode('utf-8-sig')
    else:
        text = source.read_text(encoding='utf-8-sig')
    allowed = {'Support', 'Support interface', 'Support transition'}
    if include_brim: allowed |= {'Brim', 'Skirt'}
    feature = 'Custom'; width = None; active = False; config = False; ranges = {}
    for line in text.splitlines():
        line = line.strip()
        if line == '; CONFIG_BLOCK_START': config = True
        elif line == '; CONFIG_BLOCK_END': config = False
        if config: continue
        if line in ('; CHANGE_LAYER', '; LAYER_CHANGE'): active = True
        if line == '; EXECUTABLE_BLOCK_END': active = False
        if line.startswith(('; FEATURE:', ';TYPE:')): feature = line.split(':', 1)[1].strip()
        if line.startswith(('; LINE_WIDTH:', ';WIDTH:')):
            width = float(line.split(':', 1)[1])
        if active and feature in allowed and width is not None and re.match(r'^G[0123](?:\s|$)', line) and re.search(r'\bE[-+.0-9]', line):
            old = ranges.setdefault(feature, [width, width]); old[0] = min(old[0], width); old[1] = max(old[1], width)
    return ranges


def verify(source, plate_id, volumes_path=DEFAULT_VOLUMES, *, plate=1, placement_path=None,
           line_width_mm=.42, fallback_layer_height_mm=.20, include_brim=False, max_examples=6):
    document = json.loads(Path(volumes_path).read_text(encoding='utf-8-sig'))
    placement = json.loads(Path(placement_path).read_text(encoding='utf-8-sig')) if placement_path else None
    objects = select_objects(document, plate_id, placement)
    width_ranges = declared_role_widths(source, plate, include_brim)
    requested_minimum_width = line_width_mm
    line_width_mm = max([line_width_mm, *[bounds[1] for bounds in width_ranges.values()]])
    measured, raw = extract_paths(source, plate=plate, arc_tolerance_mm=.02, max_arc_segment_mm=1.)
    data = np.frombuffer(raw, dtype=np.float32).reshape(-1, 8)
    roles = (1, 2, 3, 4) if include_brim else (1, 2, 3)
    indices = np.flatnonzero(np.isin(data[:, 7], roles)); selected = data[indices].astype(np.float64)
    all_heights = np.array([x.get('height_mm') or fallback_layer_height_mm for x in measured['layers']])
    heights = all_heights[selected[:, 6].astype(int)] if len(selected) else np.empty(0)
    if np.any(heights <= 0): raise ValueError('non-positive layer height')
    # G-code Z is deposited layer top. Represent the bead by its mid-height
    # line, then expand the clearance by a conservative envelope containing
    # its XY disk and vertical half-height. Arc chord error adds .02 mm.
    start = selected[:, :3].copy(); end = selected[:, 3:6].copy()
    start[:, 2] -= heights / 2; end[:, 2] -= heights / 2
    radius = line_width_mm / 2; chord = measured['arc_chord_tolerance_mm']
    segment_low = np.minimum(start, end) - np.c_[np.full(len(start), radius + chord), np.full(len(start), radius + chord), heights / 2 + chord]
    segment_high = np.maximum(start, end) + np.c_[np.full(len(start), radius + chord), np.full(len(start), radius + chord), heights / 2 + chord]
    definite_ids = set(); envelope_ids = set(); findings = []; checked = 0
    for obj in objects:
        for volume in obj['volumes']:
            checked += 1; matrix = np.array(volume['local_to_plate_matrix'], dtype=float)
            if matrix.shape != (4, 4) or not np.allclose(matrix[:3, :3].T @ matrix[:3, :3], np.eye(3), atol=1e-6):
                raise ValueError('feature matrix must be a rigid transform: ' + volume['feature'])
            low, high = _transformed_bounds(volume, matrix)
            chosen = np.flatnonzero(np.all(segment_high >= low, axis=1) & np.all(segment_low <= high, axis=1))
            if not len(chosen): continue
            inv = np.linalg.inv(matrix); a = start[chosen] @ inv[:3, :3].T + inv[:3, 3]; b = end[chosen] @ inv[:3, :3].T + inv[:3, 3]
            if volume['shape'] == 'box':
                definite, _, _ = segment_box(a, b, volume['min_mm'], volume['max_mm'])
                xy_scale = np.linalg.norm(inv[:3, :2], axis=1)
                padding = radius * xy_scale[None, :] + heights[chosen, None] / 2 * np.abs(inv[:3, 2])[None, :] + chord
                hit, enter, leave = segment_box(a, b, np.array(volume['min_mm']) - padding, np.array(volume['max_mm']) + padding)
            elif volume['shape'] == 'cylinder_z':
                definite, _, _ = segment_cylinder(a, b, volume['radius_mm'], *volume['z_mm'])
                padding = np.hypot(radius, heights[chosen] / 2) + chord
                hit, enter, leave = segment_cylinder(a, b, volume['radius_mm'] + padding, volume['z_mm'][0] - padding, volume['z_mm'][1] + padding)
            else: raise ValueError('unknown clearance shape: ' + volume['shape'])
            if not hit.any(): continue
            hit_indices = chosen[hit]; center_indices = chosen[definite]
            envelope_ids.update(int(indices[j]) for j in hit_indices); definite_ids.update(int(indices[j]) for j in center_indices)
            examples = []
            for relative in np.flatnonzero(hit)[:max_examples]:
                j = chosen[relative]; t = float(np.clip((enter[relative] + leave[relative]) / 2, 0, 1))
                point = start[j] + t * (end[j] - start[j])
                examples.append({'parser_segment_index': int(indices[j]), 'layer_index': int(selected[j, 6]), 'class_id': int(selected[j, 7]),
                                 'layer_height_mm': float(heights[j]), 'point_in_conservative_overlap_plate_mm': point.tolist(),
                                 'gcode_start_mm': selected[j, :3].tolist(), 'gcode_end_mm': selected[j, 3:6].tolist(),
                                 'bead_midline_enters_core': bool(definite[relative])})
            findings.append({'object_name': obj['object_name'], 'part': obj['part'], 'feature': volume['feature'], 'shape': volume['shape'],
                             'bead_midline_core_segment_count': int(definite.sum()), 'conservative_bead_envelope_segment_count': int(hit.sum()),
                             'class_ids': sorted(set(int(x) for x in selected[hit_indices, 7])), 'layer_min': int(selected[hit_indices, 6].min()), 'layer_max': int(selected[hit_indices, 6].max()), 'examples': examples})
    status = 'NO_PROTECTED_FEATURES_DECLARED' if not checked else 'INTRUSION_REVIEW_REQUIRED' if findings else 'CLEAR_FOR_DECLARED_CORES'
    return {'schema': 'POSEDOLL-O22-SUPPORT-CLEARANCE-CHECK/1', 'status': status, 'plate_id': plate_id, 'source': str(source),
            'source_sha256': _hash(source), 'protected_volumes': str(volumes_path), 'protected_volumes_sha256': _hash(volumes_path),
            'placement_manifest': str(placement_path) if placement_path else None, 'placement_manifest_sha256': _hash(placement_path) if placement_path else None,
            'checked_objects': len(objects), 'checked_feature_volumes': checked, 'support_path_segments': len(selected),
            'roles_checked': list(roles), 'line_width_mm': line_width_mm, 'requested_minimum_line_width_mm': requested_minimum_width,
            'gcode_declared_role_line_width_ranges_mm': width_ranges, 'line_width_bound': 'Maximum of requested bound and all declared support/brim widths, conservatively applied to every checked segment.', 'layer_heights_from_gcode': True,
            'fallback_layer_height_mm': fallback_layer_height_mm, 'arc_chord_tolerance_mm': chord,
            'bead_midline_core_segment_count': len(definite_ids), 'conservative_bead_envelope_segment_count': len(envelope_ids),
            'finding_count': len(findings), 'findings': findings,
            'scope': 'Finite segment intersections with oriented CAD clearance cores; checks all path segments, including between endpoints. Bead envelopes include XY half-width, downward layer thickness, and arc chord uncertainty. Conservative-only hits require review; midline hits are stronger evidence of support within the core.',
            'limitations': document.get('limitations', []) + ['Declared features are partial and inset; no full-part cavity or removal-path proof.', 'Filament swelling, actual extrusion widths differing from the supplied bound, adhesion, and physical breakaway forces are not measured.']}


def self_test():
    a = np.array([[-2.,0,0],[0.,0,-2],[2.,0,0],[-2.,2,0],[0.,0,0],[0.,0,2]])
    b = np.array([[2.,0,0],[0.,0,2],[3.,0,0],[2.,2,0],[0.,0,0],[0.,0,3]])
    want = [True,True,False,False,True,False]
    assert segment_box(a,b,[-1,-1,-1],[1,1,1])[0].tolist() == want
    assert segment_cylinder(a,b,1.,-1.,1.)[0].tolist() == want
    # Near outside XY bead, outside cap, and parallel inside-axis cases.
    assert segment_cylinder(np.array([[1.15,0,-.5],[0,0,1.15]]),np.array([[1.15,0,.5],[.5,0,1.15]]),1.25,-1.25,1.25)[0].all()
    assert not segment_cylinder(np.array([[1.15,0,-.5],[0,0,1.15]]),np.array([[1.15,0,.5],[.5,0,1.15]]),1.,-1.,1.)[0].any()
    angle=.71; rotation=np.array([[np.cos(angle),-np.sin(angle),0],[np.sin(angle),np.cos(angle),0],[0,0,1.]])
    origin=np.array([19.,24.,31.]); aa=(a@rotation.T+origin-origin)@rotation;bb=(b@rotation.T+origin-origin)@rotation
    assert segment_box(aa,bb,[-1,-1,-1],[1,1,1])[0].tolist()==want
    print('PASS: finite-box/cylinder intervals, parallel/tangent/point/cap cases, endpoint-outside crossings, rigid transform')


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source', nargs='?');parser.add_argument('--plate-id');parser.add_argument('--plate',type=int,default=1)
    parser.add_argument('--volumes',default=str(DEFAULT_VOLUMES));parser.add_argument('--placement-manifest')
    parser.add_argument('--output');parser.add_argument('--line-width',type=float,default=.42);parser.add_argument('--layer-height',type=float,default=.20)
    parser.add_argument('--include-brim',action='store_true');parser.add_argument('--self-test',action='store_true')
    args=parser.parse_args()
    if args.self_test: self_test();return
    if not args.source or not args.plate_id or not args.output:parser.error('source, --plate-id and --output are required')
    if args.line_width<=0 or args.layer_height<=0:parser.error('width and height must be positive')
    report=verify(args.source,args.plate_id,args.volumes,plate=args.plate,placement_path=args.placement_manifest,line_width_mm=args.line_width,
                  fallback_layer_height_mm=args.layer_height,include_brim=args.include_brim)
    output=Path(args.output);output.parent.mkdir(parents=True,exist_ok=True);output.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({k:report[k] for k in ['status','plate_id','checked_objects','checked_feature_volumes','support_path_segments','bead_midline_core_segment_count','conservative_bead_envelope_segment_count','finding_count']},ensure_ascii=False))

if __name__=='__main__':main()
