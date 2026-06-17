#!/usr/bin/env python3
"""
FreeCAD Phone Stand Auto-Grader
================================
Grades a student's .FCStd submission against the auto-gradable rubric.
Works by inspecting the XML inside the .FCStd zip archive - no FreeCAD
installation required.

Usage:
    python3 grade_freecad.py <path/to/submission.FCStd>
    python3 grade_freecad.py <folder/of/submissions/>
"""

import sys
import os
import zipfile
import xml.etree.ElementTree as ET
from pathlib import Path
from dataclasses import dataclass, field
from typing import List, Dict, Tuple


@dataclass
class RubricResult:
    section: str
    criterion: str
    max_points: int
    awarded: int
    comment: str = ""


@dataclass
class GradeReport:
    filename: str
    results: List[RubricResult] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)

    @property
    def total(self) -> int:
        return sum(r.awarded for r in self.results)

    @property
    def max_total(self) -> int:
        return sum(r.max_points for r in self.results)


# ----------------------------------------------------------------------
# Helpers to read the FCStd archive
# ----------------------------------------------------------------------

def load_fcstd(path: str) -> ET.Element:
    """Open an FCStd file and return the parsed Document.xml root."""
    with zipfile.ZipFile(path, 'r') as z:
        with z.open('Document.xml') as f:
            tree = ET.parse(f)
            return tree.getroot()


def find_objects_by_type(root: ET.Element, type_substring: str) -> List[ET.Element]:
    """Find all <Object> entries whose type contains the given substring."""
    return [obj for obj in root.iter('Object')
            if type_substring in obj.get('type', '')]


def get_object_data(root: ET.Element, name: str) -> ET.Element:
    """Find the ObjectData entry for a given object name."""
    for obj in root.iter('Object'):
        if obj.get('name') == name and obj.find('Properties') is not None:
            return obj
    return None


def get_property(obj_data: ET.Element, prop_name: str):
    """Get a property element from an ObjectData by name."""
    if obj_data is None:
        return None
    for prop in obj_data.iter('Property'):
        if prop.get('name') == prop_name:
            return prop
    return None


# ----------------------------------------------------------------------
# Rubric checks
# ----------------------------------------------------------------------

