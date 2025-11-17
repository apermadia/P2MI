# from _future_ import annotations
from typing import List, Tuple, Dict
import xml.etree.ElementTree as ET

# ---------- KML utilities ----------


def parse_kml_polygons(kml_path: str) -> List[List[Tuple[float, float]]]:
    # Define the namespace used in your file
    ns = {"kml": "http://www.opengis.net/kml/2.2"}

    # Parse and get root
    tree = ET.parse(kml_path)
    root = tree.getroot()

    # Find all Polygon elements with namespace
    polygons = root.findall(".//kml:Polygon", ns)

    out: List[List[Tuple[float, float]]] = []

    for poly in polygons:
        # Find coordinates inside the polygon using correct namespace
        coords_el = poly.find(
            ".//kml:outerBoundaryIs/kml:LinearRing/kml:coordinates", ns)
        if coords_el is None or not coords_el.text or not coords_el.text.strip():
            continue

        ring = []
        for triplet in coords_el.text.strip().split():
            parts = triplet.split(",")
            if len(parts) >= 2:
                lon, lat = float(parts[0]), float(parts[1])
                ring.append((lon, lat))

        if len(ring) >= 3:
            out.append(ring)

    return out


'''
def parse_kml_polygons(kml_path: str) -> List[List[Tuple[float, float]]]:
    root = ET.parse(kml_path).getroot()
    polygons = root.findall(".//{*}Polygon")
    out: List[List[Tuple[float, float]]] = []
    for poly in polygons:
        coords_el = poly.find(
            ".//{}outerBoundaryIs//{}LinearRing//{*}coordinates")
        if coords_el is None or not (coords_el.text and coords_el.text.strip()):
            continue
        ring = []
        for triplet in coords_el.text.replace("\n", " ").split():
            parts = triplet.split(",")
            if len(parts) >= 2:
                lon, lat = float(parts[0]), float(parts[1])
                ring.append((lon, lat))
        if len(ring) >= 3:
            out.append(ring)
    return out
'''


def point_in_polygon(lon: float, lat: float, poly: List[Tuple[float, float]]) -> bool:
    inside = False
    n = len(poly)
    for i in range(n):
        x1, y1 = poly[i]
        x2, y2 = poly[(i + 1) % n]
        if ((y1 > lat) != (y2 > lat)) and (lon < (x2 - x1) * (lat - y1) / ((y2 - y1) or 1e-15) + x1):
            inside = not inside
    return inside


def point_in_any(lon: float, lat: float, polygons: List[List[Tuple[float, float]]]) -> bool:
    return any(point_in_polygon(lon, lat, p) for p in polygons)


# ---------- ARC classification logic ----------
def air_risk(lat: float, lon: float, altitude_m: float, grc) -> Tuple[str, Dict[str, str]]:
    """
    Main callable function.
    Input:
        - lat, lon, altitude_m
    Output:
        - ARC classification string ("ARC-b", "ARC-c", etc.)
        - reasoning dictionary
    """

    # Set your KML paths here once
    HALIM = r"C:\Users\bevan\OneDrive - Institut Teknologi Bandung\S2-1\PDP\XPC\Halim ATZ.kml"
    SOETTA = r"C:\Users\bevan\OneDrive - Institut Teknologi Bandung\S2-1\PDP\XPC\Soetta ATZ.kml"

    halim_polys = parse_kml_polygons(HALIM)
    soetta_polys = parse_kml_polygons(SOETTA)
    in_controlled = False
    # Step 2: location

    # --- Step 3: altitude branches (revised to follow flowchart) ---
    FT_TO_M = 0.3048
    FL600_m = 60000 * FT_TO_M      # ≈ 18,288 m
    FT500_m = 500 * FT_TO_M        # ≈ 152.4 m
    a = altitude_m

    # temporary constants (until you load real data later)

    # population_class = 2  # 1–2 = rural, 3–5 = urban

    is_urban = grc >= 6
    if point_in_any(lon, lat, halim_polys):
        in_controlled = True
        arc_label = "ARC-d"
        return in_controlled, arc_label, 3, {"rule": "Inside Halim (treated as Class C) → ARC-d"}
    elif point_in_any(lon, lat, soetta_polys):
        in_controlled = True
        arc_label = "ARC-c"
        return in_controlled, arc_label, 2, {"rule": "Inside Soetta (Class A) → ARC-c"}
    elif a > FL600_m:
        arc_label = "ARC-b"
        in_controlled = False
        return in_controlled, arc_label, 1, {"rule": "OPS > FL600 → ARC-b"}
    # 500 ft < a < FL600
    elif FT500_m < a < FL600_m:
        if in_controlled:
            arc_label = "ARC-d"
            return in_controlled, arc_label, 3, {"rule": "500 ft < OPS < FL600 AND Controlled → ARC-d"}
        else:
            # uncontrolled, urban or rural → ARC-c (generalized)
            arc_label = "ARC-c"
            return in_controlled, arc_label, 2, {"rule": "500 ft < OPS < FL600 in Uncontrolled Airspace → ARC-c"}
    # OPS ≤ 500 ft
    elif a <= FT500_m:
        if in_controlled or is_urban:
            arc_label = "ARC-c"
            return in_controlled, arc_label, 2, {"rule": "OPS ≤ 500 ft AND Controlled or Urban → ARC-c"}
        else:
            arc_label = "ARC-b"
            return in_controlled, arc_label, 1, {"rule": "OPS ≤ 500 ft in Uncontrolled Rural Area → ARC-b"}
