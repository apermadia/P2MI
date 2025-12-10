import math
from typing import List, Tuple

LatLonAlt = Tuple[float, float, float]  # (lat_deg, lon_deg, alt_m)


# ---------- core functions ----------

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
    You can tune thresholds later.
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
    R_min_m: float = 1000.0,   # 1 km
    R_max_m: float = 10000.0,  # 10 km
    thresholds=(0.05, 0.2, 0.5, 1.5),
):
    """Returns (rho, level, R, n) for one timestep."""
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


# ---------- demo scenarios ----------

def print_scenario(name: str, ref: LatLonAlt, others: List[LatLonAlt]):
    rho, level, R, n = local_density_latlon(ref, others)
    print(f"{name}:")
    print(f"  n       = {n} aircraft")
    print(f"  R       = {R/1000:.2f} km")
    print(f"  density = {rho:.3f} ac/km^2")
    print(f"  level   = {level}")
    print()


if __name__ == "__main__":
    # Reference aircraft
    ref = (48.0, 11.0, 1000.0)  # (lat, lon, alt)

    # 1) Low density: few aircraft, spread out
    low_others = [
        (48.03, 11.05, 1000.0),
        (47.97, 10.95, 1050.0),
    ]

    # 2) Medium density: more aircraft, closer
    med_others = [
        (48.01, 11.01, 1000.0),
        (47.99, 11.02, 990.0),
        (48.02, 10.99, 1010.0),
        (47.98, 11.01, 980.0),
        (48.01, 10.98, 1020.0),
    ]

    # 3) High density: many aircraft, very close
    high_others = [
        (48.0005, 11.0003, 1000.0),
        (48.0003, 11.0004, 995.0),
        (47.9998, 11.0002, 1005.0),
        (48.0002, 10.9999, 1002.0),
        (47.9999, 11.0001, 998.0),
        (48.0001, 11.0005, 1003.0),
        (48.0004, 11.0001, 997.0),
        (48.0002, 11.0003, 1001.0),
        (47.9997, 11.0000, 1004.0),
        (48.0000, 10.9998, 996.0),
    ]

    print_scenario("Low density", ref, low_others)
    print_scenario("Medium density", ref, med_others)
    print_scenario("High density", ref, high_others)
