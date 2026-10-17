"""
Coverage-maximizing placement analysis: rank candidate host storefronts by
need x measured reach among currently-unserved residents, plus a de-overlapped
greedy coverage analysis - matching the reference paper's Section 8.6 method.

Candidates: active Chicago business licenses in categories comparable to
Dallas's "ordinary neighborhood retail" host types (Retail Food Establishment,
Tobacco, Package Goods, Filling Station, Tavern).

Reach (measured): sum of 2020 block population over blocks that are BOTH
currently unserved (beyond 1 mile of existing supply, from script 03) AND
within a half-mile (804.672m) of the candidate.

Need: the candidate's census tract's composite vulnerability score (script 07).

Run: python scripts/08_placement_ranking.py
(Run after scripts 01, 03, 07)
"""
import sys
from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd
import requests
from scipy.spatial import cKDTree
from shapely.geometry import Point

REPO_ROOT = Path(__file__).resolve().parent.parent
CLEAN_DIR = REPO_ROOT / "data" / "clean"

BLOCK_ACCESS_PATH = CLEAN_DIR / "block_access_distances_v2.csv"
COMPOSITE_PATH = CLEAN_DIR / "composite_vulnerability_index_tract.csv"
OUT_CANDIDATES = CLEAN_DIR / "placement_candidates_ranked.csv"
OUT_GREEDY = CLEAN_DIR / "placement_greedy_coverage.csv"

PROJECTED_CRS = "EPSG:26971"
GEOGRAPHIC_CRS = "EPSG:4326"
HALF_MILE_M = 804.672

LICENSE_API = "https://data.cityofchicago.org/resource/uupf-x98q.json"
CANDIDATE_CATEGORIES = [
    "Retail Food Establishment",
    "Tobacco",
    "Package Goods",
    "Filling Station",
    "Tavern",
]


def pull_candidates():
    print("Pulling active Chicago business licenses as placement candidates...")
    all_rows = []
    for category in CANDIDATE_CATEGORIES:
        offset = 0
        while True:
            params = {
                "$where": f"license_description='{category}' AND license_status='AAI'",
                "$select": "license_number,doing_business_as_name,address,zip_code,community_area_name,license_description,latitude,longitude",
                "$limit": 5000,
                "$offset": offset,
            }
            resp = requests.get(LICENSE_API, params=params, timeout=60)
            resp.raise_for_status()
            rows = resp.json()
            if not rows:
                break
            all_rows.extend(rows)
            offset += 5000
            if len(rows) < 5000:
                break
        print(f"  {category}: {offset + len(rows) if rows else offset} cumulative candidates pulled")

    df = pd.DataFrame(all_rows)
    df = df.dropna(subset=["latitude", "longitude"])
    df["latitude"] = df["latitude"].astype(float)
    df["longitude"] = df["longitude"].astype(float)
    before = len(df)
    df = df.drop_duplicates(subset=["address"])
    print(f"Deduplicated by address: {before} -> {len(df)} candidates")
    return df