def grade_submission(filepath: str) -> GradeReport:
    report = GradeReport(filename=os.path.basename(filepath))

    # ---- 1.1 File opens correctly (5 pts) ----
    try:
        root = load_fcstd(filepath)
        report.results.append(RubricResult(
            "1. Technical", "1.1 File opens correctly", 5, 5,
            "Valid FCStd archive"))
    except Exception as e:
        report.results.append(RubricResult(
            "1. Technical", "1.1 File opens correctly", 5, 0,
            f"Failed to open: {e}"))
        report.errors.append(str(e))
        return report  # Can't grade anything else

    # Gather all the objects we care about
    bodies = find_objects_by_type(root, 'PartDesign::Body')
    sketches = find_objects_by_type(root, 'Sketcher::SketchObject')

    # Common 3D feature types in PartDesign
    feature_types = ['PartDesign::Pad', 'PartDesign::Pocket',
                     'PartDesign::Revolution', 'PartDesign::Groove',
                     'PartDesign::Fillet', 'PartDesign::Chamfer',
                     'PartDesign::Loft', 'PartDesign::Sweep',
                     'Part::Extrusion', 'Part::Revolution']
    features = []
    for ft in feature_types:
        features.extend(find_objects_by_type(root, ft))

    # ---- 1.2 Body container present (5 pts) ----
    if bodies:
        report.results.append(RubricResult(
            "1. Technical", "1.2 PartDesign Body present", 5, 5,
            f"Found {len(bodies)} Body container(s)"))
    else:
        report.results.append(RubricResult(
            "1. Technical", "1.2 PartDesign Body present", 5, 0,
            "No PartDesign::Body found"))

    # ---- 1.3 At least one sketch (5 pts) ----
    if sketches:
        report.results.append(RubricResult(
            "1. Technical", "1.3 Sketch present", 5, 5,
            f"Found {len(sketches)} sketch(es)"))
    else:
        report.results.append(RubricResult(
            "1. Technical", "1.3 Sketch present", 5, 0,
            "No sketches found"))

    # ---- 1.4 Sketch fully constrained (12 pts) ----
    # In the XML, a fully-constrained sketch has all geometry pinned by
    # enough constraints. A reliable heuristic: count Geometry vs Constraints.
    # Line segments need 4 DOF each, arcs 5, circles 3. We approximate by
    # checking the constraint-to-geometry ratio (should be roughly 2.5x+).
    constraint_score = 0
    constraint_comment = "No sketch to evaluate"
    if sketches:
        first_sketch_name = sketches[0].get('name')
        sketch_data = get_object_data(root, first_sketch_name)

        # Count geometry
        geom_count = 0
        constraint_count = 0
        constraint_types = set()

        for elem in sketch_data.iter() if sketch_data is not None else []:
            if elem.tag == 'GeometryList':
                geom_count = int(elem.get('count', 0))
            if elem.tag == 'ConstraintList':
                constraint_count = int(elem.get('count', 0))
            if elem.tag == 'Constrain':
                ctype = elem.get('Type', '')
                if ctype:
                    constraint_types.add(ctype)

        if geom_count > 0:
            ratio = constraint_count / geom_count
            if ratio >= 2.5:
                constraint_score = 12
                constraint_comment = f"Likely fully constrained ({constraint_count} constraints on {geom_count} entities)"
            elif ratio >= 1.8:
                constraint_score = 8
                constraint_comment = f"Mostly constrained ({constraint_count} constraints on {geom_count} entities)"
            elif ratio >= 1.0:
                constraint_score = 4
                constraint_comment = f"Partially constrained ({constraint_count} constraints on {geom_count} entities)"
            else:
                constraint_score = 0
                constraint_comment = f"Under-constrained ({constraint_count} constraints on {geom_count} entities)"

    report.results.append(RubricResult(
        "1. Technical", "1.4 Sketch fully constrained", 12,
        constraint_score, constraint_comment))

    # ---- 1.5 3D feature created (13 pts) ----
    if features:
        feature_names = [f.get('type').split('::')[-1] for f in features]
        report.results.append(RubricResult(
            "1. Technical", "1.5 3D feature created", 13, 13,
            f"Found features: {', '.join(feature_names)}"))
    else:
        report.results.append(RubricResult(
            "1. Technical", "1.5 3D feature created", 13, 0,
            "No 3D solid feature (Pad/Pocket/Revolve/etc.) found"))

    # ---- 1.6 File saves cleanly (5 pts) ----
    # Check for Touched flags - if many objects are touched it suggests
    # the file wasn't recomputed before saving.
    touched = [obj for obj in root.iter('Object') if obj.get('Touched') == '1']
    if len(touched) == 0:
        report.results.append(RubricResult(
            "1. Technical", "1.6 File saved cleanly", 5, 5,
            "All objects up to date"))
    elif len(touched) <= 2:
        report.results.append(RubricResult(
            "1. Technical", "1.6 File saved cleanly", 5, 3,
            f"{len(touched)} object(s) need recompute"))
    else:
        report.results.append(RubricResult(
            "1. Technical", "1.6 File saved cleanly", 5, 0,
            f"{len(touched)} object(s) marked as touched - file not recomputed"))

    # ---- 2.1 Sketch-then-feature workflow (10 pts) ----
    # Check whether any feature references a sketch
    sketch_used_by_feature = False
    if sketches and features:
        sketch_names = {s.get('name') for s in sketches}
        for feat in features:
            feat_data = get_object_data(root, feat.get('name'))
            if feat_data is not None:
                for link in feat_data.iter('Link'):
                    if link.get('value') in sketch_names:
                        sketch_used_by_feature = True
                        break

    if sketch_used_by_feature:
        report.results.append(RubricResult(
            "2. Technique", "2.1 Sketch-then-feature workflow", 10, 10,
            "Sketch is used by a 3D feature"))
    elif sketches and not features:
        report.results.append(RubricResult(
            "2. Technique", "2.1 Sketch-then-feature workflow", 10, 3,
            "Sketch exists but no feature uses it"))
    else:
        report.results.append(RubricResult(
            "2. Technique", "2.1 Sketch-then-feature workflow", 10, 0,
            "No sketch-to-feature relationship found"))

    # ---- 2.2 Appropriate constraint types (10 pts) ----
    # Look for a mix of geometric (Coincident, Horizontal, Vertical, etc.)
    # and dimensional (Distance, DistanceX, Radius, Angle) constraints.
    geometric_types = {'Coincident', 'Horizontal', 'Vertical', 'Parallel',
                       'Perpendicular', 'Tangent', 'Equal', 'Symmetric',
                       'PointOnObject'}
    dimensional_types = {'Distance', 'DistanceX', 'DistanceY', 'Radius',
                         'Diameter', 'Angle'}

    has_geometric = bool(constraint_types & geometric_types)
    has_dimensional = bool(constraint_types & dimensional_types)

    if has_geometric and has_dimensional:
        report.results.append(RubricResult(
            "2. Technique", "2.2 Mix of constraint types", 10, 10,
            f"Used: {', '.join(sorted(constraint_types))}"))
    elif has_geometric or has_dimensional:
        report.results.append(RubricResult(
            "2. Technique", "2.2 Mix of constraint types", 10, 5,
            f"Only one category used: {', '.join(sorted(constraint_types))}"))
    else:
        report.results.append(RubricResult(
            "2. Technique", "2.2 Mix of constraint types", 10, 0,
            "No identifiable constraints"))

    # ---- 2.3 At least 2 different feature types (5 pts) ----
    unique_feature_types = {f.get('type') for f in features}
    if len(unique_feature_types) >= 2:
        report.results.append(RubricResult(
            "2. Technique", "2.3 Multiple feature types", 5, 5,
            f"{len(unique_feature_types)} different feature types"))
    elif len(unique_feature_types) == 1:
        report.results.append(RubricResult(
            "2. Technique", "2.3 Multiple feature types", 5, 2,
            "Only one feature type used"))
    else:
        report.results.append(RubricResult(
            "2. Technique", "2.3 Multiple feature types", 5, 0,
            "No features"))

    # ---- 2.4 Meaningful object names (5 pts) ----
    # Check labels on Body, Sketch, and features.
    default_name_prefixes = ('Sketch', 'Pad', 'Pocket', 'Body',
                             'Revolution', 'Fillet', 'Chamfer')
    objects_to_check = bodies + sketches + features
    renamed_count = 0
    total_checked = 0

    for obj in objects_to_check:
        obj_data = get_object_data(root, obj.get('name'))
        label_prop = get_property(obj_data, 'Label')
        if label_prop is not None:
            label_str = label_prop.find('String')
            if label_str is not None:
                label = label_str.get('value', '')
                total_checked += 1
                # A "meaningful" label is one that doesn't match the
                # default auto-generated pattern (Sketch, Sketch001, Pad, etc.)
                is_default = any(label == p or
                                 (label.startswith(p) and
                                  label[len(p):].isdigit())
                                 for p in default_name_prefixes)
                if not is_default:
                    renamed_count += 1

    if total_checked > 0:
        rename_ratio = renamed_count / total_checked
        if rename_ratio >= 0.5:
            report.results.append(RubricResult(
                "2. Technique", "2.4 Objects renamed meaningfully", 5, 5,
                f"{renamed_count}/{total_checked} objects renamed"))
        elif rename_ratio > 0:
            report.results.append(RubricResult(
                "2. Technique", "2.4 Objects renamed meaningfully", 5, 2,
                f"{renamed_count}/{total_checked} objects renamed"))
        else:
            report.results.append(RubricResult(
                "2. Technique", "2.4 Objects renamed meaningfully", 5, 0,
                "All objects using default names"))
    else:
        report.results.append(RubricResult(
            "2. Technique", "2.4 Objects renamed meaningfully", 5, 0,
            "No objects to evaluate"))

    # ---- Section 3: Design Requirements ----
    # These need real geometry - without FreeCAD installed we estimate
    # from sketch bounding box. For production use, run inside FreeCAD
    # to query actual Shape.BoundBox, Volume, etc.

    # We try to compute the sketch bounding box from the geometry points
    # in Document.xml (basic estimate - real measurements require BREP parsing).
    sketch_bbox = estimate_sketch_bbox(root)

    # ---- 3.1 Overall dimensions within spec (6 pts) ----
    # Spec: bounding box should fit within 150 x 100 x 100 mm
    if sketch_bbox:
        w, h = sketch_bbox
        # Note: this is the sketch profile - depth is unknown without a Pad
        if w <= 150 and h <= 100:
            report.results.append(RubricResult(
                "3. Design", "3.1 Dimensions within spec", 6, 6,
                f"Sketch profile {w:.1f} x {h:.1f} mm fits 150x100 spec"))
        elif w <= 200 and h <= 150:
            report.results.append(RubricResult(
                "3. Design", "3.1 Dimensions within spec", 6, 3,
                f"Sketch profile {w:.1f} x {h:.1f} mm slightly oversized"))
        else:
            report.results.append(RubricResult(
                "3. Design", "3.1 Dimensions within spec", 6, 0,
                f"Sketch profile {w:.1f} x {h:.1f} mm exceeds spec"))
    else:
        report.results.append(RubricResult(
            "3. Design", "3.1 Dimensions within spec", 6, 0,
            "Could not measure - no usable geometry"))

    # ---- 3.2 Phone slot width (6 pts) ----
    # Look for any Distance constraint value between 8 and 15 mm.
    slot_widths = find_distance_constraints(root, 8.0, 15.0)
    if slot_widths:
        report.results.append(RubricResult(
            "3. Design", "3.2 Phone slot width 8-15mm", 6, 6,
            f"Found distance(s) in range: {', '.join(f'{d:.1f}mm' for d in slot_widths)}"))
    else:
        report.results.append(RubricResult(
            "3. Design", "3.2 Phone slot width 8-15mm", 6, 0,
            "No constrained distance in 8-15mm range"))

    # ---- 3.3 Stable base (7 pts) ----
    # Rough proxy: sketch should have a base edge of at least 60mm width.
    if sketch_bbox and sketch_bbox[0] >= 60:
        report.results.append(RubricResult(
            "3. Design", "3.3 Stable base footprint", 7, 7,
            f"Base width {sketch_bbox[0]:.1f}mm - adequate footprint"))
    elif sketch_bbox and sketch_bbox[0] >= 40:
        report.results.append(RubricResult(
            "3. Design", "3.3 Stable base footprint", 7, 4,
            f"Base width {sketch_bbox[0]:.1f}mm - marginal stability"))
    else:
        report.results.append(RubricResult(
            "3. Design", "3.3 Stable base footprint", 7, 0,
            "Base too narrow or unmeasurable"))

    # ---- 3.4 Wall thickness (6 pts) ----
    # Without BREP parsing we check whether any Distance constraint is >= 2mm
    # AND a Pad exists (so there's an actual wall to measure). For a richer
    # check, run inside FreeCAD and query Shape.thickness.
    wall_check_thicknesses = find_distance_constraints(root, 2.0, 1000.0)
    if features and wall_check_thicknesses:
        report.results.append(RubricResult(
            "3. Design", "3.4 Wall thickness >= 2mm", 6, 6,
            "Dimensional constraints suggest adequate thickness"))
    elif wall_check_thicknesses:
        report.results.append(RubricResult(
            "3. Design", "3.4 Wall thickness >= 2mm", 6, 3,
            "Sketch dimensions OK but no 3D feature to verify"))
    else:
        report.results.append(RubricResult(
            "3. Design", "3.4 Wall thickness >= 2mm", 6, 0,
            "Cannot verify minimum thickness"))

    return report


