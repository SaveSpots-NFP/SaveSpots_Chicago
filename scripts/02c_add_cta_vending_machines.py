"""
Add CTA naloxone vending machine locations to the supply registry.

Per CTA's official page (transitchicago.com/naloxone/, confirmed 2026-10-18):
6 machines total. 5 are a Cook County Health pilot; the 95th/Dan Ryan machine
is a separate CDPH unit, explicitly 24/7 - the first confirmed 24-hour fixed
access point found in this registry, directly comparable to the reference
paper's Dallas finding of exactly one 24-hour point countywide.

Coordinates taken directly from CTA's own GTFS static feed (data/raw/cta_gtfs/
stops.txt, already pulled in script 06) rather than re-geocoded from an
address - this is a more precise source for a known the transit station than
address-level geocoding would be.

Run: python scripts/02c_add_cta_vending_machines.py
(Run AFTER scripts/02b_pull_library_naloxone_sites.py - appends to v2 registry)
"""
import sys
from pathlib import Path

import pandas as pd

REPO_ROOT = Path(__file__).resolve().parent.parent
CLEAN_DIR = REPO_ROOT / "data" / "clean"
REGISTRY_PATH = CLEAN_DIR / "naloxone_supply_registry_v2.csv"

# (name, latitude, longitude, is_24hr) - coordinates from CTA's own GTFS feed
CTA_VENDING_MACHINES = [
    ("CTA Naloxone Vending Machine - 47th (Red Line)", 41.810318, -87.630940, False),
    ("CTA Naloxone Vending Machine - Wilson (Red/Purple Line)", 41.965482, -87.657926, False),
    ("CTA Naloxone Vending Machine - Jefferson Park (Blue Line)", 41.970634, -87.760892, False),
    ("CTA Naloxone Vending Machine - Harlem/Lake (Green Line)", 41.886848, -87.803176, False),
    ("CTA Naloxone Vending Machine - Central Park (Pink Line)", 41.854136, -87.715159, False),
    ("CDPH Naloxone Vending Machine - 95th/Dan Ryan (Red Line, 24/7)", 41.722377, -87.624342, True),
]


def main():
    registry = pd.read_csv(REGISTRY_PATH)
    print(f"Loaded {len(registry)} existing sites")

    new_rows = []
    for name, lat, lon, is_24hr in CTA_VENDING_MACHINES:
        new_rows.append(
            {
                "name": name,
                "category": "transit_vending_machine",
                "address": None,
                "city": "Chicago",
                "state": "IL",
                "zip": None,
                "source": "CTA official naloxone page + CTA GTFS stops.txt for coordinates",
                "source_url": "https://www.transitchicago.com/naloxone/",
                "verification_date": "2026-10-18",
                "notes": f"24/7 access{'  - CONFIRMED 24hr' if is_24hr else ''}; "
                         f"{'Cook County Health pilot program' if not is_24hr else 'CDPH unit, separate from the 5-machine CCH pilot'}",
                "latitude": lat,
                "longitude": lon,
                "matched_address": None,
                "geocode_status": "FROM_GTFS",
            }
        )

    new_df = pd.DataFrame(new_rows)
    combined = pd.concat([registry, new_df], ignore_index=True)
    combined.to_csv(REGISTRY_PATH, index=False)
    print(f"Added {len(new_df)} CTA vending machine sites")
    print(f"Registry now has {len(combined)} total sites")
    print(combined["category"].value_counts().to_string())


if __name__ == "__main__":
    sys.exit(main())
