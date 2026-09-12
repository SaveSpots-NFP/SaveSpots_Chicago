# SaveSpots Chicago — Harm Reduction Access & Policy Analysis

## What this project is

Undergraduate research paper for the SaveSpots Research Department, 2026 Cohort. The
paper analyzes naloxone/harm-reduction access, policy environment, and geographic
prioritization for **Chicago / Cook County, Illinois**, modeled on the structure and
rigor of the program's reference paper (Ilyas & Ilyas, 2026, "Structural Gaps in Urban
Harm Reduction Infrastructure: A Block-Level Access and Policy Analysis of Dallas
County, Texas" — `references/Dallas paper.pdf`).

**The Dallas paper is a benchmark for depth and honesty, not a template to copy.**
Chicago's data environment is fundamentally different from Dallas's, so the analysis
itself must differ. Full program rules live in `references/SaveSpots Deliverable Guide
FINAL.pdf` — read that document in full before making methodology decisions; this file
summarizes it but is not a replacement.

Reference repo (Dallas, for structural comparison only): github.com/Ilyas1434/dallas-research-savespots

## Chicago's data environment

Declared per Section 3.2 of the guide: **Environment B — Open point-level mortality**,
likely hybrid with C (naloxone supply directory is not obviously centralized for
Chicago/Cook County and may need to be assembled).

- Cook County Medical Examiner publishes case-level overdose death records with
  geography (the guide names Cook County explicitly as "the clearest example" of this
  environment). This is the single biggest opportunity for this paper: Dallas *could
  not* validate its access/vulnerability prioritization against real death geography
  because Texas suppresses tract-level counts. Chicago can run that validation. Doing
  so is a genuinely novel result, not a replication — treat it as the paper's likely
  central contribution.
- Confirm before relying on it: whether records geocode to place of death, place of
  injury, or decedent residence. These are different questions — state which one is
  used and what it can and cannot support.
- Privacy floor (hard rule, no exceptions): nothing published — figure, table, map,
  repo file, poster panel — may contain individual-level records, addresses, or
  coordinates of overdose events or decedents. Analyze at point level locally only;
  publish aggregated (tract / ZIP / community area) only.
- Still need to inventory: naloxone/harm-reduction access point registry (state or
  county — if none exists, that's Environment C and the registry becomes a
  publishable data contribution in its own right), Illinois Good Samaritan / naloxone
  standing order law, CTA GTFS transit feed, ACS poverty/uninsurance tables, CDC/ATSDR
  SVI, SAMHSA locator, Chicago/Cook County open data portal.

## The research contract (non-negotiable, applies to every number in the paper)

1. **Classify every quantity** as one of three types, stated wherever ambiguity could
   arise:
   - **Measured** — a direct count or computed geometric quantity, no modeling/
     interpolation/smoothing (e.g., census block population, point-to-point distance).
   - **Modeled** — a published model-based rate, survey estimate, or any index derived
     from them (e.g., CDC NCHS modeled overdose rates, ACS 5-year estimates, any
     composite score).
   - **Published** — a figure transcribed from a cited report, with page/figure
     reference.
2. **Name the primary measured quantity** — at least one of the paper's three core
   answers must rest on something measured, not modeled, and the methods must state
   why it's the defensible target given Chicago's data environment. For Chicago this
   is likely observed overdose density itself (since point-level mortality is open),
   unlike Dallas where it had to be access/distance.
3. **Disclose weights; run sensitivity** on any composite/index — at least two
   alternative weightings, reporting the share of units that change classification.
   Report the result even when it fails a stability threshold; disclosure always
   strengthens the paper.
4. **Report gaps as gaps** — if a quantity can't be produced from available data,
   report "not computable" and attribute to the source that would hold it. Never
   estimate around a gap.
5. **Never allocate a coarse measure to a fine geography** — if a stat is published
   only at county level, it stays at county level. Document the exclusion as a
   limitation instead.
6. **Take the conservative figure** when sources conflict — present both, explain the
   likely discrepancy, use the more conservative estimate, and say that's what was
   done.
7. **Reproducibility** — every headline number must be regenerable by running one
   command in this repository. If a reader can't regenerate a figure from code + cited
   inputs, it doesn't go in the paper.
8. **AI is not a source** — no statistic, policy detail, program outcome, citation,
   author name, article title, or publication date may originate from an AI-generated
   summary. Every factual claim must trace to a primary source (or a secondary source
   citing one) that was actually opened and read. Check every reference against the
   actual document before it's used — LLMs fabricate plausible-looking citations.

## The three questions the paper must answer, in order

1. **Where is the burden?** Overdose burden at the finest resolution the data
   permits — state that resolution explicitly.
2. **Where is the gap?** Where need and available service diverge, using a measurable
   quantity.
3. **Where should supply go?** A ranked, geographically specific, actionable output —
   named places with a stated selection rule, not a list of neighborhoods.

## Required repo structure (Section 7.1)

