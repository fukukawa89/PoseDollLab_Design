"""Inspect actual Bambu G-code and export compact paths for the O22 support viewer.

No slicing or printer access. Source is a native 3MF, ZipFile, plain G-code,
or a readable text stream. Stats cover positive-E XY motion within Bambu
CHANGE_LAYER blocks; startup/purge/end moves are counted separately.
"""
from __future__ import annotations
import argparse
from array import array
from collections import Counter
import hashlib
import io
import json
import math
from pathlib import Path
import re
import struct
import zipfile

CLASSES = ["model", "support", "interface", "transition", "brim"]
ROLE_MAP = {"Support": 1, "Support interface": 2, "Support transition": 3, "Brim": 4, "Skirt": 4}
WORD = re.compile(r"([A-Za-z])\s*([-+]?(?:\d*\.\d+|\d+\.?\d*)(?:[eE][-+]?\d+)?)")
LAYER = re.compile(r"^;\s*(?:CHANGE_LAYER|LAYER_CHANGE)\s*$")


def _read_source(source, plate):
    if isinstance(source, zipfile.ZipFile):
        member = f"Metadata/plate_{plate}.gcode"
        return source.read(member).decode("utf-8-sig"), member
    if hasattr(source, "read"):
        t = source.read()
        return t.decode("utf-8-sig") if isinstance(t, bytes) else t, "stream"
    path = Path(source)
    if path.suffix.lower() == ".3mf" or zipfile.is_zipfile(path):
        with zipfile.ZipFile(path) as z:
            return _read_source(z, plate)[0], path.name
    return path.read_text(encoding="utf-8-sig"), path.name


def _sweep(a, b, clockwise):
    d = (a - b if clockwise else b - a) % (2 * math.pi)
    return d if d > 1e-10 else 2 * math.pi


def _arc_points(start, end, words, clockwise, arc_absolute, scale, tolerance, max_segment):
    """XY I/J or signed R arcs; return sampled endpoints excluding start."""
    x, y, z = start
    ex, ey, ez = end
    if "I" in words or "J" in words:
        cx = words.get("I", x / scale if arc_absolute else 0) * scale
        cy = words.get("J", y / scale if arc_absolute else 0) * scale
        if not arc_absolute:
            cx += x
            cy += y
    elif "R" in words:
        r = abs(words["R"] * scale)
        dx, dy = ex - x, ey - y
        chord = math.hypot(dx, dy)
        if chord < 1e-9 or chord > 2 * r + 1e-5:
            raise ValueError("invalid radius arc")
        h = math.sqrt(max(0, r * r - chord * chord / 4))
        centres = [((x + ex) / 2 + sign * -dy / chord * h,
                    (y + ey) / 2 + sign * dx / chord * h) for sign in (1, -1)]
        want_major = words["R"] < 0
        cx, cy = next((c for c in centres if (_sweep(math.atan2(y-c[1], x-c[0]), math.atan2(ey-c[1], ex-c[0]), clockwise) > math.pi + 1e-7) == want_major), centres[0])
    else:
        raise ValueError("arc missing I/J or R")
    radius = math.hypot(x - cx, y - cy)
    if radius < 1e-9:
        raise ValueError("zero radius arc")
    end_radius = math.hypot(ex - cx, ey - cy)
    if abs(end_radius - radius) > max(0.03, radius * .002):
        raise ValueError("arc endpoint radius mismatch")
    a = math.atan2(y - cy, x - cx)
    sweep = _sweep(a, math.atan2(ey - cy, ex - cx), clockwise)
    angle_limit = 2 * math.acos(max(-1, min(1, 1 - tolerance / radius)))
    n = max(1, math.ceil(sweep / max(angle_limit, 1e-5)), math.ceil(radius * sweep / max_segment))
    if n > 100000:
        raise ValueError("arc needs excessive subdivision")
    sign = -1 if clockwise else 1
    fractions = {i / n for i in range(1, n)}
    # Include cardinal extrema so bed/bounds checks do not miss an arc bulge.
    for cardinal in (0., math.pi/2, math.pi, 3*math.pi/2):
        travel = (a-cardinal if clockwise else cardinal-a) % (2*math.pi)
        if 1e-10 < travel < sweep-1e-10: fractions.add(travel/sweep)
    points = [(cx + radius * math.cos(a + sign * sweep * f), cy + radius * math.sin(a + sign * sweep * f), z + (ez-z) * f) for f in sorted(fractions)]
    points.append(end)
    return points, math.hypot(radius * sweep, ez - z)


