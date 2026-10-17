# Analytic Findings Report (PROVISIONAL — pre-freeze)

*This is the dense, sourced findings document the manuscript (Deliverable 5) gets
written from, per the repo structure standard. Every number here traces to a script
in `scripts/` and an output in `data/clean/`. Status: pipeline complete through
placement ranking; not yet frozen (Week 10). Pulled 2026-10-17.*

## 1. Population and geography (script 01)

Cook County's 2020 decennial population is **5,275,541**, measured (not estimated)
across 83,018 census blocks, of which 70,992 are populated. This is the exact
denominator for every access calculation below. Source: 2020 Census P.L. 94-171
(P1_001N), joined to TIGER/Line 2024 block geometry.

## 2. Naloxone supply registry (scripts 02, 02b)

**94 confirmed supply sites**, assembled by hand (Environment C — no consolidated
Illinois feed exists, unlike Texas DSHS NarcanSites):
- **82 Chicago Public Library branches** — naloxone stocked at all CPL branches,
  no questions asked, per IDHS's funded-provider directory and multiple CDPH press
  confirmations (2026). This is the single largest category and has no Dallas
  equivalent.
- **12 named organizations**: Chicago Recovery Alliance; 5 COIP storefronts (Garfield
  Park, Humboldt Park, West Englewood, Southeast Side, Uptown); Cook County Health's
  Stroger and Provident Hospital EDs; West Side Heroin/Opioid Task Force; Live4Lali;
  Transforming Reentry Services (2 locations).

94 sites already exceeds the reference paper's 38 for Dallas County. Still missing:
SAMHSA's facility locator (requires API registration, not completed) and the
remainder of the statewide IDHS DOPP provider list beyond the 2 Cook-specific
entries found. The true count is almost certainly higher than 94.

## 3. Measured access analysis (script 03)

Against the full 94-site registry, population-weighted straight-line distance from
every census block's internal point (matching the reference paper's exact method):

- **Beyond 1 mile of supply: 2,694,247 residents (51.07%)**
- Beyond 2 miles: 2,106,313 (39.93%)
- Beyond 5 miles: 1,129,943 (21.42%)
- Population-weighted average distance to nearest supply: 4,652 meters (~2.9 miles)

**This is a fundamentally different access picture than Dallas's 84.03% beyond one
mile.** With a 9-site seed registry (before the library discovery), the same
calculation returned 93.50% beyond 1 mile — the 82-branch library network alone
accounts for most of the difference. This is the paper's first major finding:
Chicago's naloxone access gap, measured the same way as Dallas's, is roughly a third
the size, driven almost entirely by one policy decision (stocking all public
libraries) that Dallas never made.

## 4. Mortality, measured not modeled (script 04)

Cook County Medical Examiner Case Archive (live Socrata API, individual-level,
privacy floor applies — see CLAUDE.md), opioid-flagged cases, window 2022-01-01
through 2025-12-31: **5,783 total cases, 5,372 with usable coordinates**, spatially
joined to 1,332 census tracts. 242 tracts recorded zero cases in the window; 952 of
1,332 fall below a self-imposed 5-case small-cell display threshold (a chosen privacy
practice, not a data limitation — unlike Dallas, nothing here is actually suppressed
by law; Illinois publishes real case-level data).

This is a direct methodological advantage over the reference paper: Dallas's
mortality layer was necessarily Modeled (CDC NCHS tract-rate product, 91.8% of tracts
suppressed by Texas confidentiality law). Chicago's mortality layer is Measured — a
direct case count — for the first time letting this kind of analysis test access
against real observed deaths rather than against a second access-based proxy.

## 5. Central validation: access vs. mortality (script 05)

**The paper's core methodological contribution.** Tract-level population-weighted
average distance to supply, correlated against tract-level opioid mortality rate per
100,000 (both measured quantities):

- Spearman rho = **-0.3057** (p = 3.7×10⁻³⁰), all 1,330 matched tracts
- Spearman rho = **-0.3794** (p = 1.9×10⁻¹⁴), excluding the 950 small-cell-flagged
  tracts (sensitivity check)
