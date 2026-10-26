---
name: writing-tdr
description: Minimal skeleton and gates for Technical Design Reports (detector/computer TDR) and similar long-form design documents. Use when drafting or structuring a TDR chapter or a CDR/LCDR-style document.
---

# TDR (Technical Design Report)

## Purpose

The public design document for a detector subsystem, upgrade, or computing
system: requirements -> design -> performance -> cost/schedule, at a level
a reviewer can judge technical maturity. Basic skeleton only.

## Preconditions

- Know which TDR section/chapter you own and its page budget.
- Performance numbers must come from validated simulation/reconstruction
  productions or test-beam/prototype data - identify the source before
  writing.
- Approval status of any number quoted (preliminary numbers do not go in a
  TDR body; put them in an appendix labeled as such if allowed).

## Minimal chapter structure

1. **Introduction**: context, requirements traceability (link each design
   choice to a requirement ID).
2. **Requirements**: physics/detector/computing requirements, quantified
   with margins.
3. **Design**: layout, components, interfaces; one figure per subsystem.
4. **Performance**: simulation/prototype results, with uncertainties and
   the production/sample ID behind every number.
5. **Operations / infrastructure**: environment, radiation, services,
   schedule (GLT milestones) as applicable.
6. **Costs**: only in the cost section, consistent with the project budget
   document.
7. **Summary**: maturity statement per requirement.

## Rules (harness-style)

- Requirements traceability: no design feature without a requirement, no
  requirement without a verification method.
- Every performance claim cites its input (MC campaign, test beam run).
- Consistency gate: units, naming, and numbers identical across chapters -
  maintain a shared numbers/definitions file the build includes.
- Membrane: unpublished internal numbers stay in internal notes; the TDR
  quotes only approved values.

## Validation

- Traceability table complete (requirement -> design -> verification).
- Cross-chapter consistency check passes (shared numbers file, no orphans).
- All figures generated from versioned scripts, not pasted images.

## Failure recovery

| symptom | remedy |
|---|---|
| reviewer disputes a number | go to its source production; if not validated, demote to appendix or remove |
| chapters disagree on a value | single source of truth file; rebuild all chapters |
| scope creep in design section | move detail to an internal note, keep TDR at decision level |
