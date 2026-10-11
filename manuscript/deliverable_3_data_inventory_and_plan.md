# Deliverable 3 — Data Inventory & Analysis Plan (DRAFT v1)

*This is the scoping gate per the program guide: no pipeline code should be written
until this plan is reviewed and approved. Becomes manuscript §2. This draft is ready
for your review — treat it as a proposal to sign off on, amend, or push back on
before Deliverable 4 (the analytic repository) begins.*

## Data inventory

One row per dataset investigated, including absences — a documented absence is a
finding, a silent omission is not.

| Dataset | Publisher | Endpoint | Resolution | Vintage | Access | Verdict |
|---|---|---|---|---|---|---|
| 2020 Census P.L. 94-171 block population | U.S. Census Bureau | census.gov redistricting data API/bulk files | Census block | 2020 decennial | Open | **Use** — measured population denominator, identical role to Dallas |
| TIGER/Line block & tract shapefiles | U.S. Census Bureau | census.gov TIGER/Line | Block/tract | 2024 vintage | Open | **Use** |
| ACS 5-year poverty (S1701) & uninsurance (S2701) | U.S. Census Bureau | data.census.gov / API | Census tract | 2020–2024 5-yr | Open | **Use** — but Deliverable 1's DataUSA-derived demographic figures must be replaced with a direct table pull before manuscript use |
| CDC/ATSDR Social Vulnerability Index | ATSDR | atsdr.cdc.gov/placeandhealth/svi | Census tract | 2022 | Open | **Use** |
| Cook County Medical Examiner Case Archive | Cook County | **CONFIRMED 2026-10-11**: `datacatalog.cookcountyil.gov/resource/cjeq-bs86.json` (Socrata API) | **Case-level — exact street address + lat/long**, plus `chi_commarea`/`chi_ward`/ZIP for safe aggregation | Aug 2014–present, updated daily; ~740K total records, opioid subset directly queried this pass | Open, full SoQL API + CSV/JSON/GeoJSON export | **Use — this is the paper's central data asset.** Individual-level; privacy floor applies in full (see CLAUDE.md) — raw pulls are gitignored, never committed |
| Cook County/Chicago joint opioid surveillance report | CCDPH/CDPH | cookcountypublichealth.org | Community area / citywide | Published June 2026, annual | Open, PDF | **Use** for finalized multi-year trend and demographic breakdowns |
| CDC NCHS model-based overdose mortality | CDC NCHS | data.cdc.gov (Socrata) | Census tract (aggregated to native units, per Dallas methodology) | Rolling 12-mo | Open | **Use as a secondary/comparison layer only** — since Cook County ME gives measured case-level data, the CDC modeled product's role here is to demonstrate the same modeled-vs-measured contrast the reference paper had to rely on exclusively; it is not our primary source |
| SAMHSA treatment facility locator | SAMHSA | findtreatment.gov | Point | Rolling | Open | **Use** as one input to the supply registry (Deliverable 3 registry-building task) |
| CTA GTFS feed | Chicago Transit Authority | transitchicago.com/developers/gtfs | Stop-level, 10,816 stops, 131 routes | Rolling | Open | **Use** — direct Dallas-DART equivalent |
| Illinois DOPP funded-provider directory | IDHS/DBHR | dhs.state.il.us (Illinois Overdose Prevention Programs: Contact Information) | Organization/address list, not geocoded | Rolling | Open, static list | **Use as registry seed** — requires manual geocoding; not machine-readable geodata the way Texas DSHS NarcanSites was |
| Illinois Helpline / DOPP locator | Illinois Helpline | zip-code search tool | Point, but search-only (no confirmed bulk export) | Rolling | Open, tool only | **Investigate further** — if no export exists, this confirms the registry must be manually assembled |
| Chicago Data Portal — business licenses, POIs, 311 | City of Chicago | data.cityofchicago.org | Point/address | Rolling | Open, Socrata API | **Use** for placement-model candidate sites (Deliverable 3/8 equivalent to Dallas's TABC+business-license approach) |
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
   *because* it could not validate against real deaths. This paper can instead
   directly test whether measured access gaps and measured mortality concentration
   **actually coincide** — a stronger, more defensible claim than a rank-correlation
   between two access-based rankings.

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

**5. Composite construction (if built).** Proposed five layers, equal-weighted
0.20 each as a starting justification (mirroring the CDC/ATSDR SVI convention the
reference paper cites, disclosed as an analyst choice): poverty rate (ACS S1701),
uninsurance rate (ACS S2701), CDC/ATSDR SVI, measured distance to nearest assembled
naloxone/harm-reduction site, and inverted CTA stop density within 0.5 mi. At least
two re-weighted sensitivity variants will be run (doubling one layer's weight at a
time) with flip-rate reported regardless of outcome, per Section 2.3's non-negotiable
rule. A modeled-mortality layer will **not** be included by default, since real
measured mortality is available here and folding a weaker (modeled/CDC) signal into
the index when a stronger (measured/ME) one exists would be a step backward relative
to what Dallas's constraints forced — this is a meaningful methodological departure
from the reference paper's five-layer design.

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
   - Bilingual/language-capacity flags on naloxone supply sites — expected to be
     absent, matching the reference paper's Dallas finding, but not yet confirmed
     one way or the other; will be checked directly against whatever registry
     fields the assembled supply data actually has once built, not assumed.
   - ~~Exact address-level ME case locations~~ **Resolved 2026-10-11** — the API
     does expose exact addresses/coordinates per case (see CLAUDE.md). This is not
     a gap; it's the opposite problem (handled via the privacy floor + gitignored
     raw pulls, not via reporting an absence).

## Open items before Week 5 pipeline work begins

- ~~Resolve the exact Cook County ME dashboard URL...~~ **Done 2026-10-11.**
  Confirmed endpoint, schema, and live-queried opioid counts — see CLAUDE.md's
  "Cook County Medical Examiner Case Archive" section for full detail.
- Confirm whether the IDHS DOPP contact list is complete enough to serve as a
  registry seed, or whether direct outreach to Chicago Recovery Alliance, COIP, and
  Cook County Health is needed to supplement it with actual site addresses.
- Decide the community-area vs. census-tract question for the mortality layer once
  the ME dashboard's actual resolution is confirmed.

---

## Sources consulted this pass

Cook County government dashboard-launch press releases and coverage (Governing,
GovTech, Daily Herald, cookcountyil.gov); IDHS DOPP program and contact-information
pages; CTA Developer Center and City of Chicago Data Portal (GTFS); City of Chicago
Data Portal (business licenses); U.S. Census Bureau (P.L. 94-171, TIGER/Line, ACS —
program-standard sources, not re-searched this pass since identical to the reference
paper's usage).
