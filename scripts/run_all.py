"""
Runs the full pipeline in dependency order. Requires a Census API key in
.env (see .env.example) and an internet connection (every script pulls live
from a public source - nothing is bundled, per the reproducibility standard).

Run: python scripts/run_all.py
"""
import subprocess
import sys
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parent

PIPELINE = [
    "01_pull_census_geography_population.py",
    "02_build_naloxone_supply_registry.py",
    "02b_pull_library_naloxone_sites.py",
    "03_measured_access_analysis.py",
    "04_pull_mortality_aggregate_to_tract.py",
    "05_validate_access_vs_mortality.py",
    "06_pull_acs_svi_transit.py",
    "07_build_composite_index.py",
    "08_placement_ranking.py",
]


def main():
    for script in PIPELINE:
        print(f"\n{'='*70}\nRunning {script}\n{'='*70}")
        result = subprocess.run([sys.executable, str(SCRIPTS_DIR / script)])
        if result.returncode != 0:
            sys.exit(f"FAILED at {script} (exit code {result.returncode}) - stopping pipeline")
    print("\nAll pipeline stages completed successfully.")


if __name__ == "__main__":
    sys.exit(main())
