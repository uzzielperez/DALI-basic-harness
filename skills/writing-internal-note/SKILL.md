---
name: writing-internal-note
description: Minimal structure and rules for internal notes (INT, memo, meeting note, progress note). Use when the user asks to draft or review an internal note, the shortest document type in the analysis-doc hierarchy.
---

# Internal Note

## Purpose

The smallest unit of analysis documentation: record one decision, one
cross-check, or one progress snapshot so future-you and your collaborators
do not have to re-derive it. Not a publication, not a reviewable analysis
document - say so when the user confuses it with an AN.

## Preconditions

- Know: audience (group/meeting), one-sentence purpose, and the date/version.
- Figures must come from a run directory, not an ad-hoc plot on someone's
  laptop (harness rule: reproducible from the run dir alone).

## Minimal structure

1. **Header**: title, authors, date, version, status (draft/final/superseded).
2. **Purpose**: one paragraph - what is decided/reported and why it matters.
3. **Content**: the note body; one topic per note.
4. **Numbers table**: every quoted number with source (script, run dir,
   config hash).
5. **References**: links to the ANs/TDRs/notes this touches.

## Rules

- Date and version every revision; never silently overwrite a circulated
  note - mark the old one superseded.
- Distinguish clearly: illustration vs final, preliminary vs validated.
- No secret/unpublished identifiers when the note will be circulated beyond
  the analysis team; run it through the membrane filter first if an LLM
  assists.

## Validation

- A reader can tell in 30 seconds: what changed, what is decided, what is
  still open.
- Every number traceable to a run directory or a cited document.

## Failure recovery

| symptom | remedy |
|---|---|
| note grows past ~5 pages | split it, or promote it to an AN |
| two notes disagree | declare one superseded, add a pointer in both |
| number not traceable | regenerate from the run dir or mark it "unvalidated" |
