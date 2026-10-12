"""
Pull Chicago Public Library branch locations (city open data portal) and merge
with the manually-assembled org registry into a v2 naloxone supply registry.

Why this matters: per IDHS's funded-provider page and multiple CDPH press
releases (see Deliverable 1 sources), naloxone is now stocked, no-questions-
asked, at ALL 81-82 Chicago Public Library branches - a systematic, citywide
distribution network with no equivalent in the reference paper's Dallas
analysis (which had 38 total sites of any kind). This single policy decision
plausibly changes the Chicago access picture more than any other input in this
pipeline.

Source: data.cityofchicago.org, "Libraries - Locations, Hours and Contact
Information" (resource id x8fc-8rcq) - already geocoded, no geocoding needed.

Run: python scripts/02b_pull_library_naloxone_sites.py
(Run AFTER scripts/02_build_naloxone_supply_registry.py)
"""
import sys
from pathlib import Path

import pandas as pd
import requests

REPO_ROOT = Path(__file__).resolve().parent.parent
CLEAN_DIR = REPO_ROOT / "data" / "clean"

LIBRARY_API = "https://data.cityofchicago.org/resource/x8fc-8rcq.json?$limit=200"
EXISTING_REGISTRY = CLEAN_DIR / "naloxone_supply_registry_v1.csv"
OUT_PATH = CLEAN_DIR / "naloxone_supply_registry_v2.csv"


def main():
    print("Pulling Chicago Public Library branch locations...")
    resp = requests.get(LIBRARY_API, timeout=60)
    resp.raise_for_status()
    rows = resp.json()
    print(f"  pulled {len(rows)} branches")

    lib_records = []
    missing_coords = 0
    for r in rows:
        loc = r.get("location", {})
        lat, lon = loc.get("latitude"), loc.get("longitude")
        if not lat or not lon:
            missing_coords += 1
            continue
        lib_records.append(
            {
                "name": f"Chicago Public Library - {r.get('branch_', 'Unknown branch')}",
                "category": "library_naloxone_site",
                "address": r.get("address"),
                "city": r.get("city"),
                "state": r.get("state"),
                "zip": r.get("zip"),
                "source": "City of Chicago Data Portal (x8fc-8rcq) + CDPH naloxone-at-libraries program",
                "source_url": "https://data.cityofchicago.org/Education/Libraries-Locations-Hours-and-Contact-Information/x8fc-8rcq",
                "verification_date": "2026-10-11",
                "notes": "All CPL branches stock naloxone no-questions-asked per CDPH program (confirmed multiple press sources, 2026)",
                "latitude": float(lat),
                "longitude": float(lon),
                "matched_address": None,
                "geocode_status": "FROM_SOURCE",
            }
        )
    if missing_coords:
        print(f"  WARNING: {missing_coords} branches had no coordinates, excluded")

    lib_df = pd.DataFrame(lib_records)
    print(f"  {len(lib_df)} library branches with valid coordinates")

    existing = pd.read_csv(EXISTING_REGISTRY)
    print(f"Loaded {len(existing)} previously-assembled sites")

    combined = pd.concat([existing, lib_df], ignore_index=True)
    combined.to_csv(OUT_PATH, index=False)
    print(f"\nWrote {OUT_PATH} with {len(combined)} total sites")
    print(combined["category"].value_counts().to_string())


if __name__ == "__main__":
    sys.exit(main())
