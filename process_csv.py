import pandas as pd
from local_density_sim import local_density_latlon

# ---------------------------------------------
# 1. LOAD + CLEAN CSV
# ---------------------------------------------
def load_csv(path):
    """
    Reads CSV where each row looks like:
    timestamp,aircraftid,lat,lon,alt
    (all in one combined column)
    """
    raw = pd.read_csv(path, header=0, names=["combo"])

    # split into separate columns
    df = raw["combo"].str.split(",", expand=True)
    df.columns = ["timestamp", "aircraft_id", "lat", "lon", "alt"]

    # convert numeric columns
    df["timestamp"] = df["timestamp"].astype(float)
    df["lat"] = df["lat"].astype(float)
    df["lon"] = df["lon"].astype(float)
    df["alt"] = df["alt"].astype(float)

    return df


# ---------------------------------------------
# 2. PROCESS EACH TIMESTAMP
# ---------------------------------------------
def compute_density_over_time(df):
    """
    For each timestamp:
       For each aircraft:
           use it as REF
           use all others as NEIGHBORS
           compute density
    """
    results = []

    for t in sorted(df["timestamp"].unique()):
        df_t = df[df["timestamp"] == t]

        # loop through each aircraft at this timestamp
        for _, ref_row in df_t.iterrows():
            ref_id = ref_row["aircraft_id"]
            ref = (ref_row["lat"], ref_row["lon"], ref_row["alt"])

            # all other aircraft
            others_df = df_t[df_t["aircraft_id"] != ref_id]
            others = [(row["lat"], row["lon"], row["alt"]) 
                      for _, row in others_df.iterrows()]

            # density calculation (from local_density.py)
            rho, level, R, n = local_density_latlon(ref, others)

            results.append({
                "timestamp": t,
                "ref_id": ref_id,
                "rho": rho,
                "level": level,
                "R_m": R,
                "n_neighbors": n,
            })

    return pd.DataFrame(results)


# ---------------------------------------------
# 3. MAIN EXECUTION
# ---------------------------------------------
if __name__ == "__main__":
    df = load_csv(" your_file.csv ")

    density_df = compute_density_over_time(df)

    print(density_df)
    density_df.to_csv("density_output.csv", index=False)
