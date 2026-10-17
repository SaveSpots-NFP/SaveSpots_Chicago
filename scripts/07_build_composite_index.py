"""
Build the five-layer composite vulnerability index at census tract level.

Layers (equal-weighted 0.20 each, disclosed as an analyst choice per the
CDC/ATSDR SVI convention - same justification the reference paper uses):
  1. Poverty rate (ACS S1701) - higher = more vulnerable
  2. Uninsurance rate (ACS S2701) - higher = more vulnerable
  3. CDC/ATSDR SVI overall percentile (RPL_THEMES) - higher = more vulnerable
  4. Measured distance to nearest naloxone/harm-reduction supply - higher = more vulnerable
  5. Transit connectivity, CTA stops within 0.5mi of tract centroid, INVERTED
     - fewer stops = more vulnerable

Deliberate departure from the reference paper: no modeled-mortality layer.
Chicago has real measured mortality (script 04), which is used separately as
a VALIDATION target (script 05), not folded into the index itself - folding a
weaker modeled signal in when a stronger measured one exists elsewhere would
be a step backward, and using mortality in both the index AND as what the
index is tested against would be circular.

Sensitivity analysis (non-negotiable per the research contract): two
re-weighted variants are run and the tier-flip rate is reported regardless of
whether it passes a stability threshold.

Run: python scripts/07_build_composite_index.py
(Run after scripts 01, 05, 06)
"""
import sys
from pathlib import Path

import geopandas as gpd
import jenkspy
import numpy as np
import pandas as pd
from scipy.spatial import cKDTree

REPO_ROOT = Path(__file__).resolve().parent.parent
CLEAN_DIR = REPO_ROOT / "data" / "clean"

TRACTS_PATH = CLEAN_DIR / "cook_county_tracts.gpkg"
ACCESS_PATH = CLEAN_DIR / "tract_access_vs_mortality.csv"  # has pop_weighted_avg_dist_m per tract
ACS_PATH = CLEAN_DIR / "acs_tract_poverty_uninsurance.csv"
SVI_PATH = CLEAN_DIR / "svi_2022_tract.csv"
STOPS_PATH = CLEAN_DIR / "cta_stops.csv"

OUT_PATH = CLEAN_DIR / "composite_vulnerability_index_tract.csv"

PROJECTED_CRS = "EPSG:26971"
HALF_MILE_M = 804.672
WEIGHTS = {"poverty": 0.20, "uninsured": 0.20, "svi": 0.20, "access_dist": 0.20, "transit_inv": 0.20}


def minmax(series: pd.Series) -> pd.Series:
    lo, hi = series.min(), series.max()
    if hi == lo:
        return series * 0
    return (series - lo) / (hi - lo)


def compute_transit_connectivity(tracts: gpd.GeoDataFrame, stops: pd.DataFrame) -> pd.Series:
    tracts_proj = tracts.to_crs(PROJECTED_CRS)
    centroids = tracts_proj.geometry.centroid
    stops_gdf = gpd.GeoDataFrame(
        stops, geometry=gpd.points_from_xy(stops["stop_lon"], stops["stop_lat"]), crs="EPSG:4326"
    ).to_crs(PROJECTED_CRS)
    stop_coords = np.array([(g.x, g.y) for g in stops_gdf.geometry])
    tree = cKDTree(stop_coords)
    centroid_coords = np.array([(g.x, g.y) for g in centroids])
    counts = tree.query_ball_point(centroid_coords, r=HALF_MILE_M, return_length=True)
    return pd.Series(counts, index=tracts["GEOID"].values, name="stops_within_half_mi")


def build_index(acs, svi, access, transit, mortality_df, weights: dict) -> pd.DataFrame:
    df = acs[["GEOID", "poverty_pct", "uninsured_pct"]].merge(
        svi[["GEOID", "RPL_THEMES"]], on="GEOID", how="left"
    )
    df = df.merge(access[["tract_GEOID", "pop_weighted_avg_dist_m", "tract_population"]],
                   left_on="GEOID", right_on="tract_GEOID", how="left")
    df = df.merge(transit.rename("stops_within_half_mi"), left_on="GEOID", right_index=True, how="left")

    df["n_poverty"] = minmax(df["poverty_pct"])
    df["n_uninsured"] = minmax(df["uninsured_pct"])
    df["n_svi"] = minmax(df["RPL_THEMES"])
    df["n_access_dist"] = minmax(df["pop_weighted_avg_dist_m"])
    # transit: MORE stops = LESS vulnerable, so invert after normalizing
    df["n_transit_inv"] = 1 - minmax(df["stops_within_half_mi"])

    layer_cols = {
        "poverty": "n_poverty",
        "uninsured": "n_uninsured",
        "svi": "n_svi",
        "access_dist": "n_access_dist",
        "transit_inv": "n_transit_inv",
    }

    # Weighted mean over non-null layers (rescale weights if some are missing,
    # same handling the reference paper uses for partial coverage)
    def weighted_row_mean(row):
        present = {k: row[v] for k, v in layer_cols.items() if pd.notna(row[v])}
        if not present:
            return np.nan
        w = {k: weights[k] for k in present}
        total_w = sum(w.values())
        return sum(present[k] * w[k] for k in present) / total_w

    df["composite_score"] = df.apply(weighted_row_mean, axis=1)
    return df


