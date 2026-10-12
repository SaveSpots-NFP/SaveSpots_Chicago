"""
THE PAPER'S CENTRAL METHODOLOGICAL CONTRIBUTION.

The reference paper (Dallas) could only check whether an access-based ranking
agreed with a SECOND access-based ranking (one including modeled mortality,
one not) - because Texas suppresses real mortality at fine geography. It could
never test access against actual observed deaths.

Chicago can. This script aggregates the block-level measured access analysis
(scripts/03) up to tract level and correlates it directly against measured
(not modeled, not suppressed) tract-level mortality counts (scripts/04) - a
genuinely stronger validation than Dallas's rho=0.966 rank-correlation between
two variants of the same access-based method.

Both inputs here are MEASURED, not modeled: distance is geometry, death counts
are direct case counts. Any correlation found is between two measured
quantities, which is a meaningfully different (and stronger) claim than
Dallas could make.

Run: python scripts/05_validate_access_vs_mortality.py
(Run after scripts/03 and scripts/04)
"""
import sys
from pathlib import Path

import pandas as pd
from scipy.stats import spearmanr

REPO_ROOT = Path(__file__).resolve().parent.parent
CLEAN_DIR = REPO_ROOT / "data" / "clean"

BLOCK_ACCESS_PATH = CLEAN_DIR / "block_access_distances_v2.csv"
TRACT_MORTALITY_PATH = CLEAN_DIR / "tract_opioid_mortality_counts.csv"
OUT_PATH = CLEAN_DIR / "tract_access_vs_mortality.csv"


def main():
    print("Loading block-level access data...")
    blocks = pd.read_csv(BLOCK_ACCESS_PATH)

    # Block GEOID20 (15 digits: state+county+tract+block) nests the tract
    # GEOID (11 digits) by Census construction - no spatial join needed, this
    # is exact, not approximate.
    blocks["GEOID20"] = blocks["GEOID20"].astype(str).str.zfill(15)
    blocks["tract_GEOID"] = blocks["GEOID20"].str[:11]

    print("Aggregating to tract level (population-weighted)...")
    populated = blocks[blocks["P1_001N"] > 0].copy()

    def weighted_avg(group, value_col, weight_col):
        w = group[weight_col]
        if w.sum() == 0:
            return float("nan")
        return (group[value_col] * w).sum() / w.sum()

    tract_agg = (
        populated.groupby("tract_GEOID")
        .apply(
            lambda g: pd.Series(
                {
                    "tract_population": g["P1_001N"].sum(),
                    "pop_weighted_avg_dist_m": weighted_avg(g, "dist_to_nearest_supply_m", "P1_001N"),
                    "pop_beyond_1mi": g.loc[g["beyond_1_mile"], "P1_001N"].sum(),
                    "pop_beyond_2mi": g.loc[g["beyond_2_mile"], "P1_001N"].sum(),
                }
            )
        )
        .reset_index()
    )
    tract_agg["pct_beyond_1mi"] = tract_agg["pop_beyond_1mi"] / tract_agg["tract_population"] * 100

    print(f"  {len(tract_agg)} populated tracts aggregated")

    print("Loading tract mortality data...")
    mortality = pd.read_csv(TRACT_MORTALITY_PATH)
    mortality["GEOID"] = mortality["GEOID"].astype(str).str.zfill(11)

    merged = tract_agg.merge(mortality, left_on="tract_GEOID", right_on="GEOID", how="inner")
    print(f"  {len(merged)} tracts matched between access and mortality data")

    merged["mortality_rate_per_100k"] = (
        merged["opioid_death_count"] / merged["tract_population"] * 100_000
    )

    print("\n=== CENTRAL VALIDATION: measured access vs. measured mortality ===\n")

    # Full sample (all tracts)
    rho_dist, p_dist = spearmanr(merged["pop_weighted_avg_dist_m"], merged["opioid_death_count"])
    rho_pct1mi, p_pct1mi = spearmanr(merged["pct_beyond_1mi"], merged["opioid_death_count"])
    rho_rate, p_rate = spearmanr(merged["pop_weighted_avg_dist_m"], merged["mortality_rate_per_100k"])

    print(f"Spearman rho, avg distance to supply vs. raw death COUNT: {rho_dist:.4f} (p={p_dist:.2e})")
    print(f"Spearman rho, %%beyond 1mi vs. raw death COUNT: {rho_pct1mi:.4f} (p={p_pct1mi:.2e})")
    print(f"Spearman rho, avg distance to supply vs. death RATE per 100k: {rho_rate:.4f} (p={p_rate:.2e})")

    # Excluding small-cell-flagged tracts, as a sensitivity check
    confident = merged[~merged["small_cell_flag"]]
    print(f"\n--- Sensitivity: excluding {merged['small_cell_flag'].sum()} small-cell-flagged tracts ({len(confident)} remain) ---")
    if len(confident) > 10:
        rho_c, p_c = spearmanr(confident["pop_weighted_avg_dist_m"], confident["mortality_rate_per_100k"])
        print(f"Spearman rho, avg distance vs. rate per 100k (confident tracts only): {rho_c:.4f} (p={p_c:.2e})")

    # Quartile overlap check: do the worst-access tracts overlap with the
    # highest-mortality-rate tracts?
    merged["access_quartile"] = pd.qcut(merged["pop_weighted_avg_dist_m"], 4, labels=["Q1_best", "Q2", "Q3", "Q4_worst"])
    merged["mortality_quartile"] = pd.qcut(merged["mortality_rate_per_100k"].rank(method="first"), 4, labels=["Q1_lowest", "Q2", "Q3", "Q4_highest"])
    worst_access = set(merged.loc[merged["access_quartile"] == "Q4_worst", "tract_GEOID"])
    highest_mortality = set(merged.loc[merged["mortality_quartile"] == "Q4_highest", "tract_GEOID"])
    overlap = worst_access & highest_mortality
    expected_by_chance = len(merged) * 0.25 * 0.25  # two independent quartiles, not one
    print(
        f"\nWorst-access quartile ({len(worst_access)} tracts) vs. highest-mortality-rate "
        f"quartile ({len(highest_mortality)} tracts): {len(overlap)} tracts in both "
        f"({len(overlap)/len(worst_access)*100:.1f}% overlap; {expected_by_chance:.0f} "
        f"expected under no relationship, i.e. two independent random quartiles)"
    )

    merged.to_csv(OUT_PATH, index=False)
    print(f"\nWrote {OUT_PATH}")
    print(
        "\nNOTE: correlation, even if found, does not establish that access DISTANCE "
        "causes mortality - both could be driven by a shared underlying factor "
        "(poverty, segregation, etc.). This script tests coincidence, not causation, "
        "and the manuscript must say so explicitly, same as the reference paper's "
        "treatment of its comparative case studies."
    )


if __name__ == "__main__":
    sys.exit(main())
