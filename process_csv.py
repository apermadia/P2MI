import pandas as pd
from local_density_sim import local_density_latlon  # or comment this out if the function is in the same file

# ---------------------------------------------------------
# 1. LOAD & SPLIT CSV (your exact format)
# ---------------------------------------------------------
def load_csv(path: str) -> pd.DataFrame:
    """
    Tries to handle both:
    A) file already split into 5 columns (timestamp, aircraftid, lat, lon, alt/altitude)
    B) file stored as ONE column with commas inside each line.
    """

    # First: read normally, let pandas try to split by commas
    raw = pd.read_csv(path, header=None)

    # CASE 1: we already have 5 or more columns -> just clean & rename
    if raw.shape[1] >= 5:
        # if the first row looks like a header, drop it
        first_row = raw.iloc[0].astype(str).tolist()
        if "timestamp" in first_row[0].lower():
            raw = raw.iloc[1:].reset_index(drop=True)

        # take first 5 columns as timestamp, id, lat, lon, alt
        df = raw.iloc[:, 0:5].copy()
        df.columns = ["timestamp", "aircraft_id", "lat", "lon", "alt"]

    # CASE 2: only 1 column -> need to split the string ourselves
    elif raw.shape[1] == 1:
        s = raw.iloc[:, 0].astype(str)

        # if first row is a header line, drop it
        if s.iloc[0].lower().startswith("timestamp"):
            s = s.iloc[1:]

        df = s.str.split(",", expand=True)

        if df.shape[1] < 5:
            raise ValueError(
                f"Expected at least 5 comma-separated fields, found {df.shape[1]}.\n"
                f"Example line: {s.iloc[0]!r}"
            )

        df = df.iloc[:, 0:5]
        df.columns = ["timestamp", "aircraft_id", "lat", "lon", "alt"]

    else:
        raise ValueError(f"Unexpected number of columns in raw CSV: {raw.shape[1]}")

    # Convert numeric columns
    df["timestamp"] = df["timestamp"].astype(float)
    df["lat"] = df["lat"].astype(float)
    df["lon"] = df["lon"].astype(float)
    df["alt"] = df["alt"].astype(float)

    return df

def compute_density_all_aircraft(df: pd.DataFrame):
    """
    For each timestamp and each aircraft:
      - use that aircraft as reference
      - all others at same time are neighbors
    Returns one big table with density per aircraft per timestep.
    """
    results = []

    for t in sorted(df["timestamp"].unique()):
        df_t = df[df["timestamp"] == t]

        # loop over each aircraft at this time
        for _, ref_row in df_t.iterrows():
            ref_id = ref_row["aircraft_id"]
            ref = (ref_row["lat"], ref_row["lon"], ref_row["alt"])

            others_df = df_t[df_t["aircraft_id"] != ref_id]
            others = [
                (row["lat"], row["lon"], row["alt"])
                for _, row in others_df.iterrows()
            ]

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

# ---------------------------------------------------------
# 2. SPLIT BY ODD/EVEN ROWS → 2 AIRCRAFT
# ---------------------------------------------------------
def split_two_aircraft(df: pd.DataFrame):
    """
    Assumes rows alternate:
      row0 -> aircraft 1
      row1 -> aircraft 2
      row2 -> aircraft 1
      row3 -> aircraft 2
      ...
    """
    ac1 = df.iloc[::2].reset_index(drop=True)   # even index rows: 0,2,4,...
    ac2 = df.iloc[1::2].reset_index(drop=True)  # odd index rows: 1,3,5,...
    return ac1, ac2

# ---------------------------------------------------------
# 3. DENSITY FOR EACH AIRCRAFT OVER TIME
# ---------------------------------------------------------
def compute_density_two_ac(ac1: pd.DataFrame, ac2: pd.DataFrame):
    """
    For each timestep i:
      - ac1[i] is reference 1, ac2[i] is its only neighbour
      - ac2[i] is reference 2, ac1[i] is its only neighbour
    """
    assert len(ac1) == len(ac2), "Both aircraft must have same number of timesteps"

    results_1 = []
    results_2 = []

    for i in range(len(ac1)):
        t = ac1.loc[i, "timestamp"]  # they should be the same

        # ---------- Aircraft 1 as reference ----------
        ref1 = (ac1.loc[i, "lat"], ac1.loc[i, "lon"], ac1.loc[i, "alt"])
        others1 = [(ac2.loc[i, "lat"], ac2.loc[i, "lon"], ac2.loc[i, "alt"])]
        rho1, level1, R1, n1 = local_density_latlon(ref1, others1)

        results_1.append({
            "timestamp": t,
            "ref_id": ac1.loc[i, "aircraft_id"],
            "rho": rho1,
            "level": level1,
            "R_m": R1,
            "n_neighbors": n1,
        })

        # ---------- Aircraft 2 as reference ----------
        ref2 = (ac2.loc[i, "lat"], ac2.loc[i, "lon"], ac2.loc[i, "alt"])
        others2 = [(ac1.loc[i, "lat"], ac1.loc[i, "lon"], ac1.loc[i, "alt"])]
        rho2, level2, R2, n2 = local_density_latlon(ref2, others2)

        results_2.append({
            "timestamp": t,
            "ref_id": ac2.loc[i, "aircraft_id"],
            "rho": rho2,
            "level": level2,
            "R_m": R2,
            "n_neighbors": n2,
        })

    df1 = pd.DataFrame(results_1)
    df2 = pd.DataFrame(results_2)
    return df1, df2

# ---------------------------------------------------------
# 4. MAIN
# ---------------------------------------------------------
if __name__ == "__main__":
    # 1) load full log (any number of aircraft)
    df = load_csv("logs/tes1.csv")   # path as before

    # 2) compute density for all aircraft
    density_df = compute_density_all_aircraft(df)

    # 3) save to Excel: one sheet per aircraft
    with pd.ExcelWriter("density_per_aircraft.xlsx") as writer:
        for ref_id, group in density_df.groupby("ref_id"):
            sheet_name = str(ref_id)[:31]  # Excel sheet name max 31 chars
            group.to_excel(writer, sheet_name=sheet_name, index=False)

    print("Done. Saved density_per_aircraft.xlsx")