def main():
    print("Loading inputs...")
    tracts = gpd.read_file(TRACTS_PATH)
    acs = pd.read_csv(ACS_PATH, dtype={"GEOID": str})
    svi = pd.read_csv(SVI_PATH, dtype={"GEOID": str})
    access = pd.read_csv(ACCESS_PATH, dtype={"tract_GEOID": str})
    stops = pd.read_csv(STOPS_PATH)

    print("Computing transit connectivity (CTA stops within 0.5mi of tract centroid)...")
    transit = compute_transit_connectivity(tracts, stops)

    print("Building composite index (primary spec, equal weights)...")
    df = build_index(acs, svi, access, transit, None, WEIGHTS)

    valid = df.dropna(subset=["composite_score"])
    print(f"\n{len(valid)} of {len(df)} tracts have a composite score")
    print(f"Score range: {valid['composite_score'].min():.4f} to {valid['composite_score'].max():.4f}")

    breaks = jenkspy.jenks_breaks(valid["composite_score"], n_classes=3)
    print(f"Jenks natural breaks: {breaks}")

    def assign_tier(score):
        if score >= breaks[2]:
            return "Tier 1 (highest)"
        elif score >= breaks[1]:
            return "Tier 2"
        else:
            return "Tier 3 (lowest)"

    df["tier_primary"] = df["composite_score"].apply(lambda s: assign_tier(s) if pd.notna(s) else None)
    print(df["tier_primary"].value_counts().to_string())

    # --- Sensitivity variant 1: double poverty weight ---
    w1 = WEIGHTS.copy()
    w1["poverty"] *= 2
    total = sum(w1.values())
    w1 = {k: v / total for k, v in w1.items()}
    df_v1 = build_index(acs, svi, access, transit, None, w1)
    breaks_v1 = jenkspy.jenks_breaks(df_v1["composite_score"].dropna(), n_classes=3)
    df_v1["tier_v1"] = df_v1["composite_score"].apply(
        lambda s: assign_tier(s) if pd.notna(s) else None
    ) if False else df_v1["composite_score"].apply(
        lambda s: ("Tier 1 (highest)" if s >= breaks_v1[2] else "Tier 2" if s >= breaks_v1[1] else "Tier 3 (lowest)") if pd.notna(s) else None
    )

    # --- Sensitivity variant 2: double access-distance weight ---
    w2 = WEIGHTS.copy()
    w2["access_dist"] *= 2
    total = sum(w2.values())
    w2 = {k: v / total for k, v in w2.items()}
    df_v2 = build_index(acs, svi, access, transit, None, w2)
    breaks_v2 = jenkspy.jenks_breaks(df_v2["composite_score"].dropna(), n_classes=3)
    df_v2["tier_v2"] = df_v2["composite_score"].apply(
        lambda s: ("Tier 1 (highest)" if s >= breaks_v2[2] else "Tier 2" if s >= breaks_v2[1] else "Tier 3 (lowest)") if pd.notna(s) else None
    )

    compare = df[["GEOID", "tier_primary"]].merge(df_v1[["GEOID", "tier_v1"]], on="GEOID").merge(
        df_v2[["GEOID", "tier_v2"]], on="GEOID"
    )
    compare_valid = compare.dropna()
    flip_v1 = (compare_valid["tier_primary"] != compare_valid["tier_v1"]).mean() * 100
    flip_v2 = (compare_valid["tier_primary"] != compare_valid["tier_v2"]).mean() * 100

    print(f"\n=== SENSITIVITY ANALYSIS (non-negotiable per research contract) ===")
    print(f"Doubling poverty weight: {flip_v1:.2f}% of tracts change tier")
    print(f"Doubling access-distance weight: {flip_v2:.2f}% of tracts change tier")
    print("Reporting both regardless of whether they pass a stability threshold.")

    df.to_csv(OUT_PATH, index=False)
    print(f"\nWrote {OUT_PATH}")


if __name__ == "__main__":
    sys.exit(main())
