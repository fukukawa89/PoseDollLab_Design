"""Strict geometry/paint/settings comparison of Bambu native support projects.

Object and part names are the stable identities; numeric 3MF IDs, resource
filenames, XML ordering, and UUIDs may change during a Bambu Studio round trip.
All mesh parts (including support blockers) and all build instances are checked.
This verifies preservation, not printability or physical support removability.
"""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import posixpath
import xml.etree.ElementTree as ET
import zipfile

import numpy as np

CORE = '{http://schemas.microsoft.com/3dmanufacturing/core/2015/02}'
PROD = '{http://schemas.microsoft.com/3dmanufacturing/production/2015/06}'
TOLERANCE_MM = 1e-4


def _require(condition, message):
    if not condition:
        raise AssertionError(message)


def _metadata(node):
    result = {}
    for item in node.findall('metadata'):
        key = item.get('key')
        if key is None:
            continue
        _require(key not in result, f'duplicate metadata key: {key}')
        result[key] = item.get('value', '')
    return result


def _overrides(node):
    return {k: v for k, v in _metadata(node).items()
            if 'support' in k.lower() or 'brim' in k.lower()}


def _matrix(value):
    matrix = np.eye(4)
    if value:
        numbers = np.array([float(v) for v in value.split()])
        _require(numbers.size == 12 and np.all(np.isfinite(numbers)),
                 'invalid 3MF transform')
        matrix[:3, :] = numbers.reshape(4, 3).T
    return matrix


def _member(current, value):
    if not value:
        return current
    result = posixpath.normpath(value.lstrip('/') if value.startswith('/')
                               else posixpath.join(posixpath.dirname(current), value))
    _require(not result.startswith('../'), f'component path leaves package: {value}')
    return result


def _read_project(path):
    with zipfile.ZipFile(path) as archive:
        documents = {}
        resources = {}

        def document(member):
            if member not in documents:
                doc = ET.fromstring(archive.read(member))
                _require(doc.get('unit', 'millimeter') == 'millimeter',
                         f'{member}: expected millimeter units')
                documents[member] = doc
                nodes = doc.findall(CORE + 'resources/' + CORE + 'object')
                table = {n.get('id'): n for n in nodes}
                _require(len(table) == len(nodes), f'{member}: duplicate resource ID')
                resources[member] = table
            return documents[member]

        def leaves(member, object_id, matrix, stack=()):
            key = (member, object_id)
            _require(key not in stack, f'cyclic component reference: {key}')
            document(member)
            _require(object_id in resources[member], f'missing component: {key}')
            node = resources[member][object_id]
            mesh = node.find(CORE + 'mesh')
            if mesh is not None:
                v = np.array([[float(n.get(a)) for a in ('x', 'y', 'z')]
                              for n in mesh.findall(CORE + 'vertices/' + CORE + 'vertex')], dtype=np.float64)
                triangles = mesh.findall(CORE + 'triangles/' + CORE + 'triangle')
                f = np.array([[int(n.get(a)) for a in ('v1', 'v2', 'v3')]
                              for n in triangles], dtype=np.int64)
                _require(v.ndim == 2 and v.shape[1] == 3 and len(v) > 0
                         and np.all(np.isfinite(v)), f'{key}: invalid vertices')
                _require(f.ndim == 2 and f.shape[1] == 3 and len(f) > 0
                         and int(f.min()) >= 0 and int(f.max()) < len(v),
                         f'{key}: invalid triangle indices')
                yield object_id, {
                    'world_vertices': v @ matrix[:3, :3].T + matrix[:3, 3],
                    'triangles': f,
                    'paint': tuple(n.get('paint_supports') for n in triangles),
                }
            else:
                components = node.findall(CORE + 'components/' + CORE + 'component')
                _require(components, f'{key}: object has neither mesh nor components')
                for component in components:
                    child = _member(member, component.get(PROD + 'path'))
                    yield from leaves(child, component.get('objectid'),
                                      matrix @ _matrix(component.get('transform')),
                                      stack + (key,))

        root_name = '3D/3dmodel.model'
        root = document(root_name)
        settings = ET.fromstring(archive.read('Metadata/model_settings.config'))
        objects = {}
        ids = {}
        for node in settings.findall('object'):
            name = _metadata(node).get('name')
            _require(name and name not in objects, f'missing/duplicate object name: {name!r}')
            oid = node.get('id')
            _require(oid not in ids, f'duplicate model-settings object ID: {oid}')
            ids[oid] = name
            parts = {}
            part_ids = {}
            for part in node.findall('part'):
                part_name = _metadata(part).get('name')
                _require(part_name and part_name not in parts,
                         f'{name}: missing/duplicate part name: {part_name!r}')
                pid = part.get('id')
                _require(pid not in part_ids, f'{name}: duplicate part ID: {pid}')
                part_ids[pid] = part_name
                parts[part_name] = {'subtype': part.get('subtype', 'normal_part'),
                                    'overrides': _overrides(part)}
            _require(parts, f'{name}: no named parts')
            objects[name] = {'parts': parts, 'part_ids': part_ids,
                             'overrides': _overrides(node), 'instances': []}

        for item in root.findall(CORE + 'build/' + CORE + 'item'):
            oid = item.get('objectid')
            _require(oid in ids, f'build object lacks metadata: {oid}')
            name = ids[oid]
            obj = objects[name]
            meshes = {}
            member = _member(root_name, item.get(PROD + 'path'))
            for pid, data in leaves(member, oid, _matrix(item.get('transform'))):
                _require(pid in obj['part_ids'], f'{name}: mesh part {pid} lacks metadata')
                part_name = obj['part_ids'][pid]
                _require(part_name not in meshes, f'{name}: repeated mesh for part {part_name}')
                meshes[part_name] = data
            _require(set(meshes) == set(obj['parts']), f'{name}: mesh/metadata part sets differ')
            obj['instances'].append({'printable': item.get('printable', '1'), 'meshes': meshes})
        for name, obj in objects.items():
            _require(obj['instances'], f'{name}: no build instances')
            del obj['part_ids']
        return objects