```
scripts/       one script per pipeline stage + a run_all script (dependency order)
data/raw/      dated snapshots of every input (reproducible after upstream changes)
data/clean/    every derived output + metadata files (row counts, date ranges, null rates)
figures/       every manuscript figure at 300 dpi, PNG + PDF, exported by pipeline (not by hand)
references/    source PDFs (Dallas paper, deliverable guide) and other reference docs
README.md      what/why/headline-outputs-with-file/sources-with-vintage/limitations
report.md or insights.md   dense sourced findings — manuscript is written from this
LICENSE / LICENSE-DATA     MIT for code, CC BY 4.0 for derived data
CITATION.cff   for Zenodo DOI minting
```

Standards: log row counts/date ranges/null or geocode-failure rates in every script
(stop and flag if geocode failure >10%). Handle suppression explicitly, never silently
impute. No secrets in the repo (API keys in gitignored `.env`, commit `.env.example`).
Don't commit data not licensed for redistribution — cite and link instead.

## Deliverables & semester timeline

| # | Deliverable | Becomes | Due |
|---|---|---|---|
| 1 | City Profile & Harm Reduction Landscape | Manuscript §3, §5 | Week 3 |
| 2 | Policy Matrix | Manuscript §4 | Week 4 |
| 3 | Data Inventory & Analysis Plan | Manuscript §2; scoping gate | Week 4 |
| 4 | Analytic Repository (GitHub + Zenodo DOI) | Reproducibility backing | Week 10 |
| 5 | Manuscript | The paper | Week 13 |
| 6 | Preprint (medRxiv) | Citable DOI | Week 15 |
| 7 | Conference Abstract | Symposium submissions | Wk 11 draft / Wk 15 final |
| 8 | Poster | Presentation | Week 15 |

Gates: **Week 4** (scoping — no pipeline code before sign-off) and **Week 10**
(analysis freeze — numbers don't move after this). Program runs Jul 28–Nov 8, 2026,
15 Sunday meetings.

## Manuscript structure (11 sections + refs, APA 7th ed.)

Intro (opens with Chicago-specific burden data, never national framing) → Methodology
(measured/modeled/published classification, primary measured quantity, composite
weights+sensitivity, specific limitations) → City Profile → Policy Analysis (two
layers per policy: what the law says vs. what it does) → Implementation Analysis (who
is reached vs. systematically missed, and why) → Comparative Case Study (one
structurally analogous city, one best-practice city, explicit selection justification,
named transferable lessons, explicitly qualitative not causal) → Gap Identification
(min. 6 categories: policy, implementation, geographic, demographic, data, access,
cultural, structural) → Geographic Prioritization (primary analysis; named units;
close with burden data at its honest resolution) → Metrics & Evaluation → 
Recommendations (each tied to a specific gap + location, feasibility-noted, addressed
to authorities/orgs generally — never to SaveSpots itself) → Conclusion (synthesis,
nothing new introduced).

Front matter: title page, author note with 6 required statements (author
contributions, ethics, funding, competing interests, data availability, use of AI).

## Writing standard (the "substitution test")

Every paragraph: states a local condition → gives supporting evidence → interprets it →
draws the implication for harm reduction access/delivery in Chicago specifically. If
a paragraph could be dropped into a paper about any other city unchanged, it fails
and needs rewriting. Generic framing ("fentanyl is increasingly contaminating supplies
across many cities...") is disqualifying; city-specific, quantified, interpreted
claims are the standard.

## Source standards

- **Tier 1 (preferred)**: CDC/NIH/SAMHSA/NIDA, state/county health departments, U.S.
  Census, peer-reviewed journals, GAO/KFF/Brookings/Baker Institute, legal databases
  for statutory text.
- **Tier 2 (care)**: local news with named reporter/sources, established nonprofit
  self-reported data, official point-in-time homelessness counts.
- **Prohibited**: Wikipedia/Reddit/social media, unattributed blogs, uncited
  statistics-in-articles, AI-generated summaries as fact sources, pay-to-publish
  aggregators without methodology docs.

## Common failure modes to actively avoid

Generic writing that could describe any city; description without analytical
interpretation; recommendations not earned by findings; policy stated without an
implementation/enforcement layer; figures not referenced/explained in text; overstated
certainty (blurring measured vs. modeled); undisclosed composite weights; coarse data
fabricated down to fine geography; any AI-sourced factual claim.

## Notes for future sessions

- Chicago's likely strongest paper angle: the independence/validation check Dallas
  explicitly could not run — compare an access- or vulnerability-based prioritization
  against actual observed death geography using Cook County Medical Examiner data.
- Whenever in doubt on methodology or format, re-read the relevant section of
  `references/SaveSpots Deliverable Guide FINAL.pdf` rather than relying on this
  summary — this file will drift from the source as the guide gets amended.
- Every deliverable this session helps produce should be checked against the
  `references/Dallas paper.pdf` section named in Guide §17 ("Using the Reference
  Paper") for the corresponding deliverable, before considering it done.
