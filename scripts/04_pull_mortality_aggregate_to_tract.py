"""
Pull Cook County Medical Examiner opioid-related deaths (live API, confirmed
working in Deliverable 1/3 research) and aggregate to CENSUS TRACT level via
point-in-polygon spatial join.

PRIVACY FLOOR (hard rule, no exceptions - see CLAUDE.md): this dataset contains
exact addresses, coordinates, and case numbers for individual decedents. The
raw pull is written ONLY to data/raw/cook_county_me_opioid_raw.csv, which is
gitignored and MUST NEVER be committed. Only the tract-level AGGREGATE counts
(data/clean/) are safe to publish - no case-level fields, no addresses, no
coordinates, nothing below tract geography.

Small-cell handling: per Deliverable 3's self-imposed policy (Illinois has no
suppression regime forcing this, unlike Texas, but a near-zero-population tract
reporting an exact low count could still be functionally identifying), tracts
with fewer than 5 cases in the window are flagged, not deleted - the flag is
published, the exact low count is not re-identifying on its own at tract scale
(unlike block scale) but is noted for methodological transparency.

Window: 2022-01-01 through the most recent available date, death_date field
(when death was certified, not necessarily when the overdose occurred) - this
is the dataset's main date field; see CLAUDE.md for the incident_date vs
death_date distinction still to be resolved.

Run: python scripts/04_pull_mortality_aggregate_to_tract.py
"""
import sys
from pathlib import Path

import geopandas as gpd
import pandas as pd
import requests
from shapely.geometry import Point

REPO_ROOT = Path(__file__).resolve().parent.parent
RAW_DIR = REPO_ROOT / "data" / "raw"
CLEAN_DIR = REPO_ROOT / "data" / "clean"
RAW_DIR.mkdir(parents=True, exist_ok=True)

ME_API = "https://datacatalog.cookcountyil.gov/resource/cjeq-bs86.json"
TRACTS_PATH = CLEAN_DIR / "cook_county_tracts.gpkg"

WINDOW_START = "2022-01-01T00:00:00"
WINDOW_END = "2026-01-01T00:00:00"  # exclusive; captures 2022-2025 complete-ish
SMALL_CELL_THRESHOLD = 5

RAW_SENSITIVE_PATH = RAW_DIR / "cook_county_me_opioid_raw.csv"  # GITIGNORED, never commit
CLEAN_TRACT_PATH = CLEAN_DIR / "tract_opioid_mortality_counts.csv"  # safe to commit


def pull_all_opioid_cases():
    """Paginate through the Socrata API to get every opioid case in the window."""
    all_rows = []
    offset = 0
    page_size = 5000
    while True:
        params = {
            "$where": f'opioids=true and death_date >= "{WINDOW_START}" and death_date < "{WINDOW_END}"',
            "$select": "casenumber,death_date,incident_date,age,gender,race,latino,latitude,longitude,incident_city",
            "$limit": page_size,
            "$offset": offset,
        }
        resp = requests.get(ME_API, params=params, timeout=60)
        resp.raise_for_status()
        rows = resp.json()
        if not rows:
            break
        all_rows.extend(rows)
        print(f"  pulled {len(all_rows)} cases so far...")
        offset += page_size
        if len(rows) < page_size:
            break
    return pd.DataFrame(all_rows)


def main():
    print(f"Pulling Cook County ME opioid cases, {WINDOW_START} to {WINDOW_END}...")
    df = pull_all_opioid_cases()
    print(f"Total cases pulled: {len(df)}")

    # Save raw pull LOCALLY ONLY - this path is gitignored (data/raw/cook_county_me*)
    df.to_csv(RAW_SENSITIVE_PATH, index=False)
    print(f"Wrote RAW (sensitive, gitignored, NOT committed) pull to {RAW_SENSITIVE_PATH}")

    df = df.dropna(subset=["latitude", "longitude"])
    df["latitude"] = df["latitude"].astype(float)
    df["longitude"] = df["longitude"].astype(float)
    print(f"{len(df)} cases have usable coordinates")

    print("Loading Cook County tract geometry...")
    tracts = gpd.read_file(TRACTS_PATH)

    cases_gdf = gpd.GeoDataFrame(
        df[["casenumber"]].copy(),
        geometry=[Point(xy) for xy in zip(df["longitude"], df["latitude"])],
        crs="EPSG:4326",
    )
    if tracts.crs != cases_gdf.crs:
        tracts = tracts.to_crs(cases_gdf.crs)

    print("Spatial join: cases -> tracts (point-in-polygon)...")
    joined = gpd.sjoin(cases_gdf, tracts[["GEOID", "geometry"]], how="left", predicate="within")

    unmatched = joined["GEOID"].isna().sum()
    if unmatched:
        print(f"  WARNING: {unmatched} cases did not fall within any Cook County tract "
              f"(likely addresses just outside county line, geocoding errors, or edge cases)")

    tract_counts = joined.groupby("GEOID").size().reset_index(name="opioid_death_count")

    # Merge onto the full tract list so zero-count tracts are explicit, not missing
    all_tracts = tracts[["GEOID"]].copy()
    tract_counts = all_tracts.merge(tract_counts, on="GEOID", how="left")
    tract_counts["opioid_death_count"] = tract_counts["opioid_death_count"].fillna(0).astype(int)
    tract_counts["small_cell_flag"] = tract_counts["opioid_death_count"] < SMALL_CELL_THRESHOLD

    print(f"\nTracts: {len(tract_counts)}")
    print(f"Tracts with 0 cases in window: {(tract_counts['opioid_death_count'] == 0).sum()}")
    print(f"Tracts flagged small-cell (<{SMALL_CELL_THRESHOLD}): {tract_counts['small_cell_flag'].sum()}")
    print(f"Total matched cases across all tracts: {tract_counts['opioid_death_count'].sum()}")

    CLEAN_DIR.mkdir(parents=True, exist_ok=True)
    tract_counts.to_csv(CLEAN_TRACT_PATH, index=False)
    print(f"\nWrote AGGREGATE (safe, tract-level only) output to {CLEAN_TRACT_PATH}")
    print("No addresses, coordinates, case numbers, or individual-level fields in this file.")


if __name__ == "__main__":
    sys.exit(main())