def main():
    candidates = pull_candidates()

    print("\nLoading block access data and composite index...")
    blocks = pd.read_csv(BLOCK_ACCESS_PATH)
    blocks["GEOID20"] = blocks["GEOID20"].astype(str).str.zfill(15)
    blocks["tract_GEOID"] = blocks["GEOID20"].str[:11]
    unserved = blocks[(blocks["beyond_1_mile"]) & (blocks["P1_001N"] > 0)].copy()
    print(f"  {len(unserved)} unserved populated blocks, {unserved['P1_001N'].sum():,} unserved residents total")

    composite = pd.read_csv(COMPOSITE_PATH, dtype={"GEOID": str})

    print("Projecting and building KD-tree of unserved block locations...")
    # Need lat/lon back for unserved blocks - re-derive from GEOID join is not
    # available here (block_access_distances_v2 dropped geometry); re-join to
    # the blocks geopackage for coordinates.
    blocks_geo = gpd.read_file(REPO_ROOT / "data" / "clean" / "cook_county_blocks.gpkg")
    blocks_geo["INTPTLAT20"] = blocks_geo["INTPTLAT20"].astype(float)
    blocks_geo["INTPTLON20"] = blocks_geo["INTPTLON20"].astype(float)
    unserved = unserved.merge(
        blocks_geo[["GEOID20", "INTPTLAT20", "INTPTLON20"]], on="GEOID20", how="left"
    )

    unserved_gdf = gpd.GeoDataFrame(
        unserved,
        geometry=[Point(xy) for xy in zip(unserved["INTPTLON20"], unserved["INTPTLAT20"])],
        crs=GEOGRAPHIC_CRS,
    ).to_crs(PROJECTED_CRS)
    unserved_coords = np.array([(g.x, g.y) for g in unserved_gdf.geometry])
    unserved_pop = unserved_gdf["P1_001N"].values
    tree = cKDTree(unserved_coords)

    cand_gdf = gpd.GeoDataFrame(
        candidates,
        geometry=[Point(xy) for xy in zip(candidates["longitude"], candidates["latitude"])],
        crs=GEOGRAPHIC_CRS,
    ).to_crs(PROJECTED_CRS)
    cand_coords = np.array([(g.x, g.y) for g in cand_gdf.geometry])

    print(f"Computing reach for {len(candidates)} candidates (blocks within 0.5mi)...")
    neighbor_lists = tree.query_ball_point(cand_coords, r=HALF_MILE_M)
    reach = np.array([unserved_pop[idx].sum() if len(idx) else 0 for idx in neighbor_lists])
    candidates = candidates.reset_index(drop=True)
    candidates["reach"] = reach

    print(f"Reach stats: mean={reach.mean():.1f}, median={np.median(reach):.1f}, max={reach.max()}, "
          f"{int((reach == 0).sum())} candidates with zero reach")

    # Join need (tract composite score) via spatial join to tract geometry
    tracts = gpd.read_file(REPO_ROOT / "data" / "clean" / "cook_county_tracts.gpkg")[["GEOID", "geometry"]]
    tracts = tracts.to_crs(GEOGRAPHIC_CRS)  # TIGER ships NAD83 (EPSG:4269); align to candidates' WGS84
    cand_gdf_wgs = gpd.GeoDataFrame(
        candidates, geometry=[Point(xy) for xy in zip(candidates["longitude"], candidates["latitude"])], crs=GEOGRAPHIC_CRS
    )
    cand_with_tract = gpd.sjoin(cand_gdf_wgs, tracts, how="left", predicate="within")
    candidates["tract_GEOID"] = cand_with_tract["GEOID"].values
    candidates = candidates.merge(
        composite[["GEOID", "composite_score"]], left_on="tract_GEOID", right_on="GEOID", how="left"
    )

    def minmax(s):
        lo, hi = s.min(), s.max()
        return (s - lo) / (hi - lo) if hi > lo else s * 0

    candidates["norm_reach"] = minmax(candidates["reach"])
    candidates["norm_need"] = minmax(candidates["composite_score"].fillna(candidates["composite_score"].median()))
    candidates["rank_score"] = candidates["norm_need"] * candidates["norm_reach"]

    ranked = candidates.sort_values("rank_score", ascending=False).reset_index(drop=True)
    ranked.to_csv(OUT_CANDIDATES, index=False)
    print(f"\nWrote {OUT_CANDIDATES} ({len(ranked)} ranked candidates)")
    print("\nTop 5 candidates by need x reach:")
    print(ranked[["doing_business_as_name", "address", "community_area_name", "reach", "composite_score", "rank_score"]].head(5).to_string())

    # --- Greedy de-overlapped coverage analysis ---
    print("\nRunning greedy coverage analysis (10/25/50 sites)...")
    covered = np.zeros(len(unserved_pop), dtype=bool)
    selected = []
    remaining_candidates = list(range(len(candidates)))
    for step in range(50):
        best_idx, best_new_pop = None, -1
        for ci in remaining_candidates:
            idx = neighbor_lists[ci]
            if not idx:
                continue
            new_mask = ~covered[idx]
            new_pop = unserved_pop[np.array(idx)[new_mask]].sum() if new_mask.any() else 0
            if new_pop > best_new_pop:
                best_new_pop = new_pop
                best_idx = ci
        if best_idx is None or best_new_pop <= 0:
            break
        covered[neighbor_lists[best_idx]] = True
        selected.append((candidates.loc[best_idx, "doing_business_as_name"],
                          candidates.loc[best_idx, "address"], best_new_pop))
        remaining_candidates.remove(best_idx)
        if (step + 1) in (10, 25, 50):
            total_covered = int(unserved_pop[covered].sum())
            pct = total_covered / unserved_pop.sum() * 100
            print(f"  {step+1} sites -> {total_covered:,} newly covered ({pct:.2f}% of unserved population)")

    greedy_df = pd.DataFrame(selected, columns=["name", "address", "marginal_new_coverage"])
    greedy_df.to_csv(OUT_GREEDY, index=False)
    print(f"\nWrote {OUT_GREEDY}")


if __name__ == "__main__":
    sys.exit(main())
