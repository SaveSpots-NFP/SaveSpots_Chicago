# Deliverable 3 — Data Inventory & Analysis Plan

*Becomes manuscript §2. Status as of 2026-11-01: this started as the Week 4 scoping
plan, and the pipeline it describes has since been built and run end to end
(scripts 01-08, see `report.md` for results). This document is updated to reflect
what was actually found and done, not just what was proposed — a plan that still
read as hypothetical after the work was finished would misrepresent the project.
Where the original plan changed on contact with real data, that's noted explicitly
rather than silently rewritten, per the guide's own standard for scope changes.*

*Length check ("two pages max" for "The plan" section specifically, not the
inventory table above it): the plan section runs long now that it documents actual
results rather than proposals. Trim for the two-page target when this moves into
the formal submission; this working version prioritizes completeness over the page
limit since it's also serving as the project's record of what happened.*

## Data inventory

One row per dataset investigated, including absences — a documented absence is a
finding, a silent omission is not.

| Dataset | Publisher | Endpoint | Resolution | Vintage | Access | Verdict |
|---|---|---|---|---|---|---|
| 2020 Census P.L. 94-171 block population | U.S. Census Bureau | census.gov redistricting data API/bulk files | Census block | 2020 decennial | Open | **Use** — measured population denominator, identical role to Dallas |
| TIGER/Line block & tract shapefiles | U.S. Census Bureau | census.gov TIGER/Line | Block/tract | 2024 vintage | Open | **Use** |
| ACS 5-year poverty (S1701) & uninsurance (S2701) | U.S. Census Bureau | data.census.gov / API | Census tract | 2024 5-yr | Open | **Used** — pulled directly via Census API for all 1,332 Cook County tracts, zero nulls (script 06); supersedes Deliverable 1's earlier DataUSA-derived figures, which should not be cited going forward |
| CDC/ATSDR Social Vulnerability Index | ATSDR | atsdr.cdc.gov/placeandhealth/svi | Census tract | 2022 | Open | **Use** |
| Cook County Medical Examiner Case Archive | Cook County | **CONFIRMED 2026-10-11**: `datacatalog.cookcountyil.gov/resource/cjeq-bs86.json` (Socrata API) | **Case-level — exact street address + lat/long**, plus `chi_commarea`/`chi_ward`/ZIP for safe aggregation | Aug 2014–present, updated daily; ~740K total records, opioid subset directly queried this pass | Open, full SoQL API + CSV/JSON/GeoJSON export | **Use — this is the paper's central data asset.** Individual-level; privacy floor applies in full (see CLAUDE.md) — raw pulls are gitignored, never committed |
| Cook County/Chicago joint opioid surveillance report | CCDPH/CDPH | cookcountypublichealth.org | Community area / citywide | Published June 2026, annual | Open, PDF | **Use** for finalized multi-year trend and demographic breakdowns |
| CDC NCHS model-based overdose mortality | CDC NCHS | data.cdc.gov (Socrata) | Census tract (aggregated to native units, per Dallas methodology) | Rolling 12-mo | Open | **Not pursued** — deliberate scoping decision, not an oversight: once real measured ME mortality was confirmed (next row), pulling a weaker modeled product added no analytical value and risked exactly the circularity the index design (item 5 below) was built to avoid. Documented here so the absence reads as a choice, not a gap. |
| SAMHSA treatment facility locator | SAMHSA | findtreatment.gov | Point | Rolling | Open, but requires API registration/approval | **Not used this cycle** — registration submitted conceptually but approval timeline is outside our control; the registry (103 sites, see below) was built to be usable without it rather than blocking on an external approval. Could be added in a future pass if time allows. |
| CTA GTFS feed | Chicago Transit Authority | transitchicago.com/developers/gtfs | Stop-level, 11,138 stops | Rolling | Open | **Used** — transit-connectivity composite layer (script 06/07) and exact station coordinates for the CTA naloxone vending machine sites (below) |
| Illinois DOPP funded-provider directory | IDHS/DBHR | dhs.state.il.us (Illinois Overdose Prevention Programs: Contact Information) | Organization/address list, 14 statewide entries, not pre-geocoded | Rolling | Open, static list | **Fully reviewed and used.** All 14 entries checked (not just skimmed) — only 2 serve Cook County (Live4Lali, Transforming Reentry Services), both geocoded and in the registry. This list is now exhausted as a source, not partially used. |
| Chicago Public Library branch locations | City of Chicago Data Portal | data.cityofchicago.org, resource x8fc-8rcq | Point, pre-geocoded, 82 branches | Current | Open, Socrata API | **Used — the single largest registry category.** Confirmed via IDHS directory + CDPH press coverage that naloxone is stocked at all 82 CPL branches, no questions asked; this single policy decision is most of the gap between Chicago's and Dallas's measured access figures. |
| CTA naloxone vending machines | Chicago Transit Authority | transitchicago.com/naloxone/ | Point, 6 named stations (coordinates taken from the GTFS feed above) | Current | Open, static page | **Used.** Includes the registry's only confirmed 24-hour fixed site (95th/Dan Ryan, CDPH-operated) — directly comparable to the reference paper's "exactly one 24-hour point" finding for Dallas. |
| Named harm-reduction/treatment orgs (Chicago Recovery Alliance, COIP x5, Cook County Health x2, West Side Task Force, TASC x2, Haymarket Center) | Org websites, press coverage | Various | Point, address-geocoded via Census geocoder | 2026 | Open | **Used** — 13 sites, manually compiled and geocoded (Environment C task); Haymarket Center's naloxone access specifically is flagged as independently unconfirmed, included conservatively |
| Chicago Data Portal — business licenses | City of Chicago | data.cityofchicago.org, resource uupf-x98q | Point/address, 11,370 active candidates after filtering+dedup | Current | Open, Socrata API | **Used** for placement-model candidates (script 08) — Chicago's equivalent of Dallas's TABC+business-license approach |
| IDPH statewide semiannual overdose report | IDPH | dph.illinois.gov | State/regional | Semiannual | Open, PDF | **Use** for state-level context framing |
| Chicago/Cook County PWID meta-analysis (HCV) | Published literature (PMC) | pmc.ncbi.nlm.nih.gov | Metro-area estimate, not sub-geography | 1997–2017 data | Open, peer-reviewed | **Use as context, cannot allocate to tract** — county/metro-level estimate only, per the "never allocate a coarse measure to a fine geography" rule |
| Chicago PWID HIV prevalence | — | — | — | — | **Not located** | **Report as gap** unless found in Deliverable-3 execution |
| Chicago/Cook County non-fatal ED overdose visits, sub-county | — | — | — | — | **Not located this pass** | Investigate CDPH/IDPH dashboards directly; if county-level only, exclude from tract-level work and document as a limitation, following the reference paper's treatment of ED visits |
| Chicago/Cook County settlement fund spending (local 25% share) | — | — | — | — | **Confirmed not centrally published** (per Deliverable 2) | **Report as gap** — Illinois does not require local governments to publish this |