def estimate_sketch_bbox(root: ET.Element) -> Tuple[float, float]:
    """Estimate sketch bounding box from geometry points in Document.xml.

    This parses LineSegment Start/End points to find the bounds. Returns
    (width, height) in mm, or None if no usable data.
    """
    xs, ys = [], []
    for elem in root.iter():
        # FreeCAD stores points as Vector elements with x/y/z attrs
        if elem.tag == 'Vector':
            try:
                x = float(elem.get('x', 'nan'))
                y = float(elem.get('y', 'nan'))
                if x == x and y == y:  # NaN check
                    xs.append(x)
                    ys.append(y)
            except ValueError:
                pass
    if xs and ys:
        return (max(xs) - min(xs), max(ys) - min(ys))
    return None


def find_distance_constraints(root: ET.Element,
                              min_val: float,
                              max_val: float) -> List[float]:
    """Find all dimensional constraints with values in [min_val, max_val]."""
    results = []
    for elem in root.iter('Constrain'):
        ctype = elem.get('Type', '')
        if ctype in ('Distance', 'DistanceX', 'DistanceY',
                     'Radius', 'Diameter'):
            try:
                val = float(elem.get('Value', '0'))
                # Values are stored in mm
                if min_val <= abs(val) <= max_val:
                    results.append(abs(val))
            except ValueError:
                pass
    return results


