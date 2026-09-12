# SaveSpots Chicago — Harm Reduction Access & Policy Analysis

**Status: scaffolding stage.** This README will be filled in as each deliverable is
completed — per the SaveSpots Research Department guide, headline outputs and their
source files are only added once numbers are real, reproducible, and frozen (Week 10
analysis freeze). Until then, this file tracks what's known and what's pending.

## What this analysis does

A block-level access, policy, and geographic-prioritization analysis of naloxone /
harm-reduction infrastructure in Chicago, Illinois, modeled on the standard set by
Ilyas & Ilyas (2026), "Structural Gaps in Urban Harm Reduction Infrastructure: A
Block-Level Access and Policy Analysis of Dallas County, Texas" (see
`references/Dallas paper.pdf`). Program requirements: `references/SaveSpots
Deliverable Guide FINAL.pdf`. Full project conventions: `CLAUDE.md`.

## Why it's built this way

Chicago's data environment differs from Dallas's in one decisive respect: Cook County
Medical Examiner publishes case-level overdose death records with geography, whereas
Texas suppresses mortality counts at fine geography by law. This means the Dallas
paper's central workaround (treating measured access/distance as the primary
quantity because mortality couldn't be trusted at fine geography) is not the binding
constraint here — Chicago can instead validate an access- or vulnerability-based
prioritization against real observed death geography, which Dallas explicitly could
not do. See `CLAUDE.md` for the full data-environment declaration once finalized in
Deliverable 3.

## Headline outputs

*(To be filled in after the analysis freeze — Week 10. Each entry will list the
number, the file it's reproduced from, and the script that generates it.)*

## Data sources

*(To be filled in as the Data Inventory, Deliverable 3, is completed. Each source
will list: dataset, publisher, vintage, retrieval date, access status, and whether it
was used, excluded, or reported as a gap.)*

## Limitations

*(To be filled in as the analysis plan and pipeline are built. Per program
standards, every limitation is stated specifically — not as a ritual disclaimer.)*

## Repository structure

```
scripts/       pipeline scripts + run_all
data/raw/      dated raw input snapshots
data/clean/    derived outputs + metadata
figures/       manuscript figures, 300 dpi, PNG + PDF
references/    source PDFs (Dallas paper, deliverable guide)
```

## Reproducing this analysis

*(Instructions will be added once `scripts/run_all` exists.)*