## The plan

**1. Data environment declaration.** Chicago/Cook County is a **hybrid of
Environment B (open point-level mortality) and Environment C (no consolidated
supply directory)**. Evidence: the Cook County Medical Examiner operates a public
case-archive dashboard with opioid-death filtering, updated twice daily, described
in county press materials as containing demographic detail (age, sex, race/
ethnicity) per case — this is Environment B's defining feature and something
Dallas's data environment explicitly lacked. On the supply side, no single
state-published, machine-readable naloxone-site feed comparable to Texas DSHS's
NarcanSites was located; the best available source is IDHS's static funded-provider
contact list, which will need manual geocoding — the defining feature of
Environment C.

**2. Primary measured quantity.** Because this is a hybrid environment, this paper
can name **two** measured quantities rather than the one Dallas's suppression
regime forced it into, and treat their relationship as the paper's central
methodological contribution:
   - **Measured access**: population-weighted straight-line distance from census
     blocks to the assembled naloxone/harm-reduction supply registry (identical
     construction to Dallas's primary quantity).
   - **Measured mortality**: Cook County Medical Examiner case-level opioid deaths,
     aggregated to whatever geography privacy permits (see open question below) —
     this is a direct count, not a CDC model-based rate, and is not subject to the
     tract-level suppression that made Dallas's mortality data Modeled rather than
     Measured.

   The paper's independence check inverts the reference paper's: Dallas built its
   access ranking and mortality-inclusive ranking and found they agreed (ρ = 0.966)
   *because* it could not validate against real deaths. This paper instead directly
   tests whether measured access gaps and measured mortality concentration
   **actually coincide** — a stronger, more defensible claim than a rank-correlation
   between two access-based rankings.

   **Executed (script 05):** the result is a negative Spearman correlation
   (ρ ≈ -0.32 all tracts, ρ ≈ -0.37 excluding small-cell-flagged tracts) — tracts
   closer to supply have *higher* mortality, not lower. This is not read as evidence
   against access; the most likely explanation is reverse placement (harm reduction
   orgs sited themselves in high-need areas), which this plan did not anticipate at
   scoping time and which the manuscript must frame carefully as non-causal. See
   `report.md` §5 for the full result and reasoning.

**3. Answering the three required questions.**
   - *Where is the burden?* Cook County ME case-level opioid deaths, aggregated to
     the finest geography that doesn't violate the privacy floor (Section 2.8) —
     likely Chicago's 77 community areas or census tract, pending small-cell-count
     handling; multi-year trend from the CCDPH/CDPH joint report for the narrative
     framing established in Deliverable 1.
   - *Where is the gap?* A vulnerability composite (poverty, uninsurance, SVI,
     measured distance to assembled naloxone supply, transit connectivity via CTA
     GTFS) at census tract level, disclosed weights, sensitivity-tested — same
     structure as Dallas's Section 2.5, but validated in Step 4 below against real
     mortality rather than only cross-checked against a second modeled variant.
   - *Where should supply go?* A ranked candidate-site analysis (Chicago Data
     Portal business licenses/POIs as candidates) scored by need × measured reach
     among currently unserved residents, plus a de-overlapped greedy coverage
     analysis — directly following Dallas's Section 8.6 method, which this paper
     has no reason to depart from since it is method-agnostic to data environment.
     **Executed (script 08):** 11,370 candidates ranked; top cluster in Avondale
     along the Pulaski/Diversey corridor; greedy coverage of the best 10/25/50
     sites reaches 3.51%/6.53%/9.30% of unserved population — lower percentages
     than Dallas's 5.4%/10.6%/17.7%, plausibly because Chicago's residual unserved
     population is more scattered once the library network already covers dense
     areas. See `report.md` §7.

**4. Geographic unit.** **Resolved 2026-10-11.** Census tract for the composite and
placement analysis (matching ACS/SVI's native resolution), census block for
population-weighted distance (matching Census P.L. 94-171's native resolution) —
identical geographic strategy to Dallas. The ME data question is now answered: the
Case Archive API returns exact lat/long per case, which the pipeline can
point-in-polygon against Census tract boundaries to aggregate to **tract-level
counts** — finer than Dallas's 150-unit CDC aggregation and not suppressed by any
confidentiality rule, since nothing stops us from aggregating ourselves (the
privacy floor is about what we *publish*, not what geography exists upstream). Small
tracts with very low counts (1–4 deaths) will still need a documented small-cell
handling rule — likely matching the reference paper's practice of flagging rather
than suppressing, since Illinois has no suppression regime forcing our hand the way
Texas's did, but a near-zero-population tract reporting an exact count of 1 could
still be functionally identifying and needs a stated policy before publication (e.g.,
a minimum display threshold, consistent with the privacy floor's spirit even where
not legally mandated).

**5. Composite construction — built (script 07).** Five layers, equal-weighted 0.20
each (mirroring the CDC/ATSDR SVI convention the reference paper cites, disclosed as
an analyst choice): poverty rate (ACS S1701), uninsurance rate (ACS S2701),
CDC/ATSDR SVI, measured distance to nearest assembled naloxone/harm-reduction site,
and inverted CTA stop density within 0.5 mi. A modeled-mortality layer was
deliberately excluded, since real measured mortality is available here and folding
a weaker (modeled/CDC) signal into the index when a stronger (measured/ME) one
exists elsewhere would be a step backward relative to what Dallas's constraints
forced — a meaningful methodological departure from the reference paper's
five-layer design, and one that also avoids testing the index against a quantity
(mortality) it would otherwise partly contain.

**Result:** all 1,332 tracts scored (no missing coverage). Jenks natural-break
tiers: Tier 1 (highest vulnerability) 344 tracts, Tier 2 770, Tier 3 218.
**Sensitivity analysis, as required regardless of outcome:** doubling the poverty
weight changes 0.00% of tract tiers; doubling the access-distance weight changes
12.61% — more stable than the reference paper's own distance-weighted Dallas
variant (21.5%, which exceeded Dallas's own 15% threshold).

**6. What will not be computable, and how it's reported.**
   - HIV prevalence among Chicago-area PWID — not located this pass; reported as a
     gap unless found during pipeline construction, attributed to whatever source
     would hold it (likely IDPH or CDPH direct request).
   - Sub-county non-fatal ED overdose visit data — investigate further; if only
     available at county/state level, excluded from tract-level work per the
     "never allocate a coarse measure to a fine geography" rule and documented as a
     limitation exactly as the reference paper excluded ED visits and point-in-time
     homelessness counts for Dallas.
   - Chicago/Cook-County-specific opioid settlement spending — confirmed not
     centrally published (Deliverable 2); reported as a gap, with a records
     request or direct agency outreach as the only path to closing it, not
     estimation.
   - Bilingual/language-capacity flags on naloxone supply sites — **confirmed
     absent**, not just expected. The assembled registry's fields (name, category,
     address, source, verification date, lat/long) carry no language attribute of
     any kind, matching the reference paper's Dallas finding exactly: the gap
     exists because no upstream source records it, not because this analysis
     omitted the field.
   - ~~Exact address-level ME case locations~~ **Resolved 2026-10-11** — the API
     does expose exact addresses/coordinates per case (see CLAUDE.md). This is not
     a gap; it's the opposite problem (handled via the privacy floor + gitignored
     raw pulls, not via reporting an absence).

## Status: pipeline built and run (scripts 01-08 complete)

All items originally listed here as pre-Week-5 blockers are resolved — see
`report.md` for the full results document and `CLAUDE.md` for operational detail
(especially the Cook County ME privacy-handling convention). Remaining open work is
registry completeness (SAMHSA, if the registration comes through in time) and the
manuscript write-up itself (Deliverable 5), not further scoping.

---

## Sources consulted this pass

Cook County government dashboard-launch press releases and coverage (Governing,
GovTech, Daily Herald, cookcountyil.gov); IDHS DOPP program and contact-information
pages; CTA Developer Center and City of Chicago Data Portal (GTFS); City of Chicago
Data Portal (business licenses); U.S. Census Bureau (P.L. 94-171, TIGER/Line, ACS —
program-standard sources, not re-searched this pass since identical to the reference
paper's usage).