def compare_projects(reference_path, actual_path):
    """Return a PASS summary, or raise AssertionError on any preservation failure.

    Per object/part names and support/brim overrides must match exactly, including
    absence versus presence. Triangle indices and the paint_supports attribute
    for every triangle must match exactly. World-space vertex components may
    differ by at most 0.0001 mm. Reordered IDs and build instances are accepted.
    A support blocker part is checked as strictly as a normal printable part.
    """
    reference_path, actual_path = Path(reference_path), Path(actual_path)
    reference, actual = _read_project(reference_path), _read_project(actual_path)
    _require(set(reference) == set(actual),
             f'object names differ: missing={set(reference)-set(actual)}, extra={set(actual)-set(reference)}')
    summaries = []
    maximum_error = 0.
    vertex_count = triangle_count = instance_count = 0
    subtype_counts = Counter()
    for name, expected in reference.items():
        observed = actual[name]
        _require(expected['overrides'] == observed['overrides'],
                 f'{name}: object support/brim overrides differ: {expected["overrides"]} vs {observed["overrides"]}')
        _require(set(expected['parts']) == set(observed['parts']), f'{name}: part names differ')
        for part_name, part in expected['parts'].items():
            _require(part == observed['parts'][part_name],
                     f'{name}/{part_name}: subtype or part support/brim overrides differ')
            subtype_counts[part['subtype']] += 1
        _require(len(expected['instances']) == len(observed['instances']),
                 f'{name}: build instance count changed')
        remaining = list(observed['instances'])
        object_error = 0.
        for index, wanted_instance in enumerate(expected['instances']):
            matches = []
            for candidate_index, candidate in enumerate(remaining):
                if wanted_instance['printable'] != candidate['printable']:
                    continue
                error = 0.
                valid = True
                for part_name, wanted in wanted_instance['meshes'].items():
                    found = candidate['meshes'][part_name]
                    if (wanted['world_vertices'].shape != found['world_vertices'].shape
                            or not np.array_equal(wanted['triangles'], found['triangles'])
                            or wanted['paint'] != found['paint']):
                        valid = False
                        break
                    error = max(error, float(np.max(np.abs(wanted['world_vertices'] - found['world_vertices']))))
                if valid and error <= TOLERANCE_MM:
                    matches.append((error, candidate_index))
            _require(matches, f'{name}: instance {index} has changed vertices, triangle indices, per-face paint, or printable state')
            error, selected = min(matches)
            remaining.pop(selected)
            object_error = max(object_error, error)
            instance_count += 1
            for mesh in wanted_instance['meshes'].values():
                vertex_count += len(mesh['world_vertices'])
                triangle_count += len(mesh['triangles'])
        maximum_error = max(maximum_error, object_error)
        summaries.append({'object_name': name, 'parts': len(expected['parts']),
                          'instances': len(expected['instances']),
                          'max_world_vertex_error_mm': object_error,
                          'object_support_brim_overrides': expected['overrides']})
    return {
        'status': 'PASS', 'schema': 'POSEDOLL-O22-NATIVE-SUPPORT-PRESERVATION/1',
        'reference_file': reference_path.name, 'actual_file': actual_path.name,
        'reference_sha256': hashlib.sha256(reference_path.read_bytes()).hexdigest(),
        'actual_sha256': hashlib.sha256(actual_path.read_bytes()).hexdigest(),
        'object_count': len(reference), 'part_count': sum(subtype_counts.values()),
        'part_subtypes': dict(subtype_counts), 'build_instances_checked': instance_count,
        'vertices_checked': vertex_count, 'triangle_indices_and_paint_checked': triangle_count,
        'max_world_vertex_error_mm': maximum_error, 'tolerance_mm': TOLERANCE_MM,
        'checks': ['object and part names', 'all part subtypes and build instances',
                   'every world-space vertex', 'exact triangle indices',
                   'exact paint_supports on every triangle',
                   'exact object/part support and brim overrides'],
        'objects': summaries,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('reference'); parser.add_argument('actual')
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    result = compare_projects(args.reference, args.actual)
    text = json.dumps(result, ensure_ascii=False, indent=2) + '\n'
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text, encoding='utf-8')
    print(text)


if __name__ == '__main__':
    main()
