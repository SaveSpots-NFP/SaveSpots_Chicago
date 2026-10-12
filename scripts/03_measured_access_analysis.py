"""
Measured access analysis: straight-line (Euclidean) distance from every Cook
County census block's internal point to the nearest naloxone/harm-reduction
supply site, following the reference paper's exact method (Dallas §2.4).

Projection: NAD83 / Illinois East (EPSG:26971, meters) - the Illinois analog of
the reference paper's EPSG:32138 (Texas North Central). Chosen because Cook
County falls within the Illinois East zone.

Thresholds: 1 mile (1,609.344 m), 2 miles (3,218.688 m), 5 miles (8,046.72 m) -
identical to the reference paper, for direct comparability.

IMPORTANT CAVEAT: the supply registry this script currently reads
(naloxone_supply_registry_v1.csv) has only 9 seed sites, versus the reference
paper's 38 for Dallas. These numbers are a pipeline validation run, NOT a
publishable finding - the registry still needs SAMHSA facilities and the full
IDHS DOPP provider list before any number here goes in the manuscript. This
script's job is to prove the mechanism is correct; expanding the registry is
separate work.

Run: python scripts/03_measured_access_analysis.py
"""
import sys
from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd
from scipy.spatial import cKDTree
from shapely.geometry import Point

REPO_ROOT = Path(__file__).resolve().parent.parent
CLEAN_DIR = REPO_ROOT / "data" / "clean"

BLOCKS_PATH = CLEAN_DIR / "cook_county_blocks.gpkg"
SUPPLY_PATH = CLEAN_DIR / "naloxone_supply_registry_v1.csv"

PROJECTED_CRS = "EPSG:26971"  # NAD83 / Illinois East (meters)
GEOGRAPHIC_CRS = "EPSG:4326"

MILE_M = 1609.344
THRESHOLDS = {"1_mile": MILE_M, "2_mile": 2 * MILE_M, "5_mile": 5 * MILE_M}


def main():
    print("Loading blocks and supply registry...")
    blocks = gpd.read_file(BLOCKS_PATH)
    supply = pd.read_csv(SUPPLY_PATH)
    n_supply = len(supply)
    print(f"  {len(blocks)} blocks, {n_supply} supply sites")
    print(
        f"  CAVEAT: {n_supply} sites is a seed registry, not a complete inventory "
        "(reference paper used 38 for Dallas). Treat all output as provisional."
    )

    # Census Bureau internal points (INTPTLAT20/INTPTLON20), matching the
    # reference paper's exact block-location method rather than polygon centroids
    if "INTPTLAT20" not in blocks.columns or "INTPTLON20" not in blocks.columns:
        sys.exit("ERROR: expected INTPTLAT20/INTPTLON20 columns not found in blocks file")

    blocks["INTPTLAT20"] = blocks["INTPTLAT20"].astype(float)
    blocks["INTPTLON20"] = blocks["INTPTLON20"].astype(float)
    block_points = gpd.GeoDataFrame(
        blocks[["GEOID20", "P1_001N", "COUNTYFP20"]].copy(),
        geometry=[Point(xy) for xy in zip(blocks["INTPTLON20"], blocks["INTPTLAT20"])],
        crs=GEOGRAPHIC_CRS,
    ).to_crs(PROJECTED_CRS)

    supply_points = gpd.GeoDataFrame(
        supply.copy(),
        geometry=[Point(xy) for xy in zip(supply["longitude"], supply["latitude"])],
        crs=GEOGRAPHIC_CRS,
    ).to_crs(PROJECTED_CRS)

    print("Building KD-tree and computing nearest-neighbor distances...")
    supply_coords = np.array([(geom.x, geom.y) for geom in supply_points.geometry])
    block_coords = np.array([(geom.x, geom.y) for geom in block_points.geometry])
    tree = cKDTree(supply_coords)
    distances_m, nearest_idx = tree.query(block_coords, k=1)

    block_points["dist_to_nearest_supply_m"] = distances_m
    block_points["nearest_supply_name"] = supply_points.iloc[nearest_idx]["name"].values

    for label, threshold in THRESHOLDS.items():
        block_points[f"beyond_{label}"] = block_points["dist_to_nearest_supply_m"] > threshold

    populated = block_points[block_points["P1_001N"] > 0].copy()
    total_pop = int(populated["P1_001N"].sum())
    print(f"\nTotal measured population (populated blocks): {total_pop:,}")

    for label in THRESHOLDS:
        beyond_pop = int(populated.loc[populated[f"beyond_{label}"], "P1_001N"].sum())
        pct = beyond_pop / total_pop * 100
        print(f"  Beyond {label.replace('_', ' ')}: {beyond_pop:,} residents ({pct:.2f}%)")

    print(
        f"\nTract-centroid-equivalent avg distance (population-weighted, meters): "
        f"{np.average(populated['dist_to_nearest_supply_m'], weights=populated['P1_001N']):,.0f}"
    )

    # Drop geometry for the tabular output; keep a separate geo export for mapping
    out_csv = CLEAN_DIR / "block_access_distances_v1.csv"
    block_points.drop(columns="geometry").to_csv(out_csv, index=False)
    print(f"\nWrote {out_csv}")

    out_gpkg = CLEAN_DIR / "block_access_distances_v1.gpkg"
    block_points.to_crs(GEOGRAPHIC_CRS).to_file(out_gpkg, driver="GPKG")
    print(f"Wrote {out_gpkg}")

    meta_path = CLEAN_DIR / "block_access_distances_v1.meta.txt"
    with open(meta_path, "w") as f:
        f.write("MEASURED access analysis - PROVISIONAL (v1 seed registry, 9 sites)\n")
        f.write(f"Supply sites used: {n_supply}\n")
        f.write(f"Projection: {PROJECTED_CRS}\n")
        f.write(f"Total measured population: {total_pop}\n")
        for label, threshold in THRESHOLDS.items():
            beyond_pop = int(populated.loc[populated[f"beyond_{label}"], "P1_001N"].sum())
            f.write(f"Beyond {label}: {beyond_pop} ({beyond_pop/total_pop*100:.2f}%)\n")
        f.write(
            "\nDO NOT CITE THESE NUMBERS IN THE MANUSCRIPT - registry is incomplete. "
            "Re-run after expanding naloxone_supply_registry to include SAMHSA and "
            "IDHS DOPP sites.\n"
        )
    print(f"Wrote {meta_path}")


if __name__ == "__main__":
    sys.exit(main())