# ----------------------------------------------------------------------
# Reporting
# ----------------------------------------------------------------------

def print_report(report: GradeReport):
    print("=" * 72)
    print(f"GRADE REPORT: {report.filename}")
    print("=" * 72)

    current_section = None
    section_total = 0
    section_max = 0

    for r in report.results:
        if r.section != current_section:
            if current_section is not None:
                print(f"  Section subtotal: {section_total}/{section_max}")
                print()
            print(f"[{r.section}]")
            current_section = r.section
            section_total = 0
            section_max = 0

        status = "OK" if r.awarded == r.max_points else (
            "PARTIAL" if r.awarded > 0 else "MISS")
        print(f"  {r.criterion}")
        print(f"    {r.awarded}/{r.max_points}  [{status}]  {r.comment}")
        section_total += r.awarded
        section_max += r.max_points

    print(f"  Section subtotal: {section_total}/{section_max}")
    print()
    print("-" * 72)
    print(f"TOTAL: {report.total}/{report.max_total}")

    # Grade band
    pct = (report.total / report.max_total) * 100
    if pct >= 85:
        band = "Excellent"
    elif pct >= 70:
        band = "Good"
    elif pct >= 55:
        band = "Satisfactory"
    elif pct >= 40:
        band = "Developing"
    else:
        band = "Needs resubmission"
    print(f"Grade band: {band} ({pct:.1f}%)")
    print("=" * 72)


def write_csv_summary(reports: List[GradeReport], outpath: str):
    """Write a per-student summary CSV for spreadsheet import."""
    import csv
    if not reports:
        return
    with open(outpath, 'w', newline='') as f:
        writer = csv.writer(f)
        headers = ['Filename'] + [r.criterion for r in reports[0].results] + ['Total']
        writer.writerow(headers)
        for rep in reports:
            row = [rep.filename] + [r.awarded for r in rep.results] + [rep.total]
            writer.writerow(row)


# ----------------------------------------------------------------------
# CLI
# ----------------------------------------------------------------------

def main():
    if len(sys.argv) < 2:
        print("Usage: python3 grade_freecad.py <file_or_folder>")
        sys.exit(1)

    target = Path(sys.argv[1])
    files = []
    if target.is_dir():
        files = sorted(target.glob('*.FCStd'))
    elif target.is_file():
        files = [target]
    else:
        print(f"Not found: {target}")
        sys.exit(1)

    reports = []
    for f in files:
        rep = grade_submission(str(f))
        print_report(rep)
        reports.append(rep)

    if len(reports) > 1:
        out = 'grade_summary.csv'
        write_csv_summary(reports, out)
        print(f"\nClass summary written to {out}")


if __name__ == '__main__':
    main()