def _parse(source, plate=1, collect=False, arc_tolerance_mm=.03, max_arc_segment_mm=1.):
    text, source_name = _read_source(source, plate)
    pos = [0., 0., 0.]
    e = 0.
    absolute = True
    relative_e = False
    arc_absolute = False
    scale = 1.
    plane = 17
    feature = "Custom"
    line_width = None
    layer = -1
    nominal_z = None
    layer_height = None
    active = False
    ended = False
    paths = array("f")  # x0 y0 z0 x1 y1 z1 layer class
    stats = [{"id": n, "segments": 0, "moves": 0, "filament_mm": 0., "path_mm": 0., "_layers": set(), "_widths": set(), "_min": [math.inf]*3, "_max": [-math.inf]*3} for n in CLASSES]
    layers = []
    unsupported = Counter()
    warnings = []
    feature_counts = Counter()
    outside_print_moves = 0
    outside_print_filament = 0.
    all_min = [math.inf]*3
    all_max = [-math.inf]*3
    violations = []
    total_violations = 0
    header = {}
    arc_moves = 0
    in_config = False
    for line_no, line in enumerate(text.splitlines(), 1):
        s = line.strip()
        if s == "; CONFIG_BLOCK_START": in_config = True
        elif s == "; CONFIG_BLOCK_END": in_config = False
        if in_config: continue
        if LAYER.match(s):
            layer += 1
            active = True
            ended = False
            nominal_z = None
            layer_height = None
            layers.append({"index": layer, "z_mm": None, "height_mm": None})
            continue
        if s.startswith("; Z_HEIGHT:") or s.startswith(";Z:"):
            if layer >= 0:
                nominal_z = float(s.split(":", 1)[1]); layers[layer]["z_mm"] = nominal_z
            continue
        if s.startswith("; LAYER_HEIGHT:") or s.startswith(";HEIGHT:"):
            if layer >= 0:
                layer_height = float(s.split(":", 1)[1]); layers[layer]["height_mm"] = layer_height
            continue
        if s.startswith("; LINE_WIDTH:") or s.startswith(";WIDTH:"):
            try: line_width = float(s.split(":", 1)[1])
            except ValueError: line_width = None
            continue
        if s.startswith("; FEATURE:") or s.startswith(";TYPE:"):
            feature = s.split(":", 1)[1].strip()
            if feature == "Custom" and active:
                # Bambu switches to Custom before machine_end_gcode. Later
                # layer markers may resume printing, e.g. user custom G-code.
                active = False
            elif layer >= 0 and not ended: active = True
            continue
        if s == "; EXECUTABLE_BLOCK_END": active = False; ended = True
        if s.startswith("; model printing time:"): header["estimated_time"] = s[2:]
        for label, key in (("; filament_density:", "filament_density_g_cm3"), ("; filament_diameter:", "filament_diameter_mm")):
            if s.startswith(label):
                try: header[key] = float(s.split(":", 1)[1].split(",")[0])
                except ValueError: pass
        if s.startswith("; total filament length [mm]"):
            try: header["total_filament_length_mm"] = float(s.split(":", 1)[1].split(",")[0])
            except ValueError: pass
        if s.startswith("; total filament weight [g]"):
            try: header["total_filament_weight_g"] = float(s.split(":", 1)[1].split(",")[0])
            except ValueError: pass
        code = s.split(";", 1)[0]
        code = re.sub(r"\([^)]*\)", "", code).strip()
        if not code: continue
        tokens = WORD.findall(code)
        if not tokens: continue
        if tokens[0][0].upper() == "N": tokens = tokens[1:]
        if not tokens: continue
        letter, number = tokens[0]
        command = letter.upper() + number
        args = {k.upper(): float(v) for k,v in tokens[1:]}
        if command in ("G90", "G090"): absolute = True; continue
        if command in ("G91", "G091"): absolute = False; continue
        if command == "G90.1": arc_absolute = True; continue
        if command == "G91.1": arc_absolute = False; continue
        if command == "M82": relative_e = False; continue
        if command == "M83": relative_e = True; continue
        if command == "G20": scale = 25.4; continue
        if command == "G21": scale = 1.; continue
        if command in ("G17", "G18", "G19"): plane = int(command[1:]); continue
        if command == "G92":
            for k, axis in enumerate("XYZ"):
                if axis in args: pos[k] = args[axis] * scale
            if "E" in args: e = args["E"] * scale
            continue
        if command not in ("G0", "G00", "G1", "G01", "G2", "G02", "G3", "G03"):
            continue
        target = [args.get(axis, pos[k] / scale) * scale if absolute else pos[k] + args.get(axis, 0.) * scale for k,axis in enumerate("XYZ")]
        delta_e = args.get("E", 0.) * scale if relative_e else args.get("E", e / scale) * scale - e
        if "E" in args: e = e + delta_e if relative_e else args["E"] * scale
        is_arc = command in ("G2", "G02", "G3", "G03")
        xy_motion = math.hypot(target[0]-pos[0], target[1]-pos[1]) > 1e-8 or is_arc
        if delta_e > 1e-9 and xy_motion:
            if active and layer >= 0 and feature != "Custom":
                role = ROLE_MAP.get(feature, 0)
                entry = stats[role]
                if is_arc:
                    if plane != 17:
                        unsupported[f"G{plane} extrusion arc"] += 1
                        raise ValueError(f"line {line_no}: non-XY extrusion arc is unsupported")
                    try:
                        points, path_length = _arc_points(pos, target, args, command in ("G2", "G02"), arc_absolute, scale, arc_tolerance_mm, max_arc_segment_mm)
                    except ValueError as exc:
                        raise ValueError(f"line {line_no}: {exc}") from exc
                    arc_moves += 1
                else:
                    points = [target]
                    path_length = math.dist(pos, target)
                entry["moves"] += 1
                entry["filament_mm"] += delta_e
                entry["path_mm"] += path_length
                entry["_layers"].add(layer)
                if line_width is not None: entry["_widths"].add(line_width)
                feature_counts[feature] += 1
                last = pos
                for point in points:
                    for p in (last, point):
                        for k in range(3):
                            entry["_min"][k] = min(entry["_min"][k], p[k]); entry["_max"][k] = max(entry["_max"][k], p[k])
                            all_min[k] = min(all_min[k], p[k]); all_max[k] = max(all_max[k], p[k])
                    if min(last[0], point[0], last[1], point[1], last[2], point[2]) < -0.025 or max(last[0], point[0], last[1], point[1]) > 180.025 or max(last[2], point[2]) > 180.025:
                        total_violations += 1
                        if len(violations) < 20: violations.append({"line":line_no,"class":CLASSES[role],"from":list(last),"to":list(point)})
                    entry["segments"] += 1
                    if collect: paths.extend((*last,*point,float(layer),float(role)))
                    last = point
                if layers[layer]["z_mm"] is None: layers[layer]["z_mm"] = target[2]
            else:
                outside_print_moves += 1
                outside_print_filament += delta_e
        pos = target
    for entry in stats:
        entry["layers"] = len(entry.pop("_layers"))
        widths = entry.pop("_widths")
        entry["line_width_range_mm"] = [min(widths),max(widths)] if widths else None
        lo, hi = entry.pop("_min"), entry.pop("_max")
        entry["bounds_mm"] = {"min":lo,"max":hi} if entry["moves"] else None
        entry["filament_mm"] = round(entry["filament_mm"], 5)
        entry["path_mm"] = round(entry["path_mm"], 5)
        if "filament_diameter_mm" in header:
            volume = entry["filament_mm"] * math.pi * (header["filament_diameter_mm"]/2)**2 / 1000
            entry["filament_volume_cm3"] = round(volume, 5)
            if "filament_density_g_cm3" in header: entry["estimated_mass_g"] = round(volume * header["filament_density_g_cm3"], 4)
    if layer < 0: raise ValueError("No Bambu CHANGE_LAYER or LAYER_CHANGE markers found; refusing to label startup moves as print paths")
    result = {
        "schema":"POSEDOLL-O22-GCODE-PREVIEW/1", "source":source_name,
        "gcode_sha256":hashlib.sha256(text.encode("utf-8")).hexdigest(),
        "description":"Bambu actual extrusion paths redrawn; not a Bambu Studio screenshot. Display lines are centerlines, not extrusion widths.",
        "bed_mm":[180,180,180], "header":header,"classes":stats,"layers":layers,
        "segment_count":sum(v["segments"] for v in stats),"extrusion_moves":sum(v["moves"] for v in stats),
        "arc_moves":arc_moves,"arc_chord_tolerance_mm":arc_tolerance_mm,
        "bounds_scope":"extrusion centerlines, arc extrema included; not deposited bead width",
        "arc_max_segment_mm":max_arc_segment_mm,"bounds_mm":{"min":all_min,"max":all_max} if sum(v["moves"] for v in stats) else None,
        "out_of_bed_segment_count":total_violations,"out_of_bed_examples":violations,
        "excluded_custom_extrusion_moves":outside_print_moves,"excluded_custom_filament_mm":round(outside_print_filament,5),
        "features":dict(feature_counts),"warnings":warnings,"unsupported_commands":dict(unsupported),
    }
    return result, paths


