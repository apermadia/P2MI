import math
import random
from typing import List, Tuple

LatLonAlt = Tuple[float, float, float]

# ---------- density logic (from before, slightly compacted) ----------

def density_to_level(rho: float,
                     thresholds: Tuple[float, float, float, float]) -> int:
    T1, T2, T3, T4 = thresholds
    if rho < T1:  return 1
    if rho < T2:  return 2
    if rho < T3:  return 3
    if rho < T4:  return 4
    return 5


def latlon_to_local_xy(lat_deg: float, lon_deg: float,
                       lat0_deg: float, lon0_deg: float) -> Tuple[float, float]:
    R_earth = 6371000.0  # m
    lat  = math.radians(lat_deg)
    lon  = math.radians(lon_deg)
    lat0 = math.radians(lat0_deg)
    lon0 = math.radians(lon0_deg)
    dlat = lat - lat0
    dlon = lon - lon0
    x = dlon * math.cos(lat0) * R_earth  # east
    y = dlat * R_earth                    # north
    return x, y


def compute_local_density_latlon(
    ref: LatLonAlt,
    others: List[LatLonAlt],
    alt_band_m: float = 500.0,
    R_min_m: float = 1000.0,     # 1 km
    R_max_m: float = 10000.0,    # 10 km
    thresholds: Tuple[float, float, float, float] = (0.001, 0.005, 0.01, 0.05),
):
    latA, lonA, altA = ref

    distances = []
    n = 0

    for (lat, lon, alt) in others:
        if abs(alt - altA) <= alt_band_m:
            x, y = latlon_to_local_xy(lat, lon, latA, lonA)
            d = math.hypot(x, y)
            distances.append(d)
            n += 1

    if n == 0:
        R = R_min_m
        rho = 0.0
        level = 1
        return rho, level, R, n

    R_raw = max(distances)
    R = max(R_min_m, min(R_raw, R_max_m))

    area_m2 = math.pi * R * R
    area_km2 = area_m2 / 1e6

    rho = n / area_km2
    level = density_to_level(rho, thresholds)
    return rho, level, R, n

# ---------- simple simulation of aircraft positions ----------

def simulate_step(ref: LatLonAlt,
                  others: List[LatLonAlt]) -> Tuple[LatLonAlt, List[LatLonAlt]]:
    """Move reference and other aircraft a little bit each step."""
    latA, lonA, altA = ref

    # Reference: fly east at ~150 m per step (~0.0013 deg lon at this latitude)
    lonA += 0.001  # tweak this speed as you like

    new_others: List[LatLonAlt] = []
    for (lat, lon, alt) in others:
        # small random walk around (drift in lat/lon)
        lat  += random.uniform(-0.0003, 0.0003)
        lon  += random.uniform(-0.0003, 0.0003)
        alt  += random.uniform(-20.0, 20.0)
        new_others.append((lat, lon, alt))

    return (latA, lonA, altA), new_others


def init_scene(n_others: int = 5) -> Tuple[LatLonAlt, List[LatLonAlt]]:
    """Create initial positions around some base lat/lon."""
    # Base position for reference aircraft (pick anything)
    lat0 = 48.0
    lon0 = 11.0
    alt0 = 1000.0

    ref = (lat0, lon0, alt0)

    others: List[LatLonAlt] = []
    for _ in range(n_others):
        # random offset within about +/- 0.03 deg (~3 km)
        dlat = random.uniform(-0.03, 0.03)
        dlon = random.uniform(-0.03, 0.03)
        alt  = alt0 + random.uniform(-200.0, 200.0)
        others.append((lat0 + dlat, lon0 + dlon, alt))

    return ref, others


if __name__ == "__main__":
    random.seed(0)

    ref, others = init_scene(n_others=8)

    for step in range(20):  # 20 time steps
        rho, level, R, n = compute_local_density_latlon(ref, others)

        print(f"step {step:02d}: n={n:2d}, R={R/1000:4.1f} km, "
              f"rho={rho:6.3f} ac/km^2, level={level}")

        # advance to next time step
        ref, others = simulate_step(ref, others)
