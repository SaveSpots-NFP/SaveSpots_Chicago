# SaveSpots Chicago — Harm Reduction Access & Policy Analysis

**Status: pipeline built, numbers provisional (pre-Week-10 freeze).** Every number
below is real and reproducible by running `scripts/run_all.py`, not a placeholder —
but per the program guide, nothing here is final until the Week 10 analysis freeze
(Zenodo DOI minted, numbers locked). Treat this README as a live working snapshot.

## What this analysis does

A block-level access, policy, and geographic-prioritization analysis of naloxone /
harm-reduction infrastructure in Chicago, Illinois, modeled on the standard set by
Ilyas & Ilyas (2026), "Structural Gaps in Urban Harm Reduction Infrastructure: A
Block-Level Access and Policy Analysis of Dallas County, Texas" (see
`references/Dallas paper.pdf`). Program requirements: `references/SaveSpots
Deliverable Guide FINAL.pdf`. Full project conventions: `CLAUDE.md`.

## Why it's built this way

Chicago's data environment differs from Dallas's in one decisive respect: Cook County
Medical Examiner publishes case-level overdose death records with geography
(confirmed — a live, queryable Socrata API, not suppressed), whereas Texas suppresses
mortality counts at fine geography by law. This means the Dallas paper's central
workaround (treating measured access/distance as the primary quantity because
mortality couldn't be trusted at fine geography) is not the binding constraint here —
Chicago instead validates a measured access analysis directly against real, measured
death geography, which Dallas explicitly could not do. Full data-environment
declaration: `manuscript/deliverable_3_data_inventory_and_plan.md`.

## Headline outputs (provisional)

| Finding | Number | From | Script |
|---|---|---|---|
| Cook County 2020 measured population | 5,275,541 | `data/clean/cook_county_blocks_population.meta.txt` | `01` |
| Naloxone supply registry size | 103 sites (82 CPL branches + 15 named orgs + 6 CTA vending machines) | `data/clean/naloxone_supply_registry_v2.csv` | `02`, `02b` |
| Population beyond 1 mile of supply | 50.04% (2,639,999 residents) | `data/clean/block_access_distances_v2.meta.txt` | `03` |
| Population beyond 5 miles of supply | 20.83% | `data/clean/block_access_distances_v2.meta.txt` | `03` |
| Opioid deaths, Cook County ME, 2022–2025 window | 5,783 total cases, 5,372 geocoded | `data/clean/tract_opioid_mortality_counts.csv` | `04` |
| Access-distance vs. mortality rate correlation | Spearman rho = -0.32 (all tracts), -0.37 (excl. small-cell) | `data/clean/tract_access_vs_mortality.csv` | `05` |
| Composite vulnerability tiers | Tier 1: 344 tracts, Tier 2: 770, Tier 3: 218 | `data/clean/composite_vulnerability_index_tract.csv` | `07` |
| Sensitivity: poverty-weight-doubled flip rate | 0.00% | same | `07` |
| Sensitivity: distance-weight-doubled flip rate | 12.61% | same | `07` |
| Placement candidates ranked | 11,370 (active business licenses) | `data/clean/placement_candidates_ranked.csv` | `08` |
| Greedy coverage, 10/25/50 sites | 3.51% / 6.53% / 9.30% of unserved population | `data/clean/placement_greedy_coverage.csv` | `08` |

**Read the access-vs-mortality correlation carefully**: it is NEGATIVE (closer to
supply correlates with higher, not lower, mortality). The most likely explanation is
reverse placement — harm reduction orgs sited themselves in high-need areas, so short
distance is probably a consequence of recognized need, not a protective cause. This
is not evidence that naloxone access fails; see the script's own output notes and
`manuscript/` for the full caveat. Do not quote this number without that context.

## Data sources

| Source | Publisher | Vintage | Access |
|---|---|---|---|
| 2020 Census P.L. 94-171 block population + TIGER/Line 2024 | U.S. Census Bureau | 2020 decennial / 2024 geography | Open, API (key required) |
| Medical Examiner Case Archive | Cook County | Live, updated daily; pulled window 2022–2025 | Open, Socrata API — **individual-level, privacy floor applies, raw pulls never committed** |
| ACS 5-year poverty (S1701) & uninsurance (S2701) | U.S. Census Bureau | 2024 5-year release | Open, API |
| Social Vulnerability Index 2022 | CDC/ATSDR | 2022 | Open, ArcGIS FeatureServer |
| GTFS static feed | Chicago Transit Authority | Current | Open, direct download |
| Naloxone supply registry | Assembled from IDHS DOPP directory, CDPH naloxone-at-libraries program, named org websites | 2026-10 | Manually compiled (Environment C — no consolidated state feed exists) |
| Business licenses (placement candidates) | City of Chicago Data Portal | Current/active | Open, Socrata API |

Not yet included (open gaps, not estimated around): SAMHSA facility locator (API
needs registration, not completed — skipped for now since approval timing is
outside our control); HIV prevalence among Chicago PWID. The IDHS DOPP provider
list has now been fully extracted (all 14 statewide entries reviewed; only
Live4Lali and Transforming Reentry Services serve Cook County) and is complete.

## Limitations

- **Supply registry could still grow further.** 103 sites is already well above
  the reference paper's 38 for Dallas, and the IDHS DOPP list is now fully
  reviewed, but SAMHSA's facility locator is not included (requires API
  registration/approval, outside our control) — the true access picture could
  shift somewhat further if that's added later.
- **Mortality window is 2022–2025, not a single calendar year**, chosen to keep
  tract-level counts meaningful; 952 of 1,332 tracts still fall below the self-imposed
  5-case small-cell display threshold even with 4 years pooled.
- **Access-vs-mortality correlation is not causal** and likely reflects reverse
  placement (orgs locating in high-need areas), not a causal effect of distance on
  risk. See the headline-outputs note above.
- **Business-license candidates are license-derived, not field-verified** — a
  "Tobacco" license doesn't guarantee a viable or willing host; matches the same
  caveat the reference paper applies to its own TABC-derived categories.
- **Straight-line distance, not real travel distance** — understates real burden,
  same conservatism the reference paper documents for Dallas.
- Full limitations list will be finalized for the manuscript at the Week 10 freeze.

## Repository structure

```
scripts/       pipeline scripts (01-08) + run_all.py, run in dependency order
data/raw/      dated raw input snapshots (sensitive ME pulls are gitignored, never committed)
data/clean/    derived outputs + metadata (all committed data here is aggregate/public-safe)
figures/       manuscript figures, 300 dpi, PNG + PDF (not yet generated)
manuscript/    drafted deliverable sections (city profile, policy matrix, data plan, symposium list)
references/    source PDFs (Dallas paper, deliverable guide)
```

## Reproducing this analysis

1. Copy `.env.example` to `.env` and fill in a free Census API key
   (api.census.gov/data/key_signup.html — note the two-step email-activation flow).
2. `python3 -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt`
3. `python scripts/run_all.py` — runs all 8 stages in order; each stage prints its
   own row counts, null rates, and headline numbers as it runs, and writes outputs to
   `data/clean/`.

Internet access is required — every script pulls live from its public source rather
than bundling a static copy, so re-running after upstream data changes will reflect
the latest available data (and may produce slightly different numbers than the table
above, which reflects a pull made 2026-10-18).
