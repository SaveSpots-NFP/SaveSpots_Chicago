"""
Pull the three remaining composite-index input layers for Cook County tracts:
  - ACS 2024 5-year poverty (S1701_C03_001E) and uninsurance (S2701_C05_001E)
  - CDC/ATSDR SVI 2022 overall percentile ranking (RPL_THEMES), tract level
  - CTA GTFS stop locations (for transit-connectivity layer, computed in
    script 07 against tract geometry)

Outputs to data/clean/ (all safe to commit - aggregate/public data, no PII):
  - acs_tract_poverty_uninsurance.csv
  - svi_2022_tract.csv
  - cta_stops.csv

Run: python scripts/06_pull_acs_svi_transit.py
"""
import io
import os
import sys
import zipfile
from pathlib import Path

import pandas as pd
import requests

REPO_ROOT = Path(__file__).resolve().parent.parent
CLEAN_DIR = REPO_ROOT / "data" / "clean"
RAW_DIR = REPO_ROOT / "data" / "raw"
CLEAN_DIR.mkdir(parents=True, exist_ok=True)
RAW_DIR.mkdir(parents=True, exist_ok=True)


def load_dotenv(env_path: Path):
    if not env_path.exists():
        return
    for line in env_path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        os.environ.setdefault(key.strip(), value.strip())


load_dotenv(REPO_ROOT / ".env")
CENSUS_API_KEY = os.environ.get("CENSUS_API_KEY")
if not CENSUS_API_KEY:
    sys.exit("ERROR: CENSUS_API_KEY not found in .env")

STATE_FIPS = "17"
COUNTY_FIPS = "031"


def pull_acs():
    print("Pulling ACS 2024 5-year poverty and uninsurance, Cook County tracts...")
    url = (
        "https://api.census.gov/data/2024/acs/acs5/subject"
        f"?get=S1701_C03_001E,S2701_C05_001E,NAME"
        f"&for=tract:*&in=state:{STATE_FIPS}%20county:{COUNTY_FIPS}&key={CENSUS_API_KEY}"
    )
    resp = requests.get(url, timeout=60)
    resp.raise_for_status()
    rows = resp.json()
    df = pd.DataFrame(rows[1:], columns=rows[0])
    df["GEOID"] = df["state"] + df["county"] + df["tract"]
    df = df.rename(
        columns={
            "S1701_C03_001E": "poverty_pct",
            "S2701_C05_001E": "uninsured_pct",
        }
    )
    df["poverty_pct"] = pd.to_numeric(df["poverty_pct"], errors="coerce")
    df["uninsured_pct"] = pd.to_numeric(df["uninsured_pct"], errors="coerce")
    out = df[["GEOID", "NAME", "poverty_pct", "uninsured_pct"]]
    null_count = out[["poverty_pct", "uninsured_pct"]].isna().any(axis=1).sum()
    print(f"  {len(out)} tracts pulled, {null_count} with a null value (ACS suppression/small sample)")
    out_path = CLEAN_DIR / "acs_tract_poverty_uninsurance.csv"
    out.to_csv(out_path, index=False)
    print(f"  wrote {out_path}")
    return out


def pull_svi():
    print("\nPulling CDC/ATSDR SVI 2022, Cook County tracts (ArcGIS FeatureServer)...")
    base = (
        "https://onemap.cdc.gov/onemapservices/rest/services/SVI/"
        "CDC_ATSDR_Social_Vulnerability_Index_2022_USA/FeatureServer/2/query"
    )
    all_rows = []
    offset = 0
    page_size = 1000
    while True:
        params = {
            "where": "STATE='Illinois' AND COUNTY='Cook County'",
            "outFields": "FIPS,E_TOTPOP,RPL_THEMES",
            "f": "json",
            "resultRecordCount": page_size,
            "resultOffset": offset,
        }
        resp = requests.get(base, params=params, timeout=60)
        resp.raise_for_status()
        data = resp.json()
        feats = data.get("features", [])
        if not feats:
            break
        all_rows.extend([f["attributes"] for f in feats])
        offset += page_size
        print(f"  pulled {len(all_rows)} tracts so far...")
        if len(feats) < page_size:
            break
    df = pd.DataFrame(all_rows).rename(columns={"FIPS": "GEOID"})
    # SVI uses -999 as a documented missing-data sentinel
    df["RPL_THEMES"] = df["RPL_THEMES"].replace(-999, pd.NA)
    null_count = df["RPL_THEMES"].isna().sum()
    print(f"  {len(df)} tracts pulled, {null_count} with missing RPL_THEMES (-999 sentinel)")
    out_path = CLEAN_DIR / "svi_2022_tract.csv"
    df.to_csv(out_path, index=False)
    print(f"  wrote {out_path}")
    return df


def pull_cta_stops():
    print("\nPulling CTA GTFS static feed (stops only, for transit-connectivity layer)...")
    gtfs_dir = RAW_DIR / "cta_gtfs"
    if not (gtfs_dir / "stops.txt").exists():
        gtfs_dir.mkdir(parents=True, exist_ok=True)
        resp = requests.get("https://www.transitchicago.com/downloads/sch_data/google_transit.zip", timeout=120)
        resp.raise_for_status()
        with zipfile.ZipFile(io.BytesIO(resp.content)) as zf:
            zf.extract("stops.txt", gtfs_dir)
        print(f"  downloaded and extracted stops.txt to {gtfs_dir}")
    else:
        print(f"  already have stops.txt, skipping download")

    stops = pd.read_csv(gtfs_dir / "stops.txt")
    print(f"  {len(stops)} CTA stops loaded")
    out_path = CLEAN_DIR / "cta_stops.csv"
    stops[["stop_id", "stop_name", "stop_lat", "stop_lon"]].to_csv(out_path, index=False)
    print(f"  wrote {out_path}")
    return stops


def main():
    pull_acs()
    pull_svi()
    pull_cta_stops()
    print("\nAll three layers pulled successfully.")


if __name__ == "__main__":
    sys.exit(main())
