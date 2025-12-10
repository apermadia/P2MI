import math
import random
from typing import List, Tuple

LatLonAlt = Tuple[float, float, float]  # (lat_deg, lon_deg, alt_m)

# ---------------------------------------------------------
# Core functions (same logic as before)
# ---------------------------------------------------------

def latlon_to_local_xy(lat_deg: float, lon_deg: float,
                       lat0_deg: float, lon0_deg: float) -> Tuple[float, float]:
    """Local x (east), y (north) in meters relative to (lat0, lon0)."""
    R_earth = 6371000.0  # m
    lat = math.radians(lat_deg)
    lon = math.radians(lon_deg)
    lat0 = math.radians(lat0_deg)
    lon0 = math.radians(lon0_deg)
    dlat = lat - lat0
    dlon = lon - lon0
    x = dlon * math.cos(lat0) * R_earth
    y = dlat * R_earth
    return x, y


def density_to_level(rho: float,
                     thresholds=(0.05, 0.2, 0.5, 1.5)) -> int:
    """
    Map density [ac/km^2] -> level 1..5.
    Tune thresholds later if you want.
    """
    T1, T2, T3, T4 = thresholds
    if rho < T1:  return 1
    if rho < T2:  return 2
    if rho < T3:  return 3
    if rho < T4:  return 4
    return 5


def local_density_latlon(
    ref: LatLonAlt,
    others: List[LatLonAlt],
    alt_band_m: float = 500.0,
    R_min_m: float = 20.0,   # 20 m
    R_max_m: float = 3000.0,  # 3 km
    thresholds=(0.05, 0.2, 0.5, 1.5),
):
    """Compute local density for one timestep."""
    latA, lonA, altA = ref

    distances = []
    for (lat, lon, alt) in others:
        if abs(alt - altA) <= alt_band_m:
            x, y = latlon_to_local_xy(lat, lon, latA, lonA)
            distances.append(math.hypot(x, y))

    n = len(distances)
    if n == 0:
        R = R_min_m
        rho = 0.0
        level = 1
        return rho, level, R, n

    R_raw = max(distances)
    R = max(R_min_m, min(R_raw, R_max_m))

    area_km2 = math.pi * R * R / 1e6
    rho = n / area_km2
    level = density_to_level(rho, thresholds)
    return rho, level, R, n


# ---------------------------------------------------------
# Simulation of 5 density scenarios
# ---------------------------------------------------------

def offset_deg_from_meters(d_m: float, lat0_deg: float) -> Tuple[float, float]:
    """
    Helper: approximate degree offsets for a given distance in meters.
    Used to place random aircraft around the reference.
    """
    R_earth = 6371000.0
    dlat = d_m / R_earth                 # radians
    dlon = d_m / (R_earth * math.cos(math.radians(lat0_deg)))
    return math.degrees(dlat), math.degrees(dlon)


def random_aircraft_around(ref: LatLonAlt, n: int, spread_m: float) -> List[LatLonAlt]:
    """Generate n aircraft randomly within +/- spread_m of ref in x,y."""
    lat0, lon0, alt0 = ref
    dlat1deg, dlon1deg = offset_deg_from_meters(spread_m, lat0)  # max deg offsets

    result = []
    for _ in range(n):
        # random offset within the square [-spread, +spread] in both directions
        dlat_deg = random.uniform(-dlat1deg, dlat1deg)
        dlon_deg = random.uniform(-dlon1deg, dlon1deg)
        alt = alt0 + random.uniform(-100.0, 100.0)  # small alt variation
        result.append((lat0 + dlat_deg, lon0 + dlon_deg, alt))
    return result


def print_scenario(name: str, ref: LatLonAlt, others: List[LatLonAlt]):
    rho, level, R, n = local_density_latlon(ref, others)
    print(f"{name}:")
    print(f"  n       = {n} aircraft")
    print(f"  R       = {R/1000:.2f} km")
    print(f"  density = {rho:.3f} ac/km^2")
    print(f"  level   = {level}")
    print()


if __name__ == "__main__":
    random.seed(0)

    # Reference aircraft somewhere (lat, lon arbitrary)
    ref = (48.0, 11.0, 1000.0)

    # (label, number of aircraft, spread radius in meters)
    scenarios = [
        ("Very Low density", 1, 8000.0),
        ("Low density",      3, 6000.0),
        ("Medium density",   6, 4000.0),
        ("High density",    10, 2500.0),
        ("Very High density",15, 1500.0),
    ]

    for label, n_ac, spread in scenarios:
        others = random_aircraft_around(ref, n_ac, spread)
        print_scenario(label, ref, others)