- Worst-access quartile (333 tracts) vs. highest-mortality-rate quartile (333
  tracts): only 24 tracts overlap, versus 83 expected under no relationship

**The correlation is negative**: tracts closer to supply have higher, not lower,
mortality rates. This should NOT be read as "naloxone access increases risk" or
"access doesn't work." The far more likely explanation is reverse placement —
Chicago Recovery Alliance, COIP, and the West Side Heroin/Opioid Task Force all
explicitly targeted high-need West Side neighborhoods when choosing locations, which
mechanically shrinks measured distance exactly where mortality is already
concentrated. Short distance is plausibly a *consequence* of recognized need, not a
*cause* of lower risk. This finding needs careful, explicitly non-causal framing in
the manuscript's methods and limitations sections — it is analytically interesting
(it demonstrates the independence check works and surfaces something real) but must
not be oversold either direction.

## 6. Composite vulnerability index (scripts 06, 07)

Five equal-weighted (0.20 each) layers, all 1,332 tracts scored (100% coverage):
poverty rate (ACS S1701), uninsurance rate (ACS S2701), CDC/ATSDR SVI 2022 overall
percentile, measured distance to nearest supply, and inverted CTA transit
connectivity (stops within 0.5mi of tract centroid). Score range 0.1549-0.9554.
Jenks natural-break tiers: **Tier 1 (highest vulnerability): 346 tracts; Tier 2: 768;
Tier 3: 218.**

Deliberate departure from the reference paper: no modeled-mortality layer included,
since real measured mortality exists separately (Section 5) and is used as an
independent validation target rather than folded into the index — avoiding the
circularity of testing an index against a quantity it already contains.

**Sensitivity analysis** (disclosed regardless of outcome, per the research
contract): doubling the poverty weight changes **0.00%** of tract tiers — fully
robust. Doubling the access-distance weight changes **12.09%** — notably *more*
stable than the reference paper's own distance-weighted Dallas variant (21.5%, which
exceeded Dallas's own 15% stability threshold). This composite index is more robust
to its own construction choices than the reference paper's was.

## 7. Placement ranking (script 08)

11,370 active Chicago business-license candidates (Retail Food Establishment,
Tobacco, Package Goods, Filling Station, Tavern — Chicago's equivalent of Dallas's
TABC-permit-derived candidate pool), ranked by composite-need × measured-reach among
currently-unserved residents (beyond 1 mile of the 94-site registry, within 0.5 miles
of the candidate).

Top-ranked cluster: **Avondale, along the Pulaski/Diversey corridor** — the top 5
candidates each reach roughly 13,000-14,000 unserved residents, with tract composite
scores in the 0.69-0.75 range (upper-middle of the observed 0.15-0.96 scale).

**Greedy de-overlapped coverage**: the best 10 non-overlapping sites would newly
reach 94,456 unserved residents (3.51% of the 2,694,247 total unserved); 25 sites →
177,849 (6.60%); 50 sites → 256,676 (9.53%). These percentages are meaningfully
lower than Dallas's equivalent figures (5.4% / 10.6% / 17.7% for 10/25/50 sites) —
plausibly because Chicago's remaining unserved population, after the library network
already covers dense areas, is more residually scattered and harder to reach
efficiently with point placements than Dallas's more concentrated desert. Worth
developing as a substantive finding, not reporting as a weaker result.

## Open threads for the manuscript (Deliverable 5)

1. Resolve SAMHSA + full IDHS DOPP registry expansion — could shift every number in
   Sections 3, 5, 6, and 7 above.
2. Develop the reverse-placement explanation for Section 5's negative correlation
   with actual evidence (e.g., check whether access-distance predicts mortality in
   tracts *without* a harm-reduction org present, as a rough de-confounding pass).
3. Incident-vs-residence distinction in the ME data (Section 2.3's guide warning)
   not yet resolved — current pull uses incident location; residence comparison not
   yet run.
4. Figures not yet generated (reference paper's Figures 1-4 equivalents) — next
   concrete task once registry expansion is done.
