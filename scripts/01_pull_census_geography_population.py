"""
Pull 2020 Census P.L. 94-171 block population (P1_001N) and TIGER/Line 2024 block
and tract geography, filtered to Cook County, IL (state FIPS 17, county FIPS 031).

Measured, not modeled: this is a direct decennial enumeration, identical in role to
the reference paper's Dallas block-population layer.

Outputs (data/clean/, safe to commit — no individual-level or sensitive data):
  - cook_county_blocks.gpkg   (block geometry + P1_001N population)
  - cook_county_tracts.gpkg   (tract geometry only; ACS/SVI/mortality join later)

Run: python scripts/01_pull_census_geography_population.py
"""
import io
import sys
import zipfile
from pathlib import Path

import geopandas as gpd
import pandas as pd
import requests

REPO_ROOT = Path(__file__).resolve().parent.parent
RAW_DIR = REPO_ROOT / "data" / "raw" / "tiger"
CLEAN_DIR = REPO_ROOT / "data" / "clean"
RAW_DIR.mkdir(parents=True, exist_ok=True)
CLEAN_DIR.mkdir(parents=True, exist_ok=True)

STATE_FIPS = "17"  # Illinois
COUNTY_FIPS = "031"  # Cook County

TIGER_BLOCK_URL = f"https://www2.census.gov/geo/tiger/TIGER2024/TABBLOCK20/tl_2024_{STATE_FIPS}_tabblock20.zip"
TIGER_TRACT_URL = f"https://www2.census.gov/geo/tiger/TIGER2024/TRACT/tl_2024_{STATE_FIPS}_tract.zip"
CENSUS_PL_API = (
    f"https://api.census.gov/data/2020/dec/pl"
    f"?get=P1_001N,NAME&for=block:*&in=state:{STATE_FIPS}%20county:{COUNTY_FIPS}"
)


def download_and_extract_shapefile(url: str, dest_subdir: str) -> Path:
    dest = RAW_DIR / dest_subdir
    if dest.exists() and any(dest.glob("*.shp")):
        print(f"  already have {dest_subdir}, skipping download")
        return dest
    dest.mkdir(parents=True, exist_ok=True)
    print(f"  downloading {url}")
    resp = requests.get(url, timeout=120)
    resp.raise_for_status()
    with zipfile.ZipFile(io.BytesIO(resp.content)) as zf:
        zf.extractall(dest)
    print(f"  extracted to {dest}")
    return dest


def main():
    print("Step 1: TIGER/Line block geometry (Illinois statewide, filtered after)")
    block_dir = download_and_extract_shapefile(TIGER_BLOCK_URL, "tabblock20_il")
    shp = next(block_dir.glob("*.shp"))
    blocks = gpd.read_file(shp)
    print(f"  loaded {len(blocks)} Illinois blocks")

    blocks_cook = blocks[blocks["COUNTYFP20"] == COUNTY_FIPS].copy()
    print(f"  filtered to {len(blocks_cook)} Cook County blocks")

    print("Step 2: TIGER/Line tract geometry (Illinois statewide, filtered after)")
    tract_dir = download_and_extract_shapefile(TIGER_TRACT_URL, "tract_il")
    tshp = next(tract_dir.glob("*.shp"))
    tracts = gpd.read_file(tshp)
    tracts_cook = tracts[tracts["COUNTYFP"] == COUNTY_FIPS].copy()
    print(f"  filtered to {len(tracts_cook)} Cook County tracts")

    print("Step 3: 2020 Census P.L. 94-171 block population (P1_001N), measured count")
    resp = requests.get(CENSUS_PL_API, timeout=60)
    resp.raise_for_status()
    rows = resp.json()
    pop_df = pd.DataFrame(rows[1:], columns=rows[0])
    pop_df["P1_001N"] = pop_df["P1_001N"].astype(int)
    pop_df["GEOID20"] = (
        pop_df["state"] + pop_df["county"] + pop_df["tract"] + pop_df["block"]
    )
    print(f"  pulled population for {len(pop_df)} blocks from Census API")

    print("Step 4: join population to block geometry")
    blocks_cook = blocks_cook.merge(
        pop_df[["GEOID20", "P1_001N"]], on="GEOID20", how="left"
    )
    null_pop = blocks_cook["P1_001N"].isna().sum()
    print(f"  {null_pop} blocks ({null_pop/len(blocks_cook):.2%}) have no matched population")
    if null_pop > 0:
        print("  WARNING: unmatched blocks will be treated as unpopulated (0) unless investigated")
    blocks_cook["P1_001N"] = blocks_cook["P1_001N"].fillna(0).astype(int)

    total_pop = int(blocks_cook["P1_001N"].sum())
    populated_blocks = int((blocks_cook["P1_001N"] > 0).sum())
    print(f"  Cook County 2020 total population (measured): {total_pop:,}")
    print(f"  populated blocks: {populated_blocks:,} of {len(blocks_cook):,}")

    out_blocks = CLEAN_DIR / "cook_county_blocks.gpkg"
    out_tracts = CLEAN_DIR / "cook_county_tracts.gpkg"
    blocks_cook.to_file(out_blocks, driver="GPKG")
    tracts_cook.to_file(out_tracts, driver="GPKG")
    print(f"Wrote {out_blocks}")
    print(f"Wrote {out_tracts}")

    meta_path = CLEAN_DIR / "cook_county_blocks_population.meta.txt"
    with open(meta_path, "w") as f:
        f.write(f"Source: 2020 Census P.L. 94-171 (P1_001N), TIGER/Line 2024\n")
        f.write(f"Geography: Cook County, IL (state {STATE_FIPS}, county {COUNTY_FIPS})\n")
        f.write(f"Total blocks: {len(blocks_cook)}\n")
        f.write(f"Populated blocks: {populated_blocks}\n")
        f.write(f"Unmatched/null population blocks: {null_pop}\n")
        f.write(f"Total measured population: {total_pop}\n")
        f.write(f"Tracts: {len(tracts_cook)}\n")
    print(f"Wrote {meta_path}")


if __name__ == "__main__":
    sys.exit(main())
