from __future__ import annotations
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
def air_risk(
    lat: float,
    lon: float,
    altitude_m: float,
    *,
    # provisional context inputs (set constants for now)
    in_mode_c_tmz: bool = False,
    in_controlled: bool = False,
    population_class: int = 2,   # 1–2=rural, 3–5=urban (temporary generalization)
) -> Tuple[str, Dict[str, str]]:
    """
    Returns (ARC, details) following your flowchart,
    using Halim/Soetta polygons for the airport/heliport branch,
    and simple flags for Mode-C/TMZ, controlled, and urban/rural.
    """
    HALIM = r"C:\Users\HP\Documents\ITB\Chapter 4\P2MI\Halim ATZ.kml"
    SOETTA = r"C:\Users\HP\Documents\ITB\Chapter 4\P2MI\Soetta ATZ.kml"

    halim_polys  = parse_kml_polygons(HALIM)
    soetta_polys = parse_kml_polygons(SOETTA)
    in_controlled = False

    # --- Step 2: airport/heliport environment overrides ---
    if point_in_any(lon, lat, halim_polys):
        in_controlled = True
        return "ARC-d", {"rule": "OPS in Airport/Heliport env. → Class B/C/D (Halim) → ARC-d"}
    if point_in_any(lon, lat, soetta_polys):
        in_controlled = True
        return "ARC-c", {"rule": "OPS in Airport/Heliport env. → Class A (Soetta) → ARC-c"}

        # --- Step 3: altitude branches (revised to follow flowchart) ---
    FT_TO_M  = 0.3048
    FL600_m  = 60000 * FT_TO_M      # ≈ 18,288 m
    FT500_m  = 500 * FT_TO_M        # ≈ 152.4 m
    a = altitude_m

    # temporary constants (until you load real data later)
    in_mode_c_tmz = False
    population_class = 2  # 1–2 = rural, 3–5 = urban
    is_urban = population_class >= 3

    # > FL600
    if a > FL600_m:
        return "ARC-b", {"rule": "OPS > FL600 → ARC-b"}

    # 500 ft < a < FL600
    if FT500_m < a < FL600_m:
        if in_mode_c_tmz or in_controlled:
            return "ARC-d", {"rule": "500 ft < OPS < FL600 AND (Mode-C/TMZ or Controlled) → ARC-d"}
        else:
            # uncontrolled, urban or rural → ARC-c (generalized)
            return "ARC-c", {"rule": "500 ft < OPS < FL600 in Uncontrolled Airspace → ARC-c"}

    # OPS ≤ 500 ft
    if a <= FT500_m:
        if in_mode_c_tmz or in_controlled or is_urban:
            return "ARC-c", {"rule": "OPS ≤ 500 ft AND (Mode-C/TMZ or Controlled or Urban) → ARC-c"}
        else:
            return "ARC-b", {"rule": "OPS ≤ 500 ft in Uncontrolled Rural Area → ARC-b"}

# ---------- Example usage ----------
if __name__ == "__main__":
    # Example 1: Halim
    print(air_risk(-6.2660, 106.8915, 80.0))
    # Example 2: Soetta
    print(air_risk(-6.130062, 106.649063, 90.0))
    # Example 3: Rural
    print(air_risk(-6.3478, 106.5612, 1100.0))
