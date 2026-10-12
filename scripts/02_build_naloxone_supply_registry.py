"""
Build the naloxone/harm-reduction supply registry for Chicago/Cook County.

Environment C task (per Deliverable 3): no consolidated, machine-readable,
state-published naloxone site feed exists for Illinois (unlike Texas DSHS
NarcanSites), so this registry is assembled by hand from named organizations
identified during Deliverable 1 research, then geocoded.

This is a seed (v1) registry, not final: it currently has 9 sites found during
manuscript research (Chicago Recovery Alliance, 5 COIP storefronts, 2 Cook County
Health hospital EDs, West Side Heroin/Opioid Task Force). Still missing: SAMHSA
findtreatment.gov facilities (API requires registration - see
scripts/README_registry_todo.md), the full IDHS DOPP funded-provider list, and
category/hours/24-hour-status detail for each site (per guide Environment C
requirements). This is public organization data (addresses orgs publish
themselves), not individual-level data - no privacy floor concerns here,
unlike the ME dataset.

Geocoding: Census Bureau's free Geocoder API (no key required).

Run: python scripts/02_build_naloxone_supply_registry.py
"""
import sys
import time
from pathlib import Path

import pandas as pd
import requests

REPO_ROOT = Path(__file__).resolve().parent.parent
RAW_PATH = REPO_ROOT / "data" / "raw" / "naloxone_supply_seed_v1.csv"
CLEAN_PATH = REPO_ROOT / "data" / "clean" / "naloxone_supply_registry_v1.csv"

GEOCODER_URL = "https://geocoding.geo.census.gov/geocoder/locations/onelineaddress"


def geocode_address(address: str, city: str, state: str, zip_code: str) -> dict:
    full_address = f"{address}, {city}, {state} {zip_code}"
    params = {
        "address": full_address,
        "benchmark": "Public_AR_Current",
        "format": "json",
    }
    resp = requests.get(GEOCODER_URL, params=params, timeout=30)
    resp.raise_for_status()
    data = resp.json()
    matches = data.get("result", {}).get("addressMatches", [])
    if not matches:
        return {"latitude": None, "longitude": None, "matched_address": None, "geocode_status": "NO_MATCH"}
    m = matches[0]
    coords = m["coordinates"]
    return {
        "latitude": coords["y"],
        "longitude": coords["x"],
        "matched_address": m["matchedAddress"],
        "geocode_status": "MATCHED",
    }


def main():
    df = pd.read_csv(RAW_PATH)
    print(f"Loaded {len(df)} seed sites from {RAW_PATH.name}")

    results = []
    for _, row in df.iterrows():
        print(f"  geocoding: {row['name']}")
        geo = geocode_address(row["address"], row["city"], row["state"], str(row["zip"]))
        results.append(geo)
        time.sleep(0.5)  # be polite to the free public geocoder

    geo_df = pd.DataFrame(results)
    out = pd.concat([df.reset_index(drop=True), geo_df], axis=1)

    matched = (out["geocode_status"] == "MATCHED").sum()
    print(f"Geocoded {matched} of {len(out)} sites successfully")
    if matched < len(out):
        failed = out[out["geocode_status"] != "MATCHED"]["name"].tolist()
        print(f"  WARNING: failed to geocode: {failed} — needs manual lat/long lookup")

    CLEAN_PATH.parent.mkdir(parents=True, exist_ok=True)
    out.to_csv(CLEAN_PATH, index=False)
    print(f"Wrote {CLEAN_PATH}")
    print(
        "\nNOTE: this is a v1 seed registry (9 sites). It is NOT yet a complete "
        "supply inventory - still need SAMHSA facilities and the full IDHS DOPP "
        "provider list before this is usable for the access-distance analysis."
    )


if __name__ == "__main__":
    sys.exit(main())