def extract_paths(source, plate=1, **kwargs):
    """Return (report, flat array('f')) for numerical geometry audits.

    Each 8-float record is x0,y0,z0,x1,y1,z1,layer_index,class_id.
    This is BEFORE the display-only uint16 quantization. Arc samples include
    cardinal extrema; max chord error is report['arc_chord_tolerance_mm'].
    For support-volume exclusion, include class IDs 1, 2 and 3 and account
    for extrusion half-width plus the arc chord tolerance, not just centerlines.
    """
    return _parse(source, plate=plate, collect=True, **kwargs)


def inspect_gcode(source, plate=1, **kwargs):
    """Return JSON-serializable measured path stats; accepts Path or ZipFile."""
    return _parse(source, plate=plate, collect=False, **kwargs)[0]


def export_preview(source, output_json, plate=1, **kwargs):
    """Write JSON and 16-byte/segment uint16 binary. Return the JSON object.

    Binary record: x0,y0,z0,x1,y1,z1,layer,class (little-endian uint16).
    Position = origin_mm[axis] + q * quantum_mm. Counts and bounds in JSON
    are computed before display quantization. G-code remains authoritative.
    """
    report, paths = _parse(source, plate=plate, collect=True, **kwargs)
    dst = Path(output_json)
    dst.parent.mkdir(parents=True, exist_ok=True)
    binary = dst.with_suffix(".bin")
    bounds = report["bounds_mm"] or {"min":[0,0,0],"max":[0,0,0]}
    origin = [math.floor(x) for x in bounds["min"]]
    largest = max(bounds["max"][k]-origin[k] for k in range(3))
    quantum = max(.01, largest/65534)
    if len(report["layers"]) > 65535: raise ValueError("Too many layers for preview format")
    record = struct.Struct("<8H")
    with binary.open("wb") as stream:
        batch = bytearray()
        for i in range(0,len(paths),8):
            nums = [max(0,min(65535,round((paths[i+k]-origin[k%3])/quantum))) for k in range(6)]
            nums += [round(paths[i+6]),round(paths[i+7])]
            batch.extend(record.pack(*nums))
            if len(batch) >= 1024*1024: stream.write(batch);batch.clear()
        if batch: stream.write(batch)
    report["binary"] = {"file":binary.name,"record_bytes":16,"dtype":"8xuint16_le","fields":["x0","y0","z0","x1","y1","z1","layer","class"],"origin_mm":origin,"quantum_mm":quantum,"bytes":binary.stat().st_size,"sha256":hashlib.sha256(binary.read_bytes()).hexdigest()}
    dst.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    return report


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("source");p.add_argument("--output",required=True);p.add_argument("--plate",type=int,default=1);p.add_argument("--stats-only",action="store_true")
    a=p.parse_args()
    if a.stats_only:
        report=inspect_gcode(a.source,a.plate);Path(a.output).write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    else:report=export_preview(a.source,a.output,a.plate)
    print(json.dumps({k:report[k] for k in ["segment_count","extrusion_moves","arc_moves","bounds_mm","out_of_bed_segment_count"]},ensure_ascii=False))

if __name__ == "__main__": main()
